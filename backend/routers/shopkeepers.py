from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import Shopkeeper, ShopkeeperRequirement
from ..schemas import (
    ShopkeeperResponse, ShopkeeperCreate,
    ShopkeeperRequirementCreate, ShopkeeperRequirementResponse
)

router = APIRouter(prefix="/shopkeepers", tags=["Shopkeepers"])

@router.get("", response_model=List[ShopkeeperResponse])
def get_shopkeepers(db: Session = Depends(get_db)):
    shopkeepers = db.query(Shopkeeper).order_by(Shopkeeper.id.desc()).all()
    return shopkeepers

@router.post("", response_model=ShopkeeperResponse)
def create_shopkeeper(payload: ShopkeeperCreate, db: Session = Depends(get_db)):

    shopkeeper = Shopkeeper(
        shopkeeper_name=payload.shopkeeper_name,
        shop_name=payload.shop_name,
        whatsapp_phone=payload.whatsapp_phone,
        location=payload.location,
        preferred_delivery_location=payload.preferred_delivery_location or payload.location,
        lead_status=payload.lead_status or "INTERESTED"
    )
    db.add(shopkeeper)
    db.commit()
    db.refresh(shopkeeper)

    # Add requirements if provided
    if payload.requirements:
        for req in payload.requirements:
            r = ShopkeeperRequirement(
                shopkeeper_id=shopkeeper.id,
                product_name=req.product_name,
                category=req.category,
                required_quantity=req.required_quantity,
                target_price=req.target_price,
                delivery_location=req.delivery_location or shopkeeper.location
            )
            db.add(r)
        db.commit()
        db.refresh(shopkeeper)

    return shopkeeper

@router.get("/{shopkeeper_id}", response_model=ShopkeeperResponse)
def get_shopkeeper(shopkeeper_id: int, db: Session = Depends(get_db)):
    shopkeeper = db.query(Shopkeeper).filter(Shopkeeper.id == shopkeeper_id).first()
    if not shopkeeper:
        raise HTTPException(status_code=404, detail="Shopkeeper not found")
    return shopkeeper

@router.post("/{shopkeeper_id}/requirements", response_model=ShopkeeperRequirementResponse)
def add_requirement(
    shopkeeper_id: int,
    req_payload: ShopkeeperRequirementCreate,
    db: Session = Depends(get_db)
):
    shopkeeper = db.query(Shopkeeper).filter(Shopkeeper.id == shopkeeper_id).first()
    if not shopkeeper:
        raise HTTPException(status_code=404, detail="Shopkeeper not found")

    new_req = ShopkeeperRequirement(
        shopkeeper_id=shopkeeper.id,
        product_name=req_payload.product_name,
        category=req_payload.category,
        required_quantity=req_payload.required_quantity,
        target_price=req_payload.target_price,
        delivery_location=req_payload.delivery_location or shopkeeper.location
    )
    db.add(new_req)
    db.commit()
    db.refresh(new_req)
    return new_req
