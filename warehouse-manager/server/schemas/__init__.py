from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID

class MaterialBase(BaseModel):
    name: str
    specification: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    current_stock: float = 0
    min_stock: float = 0
    material_code: Optional[str] = None
    inbound_status: str = "待入库"
    planned_inbound_date: Optional[date] = None
    purchase_date: Optional[date] = None
    notes: Optional[str] = None

class MaterialCreate(MaterialBase):
    pass

class MaterialUpdate(MaterialBase):
    pass

class MaterialResponse(MaterialBase):
    id: UUID
    properties: List[dict] = []

    class Config:
        from_attributes = True

class InboundBase(BaseModel):
    ledger_id: UUID
    inbound_date: date
    quantity: float
    supplier: Optional[str] = None
    inbound_operator: Optional[str] = None
    original_document_path: Optional[str] = None
    document_source: Optional[str] = None
    notes: Optional[str] = None

class InboundCreate(InboundBase):
    pass

class InboundResponse(InboundBase):
    id: UUID
    inbound_time: datetime

    class Config:
        from_attributes = True

class OutboundBase(BaseModel):
    ledger_id: UUID
    outbound_date: date
    quantity: float
    usage: Optional[str] = None
    receiver: Optional[str] = None
    outbound_operator: Optional[str] = None
    notes: Optional[str] = None

class OutboundCreate(OutboundBase):
    pass

class OutboundResponse(OutboundBase):
    id: UUID
    outbound_time: datetime

    class Config:
        from_attributes = True

from schemas.encoding import (
    EncodingRuleCreate, EncodingRuleUpdate, EncodingRuleResponse,
    CodeGenerateRequest, CodeGenerateResponse, CategoryListResponse, CategoryInfo
)