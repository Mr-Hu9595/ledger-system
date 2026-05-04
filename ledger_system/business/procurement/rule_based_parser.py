"""Rule-based parser for procurement list analysis - 不调用AI"""
import re
from typing import Dict, Optional
from decimal import Decimal


class RuleBasedParser:
    """Rule-based parser for extracting structured fields from procurement data"""

    @staticmethod
    def parse_nominal_diameter(value: str) -> Optional[str]:
        """从公称直径列提取DN部分"""
        if not value:
            return None
        # 匹配 DN20, DN150 等
        match = re.search(r'(DN\d+)', value, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def parse_specification(row_data: Dict) -> str:
        """从各列提取规格"""
        # 阀门：从公称直径列提取 Q47F-10-DN150 部分
        if '公称直径' in row_data and row_data['公称直径']:
            val = str(row_data['公称直径'])
            # 提取第一个分号前的部分作为规格
            if '；' in val:
                return val.split('；')[0].strip()
            elif ';' in val:
                return val.split(';')[0].strip()

        # 材料：从规格型号列
        if '规格型号' in row_data and row_data['规格型号']:
            return str(row_data['规格型号']).strip()

        # 标准件
        if '标准、规格、材质' in row_data and row_data['标准、规格、材质']:
            return str(row_data['标准、规格、材质']).strip()

        return ""

    @staticmethod
    def parse_material_type(row_data: Dict) -> str:
        """从各列提取材质"""
        # 阀体材质
        if '阀体材质' in row_data and row_data['阀体材质']:
            return str(row_data['阀体材质']).strip()

        # 公称直径列中分号后的内容
        if '公称直径' in row_data and row_data['公称直径']:
            val = str(row_data['公称直径'])
            if '；' in val:
                parts = val.split('；')
                if len(parts) > 1:
                    return parts[1].strip()
            elif ';' in val:
                parts = val.split(';')
                if len(parts) > 1:
                    return parts[1].strip()

        # 材质列
        if '材质' in row_data and row_data['材质']:
            return str(row_data['材质']).strip()

        return ""

    @staticmethod
    def parse_connection_type(row_data: Dict) -> str:
        """从各列提取连接方式"""
        # 阀门位置
        if '阀门位置' in row_data and row_data['阀门位置']:
            return str(row_data['阀门位置']).strip()

        # 公称直径列中分号后的内容（第三部分可能是连接方式）
        if '公称直径' in row_data and row_data['公称直径']:
            val = str(row_data['公称直径'])
            if '；' in val:
                parts = val.split('；')
                if len(parts) > 2:
                    return parts[2].strip()
            elif ';' in val:
                parts = val.split(';')
                if len(parts) > 2:
                    return parts[2].strip()

        # 备注中的法兰连接
        if '备注' in row_data and row_data['备注']:
            if '法兰' in str(row_data['备注']):
                return '法兰连接'

        return ""

    @staticmethod
    def parse_pressure(value: str) -> Optional[str]:
        """从设计压力列提取压力值"""
        if not value:
            return None
        # PN1.6, 1.0-1.6MPa 等
        match = re.search(r'PN?\d+\.?\d*', str(value), re.IGNORECASE)
        if match:
            return match.group(0).upper()
        return str(value).strip()

    @staticmethod
    def parse_temperature(value) -> Optional[str]:
        """从设计温度列提取温度值"""
        if not value:
            return None
        return f"{value}°C"

    @staticmethod
    def parse_thickness(spec: str) -> Optional[str]:
        """从规格中提取厚度"""
        if not spec:
            return None
        # δ10, >=2.0mm, 2.0mm 等
        match = re.search(r'(>=?\d+\.?\d*mm|δ\d+)', spec, re.IGNORECASE)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def parse_standard(row_data: Dict) -> Optional[str]:
        """从技术要求列提取执行标准"""
        # 技术要求列
        if '技术要求' in row_data and row_data['技术要求']:
            val = str(row_data['技术要求'])
            # GB/T 709-2006 等
            match = re.search(r'GB[/T]?\d+[-]?\d*', val)
            if match:
                return match.group(0)
            if '国标' in val:
                return '国标'
        return None

    @staticmethod
    def parse_row(row_data: Dict) -> Dict[str, str]:
        """解析一行数据，返回所有提取的字段"""
        result = {}

        # 规格
        spec = RuleBasedParser.parse_specification(row_data)
        if spec:
            result['specification'] = spec

        # 材质
        material = RuleBasedParser.parse_material_type(row_data)
        if material:
            result['material_type'] = material

        # 连接方式
        connection = RuleBasedParser.parse_connection_type(row_data)
        if connection:
            result['connection_type'] = connection

        # 公称直径
        if '公称直径' in row_data and row_data['公称直径']:
            nd = RuleBasedParser.parse_nominal_diameter(str(row_data['公称直径']))
            if nd:
                result['nominal_diameter'] = nd

        # 压力
        if '设计压力MPa' in row_data and row_data['设计压力MPa']:
            pressure = RuleBasedParser.parse_pressure(str(row_data['设计压力MPa']))
            if pressure:
                result['design_pressure'] = pressure

        # 温度
        if '设计温度°C' in row_data and row_data['设计温度°C']:
            temp = RuleBasedParser.parse_temperature(row_data['设计温度°C'])
            if temp:
                result['design_temperature'] = temp

        # 驱动形式
        if '驱动形式' in row_data and row_data['驱动形式']:
            result['drive_type'] = str(row_data['驱动形式']).strip()

        # 介质
        if '介质' in row_data and row_data['介质']:
            result['medium'] = str(row_data['介质']).strip()

        # 品牌
        if '品牌' in row_data and row_data['品牌']:
            result['brand'] = str(row_data['品牌']).strip()

        # 板块
        if '板块' in row_data and row_data['板块']:
            result['board'] = str(row_data['板块']).strip()

        # 物资类型
        if '物资类型' in row_data and row_data['物资类型']:
            result['item_type'] = str(row_data['物资类型']).strip()

        # 重量
        if '重量Kg' in row_data and row_data['重量Kg']:
            try:
                weight = float(row_data['重量Kg'])
                result['weight'] = str(weight)
            except:
                pass

        # 技术参数
        if '技术参数' in row_data and row_data['技术参数']:
            result['technical_params'] = str(row_data['技术参数']).strip()

        # 技术要求
        if '技术要求' in row_data and row_data['技术要求']:
            result['technical_requirements'] = str(row_data['技术要求']).strip()

        # 备注
        if '备注' in row_data and row_data['备注']:
            result['notes'] = str(row_data['备注']).strip()

        return result