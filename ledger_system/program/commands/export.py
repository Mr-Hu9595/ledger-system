"""Export command - export reports"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pandas as pd
from datetime import datetime
from ledger_system.data.database import get_session
from ledger_system.data.repository import LedgerRepository


class ExportCommand:
    """Export ledger reports"""

    def execute(self, args):
        """Execute export command"""
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if args.type == "inventory":
            self._export_inventory(output_path)
        elif args.type == "inbound":
            self._export_inbound(output_path, args)
        elif args.type == "outbound":
            self._export_outbound(output_path, args)

    def _export_inventory(self, output_path: Path):
        """Export inventory report"""
        with get_session() as session:
            repo = LedgerRepository(session)
            items = repo.get_all_ledgers()

            data = []
            for item in items:
                data.append({
                    "名称": item.name,
                    "规格": item.specification,
                    "类别": item.category,
                    "单位": item.unit,
                    "当前库存": float(item.current_stock),
                    "最小库存": float(item.min_stock),
                    "状态": "正常" if item.current_stock >= item.min_stock else "库存不足"
                })

            df = pd.DataFrame(data)
            df.to_excel(output_path, index=False, engine="openpyxl")
            print(f"库存报表已导出: {output_path}")

    def _export_inbound(self, output_path: Path, args):
        """Export inbound report"""
        with get_session() as session:
            repo = LedgerRepository(session)

            # Filter by date if specified
            start_date = None
            end_date = None
            if args.start:
                start_date = datetime.fromisoformat(args.start).date()
            if args.end:
                end_date = datetime.fromisoformat(args.end).date()

            ledgers = repo.get_all_ledgers()
            data = []

            for ledger in ledgers:
                inbounds = repo.get_inbound_history(ledger.id, days=99999)
                for ib in inbounds:
                    if start_date and ib.inbound_date < start_date:
                        continue
                    if end_date and ib.inbound_date > end_date:
                        continue

                    inbound_time_str = str(ib.inbound_time)[:8] if ib.inbound_time else ""

                    data.append({
                        "日期": ib.inbound_date,
                        "时间": inbound_time_str,
                        "材料": ledger.name,
                        "规格": ledger.specification,
                        "数量": float(ib.quantity),
                        "单位": ledger.unit,
                        "供应商": ib.supplier,
                        "入库人": ib.inbound_operator,
                        "单据来源": ib.document_source,
                        "备注": ib.notes
                    })

            df = pd.DataFrame(data)
            df = df.sort_values("日期", ascending=False)
            df.to_excel(output_path, index=False, engine="openpyxl")
            print(f"入库记录已导出: {output_path}")

    def _export_outbound(self, output_path: Path, args):
        """Export outbound report"""
        with get_session() as session:
            repo = LedgerRepository(session)

            start_date = None
            end_date = None
            if args.start:
                start_date = datetime.fromisoformat(args.start).date()
            if args.end:
                end_date = datetime.fromisoformat(args.end).date()

            ledgers = repo.get_all_ledgers()
            data = []

            for ledger in ledgers:
                outbounds = repo.get_outbound_history(ledger.id, days=99999)
                for ob in outbounds:
                    if start_date and ob.outbound_date < start_date:
                        continue
                    if end_date and ob.outbound_date > end_date:
                        continue

                    outbound_time_str = str(ob.outbound_time)[:8] if ob.outbound_time else ""

                    data.append({
                        "日期": ob.outbound_date,
                        "时间": outbound_time_str,
                        "材料": ledger.name,
                        "规格": ledger.specification,
                        "数量": float(ob.quantity),
                        "单位": ledger.unit,
                        "用途": ob.usage,
                        "领料人": ob.receiver,
                        "出库人": ob.outbound_operator,
                        "备注": ob.notes
                    })

            df = pd.DataFrame(data)
            df = df.sort_values("日期", ascending=False)
            df.to_excel(output_path, index=False, engine="openpyxl")
            print(f"出库记录已导出: {output_path}")