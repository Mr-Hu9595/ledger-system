"""EquipmentProperty (设备属性表) model"""
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ledger_system.data.models.base import BaseModel


class EquipmentProperty(BaseModel):
    """Equipment property table for dynamic key-value attributes (equipment only)"""
    __tablename__ = "equipment_property"

    ledger_id = Column(UUID(as_uuid=True), ForeignKey("ledger.id"), nullable=False)
    property_key = Column(String(50), nullable=False)  # e.g., drive_type, nominal_diameter
    property_value = Column(String(500), default="")
    property_type = Column(String(50), default="")  # e.g., mechanical, pressure, temperature

    # relationship
    ledger = relationship("Ledger", backref="equipment_properties")

    def __repr__(self):
        return f"<EquipmentProperty {self.property_key}: {self.property_value}>"


# Predefined property keys for equipment
EQUIPMENT_PROPERTY_KEYS = {
    "drive_type": ("驱动形式", "mechanical"),
    "nominal_diameter": ("公称直径", "mechanical"),
    "valve_position": ("阀门位置", "mechanical"),
    "design_pressure": ("设计压力", "pressure"),
    "design_temperature": ("设计温度", "temperature"),
    "manufacturer": ("厂家", "material"),
}
