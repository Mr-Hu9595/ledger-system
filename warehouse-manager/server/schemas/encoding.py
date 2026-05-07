from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class EncodingRuleBase(BaseModel):
    code: str
    category_code: str
    category_name: str
    subcategory_code: str
    subcategory_name: str
    subsubcategory_code: str
    subsubcategory_name: str
    spec_code: str
    spec_name: str
    unit_code: str
    unit_name: str
    supplier_code: str
    supplier_name: str
    year_code: str
    keywords: Optional[str] = None
    is_active: bool = True


class EncodingRuleCreate(EncodingRuleBase):
    pass


class EncodingRuleUpdate(BaseModel):
    category_code: Optional[str] = None
    category_name: Optional[str] = None
    subcategory_code: Optional[str] = None
    subcategory_name: Optional[str] = None
    subsubcategory_code: Optional[str] = None
    subsubcategory_name: Optional[str] = None
    spec_code: Optional[str] = None
    spec_name: Optional[str] = None
    unit_code: Optional[str] = None
    unit_name: Optional[str] = None
    supplier_code: Optional[str] = None
    supplier_name: Optional[str] = None
    year_code: Optional[str] = None
    keywords: Optional[str] = None
    is_active: Optional[bool] = None


class EncodingRuleResponse(EncodingRuleBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CodeGenerateRequest(BaseModel):
    category_code: str
    supplier_code: str
    year_code: str
    subcategory_code: str = "01"
    subsubcategory_code: str = "01"
    spec_code: str = "01"
    unit_code: str = "01"


class CodeGenerateResponse(BaseModel):
    code: str
    category_code: str
    category_name: str
    subcategory_code: str
    subcategory_name: str
    subsubcategory_code: str
    subsubcategory_name: str
    spec_code: str
    spec_name: str
    unit_code: str
    unit_name: str
    supplier_code: str
    supplier_name: str
    year_code: str


class CategoryInfo(BaseModel):
    code: str
    name: str


class CategoryListResponse(BaseModel):
    categories: List[CategoryInfo]
