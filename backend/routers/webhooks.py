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

    # 1. Handle Meta WhatsApp Cloud format
    if body.get("object") == "whatsapp_business_account":
        entries = body.get("entry", [])
        for entry in entries:
            changes = entry.get("changes", [])
            for change in changes:
                value = change.get("value", {})
                metadata = value.get("metadata", {})
                vendor_display_phone = metadata.get("display_phone_number", "+919876543210")

                # Process delivery status updates (sent, delivered, read, failed)
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

                # Process incoming messages
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

    # 2. Handle NMVE / Custom WhatsApp Webhook format
    def find_value(data, keys):
        if isinstance(data, dict):
            for key in keys:
                value = data.get(key)
                if isinstance(value, (str, int, float)) and str(value).strip():
                    return str(value).strip()
            for nested in data.values():
                result = find_value(nested, keys)
                if result:
                    return result
        elif isinstance(data, list):
            for nested in data:
                result = find_value(nested, keys)
                if result:
                    return result
        return None

    phone = WhatsAppService.clean_whatsapp_phone(
        find_value(body, ["from", "phone", "sender", "wa_id", "waId", "phoneNumber", "fromNumber"])
    )
    text_message = find_value(body, ["text", "body", "messageText", "content"]) or ""
    reference_id = find_value(body, ["referenceId", "reference_id", "reference"])
    provider_msg_id = find_value(body, ["messageId", "message_id", "externalMessageId", "external_message_id", "id"])
    raw_status = (find_value(body, ["status", "delivery_status", "deliveryStatus"]) or "").upper()

    logger.info(f"NMVE Webhook received: phone={phone}, msg_id={provider_msg_id}, status={raw_status}, text={text_message[:40] if text_message else ''}")

    # Check if delivery status event (SENT, DELIVERED, READ, FAILED)
    if raw_status in ("SENT", "DELIVERED", "READ", "FAILED") and provider_msg_id and not text_message:
        await WhatsAppService.update_delivery_status(
            db=db,
            whatsapp_message_id=provider_msg_id,
            new_status=raw_status,
            event_timestamp=datetime.now(timezone.utc),
            provider_event_id=f"nmve_evt_{provider_msg_id}_{raw_status}"
        )
        return Response(content="STATUS_UPDATED", status_code=200)

    # If incoming text message
    if phone and text_message:
        context_reply_to_id = None
        context_val = body.get("context")
        if isinstance(context_val, dict) and "id" in context_val:
            context_reply_to_id = context_val["id"]

        await WhatsAppService.process_inbound_message(
            db=db,
            sender_phone=phone,
            recipient_phone="+919876543210",
            message_text=text_message,
            whatsapp_message_id=provider_msg_id or WhatsAppService.generate_provider_message_id(),
            message_timestamp=datetime.now(timezone.utc),
            context_reply_to_id=context_reply_to_id,
            is_demo=False
        )
        return Response(content="INBOUND_PROCESSED", status_code=200)

    return Response(content="EVENT_RECEIVED", status_code=200)
