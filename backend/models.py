from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from .database import Base

def utc_now():
    return datetime.now(timezone.utc)

class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone_number = Column(String(30), nullable=False, unique=True)
    email = Column(String(100), nullable=True)
    company_name = Column(String(150), nullable=False)
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    product_offers = relationship("ProductOffer", back_populates="vendor")
    conversations = relationship("Conversation", back_populates="vendor")
    messages = relationship("Message", back_populates="vendor")


class Shopkeeper(Base):
    __tablename__ = "shopkeepers"

    id = Column(Integer, primary_key=True, index=True)
    shopkeeper_name = Column(String(100), nullable=False)
    shop_name = Column(String(150), nullable=False)
    whatsapp_phone = Column(String(30), nullable=False, index=True)
    location = Column(String(150), nullable=False)
    preferred_delivery_location = Column(String(150), nullable=True)
    lead_status = Column(String(50), default="INTERESTED") # INTERESTED, CONTACTED, NEGOTIATING, CONVERTED, NOT_INTERESTED
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    requirements = relationship("ShopkeeperRequirement", back_populates="shopkeeper", cascade="all, delete-orphan")
    interests = relationship("OfferInterest", back_populates="shopkeeper", cascade="all, delete-orphan")
    conversations = relationship("Conversation", back_populates="shopkeeper")
    messages = relationship("Message", back_populates="shopkeeper")


class ShopkeeperRequirement(Base):
    __tablename__ = "shopkeeper_requirements"

    id = Column(Integer, primary_key=True, index=True)
    shopkeeper_id = Column(Integer, ForeignKey("shopkeepers.id", ondelete="CASCADE"), nullable=False)
    product_name = Column(String(150), nullable=False)
    category = Column(String(100), nullable=False)
    required_quantity = Column(Integer, nullable=False)
    target_price = Column(Float, nullable=False)
    delivery_location = Column(String(150), nullable=True)
    created_at = Column(DateTime, default=utc_now)

    shopkeeper = relationship("Shopkeeper", back_populates="requirements")


class ProductOffer(Base):
    __tablename__ = "product_offers"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    product_name = Column(String(150), nullable=False)
    category = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    selling_price = Column(Float, nullable=False)
    available_quantity = Column(Integer, nullable=False)
    minimum_order_quantity = Column(Integer, nullable=False, default=1)
    location = Column(String(150), nullable=False)
    delivery_locations = Column(String(255), nullable=False)
    expiry_date = Column(DateTime, nullable=True)
    status = Column(String(30), default="ACTIVE")  # ACTIVE, PAUSED, EXPIRED
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    vendor = relationship("Vendor", back_populates="product_offers")
    interests = relationship("OfferInterest", back_populates="product_offer")
    conversations = relationship("Conversation", back_populates="product_offer")
    messages = relationship("Message", back_populates="product_offer")


class OfferInterest(Base):
    """
    Explicit interest expressed by a shopkeeper in a specific product offer.
    Separates explicit interest from automated algorithm matching.
    """
    __tablename__ = "offer_interests"

    id = Column(Integer, primary_key=True, index=True)
    product_offer_id = Column(Integer, ForeignKey("product_offers.id", ondelete="CASCADE"), nullable=False)
    shopkeeper_id = Column(Integer, ForeignKey("shopkeepers.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), default="INTERESTED") # INTERESTED, QUOTE_REQUESTED, SAMPLE_REQUESTED, CONVERTED
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)

    product_offer = relationship("ProductOffer", back_populates="interests")
    shopkeeper = relationship("Shopkeeper", back_populates="interests")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    shopkeeper_id = Column(Integer, ForeignKey("shopkeepers.id"), nullable=False)
    product_offer_id = Column(Integer, ForeignKey("product_offers.id"), nullable=True)
    status = Column(String(50), default="ACTIVE") # ACTIVE, ARCHIVED, CLOSED
    lead_status = Column(String(50), default="INTERESTED") # INTERESTED, CONTACTED, NEGOTIATING, CONVERTED, NOT_INTERESTED
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)
    last_message_at = Column(DateTime, default=utc_now)

    vendor = relationship("Vendor", back_populates="conversations")
    shopkeeper = relationship("Shopkeeper", back_populates="conversations")
    product_offer = relationship("ProductOffer", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", order_by="Message.message_timestamp")

    __table_args__ = (
        Index("idx_conversation_vendor_shopkeeper", "vendor_id", "shopkeeper_id"),
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    shopkeeper_id = Column(Integer, ForeignKey("shopkeepers.id"), nullable=False)
    product_offer_id = Column(Integer, ForeignKey("product_offers.id"), nullable=True)
    
    # Meta / WhatsApp identifiers
    whatsapp_message_id = Column(String(120), nullable=True, unique=True, index=True)
    provider_reply_to_id = Column(String(120), nullable=True, index=True)
    
    # Foreign key link to internal original message when replying
    reply_to_message_id = Column(Integer, ForeignKey("messages.id"), nullable=True, index=True)
    
    sender_phone = Column(String(30), nullable=False)
    recipient_phone = Column(String(30), nullable=False)
    direction = Column(String(20), nullable=False) # OUTBOUND, INBOUND
    message_text = Column(Text, nullable=False)
    
    message_timestamp = Column(DateTime, default=utc_now, index=True)
    actual_sent_timestamp = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    
    delivery_status = Column(String(30), default="PENDING") # PENDING, SENT, DELIVERED, READ, FAILED
    reply_link_type = Column(String(20), default="NONE") # EXACT, INFERRED, NONE
    
    is_demo = Column(Boolean, default=False)
    inferred_confidence = Column(Float, nullable=True)
    inferred_reason = Column(Text, nullable=True)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    vendor = relationship("Vendor", back_populates="messages")
    shopkeeper = relationship("Shopkeeper", back_populates="messages")
    product_offer = relationship("ProductOffer", back_populates="messages")
    
    # Self-referential relationship for replies
    parent_message = relationship("Message", remote_side=[id], backref="child_replies")
    status_history = relationship("MessageStatusHistory", back_populates="message", cascade="all, delete-orphan", order_by="MessageStatusHistory.status_timestamp")


class MessageStatusHistory(Base):
    __tablename__ = "message_status_history"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(30), nullable=False) # PENDING, SENT, DELIVERED, READ, FAILED
    status_timestamp = Column(DateTime, default=utc_now)
    provider_event_id = Column(String(120), nullable=True)
    created_at = Column(DateTime, default=utc_now)

    message = relationship("Message", back_populates="status_history")
