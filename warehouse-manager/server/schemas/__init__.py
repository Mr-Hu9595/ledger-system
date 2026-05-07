from pydantic import BaseModel, field_validator
from typing import Optional, List, Any
from datetime import date, datetime, time
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

class InboundUpdate(BaseModel):
    ledger_id: Optional[UUID] = None
    inbound_date: Optional[date] = None
    quantity: Optional[float] = None
    supplier: Optional[str] = None
    inbound_operator: Optional[str] = None
    original_document_path: Optional[str] = None
    document_source: Optional[str] = None
    notes: Optional[str] = None

class InboundResponse(InboundBase):
    id: UUID
    inbound_time: time
    ledger: Optional[Any] = None

    class Config:
        from_attributes = True

    @field_validator('ledger', mode='before')
    @classmethod
    def convert_ledger_to_dict(cls, v):
        if v is None:
            return None
        if hasattr(v, '__dict__'):
            # SQLAlchemy object - extract relevant fields
            return {
                'id': str(v.id) if hasattr(v, 'id') else None,
                'name': getattr(v, 'name', None),
                'specification': getattr(v, 'specification', None),
                'unit': getattr(v, 'unit', None),
                'category': getattr(v, 'category', None),
                'inbound_status': getattr(v, 'inbound_status', None),
                'current_stock': getattr(v, 'current_stock', None),
                'min_stock': getattr(v, 'min_stock', None),
            }
        return v

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

class OutboundUpdate(BaseModel):
    ledger_id: Optional[UUID] = None
    outbound_date: Optional[date] = None
    quantity: Optional[float] = None
    usage: Optional[str] = None
    receiver: Optional[str] = None
    outbound_operator: Optional[str] = None
    notes: Optional[str] = None

class OutboundResponse(OutboundBase):
    id: UUID
    outbound_time: time
    ledger: Optional[Any] = None

    class Config:
        from_attributes = True

    @field_validator('ledger', mode='before')
    @classmethod
    def convert_ledger_to_dict(cls, v):
        if v is None:
            return None
        if hasattr(v, '__dict__'):
            # SQLAlchemy object - extract relevant fields
            return {
                'id': str(v.id) if hasattr(v, 'id') else None,
                'name': getattr(v, 'name', None),
                'specification': getattr(v, 'specification', None),
                'unit': getattr(v, 'unit', None),
                'category': getattr(v, 'category', None),
                'inbound_status': getattr(v, 'inbound_status', None),
                'current_stock': getattr(v, 'current_stock', None),
                'min_stock': getattr(v, 'min_stock', None),
            }
        return v

from schemas.encoding import (
    EncodingRuleCreate, EncodingRuleUpdate, EncodingRuleResponse,
    CodeGenerateRequest, CodeGenerateResponse, CategoryListResponse, CategoryInfo
)