"""
Steel Quantity Takeoff Application
Reads DXF files and extracts rebar quantities from POZ blocks
"""

import sys
import re
from pathlib import Path
from rich.console import Console
from rich.table import Table
import ezdxf

console = Console()

# Unit weights kg/m for standard rebar diameters
UNIT_WEIGHTS = {
    6: 0.222, 8: 0.395, 10: 0.617, 12: 0.888,
    14: 1.208, 16: 1.578, 18: 1.998, 20: 2.466,
    22: 2.984, 25: 3.853, 28: 4.834, 32: 6.313
}


def extract_rebar_from_poz_blocks(dxf_path: Path) -> list:
    """Extract rebar data from POZ blocks in DXF file"""
    doc = ezdxf.readfile(str(dxf_path))
    msp = doc.modelspace()
    
    rebar_entries = []
    
    for entity in msp:
        if entity.dxftype() == 'INSERT' and entity.dxf.name.lower() == 'poz':
            attribs = {a.dxf.tag: a.dxf.text for a in entity.attribs}
            rebar_entries.append(attribs)
    
    return rebar_entries


def parse_quantity(adet_str: str) -> int:
    """Parse quantity string, handles '2x3' format"""
    if not adet_str:
        return 0
    if 'x' in adet_str.lower():
        parts = adet_str.lower().split('x')
        try:
            return int(parts[0]) * int(parts[1])
        except:
            return 0
    try:
        return int(adet_str)
    except:
        return 0


def parse_length(boy_str: str) -> int:
    """Parse length string, extracts number from 'L=800' format"""
    if not boy_str:
        return 0
    match = re.search(r'(\d+)', boy_str)
    if match:
        return int(match.group(1))
    return 0


def calculate_rebar_schedule(rebar_entries: list) -> dict:
    """Calculate rebar schedule grouped by POZ number"""
    results = {}
    
    for entry in rebar_entries:
        poz = entry.get('POZ', '')
        adet = parse_quantity(entry.get('ADET', '0'))
        cap = int(entry.get('CAP', '12')) if entry.get('CAP', '').isdigit() else 12
        boy = parse_length(entry.get('BOY', ''))
        
        if poz not in results:
            results[poz] = {
                'poz': poz,
                'cap': cap,
                'boy_cm': boy,
                'adet': 0,
                'yer': entry.get('YER', ''),
                'aralik': entry.get('ARALIK', '')
            }
        
        results[poz]['adet'] += adet
    
    return results


def display_results(results: dict):
    """Display rebar schedule as a formatted table"""
    
    console.print("\n[bold green]" + "=" * 95 + "[/bold green]")
    console.print("[bold green]METRAJ TABLOSU / QUANTITY TABLE[/bold green]")
    console.print("[bold green]" + "=" * 95 + "[/bold green]\n")
    
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("POZ NO", justify="right", style="cyan")
    table.add_column("ÇAP", justify="center", style="magenta")
    table.add_column("DEMİR ADEDİ", justify="right")
    table.add_column("DEMİR BOYU (cm)", justify="right")
    table.add_column("TOPLAM BOY (m)", justify="right", style="green")
    table.add_column("BİRİM AĞIRLIK (kg/m)", justify="right")
    table.add_column("AĞIRLIK (kg)", justify="right", style="yellow")
    
    totals_by_diameter = {}
    
    for poz in sorted(results.keys(), key=lambda x: int(x) if x.isdigit() else 0):
        r = results[poz]
        
        toplam_m = (r['adet'] * r['boy_cm']) / 100
        birim_kg = UNIT_WEIGHTS.get(r['cap'], 0)
        agirlik = toplam_m * birim_kg
        
        # Track totals by diameter
        if r['cap'] not in totals_by_diameter:
            totals_by_diameter[r['cap']] = {'length': 0, 'weight': 0}
        totals_by_diameter[r['cap']]['length'] += toplam_m
        totals_by_diameter[r['cap']]['weight'] += agirlik
        
        table.add_row(
            r['poz'],
            f"ø{r['cap']}",
            str(r['adet']),
            str(r['boy_cm']),
            f"{toplam_m:.2f}",
            f"{birim_kg:.3f}",
            f"{agirlik:.2f}"
        )
    
    console.print(table)
    
    # Print totals by diameter
    console.print("\n[bold]" + "-" * 95 + "[/bold]")
    
    grand_total_weight = 0
    for cap in sorted(totals_by_diameter.keys()):
        t = totals_by_diameter[cap]
        grand_total_weight += t['weight']
        console.print(f"[cyan]Ø{cap}[/cyan] TOPLAM BOY: [green]{t['length']:,.2f} m[/green]  |  "
                     f"BİRİM AĞIRLIK: {UNIT_WEIGHTS[cap]:.3f} kg/m  |  "
                     f"AĞIRLIK: [yellow]{t['weight']:,.2f} kg[/yellow]")
    
    console.print("[bold]" + "=" * 95 + "[/bold]")
    console.print(f"[bold red]TOPLAM AĞIRLIK / TOTAL WEIGHT: {grand_total_weight:,.2f} kg[/bold red]")
    console.print("[bold]" + "=" * 95 + "[/bold]\n")


def main():
    """Main entry point"""
    console.print("\n[bold blue]╔══════════════════════════════════════╗[/bold blue]")
    console.print("[bold blue]║     STEEL QUANTITY TAKEOFF           ║[/bold blue]")
    console.print("[bold blue]║     Çelik Metraj Hesaplama           ║[/bold blue]")
    console.print("[bold blue]╚══════════════════════════════════════╝[/bold blue]\n")
    
    # Get DXF file path from command line or use default
    if len(sys.argv) > 1:
        dxf_path = Path(sys.argv[1])
    else:
        dxf_path = Path(r"C:\Users\sercan\Desktop\Drawing2.dxf")
    
    if not dxf_path.exists():
        console.print(f"[red]Hata: DXF dosyası bulunamadı: {dxf_path}[/red]")
        console.print("[yellow]Kullanım: python main.py <dxf_dosyasi.dxf>[/yellow]")
        return
    
    console.print(f"[green]Dosya yükleniyor:[/green] {dxf_path}")
    
    # Extract rebar data
    rebar_entries = extract_rebar_from_poz_blocks(dxf_path)
    
    if not rebar_entries:
        console.print("[yellow]Uyarı: DXF dosyasında POZ bloğu bulunamadı.[/yellow]")
        return
    
    console.print(f"[green]Bulunan POZ blokları:[/green] {len(rebar_entries)}")
    
    # Calculate schedule
    results = calculate_rebar_schedule(rebar_entries)
    console.print(f"[green]Benzersiz POZ numaraları:[/green] {len(results)}")
    
    # Display results
    display_results(results)


if __name__ == "__main__":
    main()