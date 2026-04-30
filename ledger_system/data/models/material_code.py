"""MaterialCode (物料编码表) model"""
from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship
from ledger_system.data.models.base import BaseModel


class MaterialCode(BaseModel):
    """Material code table for 18-digit material identification"""
    __tablename__ = "material_code"

    code = Column(String(18), unique=True, nullable=False)  # 编码(唯一)
    category = Column(String(2), nullable=False)  # 大类编码
    mid_category = Column(String(2), nullable=False)  # 中类编码
    sub_category = Column(String(2), nullable=False)  # 小类编码
    spec = Column(String(2), nullable=False)  # 规格编码
    unit = Column(String(2), nullable=False)  # 单位编码
    supplier_code = Column(String(2), nullable=False)  # 供应商编码
    year = Column(String(2), nullable=False)  # 年份编码
    sequence = Column(Integer, nullable=False)  # 流水号
    name = Column(String(200), nullable=False)  # 物料名称
    specification = Column(String(200), default="")  # 规格型号

    def __repr__(self):
        return f"<MaterialCode {self.code}: {self.name}>"
