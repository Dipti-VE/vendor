import uuid
import time
import httpx
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from ..config import settings
from ..models import Message, MessageStatusHistory, Conversation, Shopkeeper, ProductOffer
from .connection_manager import ws_manager

logger = logging.getLogger(__name__)

class WhatsAppService:
    @staticmethod
    def generate_provider_message_id() -> str:
        unique_token = uuid.uuid4().hex[:16]
        return f"wamid.HBgM{unique_token.upper()}"

    @staticmethod
    def clean_whatsapp_phone(raw_phone: Optional[str]) -> str:
        if not raw_phone:
            return ""
        clean = "".join(filter(str.isdigit, str(raw_phone)))
        if len(clean) == 10:
            clean = "91" + clean
        return clean

    @classmethod
    def extract_provider_message_id(cls, response_body: Any) -> Optional[str]:
        if isinstance(response_body, dict):
            for key in ("messageId", "message_id", "externalMessageId", "external_message_id", "id"):
                val = response_body.get(key)
                if val:
                    return str(val)
            if "messages" in response_body and isinstance(response_body["messages"], list) and response_body["messages"]:
                first = response_body["messages"][0]
                if isinstance(first, dict) and "id" in first:
                    return str(first["id"])
            for nested in ("data", "result", "message"):
                nested_val = response_body.get(nested)
                if isinstance(nested_val, dict):
                    res = cls.extract_provider_message_id(nested_val)
                    if res:
                        return res
        return None

    @classmethod
    async def send_whatsapp_message(
        cls,
        db: Session,
        conversation: Conversation,
        message_text: str,
        vendor_phone: str,
        recipient_phone: str,
        product_offer_id: Optional[int] = None,
        reply_to_message_id: Optional[int] = None,
        is_simulation: bool = False
    ) -> Message:
        """
        Sends message through official Meta API or Demo simulation.
        Saves initial state as PENDING in DB, updates to SENT with provider ID.
        """
        now = datetime.now(timezone.utc)
        clean_recipient_phone = recipient_phone.replace("+", "").replace("-", "").replace(" ", "")
        
        # Determine native reply context if replying to an existing message
        quoted_provider_id = None
        if reply_to_message_id:
            parent_msg = db.query(Message).filter(Message.id == reply_to_message_id).first()
            if parent_msg and parent_msg.whatsapp_message_id:
                quoted_provider_id = parent_msg.whatsapp_message_id

        # 1. Create DB message record in PENDING state
        db_message = Message(
            conversation_id=conversation.id,
            vendor_id=conversation.vendor_id,
            shopkeeper_id=conversation.shopkeeper_id,
            product_offer_id=product_offer_id or conversation.product_offer_id,
            whatsapp_message_id=None,
            provider_reply_to_id=quoted_provider_id,
            reply_to_message_id=reply_to_message_id,
            sender_phone=vendor_phone,
            recipient_phone=recipient_phone,
            direction="OUTBOUND",
            message_text=message_text,
            message_timestamp=now,
            created_at=now,
            delivery_status="PENDING",
            reply_link_type="EXACT" if reply_to_message_id else "NONE",
            is_demo=is_simulation or settings.DEMO_MODE
        )
        db.add(db_message)
        db.commit()
        db.refresh(db_message)

        # Record initial status in history
        status_entry_pending = MessageStatusHistory(
            message_id=db_message.id,
            status="PENDING",
            status_timestamp=now,
            provider_event_id=None,
            created_at=now
        )
        db.add(status_entry_pending)
        db.commit()

        # 2. Attempt real WhatsApp dispatch (NMVE Gateway or Meta Cloud API)
        real_sent = False
        provider_msg_id = None
        
        target_phone = cls.clean_whatsapp_phone(recipient_phone)
        if getattr(settings, "WHATSAPP_TEST_MODE", False) and getattr(settings, "WHATSAPP_TEST_NUMBER", ""):
            test_phone = cls.clean_whatsapp_phone(settings.WHATSAPP_TEST_NUMBER)
            if test_phone:
                logger.info(f"WHATSAPP TEST MODE: redirecting {target_phone} -> {test_phone}")
                target_phone = test_phone

        if not is_simulation and settings.WHATSAPP_API_KEY and not settings.WHATSAPP_API_KEY.startswith("mock"):
            # Check if using NMVE Gateway (default) or Meta Graph API
            is_meta = bool(settings.WHATSAPP_PHONE_NUMBER_ID and settings.WHATSAPP_API_KEY.startswith("EAA"))
            
            if is_meta:
                api_url = f"https://graph.facebook.com/{settings.META_GRAPH_API_VERSION}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
                headers = {
                    "Authorization": f"Bearer {settings.WHATSAPP_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload: Dict[str, Any] = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": target_phone,
                    "type": "text",
                    "text": {"body": message_text}
                }
                if quoted_provider_id:
                    payload["context"] = {"message_id": quoted_provider_id}
            else:
                # NMVE Gateway integration
                api_url = getattr(settings, "WHATSAPP_BASE_URL", "https://nmve.io/whatsapp/api/integrations/whatsapp/messages")
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                    "Authorization": f"Bearer {settings.WHATSAPP_API_KEY}",
                    "api-key": settings.WHATSAPP_API_KEY
                }
                payload = {
                    "to": target_phone,
                    "type": "text",
                    "text": {"body": message_text},
                    "referenceId": f"vendor-{conversation.vendor_id}-offer-{product_offer_id or 0}-msg-{db_message.id}"
                }
                if getattr(settings, "WHATSAPP_CALLBACK_URL", ""):
                    payload["callbackUrl"] = settings.WHATSAPP_CALLBACK_URL
                if quoted_provider_id:
                    payload["context"] = {"message_id": quoted_provider_id}

            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(api_url, json=payload, headers=headers)
                    logger.info(f"WhatsApp API POST {api_url} -> Status {resp.status_code}: {resp.text}")
                    if resp.status_code in (200, 201, 202):
                        data = resp.json()
                        extracted_id = cls.extract_provider_message_id(data)
                        if extracted_id:
                            provider_msg_id = extracted_id
                            real_sent = True
                            db_message.is_demo = False
                    else:
                        logger.warning(f"WhatsApp API returned HTTP {resp.status_code}: {resp.text}. Falling back to demo dispatch.")
            except Exception as e:
                logger.error(f"Error calling WhatsApp API: {e}. Falling back to demo mode provider dispatch.")

        # 3. Fallback or Demo Dispatch
        if not provider_msg_id:
            provider_msg_id = cls.generate_provider_message_id()
            db_message.is_demo = True

        # Update message to SENT with provider ID
        sent_time = datetime.now(timezone.utc)
        db_message.whatsapp_message_id = provider_msg_id
        db_message.delivery_status = "SENT"
        db_message.actual_sent_timestamp = sent_time
        
        status_entry_sent = MessageStatusHistory(
            message_id=db_message.id,
            status="SENT",
            status_timestamp=sent_time,
            provider_event_id=f"evt_sent_{uuid.uuid4().hex[:8]}",
            created_at=sent_time
        )
        db.add(status_entry_sent)

        # Update conversation last message timestamp & lead status
        conversation.last_message_at = sent_time
        if conversation.lead_status == "INTERESTED":
            conversation.lead_status = "CONTACTED"
        
        db.commit()
        db.refresh(db_message)

        # Broadcast event over WebSocket
        await ws_manager.broadcast("message_sent", {
            "message_id": db_message.id,
            "conversation_id": conversation.id,
            "delivery_status": db_message.delivery_status,
            "whatsapp_message_id": db_message.whatsapp_message_id,
            "is_demo": db_message.is_demo
        })

        return db_message

    @classmethod
    async def update_delivery_status(
        cls,
        db: Session,
        whatsapp_message_id: str,
        new_status: str,
        event_timestamp: Optional[datetime] = None,
        provider_event_id: Optional[str] = None
    ) -> Optional[Message]:
        """
        Updates delivery status (SENT, DELIVERED, READ, FAILED) based on Meta webhook or simulation.
        Preserves timeline in message_status_history.
        """
        msg = db.query(Message).filter(Message.whatsapp_message_id == whatsapp_message_id).first()
        if not msg:
            logger.warning(f"No message found for whatsapp_message_id: {whatsapp_message_id}")
            return None

        event_time = event_timestamp or datetime.now(timezone.utc)

        # Avoid redundant duplicate status updates
        existing = db.query(MessageStatusHistory).filter(
            MessageStatusHistory.message_id == msg.id,
            MessageStatusHistory.status == new_status
        ).first()

        if not existing:
            status_history_record = MessageStatusHistory(
                message_id=msg.id,
                status=new_status,
                status_timestamp=event_time,
                provider_event_id=provider_event_id,
                created_at=datetime.now(timezone.utc)
            )
            db.add(status_history_record)

        msg.delivery_status = new_status
        db.commit()
        db.refresh(msg)

        # Broadcast status update
        await ws_manager.broadcast("status_updated", {
            "message_id": msg.id,
            "conversation_id": msg.conversation_id,
            "delivery_status": new_status,
            "whatsapp_message_id": whatsapp_message_id,
            "timestamp": event_time.isoformat()
        })

        return msg

    @classmethod
    async def process_inbound_message(
        cls,
        db: Session,
        sender_phone: str,
        recipient_phone: str,
        message_text: str,
        whatsapp_message_id: str,
        message_timestamp: datetime,
        context_reply_to_id: Optional[str] = None,
        is_demo: bool = False
    ) -> Tuple[Message, Conversation]:
        """
        Processes inbound message from webhook or simulation.
        Idempotent: skips if whatsapp_message_id already exists.
        Matches shopkeeper by phone.
        Finds or links reply_to_message_id using context_reply_to_id.
        """
        # Idempotency check
        existing_msg = db.query(Message).filter(Message.whatsapp_message_id == whatsapp_message_id).first()
        if existing_msg:
            logger.info(f"Duplicate incoming message webhook ignored: {whatsapp_message_id}")
            conv = db.query(Conversation).filter(Conversation.id == existing_msg.conversation_id).first()
            return existing_msg, conv

        # Find shopkeeper by phone number (flexible matching with/without country code)
        clean_phone = sender_phone.replace("+", "").replace("-", "").replace(" ", "")
        shopkeepers = db.query(Shopkeeper).all()
        matching_shopkeepers = []
        for sk in shopkeepers:
            sk_clean = sk.whatsapp_phone.replace("+", "").replace("-", "").replace(" ", "")
            if sk_clean == clean_phone or sk_clean.endswith(clean_phone) or clean_phone.endswith(sk_clean):
                matching_shopkeepers.append(sk)

        shopkeeper = None
        conversation = None

        if matching_shopkeepers:
            # 1. If native reply context exists, find parent message's conversation
            if context_reply_to_id:
                parent_msg = db.query(Message).filter(Message.whatsapp_message_id == context_reply_to_id).first()
                if parent_msg and parent_msg.shopkeeper:
                    shopkeeper = parent_msg.shopkeeper
                    conversation = parent_msg.conversation

            # 2. Otherwise pick shopkeeper with the most recent conversation
            if not conversation:
                sk_ids = [s.id for s in matching_shopkeepers]
                conversation = db.query(Conversation).filter(
                    Conversation.shopkeeper_id.in_(sk_ids)
                ).order_by(Conversation.last_message_at.desc()).first()
                if conversation:
                    shopkeeper = conversation.shopkeeper
                else:
                    shopkeeper = matching_shopkeepers[0]
        else:
            # Register unknown shopkeeper on the fly
            shopkeeper = Shopkeeper(
                shopkeeper_name=f"Shopkeeper ({sender_phone})",
                shop_name="Direct WhatsApp Inquiry",
                whatsapp_phone=sender_phone,
                location="India",
                lead_status="INTERESTED"
            )
            db.add(shopkeeper)
            db.commit()
            db.refresh(shopkeeper)

        if not conversation:
            # Find or create active conversation
            conversation = db.query(Conversation).filter(
                Conversation.shopkeeper_id == shopkeeper.id
            ).order_by(Conversation.updated_at.desc()).first()

        if not conversation:
            # Default vendor is 1
            conversation = Conversation(
                vendor_id=1,
                shopkeeper_id=shopkeeper.id,
                status="ACTIVE",
                lead_status="INTERESTED",
                created_at=datetime.now(timezone.utc),
                last_message_at=message_timestamp
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)

        # 4. Check native reply reference (context_reply_to_id)
        reply_to_msg = None
        reply_link_type = "NONE"
        inferred_confidence = None
        inferred_reason = None
        target_offer_id = conversation.product_offer_id

        if context_reply_to_id:
            # Search by provider ID
            reply_to_msg = db.query(Message).filter(Message.whatsapp_message_id == context_reply_to_id).first()
            if reply_to_msg:
                reply_link_type = "EXACT"
                if reply_to_msg.product_offer_id:
                    target_offer_id = reply_to_msg.product_offer_id
            else:
                reply_link_type = "NONE"

        # If not exact reply, check if AI can infer context
        if reply_link_type == "NONE":
            from .ai_service import infer_message_context_ai
            active_offers = db.query(ProductOffer).filter(ProductOffer.status == "ACTIVE").all()
            recent_msgs = db.query(Message).filter(
                Message.conversation_id == conversation.id
            ).order_by(Message.message_timestamp.desc()).limit(5).all()

            offers_data = [{"id": o.id, "product_name": o.product_name, "category": o.category, "selling_price": o.selling_price, "available_quantity": o.available_quantity} for o in active_offers]
            msgs_data = [{"id": m.id, "direction": m.direction, "text": m.message_text} for m in reversed(recent_msgs)]

            ai_res = infer_message_context_ai(message_text, offers_data, msgs_data)
            if ai_res.get("inferred"):
                reply_link_type = "INFERRED"
                inferred_confidence = ai_res.get("confidence")
                inferred_reason = ai_res.get("reason")
                if ai_res.get("target_offer_id"):
                    target_offer_id = ai_res.get("target_offer_id")
                if ai_res.get("target_message_id"):
                    reply_to_msg = db.query(Message).filter(Message.id == ai_res.get("target_message_id")).first()

        # 5. Save incoming message
        now = datetime.now(timezone.utc)
        inbound_message = Message(
            conversation_id=conversation.id,
            vendor_id=conversation.vendor_id,
            shopkeeper_id=shopkeeper.id,
            product_offer_id=target_offer_id,
            whatsapp_message_id=whatsapp_message_id,
            provider_reply_to_id=context_reply_to_id,
            reply_to_message_id=reply_to_msg.id if reply_to_msg else None,
            sender_phone=sender_phone,
            recipient_phone=recipient_phone,
            direction="INBOUND",
            message_text=message_text,
            message_timestamp=message_timestamp or now,
            created_at=now,
            delivery_status="DELIVERED", # Incoming message delivered to system
            reply_link_type=reply_link_type,
            is_demo=is_demo,
            inferred_confidence=inferred_confidence,
            inferred_reason=inferred_reason
        )
        db.add(inbound_message)

        # Update conversation
        conversation.last_message_at = message_timestamp or now
        conversation.updated_at = now
        if target_offer_id and not conversation.product_offer_id:
            conversation.product_offer_id = target_offer_id
        if conversation.lead_status in ("INTERESTED", "CONTACTED"):
            conversation.lead_status = "NEGOTIATING"

        db.commit()
        db.refresh(inbound_message)

        # Record status
        status_entry = MessageStatusHistory(
            message_id=inbound_message.id,
            status="DELIVERED",
            status_timestamp=message_timestamp or now,
            provider_event_id=f"evt_inbound_{uuid.uuid4().hex[:8]}",
            created_at=now
        )
        db.add(status_entry)
        db.commit()

        # Broadcast incoming message
        await ws_manager.broadcast("incoming_message", {
            "message_id": inbound_message.id,
            "conversation_id": conversation.id,
            "shopkeeper_name": shopkeeper.shopkeeper_name,
            "shop_name": shopkeeper.shop_name,
            "message_text": inbound_message.message_text,
            "direction": "INBOUND",
            "reply_link_type": reply_link_type,
            "reply_to_message_id": inbound_message.reply_to_message_id,
            "is_demo": is_demo
        })

        return inbound_message, conversation
