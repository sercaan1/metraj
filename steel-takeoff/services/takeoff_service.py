"""
Takeoff Service
Main application service orchestrating the steel takeoff workflow
"""

from pathlib import Path
from typing import Optional, Dict, List

from domain import RebarSchedule
from config import AppSettings
from analyzers import RebarAnalyzer
from .calculation_service import CalculationService


class TakeoffService:
    """
    Main service for steel quantity takeoff.
    
    Orchestrates the workflow:
    1. Parse DXF file
    2. Extract rebar items from various sources
    3. Calculate weights and lengths
    4. Generate reports/exports
    """
    
    def __init__(self, settings: Optional[AppSettings] = None):
        self.settings = settings or AppSettings.default()
        self._analyzer = RebarAnalyzer(self.settings)
        self._calculator = CalculationService()
    
    def process_file(self, file_path: Path) -> RebarSchedule:
        """
        Process a single DXF file and return the rebar schedule.
        
        Args:
            file_path: Path to the DXF file
            
        Returns:
            RebarSchedule with all extracted rebar items
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if file_path.suffix.lower() != '.dxf':
            raise ValueError(f"Unsupported file type: {file_path.suffix}")
        
        return self._analyzer.analyze_file(file_path)
    
    def process_files(self, file_paths: List[Path]) -> Dict[str, RebarSchedule]:
        """
        Process multiple DXF files.
        
        Args:
            file_paths: List of paths to DXF files
            
        Returns:
            Dict mapping file names to their schedules
        """
        results = {}
        
        for file_path in file_paths:
            try:
                schedule = self.process_file(file_path)
                results[file_path.name] = schedule
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
        
        return results
    
    def get_summary(self, schedule: RebarSchedule) -> Dict:
        """
        Get a summary of the rebar schedule.
        
        Returns dict with:
        - total_weight_kg
        - total_length_m
        - item_count
        - position_count
        - by_diameter: breakdown by diameter
        - by_position: breakdown by position
        """
        return {
            'project_name': schedule.project_name,
            'drawing_file': schedule.drawing_file,
            'total_weight_kg': round(schedule.total_weight_kg, 2),
            'total_length_m': round(schedule.total_length_m, 2),
            'item_count': len(schedule.items),
            'position_count': len(schedule.by_position()),
            'by_diameter': self._calculator.get_diameter_breakdown(schedule),
            'by_position': self._calculator.get_position_breakdown(schedule),
        }
    
    def get_file_info(self, file_path: Path) -> Dict:
        """Get information about a DXF file without full analysis"""
        return self._analyzer.get_file_summary(file_path)
    
    def merge_schedules(self, schedules: List[RebarSchedule], project_name: str = "Combined") -> RebarSchedule:
        """
        Merge multiple schedules into one.
        
        Args:
            schedules: List of RebarSchedule objects
            project_name: Name for the combined schedule
            
        Returns:
            Combined RebarSchedule
        """
        combined = RebarSchedule(project_name=project_name)
        
        for schedule in schedules:
            for item in schedule.items:
                if self.settings.analyzer.merge_duplicates:
                    combined.merge_item(item)
                else:
                    combined.add_item(item)
        
        return combined
    
    @classmethod
    def quick_analyze(cls, file_path: Path) -> Dict:
        """
        Quick analysis with default settings.
        Returns a summary dict.
        """
        service = cls()
        schedule = service.process_file(file_path)
        return service.get_summary(schedule)
    
    @classmethod
    def for_poz_blocks(cls) -> 'TakeoffService':
        """Create service configured for POZ block drawings"""
        return cls(AppSettings.for_poz_blocks())
    
    @classmethod
    def for_text_annotations(cls) -> 'TakeoffService':
        """Create service configured for text annotation drawings"""
        return cls(AppSettings.for_text_annotations())
    
    @classmethod
    def full_analysis(cls) -> 'TakeoffService':
        """Create service configured for full analysis"""
        return cls(AppSettings.full_analysis())
