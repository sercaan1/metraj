"""
Base Exporter
Abstract base class for all exporters
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from domain import RebarSchedule
from config import ExportSettings


class BaseExporter(ABC):
    """Abstract base class for schedule exporters"""
    
    def __init__(self, settings: Optional[ExportSettings] = None):
        self.settings = settings or ExportSettings()
    
    @abstractmethod
    def export(self, schedule: RebarSchedule, output_path: Optional[Path] = None) -> None:
        """Export the schedule"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Exporter name for display"""
        pass
