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