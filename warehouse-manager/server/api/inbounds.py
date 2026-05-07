from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List
from uuid import UUID
from datetime import date
from decimal import Decimal

from database import get_db
from models import Inbound, Material
from schemas import InboundCreate, InboundResponse, InboundUpdate

router = APIRouter()

@router.get("", response_model=List[InboundResponse])
def get_inbounds(
    ledger_id: UUID = None,
    start_date: date = None,
    end_date: date = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Inbound).options(joinedload(Inbound.ledger))

    if ledger_id:
        query = query.filter(Inbound.ledger_id == ledger_id)

    if start_date:
        query = query.filter(Inbound.inbound_date >= start_date)

    if end_date:
        query = query.filter(Inbound.inbound_date <= end_date)

    return query.offset(skip).limit(limit).all()

@router.post("", response_model=InboundResponse)
def create_inbound(inbound: InboundCreate, db: Session = Depends(get_db)):
    # 检查物料是否存在
    material = db.query(Material).filter(Material.id == inbound.ledger_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="物料不存在")

    # 计算 inbound_sequence: 这是该物料第N次入库
    max_seq = db.query(func.max(Inbound.inbound_sequence)).filter(
        Inbound.ledger_id == inbound.ledger_id
    ).scalar()
    inbound_sequence = (max_seq or 0) + 1

    # 计算 cumulative_in: 累计入库量
    total_in = db.query(func.sum(Inbound.quantity)).filter(
        Inbound.ledger_id == inbound.ledger_id
    ).scalar() or 0
    cumulative_in = float(total_in) + inbound.quantity

    # 创建入库记录
    inbound_data = inbound.model_dump()
    inbound_data['inbound_sequence'] = inbound_sequence
    inbound_data['cumulative_in'] = cumulative_in

    db_inbound = Inbound(**inbound_data)
    db.add(db_inbound)

    # 更新库存
    material.current_stock += inbound.quantity

    # 更新入库状态为已入库
    material.inbound_status = "已入库"

    db.commit()
    db.refresh(db_inbound)
    return db_inbound

@router.get("/{inbound_id}", response_model=InboundResponse)
def get_inbound(inbound_id: UUID, db: Session = Depends(get_db)):
    inbound = db.query(Inbound).options(joinedload(Inbound.ledger)).filter(Inbound.id == inbound_id).first()
    if not inbound:
        raise HTTPException(status_code=404, detail="入库记录不存在")
    return inbound

@router.put("/{inbound_id}", response_model=InboundResponse)
def update_inbound(inbound_id: UUID, inbound_update: InboundUpdate, db: Session = Depends(get_db)):
    inbound = db.query(Inbound).options(joinedload(Inbound.ledger)).filter(Inbound.id == inbound_id).first()
    if not inbound:
        raise HTTPException(status_code=404, detail="入库记录不存在")

    # 获取旧值用于计算库存变化
    old_quantity = inbound.quantity
    old_ledger_id = inbound.ledger_id

    # 更新字段
    update_data = inbound_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(inbound, key, value)

    new_quantity = inbound.quantity
    new_ledger_id = inbound.ledger_id

    # 如果物料或数量变化，调整库存
    if old_ledger_id != new_ledger_id:
        # 旧物料减库存
        old_material = db.query(Material).filter(Material.id == old_ledger_id).first()
        if old_material:
            old_material.current_stock -= old_quantity
        # 新物料加库存
        new_material = db.query(Material).filter(Material.id == new_ledger_id).first()
        if new_material:
            new_material.current_stock += new_quantity
    elif old_quantity != new_quantity:
        # 同一物料数量变化
        material = db.query(Material).filter(Material.id == new_ledger_id).first()
        if material:
            material.current_stock += (new_quantity - old_quantity)

    db.commit()
    db.refresh(inbound)
    return inbound

@router.delete("/{inbound_id}")
def delete_inbound(inbound_id: UUID, db: Session = Depends(get_db)):
    inbound = db.query(Inbound).options(joinedload(Inbound.ledger)).filter(Inbound.id == inbound_id).first()
    if not inbound:
        raise HTTPException(status_code=404, detail="入库记录不存在")

    # 恢复库存
    material = db.query(Material).filter(Material.id == inbound.ledger_id).first()
    if material:
        material.current_stock -= inbound.quantity

    db.delete(inbound)
    db.commit()
    return {"success": True, "message": "删除成功"}
