"""
DXF Explorer - Utility to explore and understand DXF file structure
Run this first on your DXF files to see what entities and layers they contain
"""

import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.tree import Tree

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.dxf_parser import DXFParser

console = Console()


def explore_dxf(filepath: str):
    """Explore a DXF file and show its structure"""
    path = Path(filepath)
    
    if not path.exists():
        console.print(f"[red]File not found: {path}[/red]")
        return
    
    console.print(f"\n[bold blue]Exploring: {path.name}[/bold blue]")
    console.print("=" * 60)
    
    parser = DXFParser(path)
    
    # Get entity summary
    console.print("\n[bold]Entity Summary:[/bold]")
    summary = parser.get_entity_summary()
    
    table = Table()
    table.add_column("Entity Type", style="cyan")
    table.add_column("Count", justify="right", style="green")
    
    for entity_type, count in sorted(summary.items(), key=lambda x: -x[1]):
        table.add_row(entity_type, str(count))
    
    console.print(table)
    
    # Get layers
    console.print("\n[bold]Layers:[/bold]")
    layers = parser.get_layers()
    
    tree = Tree("[bold]Layers[/bold]")
    for layer in sorted(layers):
        tree.add(f"[yellow]{layer}[/yellow]")
    
    console.print(tree)
    
    # Parse and show sample entities
    console.print("\n[bold]Sample Entities (first 10):[/bold]")
    entities = parser.parse()
    
    for i, entity in enumerate(entities[:10]):
        console.print(f"\n[cyan]Entity {i+1}:[/cyan] {entity.entity_type} on layer '{entity.layer}'")
        
        if entity.entity_type == "LINE":
            console.print(f"  Start: {entity.start_point}")
            console.print(f"  End: {entity.end_point}")
            console.print(f"  Length: {entity.length:.2f}")
        
        elif entity.entity_type == "ARC":
            console.print(f"  Center: {entity.center}")
            console.print(f"  Radius: {entity.radius:.2f}")
            console.print(f"  Angles: {entity.start_angle:.1f}° - {entity.end_angle:.1f}°")
            console.print(f"  Arc Length: {entity.length:.2f}")
        
        elif entity.entity_type == "POLYLINE":
            console.print(f"  Vertices: {len(entity.vertices)} points")
            console.print(f"  Closed: {entity.is_closed}")
            console.print(f"  Total Length: {entity.length:.2f}")
        
        elif entity.entity_type == "CIRCLE":
            console.print(f"  Center: {entity.center}")
            console.print(f"  Radius: {entity.radius:.2f}")
        
        elif entity.entity_type == "TEXT":
            console.print(f"  Content: '{entity.text_content}'")
    
    # Show text entities that might be rebar annotations
    console.print("\n[bold]Potential Rebar Annotations (TEXT entities):[/bold]")
    text_entities = [e for e in entities if e.entity_type == "TEXT"]
    
    if text_entities:
        for entity in text_entities[:20]:  # First 20
            text = entity.text_content or ""
            # Highlight if it looks like rebar annotation
            if any(c in text for c in ['ø', 'φ', '∅', 'Φ']) or 'mm' in text.lower():
                console.print(f"  [green]► {text}[/green]")
            else:
                console.print(f"  • {text}")
    else:
        console.print("  [dim]No text entities found[/dim]")


def main():
    if len(sys.argv) < 2:
        console.print("[yellow]Usage: python explore_dxf.py <path_to_dxf_file>[/yellow]")
        console.print("\nExample:")
        console.print("  python explore_dxf.py my_drawing.dxf")
        return
    
    explore_dxf(sys.argv[1])


if __name__ == "__main__":
    main()
