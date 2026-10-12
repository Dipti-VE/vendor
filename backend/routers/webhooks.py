from fastapi import APIRouter, Request, Response, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import logging

from ..config import settings
from ..database import get_db
from ..services.whatsapp_service import WhatsAppService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhooks/whatsapp", tags=["Meta WhatsApp Webhook"])

@router.get("")
def verify_meta_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    """
    Official Meta webhook verification endpoint.
    Meta sends GET request with hub.mode, hub.challenge, and hub.verify_token.
    """
    logger.info(f"Webhook verification request: mode={hub_mode}, token={hub_verify_token}")
    if hub_mode == "subscribe" and hub_verify_token == settings.WEBHOOK_VERIFY_TOKEN:
        logger.info("Meta Webhook verification succeeded!")
        return Response(content=hub_challenge, media_type="text/plain", status_code=200)
    
    logger.warning("Meta Webhook verification failed. Token mismatch.")
    raise HTTPException(status_code=403, detail="Verification token mismatch")

@router.post("")
async def receive_meta_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Official Meta webhook receiver for incoming messages and delivery status updates.
    """
    try:
        body = await request.json()
    except Exception as e:
        logger.error(f"Invalid JSON in webhook payload: {e}")
        return Response(content="INVALID_JSON", status_code=400)

    # Validate that it is a WhatsApp Business Account event
    if body.get("object") != "whatsapp_business_account":
        logger.warning(f"Unrecognized webhook object: {body.get('object')}")
        return Response(content="IGNORED", status_code=200)

    entries = body.get("entry", [])
    for entry in entries:
        changes = entry.get("changes", [])
        for change in changes:
            value = change.get("value", {})
            metadata = value.get("metadata", {})
            vendor_display_phone = metadata.get("display_phone_number", "+919876543210")

            # 1. Process delivery status updates (sent, delivered, read, failed)
            statuses = value.get("statuses", [])
            for st in statuses:
                provider_msg_id = st.get("id")
                raw_status = st.get("status", "").upper()
                timestamp_epoch = int(st.get("timestamp", 0))
                event_time = datetime.fromtimestamp(timestamp_epoch, tz=timezone.utc) if timestamp_epoch else datetime.now(timezone.utc)
                
                status_map = {
                    "SENT": "SENT",
                    "DELIVERED": "DELIVERED",
                    "READ": "READ",
                    "FAILED": "FAILED"
                }
                normalized_status = status_map.get(raw_status, raw_status)
                
                await WhatsAppService.update_delivery_status(
                    db=db,
                    whatsapp_message_id=provider_msg_id,
                    new_status=normalized_status,
                    event_timestamp=event_time,
                    provider_event_id=f"meta_evt_{provider_msg_id}_{normalized_status}"
                )

            # 2. Process incoming messages
            messages = value.get("messages", [])
            for msg_item in messages:
                msg_type = msg_item.get("type", "text")
                sender_phone = msg_item.get("from")
                provider_msg_id = msg_item.get("id")
                timestamp_epoch = int(msg_item.get("timestamp", 0))
                msg_time = datetime.fromtimestamp(timestamp_epoch, tz=timezone.utc) if timestamp_epoch else datetime.now(timezone.utc)

                text_body = ""
                if msg_type == "text":
                    text_body = msg_item.get("text", {}).get("body", "")
                elif msg_type == "button":
                    text_body = msg_item.get("button", {}).get("text", "")
                elif msg_type == "interactive":
                    interactive_obj = msg_item.get("interactive", {})
                    text_body = interactive_obj.get("list_reply", {}).get("title") or interactive_obj.get("button_reply", {}).get("title", "")
                else:
                    text_body = f"[{msg_type} message received]"

                # Check native WhatsApp reply context
                context_reply_to_id = None
                context_data = msg_item.get("context")
                if context_data and "id" in context_data:
                    context_reply_to_id = context_data.get("id")

                await WhatsAppService.process_inbound_message(
                    db=db,
                    sender_phone=sender_phone,
                    recipient_phone=vendor_display_phone,
                    message_text=text_body,
                    whatsapp_message_id=provider_msg_id,
                    message_timestamp=msg_time,
                    context_reply_to_id=context_reply_to_id,
                    is_demo=False
                )

    return Response(content="EVENT_RECEIVED", status_code=200)
