# 台账管理系统 - 数据库设计文档

**日期**: 2026-04-30
**版本**: v2.0
**状态**: 已批准

---

## 1. 设计目标

1. **材料特征维度完善** — 通过类型化属性表支持物料/设备两套独立属性体系
2. **序号与累计量自动化** — 入库/出库记录自动计算序号和累计量
3. **关键信息补全** — 台账主表增加采购日期
4. **Excel 动态报表** — 支持查询看板、多选导出、分类导出

---

## 2. 表结构设计

### 2.1 ledger（台账主表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| category | VARCHAR(20) | **material** / **equipment** |
| name | VARCHAR(200) | 名称 |
| specification | VARCHAR(500) | 规格型号 |
| unit | VARCHAR(20) | 单位 |
| current_stock | DECIMAL(10,2) | 当前库存（实时准确） |
| min_stock | DECIMAL(10,2) | 最小库存 |
| purchase_date | DATE | 采购日期 |
| material_code | VARCHAR(18) | 外键 → material_code.code |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### 2.2 inbound（入库记录）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| ledger_id | UUID | 外键 → ledger.id |
| quantity | DECIMAL(10,2) | 本次入库数量 |
| inbound_sequence | INTEGER | **第N次入库**（自动计算） |
| cumulative_in | DECIMAL(10,2) | **累计入库量**（自动计算） |
| supplier | VARCHAR(200) | 供应商 |
| inbound_date | DATE | 入库日期 |
| inbound_time | TIME | 入库时间 |
| inbound_operator | VARCHAR(100) | 操作人 |
| document_source | VARCHAR(500) | 单据来源 |
| original_document_path | VARCHAR(500) | 原始单据路径 |
| notes | TEXT | 备注 |
| created_at | TIMESTAMP | 创建时间 |

### 2.3 outbound（出库记录）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| ledger_id | UUID | 外键 → ledger.id |
| quantity | DECIMAL(10,2) | 本次出库数量 |
| outbound_sequence | INTEGER | **第N次出库**（自动计算） |
| cumulative_out | DECIMAL(10,2) | **累计出库量**（自动计算） |
| usage | VARCHAR(200) | 使用去向/用途 |
| outbound_date | DATE | 出库日期 |
| outbound_time | TIME | 出库时间 |
| receiver | VARCHAR(100) | 领用人 |
| outbound_operator | VARCHAR(100) | 操作人 |
| original_document_path | VARCHAR(500) | 原始单据路径 |
| notes | TEXT | 备注 |
| created_at | TIMESTAMP | 创建时间 |

### 2.4 material_property（物料属性表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| ledger_id | UUID | 外键 → ledger.id（仅 category=material） |
| property_key | VARCHAR(50) | 属性键 |
| property_value | VARCHAR(500) | 属性值 |
| property_type | VARCHAR(50) | 属性分类 |

**预置属性键：**

| property_key | 说明 | 示例 |
|--------------|------|------|
| execution_standard | 执行标准 | GB/T 6728-2002 |
| material_type | 材质 | Q235、304不锈钢 |
| medium | 介质 | 水、空气 |
| surface_treatment | 表面处理 | 镀锌、喷漆 |
| origin | 产地/厂家 | 杭州建材 |
| brand | 品牌 | 品牌名称 |

### 2.5 equipment_property（设备属性表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| ledger_id | UUID | 外键 → ledger.id（仅 category=equipment） |
| property_key | VARCHAR(50) | 属性键 |
| property_value | VARCHAR(500) | 属性值 |
| property_type | VARCHAR(50) | 属性分类 |

**预置属性键：**

| property_key | 说明 | 示例 |
|--------------|------|------|
| drive_type | 驱动形式 | 电动、气动、手动 |
| nominal_diameter | 公称直径 | DN50 |
| valve_position | 阀门位置 | 进口、出口 |
| design_pressure | 设计压力 | 1.6MPa |
| design_temperature | 设计温度 | -20°C~120°C |
| manufacturer | 厂家 | 某设备厂 |

### 2.6 material_code（物料编码表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| code | VARCHAR(18) | 18位编码（唯一） |
| name | VARCHAR(200) | 物料名称 |
| specification | VARCHAR(200) | 规格型号 |
| unit | VARCHAR(20) | 单位 |
| category | VARCHAR(2) | 大类编码 |
| mid_category | VARCHAR(2) | 中类编码 |
| sub_category | VARCHAR(2) | 小类编码 |
| spec | VARCHAR(2) | 规格编码 |
| supplier_code | VARCHAR(2) | 供应商编码 |
| year | VARCHAR(2) | 年份编码 |
| sequence | INTEGER | 流水号 |
| created_at | TIMESTAMP | 创建时间 |

### 2.7 category（分类表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| level | INTEGER | 1=大类, 2=中类, 3=小类 |
| parent_code | VARCHAR(18) | 父级编码 |
| code | VARCHAR(2) | 分类编码 |
| name | VARCHAR(100) | 分类名称 |
| description | VARCHAR(500) | 说明 |

### 2.8 rule_learning（规则学习库）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| raw_text | TEXT | 原始输入 |
| ai_result | JSONB | AI 解析结果 |
| rule_result | JSONB | 规则解析结果 |
| corrected_result | JSONB | 用户纠错结果 |
| source | VARCHAR(20) | ai / rule / user_correct |
| created_at | TIMESTAMP | 创建时间 |

### 2.9 document_log（文档处理日志）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| file_path | VARCHAR(500) | 文件路径 |
| process_type | VARCHAR(50) | ocr / parse |
| result | JSONB | 处理结果 |
| status | VARCHAR(20) | pending / success / failed |
| error_message | TEXT | 错误信息 |
| created_at | TIMESTAMP | 创建时间 |

---

## 3. 关系图

```
ledger ─────┬───── inbound (1:N, 带序号+累计)
            │
            ├───── outbound (1:N, 带序号+累计)
            │
            ├───── material_property (1:N, 仅 category=material)
            │
            ├───── equipment_property (1:N, 仅 category=equipment)
            │
            └───── material_code (N:1)
```

---

## 4. 序号与累计量计算规则

### 4.1 入库记录

```sql
-- 新插入库记录时
inbound_sequence = MAX(inbound_sequence FOR ledger_id) + 1
cumulative_in = MAX(cumulative_in FOR ledger_id) + quantity

-- 更新台账主表
UPDATE ledger SET current_stock = current_stock + quantity WHERE id = ledger_id
```

### 4.2 出库记录

```sql
-- 新插入库记录时
outbound_sequence = MAX(outbound_sequence FOR ledger_id) + 1
cumulative_out = MAX(cumulative_out FOR ledger_id) + quantity

-- 更新台账主表
UPDATE ledger SET current_stock = current_stock - quantity WHERE id = ledger_id
```

### 4.3 库存校验

- 出库时检查 `current_stock >= quantity`，否则拒绝
- 支持从入库/出库记录实时计算验证 `current_stock` 准确性

---

## 5. Excel 报表设计

### 5.1 Sheet 结构

```
台账报表_YYYY-MM-DD.xlsx
│
├── Sheet1: 材料看板          (Dashboard 查询界面)
├── Sheet2: 台账总览          (所有物料当前库存)
├── Sheet3: 入库记录          (所有入库历史)
├── Sheet4: 出库记录          (所有出库历史)
└── Sheet5: 物料编码          (可选)
```

### 5.2 材料看板（Sheet1）

**功能：**
- 材料搜索（下拉列表或输入）
- 选中物料后展示完整信息概览
- 支持多选添加物料到选中列表
- 展示选中物料的详细信息

**布局：**

```
┌─────────────────────────────────────────────────────────────────┐
│  [搜索材料 ▼] 或输入: [______________] [+ 添加]                   │
├─────────────────────────────────────────────────────────────────┤
│  已选中材料:                                                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ ☑ 钢筋 φ16 (2024-03-15)              [× 移除]         │    │
│  │ ☑ 水泥 PC32.5 (2024-03-10)            [× 移除]         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ═══════════════ 材料基本信息 ═══════════════                    │
│  名称: [________]  分类: [________]  单位: [________]          │
│  规格: [________]  物料编码: [________]  采购日期: [________]  │
│                                                                  │
│  ═══════════════ 物料属性 ═══════════════                        │
│  执行标准: [________]  材质: [________]  介质: [________]       │
│                                                                  │
│  ═══════════════ 库存情况 ═══════════════                        │
│  ┌────────┬────────┬────────┬────────┐                         │
│  │当前库存│最小库存 │计划采购│库存状态│                          │
│  │ 12.5吨 │  5吨   │  20吨  │ ✓正常 │                          │
│  └────────┴────────┴────────┴────────┘                         │
│                                                                  │
│  ═══════════════ 入库情况 ═══════════════                        │
│  累计入库: 50吨  第12次入库  最近: 2024-03-15 杭州建材 5吨     │
│  ┌──────┬────────┬────────┬────────┬────────┐                   │
│  │序号  │ 日期   │ 数量   │ 供应商 │ 操作人 │                   │
│  ├──────┼────────┼────────┼────────┼────────┤                   │
│  │第12次│ 03-15  │  5吨   │杭州建材│ 张三  │                   │
│  │第11次│ 03-10  │  8吨   │上海钢铁│ 李四  │                   │
│  └──────┴────────┴────────┴────────┴────────┘                   │
│                                                                  │
│  ═══════════════ 出库情况 ═══════════════                        │
│  累计出库: 37.5吨  第8次出库  最近: 2024-03-20 项目A 3吨        │
│  ┌──────┬────────┬────────┬────────┬────────┐                   │
│  │序号  │ 日期   │ 数量   │ 用途   │ 领用人 │                   │
│  ├──────┼────────┼────────┼────────┼────────┤                   │
│  │第8次 │ 03-20  │  3吨   │ 项目A  │ 王五  │                   │
│  │第7次 │ 03-18  │  5吨   │ 项目B  │ 赵六  │                   │
│  └──────┴────────┴────────┴────────┴────────┘                   │
│                                                                  │
│  [  刷新数据  ]  [  查询选中条目详情  ]  [  合并导出选中条目  ] │
└─────────────────────────────────────────────────────────────────┘
```

### 5.3 导出功能

**导出类型：**

| 导出选项 | 说明 |
|----------|------|
| 台账总览（选中条目） | 选中物料的基本信息 |
| 入库记录（选中条目） | 选中物料的所有入库历史 |
| 出库记录（选中条目） | 选中物料的所有出库历史 |
| 合并导出 | 包含以上所有Sheet |

**独立导出：**

| 导出选项 | 说明 |
|----------|------|
| 台账总览 | 所有物料的当前库存信息 |
| 入库记录 | 所有入库历史明细 |
| 出库记录 | 所有出库历史明细 |
| 物料编码 | 18位物料编码对照表 |
| 全部导出 | 包含以上所有Sheet |

**导出参数：**
- 日期范围（可选）
- 格式：Excel (.xlsx) / CSV (.csv)

### 5.4 多选合并导出结构

```
选中物料汇总_YYYY-MM-DD.xlsx
│
├── Sheet1: 选中物料概览      (所有选中物料的总览表)
├── Sheet2: 台账总览          (选中物料的当前库存)
├── Sheet3: 入库记录          (选中物料的入库历史)
└── Sheet4: 出库记录          (选中物料的出库历史)
```

---

## 6. 与现有设计的差异

| 项目 | 旧设计 | 新设计 |
|------|--------|--------|
| 材料属性 | 字段混用在 ledger 表 | 独立的 material_property / equipment_property 表 |
| 设备属性 | 字段混用在 ledger 表 | 独立的 equipment_property 表 |
| 入库序号 | 无 | inbound_sequence 字段 |
| 累计入库量 | 无 | cumulative_in 字段 |
| 出库序号 | 无 | outbound_sequence 字段 |
| 累计出库量 | 无 | cumulative_out 字段 |
| 采购日期 | 无 | purchase_date 字段 |
| 更新时间 | 无 | updated_at 字段 |
| Excel 看板 | 无 | 材料看板 Sheet |

---

## 7. 实施优先级

1. **Phase 1**: 修改数据库表结构（ledger, inbound, outbound, material_property, equipment_property）
2. **Phase 2**: 更新 Repository 层支持序号和累计量计算
3. **Phase 3**: 实现属性表的 CRUD 操作
4. **Phase 4**: Excel 导出功能增强
5. **Phase 5**: 材料看板界面开发
