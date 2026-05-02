"""Code generator for material coding system"""
from datetime import datetime
from typing import Optional, Tuple

from sqlalchemy.orm import Session
from ledger_system.data.models.material_code import MaterialCode
from ledger_system.data.models.category import Category


class CodeGenerator:
    """物料编码生成器 - 18位编码"""

    # 大类编码表（扩展性强，保留14-98给未来）
    CATEGORIES = {
        "01": "钢材/金属材料",
        "02": "电线电缆",
        "03": "管材管件",
        "04": "电气材料/元器件",
        "05": "通讯设备",
        "06": "机械设备",
        "07": "监控设备",
        "08": "雾炮设备",
        "09": "建筑五金",
        "10": "保温防水材料",
        "11": "油漆涂料",
        "12": "安全防护",
        "13": "工具仪表",
        "14": "其他设备"
    }

    # 中类编码表（按大类分组）
    MID_CATEGORIES = {
        "01": {  # 钢材/金属材料
            "01": "钢筋/螺纹钢",
            "02": "型材",
            "03": "板材",
            "04": "管材",
            "05": "钢构件"
        },
        "02": {  # 电线电缆
            "01": "电力电缆",
            "02": "控制电缆",
            "03": "通讯线缆"
        },
        "03": {  # 管材管件
            "01": "钢管",
            "02": "桥架",
            "03": "法兰",
            "04": "阀门",
            "05": "其他管件"
        },
        "04": {  # 电气材料/元器件
            "01": "配电设备",
            "02": "开关插座",
            "03": "灯具",
            "04": "其他电气材料"
        },
        "05": {  # 通讯设备
            "01": "网络设备",
            "02": "光纤设备",
            "03": "通讯配件"
        },
        "06": {  # 机械设备
            "01": "水泵",
            "02": "供水设备",
            "03": "冷干机/空压机",
            "04": "过滤器"
        },
        "07": {  # 监控设备
            "01": "摄像头",
            "02": "存储设备",
            "03": "显示器",
            "04": "监控配件"
        },
        "08": {  # 雾炮设备
            "01": "雾炮主机",
            "02": "控制柜",
            "03": "雾炮配件"
        },
        "09": {  # 建筑五金
            "01": "紧固件",
            "02": "密封材料",
            "03": "辅材"
        },
        "10": {  # 保温防水材料
            "01": "保温材料",
            "02": "防水材料"
        },
        "11": {  # 油漆涂料
            "01": "油漆",
            "02": "涂料"
        },
        "12": {  # 安全防护
            "01": "防护用品",
            "02": "安全用品"
        },
        "13": {  # 工具仪表
            "01": "工具",
            "02": "仪表"
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

    def _check_code_exists(self, code: str) -> bool:
        """检查编码是否已存在"""
        existing = self.session.query(MaterialCode).filter(
            MaterialCode.code == code
        ).first()
        return existing is not None

    def generate_unique_code(
        self,
        category: str,
        mid: str,
        sub: str,
        spec: str = "01",
        unit: str = "05",
        supplier: str = "00"
    ) -> str:
        """生成唯一的18位编码，确保不重复"""
        year = str(datetime.now().year)[-2:]

        # Try to get next sequence first
        sequence = self._get_next_sequence(category, mid, sub, year)
        code = f"{category}{mid}{sub}{spec}{unit}{supplier}{year}{sequence:04d}"

        # If code exists, find next available sequence
        while self._check_code_exists(code):
            sequence += 1
            code = f"{category}{mid}{sub}{spec}{unit}{supplier}{year}{sequence:04d}"

        return code

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
            "01": ["钢筋", "钢材", "钢板", "钢管", "钢构件", "螺纹钢", "盘圆", "工字钢", "槽钢", "角钢", "扁钢", "矩通", "镀锌"],
            "02": ["电缆", "电线", "光缆", "电力电缆", "控制电缆", "光纤", "网线", "跳线", "接地线", "电源线"],
            "03": ["管", "pvc管", "pe管", "钢管", "桥架", "穿线盒", "接线盒", "梯架", "法兰", "球阀", "止回阀", "减压阀", "浮球阀", "阀门", "弯头", "三通", "大小头"],
            "04": ["电气", "开关", "插座", "灯具", "配电箱", "断路器", "空开", "插排", "模块", "PDU", "补光灯"],
            "05": ["交换机", "路由器", "光纤收发器", "物联网卡", "网关", "光模块", "配线架", "光纤盒", "收发器", "网络", "通信柜", "通信箱", "分表计电", "防爆", "防爆柜", "防爆箱", "底层通信柜", "通信设备", "超五类网线", "超五类", "网线"],
            "06": ["水泵", "供水", "水箱", "过滤器", "冷干机", "空压机", "干燥机", "压力表", "流量计"],
            "07": ["监控", "摄像头", "录像机", "球机", "枪机", "NVR", "录像机", "红外", "对射", "门禁", "显示器", "服务器", "储存", "视频储存"],
            "08": ["雾炮", "控制柜", "雾炮主机"],
            "09": ["螺丝", "螺母", "铁丝", "钢丝绳", "螺栓", "扎带", "接头", "管卡", "铆钉", "活接", "对丝", "卡箍", "支架", "抱箍", "卡子", "铝板", "标准件", "丝头", "骑马卡", "辅材", "胶带", "密封"],
            "10": ["保温", "防水", "密封胶", "橡塑", "岩棉"],
            "11": ["油漆", "涂料", "稀释剂"],
            "12": ["防护", "安全帽", "安全带", "防护网", "劳保"],
            "13": ["工具", "仪表", "仪表", "维修"]
        }

        # 匹配大类 - 优先匹配最长关键词
        category_code = "99"  # 默认其他
        best_match_len = 0
        for code, keywords in category_keywords.items():
            for keyword in keywords:
                if keyword in name:
                    match_len = len(keyword)
                    if match_len > best_match_len:
                        best_match_len = match_len
                        category_code = code

        # 中类关键词映射（按大类分组）
        mid_keywords = {
            "01": {  # 钢材/金属材料
                "01": ["钢筋", "螺纹", "盘圆", "HPB", "HRB"],
                "02": ["角钢", "槽钢", "工字钢", "型钢"],
                "03": ["钢板", "扁钢", "铝板", "花纹板", "彩钢板"],
                "04": ["钢管", "镀锌管", "矩通", "无缝管"],
                "05": ["钢构件", "雨棚", "支架"]
            },
            "02": {  # 电线电缆
                "01": ["电力电缆", "YJV", "VV", "电源线", "接地线"],
                "02": ["控制电缆", "KVV"],
                "03": ["光纤", "光缆", "跳线", "网线", "超五类", "光模块"]
            },
            "03": {  # 管材管件
                "01": ["钢管", "镀锌管", "无缝管"],
                "02": ["桥架", "梯架"],
                "03": ["法兰", "法兰垫"],
                "04": ["球阀", "止回阀", "减压阀", "浮球阀", "阀门"],
                "05": ["弯头", "三通", "大小头", "接头", "管卡", "穿线盒", "接线盒"]
            },
            "04": {  # 电气材料/元器件
                "01": ["配电箱", "配电柜", "断路器", "空开", "开关电源"],
                "02": ["开关", "插座", "插排", "PDU"],
                "03": ["灯具", "灯", "补光灯"],
                "04": ["模块", "采集模块", "光模块"]
            },
            "05": {  # 通讯设备
                "01": ["交换机", "路由器", "网关", "收发器"],
                "02": ["光纤收发器", "配线架", "光纤盒", "终端盒"],
                "03": ["物联网卡", "通讯配件"]
            },
            "06": {  # 机械设备
                "01": ["水泵", "供水"],
                "02": ["水箱", "过滤器", "精密过滤器"],
                "03": ["冷干机", "空压机", "干燥机"],
                "04": ["压力表", "流量计"]
            },
            "07": {  # 监控设备
                "01": ["摄像头", "球机", "枪机", "NVR", "录像机"],
                "02": ["服务器", "存储", "磁盘阵列"],
                "03": ["显示器", "监视器"],
                "04": ["支架", "立杆", "壁装", "吊装", "鸭嘴支架"]
            },
            "08": {  # 雾炮设备
                "01": ["雾炮"],
                "02": ["控制柜", "电箱"],
                "03": ["塔架", "分站", "雾炮改造"]
            },
            "09": {  # 建筑五金
                "01": ["螺栓", "螺丝", "螺母", "螺钉", "铁丝", "钢丝绳", "铆钉"],
                "02": ["密封胶", "生料带"],
                "03": ["扎带", "卡扣", "管卡", "卡子", "辅材", "标准件"]
            },
            "10": {  # 保温防水材料
                "01": ["保温", "岩棉", "橡塑"],
                "02": ["防水", "密封"]
            },
            "11": {  # 油漆涂料
                "01": ["油漆", "稀释剂"],
                "02": ["涂料", "胶带"]
            },
            "12": {  # 安全防护
                "01": ["安全帽", "安全带", "防护网", "防护"],
                "02": ["劳保", "工作服"]
            },
            "13": {  # 工具仪表
                "01": ["工具", "维修"],
                "02": ["仪表", "压力表", "流量计"]
            }
        }

        # 匹配中类 - 优先匹配最长关键词
        mid_code = "01"  # 默认
        mid_kw = mid_keywords.get(category_code, {})
        best_mid_match_len = 0
        for code, keywords in mid_kw.items():
            for keyword in keywords:
                if keyword in name:
                    match_len = len(keyword)
                    if match_len > best_mid_match_len:
                        best_mid_match_len = match_len
                        mid_code = code

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

        # 生成唯一编码
        code = self.generate_unique_code(category, mid, sub, spec, unit, supplier)

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
