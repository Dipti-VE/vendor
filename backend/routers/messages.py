from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from datetime import datetime, timezone

from ..database import get_db
from ..models import Message, MessageStatusHistory, Shopkeeper, ProductOffer
from ..schemas import MessageResponse, MessageStatusHistoryResponse, MessageQuotedSummary

router = APIRouter(prefix="/messages", tags=["Messages & Audit Trail"])

def to_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if not dt:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

def format_message_audit(msg: Message, db: Session) -> MessageResponse:
    quoted = None
    if msg.reply_to_message_id:
        parent = db.query(Message).filter(Message.id == msg.reply_to_message_id).first()
        if parent:
            # Safeguard: if an INBOUND message points to another INBOUND message (customer quoting themselves),
            # resolve instead to the actual preceding OUTBOUND message from the vendor
            if msg.direction == "INBOUND" and parent.direction == "INBOUND":
                parent = db.query(Message).filter(
                    Message.conversation_id == msg.conversation_id,
                    Message.direction == "OUTBOUND",
                    Message.message_timestamp <= msg.message_timestamp
                ).order_by(Message.message_timestamp.desc()).first()

            if parent and parent.id != msg.id:
                quoted = MessageQuotedSummary(
                    id=parent.id,
                    message_text=parent.message_text,
                    sender_phone=parent.sender_phone,
                    direction=parent.direction,
                    message_timestamp=to_utc(parent.message_timestamp)
                )

    return MessageResponse(
        id=msg.id,
        conversation_id=msg.conversation_id,
        vendor_id=msg.vendor_id,
        shopkeeper_id=msg.shopkeeper_id,
        shopkeeper_name=msg.shopkeeper.shopkeeper_name if msg.shopkeeper else None,
        shop_name=msg.shopkeeper.shop_name if msg.shopkeeper else None,
        product_offer_id=msg.product_offer_id,
        product_name=msg.product_offer.product_name if msg.product_offer else None,
        whatsapp_message_id=msg.whatsapp_message_id,
        provider_reply_to_id=msg.provider_reply_to_id,
        reply_to_message_id=msg.reply_to_message_id,
        quoted_message=quoted,
        sender_phone=msg.sender_phone,
        recipient_phone=msg.recipient_phone,
        direction=msg.direction,
        message_text=msg.message_text,
        message_timestamp=to_utc(msg.message_timestamp),
        actual_sent_timestamp=to_utc(msg.actual_sent_timestamp),
        created_at=to_utc(msg.created_at),
        delivery_status=msg.delivery_status,
        reply_link_type=msg.reply_link_type,
        is_demo=msg.is_demo,
        inferred_confidence=msg.inferred_confidence,
        inferred_reason=msg.inferred_reason,
        status_history=[
            MessageStatusHistoryResponse(
                id=h.id,
                message_id=h.message_id,
                status=h.status,
                status_timestamp=to_utc(h.status_timestamp),
                provider_event_id=h.provider_event_id,
                created_at=to_utc(h.created_at)
            )
            for h in (msg.status_history or [])
        ]
    )

@router.get("", response_model=List[MessageResponse])
def get_all_messages(
    shopkeeper_id: Optional[int] = Query(None, description="Filter by shopkeeper ID"),
    offer_id: Optional[int] = Query(None, description="Filter by product offer ID"),
    direction: Optional[str] = Query(None, description="Filter by direction: INBOUND, OUTBOUND"),
    delivery_status: Optional[str] = Query(None, description="Filter by status: PENDING, SENT, DELIVERED, READ, FAILED"),
    reply_link_type: Optional[str] = Query(None, description="Filter by reply type: EXACT, INFERRED, NONE"),
    search: Optional[str] = Query(None, description="Search text in message body"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    query = db.query(Message)

    if shopkeeper_id:
        query = query.filter(Message.shopkeeper_id == shopkeeper_id)
    if offer_id:
        query = query.filter(Message.product_offer_id == offer_id)
    if direction:
        query = query.filter(Message.direction == direction)
    if delivery_status:
        query = query.filter(Message.delivery_status == delivery_status)
    if reply_link_type:
        query = query.filter(Message.reply_link_type == reply_link_type)
    if search:
        query = query.filter(Message.message_text.ilike(f"%{search}%"))

    messages = query.order_by(Message.message_timestamp.desc()).limit(limit).all()
    return [format_message_audit(m, db) for m in messages]

@router.get("/{message_id}", response_model=MessageResponse)
def get_message_detail(message_id: int, db: Session = Depends(get_db)):
    msg = db.query(Message).filter(Message.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    return format_message_audit(msg, db)

@router.get("/{message_id}/status-history", response_model=List[MessageStatusHistoryResponse])
def get_message_status_history(message_id: int, db: Session = Depends(get_db)):
    msg = db.query(Message).filter(Message.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    history = db.query(MessageStatusHistory).filter(
        MessageStatusHistory.message_id == message_id
    ).order_by(MessageStatusHistory.status_timestamp.asc()).all()

    return [
        MessageStatusHistoryResponse(
            id=h.id,
            message_id=h.message_id,
            status=h.status,
            status_timestamp=to_utc(h.status_timestamp),
            provider_event_id=h.provider_event_id,
            created_at=to_utc(h.created_at)
        )
        for h in history
    ]
