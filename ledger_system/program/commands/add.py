"""Add command - natural language ledger entry"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ledger_system.data.database import get_session
from ledger_system.data.repository import LedgerRepository
from ledger_system.business.nlp.ai_service import AIService
from ledger_system.business.nlp.rule_engine import RuleEngine
from ledger_system.business.learning.feedback import FeedbackLearning
from ledger_system.business.learning.diff_logger import DiffLogger
from ledger_system.business.code_generator import CodeGenerator
from ledger_system.business.document.document_manager import DocumentManager
from ledger_system.business.report.report_sync import ReportSync


class AddCommand:
    """Add ledger entry using natural language"""

    def __init__(self):
        self.ai_service = AIService()
        self.rule_engine = RuleEngine()

    def execute(self, args):
        """Execute add command"""
        text = " ".join(args.text)
        print(f"正在解析: {text}")

        # Try AI extraction first
        ai_result = {}
        try:
            ai_result = self.ai_service.extract_entities(text)
            print(f"AI解析结果: {ai_result}")
        except Exception as e:
            print(f"AI解析失败: {e}")

        # Rule engine fallback
        rule_result = self.rule_engine.extract_entities(text)
        print(f"规则解析结果: {rule_result}")

        # Use AI result if available, otherwise use rule
        if ai_result.get("material_name"):
            final_result = ai_result
        else:
            final_result = rule_result

        # Log difference
        with get_session() as session:
            diff_logger = DiffLogger(session)
            diff_logger.log_diff(text, ai_result, rule_result)

        # Check if we have enough info
        if not final_result.get("material_name"):
            print("错误: 未能识别材料名称")
            return

        quantity = final_result.get("quantity") or 0
        unit = final_result.get("unit", "")
        supplier = final_result.get("supplier", "")

        print(f"\n确认录入:")
        print(f"  材料: {final_result['material_name']}")
        print(f"  数量: {quantity} {unit}")
        print(f"  供应商: {supplier}")
        print(f"  日期: {final_result.get('date', '今天')}")

        if args.confirm:
            self._save_to_db(final_result)
        else:
            response = input("\n确认录入? (y/n): ").strip().lower()
            if response == "y":
                self._save_to_db(final_result)

    def _save_to_db(self, result: dict):
        """Save entry to database"""
        from datetime import date, time, datetime

        with get_session() as session:
            repo = LedgerRepository(session)

            # Find or create ledger
            ledger = repo.get_ledger_by_name(result["material_name"])
            material_code = None

            if not ledger:
                print(f"创建新材料: {result['material_name']}")

                # 生成物料编码
                code_gen = CodeGenerator(session)
                cat_code, mid_code, sub_code = code_gen.match_category(result["material_name"])

                # 确定单位编码
                unit_map = {"吨": "01", "千克": "02", "米": "03", "个": "05", "根": "04",
                           "卷": "07", "箱": "08", "块": "09", "平方": "10", "立方": "11"}
                unit_code = unit_map.get(result.get("unit", ""), "05")

                # 生成编码记录
                mat_code = code_gen.create_material_code(
                    name=result["material_name"],
                    specification=result.get("specification", ""),
                    category=cat_code,
                    mid=mid_code,
                    sub=sub_code,
                    unit=unit_code,
                    supplier="00"
                )
                material_code = mat_code.code
                print(f"  物料编码: {material_code}")

                ledger = repo.create_ledger(
                    category="material",
                    name=result["material_name"],
                    unit=result.get("unit", ""),
                    material_code=material_code
                )

            # Parse date
            inbound_date = result.get("date")
            if inbound_date and isinstance(inbound_date, str):
                inbound_date = datetime.fromisoformat(inbound_date).date()
            else:
                inbound_date = date.today()

            # Get current time
            inbound_time = time(8, 0)  # 默认早上8点
            now = datetime.now()
            inbound_time = now.time()

            # Get operator from result or use default
            inbound_operator = result.get("operator", "系统录入")

            # Add inbound
            from decimal import Decimal

            inbound = repo.add_inbound(
                ledger_id=ledger.id,
                quantity=Decimal(str(result.get("quantity", 0))),
                supplier=result.get("supplier", ""),
                inbound_date=inbound_date,
                inbound_time=inbound_time,
                inbound_operator=inbound_operator,
                notes=f"来源: 自然语言录入"
            )

            # 保存原始单据摘要
            doc_mgr = DocumentManager(session)
            txt_path = doc_mgr._create_summary_txt(
                txt_path=Path("D:/工作/日常工作/台账/documents") / f"temp_{inbound.id}.txt",
                material_name=result["material_name"],
                quantity=float(result.get("quantity", 0)),
                supplier=result.get("supplier", ""),
                document_type="inbound",
                original_file="自然语言录入",
                notes=f"来源: 自然语言录入"
            )
            # 更新入库记录的单据路径
            inbound.original_document_path = txt_path
            session.flush()

            print(f"入库成功! 当前库存: {ledger.current_stock}")

            # 同步报表
            print("正在同步报表...")
            report_sync = ReportSync()
            report_sync.sync_all()
            print(f"报表已更新: {report_sync.REPORT_FILE}")