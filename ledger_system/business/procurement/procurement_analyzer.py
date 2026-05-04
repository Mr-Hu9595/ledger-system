"""AI semantic analyzer for procurement list analysis - 优化版"""
import json
from typing import Dict, List, Optional
from pathlib import Path
import yaml
import requests
import re


class ProcurementAnalyzer:
    """AI analyzer for procurement list data"""

    def __init__(self):
        self.config = self._load_config()
        self.api_key = self.config["minimax"]["api_key"]
        self.api_host = self.config["minimax"]["api_host"]
        self.model = self.config["minimax"].get("model", "MiniMax-Text-01")

    def _load_config(self) -> dict:
        config_path = Path(__file__).parent.parent.parent / "config" / "settings.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def analyze_row(self, row_data: Dict[str, any]) -> Dict[str, str]:
        """
        Analyze a single row of procurement data and extract structured fields.
        """
        # Format row data for AI analysis
        row_text = self._format_row_data(row_data)

        prompt = f"""你是一个建筑工地材料采购清单分析助手。请分析以下采购清单数据，提取每个维度的值。

数据行:
{row_text}

请根据数据内容，提取以下维度的值：

返回格式要求（严格返回JSON，不要有任何其他内容）：
{{
  "specification": "规格型号 - 来自所有包含规格信息的列。例如：球阀从'公称直径'列提取Q47F-10-DN150；从'规格型号'列提取具体规格。格式如：DN20, Q47F-10-DN150, φ168*4.5等",
  "material_type": "材质 - 来自'材质'、'阀体材质'、'公称直径'中分号后的内容等。例如：304不锈钢, 热镀锌, Q235-A.F",
  "standard": "执行标准 - 来自'技术要求'、'标准/规格/材质'等列。例如：国标, GB/T 709-2006",
  "thickness": "厚度 - 来自'规格型号'、'技术参数'等列。例如：>=2.0mm, δ10",
  "connection_type": "连接方式 - 来自'阀门位置'、'公称直径'中分号后的内容。例如：法兰连接, 焊接",
  "pressure": "压力 - 来自'设计压力MPa'列。例如：PN1.6, 1.0-1.6MPa",
  "temperature": "温度 - 来自'设计温度°C'列。例如：60°C",
  "medium": "介质 - 来自'介质'列。例如：水, 精苯",
  "drive_type": "驱动形式 - 来自'驱动形式'列。例如：手动, 电动",
  "nominal_diameter": "公称直径 - 来自'公称直径'列，提取其中的DN部分。例如：DN150, DN100",
  "brand": "品牌 - 来自'品牌'列。例如：海康, 国优",
  "weight": "单个重量 - 来自'重量Kg'列。例如：94.2Kg",
  "board": "板块 - 来自'板块'列。例如：管控中心设备, 治理设施工艺材料",
  "item_type": "物资类型 - 来自'物资类型'列。例如：网络材料类, 监测仪表设备",
  "manufacturer": "厂家 - 来自技术参数中的厂家信息",
  "technical_params": "完整技术参数原文",
  "technical_requirements": "技术要求原文（如有）",
  "notes": "备注信息"
}}

重要规则：
1. 只返回JSON格式，不要用```包裹，不要有任何其他内容
2. 对于阀门：如果'公称直径'列包含"Q47F-10-DN150；304不锈钢；法兰"，则：
   - specification = Q47F-10-DN150
   - material_type = 304不锈钢
   - connection_type = 法兰
3. 只返回有值的维度，不要返回null或空值
4. 技术参数和技术要求要保留原文"""

        result = self._call_text_api(prompt)
        return self._parse_response(result)

    def _format_row_data(self, row_data: Dict[str, any]) -> str:
        """Format row data as text for AI analysis"""
        lines = []
        for key, value in row_data.items():
            if value is not None and str(value).strip():
                val_str = str(value).replace('\n', ' ').replace('\r', ' ')
                if len(val_str) > 200:
                    val_str = val_str[:200] + "..."
                lines.append(f"  {key}: {val_str}")
        return '\n'.join(lines)

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

    def _parse_response(self, response: str) -> Dict[str, str]:
        """Parse JSON from AI response"""
        if not response:
            return {}

        try:
            match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response)
            if match:
                json_str = match.group(1).strip()
            else:
                start = response.find("{")
                end = response.rfind("}") + 1
                if start != -1 and end != 0:
                    json_str = response[start:end]
                else:
                    json_str = response.strip()

            return json.loads(json_str)
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}, response: {response[:200]}")
            return {}