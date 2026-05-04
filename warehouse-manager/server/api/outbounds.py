from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import date

from database import get_db
from models import Outbound, Material
from schemas import OutboundCreate, OutboundResponse

router = APIRouter()

@router.get("", response_model=List[OutboundResponse])
def get_outbounds(
    ledger_id: UUID = None,
    start_date: date = None,
    end_date: date = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Outbound)

    if ledger_id:
        query = query.filter(Outbound.ledger_id == ledger_id)

    if start_date:
        query = query.filter(Outbound.outbound_date >= start_date)

    if end_date:
        query = query.filter(Outbound.outbound_date <= end_date)

    return query.offset(skip).limit(limit).all()

@router.post("", response_model=OutboundResponse)
def create_outbound(outbound: OutboundCreate, db: Session = Depends(get_db)):
    # 检查物料是否存在
    material = db.query(Material).filter(Material.id == outbound.ledger_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="物料不存在")

    # 检查库存是否足够
    if material.current_stock < outbound.quantity:
        raise HTTPException(status_code=400, detail=f"库存不足，当前库存{material.current_stock}")

    # 创建出库记录
    db_outbound = Outbound(**outbound.model_dump())
    db.add(db_outbound)

    # 更新库存
    material.current_stock -= outbound.quantity

    db.commit()
    db.refresh(db_outbound)
    return db_outbound

@router.get("/{outbound_id}", response_model=OutboundResponse)
def get_outbound(outbound_id: UUID, db: Session = Depends(get_db)):
    outbound = db.query(Outbound).filter(Outbound.id == outbound_id).first()
    if not outbound:
        raise HTTPException(status_code=404, detail="出库记录不存在")
    return outbound