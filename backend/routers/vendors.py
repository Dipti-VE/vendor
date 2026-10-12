from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Dict, Any

from ..database import get_db
from ..models import Vendor, ProductOffer, Shopkeeper, OfferInterest, Conversation, Message
from ..schemas import VendorResponse

router = APIRouter(prefix="/vendors", tags=["Vendors"])

@router.get("/me", response_model=VendorResponse)
def get_vendor_profile(db: Session = Depends(get_db)):
    vendor = db.query(Vendor).first()
    if not vendor:
        # Create default vendor if none exists
        vendor = Vendor(
            id=1,
            name="Rajesh Sharma",
            company_name="GreenPack Solutions India Pvt Ltd",
            phone_number="+919876543210",
            email="sales@greenpacksolutions.in"
        )
        db.add(vendor)
        db.commit()
        db.refresh(vendor)
    return vendor

@router.get("/metrics")
def get_dashboard_metrics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    vendor = db.query(Vendor).first()
    vendor_id = vendor.id if vendor else 1

    total_offers = db.query(ProductOffer).filter(ProductOffer.vendor_id == vendor_id).count()
    active_offers = db.query(ProductOffer).filter(
        ProductOffer.vendor_id == vendor_id,
        ProductOffer.status == "ACTIVE"
    ).count()

    total_shopkeepers = db.query(Shopkeeper).count()
    
    # Explicit interested count
    total_interests = db.query(OfferInterest).count()
    
    # Active conversations
    active_conversations = db.query(Conversation).filter(
        Conversation.vendor_id == vendor_id,
        Conversation.status == "ACTIVE"
    ).count()

    # Outbound and Inbound message counts
    outgoing_messages = db.query(Message).filter(
        Message.vendor_id == vendor_id,
        Message.direction == "OUTBOUND"
    ).count()

    incoming_messages = db.query(Message).filter(
        Message.vendor_id == vendor_id,
        Message.direction == "INBOUND"
    ).count()

    # Delivery stats
    delivered_count = db.query(Message).filter(
        Message.vendor_id == vendor_id,
        Message.direction == "OUTBOUND",
        Message.delivery_status.in_(["DELIVERED", "READ"])
    ).count()

    read_count = db.query(Message).filter(
        Message.vendor_id == vendor_id,
        Message.direction == "OUTBOUND",
        Message.delivery_status == "READ"
    ).count()

    delivery_rate = round((delivered_count / outgoing_messages * 100), 1) if outgoing_messages > 0 else 100.0

    # Conversions count
    converted_leads = db.query(Conversation).filter(
        Conversation.vendor_id == vendor_id,
        Conversation.lead_status == "CONVERTED"
    ).count()

    return {
        "total_offers": total_offers,
        "active_offers": active_offers,
        "total_shopkeepers": total_shopkeepers,
        "explicit_interests": total_interests,
        "active_conversations": active_conversations,
        "outgoing_messages": outgoing_messages,
        "incoming_messages": incoming_messages,
        "total_messages": outgoing_messages + incoming_messages,
        "delivered_count": delivered_count,
        "read_count": read_count,
        "delivery_rate": delivery_rate,
        "converted_leads": converted_leads
    }
