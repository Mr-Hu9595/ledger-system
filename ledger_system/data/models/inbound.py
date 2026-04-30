"""Inbound (入库记录) model"""
from sqlalchemy import Column, String, Numeric, Date, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ledger_system.data.models.base import BaseModel


class Inbound(BaseModel):
    """Inbound records for materials/equipment"""
    __tablename__ = "inbound"

    ledger_id = Column(UUID(as_uuid=True), ForeignKey("ledger.id"), nullable=False)
    quantity = Column(Numeric(precision=10, scale=2), nullable=False)
    supplier = Column(String(200), default="")
    inbound_date = Column(Date, nullable=False)
    document_source = Column(String(500), default="")
    operator = Column(String(100), default="")
    notes = Column(Text, default="")

    # relationship
    ledger = relationship("Ledger", backref="inbound_records")

    def __repr__(self):
        return f"<Inbound {self.ledger_id}: +{self.quantity}>"