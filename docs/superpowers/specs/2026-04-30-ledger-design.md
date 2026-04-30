# 工地材料设备进出库台账管理系统 - 设计文档

**日期**: 2026-04-30
**版本**: v1.0

---

## 1. 系统概述

### 1.1 目标
构建一个命令行驱动的自动化台账管理系统，支持：
- 自然语言录入（AI 理解+规则兜底）
- 文档/单据 OCR 解析（Excel/Word/PDF/图片）
- 自动生成台账记录
- 库存查询与使用记录查看
- 报表导出（Excel）

### 1.2 技术选型

| 组件 | 技术 |
|------|------|
| AI 主引擎 | MiniMax API (`understand_image` + NLP) |
| AI 兜底 | 本地规则引擎（正则+关键词匹配） |
| 图片 OCR | MiniMax `understand_image` |
| 数据库 | PostgreSQL |
| 导出格式 | Excel (pandas + openpyxl) |
| 文件监控 | watchdog |
| 程序语言 | Python 3.9+ |

### 1.3 用户规模
- 单人使用，无需权限系统

---

## 2. 三层架构

```
┌─────────────────────────────────────────────────────────┐
│                    程序层 (Program)                      │
│              CLI 入口 / 命令解析 / 展示                   │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                    业务层 (Business)                     │
│         AI服务 / 规则引擎 / 学习引擎 / 文档处理            │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│                    数据层 (Data)                         │
│              PostgreSQL / 规则库 / 文件存储                │
└─────────────────────────────────────────────────────────┘
```

### 2.1 程序层 (program/)
- `cli.py` - CLI 入口
- `commands/` - 命令实现（add, query, process, export）
- `display/` - 结果格式化展示

### 2.2 业务层 (business/)
- `nlp/ai_service.py` - MiniMax API 调用
- `nlp/rule_engine.py` - 本地规则兜底
- `learning/feedback.py` - 用户反馈学习
- `learning/diff_logger.py` - AI vs 规则差异记录
- `document/ocr.py` - 图片/文档 OCR
- `document/parser.py` - 结构化解析
- `document/watcher.py` - 文件夹监控

### 2.3 数据层 (data/)
- `models/` - SQLAlchemy 数据模型
- `repository/` - 数据仓储
- `database.py` - PostgreSQL 连接

---

## 3. 数据模型

### 3.1 ledger (台账主表)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| category | VARCHAR(20) | material / equipment |
| name | VARCHAR(200) | 名称 |
| specification | VARCHAR(200) | 规格 |
| unit | VARCHAR(20) | 单位 |
| current_stock | DECIMAL | 当前库存 |
| min_stock | DECIMAL | 最小库存 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### 3.2 inbound (入库记录)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| ledger_id | UUID | 外键 |
| quantity | DECIMAL | 数量 |
| supplier | VARCHAR(200) | 供应商 |
| inbound_date | DATE | 入库日期 |
| document_source | VARCHAR(500) | 单据来源 |
| operator | VARCHAR(100) | 操作人 |
| notes | TEXT | 备注 |
| created_at | TIMESTAMP | 创建时间 |

### 3.3 outbound (使用记录)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| ledger_id | UUID | 外键 |
| quantity | DECIMAL | 数量 |
| usage | VARCHAR(200) | 使用去向 |
| outbound_date | DATE | 使用日期 |
| applicant | VARCHAR(100) | 申请人 |
| approver | VARCHAR(100) | 审批人 |
| notes | TEXT | 备注 |
| created_at | TIMESTAMP | 创建时间 |

### 3.4 rule_learning (规则学习库)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| raw_text | TEXT | 原始输入 |
| ai_result | JSONB | AI 解析结果 |
| rule_result | JSONB | 规则解析结果 |
| corrected_result | JSONB | 用户纠错结果 |
| source | VARCHAR(20) | ai / rule / user_correct |
| created_at | TIMESTAMP | 时间 |

### 3.5 document_log (文档处理记录)
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| file_path | VARCHAR(500) | 文件路径 |
| process_type | VARCHAR(50) | ocr / parse |
| result | JSONB | 处理结果 |
| status | VARCHAR(20) | success / failed |
| error_message | TEXT | 错误信息 |
| created_at | TIMESTAMP | 处理时间 |

---

## 4. 命令设计

### 4.1 基础命令
```
# 自然语言录入
ledger add "今天进了3吨钢筋 from 杭州建材"

# 查询库存
ledger status [--material <name>] [--all]

# 查看记录
ledger history --material <name> --days <N>

# 手动触发文档处理
ledger process --file <path>

# 导出报表
ledger export --type <inventory|inbound|outbound> --format xlsx --output <path>

# 查看帮助
ledger help
```

### 4.2 文件监控模式
- 后台进程监控指定文件夹
- 检测到新文件自动触发处理流程

---

## 5. 工作流程

### 5.1 自然语言录入
```
用户输入 → CLI解析 → MiniMax API 提取实体
                           ↓
                    规则引擎兜底确认
                           ↓
                    学习引擎记录 (AI+规则结果)
                           ↓
                    写入 inbound 表
                           ↓
                    更新 ledger.current_stock
                           ↓
                    返回结果
```

### 5.2 文档处理
```
文件进入监控目录 OR 手动触发
        ↓
文件类型判断 (PDF/Word/Excel/图片)
        ↓
图片 → MiniMax understand_image
PDF/Word/Excel → 解析文本
        ↓
MiniMax API 结构化提取
        ↓
规则兜底 + 学习
        ↓
写入数据库
        ↓
生成台账条目
```

---

## 6. 规则学习机制

### 6.1 反馈学习
- 用户纠错时记录到 `rule_learning`
- 下次相同/相似输入时应用新规则

### 6.2 差异日志
- AI 与规则结果不一致时记录
- 定期分析改进规则

---

## 7. 配置管理

所有配置通过 `config/settings.yaml` 管理：
- MiniMax API Key
- 数据库连接
- 监控文件夹路径
- 规则库路径

---

## 8. 目录结构

```
ledger_system/
├── program/              # 程序层
│   ├── __init__.py
│   ├── cli.py
│   └── commands/
│       ├── add.py
│       ├── query.py
│       ├── process.py
│       └── export.py
│
├── business/             # 业务层
│   ├── __init__.py
│   ├── nlp/
│   │   ├── ai_service.py
│   │   └── rule_engine.py
│   ├── learning/
│   │   ├── feedback.py
│   │   └── diff_logger.py
│   └── document/
│       ├── ocr.py
│       ├── parser.py
│       └── watcher.py
│
├── data/                 # 数据层
│   ├── __init__.py
│   ├── models/
│   │   ├── ledger.py
│   │   ├── inbound.py
│   │   ├── outbound.py
│   │   ├── rule_learning.py
│   │   └── document_log.py
│   ├── repository/
│   │   └── ledger_repo.py
│   └── database.py
│
├── config/
│   └── settings.yaml
│
├── rules/
│   └── local_rules.json
│
├── docs/
│   └── specs/
│       └── 2026-04-30-ledger-design.md
│
└── main.py
```

---

## 9. 实施计划 (待细化)

1. 项目初始化 + 数据库模型
2. 程序层 CLI 框架
3. 业务层 AI 服务 + 规则引擎
4. 数据层 Repository 实现
5. 文档处理模块
6. 学习引擎
7. 集成测试
8. 文档完善