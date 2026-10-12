from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from ..models import ProductOffer, Shopkeeper, ShopkeeperRequirement, OfferInterest, Conversation, Message
from ..schemas import ShopkeeperMatchItem, MatchBreakdown, MatchesResponse
import re

def normalize_text(text: str) -> set:
    if not text:
        return set()
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', ' ', text.lower())
    words = set(cleaned.split())
    # Expand packaging synonyms
    synonyms = {
        "cup": {"cups", "glass", "paper cup", "disposable cup"},
        "cups": {"cup", "glass", "paper cup", "disposable cup"},
        "container": {"box", "takeaway", "containers", "meal box", "packaging"},
        "containers": {"box", "takeaway", "container", "meal box", "packaging"},
        "bag": {"bags", "pouch", "paper bag", "carry bag"},
        "bags": {"bag", "pouch", "paper bag", "carry bag"},
        "box": {"boxes", "carton", "pizza box", "burger box"},
        "boxes": {"box", "carton", "pizza box", "burger box"},
        "packaging": {"supplies", "disposables", "containers", "cups", "bags"}
    }
    expanded = set(words)
    for w in words:
        if w in synonyms:
            expanded.update(synonyms[w])
    return expanded

def calculate_text_similarity(offer_name: str, offer_cat: str, req_name: str, req_cat: str) -> Tuple[bool, float]:
    tokens_offer = normalize_text(f"{offer_name} {offer_cat}")
    tokens_req = normalize_text(f"{req_name} {req_cat}")
    
    cat_match = (offer_cat.strip().lower() == req_cat.strip().lower()) or \
                ("packaging" in offer_cat.lower() and "packaging" in req_cat.lower())
    
    intersection = tokens_offer.intersection(tokens_req)
    union = tokens_offer.union(tokens_req)
    
    score = (len(intersection) / max(len(union), 1)) if union else 0.0
    # Boost if any key packaging words overlap
    key_words = {"cup", "cups", "container", "containers", "bag", "bags", "box", "boxes", "tray", "trays"}
    if tokens_offer.intersection(key_words).intersection(tokens_req):
        score = max(score, 0.6)
        
    return cat_match, min(score * 1.5, 1.0)

def match_offer_with_shopkeepers(offer: ProductOffer, db: Session) -> MatchesResponse:
    # 1. Fetch explicit interests for this offer
    explicit_interests = db.query(OfferInterest).filter(
        OfferInterest.product_offer_id == offer.id
    ).all()
    explicit_interest_map = {interest.shopkeeper_id: interest.status for interest in explicit_interests}

    # 2. Fetch all shopkeepers with requirements
    shopkeepers = db.query(Shopkeeper).all()
    
    interested_list: List[ShopkeeperMatchItem] = []
    suggested_list: List[ShopkeeperMatchItem] = []

    # Get conversations to check if vendor has contacted them
    conv_map = {}
    convs = db.query(Conversation).filter(
        (Conversation.product_offer_id == offer.id) | (Conversation.product_offer_id.is_(None))
    ).all()
    for c in convs:
        conv_map[c.shopkeeper_id] = (c.id, c.last_message_at)

    for sk in shopkeepers:
        # Evaluate each requirement of the shopkeeper
        best_item: ShopkeeperMatchItem = None
        highest_score = -1

        # Check if shopkeeper is explicitly interested
        is_explicit = sk.id in explicit_interest_map
        interest_status = explicit_interest_map.get(sk.id)

        # Look through shopkeeper's requirements
        requirements = sk.requirements or []
        
        # If no requirements listed, create a dummy baseline if explicit interest exists
        if not requirements and is_explicit:
            existing_conv_id, last_contact = conv_map.get(sk.id, (None, None))
            item = ShopkeeperMatchItem(
                shopkeeper_id=sk.id,
                shopkeeper_name=sk.shopkeeper_name,
                shop_name=sk.shop_name,
                whatsapp_phone=sk.whatsapp_phone,
                location=sk.location,
                required_product=offer.product_name,
                required_quantity=offer.minimum_order_quantity,
                target_price=offer.selling_price,
                vendor_price=offer.selling_price,
                moq=offer.minimum_order_quantity,
                match_score=95,
                is_explicitly_interested=True,
                explicit_interest_status=interest_status,
                match_reasons=["Explicitly registered interest for this offer via platform inquiry"],
                breakdown=MatchBreakdown(
                    category_match=True,
                    product_name_score=1.0,
                    quantity_feasible=True,
                    budget_compatible=True,
                    price_difference_pct=0.0,
                    moq_satisfied=True,
                    location_match=True
                ),
                existing_conversation_id=existing_conv_id,
                last_contact_date=last_contact
            )
            interested_list.append(item)
            continue

        for req in requirements:
            cat_match, text_score = calculate_text_similarity(
                offer.product_name, offer.category, req.product_name, req.category
            )
            
            # Quantity feasible: required quantity is <= available quantity in stock
            quantity_feasible = req.required_quantity <= offer.available_quantity
            
            # MOQ satisfied: required quantity is >= minimum order quantity
            moq_satisfied = req.required_quantity >= offer.minimum_order_quantity
            
            # Budget compatibility: target price is >= selling price or within 20% negotiation room
            price_diff_pct = ((offer.selling_price - req.target_price) / offer.selling_price) * 100
            budget_compatible = (req.target_price >= offer.selling_price) or (price_diff_pct <= 25.0)

            # Location match: shopkeeper's delivery location or general location matches offer delivery area
            delivery_areas = [loc.strip().lower() for loc in offer.delivery_locations.split(",") if loc.strip()]
            delivery_areas.append(offer.location.lower())
            
            sk_loc = (req.delivery_location or sk.preferred_delivery_location or sk.location).lower()
            location_match = any(area in sk_loc or sk_loc in area for area in delivery_areas) or "all" in delivery_areas or "pan india" in delivery_areas or "delhi ncr" in delivery_areas

            # Calculate match score (0 - 100)
            score = 0
            reasons = []

            if text_score > 0.4:
                score += int(text_score * 40)
                reasons.append(f"Product specification closely matches requirement ('{req.product_name}')")
            elif cat_match:
                score += 20
                reasons.append(f"Category matches ('{req.category}')")

            if quantity_feasible and moq_satisfied:
                score += 25
                reasons.append(f"Required volume ({req.required_quantity:,} units) satisfies MOQ ({offer.minimum_order_quantity:,}) and available stock")
            elif quantity_feasible and not moq_satisfied:
                score += 10
                reasons.append(f"Volume ({req.required_quantity:,} units) is below standard MOQ ({offer.minimum_order_quantity:,}) but negotiable")

            if budget_compatible:
                score += 25
                if req.target_price >= offer.selling_price:
                    reasons.append(f"Budget (₹{req.target_price:.2f}) meets or exceeds selling price (₹{offer.selling_price:.2f})")
                else:
                    reasons.append(f"Budget (₹{req.target_price:.2f}) is within {abs(price_diff_pct):.0f}% of selling price (₹{offer.selling_price:.2f})")
            else:
                score += 5
                reasons.append(f"Budget gap: target is ₹{req.target_price:.2f} vs vendor price ₹{offer.selling_price:.2f}")

            if location_match:
                score += 10
                reasons.append(f"Direct delivery available to {sk.location}")

            score = min(score, 100)

            # If explicitly interested, add extra reason and highlight
            if is_explicit:
                reasons.insert(0, f"★ Explicitly expressed interest (Status: {interest_status})")
                score = max(score, 85)

            existing_conv_id, last_contact = conv_map.get(sk.id, (None, None))

            item = ShopkeeperMatchItem(
                shopkeeper_id=sk.id,
                shopkeeper_name=sk.shopkeeper_name,
                shop_name=sk.shop_name,
                whatsapp_phone=sk.whatsapp_phone,
                location=sk.location,
                required_product=req.product_name,
                required_quantity=req.required_quantity,
                target_price=req.target_price,
                vendor_price=offer.selling_price,
                moq=offer.minimum_order_quantity,
                match_score=score,
                is_explicitly_interested=is_explicit,
                explicit_interest_status=interest_status,
                match_reasons=reasons,
                breakdown=MatchBreakdown(
                    category_match=cat_match,
                    product_name_score=text_score,
                    quantity_feasible=quantity_feasible,
                    budget_compatible=budget_compatible,
                    price_difference_pct=round(price_diff_pct, 1),
                    moq_satisfied=moq_satisfied,
                    location_match=location_match
                ),
                existing_conversation_id=existing_conv_id,
                last_contact_date=last_contact
            )

            if score > highest_score:
                highest_score = score
                best_item = item

        if best_item:
            # Strictly segregate:
            # A. Interested Shopkeepers: Explicitly registered interest
            # B. Suggested Matches: Compatible requirements, even if NOT explicitly interested
            if best_item.is_explicitly_interested:
                interested_list.append(best_item)
            elif best_item.match_score >= 45: # High or medium compatibility threshold
                suggested_list.append(best_item)

    # Sort each list by match_score descending
    interested_list.sort(key=lambda x: x.match_score, reverse=True)
    suggested_list.sort(key=lambda x: x.match_score, reverse=True)

    return MatchesResponse(
        offer_id=offer.id,
        product_name=offer.product_name,
        selling_price=offer.selling_price,
        interested_shopkeepers=interested_list,
        suggested_matches=suggested_list
    )
