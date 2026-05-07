from sqlalchemy import Column, String, DateTime, Integer, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from database import Base


class EncodingRule(Base):
    __tablename__ = "encoding_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(18), unique=True, nullable=False)
    category_code = Column(String(2), nullable=False)
    category_name = Column(String(50), nullable=False)
    subcategory_code = Column(String(2), nullable=False)
    subcategory_name = Column(String(50), nullable=False)
    subsubcategory_code = Column(String(2), nullable=False)
    subsubcategory_name = Column(String(50), nullable=False)
    spec_code = Column(String(2), nullable=False)
    spec_name = Column(String(50), nullable=False)
    unit_code = Column(String(2), nullable=False)
    unit_name = Column(String(20), nullable=False)
    supplier_code = Column(String(2), nullable=False)
    supplier_name = Column(String(50), nullable=False)
    year_code = Column(String(2), nullable=False)
    keywords = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MaterialCodeSequence(Base):
    __tablename__ = "material_code_sequence"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category_code = Column(String(2), nullable=False)
    year_code = Column(String(2), nullable=False)
    last_sequence = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
