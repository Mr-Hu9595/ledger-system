"""RuleLearning (规则学习库) model"""
from sqlalchemy import Column, String, Text, JSON
from ledger_system.data.models.base import BaseModel


class RuleLearning(BaseModel):
    """Rule learning database for AI/rule feedback and diff logging"""
    __tablename__ = "rule_learning"

    raw_text = Column(Text, nullable=False)
    ai_result = Column(JSON, default={})
    rule_result = Column(JSON, default={})
    corrected_result = Column(JSON, default={})
    source = Column(String(20), default="ai")  # ai / rule / user_correct

    def __repr__(self):
        return f"<RuleLearning {self.id}: {self.source}>"