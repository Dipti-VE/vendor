from datetime import datetime, timezone, timedelta
from sqlalchemy import text
from sqlalchemy.orm import Session
from .database import Base, engine
from .models import (
    Vendor, Shopkeeper, ShopkeeperRequirement, ProductOffer,
    OfferInterest, Conversation, Message, MessageStatusHistory
)

def sync_db_sequences(db: Session):
    """Synchronize PostgreSQL auto-increment sequences with MAX(id) to prevent unique constraint violations"""
    if engine.dialect.name == "postgresql":
        tables = [
            "vendors",
            "shopkeepers",
            "shopkeeper_requirements",
            "product_offers",
            "offer_interests",
            "conversations",
            "messages",
            "message_status_history"
        ]
        for table in tables:
            try:
                db.execute(text(f"""
                    SELECT setval(
                        pg_get_serial_sequence('{table}', 'id'),
                        COALESCE((SELECT MAX(id) FROM {table}), 1)
                    );
                """))
            except Exception:
                pass
        try:
            db.commit()
        except Exception:
            pass

def seed_database(db: Session, reset: bool = False):
    if reset:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    # Check if vendor already exists
    if db.query(Vendor).first():
        sync_db_sequences(db)
        return

    now = datetime.now(timezone.utc)

    # 1. Vendor
    vendor = Vendor(
        id=1,
        name="Rajesh Sharma",
        company_name="GreenPack Solutions India Pvt Ltd",
        phone_number="+919876543210",
        email="rajesh@greenpacksolutions.in",
        created_at=now - timedelta(days=30)
    )
    db.add(vendor)
    db.commit()
    db.refresh(vendor)

    # 2. Product Offers
    offers = [
        ProductOffer(
            id=1,
            vendor_id=vendor.id,
            product_name="250ml Ripple Wall Insulated Paper Cups",
            category="Paper Cups",
            description="Premium 3-ply ripple wall cups for hot beverages (chai, coffee). Exceptional heat resistance, no cup sleeve required. Food-grade PLA coated.",
            selling_price=0.80,
            available_quantity=50000,
            minimum_order_quantity=1000,
            location="New Delhi",
            delivery_locations="Delhi NCR, Pan India, Mumbai, Bengaluru, Kolkata, Pune",
            expiry_date=now + timedelta(days=60),
            status="ACTIVE",
            created_at=now - timedelta(days=10),
            updated_at=now - timedelta(days=10)
        ),
        ProductOffer(
            id=2,
            vendor_id=vendor.id,
            product_name="750ml Kraft Paper Takeaway Food Containers",
            category="Takeaway Containers",
            description="Eco-friendly unbleached brown kraft food containers with secure leak-resistant lids. Microwave safe, oil and grease resistant.",
            selling_price=4.50,
            available_quantity=25000,
            minimum_order_quantity=500,
            location="New Delhi",
            delivery_locations="Pan India, Delhi NCR, Bengaluru, Mumbai, Hyderabad, Pune",
            expiry_date=now + timedelta(days=45),
            status="ACTIVE",
            created_at=now - timedelta(days=8),
            updated_at=now - timedelta(days=8)
        ),
        ProductOffer(
            id=3,
            vendor_id=vendor.id,
            product_name="Eco-Friendly Brown Kraft Paper Bags with Twisted Handles",
            category="Paper Bags",
            description="120 GSM heavy-duty biodegradable brown kraft paper carry bags. Supports up to 4kg weight. Perfect for cafes, bakeries, and retail takeaways.",
            selling_price=3.20,
            available_quantity=30000,
            minimum_order_quantity=500,
            location="New Delhi",
            delivery_locations="Pan India, Delhi NCR, Mumbai, Kolkata, Bengaluru",
            expiry_date=now + timedelta(days=50),
            status="ACTIVE",
            created_at=now - timedelta(days=6),
            updated_at=now - timedelta(days=6)
        ),
        ProductOffer(
            id=4,
            vendor_id=vendor.id,
            product_name="3-Compartment Biodegradable Bagasse Meal Trays with Lids",
            category="Meal Trays",
            description="100% compostable sugarcane bagasse meal trays with tight clear lids. Ideal for thali meals, executive lunches, and corporate catering.",
            selling_price=6.00,
            available_quantity=15000,
            minimum_order_quantity=300,
            location="New Delhi",
            delivery_locations="Pan India, Delhi NCR, Hyderabad, Bengaluru",
            expiry_date=now + timedelta(days=40),
            status="ACTIVE",
            created_at=now - timedelta(days=4),
            updated_at=now - timedelta(days=4)
        )
    ]
    for o in offers:
        db.add(o)
    db.commit()

    # 3. Shopkeepers & Requirements
    shopkeepers_data = [
        {
            "id": 1,
            "name": "Amit Verma",
            "shop": "Chai Point Express",
            "phone": "+919064148052",
            "location": "Connaught Place, New Delhi",
            "delivery": "Central Delhi",
            "status": "NEGOTIATING",
            "requirements": [
                {
                    "product": "250ml Ripple Paper Cups",
                    "category": "Paper Cups",
                    "qty": 10000,
                    "target_price": 0.85,
                    "loc": "Central Delhi"
                }
            ],
            "explicit_interest": 1 # Offer 1
        },
        {
            "id": 2,
            "name": "Priya Nair",
            "shop": "Royal Biryani House",
            "phone": "+919064148052",
            "location": "Indiranagar, Bengaluru",
            "delivery": "South Bengaluru",
            "status": "CONTACTED",
            "requirements": [
                {
                    "product": "750ml Kraft Food Containers",
                    "category": "Takeaway Containers",
                    "qty": 5000,
                    "target_price": 4.80,
                    "loc": "Bengaluru"
                }
            ],
            "explicit_interest": 2 # Offer 2
        },
        {
            "id": 3,
            "name": "Vikram Singh",
            "shop": "QuickBite Fast Food & Burgers",
            "phone": "+919064148052",
            "location": "Bandra West, Mumbai",
            "delivery": "Mumbai Western Suburbs",
            "status": "INTERESTED",
            "requirements": [
                {
                    "product": "Kraft Paper Takeaway Containers",
                    "category": "Takeaway Containers",
                    "qty": 4000,
                    "target_price": 4.30,
                    "loc": "Mumbai"
                },
                {
                    "product": "Brown Kraft Bags with Handles",
                    "category": "Paper Bags",
                    "qty": 3000,
                    "target_price": 3.10,
                    "loc": "Mumbai"
                }
            ],
            "explicit_interest": None # Suggested Match only
        },
        {
            "id": 4,
            "name": "Sunita Agarwal",
            "shop": "Metro Sweets & Bakery",
            "phone": "+919064148052",
            "location": "Sector 18, Noida",
            "delivery": "Noida / Delhi NCR",
            "status": "CONTACTED",
            "requirements": [
                {
                    "product": "250ml Ripple Paper Cups",
                    "category": "Paper Cups",
                    "qty": 8000,
                    "target_price": 0.78,
                    "loc": "Noida"
                },
                {
                    "product": "Paper Bags with Handles",
                    "category": "Paper Bags",
                    "qty": 5000,
                    "target_price": 3.00,
                    "loc": "Noida"
                }
            ],
            "explicit_interest": None # Suggested Match only
        },
        {
            "id": 5,
            "name": "Mohammed Farhan",
            "shop": "Spice Garden Family Restaurant",
            "phone": "+919064148052",
            "location": "Gachibowli, Hyderabad",
            "delivery": "Hyderabad Cyberabad",
            "status": "INTERESTED",
            "requirements": [
                {
                    "product": "3-Compartment Meal Trays with Lids",
                    "category": "Meal Trays",
                    "qty": 3500,
                    "target_price": 6.20,
                    "loc": "Hyderabad"
                }
            ],
            "explicit_interest": 4 # Offer 4
        },
        {
            "id": 6,
            "name": "Ritu Deshmukh",
            "shop": "Café Mocha & Bakery",
            "phone": "+919064148052",
            "location": "FC Road, Pune",
            "delivery": "Pune City",
            "status": "INTERESTED",
            "requirements": [
                {
                    "product": "250ml Ripple Insulated Paper Cups",
                    "category": "Paper Cups",
                    "qty": 15000,
                    "target_price": 0.88,
                    "loc": "Pune"
                }
            ],
            "explicit_interest": None # Suggested Match only
        },
        {
            "id": 7,
            "name": "Gurpreet Singh",
            "shop": "Golden Dhaba & Tiffin",
            "phone": "+919064148052",
            "location": "Sector 22, Chandigarh",
            "delivery": "Chandigarh Tricity",
            "status": "INTERESTED",
            "requirements": [
                {
                    "product": "Kraft Meal Containers 750ml",
                    "category": "Takeaway Containers",
                    "qty": 2000,
                    "target_price": 4.10,
                    "loc": "Chandigarh"
                }
            ],
            "explicit_interest": None # Suggested Match only
        },
        {
            "id": 8,
            "name": "Ananya Sen",
            "shop": "Artisan Coffee Roasters",
            "phone": "+919064148052",
            "location": "Park Street, Kolkata",
            "delivery": "Central Kolkata",
            "status": "CONVERTED",
            "requirements": [
                {
                    "product": "Brown Kraft Bags with Handles",
                    "category": "Paper Bags",
                    "qty": 6000,
                    "target_price": 3.30,
                    "loc": "Kolkata"
                }
            ],
            "explicit_interest": 3 # Offer 3
        }
    ]

    for sk_info in shopkeepers_data:
        sk = Shopkeeper(
            id=sk_info["id"],
            shopkeeper_name=sk_info["name"],
            shop_name=sk_info["shop"],
            whatsapp_phone=sk_info["phone"],
            location=sk_info["location"],
            preferred_delivery_location=sk_info["delivery"],
            lead_status=sk_info["status"],
            created_at=now - timedelta(days=15)
        )
        db.add(sk)
        db.commit()

        # Add requirements
        for r_info in sk_info["requirements"]:
            req = ShopkeeperRequirement(
                shopkeeper_id=sk.id,
                product_name=r_info["product"],
                category=r_info["category"],
                required_quantity=r_info["qty"],
                target_price=r_info["target_price"],
                delivery_location=r_info["loc"],
                created_at=now - timedelta(days=12)
            )
            db.add(req)
        db.commit()

        # Add explicit interest if present
        if sk_info["explicit_interest"]:
            interest = OfferInterest(
                product_offer_id=sk_info["explicit_interest"],
                shopkeeper_id=sk.id,
                status="INTERESTED",
                notes=f"Shopkeeper submitted quote request for {r_info['product']}",
                created_at=now - timedelta(days=5)
            )
            db.add(interest)
            db.commit()

    # 4. Conversations and Traceable Message History
    # Conversation 1: Amit Verma (Chai Point Express) - Offer 1
    conv1 = Conversation(
        id=1,
        vendor_id=vendor.id,
        shopkeeper_id=1,
        product_offer_id=1,
        status="ACTIVE",
        lead_status="NEGOTIATING",
        created_at=now - timedelta(hours=48),
        updated_at=now - timedelta(minutes=15),
        last_message_at=now - timedelta(minutes=15)
    )
    db.add(conv1)
    db.commit()

    # Msg 1: Outbound from Vendor
    t1 = now - timedelta(hours=48)
    msg1 = Message(
        id=1,
        conversation_id=conv1.id,
        vendor_id=vendor.id,
        shopkeeper_id=1,
        product_offer_id=1,
        whatsapp_message_id="wamid.HBgM9876543210A1B2C3",
        provider_reply_to_id=None,
        reply_to_message_id=None,
        sender_phone=vendor.phone_number,
        recipient_phone="+919064148052",
        direction="OUTBOUND",
        message_text="Hello Amit ji! We have premium 250ml Ripple Wall Insulated Paper Cups available at ₹0.80 per piece. We currently have 50,000 pieces in ready stock. Would you be interested in purchasing for Chai Point Express?",
        message_timestamp=t1,
        actual_sent_timestamp=t1,
        created_at=t1,
        delivery_status="READ",
        reply_link_type="NONE",
        is_demo=False
    )
    db.add(msg1)
    db.commit()

    # Msg 1 Status history
    hist1 = [
        MessageStatusHistory(message_id=msg1.id, status="PENDING", status_timestamp=t1, provider_event_id=None, created_at=t1),
        MessageStatusHistory(message_id=msg1.id, status="SENT", status_timestamp=t1 + timedelta(seconds=2), provider_event_id="evt_sent_1", created_at=t1 + timedelta(seconds=2)),
        MessageStatusHistory(message_id=msg1.id, status="DELIVERED", status_timestamp=t1 + timedelta(seconds=15), provider_event_id="evt_deliv_1", created_at=t1 + timedelta(seconds=15)),
        MessageStatusHistory(message_id=msg1.id, status="READ", status_timestamp=t1 + timedelta(minutes=3), provider_event_id="evt_read_1", created_at=t1 + timedelta(minutes=3)),
    ]
    for h in hist1:
        db.add(h)
    db.commit()

    # Msg 2: Inbound Reply with EXACT WhatsApp native reply quote
    t2 = now - timedelta(hours=47, minutes=50)
    msg2 = Message(
        id=2,
        conversation_id=conv1.id,
        vendor_id=vendor.id,
        shopkeeper_id=1,
        product_offer_id=1,
        whatsapp_message_id="wamid.HBgM9811122233X9Y8Z7",
        provider_reply_to_id="wamid.HBgM9876543210A1B2C3",
        reply_to_message_id=msg1.id, # Foreign Key linked to original message!
        sender_phone="+919064148052",
        recipient_phone=vendor.phone_number,
        direction="INBOUND",
        message_text="Yes, I need 10,000 pieces. Can you offer ₹0.75 per piece if I place the order today?",
        message_timestamp=t2,
        actual_sent_timestamp=t2,
        created_at=t2,
        delivery_status="DELIVERED",
        reply_link_type="EXACT", # Confirmed by WhatsApp native reply metadata
        is_demo=False
    )
    db.add(msg2)
    db.commit()

    # Msg 3: Vendor reply
    t3 = now - timedelta(hours=24)
    msg3 = Message(
        id=3,
        conversation_id=conv1.id,
        vendor_id=vendor.id,
        shopkeeper_id=1,
        product_offer_id=1,
        whatsapp_message_id="wamid.HBgM9876543210D4E5F6",
        provider_reply_to_id="wamid.HBgM9811122233X9Y8Z7",
        reply_to_message_id=msg2.id,
        sender_phone=vendor.phone_number,
        recipient_phone="+919064148052",
        direction="OUTBOUND",
        message_text="We can do ₹0.78 per piece for 10,000 pieces, including door delivery to Connaught Place within 24 hours. Would that work?",
        message_timestamp=t3,
        actual_sent_timestamp=t3,
        created_at=t3,
        delivery_status="READ",
        reply_link_type="EXACT",
        is_demo=False
    )
    db.add(msg3)
    db.commit()

    # Msg 4: Shopkeeper confirmation
    t4 = now - timedelta(minutes=15)
    msg4 = Message(
        id=4,
        conversation_id=conv1.id,
        vendor_id=vendor.id,
        shopkeeper_id=1,
        product_offer_id=1,
        whatsapp_message_id="wamid.HBgM9811122233K1L2M3",
        provider_reply_to_id="wamid.HBgM9876543210D4E5F6",
        reply_to_message_id=msg3.id,
        sender_phone="+919064148052",
        recipient_phone=vendor.phone_number,
        direction="INBOUND",
        message_text="Deal confirmed for ₹0.78! Please send the proforma invoice and bank details.",
        message_timestamp=t4,
        actual_sent_timestamp=t4,
        created_at=t4,
        delivery_status="DELIVERED",
        reply_link_type="EXACT",
        is_demo=False
    )
    db.add(msg4)
    db.commit()

    # Conversation 2: Priya Nair (Royal Biryani House) - Offer 2
    conv2 = Conversation(
        id=2,
        vendor_id=vendor.id,
        shopkeeper_id=2,
        product_offer_id=2,
        status="ACTIVE",
        lead_status="CONTACTED",
        created_at=now - timedelta(hours=12),
        updated_at=now - timedelta(hours=2),
        last_message_at=now - timedelta(hours=2)
    )
    db.add(conv2)
    db.commit()

    msg2_1 = Message(
        id=5,
        conversation_id=conv2.id,
        vendor_id=vendor.id,
        shopkeeper_id=2,
        product_offer_id=2,
        whatsapp_message_id="wamid.HBgM9876543210P1Q2R3",
        provider_reply_to_id=None,
        reply_to_message_id=None,
        sender_phone=vendor.phone_number,
        recipient_phone="+919064148052",
        direction="OUTBOUND",
        message_text="Hello Priya ji! We noticed your requirement for 750ml Kraft takeaway food containers. Our stock is ready at ₹4.50/unit with leakproof lids. Minimum order is 500 pcs.",
        message_timestamp=now - timedelta(hours=12),
        actual_sent_timestamp=now - timedelta(hours=12),
        created_at=now - timedelta(hours=12),
        delivery_status="DELIVERED",
        reply_link_type="NONE",
        is_demo=False
    )
    db.add(msg2_1)
    db.commit()

    msg2_2 = Message(
        id=6,
        conversation_id=conv2.id,
        vendor_id=vendor.id,
        shopkeeper_id=2,
        product_offer_id=2,
        whatsapp_message_id="wamid.HBgM9822233344S1T2U3",
        provider_reply_to_id=None,
        reply_to_message_id=None,
        sender_phone="+919064148052",
        recipient_phone=vendor.phone_number,
        direction="INBOUND",
        message_text="Can you dispatch a sample box of 100 containers to Indiranagar before we confirm the 5,000 order?",
        message_timestamp=now - timedelta(hours=2),
        actual_sent_timestamp=now - timedelta(hours=2),
        created_at=now - timedelta(hours=2),
        delivery_status="DELIVERED",
        reply_link_type="INFERRED", # AI inferred context based on offer 2
        inferred_confidence=0.92,
        inferred_reason="Message specifically discusses 750ml containers and sample shipment for the ongoing offer",
        is_demo=False
    )
    db.add(msg2_2)
    db.commit()

    # Conversation 3: Sunita Agarwal (Metro Sweets & Bakery)
    conv3 = Conversation(
        id=3,
        vendor_id=vendor.id,
        shopkeeper_id=4,
        product_offer_id=3,
        status="ACTIVE",
        lead_status="CONTACTED",
        created_at=now - timedelta(hours=5),
        updated_at=now - timedelta(hours=1),
        last_message_at=now - timedelta(hours=1)
    )
    db.add(conv3)
    db.commit()

    msg3_1 = Message(
        id=7,
        conversation_id=conv3.id,
        vendor_id=vendor.id,
        shopkeeper_id=4,
        product_offer_id=3,
        whatsapp_message_id="wamid.HBgM9876543210W1X2Y3",
        provider_reply_to_id=None,
        reply_to_message_id=None,
        sender_phone=vendor.phone_number,
        recipient_phone="+919064148052",
        direction="OUTBOUND",
        message_text="Hello Sunita ji! We have 120 GSM brown kraft paper carry bags at ₹3.20/pc with free delivery to Sector 18 Noida.",
        message_timestamp=now - timedelta(hours=5),
        actual_sent_timestamp=now - timedelta(hours=5),
        created_at=now - timedelta(hours=5),
        delivery_status="READ",
        reply_link_type="NONE",
        is_demo=False
    )
    db.add(msg3_1)
    db.commit()

    msg3_2 = Message(
        id=8,
        conversation_id=conv3.id,
        vendor_id=vendor.id,
        shopkeeper_id=4,
        product_offer_id=None,
        whatsapp_message_id="wamid.HBgM9844455566Z9A8B7",
        provider_reply_to_id=None,
        reply_to_message_id=None,
        sender_phone="+919064148052",
        recipient_phone=vendor.phone_number,
        direction="INBOUND",
        message_text="Do you also supply transparent sweet boxes?",
        message_timestamp=now - timedelta(hours=1),
        actual_sent_timestamp=now - timedelta(hours=1),
        created_at=now - timedelta(hours=1),
        delivery_status="DELIVERED",
        reply_link_type="NONE", # Normal message without specific reply link or offer tie
        is_demo=False
    )
    db.add(msg3_2)
    db.commit()

    sync_db_sequences(db)
    print("Seed data successfully initialized!")
