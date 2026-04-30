"""CLI entry point"""
import sys
import argparse
from ledger_system.program.commands.add import AddCommand
from ledger_system.program.commands.query import QueryCommand
from ledger_system.program.commands.process import ProcessCommand
from ledger_system.program.commands.export import ExportCommand
from ledger_system.program.commands.sync import SyncCommand


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser"""
    parser = argparse.ArgumentParser(
        prog="ledger",
        description="工地材料设备进出库台账管理系统"
    )

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # Add command
    add_parser = subparsers.add_parser("add", help="自然语言录入")
    add_parser.add_argument("text", nargs="+", help="录入文本")
    add_parser.add_argument("--confirm", action="store_true", help="确认后录入")

    # Query command
    query_parser = subparsers.add_parser("query", help="查询台账")
    query_parser.add_argument("--material", help="材料名称")
    query_parser.add_argument("--all", action="store_true", help="查询所有")
    query_parser.add_argument("--low-stock", action="store_true", help="库存不足")
    query_parser.add_argument("--days", type=int, default=30, help="历史天数")

    # Process command
    process_parser = subparsers.add_parser("process", help="处理文档")
    process_parser.add_argument("--file", required=True, help="文件路径")
    process_parser.add_argument("--folder", help="文件夹路径")

    # Export command
    export_parser = subparsers.add_parser("export", help="导出报表")
    export_parser.add_argument("--type", choices=["inventory", "inbound", "outbound", "all"],
                               default="all", help="报表类型")
    export_parser.add_argument("--format", choices=["xlsx", "csv"], default="xlsx",
                               help="导出格式")
    export_parser.add_argument("--output", required=True, help="输出路径")
    export_parser.add_argument("--start", help="开始日期 YYYY-MM-DD")
    export_parser.add_argument("--end", help="结束日期 YYYY-MM-DD")
    export_parser.add_argument("--dashboard", action="store_true",
                               help="生成交互式材料看板")
    export_parser.add_argument("--selected", nargs="+",
                               help="选中导出的物料ID列表")

    # Sync command
    sync_parser = subparsers.add_parser("sync", help="同步报表")

    # Help command
    help_parser = subparsers.add_parser("help", help="显示帮助")

    return parser


def main():
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "help":
        parser.print_help()
        return

    if args.command == "add":
        cmd = AddCommand()
        cmd.execute(args)
    elif args.command == "query":
        cmd = QueryCommand()
        cmd.execute(args)
    elif args.command == "process":
        cmd = ProcessCommand()
        cmd.execute(args)
    elif args.command == "export":
        cmd = ExportCommand()
        cmd.execute(args)
    elif args.command == "sync":
        cmd = SyncCommand()
        cmd.execute(args)
    else:
        print(f"未知命令: {args.command}")
        parser.print_help()


if __name__ == "__main__":
    main()
