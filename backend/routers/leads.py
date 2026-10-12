from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, List, Any

from ..database import get_db
from ..models import Conversation, Shopkeeper, ProductOffer, Message
from ..schemas import ConversationResponse
from .conversations import format_message_response

router = APIRouter(prefix="/leads", tags=["Lead Management"])

@router.get("/pipeline")
def get_lead_pipeline(db: Session = Depends(get_db)) -> Dict[str, List[Any]]:
    """
    Returns conversations grouped by lead status for Kanban pipeline board:
    - INTERESTED
    - CONTACTED
    - NEGOTIATING
    - CONVERTED
    - NOT_INTERESTED
    """
    statuses = ["INTERESTED", "CONTACTED", "NEGOTIATING", "CONVERTED", "NOT_INTERESTED"]
    pipeline = {s: [] for s in statuses}

    conversations = db.query(Conversation).order_by(Conversation.last_message_at.desc()).all()

    for conv in conversations:
        status_key = conv.lead_status if conv.lead_status in pipeline else "INTERESTED"
        
        # Get latest message
        latest_msg = db.query(Message).filter(
            Message.conversation_id == conv.id
        ).order_by(Message.message_timestamp.desc()).first()

        latest_preview = latest_msg.message_text if latest_msg else "No messages yet"
        latest_time = latest_msg.message_timestamp if latest_msg else conv.last_message_at

        item = {
            "conversation_id": conv.id,
            "shopkeeper_id": conv.shopkeeper_id,
            "shopkeeper_name": conv.shopkeeper.shopkeeper_name,
            "shop_name": conv.shopkeeper.shop_name,
            "whatsapp_phone": conv.shopkeeper.whatsapp_phone,
            "location": conv.shopkeeper.location,
            "product_offer_id": conv.product_offer_id,
            "product_name": conv.product_offer.product_name if conv.product_offer else None,
            "lead_status": conv.lead_status,
            "last_message_preview": latest_preview,
            "last_message_at": latest_time.isoformat() if latest_time else None
        }
        pipeline[status_key].append(item)

    return pipeline
