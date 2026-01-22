"""
Application Settings
Configuration options for the steel takeoff application
"""

from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path


@dataclass
class ParserSettings:
    """Settings for DXF parsing"""
    # Which entity types to extract
    extract_lines: bool = True
    extract_arcs: bool = True
    extract_polylines: bool = True
    extract_circles: bool = True
    extract_text: bool = True
    extract_blocks: bool = True
    
    # Block names to look for (lowercase)
    target_block_names: List[str] = field(default_factory=lambda: ['poz'])
    
    # Length tolerance for grouping similar lengths (mm)
    length_tolerance: float = 5.0


@dataclass
class AnalyzerSettings:
    """Settings for rebar analysis"""
    # Default diameter when not specified (mm)
    default_diameter: int = 12
    
    # Minimum length to consider as rebar (mm)
    min_rebar_length: float = 100.0
    
    # Maximum length for stirrups (mm)
    max_stirrup_length: float = 3000.0
    
    # Whether to merge duplicate entries
    merge_duplicates: bool = True
    
    # Analyze text annotations
    analyze_text: bool = True
    
    # Analyze POZ blocks
    analyze_poz_blocks: bool = True
    
    # Analyze geometric entities
    analyze_geometry: bool = False  # Often noisy, disabled by default


@dataclass
class ExportSettings:
    """Settings for export functionality"""
    # Excel settings
    excel_sheet_name: str = "Rebar Schedule"
    excel_include_summary: bool = True
    excel_include_charts: bool = False
    
    # Console output settings
    console_color: bool = True
    console_show_details: bool = True
    
    # Number formatting
    decimal_places_length: int = 2
    decimal_places_weight: int = 2


@dataclass
class AppSettings:
    """Main application settings"""
    parser: ParserSettings = field(default_factory=ParserSettings)
    analyzer: AnalyzerSettings = field(default_factory=AnalyzerSettings)
    export: ExportSettings = field(default_factory=ExportSettings)
    
    # Output directory for exports
    output_dir: Optional[Path] = None
    
    # Logging level
    log_level: str = "INFO"
    
    @classmethod
    def default(cls) -> 'AppSettings':
        """Create default settings"""
        return cls()
    
    @classmethod
    def for_poz_blocks(cls) -> 'AppSettings':
        """Settings optimized for POZ block drawings"""
        settings = cls()
        settings.analyzer.analyze_poz_blocks = True
        settings.analyzer.analyze_text = False
        settings.analyzer.analyze_geometry = False
        return settings
    
    @classmethod
    def for_text_annotations(cls) -> 'AppSettings':
        """Settings optimized for text annotation drawings"""
        settings = cls()
        settings.analyzer.analyze_poz_blocks = False
        settings.analyzer.analyze_text = True
        settings.analyzer.analyze_geometry = False
        return settings
    
    @classmethod
    def full_analysis(cls) -> 'AppSettings':
        """Settings for full analysis including geometry"""
        settings = cls()
        settings.analyzer.analyze_poz_blocks = True
        settings.analyzer.analyze_text = True
        settings.analyzer.analyze_geometry = True
        return settings
