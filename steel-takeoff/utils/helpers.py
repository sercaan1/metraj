"""
Utility Helpers
Common utility functions
"""

import re
from pathlib import Path
from typing import List, Optional, Tuple


def normalize_text(text: str) -> str:
    """Normalize text by removing extra whitespace and lowercasing"""
    return ' '.join(text.lower().split())


def extract_numbers(text: str) -> List[int]:
    """Extract all integers from text"""
    return [int(x) for x in re.findall(r'\d+', text)]


def extract_float(text: str) -> Optional[float]:
    """Extract first float from text"""
    match = re.search(r'(\d+(?:\.\d+)?)', text)
    if match:
        return float(match.group(1))
    return None


def parse_dimension(value: str) -> Tuple[float, str]:
    """
    Parse a dimension string and return value with unit.
    
    Examples:
        "800" -> (800.0, "mm")
        "80cm" -> (80.0, "cm")
        "0.8m" -> (0.8, "m")
    
    Returns:
        Tuple of (value, unit)
    """
    value = value.strip().lower()
    
    if 'cm' in value:
        num = extract_float(value.replace('cm', ''))
        return (num or 0, 'cm')
    elif 'm' in value and 'mm' not in value:
        num = extract_float(value.replace('m', ''))
        return (num or 0, 'm')
    else:
        num = extract_float(value.replace('mm', ''))
        return (num or 0, 'mm')


def convert_to_mm(value: float, unit: str) -> float:
    """Convert a length to millimeters"""
    conversions = {
        'mm': 1,
        'cm': 10,
        'm': 1000,
    }
    return value * conversions.get(unit.lower(), 1)


def safe_int(value: str, default: int = 0) -> int:
    """Safely convert string to int"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: str, default: float = 0.0) -> float:
    """Safely convert string to float"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def find_dxf_files(directory: Path) -> List[Path]:
    """Find all DXF files in a directory"""
    directory = Path(directory)
    if not directory.is_dir():
        return []
    
    return list(directory.glob("*.dxf")) + list(directory.glob("*.DXF"))


def format_weight(weight_kg: float, include_tons: bool = True) -> str:
    """Format weight for display"""
    if include_tons and weight_kg >= 1000:
        return f"{weight_kg:,.2f} kg ({weight_kg/1000:,.3f} ton)"
    return f"{weight_kg:,.2f} kg"


def format_length(length_m: float) -> str:
    """Format length for display"""
    return f"{length_m:,.2f} m"
