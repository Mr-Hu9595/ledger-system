"""Outbound (出库记录) model"""
from sqlalchemy import Column, String, Numeric, Date, Time, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ledger_system.data.models.base import BaseModel


class Outbound(BaseModel):
    """Outbound records for materials/equipment usage"""
    __tablename__ = "outbound"

    ledger_id = Column(UUID(as_uuid=True), ForeignKey("ledger.id"), nullable=False)
    quantity = Column(Numeric(precision=10, scale=2), nullable=False)
    usage = Column(String(200), default="")
    outbound_date = Column(Date, nullable=False)
    outbound_time = Column(Time, nullable=False)
    receiver = Column(String(100), default="")
    outbound_operator = Column(String(100), default="")
    original_document_path = Column(String(500), default="")  # 原始单据路径
    notes = Column(Text, default="")

    # relationship
    ledger = relationship("Ledger", backref="outbound_records")

    def __repr__(self):
        return f"<Outbound {self.ledger_id}: -{self.quantity}>"
