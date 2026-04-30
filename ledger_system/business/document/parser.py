"""Document parser for various file types"""
import json
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
from ledger_system.business.nlp.ai_service import AIService


class DocumentParser:
    """Parse documents to extract structured information"""

    def __init__(self):
        self.ai_service = AIService()

    def parse_file(self, file_path: str) -> Dict[str, Any]:
        """Parse file based on extension"""
        path = Path(file_path)
        suffix = path.suffix.lower()

        if suffix in [".jpg", ".jpeg", ".png", ".bmp", ".gif"]:
            return self._parse_image(path)
        elif suffix == ".pdf":
            return self._parse_pdf(path)
        elif suffix in [".xlsx", ".xls"]:
            return self._parse_excel(path)
        elif suffix in [".docx", ".doc"]:
            return self._parse_word(path)
        elif suffix == ".txt":
            return self._parse_text(path)
        else:
            return {"error": f"Unsupported file type: {suffix}"}

    def _parse_image(self, path: Path) -> Dict[str, Any]:
        """Parse image using AI vision"""
        try:
            content = self.ai_service.understand_image(str(path))
            result = self.ai_service.parse_document_content(content, "image")
            result["source"] = "image_ocr"
            result["raw_content"] = content
            return result
        except Exception as e:
            return {"error": str(e), "source": "image_ocr"}

    def _parse_pdf(self, path: Path) -> Dict[str, Any]:
        """Parse PDF file"""
        try:
            # For PDF, we'd normally use pdfplumber or PyPDF2
            # For now, treat as text extraction needed
            content = self._extract_pdf_text(path)
            result = self.ai_service.parse_document_content(content, "pdf")
            result["source"] = "pdf"
            result["raw_content"] = content[:2000]
            return result
        except Exception as e:
            return {"error": str(e), "source": "pdf"}

    def _parse_excel(self, path: Path) -> Dict[str, Any]:
        """Parse Excel file"""
        try:
            df = pd.read_excel(path)
            content = df.to_string(max_rows=50)

            # Use AI to parse structured data from Excel
            result = self.ai_service.parse_document_content(content, "excel")
            result["source"] = "excel"
            result["raw_content"] = content[:2000]
            result["rows"] = len(df)
            result["columns"] = list(df.columns)
            return result
        except Exception as e:
            return {"error": str(e), "source": "excel"}

    def _parse_word(self, path: Path) -> Dict[str, Any]:
        """Parse Word document"""
        try:
            # For Word, we'd normally use python-docx
            # Placeholder for now
            content = f"Word document: {path.name}"
            result = self.ai_service.parse_document_content(content, "word")
            result["source"] = "word"
            return result
        except Exception as e:
            return {"error": str(e), "source": "word"}

    def _parse_text(self, path: Path) -> Dict[str, Any]:
        """Parse text file"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            result = self.ai_service.parse_document_content(content, "text")
            result["source"] = "text"
            result["raw_content"] = content[:2000]
            return result
        except Exception as e:
            return {"error": str(e), "source": "text"}

    def _extract_pdf_text(self, path: Path) -> str:
        """Extract text from PDF"""
        # Placeholder - would use pdfplumber
        return f"PDF content from {path.name}"