"""Ledger (台账主表) model"""
from sqlalchemy import Column, String, Numeric, ForeignKey, Date, Text, Integer
from sqlalchemy.orm import relationship
from ledger_system.data.models.base import BaseModel


class Ledger(BaseModel):
    """Main ledger table for materials and equipment"""
    __tablename__ = "ledger"

    category = Column(String(20), nullable=False)  # material / equipment
    name = Column(String(200), nullable=False)
    specification = Column(String(500), default="")  # 规格型号
    unit = Column(String(20), default="")
    current_stock = Column(Numeric(precision=10, scale=2), default=0)
    min_stock = Column(Numeric(precision=10, scale=2), default=0)
    purchase_date = Column(Date, nullable=True)  # 采购日期
    material_code = Column(String(18), ForeignKey("material_code.code"), nullable=True)
    notes = Column(Text, default="")  # 备注
    inbound_status = Column(String(20), default="待入库")  # 待入库/部分入库/已入库
    planned_inbound_date = Column(Date, nullable=True)  # 计划入库日期

    # relationships
    code_info = relationship("MaterialCode", foreign_keys=[material_code], lazy="joined")

    def __repr__(self):
        return f"<Ledger {self.name} ({self.category}): {self.current_stock} {self.unit}>"
