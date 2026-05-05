from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
from pathlib import Path
import base64
import io
import tempfile
import os

router = APIRouter()

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.docx', '.xlsx', '.xls', '.pdf'}

@router.post("/recognize")
async def recognize(
    mode: str = Form(...),  # inbound | outbound | material
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None)
):
    """AI识别接口，支持文本、图片、文档"""

    # 导入AIService (从ledger_system复用)
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "ledger_system"))
    from business.nlp.ai_service import AIService

    ai_service = AIService()

    try:
        content = ""

        # 1. 文本输入
        if text:
            content = text

        # 2. 文件输入
        elif file:
            filename = file.filename.lower()
            if not any(filename.endswith(ext) for ext in ALLOWED_EXTENSIONS):
                raise HTTPException(status_code=400, detail="不支持的文件类型")

            file_content = await file.read()

            # 图片文件 -> 保存临时文件 -> vision API
            if filename.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                # 保存为临时文件供understand_image使用
                with tempfile.NamedTemporaryFile(delete=False, suffix=filename) as tmp:
                    tmp.write(file_content)
                    tmp_path = tmp.name
                try:
                    content = ai_service.understand_image(tmp_path)
                finally:
                    os.unlink(tmp_path)

            # Word/Excel/PDF -> 提取文本
            elif filename.endswith('.docx'):
                from docx import Document
                doc = Document(io.BytesIO(file_content))
                content = '\n'.join([p.text for p in doc.paragraphs])

            elif filename.endswith(('.xlsx', '.xls')):
                import openpyxl
                wb = openpyxl.load_workbook(io.BytesIO(file_content))
                sheets = wb.sheetnames
                content_parts = []
                for sheet_name in sheets:
                    sheet = wb[sheet_name]
                    for row in sheet.iter_rows(values_only=True):
                        row_text = ' '.join([str(c) if c else '' for c in row])
                        if row_text.strip():
                            content_parts.append(row_text)
                content = '\n'.join(content_parts)

            elif filename.endswith('.pdf'):
                # 简单PDF文本提取
                content = "PDF内容提取需要额外库支持，请使用图片或Word格式"

        else:
            raise HTTPException(status_code=400, detail="请提供text或file参数")

        # 3. 根据mode调用不同解析方法
        if mode == "material":
            result = ai_service.parse_document_content(content, "物料信息")
        elif mode == "inbound":
            result = ai_service.extract_entities(content)
        elif mode == "outbound":
            result = ai_service.extract_entities(content)
        else:
            raise HTTPException(status_code=400, detail="无效的mode参数")

        return {"success": True, "data": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))