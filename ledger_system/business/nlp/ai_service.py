"""MiniMax AI service for entity extraction and document understanding"""
import json
import re
import ast
from typing import Dict, Any, Optional
from pathlib import Path

import yaml
import requests


class AIService:
    """Service for calling MiniMax AI APIs"""

    def __init__(self):
        self.config = self._load_config()
        self.api_key = self.config["minimax"]["api_key"]
        self.api_host = self.config["minimax"].get("api_host", "api.minimaxi.com")
        self.model = "MiniMax-M2.7"

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

重要：请只返回原始JSON字符串，不要使用任何markdown格式标记，不要用```json包裹输出，直接返回JSON本身。"""

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
        """Call MiniMax text API - Claude Code compatible format"""
        url = f"https://{self.api_host}/anthropic/v1/messages"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "x-api-key": self.api_key,
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 4096
        }

        response = requests.post(url, headers=headers, json=payload, timeout=120)
        response.raise_for_status()

        result = response.json()
        # Extract content from the response - get the 'text' type content, not 'thinking'
        if "content" in result and len(result["content"]) > 0:
            for item in result["content"]:
                if item.get("type") == "text":
                    return item.get("text", "")
        return ""

    def _call_vision_api(self, image_path: str, prompt: str) -> str:
        """Call MiniMax vision API for image understanding"""
        url = f"https://{self.api_host}/v1/image understanding"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "x-api-key": self.api_key
        }

        with open(image_path, "rb") as f:
            files = {"file": f}
            data = {"prompt": prompt}
            response = requests.post(url, headers=headers, data=data, files=files, timeout=120)

        response.raise_for_status()
        result = response.json()
        return result.get("content", "")

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from AI response, stripping markdown code blocks with fallback"""
        if not response:
            return {}
        try:
            # Strip markdown code block wrappers (```json ... ``` or ``` ... ```)
            match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
            if match:
                json_str = match.group(1).strip()
            else:
                # Fallback: extract between first { and last }
                start = response.find("{")
                end = response.rfind("}") + 1
                if start != -1 and end != 0:
                    json_str = response[start:end]
                else:
                    json_str = response.strip()
            return json.loads(json_str)
        except json.JSONDecodeError:
            # Fallback: try ast.literal_eval for loose JSON
            try:
                return json.loads(json_str) if 'json_str' in dir() else ast.literal_eval(response.strip())
            except Exception:
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

重要：请只返回原始JSON字符串，不要使用任何markdown格式标记，不要用```json包裹输出，直接返回JSON本身。"""

        response = self._call_text_api(prompt)
        return self._parse_json_response(response)

    def analyze_procurement_row(self, row_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Analyze procurement row data and extract structured fields using AI.
        """
        # Format row data for AI analysis
        row_text = self._format_row_data(row_data)

        prompt = f"""你是一个建筑工地材料采购清单分析助手。请分析以下采购清单数据，提取每个维度的值。

数据行:
{row_text}

请根据数据内容，提取以下维度的值（只返回有值的维度）：

返回格式要求（严格返回JSON，不要有任何其他内容）：
{{
  "specification": "规格型号",
  "material_type": "材质",
  "standard": "执行标准",
  "thickness": "厚度",
  "connection_type": "连接方式",
  "pressure": "压力",
  "temperature": "温度",
  "medium": "介质",
  "drive_type": "驱动形式",
  "nominal_diameter": "公称直径",
  "brand": "品牌",
  "weight": "单个重量",
  "board": "板块",
  "item_type": "物资类型",
  "manufacturer": "厂家",
  "technical_params": "完整技术参数原文",
  "technical_requirements": "技术要求原文",
  "notes": "备注信息"
}}

重要规则：
1. 只返回JSON格式，不要用```包裹，不要有任何其他内容
2. 对于阀门'公称直径'列如包含"Q47F-10-DN150；304不锈钢；法兰"，则：specification=Q47F-10-DN150, material_type=304不锈钢, connection_type=法兰
3. 只返回有值的维度
4. 技术参数和技术要求要保留原文"""

        response = self._call_text_api(prompt)
        return self._parse_json_response(response)

    def _format_row_data(self, row_data: Dict[str, Any]) -> str:
        """Format row data as text for AI analysis"""
        lines = []
        for key, value in row_data.items():
            if value is not None and str(value).strip():
                val_str = str(value).replace('\n', ' ').replace('\r', ' ')
                if len(val_str) > 200:
                    val_str = val_str[:200] + "..."
                lines.append(f"  {key}: {val_str}")
        return '\n'.join(lines)