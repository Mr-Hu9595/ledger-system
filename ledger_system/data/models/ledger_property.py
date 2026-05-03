"""LedgerProperty (台账属性表) model - 统一属性表，设备和材料通用"""
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ledger_system.data.models.base import BaseModel


class LedgerProperty(BaseModel):
    """统一属性表 for dynamic key-value attributes"""
    __tablename__ = "ledger_property"

    ledger_id = Column(UUID(as_uuid=True), ForeignKey("ledger.id"), nullable=False)
    property_key = Column(String(50), nullable=False)     # 属性名
    property_value = Column(String(500), default="")      # 属性值
    property_category = Column(String(20), default="")    # 分类

    # relationship
    ledger = relationship("Ledger", backref="properties")

    def __repr__(self):
        return f"<LedgerProperty {self.property_key}: {self.property_value}>"


# 预设属性类型（可扩展）
PROPERTY_KEYS = {
    # 设备属性
    "drive_type": ("驱动形式", "mechanical"),
    "nominal_diameter": ("公称直径", "mechanical"),
    "valve_position": ("阀门位置", "mechanical"),
    "design_pressure": ("设计压力", "pressure"),
    "design_temperature": ("设计温度", "temperature"),
    # 材料属性
    "medium": ("介质", "material"),
    "material_type": ("材质", "material"),
    "execution_standard": ("执行标准", "standard"),
    "surface_treatment": ("表面处理", "material"),
    # 通用属性
    "manufacturer": ("厂家", "material"),
    "brand": ("品牌", "brand"),
    "weight": ("重量", "physical"),
    "technical_params": ("技术参数", "specification"),
    "board": ("板块", "category"),
    "item_type": ("物资类型", "category"),
    "purchase_date": ("采购单下发时间", "date"),
}