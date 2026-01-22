"""
Domain Models
Core business entities for steel takeoff
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
from .constants import UNIT_WEIGHTS, RebarShape, RebarType


@dataclass
class RebarItem:
    """Represents a single rebar specification"""
    diameter: int  # mm
    length: float  # mm
    quantity: int
    shape: str = RebarShape.STRAIGHT
    rebar_type: str = RebarType.MAIN
    position: Optional[str] = None  # POZ number
    location: Optional[str] = None  # YER - placement location
    spacing: Optional[int] = None   # ARALIK - spacing in mm
    layer: Optional[str] = None     # DXF layer name
    source: str = "unknown"         # How it was extracted (poz_block, text_annotation, etc.)
    
    @property
    def total_length_m(self) -> float:
        """Total length in meters"""
        return (self.length * self.quantity) / 1000
    
    @property
    def unit_weight(self) -> float:
        """Weight per meter in kg/m"""
        return UNIT_WEIGHTS.get(self.diameter, 0.0)
    
    @property
    def weight_kg(self) -> float:
        """Total weight in kg"""
        return self.total_length_m * self.unit_weight
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            'position': self.position,
            'diameter': self.diameter,
            'quantity': self.quantity,
            'length_mm': self.length,
            'length_cm': self.length / 10,
            'total_length_m': round(self.total_length_m, 2),
            'unit_weight': self.unit_weight,
            'weight_kg': round(self.weight_kg, 2),
            'shape': self.shape,
            'rebar_type': self.rebar_type,
            'location': self.location,
            'spacing': self.spacing,
            'source': self.source,
        }


@dataclass
class RebarSchedule:
    """Collection of rebar items with aggregation capabilities"""
    items: List[RebarItem] = field(default_factory=list)
    project_name: Optional[str] = None
    drawing_file: Optional[str] = None
    
    def add_item(self, item: RebarItem) -> None:
        """Add a rebar item to the schedule"""
        self.items.append(item)
    
    def merge_item(self, item: RebarItem) -> None:
        """Merge item with existing if same position, diameter, and length"""
        for existing in self.items:
            if (existing.position == item.position and 
                existing.diameter == item.diameter and
                existing.length == item.length):
                existing.quantity += item.quantity
                return
        self.items.append(item)
    
    @property
    def total_weight_kg(self) -> float:
        """Total weight of all items"""
        return sum(item.weight_kg for item in self.items)
    
    @property
    def total_length_m(self) -> float:
        """Total length of all items in meters"""
        return sum(item.total_length_m for item in self.items)
    
    def by_diameter(self) -> Dict[int, List[RebarItem]]:
        """Group items by diameter"""
        result: Dict[int, List[RebarItem]] = {}
        for item in self.items:
            if item.diameter not in result:
                result[item.diameter] = []
            result[item.diameter].append(item)
        return result
    
    def by_position(self) -> Dict[str, List[RebarItem]]:
        """Group items by position (POZ) number"""
        result: Dict[str, List[RebarItem]] = {}
        for item in self.items:
            key = item.position or "NO_POZ"
            if key not in result:
                result[key] = []
            result[key].append(item)
        return result
    
    def summary_by_diameter(self) -> Dict[int, dict]:
        """Get summary statistics grouped by diameter"""
        summary: Dict[int, dict] = {}
        for item in self.items:
            d = item.diameter
            if d not in summary:
                summary[d] = {
                    'diameter': d,
                    'total_quantity': 0,
                    'total_length_m': 0.0,
                    'total_weight_kg': 0.0,
                    'unit_weight': UNIT_WEIGHTS.get(d, 0.0),
                }
            summary[d]['total_quantity'] += item.quantity
            summary[d]['total_length_m'] += item.total_length_m
            summary[d]['total_weight_kg'] += item.weight_kg
        return summary
    
    def to_dict_list(self) -> List[dict]:
        """Convert all items to list of dictionaries"""
        return [item.to_dict() for item in self.items]


@dataclass
class DXFEntity:
    """Represents a geometric entity from a DXF file"""
    entity_type: str
    layer: str
    color: Optional[int] = None
    
    # LINE attributes
    start_point: Optional[tuple] = None
    end_point: Optional[tuple] = None
    
    # ARC/CIRCLE attributes
    center: Optional[tuple] = None
    radius: Optional[float] = None
    start_angle: Optional[float] = None
    end_angle: Optional[float] = None
    
    # POLYLINE attributes
    vertices: Optional[List[tuple]] = None
    is_closed: bool = False
    bulges: Optional[List[float]] = None
    
    # TEXT/MTEXT attributes
    text_content: Optional[str] = None
    insertion_point: Optional[tuple] = None
    
    # INSERT (Block) attributes
    block_name: Optional[str] = None
    attributes: Optional[Dict[str, str]] = None
    
    # Calculated
    length: Optional[float] = None


@dataclass
class ParseResult:
    """Result of parsing a DXF file"""
    entities: List[DXFEntity] = field(default_factory=list)
    layers: List[str] = field(default_factory=list)
    blocks: List[str] = field(default_factory=list)
    entity_counts: Dict[str, int] = field(default_factory=dict)
    file_path: Optional[str] = None
    
    @property
    def total_entities(self) -> int:
        return len(self.entities)
