"""Process command - document processing"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ledger_system.business.document.parser import DocumentParser
from ledger_system.business.document.watcher import FileWatcher
from ledger_system.business.document.document_manager import DocumentManager
from ledger_system.business.code_generator import CodeGenerator
from ledger_system.business.report.report_sync import ReportSync
from ledger_system.data.database import get_session
from ledger_system.data.repository import LedgerRepository
from ledger_system.data.models.document_log import DocumentLog
from datetime import date, time, datetime
from decimal import Decimal


class ProcessCommand:
    """Process documents"""

    def __init__(self):
        self.parser = DocumentParser()

    def execute(self, args):
        """Execute process command"""
        if args.folder:
            self._start_watcher(args.folder)
        elif args.file:
            self._process_file(args.file)
        else:
            print("请指定文件或文件夹")

    def _process_file(self, file_path: str):
        """Process single file"""
        print(f"处理文件: {file_path}")

        try:
            result = self.parser.parse_file(file_path)

            if "error" in result:
                print(f"处理失败: {result['error']}")
            else:
                print(f"解析结果: {result}")
                self._save_to_ledger(result, file_path)

        except Exception as e:
            print(f"处理异常: {e}")

    def _save_to_ledger(self, result: dict, file_path: str):
        """Save parsing result to ledger"""
        material_name = result.get("material_name")
        if not material_name:
            print("未能从文档中识别材料")
            return

        with get_session() as session:
            repo = LedgerRepository(session)
            doc_mgr = DocumentManager(session)

            # Find or create ledger
            ledger = repo.get_ledger_by_name(material_name)
            if not ledger:
                print(f"创建新材料: {material_name}")

                # 生成物料编码
                code_gen = CodeGenerator(session)
                cat_code, mid_code, sub_code = code_gen.match_category(material_name)

                unit_map = {"吨": "01", "千克": "02", "米": "03", "个": "05", "根": "04",
                           "卷": "07", "箱": "08", "块": "09", "平方": "10", "立方": "11"}
                unit_code = unit_map.get(result.get("unit", ""), "05")

                mat_code = code_gen.create_material_code(
                    name=material_name,
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
                    name=material_name,
                    unit=result.get("unit", ""),
                    specification=result.get("specification", ""),
                    material_code=material_code
                )

            # Parse date
            inbound_date = result.get("date")
            if inbound_date and isinstance(inbound_date, str):
                inbound_date = datetime.fromisoformat(inbound_date).date()
            else:
                inbound_date = date.today()

            # Get current time
            inbound_time = datetime.now().time()

            # Get operator
            inbound_operator = result.get("operator", "文档录入")

            # Parse quantity
            quantity = result.get("quantity") or 0
            if isinstance(quantity, str):
                try:
                    quantity = float(quantity)
                except:
                    quantity = 0

            inbound = repo.add_inbound(
                ledger_id=ledger.id,
                quantity=Decimal(str(quantity)),
                supplier=result.get("supplier", ""),
                inbound_date=inbound_date,
                inbound_time=inbound_time,
                inbound_operator=inbound_operator,
                document_source=file_path,
                notes=f"来源: 文档解析"
            )

            # 保存原始单据到日期文件夹并生成摘要
            if Path(file_path).exists():
                txt_path = doc_mgr.save_original_document(
                    source_path=file_path,
                    record_type="inbound",
                    record_id=inbound.id,
                    material_name=material_name,
                    quantity=quantity,
                    supplier=result.get("supplier", ""),
                    notes=f"来源: 文档解析"
                )
                inbound.original_document_path = txt_path
                session.flush()
                print(f"  原始单据已保存: {txt_path}")

            # Log
            log = DocumentLog(
                file_path=file_path,
                process_type="parse",
                result=result,
                status="success"
            )
            session.add(log)

            print(f"入库成功: {material_name} x {quantity}")
            print(f"当前库存: {ledger.current_stock}")

            # 同步报表
            print("正在同步报表...")
            report_sync = ReportSync()
            report_sync.sync_all()
            print(f"报表已更新: {report_sync.REPORT_FILE}")

    def _start_watcher(self, folder: str):
        """Start file watcher"""
        print(f"启动文件夹监控: {folder}")
        print("按 Ctrl+C 停止")

        def on_new_file(data: dict):
            print(f"\n检测到新文件: {data['file_path']}")
            if data["status"] == "success":
                self._save_to_ledger(data["result"], data["file_path"])
            else:
                print(f"处理失败: {data.get('result', {}).get('error')}")

        watcher = FileWatcher(folder, on_new_file)
        try:
            watcher.start()
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            watcher.stop()
            print("\n监控已停止")