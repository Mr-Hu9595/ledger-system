# 仓库管理系统 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立完整的仓库管理系统桌面应用，实现物料搜索、入库/出库管理、Excel导入导出

**Architecture:** Electron 28 桌面应用 + React 18 前端 + Python FastAPI 后端 + PostgreSQL 数据库。前端使用 Ant Design Pro UI 组件库，后端复用现有数据库表结构（ledger, ledger_property, inbound, outbound）

**Tech Stack:** Electron 28, React 18, Vite 5, Ant Design Pro 6, FastAPI 0.110, SQLAlchemy 2, PostgreSQL

---

## 项目初始化

### Task 1: 创建项目基础结构

**Files:**
- Create: `warehouse-manager/package.json` - 根目录workspace配置
- Create: `warehouse-manager/electron/main.js` - Electron主进程
- Create: `warehouse-manager/electron/preload.js` - 预加载脚本
- Create: `warehouse-manager/electron/package.json`
- Create: `warehouse-manager/client/package.json` - React前端配置
- Create: `warehouse-manager/client/vite.config.js` - Vite配置
- Create: `warehouse-manager/server/main.py` - FastAPI入口
- Create: `warehouse-manager/server/database.py` - 数据库连接
- Create: `warehouse-manager/server/models/` - 数据模型目录
- Create: `warehouse-manager/server/schemas/` - Pydantic模型目录

- [ ] **Step 1: 创建项目根目录**

```bash
mkdir -p "D:/工作/日常工作/台账/warehouse-manager"
cd "D:/工作/日常工作/台账/warehouse-manager"
```

- [ ] **Step 2: 创建根目录 package.json**

```json
{
  "name": "warehouse-manager",
  "version": "1.0.0",
  "description": "仓库管理系统",
  "scripts": {
    "dev": "concurrently \"npm run server\" \"npm run client\"",
    "server": "cd server && uvicorn main:app --reload --port 8000",
    "client": "cd client && npm run dev",
    "electron": "cd electron && electron .",
    "build": "npm run build-client && npm run build-electron"
  },
  "devDependencies": {
    "concurrently": "^8.2.0"
  }
}
```

- [ ] **Step 3: 创建 Electron 主进程文件**

```javascript
// warehouse-manager/electron/main.js
const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let serverProcess;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

  // 开发模式加载 Vite 开发服务器
  mainWindow.loadURL('http://localhost:5173');
  // 生产模式加载打包后的文件
  // mainWindow.loadFile(path.join(__dirname, '../client/dist/index.html'));

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function startServer() {
  const isDev = process.env.NODE_ENV !== 'production';
  if (isDev) {
    serverProcess = spawn('python', ['-m', 'uvicorn', 'server.main:app', '--reload', '--port', '8000'], {
      cwd: path.join(__dirname, '../server'),
      shell: true
    });
    serverProcess.stdout.on('data', (data) => {
      console.log(`Server: ${data}`);
    });
  }
}

app.whenReady().then(() => {
  startServer();
  createWindow();
});

app.on('window-all-closed', () => {
  if (serverProcess) {
    serverProcess.kill();
  }
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
```

- [ ] **Step 4: 创建 Electron preload.js**

```javascript
// warehouse-manager/electron/preload.js
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  // 调用后端API
  callAPI: (endpoint, method, data) => {
    return fetch(`http://localhost:8000${endpoint}`, {
      method: method || 'GET',
      headers: { 'Content-Type': 'application/json' },
      body: data ? JSON.stringify(data) : undefined
    }).then(res => res.json());
  },

  // 打开文件对话框
  openFileDialog: () => ipcRenderer.invoke('dialog:openFile'),

  // 保存文件对话框
  saveFileDialog: () => ipcRenderer.invoke('dialog:saveFile')
});
```

- [ ] **Step 5: 创建 Electron package.json**

```json
{
  "name": "warehouse-manager-electron",
  "version": "1.0.0",
  "main": "main.js",
  "scripts": {
    "start": "electron ."
  },
  "devDependencies": {
    "electron": "^28.0.0"
  }
}
```

- [ ] **Step 6: 创建 client/package.json**

```json
{
  "name": "warehouse-manager-client",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.22.0",
    "antd": "^5.14.0",
    "@ant-design/icons": "^5.2.6",
    "@ant-design/pro-components": "^2.6.0",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.0",
    "vite": "^5.1.0"
  }
}
```

- [ ] **Step 7: 创建 client/vite.config.js**

```javascript
// warehouse-manager/client/vite.config.js
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  }
});
```

- [ ] **Step 8: 创建 server/main.py**

```python
# warehouse-manager/server/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from models import Material, Inbound, Outbound, LedgerProperty

app = FastAPI(title="仓库管理系统API", version="1.0.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 注册路由
from api import materials, inbounds, outbounds, tools
app.include_router(materials.router, prefix="/api/materials", tags=["物料"])
app.include_router(inbounds.router, prefix="/api/inbounds", tags=["入库"])
app.include_router(outbounds.router, prefix="/api/outbounds", tags=["出库"])
app.include_router(tools.router, prefix="/api", tags=["工具"])

@app.get("/api/health")
def health_check():
    return {"status": "ok", "message": "仓库管理系统API运行中"}
```

- [ ] **Step 9: 创建 server/database.py**

```python
# warehouse-manager/server/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/ledger_db"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 10: 创建 server/models/__init__.py**

```python
# warehouse-manager/server/models/__init__.py
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Integer, Date, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
from database import Base

class Material(Base):
    __tablename__ = "ledger"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    specification = Column(String(200))
    category = Column(String(50))
    unit = Column(String(20))
    current_stock = Column(Float, default=0)
    min_stock = Column(Float, default=0)
    material_code = Column(String(50))
    inbound_status = Column(String(20), default="待入库")
    planned_inbound_date = Column(Date)
    purchase_date = Column(Date)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    properties = relationship("LedgerProperty", back_populates="ledger", cascade="all, delete-orphan")
    inbounds = relationship("Inbound", back_populates="ledger", cascade="all, delete-orphan")
    outbounds = relationship("Outbound", back_populates="ledger", cascade="all, delete-orphan")

class LedgerProperty(Base):
    __tablename__ = "ledger_property"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ledger_id = Column(UUID(as_uuid=True), ForeignKey("ledger.id"), nullable=False)
    property_key = Column(String(50), nullable=False)
    property_value = Column(String(500), default="")
    property_category = Column(String(20), default="")

    ledger = relationship("Material", back_populates="properties")

class Inbound(Base):
    __tablename__ = "inbound"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ledger_id = Column(UUID(as_uuid=True), ForeignKey("ledger.id"), nullable=False)
    inbound_date = Column(Date, nullable=False)
    inbound_time = Column(DateTime, default=datetime.utcnow)
    quantity = Column(Float, nullable=False)
    supplier = Column(String(200))
    inbound_operator = Column(String(100))
    original_document_path = Column(String(500))
    document_source = Column(String(100))
    notes = Column(Text)

    ledger = relationship("Material", back_populates="inbounds")

class Outbound(Base):
    __tablename__ = "outbound"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ledger_id = Column(UUID(as_uuid=True), ForeignKey("ledger.id"), nullable=False)
    outbound_date = Column(Date, nullable=False)
    outbound_time = Column(DateTime, default=datetime.utcnow)
    quantity = Column(Float, nullable=False)
    usage = Column(String(200))
    receiver = Column(String(100))
    outbound_operator = Column(String(100))
    original_document_path = Column(String(500))
    notes = Column(Text)

    ledger = relationship("Material", back_populates="outbounds")
```

- [ ] **Step 11: 创建 server/schemas/__init__.py**

```python
# warehouse-manager/server/schemas/__init__.py
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID

class MaterialBase(BaseModel):
    name: str
    specification: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    current_stock: float = 0
    min_stock: float = 0
    material_code: Optional[str] = None
    inbound_status: str = "待入库"
    planned_inbound_date: Optional[date] = None
    purchase_date: Optional[date] = None
    notes: Optional[str] = None

class MaterialCreate(MaterialBase):
    pass

class MaterialUpdate(MaterialBase):
    pass

class MaterialResponse(MaterialBase):
    id: UUID
    properties: List[dict] = []

    class Config:
        from_attributes = True

class InboundBase(BaseModel):
    ledger_id: UUID
    inbound_date: date
    quantity: float
    supplier: Optional[str] = None
    inbound_operator: Optional[str] = None
    original_document_path: Optional[str] = None
    document_source: Optional[str] = None
    notes: Optional[str] = None

class InboundCreate(InboundBase):
    pass

class InboundResponse(InboundBase):
    id: UUID
    inbound_time: datetime

    class Config:
        from_attributes = True

class OutboundBase(BaseModel):
    ledger_id: UUID
    outbound_date: date
    quantity: float
    usage: Optional[str] = None
    receiver: Optional[str] = None
    outbound_operator: Optional[str] = None
    notes: Optional[str] = None

class OutboundCreate(OutboundBase):
    pass

class OutboundResponse(OutboundBase):
    id: UUID
    outbound_time: datetime

    class Config:
        from_attributes = True
```

- [ ] **Step 12: 创建 server/api/__init__.py**

```python
# warehouse-manager/server/api/__init__.py
```

- [ ] **Step 13: 提交初始项目结构**

```bash
git add warehouse-manager/
git commit -m "feat: initial warehouse-manager project structure"
```

---

## 后端API实现

### Task 2: 实现物料CRUD API

**Files:**
- Create: `warehouse-manager/server/api/materials.py`
- Modify: `warehouse-manager/server/main.py`

- [ ] **Step 1: 创建物料API路由**

```python
# warehouse-manager/server/api/materials.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List
from uuid import UUID
from datetime import date

from database import get_db
from models import Material, LedgerProperty
from schemas import MaterialCreate, MaterialUpdate, MaterialResponse

router = APIRouter()

@router.get("", response_model=List[MaterialResponse])
def get_materials(
    search: Optional[str] = None,
    category: Optional[str] = None,
    inbound_status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Material)

    if search:
        query = query.filter(
            or_(
                Material.name.ilike(f"%{search}%"),
                Material.specification.ilike(f"%{search}%"),
                Material.material_code.ilike(f"%{search}%")
            )
        )

    if category:
        query = query.filter(Material.category == category)

    if inbound_status:
        query = query.filter(Material.inbound_status == inbound_status)

    materials = query.offset(skip).limit(limit).all()

    result = []
    for m in materials:
        props = {p.property_key: p.property_value for p in m.properties}
        result.append({
            "id": m.id,
            "name": m.name,
            "specification": m.specification,
            "category": m.category,
            "unit": m.unit,
            "current_stock": m.current_stock,
            "min_stock": m.min_stock,
            "material_code": m.material_code,
            "inbound_status": m.inbound_status,
            "planned_inbound_date": m.planned_inbound_date,
            "purchase_date": m.purchase_date,
            "notes": m.notes,
            "properties": list(props.items())
        })

    return result

@router.get("/{material_id}", response_model=MaterialResponse)
def get_material(material_id: UUID, db: Session = Depends(get_db)):
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="物料不存在")

    props = {p.property_key: p.property_value for p in material.properties}

    return {
        "id": material.id,
        "name": material.name,
        "specification": material.specification,
        "category": material.category,
        "unit": material.unit,
        "current_stock": material.current_stock,
        "min_stock": material.min_stock,
        "material_code": material.material_code,
        "inbound_status": material.inbound_status,
        "planned_inbound_date": material.planned_inbound_date,
        "purchase_date": material.purchase_date,
        "notes": material.notes,
        "properties": list(props.items())
    }

@router.post("", response_model=MaterialResponse)
def create_material(material: MaterialCreate, db: Session = Depends(get_db)):
    db_material = Material(**material.model_dump())
    db.add(db_material)
    db.commit()
    db.refresh(db_material)
    return db_material

@router.put("/{material_id}", response_model=MaterialResponse)
def update_material(material_id: UUID, material: MaterialUpdate, db: Session = Depends(get_db)):
    db_material = db.query(Material).filter(Material.id == material_id).first()
    if not db_material:
        raise HTTPException(status_code=404, detail="物料不存在")

    for key, value in material.model_dump().items():
        setattr(db_material, key, value)

    db.commit()
    db.refresh(db_material)
    return db_material

@router.delete("/{material_id}")
def delete_material(material_id: UUID, db: Session = Depends(get_db)):
    db_material = db.query(Material).filter(Material.id == material_id).first()
    if not db_material:
        raise HTTPException(status_code=404, detail="物料不存在")

    db.delete(db_material)
    db.commit()
    return {"message": "删除成功"}
```

- [ ] **Step 2: 更新 server/main.py 引入物料路由**

```python
# 在 main.py 中添加路由导入（已在Task1中完成）
# 确保这行存在：
from api import materials, inbounds, outbounds, tools
```

- [ ] **Step 3: 测试API**

```bash
cd "D:/工作/日常工作/台账/warehouse-manager/server"
python -c "from main import app; print('API加载成功')"
```

- [ ] **Step 4: 提交**

```bash
git add warehouse-manager/server/api/materials.py
git commit -m "feat: add materials CRUD API"
```

---

### Task 3: 实现入库CRUD API

**Files:**
- Create: `warehouse-manager/server/api/inbounds.py`

- [ ] **Step 1: 创建入库API路由**

```python
# warehouse-manager/server/api/inbounds.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import date

from database import get_db
from models import Inbound, Material
from schemas import InboundCreate, InboundResponse

router = APIRouter()

@router.get("", response_model=List[InboundResponse])
def get_inbounds(
    ledger_id: UUID = None,
    start_date: date = None,
    end_date: date = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Inbound)

    if ledger_id:
        query = query.filter(Inbound.ledger_id == ledger_id)

    if start_date:
        query = query.filter(Inbound.inbound_date >= start_date)

    if end_date:
        query = query.filter(Inbound.inbound_date <= end_date)

    return query.offset(skip).limit(limit).all()

@router.post("", response_model=InboundResponse)
def create_inbound(inbound: InboundCreate, db: Session = Depends(get_db)):
    # 检查物料是否存在
    material = db.query(Material).filter(Material.id == inbound.ledger_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="物料不存在")

    # 创建入库记录
    db_inbound = Inbound(**inbound.model_dump())
    db.add(db_inbound)

    # 更新库存
    material.current_stock += inbound.quantity

    # 更新入库状态为已入库
    material.inbound_status = "已入库"

    db.commit()
    db.refresh(db_inbound)
    return db_inbound

@router.get("/{inbound_id}", response_model=InboundResponse)
def get_inbound(inbound_id: UUID, db: Session = Depends(get_db)):
    inbound = db.query(Inbound).filter(Inbound.id == inbound_id).first()
    if not inbound:
        raise HTTPException(status_code=404, detail="入库记录不存在")
    return inbound
```

- [ ] **Step 2: 提交**

```bash
git add warehouse-manager/server/api/inbounds.py
git commit -m "feat: add inbound CRUD API"
```

---

### Task 4: 实现出库CRUD API

**Files:**
- Create: `warehouse-manager/server/api/outbounds.py`

- [ ] **Step 1: 创建出库API路由**

```python
# warehouse-manager/server/api/outbounds.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from datetime import date

from database import get_db
from models import Outbound, Material
from schemas import OutboundCreate, OutboundResponse

router = APIRouter()

@router.get("", response_model=List[OutboundResponse])
def get_outbounds(
    ledger_id: UUID = None,
    start_date: date = None,
    end_date: date = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(Outbound)

    if ledger_id:
        query = query.filter(Outbound.ledger_id == ledger_id)

    if start_date:
        query = query.filter(Outbound.outbound_date >= start_date)

    if end_date:
        query = query.filter(Outbound.outbound_date <= end_date)

    return query.offset(skip).limit(limit).all()

@router.post("", response_model=OutboundResponse)
def create_outbound(outbound: OutboundCreate, db: Session = Depends(get_db)):
    # 检查物料是否存在
    material = db.query(Material).filter(Material.id == outbound.ledger_id).first()
    if not material:
        raise HTTPException(status_code=404, detail="物料不存在")

    # 检查库存是否足够
    if material.current_stock < outbound.quantity:
        raise HTTPException(status_code=400, detail=f"库存不足，当前库存{material.current_stock}")

    # 创建出库记录
    db_outbound = Outbound(**outbound.model_dump())
    db.add(db_outbound)

    # 更新库存
    material.current_stock -= outbound.quantity

    db.commit()
    db.refresh(db_outbound)
    return db_outbound

@router.get("/{outbound_id}", response_model=OutboundResponse)
def get_outbound(outbound_id: UUID, db: Session = Depends(get_db)):
    outbound = db.query(Outbound).filter(Outbound.id == outbound_id).first()
    if not outbound:
        raise HTTPException(status_code=404, detail="出库记录不存在")
    return outbound
```

- [ ] **Step 2: 提交**

```bash
git add warehouse-manager/server/api/outbounds.py
git commit -m "feat: add outbound CRUD API"
```

---

### Task 5: 实现工具API（导入/导出/同步）

**Files:**
- Create: `warehouse-manager/server/api/tools.py`

- [ ] **Step 1: 创建工具API路由**

```python
# warehouse-manager/server/api/tools.py
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import pandas as pd
from io import BytesIO
from datetime import datetime

from database import get_db
from models import Material, LedgerProperty

router = APIRouter()

@router.post("/import/excel")
async def import_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="只支持Excel文件")

    contents = await file.read()
    df = pd.read_excel(BytesIO(contents))

    imported = 0
    for _, row in df.iterrows():
        name = row.get('名称') or row.get('name')
        if not name:
            continue

        # 检查是否已存在
        existing = db.query(Material).filter(Material.name == name).first()
        if existing:
            continue

        # 创建新物料
        material = Material(
            name=name,
            specification=row.get('规格') or row.get('specification'),
            category=row.get('类别') or row.get('category', 'material'),
            unit=row.get('单位') or row.get('unit', '个'),
            current_stock=float(row.get('当前库存') or row.get('current_stock', 0)),
            min_stock=float(row.get('最小库存') or row.get('min_stock', 0)),
            inbound_status=row.get('入库状态') or row.get('inbound_status', '待入库'),
            material_code=row.get('物料编码') or row.get('material_code')
        )
        db.add(material)
        imported += 1

    db.commit()
    return {"message": f"成功导入{imported}条物料", "total": imported}

@router.get("/export/materials")
def export_materials(db: Session = Depends(get_db)):
    materials = db.query(Material).all()

    data = []
    for m in materials:
        props = {p.property_key: p.property_value for p in m.properties}
        data.append({
            "名称": m.name,
            "规格": m.specification,
            "类别": m.category,
            "单位": m.unit,
            "当前库存": m.current_stock,
            "最小库存": m.min_stock,
            "物料编码": m.material_code,
            "入库状态": m.inbound_status,
            "品牌": props.get("brand", ""),
            "材质": props.get("material_type", ""),
            "技术参数": props.get("technical_params", "")
        })

    df = pd.DataFrame(data)
    output = BytesIO()
    df.to_excel(output, index=False, sheet_name="物料清单")
    output.seek(0)

    return FileResponse(
        BytesIO(output.read()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"物料清单_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    )

@router.get("/export/inbounds")
def export_inbounds(db: Session = Depends(get_db)):
    from models import Inbound

    inbounds = db.query(Inbound).all()

    data = []
    for ib in inbounds:
        data.append({
            "日期": ib.inbound_date,
            "物料名称": ib.ledger.name if ib.ledger else "",
            "规格": ib.ledger.specification if ib.ledger else "",
            "数量": ib.quantity,
            "单位": ib.ledger.unit if ib.ledger else "",
            "供应商": ib.supplier,
            "入库人": ib.inbound_operator,
            "备注": ib.notes
        })

    df = pd.DataFrame(data)
    output = BytesIO()
    df.to_excel(output, index=False, sheet_name="入库记录")
    output.seek(0)

    return FileResponse(
        BytesIO(output.read()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"入库记录_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    )

@router.post("/sync/report")
def sync_report(db: Session = Depends(get_db)):
    from models import Inbound, Outbound

    materials = db.query(Material).all()
    inbounds = db.query(Inbound).all()
    outbounds = db.query(Outbound).all()

    return {
        "materials_count": len(materials),
        "inbounds_count": len(inbounds),
        "outbounds_count": len(outbounds),
        "last_sync": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
```

- [ ] **Step 2: 提交**

```bash
git add warehouse-manager/server/api/tools.py
git commit -m "feat: add import/export/sync tools API"
```

---

## 前端实现

### Task 6: 创建React前端基础布局

**Files:**
- Create: `warehouse-manager/client/index.html`
- Create: `warehouse-manager/client/src/main.jsx`
- Create: `warehouse-manager/client/src/App.jsx`
- Create: `warehouse-manager/client/src/router.jsx`
- Create: `warehouse-manager/client/src/services/api.js`
- Create: `warehouse-manager/client/src/components/Layout/index.jsx`

- [ ] **Step 1: 创建 index.html**

```html
<!-- warehouse-manager/client/index.html -->
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>仓库管理系统</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
```

- [ ] **Step 2: 创建 src/main.jsx**

```javascript
// warehouse-manager/client/src/main.jsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

- [ ] **Step 3: 创建 src/index.css**

```css
/* warehouse-manager/client/src/index.css */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
}

#root {
  min-height: 100vh;
}
```

- [ ] **Step 4: 创建 src/services/api.js**

```javascript
// warehouse-manager/client/src/services/api.js
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// 物料API
export const materialAPI = {
  getList: (params) => api.get('/materials', { params }),
  getById: (id) => api.get(`/materials/${id}`),
  create: (data) => api.post('/materials', data),
  update: (id, data) => api.put(`/materials/${id}`, data),
  delete: (id) => api.delete(`/materials/${id}`)
};

// 入库API
export const inboundAPI = {
  getList: (params) => api.get('/inbounds', { params }),
  create: (data) => api.post('/inbounds', data),
  getById: (id) => api.get(`/inbounds/${id}`)
};

// 出库API
export const outboundAPI = {
  getList: (params) => api.get('/outbounds', { params }),
  create: (data) => api.post('/outbounds', data),
  getById: (id) => api.get(`/outbounds/${id}`)
};

// 工具API
export const toolsAPI = {
  importExcel: (file) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/import/excel', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
  },
  exportMaterials: () => api.get('/export/materials', { responseType: 'blob' }),
  exportInbounds: () => api.get('/export/inbounds', { responseType: 'blob' }),
  syncReport: () => api.post('/sync/report')
};

export default api;
```

- [ ] **Step 5: 创建 src/router.jsx**

```javascript
// warehouse-manager/client/src/router.jsx
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import MaterialList from './pages/MaterialList';
import MaterialCreate from './pages/MaterialCreate';
import InboundList from './pages/InboundList';
import OutboundList from './pages/OutboundList';
import Tools from './pages/Tools';

const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      { index: true, element: <Dashboard /> },
      { path: 'materials', element: <MaterialList /> },
      { path: 'materials/create', element: <MaterialCreate /> },
      { path: 'inbounds', element: <InboundList /> },
      { path: 'outbounds', element: <OutboundList /> },
      { path: 'tools', element: <Tools /> }
    ]
  }
]);

export default router;
```

- [ ] **Step 6: 创建 src/App.jsx**

```javascript
// warehouse-manager/client/src/App.jsx
import { RouterProvider } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import router from './router';

const App = () => (
  <ConfigProvider locale={zhCN}>
    <RouterProvider router={router} />
  </ConfigProvider>
);

export default App;
```

- [ ] **Step 7: 创建 src/components/Layout/index.jsx**

```javascript
// warehouse-manager/client/src/components/Layout/index.jsx
import { Layout, Menu } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  HomeOutlined,
  InboxOutlined,
  UploadOutlined,
  FileTextOutlined,
  ToolOutlined
} from '@ant-design/icons';

const { Header, Sider, Content } = Layout;

const LayoutComponent = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    { key: '/', icon: <HomeOutlined />, label: '首页' },
    {
      key: 'materials',
      icon: <InboxOutlined />,
      label: '物料管理',
      children: [
        { key: '/materials', label: '物料列表' },
        { key: '/materials/create', label: '手动录入' }
      ]
    },
    {
      key: 'inbounds',
      icon: <UploadOutlined />,
      label: '入库管理',
      children: [
        { key: '/inbounds', label: '入库记录' }
      ]
    },
    {
      key: 'outbounds',
      icon: <FileTextOutlined />,
      label: '出库管理',
      children: [
        { key: '/outbounds', label: '出库记录' }
      ]
    },
    {
      key: 'tools',
      icon: <ToolOutlined />,
      label: '工具',
      children: [
        { key: '/tools', label: '导出/同步' }
      ]
    }
  ];

  const onMenuClick = ({ key }) => {
    navigate(key);
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#001529', padding: '0 24px', display: 'flex', alignItems: 'center' }}>
        <div style={{ color: '#fff', fontSize: 20, fontWeight: 'bold' }}>仓库管理系统</div>
      </Header>
      <Layout>
        <Sider width={200} style={{ background: '#fff' }}>
          <Menu
            mode="inline"
            selectedKeys={[location.pathname]}
            defaultOpenKeys={['materials', 'inbounds', 'outbounds', 'tools']}
            items={menuItems}
            onClick={onMenuClick}
            style={{ height: '100%', borderRight: 0 }}
          />
        </Sider>
        <Layout style={{ padding: '0 24px 24px' }}>
          <Content style={{ margin: '16px 0', minHeight: 280 }}>
            {children}
          </Content>
        </Layout>
      </Layout>
    </Layout>
  );
};

export default LayoutComponent;
```

- [ ] **Step 8: 提交**

```bash
git add warehouse-manager/client/
git commit -m "feat: add React frontend basic layout and routing"
```

---

### Task 7: 实现首页看板页面

**Files:**
- Create: `warehouse-manager/client/src/pages/Dashboard/index.jsx`

- [ ] **Step 1: 创建首页看板页面**

```javascript
// warehouse-manager/client/src/pages/Dashboard/index.jsx
import { useState, useEffect } from 'react';
import { Card, Row, Col, Table, Tag, Typography } from 'antd';
import { materialAPI, inboundAPI } from '../../services/api';

const { Title } = Typography;

const Dashboard = () => {
  const [stats, setStats] = useState({
    total: 0,
    pending: 0,
    stored: 0,
    lowStock: 0
  });
  const [recentInbounds, setRecentInbounds] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      // 获取所有物料
      const materialsRes = await materialAPI.getList({ limit: 1000 });
      const materials = materialsRes.data;

      // 计算统计数据
      setStats({
        total: materials.length,
        pending: materials.filter(m => m.inbound_status === '待入库').length,
        stored: materials.filter(m => m.inbound_status === '已入库').length,
        lowStock: materials.filter(m => m.current_stock < m.min_stock).length
      });

      // 获取最近入库记录
      const inboundsRes = await inboundAPI.getList({ limit: 5 });
      setRecentInbounds(inboundsRes.data);
    } catch (error) {
      console.error('获取数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    { title: '日期', dataIndex: 'inbound_date', key: 'inbound_date' },
    { title: '物料名称', dataIndex: 'ledger_name', key: 'ledger_name', render: (text, record) => record.ledger?.name || '-' },
    { title: '数量', dataIndex: 'quantity', key: 'quantity' },
    { title: '供应商', dataIndex: 'supplier', key: 'supplier' }
  ];

  return (
    <div>
      <Title level={3}>首页看板</Title>

      {/* 统计卡片 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card title="待入库" loading={loading}>
            <div style={{ fontSize: 32, textAlign: 'center', color: '#faad14' }}>{stats.pending}</div>
          </Card>
        </Col>
        <Col span={6}>
          <Card title="已入库" loading={loading}>
            <div style={{ fontSize: 32, textAlign: 'center', color: '#52c41a' }}>{stats.stored}</div>
          </Card>
        </Col>
        <Col span={6}>
          <Card title="库存不足" loading={loading}>
            <div style={{ fontSize: 32, textAlign: 'center', color: '#ff4d4f' }}>{stats.lowStock}</div>
          </Card>
        </Col>
        <Col span={6}>
          <Card title="全部物料" loading={loading}>
            <div style={{ fontSize: 32, textAlign: 'center', color: '#1890ff' }}>{stats.total}</div>
          </Card>
        </Col>
      </Row>

      {/* 最近入库记录 */}
      <Card title="最近入库记录" loading={loading}>
        <Table
          columns={columns}
          dataSource={recentInbounds}
          rowKey="id"
          pagination={false}
        />
      </Card>
    </div>
  );
};

export default Dashboard;
```

- [ ] **Step 2: 提交**

```bash
git add warehouse-manager/client/src/pages/Dashboard/
git commit -m "feat: add dashboard page with statistics cards"
```

---

### Task 8: 实现物料列表页面

**Files:**
- Create: `warehouse-manager/client/src/pages/MaterialList/index.jsx`

- [ ] **Step 1: 创建物料列表页面**

```javascript
// warehouse-manager/client/src/pages/MaterialList/index.jsx
import { useState, useEffect } from 'react';
import { Table, Input, Select, Button, Space, Modal, Descriptions, Tag } from 'antd';
import { SearchOutlined, PlusOutlined, EyeOutlined, UploadOutlined } from '@ant-design/icons';
import { materialAPI, inboundAPI } from '../../services/api';
import { useNavigate } from 'react-router-dom';

const { Search } = Input;
const { Option } = Select;

const MaterialList = () => {
  const [materials, setMaterials] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [categoryFilter, setCategoryFilter] = useState(null);
  const [statusFilter, setStatusFilter] = useState(null);
  const [selectedMaterial, setSelectedMaterial] = useState(null);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [inboundModalVisible, setInboundModalVisible] = useState(false);
  const [inboundQuantity, setInboundQuantity] = useState(0);
  const navigate = useNavigate();

  useEffect(() => {
    fetchMaterials();
  }, [searchText, categoryFilter, statusFilter]);

  const fetchMaterials = async () => {
    setLoading(true);
    try {
      const params = { limit: 500 };
      if (searchText) params.search = searchText;
      if (categoryFilter) params.category = categoryFilter;
      if (statusFilter) params.inbound_status = statusFilter;

      const res = await materialAPI.getList(params);
      setMaterials(res.data);
    } catch (error) {
      console.error('获取物料失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (value) => {
    setSearchText(value);
  };

  const handleCategoryChange = (value) => {
    setCategoryFilter(value);
  };

  const handleStatusChange = (value) => {
    setStatusFilter(value);
  };

  const showDetail = (record) => {
    setSelectedMaterial(record);
    setDetailModalVisible(true);
  };

  const handleInbound = async () => {
    if (!selectedMaterial || inboundQuantity <= 0) return;

    try {
      await inboundAPI.create({
        ledger_id: selectedMaterial.id,
        inbound_date: new Date().toISOString().split('T')[0],
        quantity: inboundQuantity,
        inbound_operator: '系统管理员'
      });
      setInboundModalVisible(false);
      setInboundQuantity(0);
      fetchMaterials();
    } catch (error) {
      console.error('入库失败:', error);
    }
  };

  const columns = [
    { title: '名称', dataIndex: 'name', key: 'name', fixed: 'left', width: 150 },
    { title: '规格', dataIndex: 'specification', key: 'specification', width: 150 },
    { title: '类别', dataIndex: 'category', key: 'category', width: 100 },
    { title: '单位', dataIndex: 'unit', key: 'unit', width: 80 },
    { title: '当前库存', dataIndex: 'current_stock', key: 'current_stock', width: 100 },
    {
      title: '入库状态',
      dataIndex: 'inbound_status',
      key: 'inbound_status',
      width: 100,
      render: (status) => (
        <Tag color={status === '已入库' ? 'green' : 'orange'}>{status}</Tag>
      )
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right',
      render: (_, record) => (
        <Space>
          <Button size="small" icon={<EyeOutlined />} onClick={() => showDetail(record)}>详情</Button>
          <Button size="small" type="primary" icon={<UploadOutlined />} onClick={() => { setSelectedMaterial(record); setInboundModalVisible(true); }}>入库</Button>
        </Space>
      )
    }
  ];

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Search placeholder="搜索物料名称/规格/编码" onSearch={handleSearch} style={{ width: 300 }} allowClear />
        <Select placeholder="选择类别" onChange={handleCategoryChange} allowClear style={{ width: 150 }}>
          <Option value="equipment">设备</Option>
          <Option value="material">材料</Option>
          <Option value="监测仪表">监测仪表</Option>
        </Select>
        <Select placeholder="入库状态" onChange={handleStatusChange} allowClear style={{ width: 120 }}>
          <Option value="待入库">待入库</Option>
          <Option value="已入库">已入库</Option>
        </Select>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/materials/create')}>手动录入</Button>
      </Space>

      <Table
        columns={columns}
        dataSource={materials}
        rowKey="id"
        loading={loading}
        scroll={{ x: 1200 }}
        pagination={{ pageSize: 10, showSizeChanger: true, showTotal: (total) => `共 ${total} 条` }}
      />

      {/* 详情弹窗 */}
      <Modal
        title="物料详情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>关闭</Button>,
          <Button key="inbound" type="primary" onClick={() => { setDetailModalVisible(false); setInboundModalVisible(true); }}>入库</Button>
        ]}
      >
        {selectedMaterial && (
          <Descriptions bordered column={2}>
            <Descriptions.Item label="名称">{selectedMaterial.name}</Descriptions.Item>
            <Descriptions.Item label="规格">{selectedMaterial.specification}</Descriptions.Item>
            <Descriptions.Item label="类别">{selectedMaterial.category}</Descriptions.Item>
            <Descriptions.Item label="单位">{selectedMaterial.unit}</Descriptions.Item>
            <Descriptions.Item label="当前库存">{selectedMaterial.current_stock}</Descriptions.Item>
            <Descriptions.Item label="最小库存">{selectedMaterial.min_stock}</Descriptions.Item>
            <Descriptions.Item label="物料编码">{selectedMaterial.material_code}</Descriptions.Item>
            <Descriptions.Item label="入库状态">{selectedMaterial.inbound_status}</Descriptions.Item>
            <Descriptions.Item label="品牌" span={2}>{selectedMaterial.properties?.find(p => p[0] === 'brand')?.[1] || '-'}</Descriptions.Item>
            <Descriptions.Item label="材质" span={2}>{selectedMaterial.properties?.find(p => p[0] === 'material_type')?.[1] || '-'}</Descriptions.Item>
            <Descriptions.Item label="技术参数" span={2}>{selectedMaterial.properties?.find(p => p[0] === 'technical_params')?.[1] || '-'}</Descriptions.Item>
          </Descriptions>
        )}
      </Modal>

      {/* 入库弹窗 */}
      <Modal
        title="入库"
        open={inboundModalVisible}
        onCancel={() => setInboundModalVisible(false)}
        onOk={handleInbound}
      >
        <p>物料: {selectedMaterial?.name}</p>
        <p>当前库存: {selectedMaterial?.current_stock}</p>
        <p>
          入库数量:
          <input
            type="number"
            value={inboundQuantity}
            onChange={(e) => setInboundQuantity(parseFloat(e.target.value) || 0)}
            style={{ marginLeft: 8, width: 100 }}
          />
        </p>
      </Modal>
    </div>
  );
};

export default MaterialList;
```

- [ ] **Step 2: 提交**

```bash
git add warehouse-manager/client/src/pages/MaterialList/
git commit -m "feat: add material list page with search and filter"
```

---

### Task 9: 实现物料录入页面

**Files:**
- Create: `warehouse-manager/client/src/pages/MaterialCreate/index.jsx`

- [ ] **Step 1: 创建物料录入页面**

```javascript
// warehouse-manager/client/src/pages/MaterialCreate/index.jsx
import { useState } from 'react';
import { Form, Input, Select, InputNumber, Button, Card, message } from 'antd';
import { materialAPI } from '../../services/api';
import { useNavigate } from 'react-router-dom';

const { TextArea } = Input;
const { Option } = Select;

const MaterialCreate = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const onFinish = async (values) => {
    setLoading(true);
    try {
      await materialAPI.create({
        ...values,
        inbound_status: '待入库',
        current_stock: 0
      });
      message.success('物料创建成功');
      navigate('/materials');
    } catch (error) {
      message.error('创建失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card title="手动录入物料">
      <Form form={form} layout="vertical" onFinish={onFinish}>
        <Form.Item label="名称" name="name" rules={[{ required: true, message: '请输入名称' }]}>
          <Input placeholder="请输入物料名称" />
        </Form.Item>

        <Form.Item label="规格" name="specification">
          <Input placeholder="请输入规格" />
        </Form.Item>

        <Form.Item label="类别" name="category">
          <Select placeholder="请选择类别">
            <Option value="equipment">设备</Option>
            <Option value="material">材料</Option>
            <Option value="监测仪表">监测仪表</Option>
            <Option value="视频监控">视频监控</Option>
            <Option value="雾炮设备">雾炮设备</Option>
            <Option value="洗车机设备">洗车机设备</Option>
          </Select>
        </Form.Item>

        <Form.Item label="单位" name="unit">
          <Select placeholder="请选择单位">
            <Option value="个">个</Option>
            <Option value="套">套</Option>
            <Option value="米">米</Option>
            <Option value="吨">吨</Option>
            <Option value="项">项</Option>
            <Option value="批">批</Option>
          </Select>
        </Form.Item>

        <Form.Item label="品牌" name="brand">
          <Input placeholder="请输入品牌" />
        </Form.Item>

        <Form.Item label="最小库存" name="min_stock">
          <InputNumber min={0} style={{ width: '100%' }} placeholder="请输入最小库存" />
        </Form.Item>

        <Form.Item label="物料编码" name="material_code">
          <Input placeholder="请输入物料编码" />
        </Form.Item>

        <Form.Item label="备注" name="notes">
          <TextArea rows={3} placeholder="请输入备注" />
        </Form.Item>

        <Form.Item>
          <Button type="primary" htmlType="submit" loading={loading}>提交</Button>
          <Button style={{ marginLeft: 8 }} onClick={() => navigate('/materials')}>取消</Button>
        </Form.Item>
      </Form>
    </Card>
  );
};

export default MaterialCreate;
```

- [ ] **Step 2: 提交**

```bash
git add warehouse-manager/client/src/pages/MaterialCreate/
git commit -m "feat: add material create page"
```

---

### Task 10: 实现入库记录页面

**Files:**
- Create: `warehouse-manager/client/src/pages/InboundList/index.jsx`

- [ ] **Step 1: 创建入库记录页面**

```javascript
// warehouse-manager/client/src/pages/InboundList/index.jsx
import { useState, useEffect } from 'react';
import { Table, Card, Tag, Typography } from 'antd';
import { inboundAPI } from '../../services/api';

const { Title } = Typography;

const InboundList = () => {
  const [inbounds, setInbounds] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchInbounds();
  }, []);

  const fetchInbounds = async () => {
    setLoading(true);
    try {
      const res = await inboundAPI.getList({ limit: 500 });
      setInbounds(res.data);
    } catch (error) {
      console.error('获取入库记录失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    { title: '日期', dataIndex: 'inbound_date', key: 'inbound_date', width: 120 },
    { title: '时间', dataIndex: 'inbound_time', key: 'inbound_time', width: 150, render: (text) => text ? text.substring(0, 19) : '-' },
    { title: '物料名称', dataIndex: 'ledger_name', key: 'ledger_name', render: (_, record) => record.ledger?.name || '-' },
    { title: '规格', dataIndex: 'specification', render: (_, record) => record.ledger?.specification || '-' },
    { title: '数量', dataIndex: 'quantity', key: 'quantity', width: 100 },
    { title: '单位', dataIndex: 'unit', render: (_, record) => record.ledger?.unit || '-' },
    { title: '供应商', dataIndex: 'supplier', key: 'supplier', width: 150 },
    { title: '入库人', dataIndex: 'inbound_operator', key: 'inbound_operator', width: 100 },
    { title: '备注', dataIndex: 'notes', key: 'notes' }
  ];

  return (
    <div>
      <Title level={3}>入库记录</Title>
      <Card>
        <Table
          columns={columns}
          dataSource={inbounds}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10, showTotal: (total) => `共 ${total} 条` }}
        />
      </Card>
    </div>
  );
};

export default InboundList;
```

- [ ] **Step 2: 提交**

```bash
git add warehouse-manager/client/src/pages/InboundList/
git commit -m "feat: add inbound list page"
```

---

### Task 11: 实现出库记录页面

**Files:**
- Create: `warehouse-manager/client/src/pages/OutboundList/index.jsx`

- [ ] **Step 1: 创建出库记录页面**

```javascript
// warehouse-manager/client/src/pages/OutboundList/index.jsx
import { useState, useEffect } from 'react';
import { Table, Card, Typography } from 'antd';
import { outboundAPI } from '../../services/api';

const { Title } = Typography;

const OutboundList = () => {
  const [outbounds, setOutbounds] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchOutbounds();
  }, []);

  const fetchOutbounds = async () => {
    setLoading(true);
    try {
      const res = await outboundAPI.getList({ limit: 500 });
      setOutbounds(res.data);
    } catch (error) {
      console.error('获取出库记录失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const columns = [
    { title: '日期', dataIndex: 'outbound_date', key: 'outbound_date', width: 120 },
    { title: '时间', dataIndex: 'outbound_time', key: 'outbound_time', width: 150, render: (text) => text ? text.substring(0, 19) : '-' },
    { title: '物料名称', dataIndex: 'ledger_name', key: 'ledger_name', render: (_, record) => record.ledger?.name || '-' },
    { title: '规格', dataIndex: 'specification', render: (_, record) => record.ledger?.specification || '-' },
    { title: '数量', dataIndex: 'quantity', key: 'quantity', width: 100 },
    { title: '单位', dataIndex: 'unit', render: (_, record) => record.ledger?.unit || '-' },
    { title: '用途', dataIndex: 'usage', key: 'usage' },
    { title: '领料人', dataIndex: 'receiver', key: 'receiver', width: 100 },
    { title: '出库人', dataIndex: 'outbound_operator', key: 'outbound_operator', width: 100 }
  ];

  return (
    <div>
      <Title level={3}>出库记录</Title>
      <Card>
        <Table
          columns={columns}
          dataSource={outbounds}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10, showTotal: (total) => `共 ${total} 条` }}
        />
      </Card>
    </div>
  );
};

export default OutboundList;
```

- [ ] **Step 2: 提交**

```bash
git add warehouse-manager/client/src/pages/OutboundList/
git commit -m "feat: add outbound list page"
```

---

### Task 12: 实现工具页面（导入/导出/同步）

**Files:**
- Create: `warehouse-manager/client/src/pages/Tools/index.jsx`

- [ ] **Step 1: 创建工具页面**

```javascript
// warehouse-manager/client/src/pages/Tools/index.jsx
import { useState } from 'react';
import { Card, Button, Upload, message, Table, Typography, Space } from 'antd';
import { DownloadOutlined, UploadOutlined, SyncOutlined, FileExcelOutlined } from '@ant-design/icons';
import { toolsAPI } from '../../services/api';

const { Title } = Typography;

const Tools = () => {
  const [loading, setLoading] = useState(false);
  const [syncResult, setSyncResult] = useState(null);

  const handleImport = async (file) => {
    setLoading(true);
    try {
      const res = await toolsAPI.importExcel(file);
      message.success(res.data.message);
    } catch (error) {
      message.error('导入失败');
    } finally {
      setLoading(false);
    }
    return false; // 阻止默认上传
  };

  const handleExportMaterials = async () => {
    setLoading(true);
    try {
      const res = await toolsAPI.exportMaterials();
      const blob = new Blob([res.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `物料清单_${new Date().toISOString().split('T')[0]}.xlsx`;
      a.click();
      window.URL.revokeObjectURL(url);
      message.success('导出成功');
    } catch (error) {
      message.error('导出失败');
    } finally {
      setLoading(false);
    }
  };

  const handleExportInbounds = async () => {
    setLoading(true);
    try {
      const res = await toolsAPI.exportInbounds();
      const blob = new Blob([res.data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `入库记录_${new Date().toISOString().split('T')[0]}.xlsx`;
      a.click();
      window.URL.revokeObjectURL(url);
      message.success('导出成功');
    } catch (error) {
      message.error('导出失败');
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    setLoading(true);
    try {
      const res = await toolsAPI.syncReport();
      setSyncResult(res.data);
      message.success('同步成功');
    } catch (error) {
      message.error('同步失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <Title level={3}>工具</Title>

      <Space direction="vertical" style={{ width: '100%' }} size="large">
        <Card title="数据导入">
          <Upload beforeUpload={handleImport} showUploadList={false}>
            <Button type="primary" icon={<UploadOutlined />} loading={loading}>
              导入Excel
            </Button>
          </Upload>
        </Card>

        <Card title="数据导出">
          <Space>
            <Button icon={<DownloadOutlined />} onClick={handleExportMaterials} loading={loading}>
              导出物料清单
            </Button>
            <Button icon={<DownloadOutlined />} onClick={handleExportInbounds} loading={loading}>
              导出入库记录
            </Button>
          </Space>
        </Card>

        <Card title="报表同步">
          <Button type="primary" icon={<SyncOutlined />} onClick={handleSync} loading={loading}>
            同步报表
          </Button>
          {syncResult && (
            <div style={{ marginTop: 16 }}>
              <p>物料总数: {syncResult.materials_count}</p>
              <p>入库记录: {syncResult.inbounds_count}</p>
              <p>出库记录: {syncResult.outbounds_count}</p>
              <p>最后同步: {syncResult.last_sync}</p>
            </div>
          )}
        </Card>
      </Space>
    </div>
  );
};

export default Tools;
```

- [ ] **Step 2: 提交**

```bash
git add warehouse-manager/client/src/pages/Tools/
git commit -m "feat: add tools page with import/export/sync"
```

---

## 打包与测试

### Task 13: 打包Electron应用

**Files:**
- Modify: `warehouse-manager/electron/package.json`
- Modify: `warehouse-manager/package.json`

- [ ] **Step 1: 更新 package.json 添加打包脚本**

```json
{
  "scripts": {
    "dev": "concurrently \"npm run server\" \"npm run client\"",
    "server": "cd server && uvicorn main:app --reload --port 8000",
    "client": "cd client && npm run dev",
    "build": "npm run build-client && npm run build-electron",
    "build-client": "cd client && npm run build",
    "build-electron": "cd electron && electron-builder --win",
    "electron": "electron ."
  },
  "devDependencies": {
    "concurrently": "^8.2.0",
    "electron-builder": "^24.9.0"
  },
  "build": {
    "appId": "com.warehouse.manager",
    "productName": "仓库管理系统",
    "directories": {
      "output": "dist"
    },
    "win": {
      "target": "nsis",
      "icon": "icon.ico"
    },
    "nsis": {
      "oneClick": false,
      "allowToChangeInstallationDirectory": true
    }
  }
}
```

- [ ] **Step 2: 提交**

```bash
git add warehouse-manager/package.json
git commit -m "feat: add electron-builder configuration"
```

---

**Plan complete and saved to `docs/superpowers/plans/2026-05-03-warehouse-manager-plan.md`**

**Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**