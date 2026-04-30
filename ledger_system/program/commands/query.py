"""Query command - ledger and history queries"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ledger_system.data.database import get_session
from ledger_system.data.repository import LedgerRepository


class QueryCommand:
    """Query ledger status and history"""

    def execute(self, args):
        """Execute query command"""
        with get_session() as session:
            repo = LedgerRepository(session)

            if args.low_stock:
                self._query_low_stock(repo)
            elif args.all:
                self._query_all(repo)
            elif args.material:
                self._query_material(repo, args)
            else:
                self._query_all(repo)

    def _query_all(self, repo: LedgerRepository):
        """Query all ledger items"""
        items = repo.get_all_ledgers()

        print(f"\n{'='*60}")
        print(f"{'台账总览':^30}")
        print(f"{'='*60}")
        print(f"{'名称':<20} {'规格':<15} {'库存':>10} {'单位':<6} {'状态':<8}")
        print(f"{'-'*60}")

        for item in items:
            status = "正常" if item.current_stock >= item.min_stock else "⚠️ 低库存"
            print(f"{item.name:<20} {item.specification:<15} {item.current_stock:>10} {item.unit:<6} {status}")

        print(f"{'='*60}")
        print(f"共 {len(items)} 条记录")

    def _query_low_stock(self, repo: LedgerRepository):
        """Query low stock items"""
        items = repo.get_low_stock_items()

        print(f"\n{'='*60}")
        print(f"{'库存不足警告':^30}")
        print(f"{'='*60}")

        if not items:
            print("所有材料库存充足")
            return

        for item in items:
            print(f"⚠️ {item.name}: {item.current_stock} {item.unit} (最小: {item.min_stock})")

    def _query_material(self, repo: LedgerRepository, args):
        """Query specific material"""
        ledger = repo.get_ledger_by_name(args.material)

        if not ledger:
            print(f"未找到材料: {args.material}")
            return

        print(f"\n{'='*70}")
        print(f"{'材料详情':^35}")
        print(f"{'='*70}")
        print(f"{'名称:':<10} {ledger.name}")
        print(f"{'规格:':<10} {ledger.specification}")
        print(f"{'单位:':<10} {ledger.unit}")
        print(f"{'当前库存:':<10} {ledger.current_stock}")
        print(f"{'最小库存:':<10} {ledger.min_stock}")
        print(f"{'='*70}")

        # Inbound history
        inbounds = repo.get_inbound_history(ledger.id, args.days)
        print(f"\n{'入库记录 (最近 ' + str(args.days) + ' 天)':^50}")
        print(f"{'-'*70}")
        print(f"{'日期':<12} {'时间':<8} {'数量':>8} {'供应商':<15} {'入库人':<10}")
        print(f"{'-'*70}")
        for ib in inbounds:
            inbound_time_str = str(ib.inbound_time)[:8] if ib.inbound_time else ""
            print(f"{str(ib.inbound_date):<12} {inbound_time_str:<8} {float(ib.quantity):>8.2f} {ib.supplier:<15} {ib.inbound_operator:<10}")

        # Outbound history
        outbounds = repo.get_outbound_history(ledger.id, args.days)
        print(f"\n{'出库记录 (最近 ' + str(args.days) + ' 天)':^50}")
        print(f"{'-'*70}")
        print(f"{'日期':<12} {'时间':<8} {'数量':>8} {'用途':<15} {'领料人':<10} {'出库人':<10}")
        print(f"{'-'*70}")
        for ob in outbounds:
            outbound_time_str = str(ob.outbound_time)[:8] if ob.outbound_time else ""
            print(f"{str(ob.outbound_date):<12} {outbound_time_str:<8} {float(ob.quantity):>8.2f} {ob.usage:<15} {ob.receiver:<10} {ob.outbound_operator:<10}")