"""Category (分类表) model"""
from sqlalchemy import Column, Integer, String, ForeignKey
from ledger_system.data.models.base import BaseModel


class Category(BaseModel):
    """Category table for material classification hierarchy"""
    __tablename__ = "category"

    level = Column(Integer, nullable=False)  # 1=大类, 2=中类, 3=小类
    parent_code = Column(String(18), default="")  # 父级编码
    code = Column(String(2), nullable=False)  # 分类编码
    name = Column(String(100), nullable=False)  # 分类名称
    description = Column(String(500), default="")  # 说明

    def __repr__(self):
        return f"<Category {self.code}: {self.name}>"
