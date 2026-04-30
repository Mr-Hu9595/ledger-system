# 台账管理系统 - 数据库重构实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 重构数据库结构，实现物料/设备属性分离、入库出库序号自动化、Excel动态看板

**Architecture:** 三层架构（Data → Business → Program），SQLAlchemy ORM，PostgreSQL

**Tech Stack:** Python 3.9+, SQLAlchemy 2.0, PostgreSQL, pandas, openpyxl

---

## 文件结构

```
ledger_system/
├── data/
│   ├── models/
│   │   ├── base.py           # 修改: 添加 updated_at
│   │   ├── ledger.py         # 修改: 添加 purchase_date, 移除混合属性
│   │   ├── inbound.py        # 修改: 添加 inbound_sequence, cumulative_in
│   │   ├── outbound.py       # 修改: 添加 outbound_sequence, cumulative_out
│   │   ├── material_property.py    # 新建: 物料属性表
│   │   ├── equipment_property.py   # 新建: 设备属性表
│   │   └── __init__.py       # 修改: 导出新模型
│   └── repository/
│       └── ledger_repo.py    # 修改: 序号/累计量计算
├── business/
│   └── report/
│       └── report_generator.py  # 新建: Excel动态报表生成
└── program/
    └── commands/
        └── export.py         # 修改: 支持多选导出
```

---

## Phase 1: Data Layer

### Task 1: 更新 BaseModel - 添加 updated_at

**Files:**
- Modify: `ledger_system/data/models/base.py`

- [ ] **Step 1: 读取现有 base.py**

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

- [ ] **Step 2: 修改 base.py - 添加 updated_at**

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
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
```

- [ ] **Step 3: 提交**

```bash
git add ledger_system/data/models/base.py
git commit -m "feat: add updated_at to BaseModel"
```

---

### Task 2: 更新 Ledger 模型 - 添加 purchase_date，移除混合属性

**Files:**
- Modify: `ledger_system/data/models/ledger.py`

- [ ] **Step 1: 读取现有 ledger.py**

```python
"""Ledger (台账主表) model"""
from sqlalchemy import Column, String, Numeric, ForeignKey, Text
from sqlalchemy.orm import relationship
from ledger_system.data.models.base import BaseModel


class Ledger(BaseModel):
    """Main ledger table for materials and equipment"""
    __tablename__ = "ledger"

    category = Column(String(20), nullable=False)  # material / equipment
    name = Column(String(200), nullable=False)
    specification = Column(String(500), default="")  # 规格型号
    unit = Column(String(20), default="")
    current_stock = Column(Numeric(precision=10, scale=2), default=0)
    min_stock = Column(Numeric(precision=10, scale=2), default=0)
    material_code = Column(String(18), ForeignKey("material_code.code"), nullable=True)

    # 扩展字段
    medium = Column(String(100), default="")           # 介质
    design_pressure = Column(String(100), default="")  # 设计压力
    material_type = Column(String(100), default="")   # 材质
    design_temperature = Column(String(100), default="") # 设计温度
    manufacturer = Column(String(200), default="")     # 厂家
    notes = Column(Text, default="")                  # 备注
    drive_type = Column(String(50), default="")       # 驱动形式
    nominal_diameter = Column(String(50), default="")  # 公称直径
    valve_position = Column(String(100), default="")  # 阀门位置
    purchase_date = Column(String(50), default="")    # 采购日期

    # relationship
    code_info = relationship("MaterialCode", foreign_keys=[material_code], lazy="joined")

    def __repr__(self):
        return f"<Ledger {self.name} ({self.category}): {self.current_stock} {self.unit}>"
```

- [ ] **Step 2: 修改 ledger.py - 移除混合属性，添加 purchase_date 正确类型**

```python
"""Ledger (台账主表) model"""
from sqlalchemy import Column, String, Numeric, ForeignKey, Date, Text
from sqlalchemy.orm import relationship
from ledger_system.data.models.base import BaseModel


class Ledger(BaseModel):
    """Main ledger table for materials and equipment"""
    __tablename__ = "ledger"

    category = Column(String(20), nullable=False)  # material / equipment
    name = Column(String(200), nullable=False)
    specification = Column(String(500), default="")  # 规格型号
    unit = Column(String(20), default="")
    current_stock = Column(Numeric(precision=10, scale=2), default=0)
    min_stock = Column(Numeric(precision=10, scale=2), default=0)
    purchase_date = Column(Date, nullable=True)  # 采购日期
    material_code = Column(String(18), ForeignKey("material_code.code"), nullable=True)
    notes = Column(Text, default="")  # 备注

    # relationships
    code_info = relationship("MaterialCode", foreign_keys=[material_code], lazy="joined")

    def __repr__(self):
        return f"<Ledger {self.name} ({self.category}): {self.current_stock} {self.unit}>"
```

- [ ] **Step 3: 提交**

```bash
git add ledger_system/data/models/ledger.py
git commit -m "feat: refactor Ledger - add purchase_date, remove mixed properties to separate tables"
```

---

### Task 3: 更新 Inbound 模型 - 添加 inbound_sequence 和 cumulative_in

**Files:**
- Modify: `ledger_system/data/models/inbound.py`

- [ ] **Step 1: 读取现有 inbound.py**

```python
"""Inbound (入库记录) model"""
from sqlalchemy import Column, String, Numeric, Date, Time, Text, ForeignKey
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
    inbound_time = Column(Time, nullable=False)
    inbound_operator = Column(String(100), default="")
    document_source = Column(String(500), default="")
    original_document_path = Column(String(500), default="")
    notes = Column(Text, default="")

    # relationship
    ledger = relationship("Ledger", backref="inbound_records")

    def __repr__(self):
        return f"<Inbound {self.ledger_id}: +{self.quantity}>"
```

- [ ] **Step 2: 修改 inbound.py - 添加序号和累计量字段**

```python
"""Inbound (入库记录) model"""
from sqlalchemy import Column, String, Numeric, Date, Time, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ledger_system.data.models.base import BaseModel


class Inbound(BaseModel):
    """Inbound records for materials/equipment"""
    __tablename__ = "inbound"

    ledger_id = Column(UUID(as_uuid=True), ForeignKey("ledger.id"), nullable=False)
    quantity = Column(Numeric(precision=10, scale=2), nullable=False)
    inbound_sequence = Column(Integer, nullable=False, default=0)  # 第N次入库
    cumulative_in = Column(Numeric(precision=10, scale=2), nullable=False, default=0)  # 累计入库量
    supplier = Column(String(200), default="")
    inbound_date = Column(Date, nullable=False)
    inbound_time = Column(Time, nullable=False)
    inbound_operator = Column(String(100), default="")
    document_source = Column(String(500), default="")
    original_document_path = Column(String(500), default="")
    notes = Column(Text, default="")

    # relationship
    ledger = relationship("Ledger", backref="inbound_records")

    def __repr__(self):
        return f"<Inbound {self.ledger_id}: +{self.quantity} (seq:{self.inbound_sequence})>"
```

- [ ] **Step 3: 提交**

```bash
git add ledger_system/data/models/inbound.py
git commit -m "feat: add inbound_sequence and cumulative_in to Inbound model"
```

---

### Task 4: 更新 Outbound 模型 - 添加 outbound_sequence 和 cumulative_out

**Files:**
- Modify: `ledger_system/data/models/outbound.py`

- [ ] **Step 1: 读取现有 outbound.py**

```python
"""Outbound (出库记录) model"""
from sqlalchemy import Column, String, Numeric, Date, Time, Text, ForeignKey
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
    outbound_time = Column(Time, nullable=False)
    receiver = Column(String(100), default="")
    outbound_operator = Column(String(100), default="")
    original_document_path = Column(String(500), default="")
    notes = Column(Text, default="")

    # relationship
    ledger = relationship("Ledger", backref="outbound_records")

    def __repr__(self):
        return f"<Outbound {self.ledger_id}: -{self.quantity}>"
```

- [ ] **Step 2: 修改 outbound.py - 添加序号和累计量字段**

```python
"""Outbound (出库记录) model"""
from sqlalchemy import Column, String, Numeric, Date, Time, Text, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ledger_system.data.models.base import BaseModel


class Outbound(BaseModel):
    """Outbound records for materials/equipment usage"""
    __tablename__ = "outbound"

    ledger_id = Column(UUID(as_uuid=True), ForeignKey("ledger.id"), nullable=False)
    quantity = Column(Numeric(precision=10, scale=2), nullable=False)
    outbound_sequence = Column(Integer, nullable=False, default=0)  # 第N次出库
    cumulative_out = Column(Numeric(precision=10, scale=2), nullable=False, default=0)  # 累计出库量
    usage = Column(String(200), default="")
    outbound_date = Column(Date, nullable=False)
    outbound_time = Column(Time, nullable=False)
    receiver = Column(String(100), default="")
    outbound_operator = Column(String(100), default="")
    original_document_path = Column(String(500), default="")
    notes = Column(Text, default="")

    # relationship
    ledger = relationship("Ledger", backref="outbound_records")

    def __repr__(self):
        return f"<Outbound {self.ledger_id}: -{self.quantity} (seq:{self.outbound_sequence})>"
```

- [ ] **Step 3: 提交**

```bash
git add ledger_system/data/models/outbound.py
git commit -m "feat: add outbound_sequence and cumulative_out to Outbound model"
```

---

### Task 5: 创建 MaterialProperty 模型 - 物料属性表

**Files:**
- Create: `ledger_system/data/models/material_property.py`

- [ ] **Step 1: 创建 material_property.py**

```python
"""MaterialProperty (物料属性表) model"""
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ledger_system.data.models.base import BaseModel


class MaterialProperty(BaseModel):
    """Material property table for dynamic key-value attributes (materials only)"""
    __tablename__ = "material_property"

    ledger_id = Column(UUID(as_uuid=True), ForeignKey("ledger.id"), nullable=False)
    property_key = Column(String(50), nullable=False)  # e.g., execution_standard, material_type
    property_value = Column(String(500), default="")
    property_type = Column(String(50), default="")  # e.g., standard, material, medium

    # relationship
    ledger = relationship("Ledger", backref="material_properties")

    def __repr__(self):
        return f"<MaterialProperty {self.property_key}: {self.property_value}>"


# Predefined property keys for materials
MATERIAL_PROPERTY_KEYS = {
    "execution_standard": ("执行标准", "standard"),
    "material_type": ("材质", "material"),
    "medium": ("介质", "material"),
    "surface_treatment": ("表面处理", "material"),
    "origin": ("产地/厂家", "material"),
    "brand": ("品牌", "material"),
}
```

- [ ] **Step 2: 提交**

```bash
git add ledger_system/data/models/material_property.py
git commit -m "feat: add MaterialProperty model for material-specific attributes"
```

---

### Task 6: 创建 EquipmentProperty 模型 - 设备属性表

**Files:**
- Create: `ledger_system/data/models/equipment_property.py`

- [ ] **Step 1: 创建 equipment_property.py**

```python
"""EquipmentProperty (设备属性表) model"""
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ledger_system.data.models.base import BaseModel


class EquipmentProperty(BaseModel):
    """Equipment property table for dynamic key-value attributes (equipment only)"""
    __tablename__ = "equipment_property"

    ledger_id = Column(UUID(as_uuid=True), ForeignKey("ledger.id"), nullable=False)
    property_key = Column(String(50), nullable=False)  # e.g., drive_type, nominal_diameter
    property_value = Column(String(500), default="")
    property_type = Column(String(50), default="")  # e.g., mechanical, pressure, temperature

    # relationship
    ledger = relationship("Ledger", backref="equipment_properties")

    def __repr__(self):
        return f"<EquipmentProperty {self.property_key}: {self.property_value}>"


# Predefined property keys for equipment
EQUIPMENT_PROPERTY_KEYS = {
    "drive_type": ("驱动形式", "mechanical"),
    "nominal_diameter": ("公称直径", "mechanical"),
    "valve_position": ("阀门位置", "mechanical"),
    "design_pressure": ("设计压力", "pressure"),
    "design_temperature": ("设计温度", "temperature"),
    "manufacturer": ("厂家", "material"),
}
```

- [ ] **Step 2: 提交**

```bash
git add ledger_system/data/models/equipment_property.py
git commit -m "feat: add EquipmentProperty model for equipment-specific attributes"
```

---

### Task 7: 更新 models/__init__.py - 导出新模型

**Files:**
- Modify: `ledger_system/data/models/__init__.py`

- [ ] **Step 1: 读取并修改 __init__.py**

```python
"""Data models package"""
from ledger_system.data.models.base import Base
from ledger_system.data.models.ledger import Ledger
from ledger_system.data.models.inbound import Inbound
from ledger_system.data.models.outbound import Outbound
from ledger_system.data.models.material_property import MaterialProperty, MATERIAL_PROPERTY_KEYS
from ledger_system.data.models.equipment_property import EquipmentProperty, EQUIPMENT_PROPERTY_KEYS
from ledger_system.data.models.rule_learning import RuleLearning
from ledger_system.data.models.document_log import DocumentLog
from ledger_system.data.models.material_code import MaterialCode
from ledger_system.data.models.category import Category

__all__ = [
    "Base",
    "Ledger",
    "Inbound",
    "Outbound",
    "MaterialProperty",
    "MATERIAL_PROPERTY_KEYS",
    "EquipmentProperty",
    "EQUIPMENT_PROPERTY_KEYS",
    "RuleLearning",
    "DocumentLog",
    "MaterialCode",
    "Category",
]
```

- [ ] **Step 2: 提交**

```bash
git add ledger_system/data/models/__init__.py
git commit -m "feat: export new MaterialProperty and EquipmentProperty models"
```

---

### Task 8: 更新 LedgerRepository - 序号和累计量计算

**Files:**
- Modify: `ledger_system/data/repository/ledger_repo.py`

- [ ] **Step 1: 读取现有 ledger_repo.py**

```python
"""Ledger repository for data access"""
from datetime import date, time
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

    def create_ledger(
        self,
        category: str,
        name: str,
        specification: str = "",
        unit: str = "",
        min_stock: Decimal = Decimal(0),
        material_code: str = None
    ) -> Ledger:
        """Create new ledger entry"""
        ledger = Ledger(
            category=category,
            name=name,
            specification=specification,
            unit=unit,
            current_stock=Decimal(0),
            min_stock=min_stock,
            material_code=material_code
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
                    inbound_date: date = None, inbound_time: time = None,
                    inbound_operator: str = "", document_source: str = "",
                    original_document_path: str = "",
                    notes: str = "") -> Inbound:
        """Add inbound record and update stock"""
        if inbound_date is None:
            inbound_date = date.today()
        if inbound_time is None:
            inbound_time = time(8, 0)

        inbound = Inbound(
            ledger_id=ledger_id,
            quantity=quantity,
            supplier=supplier,
            inbound_date=inbound_date,
            inbound_time=inbound_time,
            inbound_operator=inbound_operator,
            document_source=document_source,
            original_document_path=original_document_path,
            notes=notes
        )
        self.session.add(inbound)

        # Update stock
        self.update_stock(ledger_id, quantity)

        return inbound

    def add_outbound(self, ledger_id: UUID, quantity: Decimal, usage: str = "",
                     outbound_date: date = None, outbound_time: time = None,
                     receiver: str = "", outbound_operator: str = "",
                     original_document_path: str = "",
                     notes: str = "") -> Optional[Outbound]:
        """Add outbound record and update stock (only if sufficient stock)"""
        if outbound_date is None:
            outbound_date = date.today()
        if outbound_time is None:
            outbound_time = time(8, 0)

        ledger = self.get_ledger_by_id(ledger_id)
        if not ledger or ledger.current_stock < quantity:
            return None

        outbound = Outbound(
            ledger_id=ledger_id,
            quantity=quantity,
            usage=usage,
            outbound_date=outbound_date,
            outbound_time=outbound_time,
            receiver=receiver,
            outbound_operator=outbound_operator,
            original_document_path=original_document_path,
            notes=notes
        )
        self.session.add(outbound)

        # Update stock
        self.update_stock(ledger_id, -quantity)

        return outbound

    def get_all_inbounds(self, days: int = 99999) -> List[Inbound]:
        """Get all inbound records"""
        from datetime import timedelta
        start_date = date.today() - timedelta(days=days)
        return self.session.query(Inbound).filter(
            Inbound.inbound_date >= start_date
        ).order_by(Inbound.inbound_date.desc(), Inbound.inbound_time.desc()).all()

    def get_all_outbounds(self, days: int = 99999) -> List[Outbound]:
        """Get all outbound records"""
        from datetime import timedelta
        start_date = date.today() - timedelta(days=days)
        return self.session.query(Outbound).filter(
            Outbound.outbound_date >= start_date
        ).order_by(Outbound.outbound_date.desc(), Outbound.outbound_time.desc()).all()

    def get_inbound_history(self, ledger_id: UUID, days: int = 30) -> List[Inbound]:
        """Get inbound history for ledger"""
        from datetime import timedelta
        start_date = date.today() - timedelta(days=days)
        return self.session.query(Inbound).filter(
            Inbound.ledger_id == ledger_id,
            Inbound.inbound_date >= start_date
        ).order_by(Inbound.inbound_date.desc(), Inbound.inbound_time.desc()).all()

    def get_outbound_history(self, ledger_id: UUID, days: int = 30) -> List[Outbound]:
        """Get outbound history for ledger"""
        from datetime import timedelta
        start_date = date.today() - timedelta(days=days)
        return self.session.query(Outbound).filter(
            Outbound.ledger_id == ledger_id,
            Outbound.outbound_date >= start_date
        ).order_by(Outbound.outbound_date.desc(), Outbound.outbound_time.desc()).all()

    def get_low_stock_items(self) -> List[Ledger]:
        """Get items at or below min_stock"""
        return self.session.query(Ledger).filter(
            Ledger.current_stock <= Ledger.min_stock
        ).all()
```

- [ ] **Step 2: 修改 ledger_repo.py - 添加序号和累计量计算**

```python
"""Ledger repository for data access"""
from datetime import date, time
from decimal import Decimal
from typing import List, Optional, Dict
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session
from ledger_system.data.models.ledger import Ledger
from ledger_system.data.models.inbound import Inbound
from ledger_system.data.models.outbound import Outbound
from ledger_system.data.models.material_property import MaterialProperty
from ledger_system.data.models.equipment_property import EquipmentProperty


class LedgerRepository:
    """Repository for ledger operations"""

    def __init__(self, session: Session):
        self.session = session

    def create_ledger(
        self,
        category: str,
        name: str,
        specification: str = "",
        unit: str = "",
        min_stock: Decimal = Decimal(0),
        material_code: str = None,
        purchase_date: date = None
    ) -> Ledger:
        """Create new ledger entry"""
        ledger = Ledger(
            category=category,
            name=name,
            specification=specification,
            unit=unit,
            current_stock=Decimal(0),
            min_stock=min_stock,
            material_code=material_code,
            purchase_date=purchase_date
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

    def _get_next_inbound_sequence(self, ledger_id: UUID) -> int:
        """Get next inbound sequence number for ledger"""
        max_seq = self.session.query(func.max(Inbound.inbound_sequence)).filter(
            Inbound.ledger_id == ledger_id
        ).scalar()
        return (max_seq or 0) + 1

    def _get_cumulative_in(self, ledger_id: UUID) -> Decimal:
        """Get current cumulative inbound for ledger"""
        total = self.session.query(func.sum(Inbound.quantity)).filter(
            Inbound.ledger_id == ledger_id
        ).scalar()
        return total or Decimal(0)

    def _get_next_outbound_sequence(self, ledger_id: UUID) -> int:
        """Get next outbound sequence number for ledger"""
        max_seq = self.session.query(func.max(Outbound.outbound_sequence)).filter(
            Outbound.ledger_id == ledger_id
        ).scalar()
        return (max_seq or 0) + 1

    def _get_cumulative_out(self, ledger_id: UUID) -> Decimal:
        """Get current cumulative outbound for ledger"""
        total = self.session.query(func.sum(Outbound.quantity)).filter(
            Outbound.ledger_id == ledger_id
        ).scalar()
        return total or Decimal(0)

    def add_inbound(self, ledger_id: UUID, quantity: Decimal, supplier: str = "",
                    inbound_date: date = None, inbound_time: time = None,
                    inbound_operator: str = "", document_source: str = "",
                    original_document_path: str = "",
                    notes: str = "") -> Inbound:
        """Add inbound record and update stock with sequence and cumulative"""
        if inbound_date is None:
            inbound_date = date.today()
        if inbound_time is None:
            inbound_time = time(8, 0)

        # Calculate sequence and cumulative BEFORE adding
        inbound_sequence = self._get_next_inbound_sequence(ledger_id)

        inbound = Inbound(
            ledger_id=ledger_id,
            quantity=quantity,
            inbound_sequence=inbound_sequence,
            cumulative_in=self._get_cumulative_in(ledger_id) + quantity,
            supplier=supplier,
            inbound_date=inbound_date,
            inbound_time=inbound_time,
            inbound_operator=inbound_operator,
            document_source=document_source,
            original_document_path=original_document_path,
            notes=notes
        )
        self.session.add(inbound)

        # Update stock
        self.update_stock(ledger_id, quantity)

        return inbound

    def add_outbound(self, ledger_id: UUID, quantity: Decimal, usage: str = "",
                     outbound_date: date = None, outbound_time: time = None,
                     receiver: str = "", outbound_operator: str = "",
                     original_document_path: str = "",
                     notes: str = "") -> Optional[Outbound]:
        """Add outbound record and update stock with sequence and cumulative"""
        if outbound_date is None:
            outbound_date = date.today()
        if outbound_time is None:
            outbound_time = time(8, 0)

        ledger = self.get_ledger_by_id(ledger_id)
        if not ledger or ledger.current_stock < quantity:
            return None

        # Calculate sequence and cumulative BEFORE adding
        outbound_sequence = self._get_next_outbound_sequence(ledger_id)

        outbound = Outbound(
            ledger_id=ledger_id,
            quantity=quantity,
            outbound_sequence=outbound_sequence,
            cumulative_out=self._get_cumulative_out(ledger_id) + quantity,
            usage=usage,
            outbound_date=outbound_date,
            outbound_time=outbound_time,
            receiver=receiver,
            outbound_operator=outbound_operator,
            original_document_path=original_document_path,
            notes=notes
        )
        self.session.add(outbound)

        # Update stock
        self.update_stock(ledger_id, -quantity)

        return outbound

    def get_all_inbounds(self, days: int = 99999) -> List[Inbound]:
        """Get all inbound records"""
        from datetime import timedelta
        start_date = date.today() - timedelta(days=days)
        return self.session.query(Inbound).filter(
            Inbound.inbound_date >= start_date
        ).order_by(Inbound.inbound_date.desc(), Inbound.inbound_time.desc()).all()

    def get_all_outbounds(self, days: int = 99999) -> List[Outbound]:
        """Get all outbound records"""
        from datetime import timedelta
        start_date = date.today() - timedelta(days=days)
        return self.session.query(Outbound).filter(
            Outbound.outbound_date >= start_date
        ).order_by(Outbound.outbound_date.desc(), Outbound.outbound_time.desc()).all()

    def get_inbound_history(self, ledger_id: UUID, days: int = 30) -> List[Inbound]:
        """Get inbound history for ledger"""
        from datetime import timedelta
        start_date = date.today() - timedelta(days=days)
        return self.session.query(Inbound).filter(
            Inbound.ledger_id == ledger_id,
            Inbound.inbound_date >= start_date
        ).order_by(Inbound.inbound_date.desc(), Inbound.inbound_time.desc()).all()

    def get_outbound_history(self, ledger_id: UUID, days: int = 30) -> List[Outbound]:
        """Get outbound history for ledger"""
        from datetime import timedelta
        start_date = date.today() - timedelta(days=days)
        return self.session.query(Outbound).filter(
            Outbound.ledger_id == ledger_id,
            Outbound.outbound_date >= start_date
        ).order_by(Outbound.outbound_date.desc(), Outbound.outbound_time.desc()).all()

    def get_low_stock_items(self) -> List[Ledger]:
        """Get items at or below min_stock"""
        return self.session.query(Ledger).filter(
            Ledger.current_stock <= Ledger.min_stock
        ).all()

    # ========== Property Management ==========

    def add_material_property(self, ledger_id: UUID, property_key: str,
                               property_value: str, property_type: str = "") -> MaterialProperty:
        """Add a property to a material ledger entry"""
        prop = MaterialProperty(
            ledger_id=ledger_id,
            property_key=property_key,
            property_value=property_value,
            property_type=property_type
        )
        self.session.add(prop)
        self.session.flush()
        return prop

    def add_equipment_property(self, ledger_id: UUID, property_key: str,
                               property_value: str, property_type: str = "") -> EquipmentProperty:
        """Add a property to an equipment ledger entry"""
        prop = EquipmentProperty(
            ledger_id=ledger_id,
            property_key=property_key,
            property_value=property_value,
            property_type=property_type
        )
        self.session.add(prop)
        self.session.flush()
        return prop

    def get_material_properties(self, ledger_id: UUID) -> List[MaterialProperty]:
        """Get all properties for a material ledger entry"""
        return self.session.query(MaterialProperty).filter(
            MaterialProperty.ledger_id == ledger_id
        ).all()

    def get_equipment_properties(self, ledger_id: UUID) -> List[EquipmentProperty]:
        """Get all properties for an equipment ledger entry"""
        return self.session.query(EquipmentProperty).filter(
            EquipmentProperty.ledger_id == ledger_id
        ).all()

    def get_ledger_with_properties(self, ledger_id: UUID) -> Optional[Dict]:
        """Get ledger entry with all its properties"""
        ledger = self.get_ledger_by_id(ledger_id)
        if not ledger:
            return None

        result = {
            "ledger": ledger,
            "properties": {}
        }

        if ledger.category == "material":
            props = self.get_material_properties(ledger_id)
            result["properties"] = {p.property_key: p.property_value for p in props}
        elif ledger.category == "equipment":
            props = self.get_equipment_properties(ledger_id)
            result["properties"] = {p.property_key: p.property_value for p in props}

        return result

    def verify_stock(self, ledger_id: UUID) -> Dict[str, Decimal]:
        """Verify current_stock by calculating from records"""
        ledger = self.get_ledger_by_id(ledger_id)
        if not ledger:
            return {"error": "Ledger not found"}

        cumulative_in = self._get_cumulative_in(ledger_id)
        cumulative_out = self._get_cumulative_out(ledger_id)
        calculated_stock = cumulative_in - cumulative_out

        return {
            "ledger_id": str(ledger_id),
            "current_stock_recorded": ledger.current_stock,
            "current_stock_calculated": calculated_stock,
            "cumulative_in": cumulative_in,
            "cumulative_out": cumulative_out,
            "is_match": ledger.current_stock == calculated_stock
        }
```

- [ ] **Step 3: 提交**

```bash
git add ledger_system/data/repository/ledger_repo.py
git commit -m "feat: add sequence/cumulative calculations and property management to LedgerRepository"
```

---

## Phase 2: Excel 导出功能

### Task 9: 创建 Excel 动态报表生成器

**Files:**
- Create: `ledger_system/business/report/report_generator.py`

- [ ] **Step 1: 创建 report_generator.py**

```python
"""Excel Report Generator for Ledger System"""
from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Optional
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils.dataframe import dataframe_to_rows

from ledger_system.data.database import get_session
from ledger_system.data.repository import LedgerRepository


class ReportGenerator:
    """Generate Excel reports from ledger data"""

    def __init__(self):
        self.repo = None

    def _get_repo(self):
        if self.repo is None:
            session = get_session().__enter__()
            self.repo = LedgerRepository(session)
        return self.repo

    def generate_full_report(self, output_path: str, start_date: date = None,
                            end_date: date = None) -> str:
        """Generate full report with all sheets"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with get_session() as session:
            repo = LedgerRepository(session)
            self.repo = repo

            with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
                # Sheet 2: 台账总览
                self._write_ledger_overview(repo, writer)

                # Sheet 3: 入库记录
                self._write_inbound_records(repo, writer, start_date, end_date)

                # Sheet 4: 出库记录
                self._write_outbound_records(repo, writer, start_date, end_date)

                # Sheet 5: 物料编码
                self._write_material_codes(repo, writer)

            return str(output_path)

    def generate_selected_report(self, ledger_ids: List[str], output_path: str) -> str:
        """Generate report for selected ledger entries"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with get_session() as session:
            repo = LedgerRepository(session)
            self.repo = repo

            with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
                # Sheet 1: 选中物料概览
                self._write_selected_overview(repo, ledger_ids, writer)

                # Sheet 2: 台账总览（选中）
                self._write_selected_ledger(repo, ledger_ids, writer)

                # Sheet 3: 入库记录（选中）
                self._write_selected_inbounds(repo, ledger_ids, writer)

                # Sheet 4: 出库记录（选中）
                self._write_selected_outbounds(repo, ledger_ids, writer)

            return str(output_path)

    def _write_ledger_overview(self, repo: LedgerRepository, writer) -> None:
        """Write ledger overview sheet"""
        ledgers = repo.get_all_ledgers()
        data = []

        for l in ledgers:
            # Get cumulative totals
            inbounds = repo.get_inbound_history(l.id, days=99999)
            outbounds = repo.get_outbound_history(l.id, days=99999)

            cumulative_in = sum(ib.quantity for ib in inbounds) if inbounds else Decimal(0)
            cumulative_out = sum(ob.quantity for outbounds) if outbounds else Decimal(0)

            status = "正常" if l.current_stock >= l.min_stock else "库存不足"

            data.append({
                "名称": l.name,
                "规格": l.specification,
                "类别": l.category,
                "单位": l.unit,
                "当前库存": float(l.current_stock),
                "最小库存": float(l.min_stock),
                "累计入库": float(cumulative_in),
                "累计出库": float(cumulative_out),
                "采购日期": l.purchase_date.isoformat() if l.purchase_date else "",
                "物料编码": l.material_code or "",
                "状态": status
            })

        df = pd.DataFrame(data)
        df.to_excel(writer, sheet_name="台账总览", index=False)
        self._apply_styles(writer.sheets["台账总览"])

    def _write_inbound_records(self, repo: LedgerRepository, writer,
                               start_date: date, end_date: date) -> None:
        """Write inbound records sheet"""
        inbounds = repo.get_all_inbounds(days=99999)

        data = []
        for ib in inbounds:
            if start_date and ib.inbound_date < start_date:
                continue
            if end_date and ib.inbound_date > end_date:
                continue

            ledger = repo.get_ledger_by_id(ib.ledger_id)
            data.append({
                "序号": f"第{ib.inbound_sequence}次",
                "入库日期": ib.inbound_date.isoformat(),
                "入库时间": ib.inbound_time.isoformat() if ib.inbound_time else "",
                "物料名称": ledger.name if ledger else "",
                "规格": ledger.specification if ledger else "",
                "数量": float(ib.quantity),
                "单位": ledger.unit if ledger else "",
                "累计入库": float(ib.cumulative_in),
                "供应商": ib.supplier,
                "操作人": ib.inbound_operator,
                "单据来源": ib.document_source,
                "备注": ib.notes
            })

        df = pd.DataFrame(data)
        df.to_excel(writer, sheet_name="入库记录", index=False)
        self._apply_styles(writer.sheets["入库记录"])

    def _write_outbound_records(self, repo: LedgerRepository, writer,
                               start_date: date, end_date: date) -> None:
        """Write outbound records sheet"""
        outbounds = repo.get_all_outbounds(days=99999)

        data = []
        for ob in outbounds:
            if start_date and ob.outbound_date < start_date:
                continue
            if end_date and ob.outbound_date > end_date:
                continue

            ledger = repo.get_ledger_by_id(ob.ledger_id)
            data.append({
                "序号": f"第{ob.outbound_sequence}次",
                "出库日期": ob.outbound_date.isoformat(),
                "出库时间": ob.outbound_time.isoformat() if ob.outbound_time else "",
                "物料名称": ledger.name if ledger else "",
                "规格": ledger.specification if ledger else "",
                "数量": float(ob.quantity),
                "单位": ledger.unit if ledger else "",
                "累计出库": float(ob.cumulative_out),
                "用途": ob.usage,
                "领用人": ob.receiver,
                "操作人": ob.outbound_operator,
                "备注": ob.notes
            })

        df = pd.DataFrame(data)
        df.to_excel(writer, sheet_name="出库记录", index=False)
        self._apply_styles(writer.sheets["出库记录"])

    def _write_material_codes(self, repo: LedgerRepository, writer) -> None:
        """Write material codes sheet"""
        from ledger_system.data.models import MaterialCode

        with get_session() as session:
            codes = session.query(MaterialCode).order_by(MaterialCode.code).all()

            data = [{
                "物料编码": c.code,
                "名称": c.name,
                "规格": c.specification,
                "单位": c.unit
            } for c in codes]

            df = pd.DataFrame(data)
            df.to_excel(writer, sheet_name="物料编码", index=False)
            self._apply_styles(writer.sheets["物料编码"])

    def _write_selected_overview(self, repo: LedgerRepository,
                                 ledger_ids: List[str], writer) -> None:
        """Write overview for selected ledger entries"""
        data = []

        for ledger_id in ledger_ids:
            from uuid import UUID
            try:
                l = repo.get_ledger_by_id(UUID(ledger_id))
            except:
                continue

            if not l:
                continue

            props = repo.get_ledger_with_properties(l.id)
            prop_dict = props.get("properties", {})

            data.append({
                "名称": l.name,
                "规格": l.specification,
                "类别": l.category,
                "单位": l.unit,
                "当前库存": float(l.current_stock),
                "物料编码": l.material_code or "",
                **prop_dict
            })

        df = pd.DataFrame(data)
        df.to_excel(writer, sheet_name="选中物料概览", index=False)
        self._apply_styles(writer.sheets["选中物料概览"])

    def _write_selected_ledger(self, repo: LedgerRepository,
                               ledger_ids: List[str], writer) -> None:
        """Write ledger for selected entries"""
        self._write_ledger_overview_filtered(repo, ledger_ids, writer, "台账总览")

    def _write_selected_inbounds(self, repo: LedgerRepository,
                                ledger_ids: List[str], writer) -> None:
        """Write inbound records for selected entries"""
        self._write_inbound_records_filtered(repo, ledger_ids, writer, "入库记录")

    def _write_selected_outbounds(self, repo: LedgerRepository,
                                 ledger_ids: List[str], writer) -> None:
        """Write outbound records for selected entries"""
        self._write_outbound_records_filtered(repo, ledger_ids, writer, "出库记录")

    def _write_ledger_overview_filtered(self, repo, ledger_ids, writer, sheet_name):
        """Write filtered ledger overview"""
        data = []
        for ledger_id in ledger_ids:
            from uuid import UUID
            try:
                l = repo.get_ledger_by_id(UUID(ledger_id))
            except:
                continue
            if not l:
                continue

            status = "正常" if l.current_stock >= l.min_stock else "库存不足"
            data.append({
                "名称": l.name,
                "规格": l.specification,
                "类别": l.category,
                "单位": l.unit,
                "当前库存": float(l.current_stock),
                "最小库存": float(l.min_stock),
                "状态": status
            })

        df = pd.DataFrame(data)
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        self._apply_styles(writer.sheets[sheet_name])

    def _write_inbound_records_filtered(self, repo, ledger_ids, writer, sheet_name):
        """Write filtered inbound records"""
        data = []
        for ledger_id in ledger_ids:
            from uuid import UUID
            try:
                inbounds = repo.get_inbound_history(UUID(ledger_id), days=99999)
            except:
                continue

            ledger = repo.get_ledger_by_id(UUID(ledger_id)) if ledger_ids else None
            for ib in inbounds:
                data.append({
                    "序号": f"第{ib.inbound_sequence}次",
                    "入库日期": ib.inbound_date.isoformat(),
                    "数量": float(ib.quantity),
                    "累计入库": float(ib.cumulative_in),
                    "供应商": ib.supplier
                })

        df = pd.DataFrame(data)
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        self._apply_styles(writer.sheets[sheet_name])

    def _write_outbound_records_filtered(self, repo, ledger_ids, writer, sheet_name):
        """Write filtered outbound records"""
        data = []
        for ledger_id in ledger_ids:
            from uuid import UUID
            try:
                outbounds = repo.get_outbound_history(UUID(ledger_id), days=99999)
            except:
                continue

            for ob in outbounds:
                data.append({
                    "序号": f"第{ob.outbound_sequence}次",
                    "出库日期": ob.outbound_date.isoformat(),
                    "数量": float(ob.quantity),
                    "累计出库": float(ob.cumulative_out),
                    "用途": ob.usage
                })

        df = pd.DataFrame(data)
        df.to_excel(writer, sheet_name=sheet_name, index=False)
        self._apply_styles(writer.sheets[sheet_name])

    def _apply_styles(self, sheet):
        """Apply standard styles to sheet"""
        header_font = Font(bold=True)
        header_fill = PatternFill(start_color="CCCCCC", end_color="CCCCCC", fill_type="solid")
        thin_border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin")
        )

        for cell in sheet[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")

        for row in sheet.iter_rows():
            for cell in row:
                cell.border = thin_border
```

- [ ] **Step 2: 提交**

```bash
git add ledger_system/business/report/report_generator.py
git commit -m "feat: add Excel report generator with multi-sheet export"
```

---

### Task 10: 更新 export 命令 - 支持多选导出

**Files:**
- Modify: `ledger_system/program/commands/export.py`

- [ ] **Step 1: 读取现有 export.py**

- [ ] **Step 2: 更新 export.py 支持多选导出**

```python
"""Export command - export reports"""
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ledger_system.business.report.report_generator import ReportGenerator


class ExportCommand:
    """Export ledger reports"""

    def execute(self, args):
        """Execute export command"""
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        generator = ReportGenerator()

        # Parse date range
        start_date = None
        end_date = None
        if hasattr(args, "start") and args.start:
            start_date = datetime.fromisoformat(args.start).date()
        if hasattr(args, "end") and args.end:
            end_date = datetime.fromisoformat(args.end).date()

        # Handle selected items export
        if hasattr(args, "selected") and args.selected:
            ledger_ids = args.selected
            result_path = generator.generate_selected_report(
                ledger_ids, str(output_path)
            )
            print(f"选中物料报表已导出: {result_path}")
            return

        # Full export
        result_path = generator.generate_full_report(
            str(output_path), start_date, end_date
        )
        print(f"报表已导出: {result_path}")
```

- [ ] **Step 3: 更新 CLI 添加 selected 参数**

在 `ledger_system/program/cli.py` 中更新 export 子命令：

```python
export_parser.add_argument("--selected", nargs="+", help="选中导出的物料ID列表")
```

- [ ] **Step 4: 提交**

```bash
git add ledger_system/program/commands/export.py ledger_system/program/cli.py
git commit -m "feat: add multi-select export support to export command"
```

---

## Phase 3: 数据迁移与验证

### Task 11: 创建数据迁移脚本

**Files:**
- Create: `ledger_system/data/migrations/add_sequence_and_properties.py`

- [ ] **Step 1: 创建迁移脚本**

```python
"""Migration script to add sequence and property fields"""
import sys
from pathlib import Path
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ledger_system.data.database import get_session, init_database
from ledger_system.data.repository import LedgerRepository
from ledger_system.data.models import Ledger, Inbound, Outbound


def migrate_inbound_sequence():
    """Migrate existing inbound records with sequence numbers"""
    print("迁移入库记录序号...")

    with get_session() as session:
        repo = LedgerRepository(session)

        # Get all inbounds grouped by ledger
        inbounds = session.query(Inbound).order_by(
            Inbound.ledger_id, Inbound.inbound_date, Inbound.inbound_time
        ).all()

        current_ledger_id = None
        sequence = 0
        cumulative = Decimal(0)

        for ib in inbounds:
            if ib.ledger_id != current_ledger_id:
                current_ledger_id = ib.ledger_id
                sequence = 0
                cumulative = Decimal(0)

            sequence += 1
            cumulative += ib.quantity

            ib.inbound_sequence = sequence
            ib.cumulative_in = cumulative

        session.commit()
        print(f"完成: 迁移了 {len(inbounds)} 条入库记录")


def migrate_outbound_sequence():
    """Migrate existing outbound records with sequence numbers"""
    print("迁移出库记录序号...")

    with get_session() as session:
        repo = LedgerRepository(session)

        # Get all outbounds grouped by ledger
        outbounds = session.query(Outbound).order_by(
            Outbound.ledger_id, Outbound.outbound_date, Outbound.outbound_time
        ).all()

        current_ledger_id = None
        sequence = 0
        cumulative = Decimal(0)

        for ob in outbounds:
            if ob.ledger_id != current_ledger_id:
                current_ledger_id = ob.ledger_id
                sequence = 0
                cumulative = Decimal(0)

            sequence += 1
            cumulative += ob.quantity

            ob.outbound_sequence = sequence
            ob.cumulative_out = cumulative

        session.commit()
        print(f"完成: 迁移了 {len(outbounds)} 条出库记录")


def migrate_material_properties():
    """Migrate material-specific properties from ledger to material_property table"""
    print("迁移物料属性...")

    from ledger_system.data.models import MaterialProperty

    # Property keys that belong to materials
    material_keys = ["medium", "material_type", "execution_standard",
                     "surface_treatment", "origin", "brand"]

    with get_session() as session:
        ledgers = session.query(Ledger).filter(Ledger.category == "material").all()

        count = 0
        for ledger in ledgers:
            for key in material_keys:
                value = getattr(ledger, key, None) or ""
                if value and value != "" and value != "0":
                    prop = MaterialProperty(
                        ledger_id=ledger.id,
                        property_key=key,
                        property_value=str(value),
                        property_type="material"
                    )
                    session.add(prop)
                    count += 1

        session.commit()
        print(f"完成: 迁移了 {count} 条物料属性")


def migrate_equipment_properties():
    """Migrate equipment-specific properties from ledger to equipment_property table"""
    print("迁移设备属性...")

    from ledger_system.data.models import EquipmentProperty

    # Property keys that belong to equipment
    equipment_keys = ["drive_type", "nominal_diameter", "valve_position",
                      "design_pressure", "design_temperature", "manufacturer"]

    with get_session() as session:
        ledgers = session.query(Ledger).filter(Ledger.category == "equipment").all()

        count = 0
        for ledger in ledgers:
            for key in equipment_keys:
                value = getattr(ledger, key, None) or ""
                if value and value != "" and value != "0":
                    prop = EquipmentProperty(
                        ledger_id=ledger.id,
                        property_key=key,
                        property_value=str(value),
                        property_type="mechanical"
                    )
                    session.add(prop)
                    count += 1

        session.commit()
        print(f"完成: 迁移了 {count} 条设备属性")


def remove_old_columns():
    """Remove old mixed columns from ledger table (requires DB migration)"""
    print("注意: 需要手动执行数据库迁移移除以下旧字段:")
    print("  - ledger.meduem, ledger.design_pressure, ledger.material_type")
    print("  - ledger.design_temperature, ledger.manufacturer, ledger.drive_type")
    print("  - ledger.nominal_diameter, ledger.valve_position")
    print("  请执行: ALTER TABLE ledger DROP COLUMN IF EXISTS <column_name>;")


if __name__ == "__main__":
    print("开始数据迁移...")
    migrate_inbound_sequence()
    migrate_outbound_sequence()
    migrate_material_properties()
    migrate_equipment_properties()
    remove_old_columns()
    print("迁移完成!")
```

- [ ] **Step 2: 提交**

```bash
git add ledger_system/data/migrations/add_sequence_and_properties.py
git commit -m "feat: add migration script for new schema"
```

---

---

## Phase 4: 材料看板（交互式 Dashboard）

### Task 12: 创建材料看板生成器

**Files:**
- Create: `ledger_system/business/report/dashboard_generator.py`

- [ ] **Step 1: 创建 dashboard_generator.py**

```python
"""Material Dashboard Generator - Interactive Excel Dashboard"""
from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Optional
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.chart import BarChart, Reference

from ledger_system.data.database import get_session
from ledger_system.data.repository import LedgerRepository


class DashboardGenerator:
    """Generate interactive Excel dashboard for material lookup"""

    def __init__(self):
        self.repo = None

    def generate(self, output_path: str) -> str:
        """Generate interactive dashboard Excel file"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        wb = Workbook()

        # Sheet 1: 材料看板 (Dashboard)
        self._create_dashboard_sheet(wb)

        # Sheet 2: 台账总览 (数据源)
        self._create_ledger_data_sheet(wb)

        # Sheet 3: 入库记录 (数据源)
        self._create_inbound_data_sheet(wb)

        # Sheet 4: 出库记录 (数据源)
        self._create_outbound_data_sheet(wb)

        wb.save(str(output_path))
        return str(output_path)

    def _create_dashboard_sheet(self, wb: Workbook) -> None:
        """Create the interactive dashboard sheet"""
        ws = wb.active
        ws.title = "材料看板"

        # Styles
        header_font = Font(bold=True, size=14, color="FFFFFF")
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        section_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        section_font = Font(bold=True, size=12)
        thin_border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin")
        )

        # Title
        ws.merge_cells("A1:L1")
        ws["A1"] = "材料信息看板"
        ws["A1"].font = Font(bold=True, size=18)
        ws["A1"].alignment = Alignment(horizontal="center")

        # Row 2: Search area
        ws["A3"] = "搜索材料:"
        ws["A3"].font = Font(bold=True)
        ws["B3"] = "=IFERROR(INDEX(台账总览!B:B, MATCH(材料看板!B2, 台账总览!A:A, 0)), \"\")"
        ws["B3"].font = Font(bold=True, size=12)
        ws["B3"].fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
        ws["C3"] = "← 输入物料名称或选择"

        # === Section 1: Basic Info ===
        ws.merge_cells("A5:L5")
        ws["A5"] = "基本信息"
        ws["A5"].fill = section_fill
        ws["A5"].font = section_font

        basic_labels = [
            ("名称", "B6"), ("规格", "B7"), ("类别", "B8"), ("单位", "C6"),
            ("物料编码", "C7"), ("采购日期", "C8"), ("当前库存", "E6"),
            ("最小库存", "E7"), ("库存状态", "E8"), ("累计入库", "G6"),
            ("累计出库", "G7"), ("净入库量", "G8")
        ]

        for label, cell in basic_labels:
            ws[cell] = label
            ws[cell].font = Font(bold=True)
            ws[cell].border = thin_border

        # VLOOKUP formulas for basic info
        ws["D6"] = "=IFERROR(VLOOKUP($B$3, 台账总览!A:N, 2, 0), \"\")"  # 名称
        ws["D7"] = "=IFERROR(VLOOKUP($B$3, 台账总览!A:N, 3, 0), \"\")"  # 规格
        ws["D8"] = "=IFERROR(VLOOKUP($B$3, 台账总览!A:N, 4, 0), \"\")"  # 类别
        ws["D6"].border = thin_border
        ws["D7"].border = thin_border
        ws["D8"].border = thin_border

        ws["E6"] = "=IFERROR(VLOOKUP($B$3, 台账总览!A:N, 5, 0), \"\")"  # 单位
        ws["E7"] = "=IFERROR(VLOOKUP($B$3, 台账总览!A:N, 12, 0), \"\")"  # 物料编码
        ws["E8"] = "=IFERROR(VLOOKUP($B$3, 台账总览!A:N, 13, 0), \"\")"  # 采购日期
        ws["E6"].border = thin_border
        ws["E7"].border = thin_border
        ws["E8"].border = thin_border

        ws["F6"] = "=IFERROR(VLOOKUP($B$3, 台账总览!A:N, 6, 0), \"\")"  # 当前库存
        ws["F7"] = "=IFERROR(VLOOKUP($B$3, 台账总览!A:N, 7, 0), \"\")"  # 最小库存
        ws["F8"] = "=IF(B3=\"\", \"\", IF(F6>=F7, \"✓ 正常\", \"⚠️ 库存不足\"))"  # 库存状态
        ws["F6"].border = thin_border
        ws["F7"].border = thin_border
        ws["F8"].border = thin_border

        ws["H6"] = "=IFERROR(VLOOKUP($B$3, 台账总览!A:N, 8, 0), \"\")"  # 累计入库
        ws["H7"] = "=IFERROR(VLOOKUP($B$3, 台账总览!A:N, 9, 0), \"\")"  # 累计出库
        ws["H8"] = "=IFERROR(VLOOKUP($B$3, 台账总览!A:N, 10, 0), \"\")"  # 净入库量
        ws["H6"].border = thin_border
        ws["H7"].border = thin_border
        ws["H8"].border = thin_border

        # === Section 2: Inbound History ===
        ws.merge_cells("A10:L10")
        ws["A10"] = "入库记录 (最近10条)"
        ws["A10"].fill = section_fill
        ws["A10"].font = section_font

        # Header row
        headers = ["序号", "日期", "时间", "数量", "单位", "累计入库", "供应商", "操作人", "备注"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=11, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.border = thin_border
            cell.alignment = Alignment(horizontal="center")

        # Data rows with VLOOKUP
        for row in range(12, 22):  # 10 rows
            ws.cell(row=row, column=1, value=f"第{row-11}次").border = thin_border
            for col in range(2, 10):
                ws.cell(row=row, column=col).border = thin_border

        # === Section 3: Outbound History ===
        ws.merge_cells("A24:L24")
        ws["A24"] = "出库记录 (最近10条)"
        ws["A24"].fill = section_fill
        ws["A24"].font = section_font

        # Header row
        for col, header in enumerate(headers[:7], 1):
            cell = ws.cell(row=25, column=col, value=header.replace("入库", "出库"))
            cell.font = header_font
            cell.fill = header_fill
            cell.border = thin_border
            cell.alignment = Alignment(horizontal="center")

        for row in range(26, 36):  # 10 rows
            ws.cell(row=row, column=1, value=f"第{row-25}次").border = thin_border
            for col in range(2, 8):
                ws.cell(row=row, column=col).border = thin_border

        # === Data Validation (Dropdown) ===
        # Create named range for materials
        # This will be populated when data sheets are created

        # Set column widths
        column_widths = {
            "A": 15, "B": 18, "C": 18, "D": 15, "E": 12, "F": 15,
            "G": 15, "H": 12, "I": 15, "J": 15, "K": 15, "L": 15
        }
        for col, width in column_widths.items():
            ws.column_dimensions[col].width = width

    def _create_ledger_data_sheet(self, wb: Workbook) -> None:
        """Create ledger overview data sheet"""
        ws = wb.create_sheet("台账总览")

        with get_session() as session:
            repo = LedgerRepository(session)
            ledgers = repo.get_all_ledgers()

            headers = ["名称", "规格", "类别", "单位", "当前库存", "最小库存",
                      "累计入库", "累计出库", "净入库量", "状态", "物料编码", "采购日期", "ID"]

            # Header row
            for col, header in enumerate(headers, 1):
                ws.cell(row=1, column=col, value=header)

            # Data rows
            for row_idx, l in enumerate(ledgers, 2):
                inbounds = repo.get_inbound_history(l.id, days=99999)
                outbounds = repo.get_outbound_history(l.id, days=99999)
                cumulative_in = sum(ib.quantity for ib in inbounds) if inbounds else Decimal(0)
                cumulative_out = sum(ob.quantity for ob in outbounds) if outbounds else Decimal(0)
                net_in = cumulative_in - cumulative_out
                status = "正常" if l.current_stock >= l.min_stock else "库存不足"

                ws.cell(row=row_idx, column=1, value=l.name)
                ws.cell(row=row_idx, column=2, value=l.specification)
                ws.cell(row=row_idx, column=3, value=l.category)
                ws.cell(row=row_idx, column=4, value=l.unit)
                ws.cell(row=row_idx, column=5, value=float(l.current_stock))
                ws.cell(row=row_idx, column=6, value=float(l.min_stock))
                ws.cell(row=row_idx, column=7, value=float(cumulative_in))
                ws.cell(row=row_idx, column=8, value=float(cumulative_out))
                ws.cell(row=row_idx, column=9, value=float(net_in))
                ws.cell(row=row_idx, column=10, value=status)
                ws.cell(row=row_idx, column=11, value=l.material_code or "")
                ws.cell(row=row_idx, column=12, value=l.purchase_date.isoformat() if l.purchase_date else "")
                ws.cell(row=row_idx, column=13, value=str(l.id))

        # Freeze top row
        ws.freeze_panes = "A2"

    def _create_inbound_data_sheet(self, wb: Workbook) -> None:
        """Create inbound records data sheet"""
        ws = wb.create_sheet("入库记录数据")

        with get_session() as session:
            repo = LedgerRepository(session)
            inbounds = repo.get_all_inbounds(days=99999)

            headers = ["物料名称", "序号", "日期", "时间", "数量", "单位",
                      "累计入库", "供应商", "操作人", "备注"]

            for col, header in enumerate(headers, 1):
                ws.cell(row=1, column=col, value=header)

            for row_idx, ib in enumerate(inbounds, 2):
                ledger = repo.get_ledger_by_id(ib.ledger_id)
                ws.cell(row=row_idx, column=1, value=ledger.name if ledger else "")
                ws.cell(row=row_idx, column=2, value=ib.inbound_sequence)
                ws.cell(row=row_idx, column=3, value=ib.inbound_date.isoformat())
                ws.cell(row=row_idx, column=4, value=str(ib.inbound_time) if ib.inbound_time else "")
                ws.cell(row=row_idx, column=5, value=float(ib.quantity))
                ws.cell(row=row_idx, column=6, value=ledger.unit if ledger else "")
                ws.cell(row=row_idx, column=7, value=float(ib.cumulative_in))
                ws.cell(row=row_idx, column=8, value=ib.supplier)
                ws.cell(row=row_idx, column=9, value=ib.inbound_operator)
                ws.cell(row=row_idx, column=10, value=ib.notes)

        ws.freeze_panes = "A2"

    def _create_outbound_data_sheet(self, wb: Workbook) -> None:
        """Create outbound records data sheet"""
        ws = wb.create_sheet("出库记录数据")

        with get_session() as session:
            repo = LedgerRepository(session)
            outbounds = repo.get_all_outbounds(days=99999)

            headers = ["物料名称", "序号", "日期", "时间", "数量", "单位",
                      "累计出库", "用途", "领用人", "操作人", "备注"]

            for col, header in enumerate(headers, 1):
                ws.cell(row=1, column=col, value=header)

            for row_idx, ob in enumerate(outbounds, 2):
                ledger = repo.get_ledger_by_id(ob.ledger_id)
                ws.cell(row=row_idx, column=1, value=ledger.name if ledger else "")
                ws.cell(row=row_idx, column=2, value=ob.outbound_sequence)
                ws.cell(row=row_idx, column=3, value=ob.outbound_date.isoformat())
                ws.cell(row=row_idx, column=4, value=str(ob.outbound_time) if ob.outbound_time else "")
                ws.cell(row=row_idx, column=5, value=float(ob.quantity))
                ws.cell(row=row_idx, column=6, value=ledger.unit if ledger else "")
                ws.cell(row=row_idx, column=7, value=float(ob.cumulative_out))
                ws.cell(row=row_idx, column=8, value=ob.usage)
                ws.cell(row=row_idx, column=9, value=ob.receiver)
                ws.cell(row=row_idx, column=10, value=ob.outbound_operator)
                ws.cell(row=row_idx, column=11, value=ob.notes)

        ws.freeze_panes = "A2"
```

- [ ] **Step 2: 提交**

```bash
git add ledger_system/business/report/dashboard_generator.py
git commit -m "feat: add interactive material dashboard generator"
```

---

### Task 13: 更新 export 命令 - 支持生成材料看板

**Files:**
- Modify: `ledger_system/program/commands/export.py`

- [ ] **Step 1: 更新 export.py 添加看板生成功能**

```python
"""Export command - export reports and dashboard"""
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ledger_system.business.report.report_generator import ReportGenerator
from ledger_system.business.report.dashboard_generator import DashboardGenerator


class ExportCommand:
    """Export ledger reports and dashboard"""

    def execute(self, args):
        """Execute export command"""
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate dashboard
        if hasattr(args, "dashboard") and args.dashboard:
            generator = DashboardGenerator()
            result_path = generator.generate(str(output_path))
            print(f"材料看板已生成: {result_path}")
            return

        # Parse date range
        start_date = None
        end_date = None
        if hasattr(args, "start") and args.start:
            start_date = datetime.fromisoformat(args.start).date()
        if hasattr(args, "end") and args.end:
            end_date = datetime.fromisoformat(args.end).date()

        # Handle selected items export
        if hasattr(args, "selected") and args.selected:
            generator = ReportGenerator()
            result_path = generator.generate_selected_report(
                args.selected, str(output_path)
            )
            print(f"选中物料报表已导出: {result_path}")
            return

        # Full export
        generator = ReportGenerator()
        result_path = generator.generate_full_report(
            str(output_path), start_date, end_date
        )
        print(f"报表已导出: {result_path}")
```

- [ ] **Step 2: 更新 CLI 添加 dashboard 参数**

在 `ledger_system/program/cli.py` 中更新：

```python
export_parser.add_argument("--dashboard", action="store_true",
                         help="生成交互式材料看板")
```

- [ ] **Step 3: 提交**

```bash
git add ledger_system/program/commands/export.py ledger_system/program/cli.py
git commit -m "feat: add dashboard generation to export command"
```

---

## Phase 5: 看板公式联动（高级交互）

### Task 14: 实现看板与数据源的公式联动

**Files:**
- Modify: `ledger_system/business/report/dashboard_generator.py`

- [ ] **Step 1: 更新 dashboard_generator.py 添加完整公式联动**

```python
"""Dashboard Generator - Enhanced with formula linkages"""
# 在 _create_dashboard_sheet 方法中添加以下公式联动

# 入库记录公式 - 使用 INDEX/MATCH
inbound_headers = ["序号", "日期", "时间", "数量", "单位", "累计入库", "供应商", "操作人", "备注"]
for row in range(12, 22):  # 10 rows
    # 序号
    ws.cell(row=row, column=1,
            value=f'=IFERROR(INDEX(入库记录数据!B$2:B$1000, MATCH(1, (入库记录数据!A$2:A$1000=$B$3)*(入库记录数据!B$2:B$1000={row-11}), 0)), "")')
    # 简化版 - 使用辅助列
    # 由于 Excel 数组公式复杂，使用 SUMIFS 简化
    ws.cell(row=row, column=1, value=f"第{row-11}次")
    ws.cell(row=row, column=2,
            value=f'=IFERROR(INDEX(入库记录数据!C:C, SMALL(IF(入库记录数据!A$2:A$1000=$B$3, ROW(入库记录数据!A$2:A$1000)-1), {row-11})), "")')
    ws.cell(row=row, column=4,
            value=f'=IFERROR(INDEX(入库记录数据!E:E, SMALL(IF(入库记录数据!A$2:A$1000=$B$3, ROW(入库记录数据!A$2:A$1000)-1), {row-11})), "")')
    ws.cell(row=row, column=6,
            value=f'=IFERROR(INDEX(入库记录数据!G:G, SMALL(IF(入库记录数据!A$2:A$1000=$B$3, ROW(入库记录数据!A$2:A$1000)-1), {row-11})), "")')
    ws.cell(row=row, column=8,
            value=f'=IFERROR(INDEX(入库记录数据!H:H, SMALL(IF(入库记录数据!A$2:A$1000=$B$3, ROW(入库记录数据!A$2:A$1000)-1), {row-11})), "")')

# 注: 完整公式联动需要 Excel 支持动态数组，或使用 VBA/脚本辅助
# 建议: 使用 Python 脚本定期刷新数据源，确保看板显示最新数据
```

- [ ] **Step 2: 添加多选物料功能**

在看板中添加多选列表区域，显示已选中的多个物料。

- [ ] **Step 3: 提交**

```bash
git add ledger_system/business/report/dashboard_generator.py
git commit -m "feat: enhance dashboard with formula linkages"
```

---

## 实施总结

| Phase | Task | Description |
|-------|------|-------------|
| 1 | 1 | BaseModel 添加 updated_at |
| 1 | 2 | Ledger 重构 - 添加 purchase_date |
| 1 | 3 | Inbound 添加序号和累计量 |
| 1 | 4 | Outbound 添加序号和累计量 |
| 1 | 5 | 创建 MaterialProperty 模型 |
| 1 | 6 | 创建 EquipmentProperty 模型 |
| 1 | 7 | 更新 models/__init__.py |
| 1 | 8 | LedgerRepository 重构 |
| 2 | 9 | Excel 报表生成器 |
| 2 | 10 | export 命令更新 |
| 3 | 11 | 数据迁移脚本 |
| 4 | 12 | 材料看板生成器 (DashboardGenerator) |
| 4 | 13 | export 命令添加 --dashboard 参数 |
| 5 | 14 | 看板公式联动增强 |

---

**Plan complete and saved to `docs/superpowers/plans/2026-04-30-database-implementation.md`**
