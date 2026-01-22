"""
Console Exporter
Rich console output for rebar schedules
"""

from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from domain import RebarSchedule, UNIT_WEIGHTS
from config import ExportSettings
from services import CalculationService
from .base import BaseExporter


class ConsoleExporter(BaseExporter):
    """Exports schedule to console with rich formatting"""
    
    def __init__(self, settings: Optional[ExportSettings] = None):
        super().__init__(settings)
        self.console = Console()
        self._calculator = CalculationService()
    
    @property
    def name(self) -> str:
        return "Console"
    
    def export(self, schedule: RebarSchedule, output_path: Optional[Path] = None) -> None:
        """Export schedule to console"""
        self._print_header(schedule)
        self._print_detail_table(schedule)
        self._print_diameter_summary(schedule)
        self._print_total(schedule)
    
    def _print_header(self, schedule: RebarSchedule) -> None:
        """Print header banner"""
        self.console.print()
        self.console.print(Panel.fit(
            "[bold blue]STEEL QUANTITY TAKEOFF[/bold blue]\n"
            "[bold blue]Çelik Metraj Hesaplama[/bold blue]",
            border_style="blue"
        ))
        self.console.print()
        
        if schedule.project_name:
            self.console.print(f"[green]Proje / Project:[/green] {schedule.project_name}")
        if schedule.drawing_file:
            self.console.print(f"[green]Dosya / File:[/green] {schedule.drawing_file}")
        self.console.print()
    
    def _print_detail_table(self, schedule: RebarSchedule) -> None:
        """Print detailed position table"""
        self.console.print("[bold]" + "=" * 100 + "[/bold]")
        self.console.print("[bold]METRAJ TABLOSU / QUANTITY TABLE[/bold]")
        self.console.print("[bold]" + "=" * 100 + "[/bold]")
        self.console.print()
        
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("POZ NO", justify="right", style="cyan", width=8)
        table.add_column("ÇAP", justify="center", style="magenta", width=6)
        table.add_column("ADET", justify="right", width=8)
        table.add_column("BOY (cm)", justify="right", width=10)
        table.add_column("TOPLAM (m)", justify="right", style="green", width=12)
        table.add_column("BR. AĞIRLIK", justify="right", width=12)
        table.add_column("AĞIRLIK (kg)", justify="right", style="yellow", width=12)
        table.add_column("YER", justify="left", width=15)
        
        breakdown = self._calculator.get_position_breakdown(schedule)
        
        for item in breakdown:
            table.add_row(
                item['position'],
                item['diameter_str'],
                str(item['quantity']),
                f"{item['length_cm']:.0f}",
                f"{item['total_length_m']:.2f}",
                f"{item['unit_weight_kg_m']:.3f}",
                f"{item['total_weight_kg']:.2f}",
                item['location']
            )
        
        self.console.print(table)
        self.console.print()
    
    def _print_diameter_summary(self, schedule: RebarSchedule) -> None:
        """Print summary by diameter"""
        self.console.print("[bold]" + "-" * 100 + "[/bold]")
        self.console.print("[bold]ÇAP BAZINDA ÖZET / SUMMARY BY DIAMETER[/bold]")
        self.console.print("[bold]" + "-" * 100 + "[/bold]")
        
        breakdown = self._calculator.get_diameter_breakdown(schedule)
        
        for item in breakdown:
            self.console.print(
                f"[cyan]{item['diameter_str']:>4}[/cyan]  "
                f"TOPLAM BOY: [green]{item['total_length_m']:>10,.2f} m[/green]  |  "
                f"BİRİM AĞIRLIK: {item['unit_weight_kg_m']:.3f} kg/m  |  "
                f"AĞIRLIK: [yellow]{item['total_weight_kg']:>10,.2f} kg[/yellow]"
            )
        
        self.console.print()
    
    def _print_total(self, schedule: RebarSchedule) -> None:
        """Print grand total"""
        self.console.print("[bold]" + "=" * 100 + "[/bold]")
        
        total_weight = schedule.total_weight_kg
        total_length = schedule.total_length_m
        
        self.console.print(
            f"[bold]TOPLAM BOY / TOTAL LENGTH: [green]{total_length:,.2f} m[/green][/bold]"
        )
        self.console.print(
            f"[bold red]TOPLAM AĞIRLIK / TOTAL WEIGHT: {total_weight:,.2f} kg[/bold red]"
        )
        self.console.print(
            f"[bold red]                              {total_weight/1000:,.3f} ton[/bold red]"
        )
        
        self.console.print("[bold]" + "=" * 100 + "[/bold]")
        self.console.print()
    
    def print_file_info(self, info: dict) -> None:
        """Print file information summary"""
        self.console.print()
        self.console.print(Panel.fit(
            "[bold]DXF FILE INFORMATION[/bold]",
            border_style="blue"
        ))
        
        self.console.print(f"[green]File:[/green] {info['file']}")
        self.console.print(f"[green]Total Entities:[/green] {info['total_entities']}")
        self.console.print(f"[green]POZ Blocks:[/green] {info['poz_block_count']}")
        self.console.print(f"[green]Text Entities:[/green] {info['text_entity_count']}")
        
        self.console.print()
        self.console.print("[bold]Entity Counts:[/bold]")
        for entity_type, count in sorted(info['entity_counts'].items(), key=lambda x: -x[1]):
            self.console.print(f"  {entity_type}: {count}")
        
        self.console.print()
        self.console.print("[bold]Layers:[/bold]")
        for layer in sorted(info['layers']):
            marker = "[green]►[/green]" if layer in info['rebar_layers'] else " "
            self.console.print(f"  {marker} {layer}")
        
        if info['blocks']:
            self.console.print()
            self.console.print("[bold]Block Definitions:[/bold]")
            for block in sorted(info['blocks']):
                self.console.print(f"  • {block}")
        
        self.console.print()
