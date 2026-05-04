from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
from uuid import UUID
from datetime import date

from database import get_db
from models import Material, LedgerProperty
from schemas import MaterialCreate, MaterialUpdate, MaterialResponse

router = APIRouter()

def build_material_response(material):
    """Build MaterialResponse dict from SQLAlchemy model"""
    props = {p.property_key: p.property_value for p in material.properties}
    return {
        "id": material.id,
        "name": material.name,
        "specification": material.specification,
        "category": material.category,
        "unit": material.unit,
        "current_stock": material.current_stock,
        "min_stock": material.min_stock,
        "material_code": material.material_code,
        "inbound_status": material.inbound_status,
        "planned_inbound_date": material.planned_inbound_date,
        "purchase_date": material.purchase_date,
        "notes": material.notes,
        "properties": [{"key": k, "value": v} for k, v in props.items()]
    }

@router.get("", response_model=List[MaterialResponse])
def get_materials(
    search: Optional[str] = None,
    category: Optional[str] = None,
    inbound_status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Material)

    if search:
        query = query.filter(
            or_(
                Material.name.ilike(f"%{search}%"),
                Material.specification.ilike(f"%{search}%"),
                Material.material_code.ilike(f"%{search}%")
            )
        )

    if category:
        query = query.filter(Material.category == category)

    if inbound_status:
        query = query.filter(Material.inbound_status == inbound_status)

    materials = query.offset(skip).limit(limit).all()
    return [build_material_response(m) for m in materials]

@router.get("/{material_id}", response_model=MaterialResponse)
def get_material(material_id: UUID, db: Session = Depends(get_db)):
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="物料不存在")
    return build_material_response(material)

@router.post("", response_model=MaterialResponse)
def create_material(material: MaterialCreate, db: Session = Depends(get_db)):
    db_material = Material(**material.model_dump())
    db.add(db_material)
    db.commit()
    db.refresh(db_material)
    return build_material_response(db_material)

@router.put("/{material_id}", response_model=MaterialResponse)
def update_material(material_id: UUID, material: MaterialUpdate, db: Session = Depends(get_db)):
    db_material = db.query(Material).filter(Material.id == material_id).first()
    if not db_material:
        raise HTTPException(status_code=404, detail="物料不存在")

    for key, value in material.model_dump().items():
        if value is not None:
            setattr(db_material, key, value)

    db.commit()
    db.refresh(db_material)
    return build_material_response(db_material)

@router.delete("/{material_id}")
def delete_material(material_id: UUID, db: Session = Depends(get_db)):
    db_material = db.query(Material).filter(Material.id == material_id).first()
    if not db_material:
        raise HTTPException(status_code=404, detail="物料不存在")

    db.delete(db_material)
    db.commit()
    return {"message": "删除成功"}