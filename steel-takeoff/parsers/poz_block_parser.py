"""
POZ Block Parser
Extracts rebar data from POZ block attributes in DXF files
"""

import re
from typing import List, Optional

from domain import RebarItem, DXFEntity, RebarType, RebarShape
from domain.constants import STANDARD_DIAMETERS


class PozBlockParser:
    """
    Parser for POZ (Position) blocks commonly used in Turkish construction drawings.
    
    POZ blocks typically have attributes like:
    - POZ: Position number (e.g., "1", "2", "15")
    - ADET: Quantity (e.g., "10", "2x5")
    - CAP: Diameter in mm (e.g., "12", "16")
    - BOY: Length specification (e.g., "L=800", "850")
    - YER: Location/placement (e.g., "Kiriş", "Kolon")
    - ARALIK: Spacing (e.g., "15", "20")
    """
    
    def __init__(self, block_name: str = "poz"):
        self.block_name = block_name.lower()
    
    def parse_blocks(self, entities: List[DXFEntity]) -> List[RebarItem]:
        """Parse all POZ block inserts and return rebar items"""
        items = []
        
        poz_inserts = [
            e for e in entities 
            if e.entity_type == "INSERT" and 
               e.block_name and 
               e.block_name.lower() == self.block_name
        ]
        
        for insert in poz_inserts:
            item = self._parse_single_block(insert)
            if item:
                items.append(item)
        
        return items
    
    def _parse_single_block(self, entity: DXFEntity) -> Optional[RebarItem]:
        """Parse a single POZ block INSERT entity"""
        if not entity.attributes:
            return None
        
        attribs = {k.upper(): v for k, v in entity.attributes.items()}
        
        # Extract position number
        position = attribs.get('POZ', attribs.get('NO', ''))
        
        # Extract and parse quantity
        quantity = self._parse_quantity(attribs.get('ADET', '1'))
        if quantity == 0:
            quantity = 1
        
        # Extract diameter
        diameter = self._parse_diameter(attribs.get('CAP', attribs.get('DIA', '12')))
        if diameter not in STANDARD_DIAMETERS:
            diameter = 12  # Default
        
        # Extract length
        length = self._parse_length(attribs.get('BOY', attribs.get('LENGTH', '0')))
        if length == 0:
            return None  # Skip items without length
        
        # Extract optional fields
        location = attribs.get('YER', attribs.get('LOCATION', ''))
        spacing = self._parse_spacing(attribs.get('ARALIK', attribs.get('SPACING', '')))
        
        # Determine rebar type from location or other hints
        rebar_type = self._determine_type(location, attribs)
        
        return RebarItem(
            diameter=diameter,
            length=length,
            quantity=quantity,
            shape=RebarShape.STRAIGHT,  # POZ blocks typically represent straight bars
            rebar_type=rebar_type,
            position=position,
            location=location,
            spacing=spacing,
            layer=entity.layer,
            source="poz_block"
        )
    
    def _parse_quantity(self, value: str) -> int:
        """
        Parse quantity string.
        Handles formats: "10", "2x5", "3X4"
        """
        if not value:
            return 0
        
        value = value.strip()
        
        # Handle multiplication format
        if 'x' in value.lower():
            parts = value.lower().split('x')
            try:
                return int(parts[0].strip()) * int(parts[1].strip())
            except (ValueError, IndexError):
                return 0
        
        # Simple integer
        try:
            return int(value)
        except ValueError:
            return 0
    
    def _parse_diameter(self, value: str) -> int:
        """Parse diameter string, extracting numeric value"""
        if not value:
            return 12
        
        # Remove common prefixes
        value = re.sub(r'[øφ∅ΦƒQ\[]', '', value)
        
        # Extract first number
        match = re.search(r'(\d+)', value)
        if match:
            return int(match.group(1))
        return 12
    
    def _parse_length(self, value: str) -> float:
        """
        Parse length string.
        Handles formats: "800", "L=800", "L:800", "80 cm"
        
        IMPORTANT: In Turkish construction drawings, BOY values are in CENTIMETERS!
        Returns length in mm (for internal consistency)
        """
        if not value:
            return 0.0
        
        value = value.strip().upper()
        
        # Remove L= or L: prefix
        value = re.sub(r'^[Ll]\s*[=:]\s*', '', value)
        
        # Check for explicit unit suffix
        is_cm = 'CM' in value
        is_mm = 'MM' in value
        is_m = value.endswith('M') and not is_mm and not is_cm
        
        # Remove unit suffixes
        value = re.sub(r'(CM|MM|M)\b', '', value)
        
        # Extract number
        match = re.search(r'(\d+(?:\.\d+)?)', value)
        if match:
            length = float(match.group(1))
            
            if is_mm:
                return length  # Already mm
            elif is_m:
                return length * 1000  # m to mm
            else:
                # Default: BOY values are in CENTIMETERS in Turkish drawings
                # Convert cm to mm
                return length * 10
        
        return 0.0
    
    def _parse_spacing(self, value: str) -> Optional[int]:
        """Parse spacing value"""
        if not value:
            return None
        
        match = re.search(r'(\d+)', value)
        if match:
            return int(match.group(1))
        return None
    
    def _determine_type(self, location: str, attribs: dict) -> str:
        """Determine rebar type based on location or attributes"""
        location_lower = location.lower() if location else ''
        
        # Check for stirrup indicators
        if any(kw in location_lower for kw in ['etr', 'stirrup', 'etriye']):
            return RebarType.STIRRUP
        
        # Check for montage
        if any(kw in location_lower for kw in ['mon', 'montaj', 'montage']):
            return RebarType.MONTAGE
        
        # Check for additional bars
        if any(kw in location_lower for kw in ['ila', 'ilave', 'additional']):
            return RebarType.ADDITIONAL
        
        # Check SEKIL (shape) attribute for stirrup
        sekil = attribs.get('SEKIL', attribs.get('SHAPE', '')).lower()
        if any(kw in sekil for kw in ['etr', 'stirrup', 'etriye', 'closed']):
            return RebarType.STIRRUP
        
        return RebarType.MAIN
