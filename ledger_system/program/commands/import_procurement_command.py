"""import_procurement 命令 - 导入采购清单到台账"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from ledger_system.business.procurement import import_procurement_list


class ImportProcurementCommand:

    def execute(self, args: argparse.Namespace):
        file_path = args.file

        if not Path(file_path).exists():
            print(f"文件不存在: {file_path}")
            return

        print(f"开始导入: {file_path}")
        results = import_procurement_list(file_path)

        print("\n=== 导入结果 ===")
        total = 0
        for sheet, result in results.items():
            if result["status"] == "success":
                print(f"  {sheet}: {result['created']} 条")
                total += result.get("created", 0)
            else:
                print(f"  {sheet}: {result['status']} - {result.get('reason', '')}")

        print(f"\n总计: {total} 条记录导入完成")


def add_parser(subparsers):
    parser = subparsers.add_parser("import", help="导入采购清单到台账")
    parser.add_argument("file", help="采购清单Excel文件路径")
    return parser