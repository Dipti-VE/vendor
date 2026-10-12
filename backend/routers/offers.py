from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

from ..database import get_db
from ..models import ProductOffer, OfferInterest, Vendor, Shopkeeper
from ..schemas import (
    ProductOfferResponse, ProductOfferCreate, ProductOfferUpdate,
    MatchesResponse, OfferInterestCreate, OfferInterestResponse
)
from ..services.matching_service import match_offer_with_shopkeepers
from ..services.connection_manager import ws_manager

router = APIRouter(prefix="/offers", tags=["Product Offers"])

@router.get("", response_model=List[ProductOfferResponse])
def get_product_offers(
    status: Optional[str] = Query(None, description="Filter by status: ACTIVE, PAUSED, EXPIRED"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db)
):
    query = db.query(ProductOffer)
    if status:
        query = query.filter(ProductOffer.status == status)
    if category:
        query = query.filter(ProductOffer.category == category)
        
    offers = query.order_by(ProductOffer.id.desc()).all()
    results = []

    for offer in offers:
        # Count explicit interests
        interest_count = db.query(OfferInterest).filter(OfferInterest.product_offer_id == offer.id).count()
        # Compute match counts
        matches_data = match_offer_with_shopkeepers(offer, db)
        
        offer_dict = ProductOfferResponse.model_validate(offer)
        offer_dict.interested_count = interest_count
        offer_dict.suggested_matches_count = len(matches_data.suggested_matches)
        results.append(offer_dict)

    return results

@router.post("", response_model=ProductOfferResponse)
async def create_product_offer(payload: ProductOfferCreate, db: Session = Depends(get_db)):
    vendor = db.query(Vendor).first()
    vendor_id = vendor.id if vendor else 1

    offer = ProductOffer(
        vendor_id=vendor_id,
        product_name=payload.product_name,
        category=payload.category,
        description=payload.description,
        selling_price=payload.selling_price,
        available_quantity=payload.available_quantity,
        minimum_order_quantity=payload.minimum_order_quantity,
        location=payload.location,
        delivery_locations=payload.delivery_locations,
        expiry_date=payload.expiry_date,
        status=payload.status or "ACTIVE",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(offer)
    db.commit()
    db.refresh(offer)

    # Broadcast new offer
    await ws_manager.broadcast("offer_created", {
        "offer_id": offer.id,
        "product_name": offer.product_name,
        "selling_price": offer.selling_price
    })

    res = ProductOfferResponse.model_validate(offer)
    res.interested_count = 0
    res.suggested_matches_count = 0
    return res

@router.get("/{offer_id}", response_model=ProductOfferResponse)
def get_product_offer(offer_id: int, db: Session = Depends(get_db)):
    offer = db.query(ProductOffer).filter(ProductOffer.id == offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Product offer not found")

    interest_count = db.query(OfferInterest).filter(OfferInterest.product_offer_id == offer.id).count()
    matches_data = match_offer_with_shopkeepers(offer, db)

    res = ProductOfferResponse.model_validate(offer)
    res.interested_count = interest_count
    res.suggested_matches_count = len(matches_data.suggested_matches)
    return res

@router.patch("/{offer_id}", response_model=ProductOfferResponse)
def update_product_offer(offer_id: int, payload: ProductOfferUpdate, db: Session = Depends(get_db)):
    offer = db.query(ProductOffer).filter(ProductOffer.id == offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Product offer not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(offer, field, val)
    offer.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(offer)

    interest_count = db.query(OfferInterest).filter(OfferInterest.product_offer_id == offer.id).count()
    res = ProductOfferResponse.model_validate(offer)
    res.interested_count = interest_count
    return res

@router.get("/{offer_id}/matches", response_model=MatchesResponse)
def get_offer_matches(offer_id: int, db: Session = Depends(get_db)):
    offer = db.query(ProductOffer).filter(ProductOffer.id == offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Product offer not found")

    matches = match_offer_with_shopkeepers(offer, db)
    return matches

@router.post("/{offer_id}/interest", response_model=OfferInterestResponse)
async def express_offer_interest(offer_id: int, payload: OfferInterestCreate, db: Session = Depends(get_db)):
    offer = db.query(ProductOffer).filter(ProductOffer.id == offer_id).first()
    if not offer:
        raise HTTPException(status_code=404, detail="Product offer not found")

    shopkeeper = db.query(Shopkeeper).filter(Shopkeeper.id == payload.shopkeeper_id).first()
    if not shopkeeper:
        raise HTTPException(status_code=404, detail="Shopkeeper not found")

    existing = db.query(OfferInterest).filter(
        OfferInterest.product_offer_id == offer_id,
        OfferInterest.shopkeeper_id == payload.shopkeeper_id
    ).first()

    if existing:
        existing.status = payload.status or "INTERESTED"
        existing.notes = payload.notes or existing.notes
        db.commit()
        db.refresh(existing)
        interest_record = existing
    else:
        interest_record = OfferInterest(
            product_offer_id=offer_id,
            shopkeeper_id=payload.shopkeeper_id,
            status=payload.status or "INTERESTED",
            notes=payload.notes or "Expressed explicit interest via marketplace inquiry",
            created_at=datetime.now(timezone.utc)
        )
        db.add(interest_record)
        db.commit()
        db.refresh(interest_record)

    # Broadcast interest event
    await ws_manager.broadcast("interest_expressed", {
        "offer_id": offer_id,
        "product_name": offer.product_name,
        "shopkeeper_id": shopkeeper.id,
        "shopkeeper_name": shopkeeper.shopkeeper_name,
        "shop_name": shopkeeper.shop_name
    })

    return interest_record
