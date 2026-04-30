"""MaterialProperty (物料属性表) model"""
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ledger_system.data.models.base import BaseModel


class MaterialProperty(BaseModel):
    """Material property table for dynamic key-value attributes (materials only)"""
    __tablename__ = "material_property"

    ledger_id = Column(UUID(as_uuid=True), ForeignKey("ledger.id"), nullable=False)
    property_key = Column(String(50), nullable=False)  # e.g., execution_standard, material_type
    property_value = Column(String(500), default="")
    property_type = Column(String(50), default="")  # e.g., standard, material, medium

    # relationship
    ledger = relationship("Ledger", backref="material_properties")

    def __repr__(self):
        return f"<MaterialProperty {self.property_key}: {self.property_value}>"


# Predefined property keys for materials
MATERIAL_PROPERTY_KEYS = {
    "execution_standard": ("执行标准", "standard"),
    "material_type": ("材质", "material"),
    "medium": ("介质", "material"),
    "surface_treatment": ("表面处理", "material"),
    "origin": ("产地/厂家", "material"),
    "brand": ("品牌", "material"),
}
