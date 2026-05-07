from sqlalchemy.orm import Session
from sqlalchemy import update
from models.encoding import EncodingRule, MaterialCodeSequence
from datetime import datetime


# Hardcoded 14 categories based on existing material classification system
CATEGORIES = [
    {"code": "01", "name": "电气设备"},
    {"code": "02", "name": "电线电缆"},
    {"code": "03", "name": "管材管件"},
    {"code": "04", "name": "建筑材料"},
    {"code": "05", "name": "五金工具"},
    {"code": "06", "name": "化工材料"},
    {"code": "07", "name": "照明设备"},
    {"code": "08", "name": "消防器材"},
    {"code": "09", "name": "仪表仪器"},
    {"code": "10", "name": "机械设备"},
    {"code": "11", "name": "劳保用品"},
    {"code": "12", "name": "办公用品"},
    {"code": "13", "name": "其他材料"},
    {"code": "14", "name": "钢材类"},
]

# Subcategory mappings (simplified - can be expanded)
SUBCATEGORIES = {
    "01": {"code": "01", "name": "通用"},
    "02": {"code": "01", "name": "通用"},
    "03": {"code": "01", "name": "通用"},
    "04": {"code": "01", "name": "通用"},
    "05": {"code": "01", "name": "通用"},
    "06": {"code": "01", "name": "通用"},
    "07": {"code": "01", "name": "通用"},
    "08": {"code": "01", "name": "通用"},
    "09": {"code": "01", "name": "通用"},
    "10": {"code": "01", "name": "通用"},
    "11": {"code": "01", "name": "通用"},
    "12": {"code": "01", "name": "通用"},
    "13": {"code": "01", "name": "通用"},
    "14": {"code": "01", "name": "通用"},
}

# Specification mappings (simplified)
SPECS = {
    "01": {"code": "01", "name": "标准"},
}

# Unit mappings
UNITS = {
    "01": {"code": "01", "name": "个"},
    "02": {"code": "02", "name": "米"},
    "03": {"code": "03", "name": "千克"},
    "04": {"code": "04", "name": "吨"},
    "05": {"code": "05", "name": "套"},
    "06": {"code": "06", "name": "根"},
    "07": {"code": "07", "name": "卷"},
    "08": {"code": "08", "name": "箱"},
}

# Supplier mappings (simplified - can be expanded)
SUPPLIERS = {
    "01": {"code": "01", "name": "默认供应商"},
}


def generate_code(db: Session, category_code: str, supplier_code: str, year_code: str,
                  subcategory_code: str = "01", subsubcategory_code: str = "01",
                  spec_code: str = "01", unit_code: str = "01") -> dict:
    """
    Generate a new 18-digit material code.
    Returns the generated code and full rule information.
    """
    # Get category name
    category_name = next((c["name"] for c in CATEGORIES if c["code"] == category_code), "未知类别")

    # Get subcategory name
    subcategory_name = SUBCATEGORIES.get(subcategory_code, {"name": "通用"}).get("name", "通用")

    # Get subsubcategory name
    subsubcategory_name = "小类"

    # Get spec name
    spec_name = SPECS.get(spec_code, {"name": "标准"}).get("name", "标准")

    # Get unit name
    unit_name = UNITS.get(unit_code, {"name": "个"}).get("name", "个")

    # Get supplier name
    supplier_name = SUPPLIERS.get(supplier_code, {"name": "默认供应商"}).get("name", "默认供应商")

    # Get or create sequence record
    seq_record = db.query(MaterialCodeSequence).filter(
        MaterialCodeSequence.category_code == category_code,
        MaterialCodeSequence.year_code == year_code
    ).first()

    if not seq_record:
        seq_record = MaterialCodeSequence(
            category_code=category_code,
            year_code=year_code,
            last_sequence=0
        )
        db.add(seq_record)

    # Increment sequence
    seq_record.last_sequence += 1
    new_sequence = seq_record.last_sequence

    # Format sequence number (4 digits)
    sequence_str = f"{new_sequence:04d}"

    # Build the 18-digit code
    code = (f"{category_code}{subcategory_code}{subsubcategory_code}"
            f"{spec_code}{unit_code}{supplier_code}{year_code}{sequence_str}")

    db.commit()

    return {
        "code": code,
        "category_code": category_code,
        "category_name": category_name,
        "subcategory_code": subcategory_code,
        "subcategory_name": subcategory_name,
        "subsubcategory_code": subsubcategory_code,
        "subsubcategory_name": subsubcategory_name,
        "spec_code": spec_code,
        "spec_name": spec_name,
        "unit_code": unit_code,
        "unit_name": unit_name,
        "supplier_code": supplier_code,
        "supplier_name": supplier_name,
        "year_code": year_code,
    }


def match_keyword(db: Session, keyword: str) -> EncodingRule:
    """
    Find the best matching encoding rule based on keyword.
    Longest match wins.
    """
    if not keyword:
        return None

    keyword_lower = keyword.lower().strip()

    # Search for matching rules
    rules = db.query(EncodingRule).filter(
        EncodingRule.is_active == True
    ).all()

    best_match = None
    best_match_length = 0

    for rule in rules:
        if not rule.keywords:
            continue

        # Split keywords and check for matches
        rule_keywords = [k.strip().lower() for k in rule.keywords.split(",")]
        for kw in rule_keywords:
            if kw and keyword_lower.find(kw) != -1:
                # Found a match, check if it's longer than current best
                if len(kw) > best_match_length:
                    best_match_length = len(kw)
                    best_match = rule

    return best_match


def get_categories() -> list:
    """Return the hardcoded 14 categories."""
    return CATEGORIES
