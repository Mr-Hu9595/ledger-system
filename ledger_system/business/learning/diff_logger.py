"""Difference logger for AI vs rule comparison"""
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any

from sqlalchemy.orm import Session
from ledger_system.data.models.rule_learning import RuleLearning


class DiffLogger:
    """Log differences between AI and rule extraction results"""

    def __init__(self, session: Session):
        self.session = session

    def log_diff(self, raw_text: str, ai_result: Dict[str, Any],
                 rule_result: Dict[str, Any]) -> None:
        """Log difference between AI and rule results"""
        # Calculate difference score
        diff_score = self._calculate_diff_score(ai_result, rule_result)

        # Only log if there's meaningful difference
        if diff_score > 0:
            record = RuleLearning(
                raw_text=raw_text,
                ai_result=ai_result,
                rule_result=rule_result,
                corrected_result={},
                source="ai_rule_diff"
            )
            self.session.add(record)
            self.session.flush()

    def _calculate_diff_score(self, ai_result: Dict[str, Any],
                              rule_result: Dict[str, Any]) -> float:
        """Calculate difference score between two results"""
        score = 0.0

        fields = ["material_name", "quantity", "unit", "supplier"]
        for field in fields:
            ai_val = ai_result.get(field, "")
            rule_val = rule_result.get(field, "")

            if ai_val and rule_val and str(ai_val).lower() != str(rule_val).lower():
                score += 1.0

        return score

    def get_significant_diffs(self, limit: int = 20) -> list:
        """Get significant differences for analysis"""
        records = self.session.query(RuleLearning).filter(
            RuleLearning.source == "ai_rule_diff"
        ).order_by(RuleLearning.created_at.desc()).limit(limit).all()

        return [
            {
                "id": str(r.id),
                "raw_text": r.raw_text,
                "ai_result": r.ai_result,
                "rule_result": r.rule_result,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in records
        ]