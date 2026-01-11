"""
Rebar Analyzer Module
Analyzes geometric entities to identify and quantify rebar
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from src.dxf_parser import GeometricEntity


@dataclass
class RebarItem:
    """Represents a single rebar item"""
    diameter: int  # mm (8, 10, 12, 14, 16, 18, 20, 22, 25, 28, 32)
    length: float  # mm
    quantity: int
    shape: str  # "STRAIGHT", "L-SHAPE", "U-SHAPE", "STIRRUP", etc.
    layer: str
    
    # Calculated fields
    @property
    def total_length(self) -> float:
        """Total length in meters"""
        return (self.length * self.quantity) / 1000
    
    @property
    def unit_weight(self) -> float:
        """Weight per meter in kg/m"""
        # Standard rebar unit weights (kg/m)
        weights = {
            6: 0.222,
            8: 0.395,
            10: 0.617,
            12: 0.888,
            14: 1.208,
            16: 1.578,
            18: 1.998,
            20: 2.466,
            22: 2.984,
            25: 3.853,
            28: 4.834,
            32: 6.313,
            36: 7.990,
            40: 9.864,
        }
        return weights.get(self.diameter, 0)
    
    @property
    def weight(self) -> float:
        """Total weight in kg"""
        return self.total_length * self.unit_weight
    
    def to_dict(self) -> dict:
        """Convert to dictionary for display"""
        return {
            'diameter': self.diameter,
            'length': self.length,
            'quantity': self.quantity,
            'shape': self.shape,
            'layer': self.layer,
            'total_length': self.total_length,
            'weight': self.weight,
        }


class RebarAnalyzer:
    """Analyzes DXF entities to identify rebar elements"""
    
    # Common rebar layer name patterns
    REBAR_LAYER_PATTERNS = [
        r'(?i)rebar',
        r'(?i)steel',
        r'(?i)reinforc',
        r'(?i)donat[iı]',  # Turkish: donatı
        r'(?i)demir',      # Turkish: demir (iron/steel)
        r'(?i)çelik',      # Turkish: çelik (steel)
        r'(?i)arm',        # armature
        r'(?i)bar',
        r'(?i)stirrup',
        r'(?i)etriye',     # Turkish: etriye (stirrup)
    ]
    
    # Standard rebar diameters (mm)
    STANDARD_DIAMETERS = [6, 8, 10, 12, 14, 16, 18, 20, 22, 25, 28, 32, 36, 40]
    
    # Rebar annotation patterns (e.g., "10ø16", "ø12/15", "5-ø20")
    REBAR_TEXT_PATTERNS = [
        r'(\d+)\s*[øφ∅Φ]\s*(\d+)',           # "10ø16" - quantity + diameter
        r'[øφ∅Φ]\s*(\d+)\s*/\s*(\d+)',       # "ø12/15" - diameter/spacing
        r'(\d+)\s*-\s*[øφ∅Φ]\s*(\d+)',       # "5-ø20" - quantity-diameter
        r'[øφ∅Φ]\s*(\d+)',                   # "ø16" - just diameter
    ]
    
    def __init__(self, entities: List[GeometricEntity]):
        self.entities = entities
        self.rebar_layers = set()
        self._identify_rebar_layers()
    
    def _identify_rebar_layers(self):
        """Identify layers that likely contain rebar"""
        all_layers = set(e.layer for e in self.entities)
        
        for layer in all_layers:
            for pattern in self.REBAR_LAYER_PATTERNS:
                if re.search(pattern, layer):
                    self.rebar_layers.add(layer)
                    break
    
    def analyze(self) -> List[dict]:
        """Analyze entities and return rebar items"""
        rebar_items = []
        
        # First, try to extract from text annotations
        text_based = self._analyze_text_annotations()
        rebar_items.extend(text_based)
        
        # Then, analyze geometric entities on rebar layers
        geometry_based = self._analyze_geometry()
        rebar_items.extend(geometry_based)
        
        return rebar_items
    
    def _analyze_text_annotations(self) -> List[dict]:
        """Extract rebar info from text annotations"""
        results = []
        
        text_entities = [e for e in self.entities if e.entity_type == "TEXT"]
        
        for entity in text_entities:
            if not entity.text_content:
                continue
            
            text = entity.text_content.strip()
            
            # Try to match rebar patterns
            for pattern in self.REBAR_TEXT_PATTERNS:
                match = re.search(pattern, text)
                if match:
                    groups = match.groups()
                    
                    # Parse based on pattern type
                    if len(groups) == 2:
                        # Check if first group is quantity or diameter
                        first, second = int(groups[0]), int(groups[1])
                        
                        if first in self.STANDARD_DIAMETERS and second not in self.STANDARD_DIAMETERS:
                            # ø12/15 pattern (diameter/spacing)
                            diameter = first
                            quantity = 1  # Unknown quantity
                        elif second in self.STANDARD_DIAMETERS:
                            # 10ø16 pattern (quantity + diameter)
                            quantity = first
                            diameter = second
                        else:
                            continue
                    elif len(groups) == 1:
                        # Just diameter
                        diameter = int(groups[0])
                        quantity = 1
                    else:
                        continue
                    
                    if diameter in self.STANDARD_DIAMETERS:
                        item = RebarItem(
                            diameter=diameter,
                            length=0,  # Unknown from text alone
                            quantity=quantity,
                            shape="UNKNOWN",
                            layer=entity.layer
                        )
                        results.append(item.to_dict())
                    break
        
        return results
    
    def _analyze_geometry(self) -> List[dict]:
        """Analyze geometric entities to identify rebar"""
        results = []
        
        # Group entities by layer
        layer_entities = {}
        for entity in self.entities:
            if entity.layer not in layer_entities:
                layer_entities[entity.layer] = []
            layer_entities[entity.layer].append(entity)
        
        # Analyze entities on rebar layers
        for layer in self.rebar_layers:
            if layer not in layer_entities:
                continue
            
            entities = layer_entities[layer]
            
            # Analyze lines (potential straight bars)
            lines = [e for e in entities if e.entity_type == "LINE"]
            line_results = self._analyze_lines(lines, layer)
            results.extend(line_results)
            
            # Analyze polylines (potential bent bars or stirrups)
            polylines = [e for e in entities if e.entity_type == "POLYLINE"]
            polyline_results = self._analyze_polylines(polylines, layer)
            results.extend(polyline_results)
        
        return results
    
    def _analyze_lines(self, lines: List[GeometricEntity], layer: str) -> List[dict]:
        """Analyze LINE entities for potential rebar"""
        results = []
        
        # Group lines by similar lengths (within tolerance)
        length_groups = self._group_by_length(lines, tolerance=5)  # 5mm tolerance
        
        for length, group in length_groups.items():
            if len(group) >= 1:
                # Assume ø12 for now (we need more context to determine diameter)
                item = RebarItem(
                    diameter=12,  # Default assumption
                    length=length,
                    quantity=len(group),
                    shape="STRAIGHT",
                    layer=layer
                )
                results.append(item.to_dict())
        
        return results
    
    def _analyze_polylines(self, polylines: List[GeometricEntity], layer: str) -> List[dict]:
        """Analyze POLYLINE entities for potential rebar shapes"""
        results = []
        
        for pline in polylines:
            if not pline.vertices or len(pline.vertices) < 2:
                continue
            
            # Determine shape based on number of vertices and closure
            num_vertices = len(pline.vertices)
            
            if pline.is_closed:
                if num_vertices == 4:
                    shape = "STIRRUP"
                else:
                    shape = "CLOSED-SHAPE"
            elif num_vertices == 2:
                shape = "STRAIGHT"
            elif num_vertices == 3:
                shape = "L-SHAPE"
            elif num_vertices == 4:
                shape = "U-SHAPE"
            else:
                shape = f"BENT-{num_vertices}PT"
            
            item = RebarItem(
                diameter=12,  # Default assumption
                length=pline.length or 0,
                quantity=1,
                shape=shape,
                layer=layer
            )
            results.append(item.to_dict())
        
        return results
    
    def _group_by_length(self, entities: List[GeometricEntity], tolerance: float) -> Dict[float, List[GeometricEntity]]:
        """Group entities by similar lengths"""
        groups = {}
        
        for entity in entities:
            if entity.length is None:
                continue
            
            length = round(entity.length / tolerance) * tolerance
            
            if length not in groups:
                groups[length] = []
            groups[length].append(entity)
        
        return groups
    
    def get_layer_summary(self) -> dict:
        """Get summary of entities per layer"""
        summary = {}
        
        for entity in self.entities:
            if entity.layer not in summary:
                summary[entity.layer] = {'count': 0, 'types': set(), 'is_rebar': entity.layer in self.rebar_layers}
            summary[entity.layer]['count'] += 1
            summary[entity.layer]['types'].add(entity.entity_type)
        
        # Convert sets to lists for JSON compatibility
        for layer in summary:
            summary[layer]['types'] = list(summary[layer]['types'])
        
        return summary
