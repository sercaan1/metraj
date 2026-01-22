"""
CLI Application
Main entry point for command-line interface
"""

import argparse
import sys

from rich.console import Console

from .commands import cmd_analyze, cmd_info, cmd_batch


console = Console()


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser"""
    parser = argparse.ArgumentParser(
        prog='steel-takeoff',
        description='Steel Quantity Takeoff - Extract rebar quantities from DXF drawings',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s analyze drawing.dxf              Analyze and display results
  %(prog)s analyze drawing.dxf --excel      Analyze and export to Excel
  %(prog)s info drawing.dxf                 Show file information
  %(prog)s batch ./drawings --excel         Process all DXF files in folder
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze a DXF file')
    analyze_parser.add_argument('file', help='Path to DXF file')
    analyze_parser.add_argument('--excel', '-e', action='store_true', help='Export to Excel')
    analyze_parser.add_argument('--output', '-o', help='Output directory for Excel file')
    
    # info command
    info_parser = subparsers.add_parser('info', help='Show DXF file information')
    info_parser.add_argument('file', help='Path to DXF file')
    
    # batch command
    batch_parser = subparsers.add_parser('batch', help='Process all DXF files in a directory')
    batch_parser.add_argument('directory', help='Directory containing DXF files')
    batch_parser.add_argument('--excel', '-e', action='store_true', default=True, help='Export to Excel (default: True)')
    batch_parser.add_argument('--no-excel', action='store_true', help='Do not export to Excel')
    batch_parser.add_argument('--output', '-o', help='Output directory for Excel files')
    
    return parser


def main(args=None) -> int:
    """Main CLI entry point"""
    parser = create_parser()
    parsed = parser.parse_args(args)
    
    if not parsed.command:
        parser.print_help()
        return 0
    
    try:
        if parsed.command == 'analyze':
            cmd_analyze(
                parsed.file,
                export_excel=parsed.excel,
                output_dir=parsed.output
            )
        
        elif parsed.command == 'info':
            cmd_info(parsed.file)
        
        elif parsed.command == 'batch':
            cmd_batch(
                parsed.directory,
                export_excel=not parsed.no_excel,
                output_dir=parsed.output
            )
        
        return 0
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        return 1
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1


if __name__ == '__main__':
    sys.exit(main())
