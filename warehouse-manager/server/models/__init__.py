from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer, Date, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from database import Base

class Material(Base):
    __tablename__ = "ledger"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    specification = Column(String(200))
    category = Column(String(50))
    unit = Column(String(20))
    current_stock = Column(Float, default=0)
    min_stock = Column(Float, default=0)
    material_code = Column(String(50))
    inbound_status = Column(String(20), default="待入库")
    planned_inbound_date = Column(Date)
    purchase_date = Column(Date)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    properties = relationship("LedgerProperty", back_populates="ledger", cascade="all, delete-orphan")
    inbounds = relationship("Inbound", back_populates="ledger", cascade="all, delete-orphan")
    outbounds = relationship("Outbound", back_populates="ledger", cascade="all, delete-orphan")

class LedgerProperty(Base):
    __tablename__ = "ledger_property"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ledger_id = Column(UUID(as_uuid=True), ForeignKey("ledger.id"), nullable=False)
    property_key = Column(String(50), nullable=False)
    property_value = Column(String(500), default="")
    property_category = Column(String(20), default="")

    ledger = relationship("Material", back_populates="properties")

class Inbound(Base):
    __tablename__ = "inbound"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ledger_id = Column(UUID(as_uuid=True), ForeignKey("ledger.id"), nullable=False)
    inbound_date = Column(Date, nullable=False)
    inbound_time = Column(DateTime, default=datetime.utcnow)
    quantity = Column(Float, nullable=False)
    supplier = Column(String(200))
    inbound_operator = Column(String(100))
    original_document_path = Column(String(500))
    document_source = Column(String(100))
    notes = Column(Text)

    ledger = relationship("Material", back_populates="inbounds")

class Outbound(Base):
    __tablename__ = "outbound"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ledger_id = Column(UUID(as_uuid=True), ForeignKey("ledger.id"), nullable=False)
    outbound_date = Column(Date, nullable=False)
    outbound_time = Column(DateTime, default=datetime.utcnow)
    quantity = Column(Float, nullable=False)
    usage = Column(String(200))
    receiver = Column(String(100))
    outbound_operator = Column(String(100))
    original_document_path = Column(String(500))
    notes = Column(Text)

    ledger = relationship("Material", back_populates="outbounds")

from models.encoding import EncodingRule, MaterialCodeSequence