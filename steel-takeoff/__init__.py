"""
Steel Quantity Takeoff
Extract rebar quantities from DXF construction drawings
"""

__version__ = '1.0.0'
__author__ = 'Sero'

from domain import RebarItem, RebarSchedule, UNIT_WEIGHTS
from services import TakeoffService, CalculationService
from exporters import ConsoleExporter, ExcelExporter
from config import AppSettings

__all__ = [
    'RebarItem',
    'RebarSchedule',
    'UNIT_WEIGHTS',
    'TakeoffService',
    'CalculationService',
    'ConsoleExporter',
    'ExcelExporter',
    'AppSettings',
]


def quick_analyze(file_path):
    """Quick analysis shortcut"""
    return TakeoffService.quick_analyze(file_path)
