from typing import List, Optional, Any, Dict
from datetime import datetime
from pydantic import BaseModel, Field

# --- Vendor Schemas ---
class VendorBase(BaseModel):
    name: str
    phone_number: str
    email: Optional[str] = None
    company_name: str

class VendorResponse(VendorBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# --- Shopkeeper Requirement Schemas ---
class ShopkeeperRequirementBase(BaseModel):
    product_name: str
    category: str
    required_quantity: int
    target_price: float
    delivery_location: Optional[str] = None

class ShopkeeperRequirementCreate(ShopkeeperRequirementBase):
    pass

class ShopkeeperRequirementResponse(ShopkeeperRequirementBase):
    id: int
    shopkeeper_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# --- Shopkeeper Schemas ---
class ShopkeeperBase(BaseModel):
    shopkeeper_name: str
    shop_name: str
    whatsapp_phone: str
    location: str
    preferred_delivery_location: Optional[str] = None
    lead_status: Optional[str] = "INTERESTED"

class ShopkeeperCreate(ShopkeeperBase):
    requirements: Optional[List[ShopkeeperRequirementCreate]] = []

class ShopkeeperResponse(ShopkeeperBase):
    id: int
    created_at: datetime
    requirements: List[ShopkeeperRequirementResponse] = []

    class Config:
        from_attributes = True


# --- Product Offer Schemas ---
class ProductOfferBase(BaseModel):
    product_name: str
    category: str
    description: Optional[str] = None
    selling_price: float
    available_quantity: int
    minimum_order_quantity: int = 1
    location: str
    delivery_locations: str
    expiry_date: Optional[datetime] = None
    status: Optional[str] = "ACTIVE"

class ProductOfferCreate(ProductOfferBase):
    vendor_id: Optional[int] = 1

class ProductOfferUpdate(BaseModel):
    product_name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    selling_price: Optional[float] = None
    available_quantity: Optional[int] = None
    minimum_order_quantity: Optional[int] = None
    location: Optional[str] = None
    delivery_locations: Optional[str] = None
    expiry_date: Optional[datetime] = None
    status: Optional[str] = None

class ProductOfferResponse(ProductOfferBase):
    id: int
    vendor_id: int
    created_at: datetime
    updated_at: datetime
    interested_count: Optional[int] = 0
    suggested_matches_count: Optional[int] = 0

    class Config:
        from_attributes = True


# --- Offer Interest Schemas ---
class OfferInterestCreate(BaseModel):
    shopkeeper_id: int
    status: Optional[str] = "INTERESTED"
    notes: Optional[str] = None

class OfferInterestResponse(BaseModel):
    id: int
    product_offer_id: int
    shopkeeper_id: int
    status: str
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# --- Match Schemas ---
class MatchBreakdown(BaseModel):
    category_match: bool
    product_name_score: float
    quantity_feasible: bool
    budget_compatible: bool
    price_difference_pct: float
    moq_satisfied: bool
    location_match: bool

class ShopkeeperMatchItem(BaseModel):
    shopkeeper_id: int
    shopkeeper_name: str
    shop_name: str
    whatsapp_phone: str
    location: str
    required_product: str
    required_quantity: int
    target_price: float
    vendor_price: float
    moq: int
    match_score: int # 0 to 100
    is_explicitly_interested: bool # True if explicitly expressed interest
    explicit_interest_status: Optional[str] = None
    match_reasons: List[str]
    breakdown: MatchBreakdown
    existing_conversation_id: Optional[int] = None
    last_contact_date: Optional[datetime] = None


class MatchesResponse(BaseModel):
    offer_id: int
    product_name: str
    selling_price: float
    interested_shopkeepers: List[ShopkeeperMatchItem]
    suggested_matches: List[ShopkeeperMatchItem]


# --- Message & Status History Schemas ---
class MessageStatusHistoryResponse(BaseModel):
    id: int
    message_id: int
    status: str
    status_timestamp: datetime
    provider_event_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MessageBase(BaseModel):
    message_text: str
    product_offer_id: Optional[int] = None
    reply_to_message_id: Optional[int] = None

class MessageSendRequest(MessageBase):
    shopkeeper_id: int
    is_simulation: Optional[bool] = False

class MessageQuotedSummary(BaseModel):
    id: int
    message_text: str
    sender_phone: str
    direction: str
    message_timestamp: datetime

class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    vendor_id: int
    shopkeeper_id: int
    shopkeeper_name: Optional[str] = None
    shop_name: Optional[str] = None
    product_offer_id: Optional[int] = None
    product_name: Optional[str] = None
    whatsapp_message_id: Optional[str] = None
    provider_reply_to_id: Optional[str] = None
    reply_to_message_id: Optional[int] = None
    quoted_message: Optional[MessageQuotedSummary] = None
    sender_phone: str
    recipient_phone: str
    direction: str # OUTBOUND, INBOUND
    message_text: str
    message_timestamp: datetime
    actual_sent_timestamp: Optional[datetime] = None
    created_at: datetime
    delivery_status: str # PENDING, SENT, DELIVERED, READ, FAILED
    reply_link_type: str # EXACT, INFERRED, NONE
    is_demo: bool
    inferred_confidence: Optional[float] = None
    inferred_reason: Optional[str] = None
    status_history: List[MessageStatusHistoryResponse] = []

    class Config:
        from_attributes = True


# --- Conversation Schemas ---
class ConversationResponse(BaseModel):
    id: int
    vendor_id: int
    shopkeeper_id: int
    shopkeeper_name: str
    shop_name: str
    whatsapp_phone: str
    shopkeeper_location: str
    product_offer_id: Optional[int] = None
    product_name: Optional[str] = None
    status: str
    lead_status: str
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime
    latest_message: Optional[MessageResponse] = None
    unread_count: int = 0
    total_messages: int = 0

    class Config:
        from_attributes = True


class ConversationLeadStatusUpdate(BaseModel):
    lead_status: str # INTERESTED, CONTACTED, NEGOTIATING, CONVERTED, NOT_INTERESTED


# --- Demo Simulation Schemas ---
class SimulateInboundMessageRequest(BaseModel):
    shopkeeper_id: int
    message_text: str
    product_offer_id: Optional[int] = None
    reply_to_message_id: Optional[int] = None  # If set, simulates WhatsApp native reply with context.id
    use_native_reply: bool = False             # If true and reply_to_message_id is provided, sets reply_link_type="EXACT"

class SimulateStatusChangeRequest(BaseModel):
    message_id: int
    new_status: str # SENT, DELIVERED, READ, FAILED


# --- AI Assistance Schemas ---
class AIDraftRequest(BaseModel):
    conversation_id: int
    product_offer_id: Optional[int] = None
    intent: Optional[str] = "initial_pitch" # initial_pitch, negotiate_price, confirm_quantity, follow_up

class AIDraftResponse(BaseModel):
    suggested_text: str
    reasoning: str
