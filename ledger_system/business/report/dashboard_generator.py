"""Material Dashboard Generator - Interactive Excel Dashboard"""
from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Optional
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

from ledger_system.data.database import get_session
from ledger_system.data.repository import LedgerRepository


class DashboardGenerator:
    """Generate interactive Excel dashboard for material lookup"""

    def __init__(self):
        self.repo = None

    def generate(self, output_path: str) -> str:
        """Generate interactive dashboard Excel file"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        wb = Workbook()

        # Sheet 1: 材料看板 (Dashboard)
        self._create_dashboard_sheet(wb)

        # Sheet 2: 台账总览 (数据源)
        self._create_ledger_data_sheet(wb)

        # Sheet 3: 入库记录 (数据源)
        self._create_inbound_data_sheet(wb)

        # Sheet 4: 出库记录 (数据源)
        self._create_outbound_data_sheet(wb)

        wb.save(str(output_path))
        return str(output_path)

    def _create_dashboard_sheet(self, wb: Workbook) -> None:
        """Create the interactive dashboard sheet"""
        ws = wb.active
        ws.title = "材料看板"

        # Styles
        header_font = Font(bold=True, size=14, color="FFFFFF")
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        section_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")
        section_font = Font(bold=True, size=12)
        thin_border = Border(
            left=Side(style="thin"),
            right=Side(style="thin"),
            top=Side(style="thin"),
            bottom=Side(style="thin")
        )

        # Title
        ws.merge_cells("A1:L1")
        ws["A1"] = "材料信息看板"
        ws["A1"].font = Font(bold=True, size=18)
        ws["A1"].alignment = Alignment(horizontal="center")

        # Row 3: Search area
        ws["A3"] = "搜索材料:"
        ws["A3"].font = Font(bold=True)
        ws["B3"] = ""  # User input cell
        ws["B3"].fill = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
        ws["B3"].border = thin_border
        ws["C3"] = "← 输入物料名称"
        ws["C3"].font = Font(italic=True, color="666666")

        # === Section 1: Basic Info ===
        ws.merge_cells("A5:L5")
        ws["A5"] = "基本信息"
        ws["A5"].fill = section_fill
        ws["A5"].font = section_font

        # Basic info labels and values
        basic_info = [
            ("名称", "B6", "D6"),
            ("规格", "B7", "D7"),
            ("类别", "B8", "D8"),
            ("单位", "F6", "G6"),
            ("物料编码", "F7", "G7"),
            ("采购日期", "F8", "G8"),
            ("当前库存", "I6", "J6"),
            ("最小库存", "I7", "J7"),
            ("库存状态", "I8", "J8"),
        ]

        for label, label_cell, value_cell in basic_info:
            ws[label_cell] = label + ":"
            ws[label_cell].font = Font(bold=True)
            ws[label_cell].border = thin_border
            ws[value_cell].border = thin_border

        # === Section 2: Inbound History ===
        ws.merge_cells("A10:L10")
        ws["A10"] = "入库记录 (最近10条)"
        ws["A10"].fill = section_fill
        ws["A10"].font = section_font

        # Header row for inbound
        inbound_headers = ["序号", "日期", "时间", "数量", "单位", "累计入库", "供应商", "操作人", "备注"]
        for col, header in enumerate(inbound_headers, 1):
            cell = ws.cell(row=11, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.border = thin_border
            cell.alignment = Alignment(horizontal="center")

        # Data rows for inbound (empty, will be filled by formulas or manual)
        for row in range(12, 22):  # 10 rows
            ws.cell(row=row, column=1, value=f"第{row-11}次").border = thin_border
            for col in range(2, 10):
                ws.cell(row=row, column=col).border = thin_border

        # === Section 3: Outbound History ===
        ws.merge_cells("A24:L24")
        ws["A24"] = "出库记录 (最近10条)"
        ws["A24"].fill = section_fill
        ws["A24"].font = section_font

        # Header row for outbound
        outbound_headers = ["序号", "日期", "时间", "数量", "单位", "累计出库", "用途", "领用人", "操作人", "备注"]
        for col, header in enumerate(outbound_headers, 1):
            cell = ws.cell(row=25, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.border = thin_border
            cell.alignment = Alignment(horizontal="center")

        # Data rows for outbound
        for row in range(26, 36):  # 10 rows
            ws.cell(row=row, column=1, value=f"第{row-25}次").border = thin_border
            for col in range(2, 11):
                ws.cell(row=row, column=col).border = thin_border

        # Set column widths
        column_widths = {
            "A": 12, "B": 15, "C": 15, "D": 15, "E": 10, "F": 15,
            "G": 18, "H": 12, "I": 15, "J": 12, "K": 15, "L": 15
        }
        for col, width in column_widths.items():
            ws.column_dimensions[col].width = width

        # Add data validation for material name dropdown
        # Note: This creates a simple dropdown - actual implementation would
        # need to reference the data sheet for the list

    def _create_ledger_data_sheet(self, wb: Workbook) -> None:
        """Create ledger overview data sheet"""
        ws = wb.create_sheet("台账总览")

        with get_session() as session:
            repo = LedgerRepository(session)
            ledgers = repo.get_all_ledgers()

            headers = ["名称", "规格", "类别", "单位", "当前库存", "最小库存",
                      "累计入库", "累计出库", "净入库量", "状态", "物料编码", "采购日期", "ID"]

            # Header row
            for col, header in enumerate(headers, 1):
                ws.cell(row=1, column=col, value=header)

            # Data rows
            for row_idx, l in enumerate(ledgers, 2):
                inbounds = repo.get_inbound_history(l.id, days=99999)
                outbounds = repo.get_outbound_history(l.id, days=99999)
                cumulative_in = sum(ib.quantity for ib in inbounds) if inbounds else Decimal(0)
                cumulative_out = sum(ob.quantity for ob in outbounds) if outbounds else Decimal(0)
                net_in = cumulative_in - cumulative_out
                status = "正常" if l.current_stock >= l.min_stock else "库存不足"

                ws.cell(row=row_idx, column=1, value=l.name)
                ws.cell(row=row_idx, column=2, value=l.specification)
                ws.cell(row=row_idx, column=3, value=l.category)
                ws.cell(row=row_idx, column=4, value=l.unit)
                ws.cell(row=row_idx, column=5, value=float(l.current_stock))
                ws.cell(row=row_idx, column=6, value=float(l.min_stock))
                ws.cell(row=row_idx, column=7, value=float(cumulative_in))
                ws.cell(row=row_idx, column=8, value=float(cumulative_out))
                ws.cell(row=row_idx, column=9, value=float(net_in))
                ws.cell(row=row_idx, column=10, value=status)
                ws.cell(row=row_idx, column=11, value=l.material_code or "")
                ws.cell(row=row_idx, column=12, value=l.purchase_date.isoformat() if l.purchase_date else "")
                ws.cell(row=row_idx, column=13, value=str(l.id))

        # Freeze top row
        ws.freeze_panes = "A2"

    def _create_inbound_data_sheet(self, wb: Workbook) -> None:
        """Create inbound records data sheet"""
        ws = wb.create_sheet("入库记录数据")

        with get_session() as session:
            repo = LedgerRepository(session)
            inbounds = repo.get_all_inbounds(days=99999)

            headers = ["物料名称", "序号", "日期", "时间", "数量", "单位",
                      "累计入库", "供应商", "操作人", "备注"]

            for col, header in enumerate(headers, 1):
                ws.cell(row=1, column=col, value=header)

            for row_idx, ib in enumerate(inbounds, 2):
                ledger = repo.get_ledger_by_id(ib.ledger_id)
                ws.cell(row=row_idx, column=1, value=ledger.name if ledger else "")
                ws.cell(row=row_idx, column=2, value=ib.inbound_sequence)
                ws.cell(row=row_idx, column=3, value=ib.inbound_date.isoformat())
                ws.cell(row=row_idx, column=4, value=str(ib.inbound_time) if ib.inbound_time else "")
                ws.cell(row=row_idx, column=5, value=float(ib.quantity))
                ws.cell(row=row_idx, column=6, value=ledger.unit if ledger else "")
                ws.cell(row=row_idx, column=7, value=float(ib.cumulative_in))
                ws.cell(row=row_idx, column=8, value=ib.supplier)
                ws.cell(row=row_idx, column=9, value=ib.inbound_operator)
                ws.cell(row=row_idx, column=10, value=ib.notes)

        ws.freeze_panes = "A2"

    def _create_outbound_data_sheet(self, wb: Workbook) -> None:
        """Create outbound records data sheet"""
        ws = wb.create_sheet("出库记录数据")

        with get_session() as session:
            repo = LedgerRepository(session)
            outbounds = repo.get_all_outbounds(days=99999)

            headers = ["物料名称", "序号", "日期", "时间", "数量", "单位",
                      "累计出库", "用途", "领用人", "操作人", "备注"]

            for col, header in enumerate(headers, 1):
                ws.cell(row=1, column=col, value=header)

            for row_idx, ob in enumerate(outbounds, 2):
                ledger = repo.get_ledger_by_id(ob.ledger_id)
                ws.cell(row=row_idx, column=1, value=ledger.name if ledger else "")
                ws.cell(row=row_idx, column=2, value=ob.outbound_sequence)
                ws.cell(row=row_idx, column=3, value=ob.outbound_date.isoformat())
                ws.cell(row=row_idx, column=4, value=str(ob.outbound_time) if ob.outbound_time else "")
                ws.cell(row=row_idx, column=5, value=float(ob.quantity))
                ws.cell(row=row_idx, column=6, value=ledger.unit if ledger else "")
                ws.cell(row=row_idx, column=7, value=float(ob.cumulative_out))
                ws.cell(row=row_idx, column=8, value=ob.usage)
                ws.cell(row=row_idx, column=9, value=ob.receiver)
                ws.cell(row=row_idx, column=10, value=ob.outbound_operator)
                ws.cell(row=row_idx, column=11, value=ob.notes)

        ws.freeze_panes = "A2"
