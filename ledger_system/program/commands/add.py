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
            if not ledger:
                print(f"创建新材料: {result['material_name']}")
                ledger = repo.create_ledger(
                    category="material",
                    name=result["material_name"],
                    unit=result.get("unit", "")
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

            repo.add_inbound(
                ledger_id=ledger.id,
                quantity=Decimal(str(result.get("quantity", 0))),
                supplier=result.get("supplier", ""),
                inbound_date=inbound_date,
                inbound_time=inbound_time,
                inbound_operator=inbound_operator,
                notes=f"来源: 自然语言录入"
            )

            print(f"入库成功! 当前库存: {ledger.current_stock}")