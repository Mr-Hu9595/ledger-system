"""Ledger (台账主表) model"""
from sqlalchemy import Column, String, Numeric
from ledger_system.data.models.base import BaseModel


class Ledger(BaseModel):
    """Main ledger table for materials and equipment"""
    __tablename__ = "ledger"

    category = Column(String(20), nullable=False)  # material / equipment
    name = Column(String(200), nullable=False)
    specification = Column(String(200), default="")
    unit = Column(String(20), default="")
    current_stock = Column(Numeric(precision=10, scale=2), default=0)
    min_stock = Column(Numeric(precision=10, scale=2), default=0)

    def __repr__(self):
        return f"<Ledger {self.name} ({self.category}): {self.current_stock} {self.unit}>"