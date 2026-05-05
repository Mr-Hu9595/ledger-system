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
    # 需要添加台账目录，而不是ledger_system目录
    sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
    from ledger_system.business.nlp.ai_service import AIService

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

            # 图片文件 -> 使用MiniMax vision API (修复URL格式)
            if filename.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                import requests
                config_path = Path(__file__).parent.parent.parent.parent / "ledger_system" / "config" / "settings.yaml"
                import yaml
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                api_key = config["minimax"]["api_key"]
                api_host = config["minimax"].get("api_host", "api.minimaxi.com")

                # 正确的MiniMax图片理解API URL
                url = f"https://{api_host}/v1/image_understanding"
                b64_image = base64.b64encode(file_content).decode('utf-8')

                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "x-api-key": api_key
                }
                data = {
                    "prompt": "请描述这张图片中的所有文字内容和关键信息，包括：材料名称、规格、数量、单位、供应商、日期等建筑工地相关单据信息。"
                }
                files = {"file": (filename, io.BytesIO(file_content), f"image/{filename.split('.')[-1]}")}

                response = requests.post(url, headers=headers, data=data, files=files, timeout=120)
                if response.status_code != 200:
                    raise HTTPException(status_code=500, detail=f"MiniMax API error: {response.text}")
                resp_json = response.json()
                content = resp_json.get("content", "")
                if not content:
                    content = resp_json.get("text", str(resp_json))

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
                try:
                    import pdfplumber
                    with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                        content_parts = []
                        for page in pdf.pages:
                            text = page.extract_text()
                            if text:
                                content_parts.append(text)
                        content = '\n'.join(content_parts)
                except ImportError:
                    content = "PDF提取需要安装pdfplumber库，请使用图片或Word格式"
                except Exception as e:
                    content = f"PDF提取失败: {str(e)}，请使用图片或Word格式"

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