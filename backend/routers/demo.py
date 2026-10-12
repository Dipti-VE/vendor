import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from ..database import get_db
from ..models import Shopkeeper, Message, Conversation, Vendor, ProductOffer, MessageStatusHistory
from ..schemas import SimulateInboundMessageRequest, SimulateStatusChangeRequest, MessageResponse
from ..services.whatsapp_service import WhatsAppService
from ..services.connection_manager import ws_manager
from ..routers.conversations import format_message_response

router = APIRouter(prefix="/demo", tags=["Demo Mode Simulator"])

@router.post("/simulate-inbound", response_model=MessageResponse)
async def simulate_inbound_reply(payload: SimulateInboundMessageRequest, db: Session = Depends(get_db)):
    """
    Simulates a shopkeeper sending an incoming WhatsApp message.
    Can simulate both WhatsApp native reply (with context.id) and regular message.
    Labels the message as simulated demo data (is_demo=True).
    """
    shopkeeper = db.query(Shopkeeper).filter(Shopkeeper.id == payload.shopkeeper_id).first()
    if not shopkeeper:
        raise HTTPException(status_code=404, detail="Shopkeeper not found")

    vendor = db.query(Vendor).first()
    vendor_phone = vendor.phone_number if vendor else "+919876543210"

    # Simulated provider message ID
    simulated_wamid = f"wamid.HBgM_SIM_{uuid.uuid4().hex[:12].upper()}"

    # Determine simulated context.id if native reply
    context_reply_id = None
    if payload.use_native_reply and payload.reply_to_message_id:
        parent_msg = db.query(Message).filter(Message.id == payload.reply_to_message_id).first()
        if parent_msg:
            context_reply_id = parent_msg.whatsapp_message_id or f"wamid.HBgM_REF_{parent_msg.id}"

    now = datetime.now(timezone.utc)
    inbound_msg, conv = await WhatsAppService.process_inbound_message(
        db=db,
        sender_phone=shopkeeper.whatsapp_phone,
        recipient_phone=vendor_phone,
        message_text=payload.message_text,
        whatsapp_message_id=simulated_wamid,
        message_timestamp=now,
        context_reply_to_id=context_reply_id,
        is_demo=True
    )

    return format_message_response(inbound_msg, db)

@router.post("/simulate-status", response_model=MessageResponse)
async def simulate_delivery_status(payload: SimulateStatusChangeRequest, db: Session = Depends(get_db)):
    """
    Simulates status updates (SENT -> DELIVERED -> READ -> FAILED) for a message.
    """
    msg = db.query(Message).filter(Message.id == payload.message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    valid_statuses = ["PENDING", "SENT", "DELIVERED", "READ", "FAILED"]
    status_upper = payload.new_status.upper()
    if status_upper not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of {valid_statuses}")

    now = datetime.now(timezone.utc)
    updated_msg = await WhatsAppService.update_delivery_status(
        db=db,
        whatsapp_message_id=msg.whatsapp_message_id or f"wamid.HBgM_{msg.id}",
        new_status=status_upper,
        event_timestamp=now,
        provider_event_id=f"demo_evt_{uuid.uuid4().hex[:8]}"
    )

    return format_message_response(updated_msg, db)

@router.post("/reset-seed")
def reset_seed_data(db: Session = Depends(get_db)):
    """
    Resets the database with rich packaging marketplace sample data.
    """
    from ..seed_data import seed_database
    seed_database(db, reset=True)
    return {"message": "Database successfully reset and re-seeded with demo data"}
