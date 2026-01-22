"""
Text Annotation Parser
Extracts rebar data from TEXT annotations in DXF files

IMPORTANT: This parser uses the EXACT same patterns as the original CLI tool!
"""

import re
from typing import List, Optional

from domain import RebarItem, DXFEntity, RebarType, RebarShape
from domain.constants import STANDARD_DIAMETERS


class TextAnnotationParser:
    """
    Parser for free-form text annotations in construction drawings.
    
    Uses the exact same patterns as the original CLI tool for consistency.
    """
    
    # Patterns for text-based rebar annotations
    # Note: [ƒφøΦ\[] matches various diameter symbols including [ used in some drawings
    # ORDER MATTERS - more specific patterns must come first!
    PATTERNS = [
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
    
    # Layer name keywords that indicate rebar content
    REBAR_LAYER_KEYWORDS = ['REBAR', 'DONATI', 'DONATL']
    
    def parse_texts(self, entities: List[DXFEntity]) -> List[RebarItem]:
        """Parse all TEXT entities and return rebar items"""
        items = []
        
        for entity in entities:
            if entity.entity_type != "TEXT" or not entity.text_content:
                continue
            
            layer = entity.layer or ""
            text = entity.text_content.strip()
            
            # Only process rebar-related layers (same as original tool)
            layer_upper = layer.upper()
            if not any(kw in layer_upper for kw in self.REBAR_LAYER_KEYWORDS):
                continue
            
            # Try each pattern (order matters!)
            for pattern, tip in self.PATTERNS:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    groups = match.groups()
                    item = self._create_item_from_match(groups, tip, layer)
                    if item:
                        items.append(item)
                    break  # Found a match, no need to try other patterns
        
        return items
    
    def _create_item_from_match(self, groups: tuple, tip: str, layer: str) -> Optional[RebarItem]:
        """Create RebarItem from regex match groups"""
        
        spacing = None
        
        if tip == 'etriye':
            # Stirrups: qty, diameter, spacing, length
            quantity = int(groups[0])
            diameter = int(groups[1])
            spacing = int(groups[2])
            length_cm = int(groups[3])
            rebar_type = RebarType.STIRRUP
            
        elif tip in ['döşeme_alt', 'döşeme_üst', 'döşeme']:
            # Slab reinforcement: qty, diameter, spacing, length
            quantity = int(groups[0])
            diameter = int(groups[1])
            spacing = int(groups[2])
            length_cm = int(groups[3])
            
            if tip == 'döşeme_alt':
                rebar_type = RebarType.BOTTOM
            elif tip == 'döşeme_üst':
                rebar_type = RebarType.TOP
            else:
                rebar_type = RebarType.MAIN
                
        elif tip in ['döşeme_alt_dist', 'döşeme_üst_dist']:
            # Distributed slab rebar without quantity - skip these
            # They are typically reference annotations
            return None
            
        elif tip in ['ilave', 'montaj', 'govde', 'pilye']:
            # Other bars: qty, diameter, length (no spacing in pattern)
            quantity = int(groups[0])
            diameter = int(groups[1])
            length_cm = int(groups[2])
            
            if tip == 'ilave':
                rebar_type = RebarType.ADDITIONAL
            elif tip == 'montaj':
                rebar_type = RebarType.MONTAGE
            else:
                rebar_type = RebarType.MAIN
        else:
            return None
        
        # Validate diameter
        if diameter not in STANDARD_DIAMETERS:
            return None
        
        return RebarItem(
            diameter=diameter,
            length=length_cm * 10,  # Convert cm to mm (internal storage is mm)
            quantity=quantity,
            shape=RebarShape.STIRRUP if tip == 'etriye' else RebarShape.STRAIGHT,
            rebar_type=rebar_type,
            position=None,
            location=tip,  # Store the type as location for grouping
            spacing=spacing,
            layer=layer,
            source=f"text_{tip}"
        )
