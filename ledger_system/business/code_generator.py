"""Code generator for material coding system"""
from datetime import datetime
from typing import Optional, Tuple

from sqlalchemy.orm import Session
from ledger_system.data.models.material_code import MaterialCode
from ledger_system.data.models.category import Category


class CodeGenerator:
    """物料编码生成器 - 18位编码"""

    # 大类编码表
    CATEGORIES = {
        "01": "钢材类",
        "02": "水泥类",
        "03": "混凝土类",
        "04": "电缆类",
        "05": "管材类",
        "06": "木材类",
        "07": "电气类",
        "08": "设备类",
        "09": "五金类",
        "10": "防护类",
        "11": "油漆涂料类",
        "12": "保温防水类",
        "99": "其他"
    }

    # 中类编码表（按大类分组）
    MID_CATEGORIES = {
        "01": {  # 钢材类
            "01": "盘圆钢筋",
            "02": "螺纹钢筋",
            "03": "工字钢",
            "04": "槽钢",
            "05": "角钢",
            "06": "钢板",
            "07": "钢管",
            "08": "钢构件"
        },
        "04": {  # 电缆类
            "01": "电力电缆",
            "02": "控制电缆",
            "03": "通信电缆",
            "04": "光纤电缆",
            "05": "特种电缆"
        },
        "08": {  # 设备类
            "01": "配电设备",
            "02": "发电设备",
            "03": "监控设备",
            "04": "网络设备",
            "05": "消防设备",
            "06": "电梯设备",
            "07": "暖通设备"
        }
    }

    # 单位编码表
    UNITS = {
        "01": "吨",
        "02": "千克",
        "03": "米",
        "04": "根",
        "05": "个",
        "06": "套",
        "07": "卷",
        "08": "箱",
        "09": "块",
        "10": "平方",
        "11": "立方",
        "12": "包"
    }

    # 规格编码表
    SPECS = {
        "01": "标准规格",
        "02": "大规格",
        "03": "小规格"
    }

    def __init__(self, session: Session):
        self.session = session

    def generate_code(
        self,
        category: str,
        mid: str,
        sub: str,
        spec: str = "01",
        unit: str = "05",
        supplier: str = "00"
    ) -> str:
        """生成18位编码"""
        year = str(datetime.now().year)[-2:]
        sequence = self._get_next_sequence(category, mid, sub, year)

        code = f"{category}{mid}{sub}{spec}{unit}{supplier}{year}{sequence:04d}"
        return code

    def _get_next_sequence(
        self,
        category: str,
        mid: str,
        sub: str,
        year: str
    ) -> int:
        """获取下一个流水号"""
        prefix = f"{category}{mid}{sub}{year}"

        last = self.session.query(MaterialCode).filter(
            MaterialCode.code.like(f"{prefix}%")
        ).order_by(MaterialCode.sequence.desc()).first()

        if last:
            return last.sequence + 1
        return 1

    def parse_code(self, code: str) -> dict:
        """解析编码，返回各部分含义"""
        if len(code) != 18:
            return {}

        return {
            "category": code[0:2],
            "category_name": self.CATEGORIES.get(code[0:2], "未知"),
            "mid_category": code[2:4],
            "sub_category": code[4:6],
            "spec": code[6:8],
            "unit": code[8:10],
            "supplier_code": code[10:12],
            "year": code[12:14],
            "sequence": code[14:18]
        }

    def match_category(self, material_name: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """根据物料名称匹配分类"""
        name = material_name.lower()

        # 大类关键词映射
        category_keywords = {
            "01": ["钢筋", "钢材", "钢板", "钢管", "钢构件", "螺纹钢", "盘圆", "工字钢", "槽钢", "角钢"],
            "02": ["水泥"],
            "03": ["混凝土", "商砼"],
            "04": ["电缆", "电线", "光缆", "电力电缆", "控制电缆"],
            "05": ["管", "pvc管", "pe管", "钢管"],
            "06": ["木材", "模板", "木方", "竹胶板"],
            "07": ["电气", "开关", "插座", "灯具", "配电箱"],
            "08": ["设备", "监控", "摄像头", "交换机", "电梯", "空调", "风机"],
            "09": ["五金", "螺丝", "螺母", "铁丝", "钢丝绳"],
            "10": ["防护", "安全帽", "安全带", "防护网"],
            "11": ["油漆", "涂料", "稀释剂"],
            "12": ["保温", "防水", "密封胶"]
        }

        # 匹配大类
        category_code = "99"  # 默认其他
        for code, keywords in category_keywords.items():
            for keyword in keywords:
                if keyword in name:
                    category_code = code
                    break
            else:
                continue
            break

        # 中类关键词映射（按大类分组）
        mid_keywords = {
            "01": {  # 钢材类
                "01": ["盘圆", "光圆", "HPB"],
                "02": ["螺纹", "带肋", "HRB"],
                "03": ["工字钢"],
                "04": ["槽钢"],
                "05": ["角钢"],
                "06": ["钢板"],
                "07": ["钢管"],
                "08": ["钢构件"]
            },
            "04": {  # 电缆类
                "01": ["电力电缆", "YJV", "VV"],
                "02": ["控制电缆", "KVV"],
                "03": ["通信电缆"],
                "04": ["光纤", "光缆"],
                "05": ["特种电缆", "耐火", "阻燃"]
            },
            "08": {  # 设备类
                "01": ["配电", "变压器", "配电柜"],
                "02": ["发电", "发电机", "UPS"],
                "03": ["监控", "摄像头", "NVR", "录像机"],
                "04": ["网络", "交换机", "路由器"],
                "05": ["消防", "烟感", "温感", "灭火器"],
                "06": ["电梯", "升降梯", "扶梯"],
                "07": ["暖通", "空调", "风机盘管"]
            }
        }

        # 匹配中类
        mid_code = "01"  # 默认
        mid_kw = mid_keywords.get(category_code, {})
        for code, keywords in mid_kw.items():
            for keyword in keywords:
                if keyword in name:
                    mid_code = code
                    break
            else:
                continue
            break

        # 小类默认01
        sub_code = "01"

        return category_code, mid_code, sub_code

    def create_material_code(
        self,
        name: str,
        specification: str = "",
        category: str = None,
        mid: str = None,
        sub: str = None,
        spec: str = "01",
        unit: str = "05",
        supplier: str = "00"
    ) -> MaterialCode:
        """创建新的物料编码"""
        # 如果没有分类信息，从名称匹配
        if not category:
            category, mid, sub = self.match_category(name)
            if not category:
                category = "99"
            if not mid:
                mid = "01"
            if not sub:
                sub = "01"

        # 生成编码
        code = self.generate_code(category, mid, sub, spec, unit, supplier)

        # 创建记录
        material_code = MaterialCode(
            code=code,
            category=category,
            mid_category=mid,
            sub_category=sub,
            spec=spec,
            unit=unit,
            supplier_code=supplier,
            year=str(datetime.now().year)[-2:],
            sequence=int(code[14:18]),
            name=name,
            specification=specification
        )
        self.session.add(material_code)
        self.session.flush()
        return material_code

    def get_code_info(self, code: str) -> Optional[dict]:
        """获取编码详细信息"""
        material = self.session.query(MaterialCode).filter(
            MaterialCode.code == code
        ).first()

        if not material:
            return None

        return {
            "code": material.code,
            "name": material.name,
            "specification": material.specification,
            "category": material.category,
            "category_name": self.CATEGORIES.get(material.category, "未知"),
            "mid_category": material.mid_category,
            "unit": material.unit,
            "unit_name": self.UNITS.get(material.unit, "未知"),
            "year": material.year,
            "sequence": material.sequence
        }
