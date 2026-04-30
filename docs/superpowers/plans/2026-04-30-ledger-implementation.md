# 台账管理系统 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a CLI-driven ledger system for construction site material/equipment inventory with AI-powered natural language input, document OCR, and rule learning.

**Architecture:** Three-layer architecture (Program → Business → Data). MiniMax AI for NLP/image understanding with local rule engine fallback. PostgreSQL for data persistence.

**Tech Stack:** Python 3.9+, PostgreSQL, SQLAlchemy, MiniMax API, pandas, openpyxl, watchdog

---

## Phase 1: Project Scaffold & Data Layer

### Task 1: Project Initialization

**Files:**
- Create: `ledger_system/pyproject.toml`
- Create: `ledger_system/main.py`
- Create: `ledger_system/config/settings.yaml`

- [ ] **Step 1: Create pyproject.toml**

```toml
[project]
name = "ledger-system"
version = "0.1.0"
description = "Construction site material/equipment inventory ledger system"
requires-python = ">=3.9"
dependencies = [
    "sqlalchemy>=2.0.0",
    "psycopg2-binary>=2.9.9",
    "pandas>=2.0.0",
    "openpyxl>=3.1.0",
    "pyyaml>=6.0",
    "anthropic>=0.20.0",
    "requests>=2.31.0",
    "watchdog>=3.0.0",
    "python-dateutil>=2.8.0",
]

[project.scripts]
ledger = "ledger_system.main:main"
```

- [ ] **Step 2: Create config/settings.yaml**

```yaml
database:
  host: "localhost"
  port: 5432
  name: "ledger_db"
  user: "postgres"
  password: "your_password"

minimax:
  api_key: "sk-cp-Tb9Viw7IZP432RPTrsO27Upe8FvAmoZjy9Lm2g4JCkgoeC_kWobSTrbV_gT4SyO2xi6veJzoh883fW_SAQHOQqdrd9VA5mbaaQ-XZpj5hRfLJuTmkNQ9OgA"
  api_host: "api.minimax.io"
  model: "MiniMax-Text-01"

monitor:
  watch_folder: "D:/工作/日常工作/台账/documents"
  auto_process: true

rules:
  local_rules_path: "ledger_system/rules/local_rules.json"
```

- [ ] **Step 3: Create main.py**

```python
"""Ledger System - Entry Point"""
from ledger_system.program.cli import main

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Create ledger_system/__init__.py**

```python
"""Ledger System Package"""
__version__ = "0.1.0"
```

- [ ] **Step 5: Commit**

```bash
cd "D:/工作/日常工作/台账"
git init
git add ledger_system/pyproject.toml ledger_system/main.py ledger_system/config/settings.yaml ledger_system/__init__.py
git commit -m "feat: initialize ledger system project structure"
```

---

### Task 2: Database Setup

**Files:**
- Create: `ledger_system/data/database.py`
- Create: `ledger_system/data/models/__init__.py`

- [ ] **Step 1: Create database.py**

```python
"""Database connection and session management"""
import os
from pathlib import Path
from typing import Generator

import yaml
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base

Base = declarative_base()

_DB_CONFIG = None


def load_config() -> dict:
    """Load database config from settings.yaml"""
    global _DB_CONFIG
    if _DB_CONFIG is None:
        config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        _DB_CONFIG = config["database"]
    return _DB_CONFIG


def get_engine():
    """Create SQLAlchemy engine"""
    cfg = load_config()
    url = f"postgresql://{cfg['user']}:{cfg['password']}@{cfg['host']}:{cfg['port']}/{cfg['name']}"
    return create_engine(url, echo=False)


def get_session_factory():
    """Create session factory"""
    engine = get_engine()
    return sessionmaker(bind=engine)


def get_session() -> Generator[Session, None, None]:
    """Get database session (context manager)"""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_database():
    """Create all tables"""
    engine = get_engine()
    Base.metadata.create_all(engine)
```

- [ ] **Step 2: Create data/models/__init__.py**

```python
"""Data models package"""
from ledger_system.data.models.base import Base
from ledger_system.data.models.ledger import Ledger
from ledger_system.data.models.inbound import Inbound
from ledger_system.data.models.outbound import Outbound
from ledger_system.data.models.rule_learning import RuleLearning
from ledger_system.data.models.document_log import DocumentLog

__all__ = ["Base", "Ledger", "Inbound", "Outbound", "RuleLearning", "DocumentLog"]
```

- [ ] **Step 3: Create data/models/base.py**

```python
"""Base model with common fields"""
import uuid
from datetime import datetime

from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from ledger_system.data.database import Base


class BaseModel(Base):
    """Base model with id and timestamps"""
    __abstract__ = True

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
```

- [ ] **Step 4: Commit**

```bash
git add ledger_system/data/database.py ledger_system/data/models/__init__.py ledger_system/data/models/base.py
git commit -m "feat: add database connection and base model"
```

---

### Task 3: Data Models

**Files:**
- Create: `ledger_system/data/models/ledger.py`
- Create: `ledger_system/data/models/inbound.py`
- Create: `ledger_system/data/models/outbound.py`
- Create: `ledger_system/data/models/rule_learning.py`
- Create: `ledger_system/data/models/document_log.py`

- [ ] **Step 1: Create ledger.py**

```python
"""Ledger (台账主表) model"""
from sqlalchemy import Column, String, Numeric
from ledger_system.data.models.base import BaseModel


class Ledger(BaseModel):
    """Main ledger table for materials and equipment"""
    __tablename__ = "ledger"

    category = Column(String(20), nullable=False)  # material / equipment
    name = Column(String(200), nullable=False)
    specification = Column(String(200), default="")
    unit = Column(String(20), default="")
    current_stock = Column(Numeric(precision=10, scale=2), default=0)
    min_stock = Column(Numeric(precision=10, scale=2), default=0)

    def __repr__(self):
        return f"<Ledger {self.name} ({self.category}): {self.current_stock} {self.unit}>"
```

- [ ] **Step 2: Create inbound.py**

```python
"""Inbound (入库记录) model"""
from sqlalchemy import Column, String, Numeric, Date, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ledger_system.data.models.base import BaseModel


class Inbound(BaseModel):
    """Inbound records for materials/equipment"""
    __tablename__ = "inbound"

    ledger_id = Column(UUID(as_uuid=True), ForeignKey("ledger.id"), nullable=False)
    quantity = Column(Numeric(precision=10, scale=2), nullable=False)
    supplier = Column(String(200), default="")
    inbound_date = Column(Date, nullable=False)
    document_source = Column(String(500), default="")
    operator = Column(String(100), default="")
    notes = Column(Text, default="")

    # relationship
    ledger = relationship("Ledger", backref="inbound_records")

    def __repr__(self):
        return f"<Inbound {self.ledger_id}: +{self.quantity}>"
```

- [ ] **Step 3: Create outbound.py**

```python
"""Outbound (使用记录) model"""
from sqlalchemy import Column, String, Numeric, Date, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ledger_system.data.models.base import BaseModel


class Outbound(BaseModel):
    """Outbound records for materials/equipment usage"""
    __tablename__ = "outbound"

    ledger_id = Column(UUID(as_uuid=True), ForeignKey("ledger.id"), nullable=False)
    quantity = Column(Numeric(precision=10, scale=2), nullable=False)
    usage = Column(String(200), default="")
    outbound_date = Column(Date, nullable=False)
    applicant = Column(String(100), default="")
    approver = Column(String(100), default="")
    notes = Column(Text, default="")

    # relationship
    ledger = relationship("Ledger", backref="outbound_records")

    def __repr__(self):
        return f"<Outbound {self.ledger_id}: -{self.quantity}>"
```

- [ ] **Step 4: Create rule_learning.py**

```python
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
```

- [ ] **Step 5: Create document_log.py**

```python
"""DocumentLog (文档处理记录) model"""
from sqlalchemy import Column, String, Text, JSON
from ledger_system.data.models.base import BaseModel


class DocumentLog(BaseModel):
    """Document processing log"""
    __tablename__ = "document_log"

    file_path = Column(String(500), nullable=False)
    process_type = Column(String(50), default="ocr")  # ocr / parse
    result = Column(JSON, default={})
    status = Column(String(20), default="pending")  # pending / success / failed
    error_message = Column(Text, default="")

    def __repr__(self):
        return f"<DocumentLog {self.file_path}: {self.status}>"
```

- [ ] **Step 6: Commit**

```bash
git add ledger_system/data/models/ledger.py ledger_system/data/models/inbound.py ledger_system/data/models/outbound.py ledger_system/data/models/rule_learning.py ledger_system/data/models/document_log.py
git commit -m "feat: add all data models (Ledger, Inbound, Outbound, RuleLearning, DocumentLog)"
```

---

### Task 4: Repository Layer

**Files:**
- Create: `ledger_system/data/repository/__init__.py`
- Create: `ledger_system/data/repository/ledger_repo.py`

- [ ] **Step 1: Create repository/__init__.py**

```python
"""Repository layer package"""
from ledger_system.data.repository.ledger_repo import LedgerRepository

__all__ = ["LedgerRepository"]
```

- [ ] **Step 2: Create ledger_repo.py**

```python
"""Ledger repository for data access"""
from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session
from ledger_system.data.models.ledger import Ledger
from ledger_system.data.models.inbound import Inbound
from ledger_system.data.models.outbound import Outbound


class LedgerRepository:
    """Repository for ledger operations"""

    def __init__(self, session: Session):
        self.session = session

    def create_ledger(self, category: str, name: str, specification: str = "",
                      unit: str = "", min_stock: Decimal = Decimal(0)) -> Ledger:
        """Create new ledger entry"""
        ledger = Ledger(
            category=category,
            name=name,
            specification=specification,
            unit=unit,
            current_stock=Decimal(0),
            min_stock=min_stock
        )
        self.session.add(ledger)
        self.session.flush()
        return ledger

    def get_ledger_by_id(self, ledger_id: UUID) -> Optional[Ledger]:
        """Get ledger by ID"""
        return self.session.query(Ledger).filter(Ledger.id == ledger_id).first()

    def get_ledger_by_name(self, name: str) -> Optional[Ledger]:
        """Get ledger by name (case-insensitive)"""
        return self.session.query(Ledger).filter(
            Ledger.name.ilike(f"%{name}%")
        ).first()

    def get_all_ledgers(self) -> List[Ledger]:
        """Get all ledgers"""
        return self.session.query(Ledger).order_by(Ledger.name).all()

    def get_ledgers_by_category(self, category: str) -> List[Ledger]:
        """Get ledgers by category"""
        return self.session.query(Ledger).filter(
            Ledger.category == category
        ).order_by(Ledger.name).all()

    def update_stock(self, ledger_id: UUID, quantity_change: Decimal) -> bool:
        """Update ledger stock (positive for add, negative for subtract)"""
        ledger = self.get_ledger_by_id(ledger_id)
        if not ledger:
            return False
        ledger.current_stock = ledger.current_stock + quantity_change
        self.session.flush()
        return True

    def add_inbound(self, ledger_id: UUID, quantity: Decimal, supplier: str = "",
                    inbound_date: date = None, document_source: str = "",
                    operator: str = "", notes: str = "") -> Inbound:
        """Add inbound record and update stock"""
        if inbound_date is None:
            inbound_date = date.today()

        inbound = Inbound(
            ledger_id=ledger_id,
            quantity=quantity,
            supplier=supplier,
            inbound_date=inbound_date,
            document_source=document_source,
            operator=operator,
            notes=notes
        )
        self.session.add(inbound)

        # Update stock
        self.update_stock(ledger_id, quantity)

        return inbound

    def add_outbound(self, ledger_id: UUID, quantity: Decimal, usage: str = "",
                     outbound_date: date = None, applicant: str = "",
                     approver: str = "", notes: str = "") -> Optional[Outbound]:
        """Add outbound record and update stock (only if sufficient stock)"""
        if outbound_date is None:
            outbound_date = date.today()

        ledger = self.get_ledger_by_id(ledger_id)
        if not ledger or ledger.current_stock < quantity:
            return None

        outbound = Outbound(
            ledger_id=ledger_id,
            quantity=quantity,
            usage=usage,
            outbound_date=outbound_date,
            applicant=applicant,
            approver=approver,
            notes=notes
        )
        self.session.add(outbound)

        # Update stock
        self.update_stock(ledger_id, -quantity)

        return outbound

    def get_inbound_history(self, ledger_id: UUID, days: int = 30) -> List[Inbound]:
        """Get inbound history for ledger"""
        from datetime import timedelta
        start_date = date.today() - timedelta(days=days)
        return self.session.query(Inbound).filter(
            Inbound.ledger_id == ledger_id,
            Inbound.inbound_date >= start_date
        ).order_by(Inbound.inbound_date.desc()).all()

    def get_outbound_history(self, ledger_id: UUID, days: int = 30) -> List[Outbound]:
        """Get outbound history for ledger"""
        from datetime import timedelta
        start_date = date.today() - timedelta(days=days)
        return self.session.query(Outbound).filter(
            Outbound.ledger_id == ledger_id,
            Outbound.outbound_date >= start_date
        ).order_by(Outbound.outbound_date.desc()).all()

    def get_low_stock_items(self) -> List[Ledger]:
        """Get items at or below min_stock"""
        return self.session.query(Ledger).filter(
            Ledger.current_stock <= Ledger.min_stock
        ).all()
```

- [ ] **Step 3: Commit**

```bash
git add ledger_system/data/repository/__init__.py ledger_system/data/repository/ledger_repo.py
git commit -m "feat: add LedgerRepository for data access"
```

---

## Phase 2: Business Layer

### Task 5: AI Service (MiniMax)

**Files:**
- Create: `ledger_system/business/__init__.py`
- Create: `ledger_system/business/nlp/__init__.py`
- Create: `ledger_system/business/nlp/ai_service.py`

- [ ] **Step 1: Create business/__init__.py**

```python
"""Business layer package"""
```

- [ ] **Step 2: Create business/nlp/__init__.py**

```python
"""NLP package"""
from ledger_system.business.nlp.ai_service import AIService

__all__ = ["AIService"]
```

- [ ] **Step 3: Create ai_service.py**

```python
"""MiniMax AI service for entity extraction and document understanding"""
import json
from typing import Dict, Any, Optional
from pathlib import Path

import yaml
import requests


class AIService:
    """Service for calling MiniMax AI APIs"""

    def __init__(self):
        self.config = self._load_config()
        self.api_key = self.config["minimax"]["api_key"]
        self.api_host = self.config["minimax"]["api_host"]
        self.model = self.config["minimax"].get("model", "MiniMax-Text-01")

    def _load_config(self) -> dict:
        """Load config from settings.yaml"""
        config_path = Path(__file__).parent.parent.parent / "config" / "settings.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract entities from natural language text"""
        prompt = f"""你是一个建筑工地材料入库记录解析助手。请从以下文本中提取关键信息:

文本: {text}

请以JSON格式返回，字段包括:
- material_name: 材料名称
- quantity: 数量（数字）
- unit: 单位（如：吨、个、米等）
- supplier: 供应商/来源
- date: 日期（格式：YYYY-MM-DD），如果文本中没有则用今天
- notes: 备注信息

只返回JSON，不要有其他内容。"""

        response = self._call_text_api(prompt)
        return self._parse_json_response(response)

    def understand_image(self, image_path: str) -> str:
        """Understand image content using MiniMax vision API"""
        prompt = """你是一个建筑工地单据识别助手。请描述这张图片中的所有文字内容和关键信息，包括：
- 材料名称和规格
- 数量和单位
- 供应商信息
- 日期
- 其他相关信息

请详细描述所有可见的文字内容。"""

        return self._call_vision_api(image_path, prompt)

    def _call_text_api(self, prompt: str) -> str:
        """Call MiniMax text API"""
        url = f"https://{self.api_host}/v1/text/chatcompletion_v2"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        result = response.json()
        return result["choices"][0]["messages"][0]["text"]

    def _call_vision_api(self, image_path: str, prompt: str) -> str:
        """Call MiniMax vision API for image understanding"""
        url = f"https://{self.api_host}/v1/image understanding"

        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        with open(image_path, "rb") as f:
            files = {"file": f}
            data = {"prompt": prompt}
            response = requests.post(url, headers=headers, data=data, files=files, timeout=120)

        response.raise_for_status()
        result = response.json()
        return result.get("content", "")

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from AI response"""
        try:
            # Try to extract JSON from response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end != 0:
                return json.loads(response[start:end])
            return {}
        except json.JSONDecodeError:
            return {}

    def parse_document_content(self, content: str, file_type: str) -> Dict[str, Any]:
        """Parse structured information from document content"""
        prompt = f"""你是一个建筑工地单据解析助手。请从以下文档内容中提取关键信息:

文档类型: {file_type}
内容:
{content[:2000]}

请以JSON格式返回，字段包括:
- material_name: 材料名称
- quantity: 数量（数字）
- unit: 单位
- supplier: 供应商
- date: 日期（YYYY-MM-DD）
- specification: 规格
- notes: 备注

只返回JSON。"""

        response = self._call_text_api(prompt)
        return self._parse_json_response(response)
```

- [ ] **Step 4: Commit**

```bash
git add ledger_system/business/__init__.py ledger_system/business/nlp/__init__.py ledger_system/business/nlp/ai_service.py
git commit -m "feat: add MiniMax AI service for entity extraction"
```

---

### Task 6: Rule Engine (Local Fallback)

**Files:**
- Create: `ledger_system/business/nlp/rule_engine.py`

- [ ] **Step 1: Create rule_engine.py**

```python
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
```

- [ ] **Step 2: Create rules/local_rules.json**

```json
{
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
```

- [ ] **Step 3: Commit**

```bash
git add ledger_system/business/nlp/rule_engine.py ledger_system/rules/local_rules.json
git commit -m "feat: add local rule engine for entity extraction fallback"
```

---

### Task 7: Learning Engine

**Files:**
- Create: `ledger_system/business/learning/__init__.py`
- Create: `ledger_system/business/learning/feedback.py`
- Create: `ledger_system/business/learning/diff_logger.py`

- [ ] **Step 1: Create business/learning/__init__.py**

```python
"""Learning engine package"""
```

- [ ] **Step 2: Create feedback.py**

```python
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
```

- [ ] **Step 3: Create diff_logger.py**

```python
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
```

- [ ] **Step 4: Commit**

```bash
git add ledger_system/business/learning/__init__.py ledger_system/business/learning/feedback.py ledger_system/business/learning/diff_logger.py
git commit -m "feat: add learning engine (feedback + diff logging)"
```

---

### Task 8: Document Processing

**Files:**
- Create: `ledger_system/business/document/__init__.py`
- Create: `ledger_system/business/document/parser.py`
- Create: `ledger_system/business/document/watcher.py`

- [ ] **Step 1: Create business/document/__init__.py**

```python
"""Document processing package"""
```

- [ ] **Step 2: Create parser.py**

```python
"""Document parser for various file types"""
import json
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
from ledger_system.business.nlp.ai_service import AIService


class DocumentParser:
    """Parse documents to extract structured information"""

    def __init__(self):
        self.ai_service = AIService()

    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """Parse file based on extension"""
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix in [".jpg", ".jpeg", ".png", ".bmp", ".gif"]:
            return self._parse_image(path)
        elif suffix == ".pdf":
            return self._parse_pdf(path)
        elif suffix in [".xlsx", ".xls"]:
            return self._parse_excel(path)
        elif suffix in [".docx", ".doc"]:
            return self._parse_word(path)
        elif suffix == ".txt":
            return self._parse_text(path)
        else:
            return {"error": f"Unsupported file type: {suffix}"}

    def _parse_image(self, path: Path) -> Dict[str, Any]:
        """Parse image using AI vision"""
        try:
            content = self.ai_service.understand_image(str(path))
            result = self.ai_service.parse_document_content(content, "image")
            result["source"] = "image_ocr"
            result["raw_content"] = content
            return result
        except Exception as e:
            return {"error": str(e), "source": "image_ocr"}

    def _parse_pdf(self, path: Path) -> Dict[str, Any]:
        """Parse PDF file"""
        try:
            # For PDF, we'd normally use pdfplumber or PyPDF2
            # For now, treat as text extraction needed
            content = self._extract_pdf_text(path)
            result = self.ai_service.parse_document_content(content, "pdf")
            result["source"] = "pdf"
            result["raw_content"] = content[:2000]
            return result
        except Exception as e:
            return {"error": str(e), "source": "pdf"}

    def _parse_excel(self, path: Path) -> Dict[str, Any]:
        """Parse Excel file"""
        try:
            df = pd.read_excel(path)
            content = df.to_string(max_rows=50)

            # Use AI to parse structured data from Excel
            result = self.ai_service.parse_document_content(content, "excel")
            result["source"] = "excel"
            result["raw_content"] = content[:2000]
            result["rows"] = len(df)
            result["columns"] = list(df.columns)
            return result
        except Exception as e:
            return {"error": str(e), "source": "excel"}

    def _parse_word(self, path: Path) -> Dict[str, Any]:
        """Parse Word document"""
        try:
            # For Word, we'd normally use python-docx
            # Placeholder for now
            content = f"Word document: {path.name}"
            result = self.ai_service.parse_document_content(content, "word")
            result["source"] = "word"
            return result
        except Exception as e:
            return {"error": str(e), "source": "word"}

    def _parse_text(self, path: Path) -> Dict[str, Any]:
        """Parse text file"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            result = self.ai_service.parse_document_content(content, "text")
            result["source"] = "text"
            result["raw_content"] = content[:2000]
            return result
        except Exception as e:
            return {"error": str(e), "source": "text"}

    def _extract_pdf_text(self, path: Path) -> str:
        """Extract text from PDF"""
        # Placeholder - would use pdfplumber
        return f"PDF content from {path.name}"
```

- [ ] **Step 3: Create watcher.py**

```python
"""File system watcher for automatic document processing"""
import time
from pathlib import Path
from typing import Callable, Optional

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from ledger_system.business.document.parser import DocumentParser


class DocumentHandler(FileSystemEventHandler):
    """Handle file system events for document processing"""

    def __init__(self, callback: Callable[[str], None], supported_extensions: list):
        self.callback = callback
        self.supported_extensions = supported_extensions
        self.cooldown_seconds = 5
        self.last_processed = {}

    def on_created(self, event: FileCreatedEvent):
        """Handle file creation event"""
        if event.is_directory:
            return

        path = Path(event.src_path)
        if path.suffix.lower() not in self.supported_extensions:
            return

        # Cooldown to avoid processing same file multiple times
        current_time = time.time()
        last_time = self.last_processed.get(str(path), 0)
        if current_time - last_time < self.cooldown_seconds:
            return

        self.last_processed[str(path)] = current_time
        self.callback(str(path))


class FileWatcher:
    """Watch folder for new documents"""

    def __init__(self, watch_path: str, callback: Callable[[str], None]):
        self.watch_path = Path(watch_path)
        self.callback = callback
        self.supported_extensions = [
            ".jpg", ".jpeg", ".png", ".bmp",  # Images
            ".pdf",  # PDF
            ".xlsx", ".xls",  # Excel
            ".docx", ".doc",  # Word
            ".txt"  # Text
        ]
        self.observer: Optional[Observer] = None
        self.parser = DocumentParser()

    def start(self):
        """Start watching"""
        self.watch_path.mkdir(parents=True, exist_ok=True)

        event_handler = DocumentHandler(
            callback=self._handle_new_file,
            supported_extensions=self.supported_extensions
        )

        self.observer = Observer()
        self.observer.schedule(event_handler, str(self.watch_path), recursive=False)
        self.observer.start()

        return self

    def stop(self):
        """Stop watching"""
        if self.observer:
            self.observer.stop()
            self.observer.join()

    def _handle_new_file(self, file_path: str):
        """Handle new file detected"""
        try:
            result = self.parser.parse_file(file_path)
            self.callback({
                "file_path": file_path,
                "result": result,
                "status": "success" if "error" not in result else "failed"
            })
        except Exception as e:
            self.callback({
                "file_path": file_path,
                "result": {"error": str(e)},
                "status": "failed"
            })

    def process_existing(self):
        """Process existing files in watch folder"""
        for path in self.watch_path.iterdir():
            if path.is_file() and path.suffix.lower() in self.supported_extensions:
                self._handle_new_file(str(path))
```

- [ ] **Step 4: Commit**

```bash
git add ledger_system/business/document/__init__.py ledger_system/business/document/parser.py ledger_system/business/document/watcher.py
git commit -m "feat: add document parser and file watcher"
```

---

## Phase 3: Program Layer (CLI)

### Task 9: CLI Implementation

**Files:**
- Create: `ledger_system/program/__init__.py`
- Create: `ledger_system/program/cli.py`
- Create: `ledger_system/program/commands/__init__.py`
- Create: `ledger_system/program/commands/add.py`
- Create: `ledger_system/program/commands/query.py`
- Create: `ledger_system/program/commands/process.py`
- Create: `ledger_system/program/commands/export.py`

- [ ] **Step 1: Create program/__init__.py**

```python
"""Program layer package"""
```

- [ ] **Step 2: Create program/cli.py**

```python
"""CLI entry point"""
import sys
import argparse
from ledger_system.program.commands.add import AddCommand
from ledger_system.program.commands.query import QueryCommand
from ledger_system.program.commands.process import ProcessCommand
from ledger_system.program.commands.export import ExportCommand


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser"""
    parser = argparse.ArgumentParser(
        prog="ledger",
        description="工地材料设备进出库台账管理系统"
    )

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # Add command
    add_parser = subparsers.add_parser("add", help="自然语言录入")
    add_parser.add_argument("text", nargs="+", help="录入文本")
    add_parser.add_argument("--confirm", action="store_true", help="确认后录入")

    # Query command
    query_parser = subparsers.add_parser("query", help="查询台账")
    query_parser.add_argument("--material", help="材料名称")
    query_parser.add_argument("--all", action="store_true", help="查询所有")
    query_parser.add_argument("--low-stock", action="store_true", help="库存不足")
    query_parser.add_argument("--days", type=int, default=30, help="历史天数")

    # Process command
    process_parser = subparsers.add_parser("process", help="处理文档")
    process_parser.add_argument("--file", required=True, help="文件路径")
    process_parser.add_argument("--folder", help="文件夹路径")

    # Export command
    export_parser = subparsers.add_parser("export", help="导出报表")
    export_parser.add_argument("--type", choices=["inventory", "inbound", "outbound"],
                               required=True, help="报表类型")
    export_parser.add_argument("--format", choices=["xlsx", "csv"], default="xlsx",
                               help="导出格式")
    export_parser.add_argument("--output", required=True, help="输出路径")
    export_parser.add_argument("--start", help="开始日期 YYYY-MM-DD")
    export_parser.add_argument("--end", help="结束日期 YYYY-MM-DD")

    # Help command
    help_parser = subparsers.add_parser("help", help="显示帮助")

    return parser


def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "help":
        parser.print_help()
        return

    # Route to command handler
    if args.command == "add":
        cmd = AddCommand()
        cmd.execute(args)
    elif args.command == "query":
        cmd = QueryCommand()
        cmd.execute(args)
    elif args.command == "process":
        cmd = ProcessCommand()
        cmd.execute(args)
    elif args.command == "export":
        cmd = ExportCommand()
        cmd.execute(args)
    else:
        print(f"未知命令: {args.command}")
        parser.print_help()


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Create program/commands/__init__.py**

```python
"""Commands package"""
```

- [ ] **Step 4: Create add.py**

```python
"""Add command - natural language ledger entry"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ledger_system.data.database import get_session
from ledger_system.data.repository import LedgerRepository
from ledger_system.business.nlp.ai_service import AIService
from ledger_system.business.nlp.rule_engine import RuleEngine
from ledger_system.business.learning.feedback import FeedbackLearning
from ledger_system.business.learning.diff_logger import DiffLogger


class AddCommand:
    """Add ledger entry using natural language"""

    def __init__(self):
        self.ai_service = AIService()
        self.rule_engine = RuleEngine()

    def execute(self, args):
        """Execute add command"""
        text = " ".join(args.text)
        print(f"正在解析: {text}")

        # Try AI extraction first
        ai_result = {}
        try:
            ai_result = self.ai_service.extract_entities(text)
            print(f"AI解析结果: {ai_result}")
        except Exception as e:
            print(f"AI解析失败: {e}")

        # Rule engine fallback
        rule_result = self.rule_engine.extract_entities(text)
        print(f"规则解析结果: {rule_result}")

        # Use AI result if available, otherwise use rule
        if ai_result.get("material_name"):
            final_result = ai_result
        else:
            final_result = rule_result

        # Log difference
        with get_session() as session:
            diff_logger = DiffLogger(session)
            diff_logger.log_diff(text, ai_result, rule_result)

        # Check if we have enough info
        if not final_result.get("material_name"):
            print("错误: 未能识别材料名称")
            return

        quantity = final_result.get("quantity") or 0
        unit = final_result.get("unit", "")
        supplier = final_result.get("supplier", "")

        print(f"\n确认录入:")
        print(f"  材料: {final_result['material_name']}")
        print(f"  数量: {quantity} {unit}")
        print(f"  供应商: {supplier}")
        print(f"  日期: {final_result.get('date', '今天')}")

        if args.confirm:
            self._save_to_db(final_result)
        else:
            response = input("\n确认录入? (y/n): ").strip().lower()
            if response == "y":
                self._save_to_db(final_result)

    def _save_to_db(self, result: dict):
        """Save entry to database"""
        with get_session() as session:
            repo = LedgerRepository(session)

            # Find or create ledger
            ledger = repo.get_ledger_by_name(result["material_name"])
            if not ledger:
                print(f"创建新材料: {result['material_name']}")
                ledger = repo.create_ledger(
                    category="material",
                    name=result["material_name"],
                    unit=result.get("unit", "")
                )

            # Add inbound
            from datetime import date
            from decimal import Decimal

            inbound_date = result.get("date")
            if inbound_date and isinstance(inbound_date, str):
                from datetime import datetime
                inbound_date = datetime.fromisoformat(inbound_date).date()
            else:
                inbound_date = date.today()

            repo.add_inbound(
                ledger_id=ledger.id,
                quantity=Decimal(str(result.get("quantity", 0))),
                supplier=result.get("supplier", ""),
                inbound_date=inbound_date,
                operator="system",
                notes=f"来源: 自然语言录入"
            )

            print(f"入库成功! 当前库存: {ledger.current_stock}")
```

- [ ] **Step 5: Create query.py**

```python
"""Query command - ledger and history queries"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ledger_system.data.database import get_session
from ledger_system.data.repository import LedgerRepository


class QueryCommand:
    """Query ledger status and history"""

    def execute(self, args):
        """Execute query command"""
        with get_session() as session:
            repo = LedgerRepository(session)

            if args.low_stock:
                self._query_low_stock(repo)
            elif args.all:
                self._query_all(repo)
            elif args.material:
                self._query_material(repo, args)
            else:
                self._query_all(repo)

    def _query_all(self, repo: LedgerRepository):
        """Query all ledger items"""
        items = repo.get_all_ledgers()

        print(f"\n{'='*60}")
        print(f"{'台账总览':^30}")
        print(f"{'='*60}")
        print(f"{'名称':<20} {'规格':<15} {'库存':>10} {'单位':<6} {'状态':<8}")
        print(f"{'-'*60}")

        for item in items:
            status = "正常" if item.current_stock >= item.min_stock else "⚠️ 低库存"
            print(f"{item.name:<20} {item.specification:<15} {item.current_stock:>10} {item.unit:<6} {status}")

        print(f"{'='*60}")
        print(f"共 {len(items)} 条记录")

    def _query_low_stock(self, repo: LedgerRepository):
        """Query low stock items"""
        items = repo.get_low_stock_items()

        print(f"\n{'='*60}")
        print(f"{'库存不足警告':^30}")
        print(f"{'='*60}")

        if not items:
            print("所有材料库存充足")
            return

        for item in items:
            print(f"⚠️ {item.name}: {item.current_stock} {item.unit} (最小: {item.min_stock})")

    def _query_material(self, repo: LedgerRepository, args):
        """Query specific material"""
        ledger = repo.get_ledger_by_name(args.material)

        if not ledger:
            print(f"未找到材料: {args.material}")
            return

        print(f"\n{'='*60}")
        print(f"材料: {ledger.name}")
        print(f"规格: {ledger.specification}")
        print(f"当前库存: {ledger.current_stock} {ledger.unit}")
        print(f"最小库存: {ledger.min_stock} {ledger.unit}")
        print(f"{'='*60}")

        # Inbound history
        inbounds = repo.get_inbound_history(ledger.id, args.days)
        print(f"\n入库记录 (最近 {args.days} 天):")
        print(f"{'日期':<12} {'数量':>10} {'供应商':<20} {'操作人':<10}")
        print(f"{'-'*52}")
        for ib in inbounds:
            print(f"{str(ib.inbound_date):<12} {ib.quantity:>10} {ib.supplier:<20} {ib.operator:<10}")

        # Outbound history
        outbounds = repo.get_outbound_history(ledger.id, args.days)
        print(f"\n使用记录 (最近 {args.days} 天):")
        print(f"{'日期':<12} {'数量':>10} {'用途':<20} {'申请人':<10}")
        print(f"{'-'*52}")
        for ob in outbounds:
            print(f"{str(ob.outbound_date):<12} {ob.quantity:>10} {ob.usage:<20} {ob.applicant:<10}")
```

- [ ] **Step 6: Create process.py**

```python
"""Process command - document processing"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ledger_system.business.document.parser import DocumentParser
from ledger_system.business.document.watcher import FileWatcher
from ledger_system.data.database import get_session
from ledger_system.data.repository import LedgerRepository
from ledger_system.data.models.document_log import DocumentLog
from datetime import date
from decimal import Decimal


class ProcessCommand:
    """Process documents"""

    def __init__(self):
        self.parser = DocumentParser()

    def execute(self, args):
        """Execute process command"""
        if args.folder:
            self._start_watcher(args.folder)
        elif args.file:
            self._process_file(args.file)
        else:
            print("请指定文件或文件夹")

    def _process_file(self, file_path: str):
        """Process single file"""
        print(f"处理文件: {file_path}")

        try:
            result = self.parser.parse_file(file_path)

            if "error" in result:
                print(f"处理失败: {result['error']}")
            else:
                print(f"解析结果: {result}")
                self._save_to_ledger(result, file_path)

        except Exception as e:
            print(f"处理异常: {e}")

    def _save_to_ledger(self, result: dict, file_path: str):
        """Save parsing result to ledger"""
        material_name = result.get("material_name")
        if not material_name:
            print("未能从文档中识别材料")
            return

        with get_session() as session:
            repo = LedgerRepository(session)

            # Find or create ledger
            ledger = repo.get_ledger_by_name(material_name)
            if not ledger:
                ledger = repo.create_ledger(
                    category="material",
                    name=material_name,
                    unit=result.get("unit", ""),
                    specification=result.get("specification", "")
                )

            # Add inbound
            inbound_date = result.get("date")
            if inbound_date and isinstance(inbound_date, str):
                from datetime import datetime
                inbound_date = datetime.fromisoformat(inbound_date).date()
            else:
                inbound_date = date.today()

            quantity = result.get("quantity") or 0
            if isinstance(quantity, str):
                try:
                    quantity = float(quantity)
                except:
                    quantity = 0

            repo.add_inbound(
                ledger_id=ledger.id,
                quantity=Decimal(str(quantity)),
                supplier=result.get("supplier", ""),
                inbound_date=inbound_date,
                document_source=file_path,
                operator="document",
                notes=f"来源: 文档解析"
            )

            # Log
            log = DocumentLog(
                file_path=file_path,
                process_type="parse",
                result=result,
                status="success"
            )
            session.add(log)

            print(f"入库成功: {material_name} x {quantity}")
            print(f"当前库存: {ledger.current_stock}")

    def _start_watcher(self, folder: str):
        """Start file watcher"""
        print(f"启动文件夹监控: {folder}")
        print("按 Ctrl+C 停止")

        def on_new_file(data: dict):
            print(f"\n检测到新文件: {data['file_path']}")
            if data["status"] == "success":
                self._save_to_ledger(data["result"], data["file_path"])
            else:
                print(f"处理失败: {data.get('result', {}).get('error')}")

        watcher = FileWatcher(folder, on_new_file)
        try:
            watcher.start()
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            watcher.stop()
            print("\n监控已停止")
```

- [ ] **Step 7: Create export.py**

```python
"""Export command - export reports"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
from datetime import datetime
from ledger_system.data.database import get_session
from ledger_system.data.repository import LedgerRepository


class ExportCommand:
    """Export ledger reports"""

    def execute(self, args):
        """Execute export command"""
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if args.type == "inventory":
            self._export_inventory(output_path)
        elif args.type == "inbound":
            self._export_inbound(output_path, args)
        elif args.type == "outbound":
            self._export_outbound(output_path, args)

    def _export_inventory(self, output_path: Path):
        """Export inventory report"""
        with get_session() as session:
            repo = LedgerRepository(session)
            items = repo.get_all_ledgers()

            data = []
            for item in items:
                data.append({
                    "名称": item.name,
                    "规格": item.specification,
                    "类别": item.category,
                    "单位": item.unit,
                    "当前库存": float(item.current_stock),
                    "最小库存": float(item.min_stock),
                    "状态": "正常" if item.current_stock >= item.min_stock else "库存不足"
                })

            df = pd.DataFrame(data)
            df.to_excel(output_path, index=False, engine="openpyxl")
            print(f"库存报表已导出: {output_path}")

    def _export_inbound(self, output_path: Path, args):
        """Export inbound report"""
        with get_session() as session:
            repo = LedgerRepository(session)

            # Filter by date if specified
            start_date = None
            end_date = None
            if args.start:
                start_date = datetime.fromisoformat(args.start).date()
            if args.end:
                end_date = datetime.fromisoformat(args.end).date()

            ledgers = repo.get_all_ledgers()
            data = []

            for ledger in ledgers:
                inbounds = repo.get_inbound_history(ledger.id, days=99999)
                for ib in inbounds:
                    if start_date and ib.inbound_date < start_date:
                        continue
                    if end_date and ib.inbound_date > end_date:
                        continue

                    data.append({
                        "日期": ib.inbound_date,
                        "材料": ledger.name,
                        "规格": ledger.specification,
                        "数量": float(ib.quantity),
                        "单位": ledger.unit,
                        "供应商": ib.supplier,
                        "操作人": ib.operator,
                        "备注": ib.notes
                    })

            df = pd.DataFrame(data)
            df = df.sort_values("日期", ascending=False)
            df.to_excel(output_path, index=False, engine="openpyxl")
            print(f"入库记录已导出: {output_path}")

    def _export_outbound(self, output_path: Path, args):
        """Export outbound report"""
        with get_session() as session:
            repo = LedgerRepository(session)

            start_date = None
            end_date = None
            if args.start:
                start_date = datetime.fromisoformat(args.start).date()
            if args.end:
                end_date = datetime.fromisoformat(args.end).date()

            ledgers = repo.get_all_ledgers()
            data = []

            for ledger in ledgers:
                outbounds = repo.get_outbound_history(ledger.id, days=99999)
                for ob in outbounds:
                    if start_date and ob.outbound_date < start_date:
                        continue
                    if end_date and ob.outbound_date > end_date:
                        continue

                    data.append({
                        "日期": ob.outbound_date,
                        "材料": ledger.name,
                        "规格": ledger.specification,
                        "数量": float(ob.quantity),
                        "单位": ledger.unit,
                        "用途": ob.usage,
                        "申请人": ob.applicant,
                        "审批人": ob.approver,
                        "备注": ob.notes
                    })

            df = pd.DataFrame(data)
            df = df.sort_values("日期", ascending=False)
            df.to_excel(output_path, index=False, engine="openpyxl")
            print(f"使用记录已导出: {output_path}")
```

- [ ] **Step 8: Commit**

```bash
git add ledger_system/program/__init__.py ledger_system/program/cli.py ledger_system/program/commands/__init__.py ledger_system/program/commands/add.py ledger_system/program/commands/query.py ledger_system/program/commands/process.py ledger_system/program/commands/export.py
git commit -m "feat: add CLI program layer with all commands"
```

---

## Summary

### Task List

| Phase | Task | Description |
|-------|------|-------------|
| 1 | 1 | Project initialization + config |
| 1 | 2 | Database setup |
| 1 | 3 | Data models (5 tables) |
| 1 | 4 | Repository layer |
| 2 | 5 | AI Service (MiniMax) |
| 2 | 6 | Rule Engine |
| 2 | 7 | Learning Engine |
| 2 | 8 | Document Processing |
| 3 | 9 | CLI Implementation |

### Next Steps

1. Initialize git in project folder
2. Create virtual environment and install dependencies
3. Create PostgreSQL database
4. Run each task sequentially
5. Test with real data

---

**Plan complete and saved to `docs/superpowers/plans/2026-04-30-ledger-implementation.md`**

Two execution options:

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

Which approach?