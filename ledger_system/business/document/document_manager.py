"""Document manager for handling original documents"""
import shutil
from pathlib import Path
from datetime import datetime, date
from typing import Optional
from uuid import UUID

from ledger_system.data.models.inbound import Inbound
from ledger_system.data.models.outbound import Outbound


class DocumentManager:
    """管理原始单据的存储和关联"""

    ROOT_DIR = Path("D:/工作/日常工作/台账/documents")

    def __init__(self, session=None):
        self.session = session

    def save_original_document(
        self,
        source_path: str,
        record_type: str,
        record_id: UUID,
        material_name: str,
        quantity: float,
        supplier: str = "",
        notes: str = ""
    ) -> str:
        """保存原始单据到日期子文件夹，并生成txt摘要"""
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        today = date.today()
        date_folder = self.ROOT_DIR / today.strftime("%Y-%m-%d")
        date_folder.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%H%M%S")
        ext = source.suffix
        filename = f"{today.strftime('%Y%m%d')}_{timestamp}_{material_name[:20]}{ext}"
        dest_path = date_folder / filename

        shutil.copy2(source_path, dest_path)

        txt_path = date_folder / f"{today.strftime('%Y%m%d')}_{timestamp}_{material_name[:20]}_摘要.txt"
        self._create_summary_txt(
            txt_path,
            material_name=material_name,
            quantity=quantity,
            supplier=supplier,
            document_type=record_type,
            original_file=str(dest_path),
            notes=notes
        )

        return str(txt_path)

    def _create_summary_txt(
        self,
        txt_path: Path,
        material_name: str,
        quantity: float,
        supplier: str,
        document_type: str,
        original_file: str,
        notes: str
    ):
        """创建单据摘要txt文件"""
        content = f"""原始单据摘要
{'='*40}
文档类型: {document_type}
物料名称: {material_name}
数量: {quantity}
供应商: {supplier or '未知'}
原始文件: {original_file}
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
备注: {notes or '无'}
{'='*40}
本文件由台账系统自动生成
原始单据保存在同目录下的对应文件中
"""
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(content)

    def _create_summary_txt_inline(
        self,
        material_name: str,
        quantity: float,
        supplier: str = "",
        document_type: str = "inbound",
        notes: str = ""
    ) -> str:
        """创建摘要txt（无源文件时）"""
        today = date.today()
        date_folder = self.ROOT_DIR / today.strftime("%Y-%m-%d")
        date_folder.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%H%M%S")
        txt_path = date_folder / f"{today.strftime('%Y%m%d')}_{timestamp}_{material_name[:20]}_摘要.txt"

        content = f"""原始单据摘要
{'='*40}
文档类型: {document_type}
物料名称: {material_name}
数量: {quantity}
供应商: {supplier or '未知'}
原始文件: 自然语言录入
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
备注: {notes or '无'}
{'='*40}
本文件由台账系统自动生成
"""
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(content)

        return str(txt_path)

    def link_document_to_record(self, record_type: str, record_id: UUID, document_path: str):
        """将文档路径关联到入库/出库记录"""
        if not self.session:
            return

        if record_type == "inbound":
            record = self.session.query(Inbound).filter(Inbound.id == record_id).first()
        else:
            record = self.session.query(Outbound).filter(Outbound.id == record_id).first()

        if record:
            record.original_document_path = document_path
            self.session.flush()

    def list_documents_by_date(self, target_date: date = None) -> list:
        """列出指定日期的所有单据文件"""
        if target_date is None:
            target_date = date.today()

        date_folder = self.ROOT_DIR / target_date.strftime("%Y-%m-%d")
        if not date_folder.exists():
            return []

        files = []
        for f in date_folder.iterdir():
            if f.is_file():
                files.append({
                    "path": str(f),
                    "name": f.name,
                    "type": f.suffix,
                    "size": f.stat().st_size
                })
        return files
