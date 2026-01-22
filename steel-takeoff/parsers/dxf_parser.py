"""
DXF Parser
Parses DXF files and extracts geometric entities
"""

import math
from pathlib import Path
from typing import List, Dict, Optional

import ezdxf
from ezdxf.entities import Line, Arc, LWPolyline, Polyline, Circle, Text, MText, Insert

from domain import DXFEntity, ParseResult
from .base import BaseParser


class DXFParser(BaseParser):
    """Parser for DXF (Drawing Exchange Format) files"""
    
    def __init__(self, file_path: Path):
        super().__init__(file_path)
        self._doc = None
        self._modelspace = None
    
    @property
    def supported_extensions(self) -> tuple:
        return ('.dxf',)
    
    @property
    def doc(self):
        """Lazy load the DXF document"""
        if self._doc is None:
            self._doc = ezdxf.readfile(str(self.file_path))
        return self._doc
    
    @property
    def modelspace(self):
        """Get the modelspace"""
        if self._modelspace is None:
            self._modelspace = self.doc.modelspace()
        return self._modelspace
    
    def parse(self) -> ParseResult:
        """Parse the DXF file and return all entities"""
        entities = []
        entity_counts: Dict[str, int] = {}
        
        for entity in self.modelspace:
            parsed = self._parse_entity(entity)
            if parsed:
                entities.append(parsed)
                entity_type = parsed.entity_type
                entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
        
        return ParseResult(
            entities=entities,
            layers=self.get_layers(),
            blocks=self.get_block_names(),
            entity_counts=entity_counts,
            file_path=str(self.file_path)
        )
    
    def _parse_entity(self, entity) -> Optional[DXFEntity]:
        """Parse a single DXF entity based on its type"""
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
        elif isinstance(entity, Insert):
            return self._parse_insert(entity)
        return None
    
    def _parse_line(self, entity: Line) -> DXFEntity:
        """Parse LINE entity"""
        dxf = entity.dxf
        start = (dxf.start.x, dxf.start.y, dxf.start.z)
        end = (dxf.end.x, dxf.end.y, dxf.end.z)
        
        length = math.sqrt(
            (end[0] - start[0])**2 +
            (end[1] - start[1])**2 +
            (end[2] - start[2])**2
        )
        
        return DXFEntity(
            entity_type="LINE",
            layer=dxf.layer,
            color=getattr(dxf, 'color', None),
            start_point=start,
            end_point=end,
            length=length
        )
    
    def _parse_arc(self, entity: Arc) -> DXFEntity:
        """Parse ARC entity"""
        dxf = entity.dxf
        center = (dxf.center.x, dxf.center.y, dxf.center.z)
        
        angle_diff = dxf.end_angle - dxf.start_angle
        if angle_diff < 0:
            angle_diff += 360
        arc_length = 2 * math.pi * dxf.radius * (angle_diff / 360)
        
        return DXFEntity(
            entity_type="ARC",
            layer=dxf.layer,
            color=getattr(dxf, 'color', None),
            center=center,
            radius=dxf.radius,
            start_angle=dxf.start_angle,
            end_angle=dxf.end_angle,
            length=arc_length
        )
    
    def _parse_polyline(self, entity) -> DXFEntity:
        """Parse POLYLINE or LWPOLYLINE entity"""
        dxf = entity.dxf
        
        if isinstance(entity, LWPolyline):
            points = list(entity.get_points(format='xyb'))
            vertices = [(p[0], p[1]) for p in points]
            bulges = [p[2] for p in points]
        else:
            vertices = [(v.dxf.location.x, v.dxf.location.y) for v in entity.vertices]
            bulges = [getattr(v.dxf, 'bulge', 0) for v in entity.vertices]
        
        # Calculate length
        length = 0.0
        for i in range(len(vertices) - 1):
            dx = vertices[i + 1][0] - vertices[i][0]
            dy = vertices[i + 1][1] - vertices[i][1]
            length += math.sqrt(dx**2 + dy**2)
        
        is_closed = getattr(entity, 'closed', False)
        if is_closed and len(vertices) > 1:
            dx = vertices[0][0] - vertices[-1][0]
            dy = vertices[0][1] - vertices[-1][1]
            length += math.sqrt(dx**2 + dy**2)
        
        return DXFEntity(
            entity_type="POLYLINE",
            layer=dxf.layer,
            color=getattr(dxf, 'color', None),
            vertices=vertices,
            bulges=bulges,
            is_closed=is_closed,
            length=length
        )
    
    def _parse_circle(self, entity: Circle) -> DXFEntity:
        """Parse CIRCLE entity"""
        dxf = entity.dxf
        center = (dxf.center.x, dxf.center.y, dxf.center.z)
        circumference = 2 * math.pi * dxf.radius
        
        return DXFEntity(
            entity_type="CIRCLE",
            layer=dxf.layer,
            color=getattr(dxf, 'color', None),
            center=center,
            radius=dxf.radius,
            length=circumference
        )
    
    def _parse_text(self, entity) -> DXFEntity:
        """Parse TEXT or MTEXT entity"""
        dxf = entity.dxf
        
        if isinstance(entity, MText):
            text_content = entity.text
            insertion = (entity.dxf.insert.x, entity.dxf.insert.y, entity.dxf.insert.z)
        else:
            text_content = dxf.text
            insertion = (dxf.insert.x, dxf.insert.y, dxf.insert.z)
        
        return DXFEntity(
            entity_type="TEXT",
            layer=dxf.layer,
            color=getattr(dxf, 'color', None),
            text_content=text_content,
            insertion_point=insertion
        )
    
    def _parse_insert(self, entity: Insert) -> DXFEntity:
        """Parse INSERT (block reference) entity"""
        dxf = entity.dxf
        
        # Extract block attributes
        attributes = {}
        for attrib in entity.attribs:
            attributes[attrib.dxf.tag] = attrib.dxf.text
        
        insertion = (dxf.insert.x, dxf.insert.y, dxf.insert.z)
        
        return DXFEntity(
            entity_type="INSERT",
            layer=dxf.layer,
            color=getattr(dxf, 'color', None),
            block_name=dxf.name,
            attributes=attributes,
            insertion_point=insertion
        )
    
    def get_layers(self) -> List[str]:
        """Get all layer names in the document"""
        return [layer.dxf.name for layer in self.doc.layers]
    
    def get_block_names(self) -> List[str]:
        """Get all block definition names"""
        return [block.name for block in self.doc.blocks if not block.name.startswith('*')]
    
    def get_entities_by_type(self, entity_type: str) -> List[DXFEntity]:
        """Get all entities of a specific type"""
        result = self.parse()
        return [e for e in result.entities if e.entity_type == entity_type]
    
    def get_entities_by_layer(self, layer_name: str) -> List[DXFEntity]:
        """Get all entities on a specific layer"""
        result = self.parse()
        return [e for e in result.entities if e.layer == layer_name]
    
    def get_block_inserts(self, block_name: str) -> List[DXFEntity]:
        """Get all INSERT entities for a specific block"""
        result = self.parse()
        return [
            e for e in result.entities 
            if e.entity_type == "INSERT" and e.block_name.lower() == block_name.lower()
        ]
