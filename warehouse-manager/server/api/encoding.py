from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
from uuid import UUID

from database import get_db
from models.encoding import EncodingRule, MaterialCodeSequence
from schemas.encoding import (
    EncodingRuleCreate, EncodingRuleUpdate, EncodingRuleResponse,
    CodeGenerateRequest, CodeGenerateResponse, CategoryListResponse, CategoryInfo
)
from api import encoding_service


router = APIRouter()


@router.get("/rules", response_model=List[EncodingRuleResponse])
def get_encoding_rules(
    category_code: Optional[str] = Query(None, description="按大类编码过滤"),
    keyword: Optional[str] = Query(None, description="关键字搜索"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(EncodingRule)

    if category_code:
        query = query.filter(EncodingRule.category_code == category_code)

    if keyword:
        query = query.filter(
            or_(
                EncodingRule.keywords.ilike(f"%{keyword}%"),
                EncodingRule.category_name.ilike(f"%{keyword}%"),
                EncodingRule.code.ilike(f"%{keyword}%")
            )
        )

    if is_active is not None:
        query = query.filter(EncodingRule.is_active == is_active)

    rules = query.offset(skip).limit(limit).all()
    return rules


@router.get("/rules/{rule_id}", response_model=EncodingRuleResponse)
def get_encoding_rule(rule_id: UUID, db: Session = Depends(get_db)):
    rule = db.query(EncodingRule).filter(EncodingRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="编码规则不存在")
    return rule


@router.post("/rules", response_model=EncodingRuleResponse)
def create_encoding_rule(rule: EncodingRuleCreate, db: Session = Depends(get_db)):
    # Check if code already exists
    existing = db.query(EncodingRule).filter(EncodingRule.code == rule.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="编码已存在")

    db_rule = EncodingRule(**rule.model_dump())
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule


@router.put("/rules/{rule_id}", response_model=EncodingRuleResponse)
def update_encoding_rule(rule_id: UUID, rule: EncodingRuleUpdate, db: Session = Depends(get_db)):
    db_rule = db.query(EncodingRule).filter(EncodingRule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="编码规则不存在")

    update_data = rule.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if value is not None:
            setattr(db_rule, key, value)

    db.commit()
    db.refresh(db_rule)
    return db_rule


@router.delete("/rules/{rule_id}")
def delete_encoding_rule(rule_id: UUID, db: Session = Depends(get_db)):
    db_rule = db.query(EncodingRule).filter(EncodingRule.id == rule_id).first()
    if not db_rule:
        raise HTTPException(status_code=404, detail="编码规则不存在")

    db.delete(db_rule)
    db.commit()
    return {"message": "删除成功"}


@router.get("/categories", response_model=CategoryListResponse)
def get_categories():
    """Get all 14 material categories."""
    categories = encoding_service.get_categories()
    return {"categories": [CategoryInfo(**c) for c in categories]}


@router.post("/generate", response_model=CodeGenerateResponse)
def generate_code(request: CodeGenerateRequest, db: Session = Depends(get_db)):
    """
    Generate a new 18-digit material code.
    The code is constructed from: category(2) + subcategory(2) + subsubcategory(2) +
    spec(2) + unit(2) + supplier(2) + year(2) + sequence(4)
    """
    result = encoding_service.generate_code(
        db=db,
        category_code=request.category_code,
        supplier_code=request.supplier_code,
        year_code=request.year_code,
        subcategory_code=request.subcategory_code,
        subsubcategory_code=request.subsubcategory_code,
        spec_code=request.spec_code,
        unit_code=request.unit_code
    )
    return CodeGenerateResponse(**result)


@router.get("/match/{keyword}", response_model=EncodingRuleResponse)
def match_keyword(keyword: str, db: Session = Depends(get_db)):
    """
    Find the best matching encoding rule based on keyword.
    Longest match wins.
    """
    rule = encoding_service.match_keyword(db, keyword)
    if not rule:
        raise HTTPException(status_code=404, detail="未找到匹配的编码规则")
    return rule
