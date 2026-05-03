"""各Sheet的解析器 - 将Excel行数据转换为Ledger记录格式"""
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Tuple


class SheetParser:
    """基础解析器"""

    @staticmethod
    def excel_date_to_date(excel_date):
        """Excel日期数字转为date对象"""
        if excel_date is None:
            return None
        if isinstance(excel_date, (int, float)):
            try:
                return (datetime(1899, 12, 30) + timedelta(days=int(excel_date))).date()
            except:
                return None
        if isinstance(excel_date, datetime):
            return excel_date.date()
        return None

    @staticmethod
    def detect_category(name: str, item_type: str, sheet_name: str) -> str:
        """判断是设备还是材料"""
        name_lower = (name or "").lower()
        item_type_lower = (item_type or "").lower()

        # 阀门一定是设备
        if any(kw in name_lower for kw in ['球阀', '闸阀', '截止阀', '止回阀', '蝶阀']):
            return "equipment"

        # 设备关键词
        equipment_kw = ['服务器', '主机', '仪表', '传感器', '流量计', '冷干机', '塔架', '控制柜', '摄像头', '交换机']
        if any(kw in name_lower for kw in equipment_kw):
            return "equipment"

        # 默认材料
        return "material"


class Sheet01Parser(SheetParser):
    """01设备采购清单汇总表解析器 (42行)"""

    @staticmethod
    def parse_row(row: Tuple) -> Dict:
        """row: (序号, 板块, 物资名称, 物资类型, 数量, 单位, 技术参数, 品牌, 采购单下发时间, 是否已到货, 到货时间, 备注)"""
        seq, board, name, item_type, qty, unit, tech_params, brand, purchase_date, arrived, arrived_date, notes = row

        return {
            "name": name,
            "category": SheetParser.detect_category(name, item_type, "01设备采购清单汇总表"),
            "specification": "",
            "unit": unit or "",
            "quantity": qty,
            "inbound_status": "待入库",
            "planned_inbound_date": SheetParser.excel_date_to_date(purchase_date),
            "properties": {
                "board": board,
                "item_type": item_type,
                "technical_params": tech_params,
                "brand": brand,
                "purchase_date": str(purchase_date) if purchase_date else None,
            }
        }


class Sheet01_01Parser(SheetParser):
    """01-01流量计安装材料采购清单解析器 (22行)"""

    @staticmethod
    def parse_row(row: Tuple) -> Dict:
        """row: (序号, 材料名称, 规格型号, 材质, 技术要求, 数量, 单位, 重量Kg, 备注, 采购单下发时间, 是否已到货, 到货时间, 备注2)"""
        seq, name, spec, material, tech_req, qty, unit, weight, notes, purchase_date, arrived, arrived_date, notes2 = row

        return {
            "name": name,
            "category": "material",
            "specification": spec or "",
            "unit": unit or "",
            "quantity": qty,
            "inbound_status": "待入库",
            "planned_inbound_date": SheetParser.excel_date_to_date(purchase_date),
            "properties": {
                "material_type": material,
                "technical_params": tech_req,
                "weight": str(weight) if weight else None,
                "notes": notes or notes2 or "",
            }
        }


class Sheet02Parser(SheetParser):
    """02材料采购清单汇总表解析器 (66行)"""

    @staticmethod
    def parse_row(row: Tuple) -> Dict:
        """row: (序号, 板块, 物资名称, 物资类型, 数量, 单位, 技术参数, 品牌, 采购单下发时间, 是否已到货, 到货时间, 备注)"""
        seq, board, name, item_type, qty, unit, tech_params, brand, purchase_date, arrived, arrived_date, notes = row

        return {
            "name": name,
            "category": SheetParser.detect_category(name, item_type, "02材料采购清单汇总表"),
            "specification": "",
            "unit": unit or "",
            "quantity": qty,
            "inbound_status": "待入库",
            "planned_inbound_date": SheetParser.excel_date_to_date(purchase_date),
            "properties": {
                "board": board,
                "item_type": item_type,
                "technical_params": tech_params,
                "brand": brand,
                "purchase_date": str(purchase_date) if purchase_date else None,
            }
        }


class Sheet02_01Parser(SheetParser):
    """02-01雾炮塔架材料清单解析器 (17行)"""

    @staticmethod
    def parse_row(row: Tuple) -> Dict:
        """row: (序号, 材料名称, 规格型号, 材质, 技术要求, 数量, 单位, 重量Kg, 备注, 采购单下发时间, 是否已到货, 到货时间, 备注2, ...)"""
        seq, name, spec, material, tech_req, qty, unit, weight, notes, purchase_date, arrived, arrived_date, notes2 = row[:13]

        return {
            "name": name,
            "category": "material",
            "specification": spec or "",
            "unit": unit or "",
            "quantity": qty,
            "inbound_status": "待入库",
            "planned_inbound_date": SheetParser.excel_date_to_date(purchase_date),
            "properties": {
                "material_type": material,
                "technical_params": tech_req,
                "weight": str(weight) if weight else None,
                "notes": notes or notes2 or "",
            }
        }


class Sheet02_02Parser(SheetParser):
    """02-02阀门采购清单解析器 (11行) - 设备专属字段"""

    @staticmethod
    def parse_row(row: Tuple) -> Dict:
        """row: (序号, 名称, 驱动形式, 公称直径, 介质, 设计压力MPa, 设计温度°C, 阀门位置, 数量, 单位, 阀体材质, 备注, 采购单下发时间, 是否已到货, 到货时间, 备注2)"""
        seq, name, drive_type, nom_dia, medium, design_pressure, design_temp, valve_pos, qty, unit, material_type, notes, purchase_date, arrived, arrived_date, notes2 = row

        return {
            "name": name,
            "category": "equipment",
            "specification": f"{nom_dia}; {material_type}" if nom_dia and material_type else (nom_dia or material_type or ""),
            "unit": unit or "",
            "quantity": qty,
            "inbound_status": "待入库",
            "planned_inbound_date": SheetParser.excel_date_to_date(purchase_date),
            "properties": {
                "drive_type": drive_type,
                "nominal_diameter": nom_dia,
                "medium": medium,
                "design_pressure": design_pressure,
                "design_temperature": str(design_temp) if design_temp else None,
                "valve_position": valve_pos,
                "material_type": material_type,
                "notes": notes or notes2 or "",
            }
        }


class Sheet02_03Parser(SheetParser):
    """02-03标准件采购清单解析器 (46行)"""

    @staticmethod
    def parse_row(row: Tuple) -> Dict:
        """row: (序号, 名称, 标准/规格/材质, 要求, 数量, 单位, 备注, 采购单下发时间, 是否已到货, 到货时间, 备注2, ...)"""
        seq, name, spec_material, requirement, qty, unit, notes, purchase_date, arrived, arrived_date, notes2 = row[:11]

        return {
            "name": name,
            "category": "material",
            "specification": spec_material or "",
            "unit": unit or "",
            "quantity": qty,
            "inbound_status": "待入库",
            "planned_inbound_date": SheetParser.excel_date_to_date(purchase_date),
            "properties": {
                "technical_params": requirement,
                "notes": notes or notes2 or "",
            }
        }


class Sheet03Parser(SheetParser):
    """03电气材料采购清单解析器 (48行)"""

    @staticmethod
    def parse_row(row: Tuple) -> Dict:
        """row: (序号, 物资名称, 物资类型, 数量, 单位, 技术参数, 品牌, 采购单下发时间, 是否已到货, 到货时间, 备注)"""
        seq, name, item_type, qty, unit, tech_params, brand, purchase_date, arrived, arrived_date, notes = row

        return {
            "name": name,
            "category": SheetParser.detect_category(name, item_type, "03电气材料采购清单"),
            "specification": "",
            "unit": unit or "",
            "quantity": qty,
            "inbound_status": "待入库",
            "planned_inbound_date": SheetParser.excel_date_to_date(purchase_date),
            "properties": {
                "item_type": item_type,
                "technical_params": tech_params,
                "brand": brand,
                "notes": notes or "",
            }
        }


# 解析器映射
SHEET_PARSERS = {
    "01设备采购清单汇总表": Sheet01Parser,
    "01-01流量计安装材料采购清单": Sheet01_01Parser,
    "02材料采购清单汇总表": Sheet02Parser,
    "02-01雾炮塔架材料清单": Sheet02_01Parser,
    "02-02阀门采购清单": Sheet02_02Parser,
    "02-03标准件采购清单": Sheet02_03Parser,
    "03电气材料采购清单": Sheet03Parser,
}