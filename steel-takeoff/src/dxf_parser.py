"""
DXF Parser Module
Reads DXF files and extracts geometric entities
"""

from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Tuple
import ezdxf
from ezdxf.entities import Line, Arc, LWPolyline, Polyline, Circle, Text, MText


@dataclass
class GeometricEntity:
    """Represents a geometric entity from the DXF file"""
    entity_type: str  # LINE, ARC, POLYLINE, CIRCLE, etc.
    layer: str
    color: Optional[int] = None
    
    # For LINE
    start_point: Optional[Tuple[float, float, float]] = None
    end_point: Optional[Tuple[float, float, float]] = None
    
    # For ARC
    center: Optional[Tuple[float, float, float]] = None
    radius: Optional[float] = None
    start_angle: Optional[float] = None
    end_angle: Optional[float] = None
    
    # For POLYLINE - list of vertices
    vertices: Optional[List[Tuple[float, float]]] = None
    is_closed: bool = False
    bulges: Optional[List[float]] = None  # For curved segments
    
    # For CIRCLE
    # Uses center and radius from ARC fields
    
    # Calculated
    length: Optional[float] = None
    
    # For TEXT/MTEXT - might contain rebar annotations
    text_content: Optional[str] = None


class DXFParser:
    """Parses DXF files and extracts entities"""
    
    def __init__(self, filepath: Path):
        self.filepath = Path(filepath)
        self.doc = None
        self.modelspace = None
        
    def parse(self) -> List[GeometricEntity]:
        """Parse the DXF file and return list of entities"""
        self.doc = ezdxf.readfile(str(self.filepath))
        self.modelspace = self.doc.modelspace()
        
        entities = []
        
        for entity in self.modelspace:
            parsed = self._parse_entity(entity)
            if parsed:
                entities.append(parsed)
        
        return entities
    
    def _parse_entity(self, entity) -> Optional[GeometricEntity]:
        """Parse a single DXF entity"""
        dxf = entity.dxf
        
        if isinstance(entity, Line):
            return self._parse_line(entity)
        elif isinstance(entity, Arc):
            return self._parse_arc(entity)
        elif isinstance(entity, (LWPolyline, Polyline)):
            return self._parse_polyline(entity)
        elif isinstance(entity, Circle):
            return self._parse_circle(entity)
        elif isinstance(entity, (Text, MText)):
            return self._parse_text(entity)
        
        return None
    
    def _parse_line(self, entity: Line) -> GeometricEntity:
        """Parse LINE entity"""
        dxf = entity.dxf
        start = (dxf.start.x, dxf.start.y, dxf.start.z)
        end = (dxf.end.x, dxf.end.y, dxf.end.z)
        
        # Calculate length
        length = (
            (end[0] - start[0])**2 + 
            (end[1] - start[1])**2 + 
            (end[2] - start[2])**2
        ) ** 0.5
        
        return GeometricEntity(
            entity_type="LINE",
            layer=dxf.layer,
            color=dxf.color if hasattr(dxf, 'color') else None,
            start_point=start,
            end_point=end,
            length=length
        )
    
    def _parse_arc(self, entity: Arc) -> GeometricEntity:
        """Parse ARC entity"""
        import math
        dxf = entity.dxf
        center = (dxf.center.x, dxf.center.y, dxf.center.z)
        
        # Calculate arc length
        angle_diff = dxf.end_angle - dxf.start_angle
        if angle_diff < 0:
            angle_diff += 360
        arc_length = 2 * math.pi * dxf.radius * (angle_diff / 360)
        
        return GeometricEntity(
            entity_type="ARC",
            layer=dxf.layer,
            color=dxf.color if hasattr(dxf, 'color') else None,
            center=center,
            radius=dxf.radius,
            start_angle=dxf.start_angle,
            end_angle=dxf.end_angle,
            length=arc_length
        )
    
    def _parse_polyline(self, entity) -> GeometricEntity:
        """Parse POLYLINE or LWPOLYLINE entity"""
        dxf = entity.dxf
        
        if isinstance(entity, LWPolyline):
            # LWPolyline has vertices as (x, y, start_width, end_width, bulge)
            points = list(entity.get_points(format='xyb'))
            vertices = [(p[0], p[1]) for p in points]
            bulges = [p[2] for p in points]
        else:
            # Regular Polyline
            vertices = [(v.dxf.location.x, v.dxf.location.y) for v in entity.vertices]
            bulges = [v.dxf.bulge if hasattr(v.dxf, 'bulge') else 0 for v in entity.vertices]
        
        # Calculate total length (simplified - doesn't account for bulges/curves yet)
        length = 0
        for i in range(len(vertices) - 1):
            dx = vertices[i+1][0] - vertices[i][0]
            dy = vertices[i+1][1] - vertices[i][1]
            length += (dx**2 + dy**2) ** 0.5
        
        # If closed, add distance from last to first
        is_closed = entity.closed if hasattr(entity, 'closed') else False
        if is_closed and len(vertices) > 1:
            dx = vertices[0][0] - vertices[-1][0]
            dy = vertices[0][1] - vertices[-1][1]
            length += (dx**2 + dy**2) ** 0.5
        
        return GeometricEntity(
            entity_type="POLYLINE",
            layer=dxf.layer,
            color=dxf.color if hasattr(dxf, 'color') else None,
            vertices=vertices,
            bulges=bulges,
            is_closed=is_closed,
            length=length
        )
    
    def _parse_circle(self, entity: Circle) -> GeometricEntity:
        """Parse CIRCLE entity"""
        import math
        dxf = entity.dxf
        center = (dxf.center.x, dxf.center.y, dxf.center.z)
        circumference = 2 * math.pi * dxf.radius
        
        return GeometricEntity(
            entity_type="CIRCLE",
            layer=dxf.layer,
            color=dxf.color if hasattr(dxf, 'color') else None,
            center=center,
            radius=dxf.radius,
            length=circumference
        )
    
    def _parse_text(self, entity) -> GeometricEntity:
        """Parse TEXT or MTEXT entity - might contain rebar annotations"""
        dxf = entity.dxf
        
        if isinstance(entity, MText):
            text_content = entity.text
        else:
            text_content = dxf.text
        
        return GeometricEntity(
            entity_type="TEXT",
            layer=dxf.layer,
            color=dxf.color if hasattr(dxf, 'color') else None,
            text_content=text_content
        )
    
    def get_layers(self) -> List[str]:
        """Get all layer names in the document"""
        if not self.doc:
            self.doc = ezdxf.readfile(str(self.filepath))
        return [layer.dxf.name for layer in self.doc.layers]
    
    def get_entity_summary(self) -> dict:
        """Get summary of entity types and counts"""
        if not self.doc:
            self.doc = ezdxf.readfile(str(self.filepath))
        if not self.modelspace:
            self.modelspace = self.doc.modelspace()
        
        summary = {}
        for entity in self.modelspace:
            entity_type = entity.dxftype()
            summary[entity_type] = summary.get(entity_type, 0) + 1
        
        return summary
