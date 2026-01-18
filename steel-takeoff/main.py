"""
Steel Quantity Takeoff Application
Reads DXF files and extracts rebar quantities from POZ blocks or TEXT annotations
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


# ============================================================
# METHOD 1: Extract from POZ Blocks (like Drawing1.dxf)
# ============================================================

def extract_rebar_from_poz_blocks(msp) -> list:
    """Extract rebar data from POZ blocks in DXF file"""
    rebar_entries = []
    
    for entity in msp:
        if entity.dxftype() == 'INSERT' and entity.dxf.name.lower() == 'poz':
            attribs = {a.dxf.tag: a.dxf.text for a in entity.attribs}
            rebar_entries.append(attribs)
    
    return rebar_entries


# ============================================================
# METHOD 2: Extract from TEXT Annotations (like Drawing3.dxf)
# ============================================================

def extract_rebar_from_text(msp) -> list:
    """Extract rebar data from TEXT annotations"""
    rebar_entries = []
    
    # Patterns for text-based rebar annotations
    # Note: [ƒφøΦ\[] matches various diameter symbols including [ used in some drawings
    patterns = [
        # === BEAM PATTERNS (Kiriş) ===
        # Pattern 1: "16ƒ10/20 etr. l=206" - stirrups with spacing
        (r'(\d+)[ƒφøΦ\[](\d+)/(\d+)\s+etr\.\s+l=\s*(\d+)', 'etriye'),
        
        # Pattern 2: "3ƒ14 ila. l= 250" - additional bars with length
        (r'(\d+)[ƒφøΦ\[](\d+)\s+ila\.\s+l=\s*(\d+)', 'ilave'),
        
        # Pattern 3: "3ƒ14 mon. l= 735" - montage bars with length
        (r'(\d+)[ƒφøΦ\[](\d+)\s+mon\.\s+l=\s*(\d+)', 'montaj'),
        
        # Pattern 4: "4ƒ16 gov. l= 305" - body bars with length
        (r'(\d+)[ƒφøΦ\[](\d+)\s+gov\.\s+l=\s*(\d+)', 'govde'),
        
        # Pattern 5: "2ƒ14 l= 320" - simple bars with length (beam)
        (r'(\d+)[ƒφøΦ\[](\d+)\s+l=\s*(\d+)(?!\s*\()', 'pilye'),
        
        # === SLAB PATTERNS (Döşeme) ===
        # Pattern 6: "18ƒ8/29  l=265 (alt)" - slab bottom reinforcement
        (r'(\d+)[ƒφøΦ\[](\d+)/(\d+)\s+l=\s*(\d+)\s*\(alt\)', 'döşeme_alt'),
        
        # Pattern 7: "10ƒ8/24  l=105 (ust)" - slab top reinforcement  
        (r'(\d+)[ƒφøΦ\[](\d+)/(\d+)\s+l=\s*(\d+)\s*\((?:ust|üst)\)', 'döşeme_üst'),
        
        # Pattern 8: "18ƒ8/29  l=470" - slab reinforcement without position
        (r'(\d+)[ƒφøΦ\[](\d+)/(\d+)\s+l=\s*(\d+)(?!\s*\()', 'döşeme'),
        
        # Pattern 9: "ƒ12/20  l=945 (alt)" - slab rebar without quantity (distributed)
        (r'[ƒφøΦ\[](\d+)/(\d+)\s*l=\s*(\d+)\s*\(alt\)', 'döşeme_alt_dist'),
        
        # Pattern 10: "ƒ12/20  l=1115 (ust)" - slab rebar without quantity (distributed)
        (r'[ƒφøΦ\[](\d+)/(\d+)\s*l=\s*(\d+)\s*\((?:ust|üst)\)', 'döşeme_üst_dist'),
    ]
    
    for entity in msp:
        if entity.dxftype() == 'TEXT':
            layer = entity.dxf.layer
            text = entity.dxf.text.strip()
            
            # Only process rebar-related layers
            layer_upper = layer.upper()
            if not any(x in layer_upper for x in ['REBAR', 'DONATI', 'DONATL']):
                continue
            
            # Try each pattern
            for pattern, tip in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    
                    if tip == 'etriye':
                        # Stirrups: qty, diameter, spacing, length
                        rebar_entries.append({
                            'ADET': groups[0],
                            'CAP': groups[1],
                            'ARALIK': f"/{groups[2]}",
                            'BOY': f"L={groups[3]}",
                            'YER': tip,
                            'SOURCE': 'TEXT'
                        })
                    elif tip in ['döşeme_alt', 'döşeme_üst', 'döşeme']:
                        # Slab reinforcement: qty, diameter, spacing, length
                        rebar_entries.append({
                            'ADET': groups[0],
                            'CAP': groups[1],
                            'ARALIK': f"/{groups[2]}",
                            'BOY': f"L={groups[3]}",
                            'YER': tip,
                            'SOURCE': 'TEXT'
                        })
                    elif tip in ['döşeme_alt_dist', 'döşeme_üst_dist']:
                        # Distributed slab rebar without quantity: diameter, spacing, length
                        # Skip these - they are typically reference annotations
                        pass
                    else:
                        # Other bars: qty, diameter, length
                        rebar_entries.append({
                            'ADET': groups[0],
                            'CAP': groups[1],
                            'ARALIK': '',
                            'BOY': f"L={groups[2]}",
                            'YER': tip,
                            'SOURCE': 'TEXT'
                        })
                    break  # Found a match, no need to try other patterns
    
    return rebar_entries


# ============================================================
# Parsing Helpers
# ============================================================

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


# ============================================================
# Schedule Calculations
# ============================================================

def calculate_rebar_schedule_by_poz(rebar_entries: list) -> dict:
    """Calculate rebar schedule grouped by POZ number (for block-based data)"""
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


def calculate_rebar_schedule_by_diameter(rebar_entries: list) -> dict:
    """Calculate rebar schedule grouped by diameter and type (for text-based data)"""
    results = {}
    
    for entry in rebar_entries:
        adet = parse_quantity(entry.get('ADET', '0'))
        cap = int(entry.get('CAP', '12')) if entry.get('CAP', '').isdigit() else 12
        boy = parse_length(entry.get('BOY', ''))
        yer = entry.get('YER', '')
        
        key = f"{cap}_{yer}"
        
        if key not in results:
            results[key] = {
                'cap': cap,
                'yer': yer,
                'adet': 0,
                'total_length_cm': 0
            }
        
        results[key]['adet'] += adet
        results[key]['total_length_cm'] += adet * boy
    
    return results


# ============================================================
# Display Functions
# ============================================================

def display_results_by_poz(results: dict):
    """Display rebar schedule grouped by POZ"""
    console.print("\n[bold green]" + "=" * 95 + "[/bold green]")
    console.print("[bold green]METRAJ TABLOSU / QUANTITY TABLE (POZ Bazlı)[/bold green]")
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
    print_totals(totals_by_diameter)


def display_results_by_diameter(results: dict):
    """Display rebar schedule grouped by diameter"""
    console.print("\n[bold green]" + "=" * 95 + "[/bold green]")
    console.print("[bold green]METRAJ TABLOSU / QUANTITY TABLE (Çap Bazlı)[/bold green]")
    console.print("[bold green]" + "=" * 95 + "[/bold green]\n")
    
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("ÇAP", justify="center", style="magenta")
    table.add_column("TİP", justify="left", style="cyan")
    table.add_column("DEMİR ADEDİ", justify="right")
    table.add_column("TOPLAM BOY (m)", justify="right", style="green")
    table.add_column("BİRİM AĞIRLIK (kg/m)", justify="right")
    table.add_column("AĞIRLIK (kg)", justify="right", style="yellow")
    
    totals_by_diameter = {}
    
    for key in sorted(results.keys(), key=lambda x: (int(x.split('_')[0]), x.split('_')[1])):
        r = results[key]
        
        toplam_m = r['total_length_cm'] / 100
        birim_kg = UNIT_WEIGHTS.get(r['cap'], 0)
        agirlik = toplam_m * birim_kg
        
        if r['cap'] not in totals_by_diameter:
            totals_by_diameter[r['cap']] = {'length': 0, 'weight': 0}
        totals_by_diameter[r['cap']]['length'] += toplam_m
        totals_by_diameter[r['cap']]['weight'] += agirlik
        
        table.add_row(
            f"ø{r['cap']}",
            r['yer'],
            str(r['adet']),
            f"{toplam_m:.2f}",
            f"{birim_kg:.3f}",
            f"{agirlik:.2f}"
        )
    
    console.print(table)
    print_totals(totals_by_diameter)


def print_totals(totals_by_diameter: dict):
    """Print totals by diameter and grand total"""
    console.print("\n[bold]" + "-" * 95 + "[/bold]")
    
    grand_total_weight = 0
    for cap in sorted(totals_by_diameter.keys()):
        t = totals_by_diameter[cap]
        grand_total_weight += t['weight']
        console.print(f"[cyan]Ø{cap}[/cyan] TOPLAM BOY: [green]{t['length']:,.2f} m[/green]  |  "
                     f"BİRİM AĞIRLIK: {UNIT_WEIGHTS.get(cap, 0):.3f} kg/m  |  "
                     f"AĞIRLIK: [yellow]{t['weight']:,.2f} kg[/yellow]")
    
    console.print("[bold]" + "=" * 95 + "[/bold]")
    console.print(f"[bold red]TOPLAM AĞIRLIK / TOTAL WEIGHT: {grand_total_weight:,.2f} kg[/bold red]")
    console.print("[bold]" + "=" * 95 + "[/bold]\n")


# ============================================================
# Main Entry Point
# ============================================================

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
        dxf_path = Path(r"C:\Users\sercan\Desktop\Drawing5.dxf")
    
    if not dxf_path.exists():
        console.print(f"[red]Hata: DXF dosyası bulunamadı: {dxf_path}[/red]")
        console.print("[yellow]Kullanım: python main.py <dxf_dosyasi.dxf>[/yellow]")
        return
    
    console.print(f"[green]Dosya yükleniyor:[/green] {dxf_path}")
    
    # Load DXF file
    doc = ezdxf.readfile(str(dxf_path))
    msp = doc.modelspace()
    
    # ========================================
    # Try Method 1: POZ Blocks
    # ========================================
    console.print("\n[cyan]Yöntem 1: POZ blokları aranıyor...[/cyan]")
    rebar_entries = extract_rebar_from_poz_blocks(msp)
    
    if rebar_entries:
        console.print(f"[green]✓ Bulunan POZ blokları:[/green] {len(rebar_entries)}")
        results = calculate_rebar_schedule_by_poz(rebar_entries)
        console.print(f"[green]✓ Benzersiz POZ numaraları:[/green] {len(results)}")
        display_results_by_poz(results)
        return
    
    console.print("[yellow]✗ POZ bloğu bulunamadı.[/yellow]")
    
    # ========================================
    # Try Method 2: TEXT Annotations
    # ========================================
    console.print("\n[cyan]Yöntem 2: TEXT notasyonları aranıyor...[/cyan]")
    rebar_entries = extract_rebar_from_text(msp)
    
    if rebar_entries:
        console.print(f"[green]✓ Bulunan donatı notasyonları:[/green] {len(rebar_entries)}")
        results = calculate_rebar_schedule_by_diameter(rebar_entries)
        console.print(f"[green]✓ Benzersiz gruplar:[/green] {len(results)}")
        display_results_by_diameter(results)
        return
    
    console.print("[yellow]✗ TEXT notasyonu bulunamadı.[/yellow]")
    
    # ========================================
    # No data found
    # ========================================
    console.print("\n[red]Uyarı: DXF dosyasında tanınabilir donatı verisi bulunamadı.[/red]")
    console.print("[dim]Desteklenen formatlar:[/dim]")
    console.print("[dim]  - POZ blokları (POZ, ADET, CAP, BOY attributes)[/dim]")
    console.print("[dim]  - TEXT notasyonları (örn: '16ƒ10/20 etr. l=206', '3ƒ14 mon. l=735')[/dim]")


if __name__ == "__main__":
    main()