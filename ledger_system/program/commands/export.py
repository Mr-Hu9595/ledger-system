"""Export command - export reports and dashboard"""
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ledger_system.business.report.report_generator import ReportGenerator


class ExportCommand:
    """Export ledger reports and dashboard"""

    def execute(self, args):
        """Execute export command"""
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate dashboard
        if hasattr(args, "dashboard") and args.dashboard:
            from ledger_system.business.report.dashboard_generator import DashboardGenerator
            generator = DashboardGenerator()
            result_path = generator.generate(str(output_path))
            print(f"材料看板已生成: {result_path}")
            return

        # Handle selected items export
        if hasattr(args, "selected") and args.selected:
            generator = ReportGenerator()
            result_path = generator.generate_selected_report(
                args.selected, str(output_path)
            )
            print(f"选中物料报表已导出: {result_path}")
            return

        # Parse date range
        start_date = None
        end_date = None
        if hasattr(args, "start") and args.start:
            start_date = datetime.fromisoformat(args.start).date()
        if hasattr(args, "end") and args.end:
            end_date = datetime.fromisoformat(args.end).date()

        # Export based on type
        generator = ReportGenerator()
        if args.type == "inventory":
            result_path = generator.generate_full_report(
                str(output_path), start_date, end_date
            )
            print(f"库存报表已导出: {result_path}")
        elif args.type == "inbound":
            # For inbound only, use the generator
            result_path = generator.generate_full_report(
                str(output_path), start_date, end_date
            )
            print(f"入库记录已导出: {result_path}")
        elif args.type == "outbound":
            result_path = generator.generate_full_report(
                str(output_path), start_date, end_date
            )
            print(f"出库记录已导出: {result_path}")
        else:
            # Full export
            result_path = generator.generate_full_report(
                str(output_path), start_date, end_date
            )
            print(f"报表已导出: {result_path}")
