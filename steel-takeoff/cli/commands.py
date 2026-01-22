"""
CLI Commands
Command handlers for the CLI application
"""

from pathlib import Path
from typing import Optional
import sys

from rich.console import Console

from services import TakeoffService
from exporters import ConsoleExporter, ExcelExporter
from config import AppSettings


console = Console()


def cmd_analyze(file_path: str, export_excel: bool = False, output_dir: Optional[str] = None) -> None:
    """
    Analyze a DXF file and display/export rebar schedule.
    
    Args:
        file_path: Path to the DXF file
        export_excel: Whether to export to Excel
        output_dir: Directory for Excel output
    """
    path = Path(file_path)
    
    if not path.exists():
        console.print(f"[red]Error: File not found: {path}[/red]")
        sys.exit(1)
    
    if path.suffix.lower() != '.dxf':
        console.print(f"[red]Error: Unsupported file type: {path.suffix}[/red]")
        sys.exit(1)
    
    console.print(f"[blue]Analyzing: {path.name}[/blue]")
    
    # Create service and analyze
    service = TakeoffService()
    
    try:
        schedule = service.process_file(path)
    except Exception as e:
        console.print(f"[red]Error analyzing file: {e}[/red]")
        sys.exit(1)
    
    if not schedule.items:
        console.print("[yellow]Warning: No rebar items found in the file.[/yellow]")
        console.print("[yellow]The file may not contain POZ blocks or recognized text annotations.[/yellow]")
    
    # Console output
    console_exporter = ConsoleExporter()
    console_exporter.export(schedule)
    
    # Excel export
    if export_excel:
        excel_exporter = ExcelExporter()
        
        if output_dir:
            output_path = Path(output_dir) / f"{path.stem}_schedule.xlsx"
        else:
            output_path = path.with_suffix('.xlsx')
        
        try:
            result_path = excel_exporter.export(schedule, output_path)
            console.print(f"[green]Excel exported to: {result_path}[/green]")
        except Exception as e:
            console.print(f"[red]Error exporting Excel: {e}[/red]")


def cmd_info(file_path: str) -> None:
    """
    Display information about a DXF file without full analysis.
    
    Args:
        file_path: Path to the DXF file
    """
    path = Path(file_path)
    
    if not path.exists():
        console.print(f"[red]Error: File not found: {path}[/red]")
        sys.exit(1)
    
    service = TakeoffService()
    
    try:
        info = service.get_file_info(path)
    except Exception as e:
        console.print(f"[red]Error reading file: {e}[/red]")
        sys.exit(1)
    
    console_exporter = ConsoleExporter()
    console_exporter.print_file_info(info)


def cmd_batch(directory: str, export_excel: bool = True, output_dir: Optional[str] = None) -> None:
    """
    Process all DXF files in a directory.
    
    Args:
        directory: Directory containing DXF files
        export_excel: Whether to export to Excel
        output_dir: Directory for output files
    """
    dir_path = Path(directory)
    
    if not dir_path.exists():
        console.print(f"[red]Error: Directory not found: {dir_path}[/red]")
        sys.exit(1)
    
    if not dir_path.is_dir():
        console.print(f"[red]Error: Path is not a directory: {dir_path}[/red]")
        sys.exit(1)
    
    dxf_files = list(dir_path.glob("*.dxf")) + list(dir_path.glob("*.DXF"))
    
    if not dxf_files:
        console.print(f"[yellow]No DXF files found in {dir_path}[/yellow]")
        return
    
    console.print(f"[blue]Found {len(dxf_files)} DXF files[/blue]")
    
    output_path = Path(output_dir) if output_dir else dir_path
    
    service = TakeoffService()
    excel_exporter = ExcelExporter()
    
    total_weight = 0.0
    
    for dxf_file in dxf_files:
        console.print(f"\n[cyan]Processing: {dxf_file.name}[/cyan]")
        
        try:
            schedule = service.process_file(dxf_file)
            weight = schedule.total_weight_kg
            total_weight += weight
            
            console.print(f"  Items: {len(schedule.items)}")
            console.print(f"  Weight: [yellow]{weight:,.2f} kg[/yellow]")
            
            if export_excel:
                excel_path = output_path / f"{dxf_file.stem}_schedule.xlsx"
                excel_exporter.export(schedule, excel_path)
                console.print(f"  Excel: {excel_path.name}")
        
        except Exception as e:
            console.print(f"  [red]Error: {e}[/red]")
    
    console.print(f"\n[bold]Total weight from all files: [yellow]{total_weight:,.2f} kg[/yellow] ({total_weight/1000:,.3f} ton)[/bold]")
