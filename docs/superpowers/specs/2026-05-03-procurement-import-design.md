# 采购清单导入设计方案

## 概述

将 `设备材料采购清单汇总表20260421.xlsx` 中的所有采购数据导入台账数据库，作为"待入库"状态记录。

## 数据源

| Sheet | 行数 |
|-------|------|
| 01设备采购清单汇总表 | 42 |
| 01-01流量计安装材料采购清单 | 22 |
| 02材料采购清单汇总表 | 66 |
| 02-01雾炮塔架材料清单 | 17 |
| 02-02阀门采购清单 | 11 |
| 02-03标准件采购清单 | 46 |
| 03电气材料采购清单 | 48 |
| 到货清单 | 0 (空) |

**总计: 252 条记录**

## 数据库扩展

### 1. Ledger 表新增字段

```python
inbound_status = Column(String(20), default="待入库")  # 待入库/部分入库/已入库
planned_inbound_date = Column(Date, nullable=True)      # 计划入库日期
```

### 2. 统一属性表 ledger_property

设备和材料共用，支持属性扩展：

```python
class LedgerProperty(BaseModel):
    __tablename__ = "ledger_property"

    ledger_id = Column(UUID(as_uuid=True), ForeignKey("ledger.id"), nullable=False)
    property_key = Column(String(50), nullable=False)     # 属性名
    property_value = Column(String(500), default="")      # 属性值
    property_category = Column(String(20), default="")    # 分类

    ledger = relationship("Ledger", backref="properties")
```

### 3. 预设属性类型（可扩展）

| property_key | 中文名 | category |
|--------------|--------|----------|
| drive_type | 驱动形式 | mechanical |
| nominal_diameter | 公称直径 | mechanical |
| medium | 介质 | material |
| design_pressure | 设计压力 | pressure |
| design_temperature | 设计温度 | temperature |
| valve_position | 阀门位置 | mechanical |
| manufacturer | 厂家 | material |
| material_type | 材质 | material |
| execution_standard | 执行标准 | standard |
| surface_treatment | 表面处理 | material |
| brand | 品牌 | material |
| weight | 重量 | physical |
| technical_params | 技术参数 | specification |
| board | 板块 | category |
| item_type | 物资类型 | category |

## 导入规则

### 1. 分类判断

每行数据独立判断是设备(equipment)还是材料(material)：
- 阀门类 → equipment
- 服务器、仪表、塔架类 → equipment
- 钢管、螺栓、光缆、标准件 → material
- 混合Sheet（如01设备采购清单汇总表）按行判断

### 2. 不去重

每行数据独立创建 Ledger 记录，即使名称+规格相同也分别创建。

### 3. 不合并数量

原始数量保持不变，每行一个 Ledger 记录。

### 4. 属性全量写入

该行所有非空字段都存入 `ledger_property` 表，包括：
- 技术参数
- 品牌
- 采购单下发时间
- 重量
- 备注
- 等

### 5. 状态标记

- `inbound_status = "待入库"`
- `planned_inbound_date = 2026-04-21` (Excel日期值46133转换)

## 实现步骤

1. **数据库迁移**:
   - 创建 `ledger_property` 表
   - Ledger 表新增 `inbound_status`, `planned_inbound_date` 字段

2. **导入脚本**:
   - 读取Excel所有Sheet
   - 逐Sheet逐行解析
   - 每行创建 Ledger + 关联属性
   - 支持分批导入（每Sheet一个事务）

3. **验证**:
   - 统计导入记录数
   - 验证属性完整性

## 字段映射示例

### 设备 (01设备采购清单汇总表)
```
name: 视频储存服务器
category: equipment
specification: -
unit: 套
current_stock: 0 (待入库)
inbound_status: 待入库
planned_inbound_date: 2026-04-21
properties:
  - board: 管控中心设备
  - item_type: 管控中心设备
  - technical_params: [硬件规格]...
  - brand: 海康
  - purchase_date: 46133
```

### 阀门 (02-02阀门采购清单)
```
name: 球阀-1
category: equipment
specification: Q47F-10-DN150；304不锈钢；法兰
unit: 个
current_stock: 0
inbound_status: 待入库
properties:
  - drive_type: 手动
  - nominal_diameter: DN150
  - medium: 水
  - design_pressure: PN1.6
  - design_temperature: 60°C
  - material_type: 304不锈钢
  - valve_position: 法兰连接
```