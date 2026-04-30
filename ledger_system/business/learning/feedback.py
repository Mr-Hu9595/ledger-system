"""Feedback learning for rule improvement"""
import json
from datetime import datetime
from typing import Dict, Any
from uuid import UUID

from sqlalchemy.orm import Session
from ledger_system.data.models.rule_learning import RuleLearning


class FeedbackLearning:
    """Handle user feedback and learn from corrections"""

    def __init__(self, session: Session):
        self.session = session

    def record_feedback(self, raw_text: str, ai_result: Dict[str, Any],
                        rule_result: Dict[str, Any], corrected: Dict[str, Any],
                        source: str = "user_correct") -> RuleLearning:
        """Record user correction feedback"""
        record = RuleLearning(
            raw_text=raw_text,
            ai_result=ai_result,
            rule_result=rule_result,
            corrected_result=corrected,
            source=source
        )
        self.session.add(record)
        self.session.flush()
        return record

    def get_similar_learning(self, text: str, limit: int = 5) -> list:
        """Get similar learning records for pattern matching"""
        records = self.session.query(RuleLearning).filter(
            RuleLearning.raw_text.ilike(f"%{text[:20]}%")
        ).order_by(RuleLearning.created_at.desc()).limit(limit).all()

        return [
            {
                "raw_text": r.raw_text,
                "corrected_result": r.corrected_result,
                "source": r.source
            }
            for r in records
        ]

    def update_local_rules(self, learning_records: list) -> Dict[str, Any]:
        """Update local rules based on learning records"""
        material_aliases = {}
        supplier_aliases = {}

        for record in learning_records:
            if record.get("source") == "user_correct":
                corrected = record.get("corrected_result", {})
                raw = record.get("raw_text", "")

                # Extract material alias
                if "material_name" in corrected:
                    for alias in [raw, raw[:4], raw[2:]]:
                        if alias and len(alias) >= 2:
                            material_aliases[alias] = corrected["material_name"]
                            break

                # Extract supplier alias
                if "supplier" in corrected and "supplier" in corrected:
                    pass

        return {
            "material_aliases": material_aliases,
            "supplier_aliases": supplier_aliases
        }