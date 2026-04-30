"""Local rule engine for entity extraction fallback"""
import re
import json
from datetime import date
from typing import Dict, Any, Optional
from pathlib import Path

from ledger_system.data.models.rule_learning import RuleLearning


# Common patterns for construction materials
MATERIAL_PATTERNS = [
    r"钢筋", r"水泥", r"混凝土", r"砖", r"砂", r"石", r"木材",
    r"钢管", r"钢板", r"电缆", r"电线", r"开关", r"灯具",
    r"水泵", r"电机", r"变压器", r"配电柜"
]

UNIT_PATTERNS = [
    (r"(\d+(?:\.\d+)?)\s*吨", "吨"),
    (r"(\d+(?:\.\d+)?)\s*米", "米"),
    (r"(\d+(?:\.\d+)?)\s*个", "个"),
    (r"(\d+(?:\.\d+)?)\s*根", "根"),
    (r"(\d+(?:\.\d+)?)\s*卷", "卷"),
    (r"(\d+(?:\.\d+)?)\s*箱", "箱"),
    (r"(\d+(?:\.\d+)?)\s*块", "块"),
    (r"(\d+(?:\.\d+)?)\s*方", "方"),
]

SUPPLIER_PATTERNS = [
    r"来自\s*(.+?)(?:\s|,|$)",
    r"from\s+(.+?)(?:\s|,|$)",
    r"供应商[：:]\s*(.+?)(?:\s|,|$)",
    r"厂家[：:]\s*(.+?)(?:\s|,|$)",
]


class RuleEngine:
    """Local rule engine for entity extraction"""

    def __init__(self, rules_path: Optional[str] = None):
        self.rules_path = rules_path or self._get_default_rules_path()
        self.local_rules = self._load_local_rules()

    def _get_default_rules_path(self) -> str:
        """Get default rules path"""
        return str(Path(__file__).parent.parent.parent / "rules" / "local_rules.json")

    def _load_local_rules(self) -> Dict[str, Any]:
        """Load local rules from JSON file"""
        path = Path(self.rules_path)
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"material_aliases": {}, "supplier_aliases": {}}

    def extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract entities using local rules"""
        result = {
            "material_name": self._extract_material(text),
            "quantity": self._extract_quantity(text),
            "unit": self._extract_unit(text),
            "supplier": self._extract_supplier(text),
            "date": date.today().isoformat(),
            "notes": ""
        }
        return result

    def _extract_material(self, text: str) -> str:
        """Extract material name"""
        for pattern in MATERIAL_PATTERNS:
            match = re.search(pattern, text)
            if match:
                return match.group(0)

        # Check aliases
        aliases = self.local_rules.get("material_aliases", {})
        for alias, material in aliases.items():
            if alias in text:
                return material

        # Default: try to find any Chinese material-related word
        match = re.search(r"[一-龥]{2,6}(?:材料|物资|货物|商品)", text)
        if match:
            return match.group(0)[:-2] if match.group(0).endswith("材料") else match.group(0)

        return ""

    def _extract_quantity(self, text: str) -> Optional[float]:
        """Extract quantity"""
        for pattern, _ in UNIT_PATTERNS:
            match = re.search(pattern, text)
            if match:
                return float(match.group(1))
        return None

    def _extract_unit(self, text: str) -> str:
        """Extract unit"""
        for pattern, unit in UNIT_PATTERNS:
            if re.search(pattern, text):
                return unit
        return ""

    def _extract_supplier(self, text: str) -> str:
        """Extract supplier"""
        for pattern in SUPPLIER_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # Check aliases
        aliases = self.local_rules.get("supplier_aliases", {})
        for alias, supplier in aliases.items():
            if alias in text:
                return supplier

        return ""

    def apply_learned_rules(self, text: str, learned_rules: list) -> Dict[str, Any]:
        """Apply learned rules from feedback"""
        result = self.extract_entities(text)

        for rule in learned_rules:
            if rule.get("source") == "user_correct" and rule.get("raw_text"):
                # Simple pattern matching - if raw_text is substring of input
                if rule["raw_text"] in text or text in rule["raw_text"]:
                    corrected = rule.get("corrected_result", {})
                    result.update(corrected)

        return result


# Default rules file if it doesn't exist
DEFAULT_RULES = {
    "material_aliases": {
        "盘圆": "钢筋",
        "螺纹钢": "钢筋",
        "PC32.5": "水泥",
        "PO42.5": "水泥"
    },
    "supplier_aliases": {
        "杭州建材": "杭州建材有限公司",
        "上海钢铁": "上海钢铁集团"
    }
}