"""DocumentLog (文档处理记录) model"""
from sqlalchemy import Column, String, Text, JSON
from ledger_system.data.models.base import BaseModel


class DocumentLog(BaseModel):
    """Document processing log"""
    __tablename__ = "document_log"

    file_path = Column(String(500), nullable=False)
    process_type = Column(String(50), default="ocr")  # ocr / parse
    result = Column(JSON, default={})
    status = Column(String(20), default="pending")  # pending / success / failed
    error_message = Column(Text, default="")

    def __repr__(self):
        return f"<DocumentLog {self.file_path}: {self.status}>"