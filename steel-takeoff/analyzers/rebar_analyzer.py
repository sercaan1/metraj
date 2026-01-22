"""
Rebar Analyzer
Main analysis orchestrator combining multiple parsers
"""

from pathlib import Path
from typing import List, Dict, Optional

from domain import RebarItem, RebarSchedule, ParseResult, DXFEntity
from config import AppSettings, is_rebar_layer
from parsers import DXFParser, PozBlockParser, TextAnnotationParser


class RebarAnalyzer:
    """
    Main analyzer that orchestrates rebar extraction from DXF files.
    
    Combines results from:
    - POZ block parser (structured block attributes)
    - Text annotation parser (free-form text)
    - Geometric analysis (optional, for lines/polylines on rebar layers)
    """
    
    def __init__(self, settings: Optional[AppSettings] = None):
        self.settings = settings or AppSettings.default()
        self._poz_parser = PozBlockParser()
        self._text_parser = TextAnnotationParser()
    
    def analyze_file(self, file_path: Path) -> RebarSchedule:
        """
        Analyze a DXF file and return a rebar schedule.
        
        Args:
            file_path: Path to the DXF file
            
        Returns:
            RebarSchedule containing all extracted rebar items
        """
        file_path = Path(file_path)
        
        # Parse DXF file
        dxf_parser = DXFParser(file_path)
        parse_result = dxf_parser.parse()
        
        # Create schedule
        schedule = RebarSchedule(
            project_name=file_path.stem,
            drawing_file=str(file_path)
        )
        
        # Extract from POZ blocks
        if self.settings.analyzer.analyze_poz_blocks:
            poz_items = self._poz_parser.parse_blocks(parse_result.entities)
            for item in poz_items:
                if self.settings.analyzer.merge_duplicates:
                    schedule.merge_item(item)
                else:
                    schedule.add_item(item)
        
        # Extract from text annotations
        if self.settings.analyzer.analyze_text:
            text_items = self._text_parser.parse_texts(parse_result.entities)
            for item in text_items:
                if self.settings.analyzer.merge_duplicates:
                    schedule.merge_item(item)
                else:
                    schedule.add_item(item)
        
        # Optional: analyze geometry on rebar layers
        if self.settings.analyzer.analyze_geometry:
            geo_items = self._analyze_geometry(parse_result.entities)
            for item in geo_items:
                if self.settings.analyzer.merge_duplicates:
                    schedule.merge_item(item)
                else:
                    schedule.add_item(item)
        
        return schedule
    
    def _analyze_geometry(self, entities: List[DXFEntity]) -> List[RebarItem]:
        """
        Analyze geometric entities on rebar layers.
        This is optional and often noisy.
        """
        items = []
        
        # Identify rebar layers
        rebar_layers = set()
        for entity in entities:
            if is_rebar_layer(entity.layer):
                rebar_layers.add(entity.layer)
        
        # Group entities by layer and analyze
        for layer in rebar_layers:
            layer_entities = [e for e in entities if e.layer == layer]
            
            # Analyze lines
            lines = [e for e in layer_entities if e.entity_type == "LINE"]
            line_items = self._analyze_lines(lines, layer)
            items.extend(line_items)
            
            # Analyze polylines
            polylines = [e for e in layer_entities if e.entity_type == "POLYLINE"]
            pline_items = self._analyze_polylines(polylines, layer)
            items.extend(pline_items)
        
        return items
    
    def _analyze_lines(self, lines: List[DXFEntity], layer: str) -> List[RebarItem]:
        """Analyze LINE entities for potential rebar"""
        from domain import RebarShape, RebarType
        
        items = []
        tolerance = self.settings.parser.length_tolerance
        min_length = self.settings.analyzer.min_rebar_length
        default_dia = self.settings.analyzer.default_diameter
        
        # Group lines by similar lengths
        length_groups: Dict[float, List[DXFEntity]] = {}
        
        for line in lines:
            if line.length is None or line.length < min_length:
                continue
            
            rounded_length = round(line.length / tolerance) * tolerance
            if rounded_length not in length_groups:
                length_groups[rounded_length] = []
            length_groups[rounded_length].append(line)
        
        # Create items for each length group
        for length, group in length_groups.items():
            if len(group) >= 1:
                items.append(RebarItem(
                    diameter=default_dia,
                    length=length,
                    quantity=len(group),
                    shape=RebarShape.STRAIGHT,
                    rebar_type=RebarType.MAIN,
                    layer=layer,
                    source="geometry_line"
                ))
        
        return items
    
    def _analyze_polylines(self, polylines: List[DXFEntity], layer: str) -> List[RebarItem]:
        """Analyze POLYLINE entities for potential rebar shapes"""
        from domain import RebarShape, RebarType
        
        items = []
        min_length = self.settings.analyzer.min_rebar_length
        max_stirrup = self.settings.analyzer.max_stirrup_length
        default_dia = self.settings.analyzer.default_diameter
        
        for pline in polylines:
            if not pline.vertices or len(pline.vertices) < 2:
                continue
            
            if pline.length is None or pline.length < min_length:
                continue
            
            # Determine shape based on vertices and closure
            num_vertices = len(pline.vertices)
            
            if pline.is_closed:
                if num_vertices == 4 and pline.length < max_stirrup:
                    shape = RebarShape.STIRRUP
                    rebar_type = RebarType.STIRRUP
                else:
                    shape = RebarShape.CLOSED
                    rebar_type = RebarType.MAIN
            elif num_vertices == 2:
                shape = RebarShape.STRAIGHT
                rebar_type = RebarType.MAIN
            elif num_vertices == 3:
                shape = RebarShape.L_SHAPE
                rebar_type = RebarType.MAIN
            elif num_vertices == 4:
                shape = RebarShape.U_SHAPE
                rebar_type = RebarType.MAIN
            else:
                shape = RebarShape.BENT
                rebar_type = RebarType.MAIN
            
            items.append(RebarItem(
                diameter=default_dia,
                length=pline.length,
                quantity=1,
                shape=shape,
                rebar_type=rebar_type,
                layer=layer,
                source="geometry_polyline"
            ))
        
        return items
    
    def get_file_summary(self, file_path: Path) -> Dict:
        """Get summary information about a DXF file without full analysis"""
        dxf_parser = DXFParser(file_path)
        parse_result = dxf_parser.parse()
        
        # Count POZ blocks
        poz_count = sum(
            1 for e in parse_result.entities 
            if e.entity_type == "INSERT" and e.block_name and e.block_name.lower() == "poz"
        )
        
        # Count text entities
        text_count = sum(1 for e in parse_result.entities if e.entity_type == "TEXT")
        
        # Find rebar layers
        rebar_layers = [layer for layer in parse_result.layers if is_rebar_layer(layer)]
        
        return {
            'file': str(file_path),
            'total_entities': parse_result.total_entities,
            'entity_counts': parse_result.entity_counts,
            'layers': parse_result.layers,
            'rebar_layers': rebar_layers,
            'blocks': parse_result.blocks,
            'poz_block_count': poz_count,
            'text_entity_count': text_count,
        }
