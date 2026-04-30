"""MiniMax AI service for entity extraction and document understanding"""
import json
from typing import Dict, Any, Optional
from pathlib import Path

import yaml
import requests


class AIService:
    """Service for calling MiniMax AI APIs"""

    def __init__(self):
        self.config = self._load_config()
        self.api_key = self.config["minimax"]["api_key"]
        self.api_host = self.config["minimax"]["api_host"]
        self.model = self.config["minimax"].get("model", "MiniMax-Text-01")

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

只返回JSON，不要有其他内容。"""

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
        """Call MiniMax text API"""
        url = f"https://{self.api_host}/v1/text/chatcompletion_v2"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        result = response.json()
        return result["choices"][0]["messages"][0]["text"]

    def _call_vision_api(self, image_path: str, prompt: str) -> str:
        """Call MiniMax vision API for image understanding"""
        url = f"https://{self.api_host}/v1/image understanding"

        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }

        with open(image_path, "rb") as f:
            files = {"file": f}
            data = {"prompt": prompt}
            response = requests.post(url, headers=headers, data=data, files=files, timeout=120)

        response.raise_for_status()
        result = response.json()
        return result.get("content", "")

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from AI response"""
        try:
            # Try to extract JSON from response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start != -1 and end != 0:
                return json.loads(response[start:end])
            return {}
        except json.JSONDecodeError:
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

只返回JSON。"""

        response = self._call_text_api(prompt)
        return self._parse_json_response(response)