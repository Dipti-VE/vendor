from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from datetime import datetime, timezone

from ..database import get_db
from ..models import Conversation, Message, Shopkeeper, ProductOffer, Vendor, MessageStatusHistory
from ..schemas import (
    ConversationResponse, ConversationLeadStatusUpdate,
    MessageResponse, MessageSendRequest, MessageQuotedSummary,
    MessageStatusHistoryResponse,
    AIDraftRequest, AIDraftResponse
)
from ..services.whatsapp_service import WhatsAppService
from ..services.ai_service import generate_smart_reply_draft_ai
from ..services.connection_manager import ws_manager

router = APIRouter(prefix="/conversations", tags=["Conversations & WhatsApp Inbox"])

def to_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if not dt:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

def format_message_response(msg: Message, db: Session) -> MessageResponse:
    # Resolve quoted message if any
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

@router.get("", response_model=List[ConversationResponse])
def get_conversations(
    search: Optional[str] = Query(None, description="Search by shopkeeper name, shop name, or phone"),
    offer_id: Optional[int] = Query(None, description="Filter by product offer ID"),
    lead_status: Optional[str] = Query(None, description="Filter by lead status"),
    db: Session = Depends(get_db)
):
    query = db.query(Conversation)

    if offer_id:
        query = query.filter(Conversation.product_offer_id == offer_id)
    if lead_status:
        query = query.filter(Conversation.lead_status == lead_status)

    if search:
        search_filter = f"%{search}%"
        query = query.join(Shopkeeper).filter(
            or_(
                Shopkeeper.shopkeeper_name.ilike(search_filter),
                Shopkeeper.shop_name.ilike(search_filter),
                Shopkeeper.whatsapp_phone.ilike(search_filter)
            )
        )

    conversations = query.order_by(Conversation.last_message_at.desc()).all()
    results = []

    for conv in conversations:
        # Latest message
        latest_msg = db.query(Message).filter(
            Message.conversation_id == conv.id
        ).order_by(Message.message_timestamp.desc()).first()

        latest_resp = format_message_response(latest_msg, db) if latest_msg else None
        
        # Total messages
        total_msg_count = db.query(Message).filter(Message.conversation_id == conv.id).count()

        # Unread incoming messages
        unread_count = db.query(Message).filter(
            Message.conversation_id == conv.id,
            Message.direction == "INBOUND",
            Message.delivery_status != "READ"
        ).count()

        results.append(ConversationResponse(
            id=conv.id,
            vendor_id=conv.vendor_id,
            shopkeeper_id=conv.shopkeeper_id,
            shopkeeper_name=conv.shopkeeper.shopkeeper_name,
            shop_name=conv.shopkeeper.shop_name,
            whatsapp_phone=conv.shopkeeper.whatsapp_phone,
            shopkeeper_location=conv.shopkeeper.location,
            product_offer_id=conv.product_offer_id,
            product_name=conv.product_offer.product_name if conv.product_offer else None,
            status=conv.status,
            lead_status=conv.lead_status,
            created_at=to_utc(conv.created_at),
            updated_at=to_utc(conv.updated_at),
            last_message_at=to_utc(conv.last_message_at),
            latest_message=latest_resp,
            unread_count=unread_count,
            total_messages=total_msg_count
        ))

    return results

@router.post("", response_model=ConversationResponse)
def get_or_create_conversation(
    shopkeeper_id: int = Query(...),
    product_offer_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    shopkeeper = db.query(Shopkeeper).filter(Shopkeeper.id == shopkeeper_id).first()
    if not shopkeeper:
        raise HTTPException(status_code=404, detail="Shopkeeper not found")

    vendor = db.query(Vendor).first()
    vendor_id = vendor.id if vendor else 1

    # Check if conversation already exists
    conv = db.query(Conversation).filter(
        Conversation.vendor_id == vendor_id,
        Conversation.shopkeeper_id == shopkeeper_id
    ).first()

    now = datetime.now(timezone.utc)
    if not conv:
        conv = Conversation(
            vendor_id=vendor_id,
            shopkeeper_id=shopkeeper_id,
            product_offer_id=product_offer_id,
            status="ACTIVE",
            lead_status="INTERESTED",
            created_at=now,
            updated_at=now,
            last_message_at=now
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
    elif product_offer_id and not conv.product_offer_id:
        conv.product_offer_id = product_offer_id
        conv.updated_at = now
        db.commit()
        db.refresh(conv)

    return ConversationResponse(
        id=conv.id,
        vendor_id=conv.vendor_id,
        shopkeeper_id=conv.shopkeeper_id,
        shopkeeper_name=conv.shopkeeper.shopkeeper_name,
        shop_name=conv.shopkeeper.shop_name,
        whatsapp_phone=conv.shopkeeper.whatsapp_phone,
        shopkeeper_location=conv.shopkeeper.location,
        product_offer_id=conv.product_offer_id,
        product_name=conv.product_offer.product_name if conv.product_offer else None,
        status=conv.status,
        lead_status=conv.lead_status,
        created_at=to_utc(conv.created_at),
        updated_at=to_utc(conv.updated_at),
        last_message_at=to_utc(conv.last_message_at),
        latest_message=None,
        unread_count=0,
        total_messages=0
    )

@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
def get_conversation_messages(conversation_id: int, db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.message_timestamp.asc()).all()

    # Mark incoming unread messages as READ when vendor views conversation
    has_unread = False
    for m in messages:
        if m.direction == "INBOUND" and m.delivery_status != "READ":
            m.delivery_status = "READ"
            has_unread = True
    if has_unread:
        db.commit()

    return [format_message_response(m, db) for m in messages]

@router.post("/{conversation_id}/messages", response_model=MessageResponse)
async def send_conversation_message(
    conversation_id: int,
    payload: MessageSendRequest,
    db: Session = Depends(get_db)
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    vendor = db.query(Vendor).filter(Vendor.id == conv.vendor_id).first()
    vendor_phone = vendor.phone_number if vendor else "+919876543210"

    shopkeeper = db.query(Shopkeeper).filter(Shopkeeper.id == conv.shopkeeper_id).first()
    if not shopkeeper:
        raise HTTPException(status_code=404, detail="Shopkeeper not found")

    # Send outbound WhatsApp message
    db_message = await WhatsAppService.send_whatsapp_message(
        db=db,
        conversation=conv,
        message_text=payload.message_text,
        vendor_phone=vendor_phone,
        recipient_phone=shopkeeper.whatsapp_phone,
        product_offer_id=payload.product_offer_id or conv.product_offer_id,
        reply_to_message_id=payload.reply_to_message_id,
        is_simulation=payload.is_simulation or False,
        is_template=payload.is_template or False,
        template_name=payload.template_name or "hello_world"
    )

    return format_message_response(db_message, db)

@router.post("/{conversation_id}/initiate-template", response_model=MessageResponse)
async def initiate_conversation_template(
    conversation_id: int,
    template_name: Optional[str] = Query("hello_world"),
    db: Session = Depends(get_db)
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    vendor = db.query(Vendor).filter(Vendor.id == conv.vendor_id).first()
    vendor_phone = vendor.phone_number if vendor else "+919876543210"

    shopkeeper = db.query(Shopkeeper).filter(Shopkeeper.id == conv.shopkeeper_id).first()
    if not shopkeeper:
        raise HTTPException(status_code=404, detail="Shopkeeper not found")

    # Send outbound WhatsApp Template (hello_world)
    db_message = await WhatsAppService.send_whatsapp_message(
        db=db,
        conversation=conv,
        message_text="hello_world",
        vendor_phone=vendor_phone,
        recipient_phone=shopkeeper.whatsapp_phone,
        product_offer_id=conv.product_offer_id,
        is_simulation=False,
        is_template=True,
        template_name=template_name or "hello_world"
    )

    return format_message_response(db_message, db)

@router.patch("/{conversation_id}/status", response_model=ConversationResponse)
async def update_conversation_lead_status(
    conversation_id: int,
    payload: ConversationLeadStatusUpdate,
    db: Session = Depends(get_db)
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conv.lead_status = payload.lead_status
    conv.updated_at = datetime.now(timezone.utc)
    
    # Also update shopkeeper's overall lead status
    if conv.shopkeeper:
        conv.shopkeeper.lead_status = payload.lead_status

    db.commit()
    db.refresh(conv)

    await ws_manager.broadcast("lead_status_changed", {
        "conversation_id": conv.id,
        "shopkeeper_id": conv.shopkeeper_id,
        "new_status": payload.lead_status
    })

    return ConversationResponse(
        id=conv.id,
        vendor_id=conv.vendor_id,
        shopkeeper_id=conv.shopkeeper_id,
        shopkeeper_name=conv.shopkeeper.shopkeeper_name,
        shop_name=conv.shopkeeper.shop_name,
        whatsapp_phone=conv.shopkeeper.whatsapp_phone,
        shopkeeper_location=conv.shopkeeper.location,
        product_offer_id=conv.product_offer_id,
        product_name=conv.product_offer.product_name if conv.product_offer else None,
        status=conv.status,
        lead_status=conv.lead_status,
        created_at=to_utc(conv.created_at),
        updated_at=to_utc(conv.updated_at),
        last_message_at=to_utc(conv.last_message_at)
    )

@router.post("/{conversation_id}/ai-draft", response_model=AIDraftResponse)
def get_ai_message_draft(
    conversation_id: int,
    payload: AIDraftRequest,
    db: Session = Depends(get_db)
):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    offer_id = payload.product_offer_id or conv.product_offer_id
    offer = db.query(ProductOffer).filter(ProductOffer.id == offer_id).first() if offer_id else None

    offer_info = {}
    if offer:
        offer_info = {
            "product_name": offer.product_name,
            "category": offer.category,
            "selling_price": offer.selling_price,
            "available_quantity": offer.available_quantity,
            "minimum_order_quantity": offer.minimum_order_quantity
        }
    else:
        offer_info = {
            "product_name": "Packaging Supplies",
            "category": "Packaging",
            "selling_price": 1.0,
            "available_quantity": 10000,
            "minimum_order_quantity": 500
        }

    # Fetch up to 10 recent messages in chronological order
    recent_msgs = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.message_timestamp.desc()).limit(10).all()
    recent_msgs_chrono = list(reversed(recent_msgs))

    # Find the target message being responded to
    target_msg = None
    if payload.reply_to_message_id:
        target_msg = db.query(Message).filter(Message.id == payload.reply_to_message_id).first()

    # If not explicitly specified, find the most recent inbound message from the customer
    if not target_msg:
        for m in reversed(recent_msgs_chrono):
            if m.direction == "INBOUND":
                target_msg = m
                break

    # If still no inbound message, take the latest message
    if not target_msg and recent_msgs_chrono:
        target_msg = recent_msgs_chrono[-1]

    history = [f"{m.direction}: {m.message_text}" for m in recent_msgs_chrono]
    last_customer_text = target_msg.message_text if target_msg else None

    draft = generate_smart_reply_draft_ai(
        offer_info=offer_info,
        shopkeeper_name=conv.shopkeeper.shopkeeper_name,
        shop_name=conv.shopkeeper.shop_name,
        recent_history=history,
        last_customer_message=last_customer_text,
        intent=payload.intent
    )

    return AIDraftResponse(
        suggested_text=draft.get("suggested_text", ""),
        reasoning=draft.get("reasoning", ""),
        reply_to_message_id=target_msg.id if target_msg else None
    )
