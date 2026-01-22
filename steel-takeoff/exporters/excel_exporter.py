"""
Excel Exporter
Export rebar schedules to Excel format
"""

from pathlib import Path
from typing import Optional
from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from domain import RebarSchedule, UNIT_WEIGHTS
from config import ExportSettings
from services import CalculationService
from .base import BaseExporter


class ExcelExporter(BaseExporter):
    """Exports schedule to Excel format"""
    
    # Style constants
    HEADER_FILL = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
    SUBHEADER_FILL = PatternFill(start_color="D6DCE4", end_color="D6DCE4", fill_type="solid")
    TOTAL_FILL = PatternFill(start_color="FFC000", end_color="FFC000", fill_type="solid")
    TOTAL_FONT = Font(bold=True, size=12)
    
    THIN_BORDER = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    def __init__(self, settings: Optional[ExportSettings] = None):
        super().__init__(settings)
        self._calculator = CalculationService()
    
    @property
    def name(self) -> str:
        return "Excel"
    
    def export(self, schedule: RebarSchedule, output_path: Optional[Path] = None) -> Path:
        """
        Export schedule to Excel file.
        
        Args:
            schedule: RebarSchedule to export
            output_path: Optional output path. If None, generates based on project name.
            
        Returns:
            Path to the created Excel file
        """
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{schedule.project_name or 'rebar_schedule'}_{timestamp}.xlsx"
            output_path = Path(filename)
        
        output_path = Path(output_path)
        
        wb = Workbook()
        
        # Create main schedule sheet
        ws_schedule = wb.active
        ws_schedule.title = "Rebar Schedule"
        self._create_schedule_sheet(ws_schedule, schedule)
        
        # Create summary sheet
        if self.settings.excel_include_summary:
            ws_summary = wb.create_sheet("Summary")
            self._create_summary_sheet(ws_summary, schedule)
        
        wb.save(output_path)
        return output_path
    
    def _create_schedule_sheet(self, ws, schedule: RebarSchedule) -> None:
        """Create the main schedule sheet"""
        # Title
        ws.merge_cells('A1:H1')
        ws['A1'] = "STEEL QUANTITY TAKEOFF - ÇELİK METRAJ"
        ws['A1'].font = Font(bold=True, size=16)
        ws['A1'].alignment = Alignment(horizontal='center')
        
        # Project info
        ws['A2'] = f"Project: {schedule.project_name or 'N/A'}"
        ws['A3'] = f"File: {schedule.drawing_file or 'N/A'}"
        ws['A4'] = f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Determine if this is POZ-based or text-based data
        has_poz_data = any(
            item.position and item.position != 'NO_POZ' 
            for item in schedule.items
        )
        
        if has_poz_data:
            # POZ-based: show POZ NO, ÇAP, ADET, BOY, etc.
            self._create_poz_based_sheet(ws, schedule)
        else:
            # Text-based: group by diameter + type like original tool
            self._create_text_based_sheet(ws, schedule)
    
    def _create_poz_based_sheet(self, ws, schedule: RebarSchedule) -> None:
        """Create sheet for POZ-based data"""
        headers = [
            ('POZ NO', 10),
            ('ÇAP (mm)', 10),
            ('ADET', 10),
            ('BOY (cm)', 12),
            ('TOPLAM BOY (m)', 15),
            ('BİRİM AĞIRLIK (kg/m)', 18),
            ('AĞIRLIK (kg)', 15),
            ('YER', 20),
        ]
        
        header_row = 6
        for col, (header, width) in enumerate(headers, 1):
            cell = ws.cell(row=header_row, column=col, value=header)
            cell.font = self.HEADER_FONT
            cell.fill = self.HEADER_FILL
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = self.THIN_BORDER
            ws.column_dimensions[get_column_letter(col)].width = width
        
        # Data rows
        breakdown = self._calculator.get_position_breakdown(schedule)
        
        for row_idx, item in enumerate(breakdown, header_row + 1):
            ws.cell(row=row_idx, column=1, value=item['position']).border = self.THIN_BORDER
            ws.cell(row=row_idx, column=2, value=item['diameter']).border = self.THIN_BORDER
            ws.cell(row=row_idx, column=3, value=item['quantity']).border = self.THIN_BORDER
            ws.cell(row=row_idx, column=4, value=item['length_cm']).border = self.THIN_BORDER
            ws.cell(row=row_idx, column=5, value=f'=C{row_idx}*D{row_idx}/100').border = self.THIN_BORDER
            ws.cell(row=row_idx, column=6, value=item['unit_weight_kg_m']).border = self.THIN_BORDER
            ws.cell(row=row_idx, column=7, value=f'=E{row_idx}*F{row_idx}').border = self.THIN_BORDER
            ws.cell(row=row_idx, column=8, value=item['location']).border = self.THIN_BORDER
            
            ws.cell(row=row_idx, column=5).number_format = '#,##0.00'
            ws.cell(row=row_idx, column=6).number_format = '0.000'
            ws.cell(row=row_idx, column=7).number_format = '#,##0.00'
        
        # Total row
        self._add_total_row(ws, header_row, len(breakdown), poz_based=True)
    
    def _create_text_based_sheet(self, ws, schedule: RebarSchedule) -> None:
        """Create sheet for text-based data (grouped by diameter + type)"""
        # Headers matching original tool output
        headers = [
            ('ÇAP', 8),
            ('TİP', 15),
            ('DEMİR ADEDİ', 12),
            ('TOPLAM BOY (m)', 16),
            ('BİRİM AĞIRLIK (kg/m)', 20),
            ('AĞIRLIK (kg)', 15),
        ]
        
        header_row = 6
        for col, (header, width) in enumerate(headers, 1):
            cell = ws.cell(row=header_row, column=col, value=header)
            cell.font = self.HEADER_FONT
            cell.fill = self.HEADER_FILL
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = self.THIN_BORDER
            ws.column_dimensions[get_column_letter(col)].width = width
        
        # Data rows - grouped by diameter + type
        breakdown = self._calculator.get_diameter_type_breakdown(schedule)
        
        for row_idx, item in enumerate(breakdown, header_row + 1):
            ws.cell(row=row_idx, column=1, value=item['diameter_str']).border = self.THIN_BORDER
            ws.cell(row=row_idx, column=2, value=item['location']).border = self.THIN_BORDER
            ws.cell(row=row_idx, column=3, value=item['quantity']).border = self.THIN_BORDER
            ws.cell(row=row_idx, column=4, value=item['total_length_m']).border = self.THIN_BORDER
            ws.cell(row=row_idx, column=5, value=item['unit_weight_kg_m']).border = self.THIN_BORDER
            ws.cell(row=row_idx, column=6, value=item['total_weight_kg']).border = self.THIN_BORDER
            
            ws.cell(row=row_idx, column=4).number_format = '#,##0.00'
            ws.cell(row=row_idx, column=5).number_format = '0.000'
            ws.cell(row=row_idx, column=6).number_format = '#,##0.00'
        
        # Total row
        self._add_total_row(ws, header_row, len(breakdown), poz_based=False)
    
    def _add_total_row(self, ws, header_row: int, num_items: int, poz_based: bool) -> None:
        """Add total row to the sheet"""
        total_row = header_row + num_items + 1
        
        ws.cell(row=total_row, column=1, value="TOPLAM / TOTAL").font = self.TOTAL_FONT
        
        if poz_based:
            ws.merge_cells(f'A{total_row}:D{total_row}')
            # Total length
            ws.cell(row=total_row, column=5, value=f'=SUM(E{header_row+1}:E{total_row-1})')
            ws.cell(row=total_row, column=5).number_format = '#,##0.00'
            ws.cell(row=total_row, column=5).font = self.TOTAL_FONT
            ws.cell(row=total_row, column=5).fill = self.TOTAL_FILL
            # Total weight
            ws.cell(row=total_row, column=7, value=f'=SUM(G{header_row+1}:G{total_row-1})')
            ws.cell(row=total_row, column=7).number_format = '#,##0.00'
            ws.cell(row=total_row, column=7).font = self.TOTAL_FONT
            ws.cell(row=total_row, column=7).fill = self.TOTAL_FILL
            # Borders
            for col in range(1, 9):
                ws.cell(row=total_row, column=col).border = self.THIN_BORDER
        else:
            ws.merge_cells(f'A{total_row}:C{total_row}')
            # Total length
            ws.cell(row=total_row, column=4, value=f'=SUM(D{header_row+1}:D{total_row-1})')
            ws.cell(row=total_row, column=4).number_format = '#,##0.00'
            ws.cell(row=total_row, column=4).font = self.TOTAL_FONT
            ws.cell(row=total_row, column=4).fill = self.TOTAL_FILL
            # Total weight
            ws.cell(row=total_row, column=6, value=f'=SUM(F{header_row+1}:F{total_row-1})')
            ws.cell(row=total_row, column=6).number_format = '#,##0.00'
            ws.cell(row=total_row, column=6).font = self.TOTAL_FONT
            ws.cell(row=total_row, column=6).fill = self.TOTAL_FILL
            # Borders
            for col in range(1, 7):
                ws.cell(row=total_row, column=col).border = self.THIN_BORDER
    
    def _create_summary_sheet(self, ws, schedule: RebarSchedule) -> None:
        """Create the summary sheet with breakdown by diameter"""
        # Title
        ws.merge_cells('A1:E1')
        ws['A1'] = "DIAMETER SUMMARY - ÇAP BAZINDA ÖZET"
        ws['A1'].font = Font(bold=True, size=14)
        ws['A1'].alignment = Alignment(horizontal='center')
        
        # Headers
        headers = [
            ('ÇAP (mm)', 12),
            ('TOPLAM BOY (m)', 18),
            ('BİRİM AĞIRLIK (kg/m)', 20),
            ('TOPLAM AĞIRLIK (kg)', 20),
            ('ORAN (%)', 12),
        ]
        
        header_row = 3
        for col, (header, width) in enumerate(headers, 1):
            cell = ws.cell(row=header_row, column=col, value=header)
            cell.font = self.HEADER_FONT
            cell.fill = self.HEADER_FILL
            cell.alignment = Alignment(horizontal='center')
            cell.border = self.THIN_BORDER
            ws.column_dimensions[get_column_letter(col)].width = width
        
        # Data
        breakdown = self._calculator.get_diameter_breakdown(schedule)
        total_weight = schedule.total_weight_kg
        
        for row_idx, item in enumerate(breakdown, header_row + 1):
            ws.cell(row=row_idx, column=1, value=f"ø{item['diameter']}").border = self.THIN_BORDER
            ws.cell(row=row_idx, column=2, value=item['total_length_m']).border = self.THIN_BORDER
            ws.cell(row=row_idx, column=3, value=item['unit_weight_kg_m']).border = self.THIN_BORDER
            ws.cell(row=row_idx, column=4, value=item['total_weight_kg']).border = self.THIN_BORDER
            
            # Percentage formula
            pct = (item['total_weight_kg'] / total_weight * 100) if total_weight > 0 else 0
            ws.cell(row=row_idx, column=5, value=pct).border = self.THIN_BORDER
            
            # Formatting
            ws.cell(row=row_idx, column=2).number_format = '#,##0.00'
            ws.cell(row=row_idx, column=3).number_format = '0.000'
            ws.cell(row=row_idx, column=4).number_format = '#,##0.00'
            ws.cell(row=row_idx, column=5).number_format = '0.0'
        
        # Total row
        total_row = header_row + len(breakdown) + 1
        ws.cell(row=total_row, column=1, value="TOPLAM").font = self.TOTAL_FONT
        ws.cell(row=total_row, column=2, value=f'=SUM(B{header_row+1}:B{total_row-1})')
        ws.cell(row=total_row, column=4, value=f'=SUM(D{header_row+1}:D{total_row-1})')
        ws.cell(row=total_row, column=5, value=f'=SUM(E{header_row+1}:E{total_row-1})')
        
        for col in range(1, 6):
            ws.cell(row=total_row, column=col).border = self.THIN_BORDER
            ws.cell(row=total_row, column=col).fill = self.TOTAL_FILL
            ws.cell(row=total_row, column=col).font = self.TOTAL_FONT
        
        ws.cell(row=total_row, column=2).number_format = '#,##0.00'
        ws.cell(row=total_row, column=4).number_format = '#,##0.00'
        ws.cell(row=total_row, column=5).number_format = '0.0'
        
        # Tonnage
        tonnage_row = total_row + 2
        ws.cell(row=tonnage_row, column=1, value="TOPLAM (ton)").font = Font(bold=True, size=12, color="FF0000")
        ws.cell(row=tonnage_row, column=4, value=f'=D{total_row}/1000')
        ws.cell(row=tonnage_row, column=4).font = Font(bold=True, size=12, color="FF0000")
        ws.cell(row=tonnage_row, column=4).number_format = '#,##0.000'
