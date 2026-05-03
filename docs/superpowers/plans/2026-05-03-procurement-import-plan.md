# 采购清单导入实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 `设备材料采购清单汇总表20260421.xlsx` 中所有采购数据导入台账数据库，状态标记为"待入库"

**Architecture:** 创建统一的 `ledger_property` 属性表存储所有扩展字段，设备和材料共用，支持属性扩展。Ledger表新增 `inbound_status` 和 `planned_inbound_date` 字段标记入库状态。

**Tech Stack:** Python, SQLAlchemy, openpyxl, PostgreSQL

---

## 文件结构

```
ledger_system/
├── data/
│   ├── models/
│   │   ├── __init__.py                    # 导出 LedgerProperty
│   │   └── ledger_property.py             # 新增: 统一属性表模型
│   └── migrations/
│       └── 002_add_inbound_status_and_property_table.py  # 新增: 数据库迁移
├── business/
│   └── import/
│       ├── __init__.py                   # 新增
│       ├── procurement_import.py          # 新增: 采购清单导入主逻辑
│       └── sheet_parsers.py               # 新增: 各Sheet解析器
└── program/
    └── commands/
        └── import_procurement.py          # 新增: CLI命令
```

---

## 任务 1: 创建 LedgerProperty 模型

**Files:**
- Create: `ledger_system/data/models/ledger_property.py`
- Modify: `ledger_system/data/models/__init__.py`

- [ ] **Step 1: 创建 ledger_property.py**

```python
"""LedgerProperty (台账属性表) model - 统一属性表，设备和材料通用"""
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ledger_system.data.models.base import BaseModel


class LedgerProperty(BaseModel):
    """统一属性表 for dynamic key-value attributes"""
    __tablename__ = "ledger_property"

    ledger_id = Column(UUID(as_uuid=True), ForeignKey("ledger.id"), nullable=False)
    property_key = Column(String(50), nullable=False)     # 属性名
    property_value = Column(String(500), default="")      # 属性值
    property_category = Column(String(20), default="")    # 分类

    # relationship
    ledger = relationship("Ledger", backref="properties")

    def __repr__(self):
        return f"<LedgerProperty {self.property_key}: {self.property_value}>"


# 预设属性类型（可扩展）
PROPERTY_KEYS = {
    # 设备属性
    "drive_type": ("驱动形式", "mechanical"),
    "nominal_diameter": ("公称直径", "mechanical"),
    "valve_position": ("阀门位置", "mechanical"),
    "design_pressure": ("设计压力", "pressure"),
    "design_temperature": ("设计温度", "temperature"),
    # 材料属性
    "medium": ("介质", "material"),
    "material_type": ("材质", "material"),
    "execution_standard": ("执行标准", "standard"),
    "surface_treatment": ("表面处理", "material"),
    # 通用属性
    "manufacturer": ("厂家", "material"),
    "brand": ("品牌", "material"),
    "weight": ("重量", "physical"),
    "technical_params": ("技术参数", "specification"),
    "board": ("板块", "category"),
    "item_type": ("物资类型", "category"),
    "purchase_date": ("采购单下发时间", "date"),
}
```

- [ ] **Step 2: 修改 __init__.py 导出 LedgerProperty**

在 `ledger_system/data/models/__init__.py` 添加:
```python
from ledger_system.data.models.ledger_property import LedgerProperty
```

- [ ] **Step 3: 验证模型创建**

Run: `cd /d/工作/日常工作/台账 && PYTHONPATH=. python -c "from ledger_system.data.models import LedgerProperty; print('OK')"`
Expected: OK

---

## 任务 2: 数据库迁移

**Files:**
- Create: `ledger_system/data/migrations/002_add_inbound_status_and_property_table.py`

- [ ] **Step 1: 创建迁移脚本**

```python
"""Migration: 添加 inbound_status, planned_inbound_date 字段和 ledger_property 表"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ledger_system.data.database import get_session
from sqlalchemy import text


def migrate():
    with get_session() as session:
        # 1. 添加 Ledger 表新字段
        session.execute(text("""
            ALTER TABLE ledger 
            ADD COLUMN IF NOT EXISTS inbound_status VARCHAR(20) DEFAULT '待入库',
            ADD COLUMN IF NOT EXISTS planned_inbound_date DATE;
        """))
        
        # 2. 创建 ledger_property 表
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS ledger_property (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ledger_id UUID NOT NULL REFERENCES ledger(id),
                property_key VARCHAR(50) NOT NULL,
                property_value VARCHAR(500) DEFAULT '',
                property_category VARCHAR(20) DEFAULT ''
            );
        """))
        
        # 3. 创建索引
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_ledger_property_ledger_id ON ledger_property(ledger_id);
            CREATE INDEX IF NOT EXISTS idx_ledger_property_key ON ledger_property(property_key);
        """))
        
        session.commit()
        print("Migration completed: ledger.inbound_status, ledger.planned_inbound_date, ledger_property table")


if __name__ == "__main__":
    migrate()
```

- [ ] **Step 2: 执行迁移**

Run: `cd /d/工作/日常工作/台账 && PYTHONPATH=. python ledger_system/data/migrations/002_add_inbound_status_and_property_table.py`
Expected: Migration completed: ...

- [ ] **Step 3: 验证迁移**

Run: `cd /d/工作/日常工作/台账 && PYTHONPATH=. python -c "
from ledger_system.data.database import get_session
from sqlalchemy import inspect
with get_session() as session:
    inspector = inspect(session.bind)
    cols = inspector.get_columns('ledger')
    print('Ledger new columns:', [c['name'] for c in cols if c['name'] in ['inbound_status', 'planned_inbound_date']])
    tables = inspector.get_table_names()
    print('Tables:', tables)
"`
Expected: 显示新字段和 ledger_property 表

---

## 任务 3: 创建 Sheet 解析器

**Files:**
- Create: `ledger_system/business/import/sheet_parsers.py`

- [ ] **Step 1: 创建 sheet_parsers.py**

```python
"""各Sheet的解析器 - 将Excel行数据转换为Ledger记录格式"""
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Tuple


class SheetParser:
    """基础解析器"""
    
    @staticmethod
    def excel_date_to_date(excel_date) -> date:
        """Excel日期数字转为date对象"""
        if excel_date is None:
            return None
        if isinstance(excel_date, (int, float)):
            # Excel epoch is Jan 1, 1900; Python epoch is Jan 1, 1970
            # Excel date 46133 = 2026-04-21
            try:
                return datetime(1899, 12, 30) + timedelta(days=int(excel_date)).date()
            except:
                return None
        if isinstance(excel_date, datetime):
            return excel_date.date()
        return None
    
    @staticmethod
    def detect_category(name: str, item_type: str, sheet_name: str) -> str:
        """判断是设备还是材料"""
        name_lower = (name or "").lower()
        item_type_lower = (item_type or "").lower()
        
        # 阀门一定是设备
        if any(kw in name_lower for kw in ['球阀', '闸阀', '截止阀', '止回阀', '蝶阀']):
            return "equipment"
        
        # 设备关键词
        equipment_kw = ['服务器', '主机', '仪表', '传感器', '流量计', '冷干机', '塔架', '控制柜', '摄像头', '交换机']
        if any(kw in name_lower for kw in equipment_kw):
            return "equipment"
        
        # 默认材料
        return "material"


class Sheet01Parser(SheetParser):
    """01设备采购清单汇总表解析器 (42行)"""
    
    @staticmethod
    def parse_row(row: Tuple) -> Dict:
        """row: (序号, 板块, 物资名称, 物资类型, 数量, 单位, 技术参数, 品牌, 采购单下发时间, 是否已到货, 到货时间, 备注)"""
        seq, board, name, item_type, qty, unit, tech_params, brand, purchase_date, arrived, arrived_date, notes = row
        
        return {
            "name": name,
            "category": SheetParser.detect_category(name, item_type, "01设备采购清单汇总表"),
            "specification": "",
            "unit": unit or "",
            "quantity": qty,
            "inbound_status": "待入库",
            "planned_inbound_date": SheetParser.excel_date_to_date(purchase_date),
            "properties": {
                "board": board,
                "item_type": item_type,
                "technical_params": tech_params,
                "brand": brand,
                "purchase_date": str(purchase_date) if purchase_date else None,
            }
        }


class Sheet01_01Parser(SheetParser):
    """01-01流量计安装材料采购清单解析器 (22行)"""
    
    @staticmethod
    def parse_row(row: Tuple) -> Dict:
        """row: (序号, 材料名称, 规格型号, 材质, 技术要求, 数量, 单位, 重量Kg, 备注, 采购单下发时间, 是否已到货, 到货时间, 备注2)"""
        seq, name, spec, material, tech_req, qty, unit, weight, notes, purchase_date, arrived, arrived_date, notes2 = row
        
        return {
            "name": name,
            "category": "material",
            "specification": spec or "",
            "unit": unit or "",
            "quantity": qty,
            "inbound_status": "待入库",
            "planned_inbound_date": SheetParser.excel_date_to_date(purchase_date),
            "properties": {
                "material_type": material,
                "technical_params": tech_req,
                "weight": str(weight) if weight else None,
                "notes": notes or notes2 or "",
                "brand": None,
            }
        }


class Sheet02Parser(SheetParser):
    """02材料采购清单汇总表解析器 (66行)"""
    
    @staticmethod
    def parse_row(row: Tuple) -> Dict:
        """row: (序号, 板块, 物资名称, 物资类型, 数量, 单位, 技术参数, 品牌, 采购单下发时间, 是否已到货, 到货时间, 备注)"""
        seq, board, name, item_type, qty, unit, tech_params, brand, purchase_date, arrived, arrived_date, notes = row
        
        return {
            "name": name,
            "category": SheetParser.detect_category(name, item_type, "02材料采购清单汇总表"),
            "specification": "",
            "unit": unit or "",
            "quantity": qty,
            "inbound_status": "待入库",
            "planned_inbound_date": SheetParser.excel_date_to_date(purchase_date),
            "properties": {
                "board": board,
                "item_type": item_type,
                "technical_params": tech_params,
                "brand": brand,
                "purchase_date": str(purchase_date) if purchase_date else None,
            }
        }


class Sheet02_01Parser(SheetParser):
    """02-01雾炮塔架材料清单解析器 (17行)"""
    
    @staticmethod
    def parse_row(row: Tuple) -> Dict:
        """row: (序号, 材料名称, 规格型号, 材质, 技术要求, 数量, 单位, 重量Kg, 备注, 采购单下发时间, 是否已到货, 到货时间, 备注2, ...)"""
        seq, name, spec, material, tech_req, qty, unit, weight, notes, purchase_date, arrived, arrived_date, notes2 = row[:13]
        
        return {
            "name": name,
            "category": "material",
            "specification": spec or "",
            "unit": unit or "",
            "quantity": qty,
            "inbound_status": "待入库",
            "planned_inbound_date": SheetParser.excel_date_to_date(purchase_date),
            "properties": {
                "material_type": material,
                "technical_params": tech_req,
                "weight": str(weight) if weight else None,
                "notes": notes or notes2 or "",
            }
        }


class Sheet02_02Parser(SheetParser):
    """02-02阀门采购清单解析器 (11行) - 设备专属字段"""
    
    @staticmethod
    def parse_row(row: Tuple) -> Dict:
        """row: (序号, 名称, 驱动形式, 公称直径, 介质, 设计压力MPa, 设计温度°C, 阀门位置, 数量, 单位, 阀体材质, 备注, 采购单下发时间, 是否已到货, 到货时间, 备注2)"""
        seq, name, drive_type, nom_dia, medium, design_pressure, design_temp, valve_pos, qty, unit, material_type, notes, purchase_date, arrived, arrived_date, notes2 = row
        
        return {
            "name": name,
            "category": "equipment",
            "specification": f"{nom_dia}; {material_type}" if nom_dia and material_type else (nom_dia or material_type or ""),
            "unit": unit or "",
            "quantity": qty,
            "inbound_status": "待入库",
            "planned_inbound_date": SheetParser.excel_date_to_date(purchase_date),
            "properties": {
                "drive_type": drive_type,
                "nominal_diameter": nom_dia,
                "medium": medium,
                "design_pressure": design_pressure,
                "design_temperature": str(design_temp) if design_temp else None,
                "valve_position": valve_pos,
                "material_type": material_type,
                "notes": notes or notes2 or "",
            }
        }


class Sheet02_03Parser(SheetParser):
    """02-03标准件采购清单解析器 (46行)"""
    
    @staticmethod
    def parse_row(row: Tuple) -> Dict:
        """row: (序号, 名称, 标准/规格/材质, 要求, 数量, 单位, 备注, 采购单下发时间, 是否已到货, 到货时间, 备注2, ...)"""
        seq, name, spec_material, requirement, qty, unit, notes, purchase_date, arrived, arrived_date, notes2 = row[:11]
        
        return {
            "name": name,
            "category": "material",
            "specification": spec_material or "",
            "unit": unit or "",
            "quantity": qty,
            "inbound_status": "待入库",
            "planned_inbound_date": SheetParser.excel_date_to_date(purchase_date),
            "properties": {
                "technical_params": requirement,
                "notes": notes or notes2 or "",
            }
        }


class Sheet03Parser(SheetParser):
    """03电气材料采购清单解析器 (48行)"""
    
    @staticmethod
    def parse_row(row: Tuple) -> Dict:
        """row: (序号, 物资名称, 物资类型, 数量, 单位, 技术参数, 品牌, 采购单下发时间, 是否已到货, 到货时间, 备注)"""
        seq, name, item_type, qty, unit, tech_params, brand, purchase_date, arrived, arrived_date, notes = row
        
        return {
            "name": name,
            "category": SheetParser.detect_category(name, item_type, "03电气材料采购清单"),
            "specification": "",
            "unit": unit or "",
            "quantity": qty,
            "inbound_status": "待入库",
            "planned_inbound_date": SheetParser.excel_date_to_date(purchase_date),
            "properties": {
                "item_type": item_type,
                "technical_params": tech_params,
                "brand": brand,
                "notes": notes or "",
            }
        }


# 解析器映射
SHEET_PARSERS = {
    "01设备采购清单汇总表": Sheet01Parser,
    "01-01流量计安装材料采购清单": Sheet01_01Parser,
    "02材料采购清单汇总表": Sheet02Parser,
    "02-01雾炮塔架材料清单": Sheet02_01Parser,
    "02-02阀门采购清单": Sheet02_02Parser,
    "02-03标准件采购清单": Sheet02_03Parser,
    "03电气材料采购清单": Sheet03Parser,
}
```

- [ ] **Step 2: 验证解析器**

Run: `cd /d/工作/日常工作/台账 && PYTHONPATH=. python -c "
from ledger_system.business.import.sheet_parsers import SHEET_PARSERS
print('Loaded parsers:', list(SHEET_PARSERS.keys()))
"`

---

## 任务 4: 创建采购导入主逻辑

**Files:**
- Create: `ledger_system/business/import/procurement_import.py`
- Create: `ledger_system/business/import/__init__.py`

- [ ] **Step 1: 创建 procurement_import.py**

```python
"""采购清单导入主逻辑"""
from datetime import timedelta
from decimal import Decimal
from typing import Dict, List
import logging

from openpyxl import load_workbook
from ledger_system.data.database import get_session
from ledger_system.data.models import Ledger, LedgerProperty
from ledger_system.business.import.sheet_parsers import SHEET_PARSERS

logger = logging.getLogger(__name__)


class ProcurementImporter:
    """采购清单导入器"""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.wb = None
        self.total_created = 0
        self.sheet_stats = {}
    
    def import_all(self) -> Dict:
        """导入所有Sheet"""
        self.wb = load_workbook(self.file_path, data_only=True)
        
        results = {}
        for sheet_name in self.wb.sheetnames:
            if sheet_name == "到货清单":
                results[sheet_name] = {"status": "skipped", "reason": "空Sheet"}
                continue
            
            parser_class = SHEET_PARSERS.get(sheet_name)
            if not parser_class:
                logger.warning(f"未找到解析器: {sheet_name}")
                results[sheet_name] = {"status": "skipped", "reason": "无解析器"}
                continue
            
            created = self._import_sheet(sheet_name, parser_class)
            results[sheet_name] = {"status": "success", "created": created}
        
        self.wb.close()
        return results
    
    def _import_sheet(self, sheet_name: str, parser_class) -> int:
        """导入单个Sheet"""
        ws = self.wb[sheet_name]
        created = 0
        
        # 跳过前两行(标题和表头)
        rows = list(ws.iter_rows(min_row=3, values_only=True))
        
        with get_session() as session:
            for row in rows:
                # 跳过空行
                if not any(cell is not None for cell in row):
                    continue
                
                try:
                    data = parser_class.parse_row(row)
                    self._create_ledger_with_properties(session, data)
                    created += 1
                except Exception as e:
                    logger.error(f"解析行失败 [{sheet_name}]: {e}, row={row}")
            
            session.commit()
        
        self.total_created += created
        self.sheet_stats[sheet_name] = created
        logger.info(f"导入完成 [{sheet_name}]: {created} 条")
        return created
    
    def _create_ledger_with_properties(self, session, data: Dict):
        """创建Ledger记录及关联属性"""
        # 创建Ledger
        ledger = Ledger(
            category=data["category"],
            name=data["name"],
            specification=data.get("specification", ""),
            unit=data.get("unit", ""),
            current_stock=Decimal(str(data.get("quantity", 0))),
            min_stock=Decimal("0"),
            inbound_status=data.get("inbound_status", "待入库"),
            planned_inbound_date=data.get("planned_inbound_date"),
        )
        session.add(ledger)
        session.flush()  # 获取ID
        
        # 创建属性记录
        properties = data.get("properties", {})
        for key, value in properties.items():
            if value is None or value == "":
                continue
            
            prop = LedgerProperty(
                ledger_id=ledger.id,
                property_key=str(key),
                property_value=str(value),
                property_category=self._get_property_category(key)
            )
            session.add(prop)
    
    @staticmethod
    def _get_property_category(key: str) -> str:
        """获取属性分类"""
        from ledger_system.data.models.ledger_property import PROPERTY_KEYS
        return PROPERTY_KEYS.get(key, ("", ""))[1] if key in PROPERTY_KEYS else ""
    
    @staticmethod
    def excel_date_to_date(excel_date) -> date:
        """Excel日期数字转为date对象"""
        if excel_date is None:
            return None
        if isinstance(excel_date, (int, float)):
            try:
                from datetime import datetime
                return (datetime(1899, 12, 30) + timedelta(days=int(excel_date))).date()
            except:
                return None
        if hasattr(excel_date, 'date'):
            return excel_date.date()
        return None


def import_procurement_list(file_path: str) -> Dict:
    """导入采购清单主函数"""
    importer = ProcurementImporter(file_path)
    return importer.import_all()
```

- [ ] **Step 2: 创建 __init__.py**

```python
"""采购导入模块"""
from ledger_system.business.import.procurement_import import ProcurementImporter, import_procurement_list

__all__ = ["ProcurementImporter", "import_procurement_list"]
```

- [ ] **Step 3: 验证导入逻辑**

Run: `cd /d/工作/日常工作/台账 && PYTHONPATH=. python -c "
from ledger_system.business.import.procurement_import import ProcurementImporter
from ledger_system.business.import.sheet_parsers import SHEET_PARSERS
print('Importers OK, parsers:', len(SHEET_PARSERS))
"`

---

## 任务 5: 创建 CLI 命令

**Files:**
- Create: `ledger_system/program/commands/import_procurement_command.py`
- Modify: `ledger_system/program/cli.py`

- [ ] **Step 1: 创建 import_procurement_command.py**

```python
"""import_procurement 命令 - 导入采购清单到台账"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from ledger_system.business.import import import_procurement_list


class ImportProcurementCommand:
    
    def execute(self, args: argparse.Namespace):
        file_path = args.file
        
        if not Path(file_path).exists():
            print(f"文件不存在: {file_path}")
            return
        
        print(f"开始导入: {file_path}")
        results = import_procurement_list(file_path)
        
        print("\n=== 导入结果 ===")
        total = 0
        for sheet, result in results.items():
            if result["status"] == "success":
                print(f"  {sheet}: {result['created']} 条")
                total += result.get("created", 0)
            else:
                print(f"  {sheet}: {result['status']} - {result.get('reason', '')}")
        
        print(f"\n总计: {total} 条记录导入完成")


def add_parser(subparsers):
    parser = subparsers.add_parser("import", help="导入采购清单到台账")
    parser.add_argument("file", help="采购清单Excel文件路径")
    return parser
```

- [ ] **Step 2: 修改 cli.py 添加 import 命令**

在 cli.py 的 imports 中添加:
```python
from ledger_system.program.commands.import_procurement_command import ImportProcurementCommand
```

在 create_parser() 中 import_parser:
```python
import_parser = subparsers.add_parser("import", help="导入采购清单到台账")
import_parser.add_argument("file", help="采购清单Excel文件路径")
```

在 main() 中添加:
```python
elif args.command == "import":
    cmd = ImportProcurementCommand()
    cmd.execute(args)
```

- [ ] **Step 3: 测试CLI命令**

Run: `cd /d/工作/日常工作/台账 && PYTHONPATH=. python ledger_system/program/cli.py import --help`
Expected: 显示 import 命令帮助

---

## 任务 6: 执行导入

**Files:**
- Execute: 导入 `设备材料采购清单汇总表20260421.xlsx`

- [ ] **Step 1: 执行导入**

Run: `cd /d/工作/日常工作/台账 && PYTHONPATH=. python ledger_system/program/cli.py import "设备材料采购清单汇总表20260421.xlsx" 2>&1`
Expected: 显示每Sheet导入结果，总计252条左右

- [ ] **Step 2: 验证导入结果**

Run: `cd /d/工作/日常工作/台账 && PYTHONPATH=. python -c "
from ledger_system.data.database import get_session
from ledger_system.data.models import Ledger, LedgerProperty
from sqlalchemy import func

with get_session() as session:
    total = session.query(func.count(Ledger.id)).scalar()
    equipment = session.query(func.count(Ledger.id)).filter(Ledger.category == 'equipment').scalar()
    material = session.query(func.count(Ledger.id)).filter(Ledger.category == 'material').scalar()
    pending = session.query(func.count(Ledger.id)).filter(Ledger.inbound_status == '待入库').scalar()
    props = session.query(func.count(LedgerProperty.id)).scalar()
    
    print(f'总记录: {total}')
    print(f'  设备: {equipment}')
    print(f'  材料: {material}')
    print(f'  待入库: {pending}')
    print(f'  属性记录: {props}')
"`

---

## 任务 7: 验证数据完整性

**Files:**
- Query: 验证数据

- [ ] **Step 1: 检查各Sheet数据量**

Run: `cd /d/工作/日常工作/台账 && PYTHONPATH=. python -c "
from ledger_system.data.database import get_session
from ledger_system.data.models import Ledger, LedgerProperty

with get_session() as session:
    # 按属性统计各Sheet来源
    props = session.query(
        LedgerProperty.property_value,
        func.count(LedgerProperty.id)
    ).filter(
        LedgerProperty.property_key == 'board'
    ).group_by(LedgerProperty.property_value).all()
    
    print('板块分布:')
    for p, c in props:
        print(f'  {p}: {c}')
    
    # 检查阀门设备属性
    valve = session.query(Ledger).filter(Ledger.name.like('%阀%')).all()
    print(f'\\n阀门记录数: {len(valve)}')
    if valve:
        v = valve[0]
        print(f'  第一个: {v.name}, 规格: {v.specification}')
        props = session.query(LedgerProperty).filter(LedgerProperty.ledger_id == v.id).all()
        print(f'  属性: {[(p.property_key, p.property_value) for p in props]}')
"`

---

## 任务 8: 提交代码

**Files:**
- Commit: 提交所有更改

- [ ] **Step 1: 提交**

Run: `cd /d/工作/日常工作/台账 && git add -A && git status`
Expected: 显示新文件和修改

Run: `git commit -m "$(cat <<'EOF'
feat: 采购清单导入功能

- 新增 LedgerProperty 统一属性表模型
- Ledger 新增 inbound_status, planned_inbound_date 字段
- 创建各Sheet解析器支持8个表格导入
- 新增 import CLI 命令
- 导入 设备材料采购清单汇总表20260421.xlsx 共252条记录

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"`