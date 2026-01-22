"""
Calculation Service
Weight and length calculations for rebar
"""

from typing import Dict, List

from domain import RebarItem, RebarSchedule, UNIT_WEIGHTS


class CalculationService:
    """Service for rebar calculations"""
    
    @staticmethod
    def calculate_item_weight(item: RebarItem) -> float:
        """Calculate weight for a single rebar item in kg"""
        total_length_m = (item.length * item.quantity) / 1000
        unit_weight = UNIT_WEIGHTS.get(item.diameter, 0.0)
        return total_length_m * unit_weight
    
    @staticmethod
    def calculate_schedule_weight(schedule: RebarSchedule) -> float:
        """Calculate total weight for a schedule in kg"""
        return sum(item.weight_kg for item in schedule.items)
    
    @staticmethod
    def calculate_schedule_length(schedule: RebarSchedule) -> float:
        """Calculate total length for a schedule in meters"""
        return sum(item.total_length_m for item in schedule.items)
    
    @staticmethod
    def summarize_by_diameter(schedule: RebarSchedule) -> Dict[int, Dict]:
        """
        Get summary statistics grouped by diameter.
        
        Returns dict with structure:
        {
            12: {
                'diameter': 12,
                'total_quantity': 50,
                'total_length_m': 125.5,
                'total_weight_kg': 111.44,
                'unit_weight': 0.888
            },
            ...
        }
        """
        summary: Dict[int, Dict] = {}
        
        for item in schedule.items:
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
    
    @staticmethod
    def summarize_by_position(schedule: RebarSchedule) -> Dict[str, Dict]:
        """
        Get summary statistics grouped by position (POZ).
        
        Returns dict with structure:
        {
            '1': {
                'position': '1',
                'diameter': 12,
                'total_quantity': 10,
                'length_mm': 800,
                'total_length_m': 8.0,
                'total_weight_kg': 7.1,
                'location': 'Kiriş'
            },
            ...
        }
        """
        summary: Dict[str, Dict] = {}
        
        for item in schedule.items:
            pos = item.position or 'NO_POZ'
            
            if pos not in summary:
                summary[pos] = {
                    'position': pos,
                    'diameter': item.diameter,
                    'total_quantity': 0,
                    'length_mm': item.length,
                    'total_length_m': 0.0,
                    'total_weight_kg': 0.0,
                    'unit_weight': UNIT_WEIGHTS.get(item.diameter, 0.0),
                    'location': item.location,
                    'rebar_type': item.rebar_type,
                }
            
            summary[pos]['total_quantity'] += item.quantity
            summary[pos]['total_length_m'] += item.total_length_m
            summary[pos]['total_weight_kg'] += item.weight_kg
        
        return summary
    
    @staticmethod
    def get_diameter_breakdown(schedule: RebarSchedule) -> List[Dict]:
        """
        Get detailed breakdown by diameter for reporting.
        Returns a list sorted by diameter.
        """
        summary = CalculationService.summarize_by_diameter(schedule)
        
        result = []
        for diameter in sorted(summary.keys()):
            data = summary[diameter]
            result.append({
                'diameter': diameter,
                'diameter_str': f'ø{diameter}',
                'total_quantity': data['total_quantity'],
                'total_length_m': round(data['total_length_m'], 2),
                'unit_weight_kg_m': data['unit_weight'],
                'total_weight_kg': round(data['total_weight_kg'], 2),
            })
        
        return result
    
    @staticmethod
    def get_position_breakdown(schedule: RebarSchedule) -> List[Dict]:
        """
        Get detailed breakdown by position for reporting.
        Returns a list sorted by position number.
        """
        summary = CalculationService.summarize_by_position(schedule)
        
        result = []
        for pos in sorted(summary.keys(), key=lambda x: int(x) if x.isdigit() else float('inf')):
            data = summary[pos]
            result.append({
                'position': pos,
                'diameter': data['diameter'],
                'diameter_str': f'ø{data["diameter"]}',
                'quantity': data['total_quantity'],
                'length_mm': data['length_mm'],
                'length_cm': data['length_mm'] / 10 if data['length_mm'] else 0,
                'total_length_m': round(data['total_length_m'], 2),
                'unit_weight_kg_m': data['unit_weight'],
                'total_weight_kg': round(data['total_weight_kg'], 2),
                'location': data['location'] or '',
                'rebar_type': data['rebar_type'],
            })
        
        return result
    
    @staticmethod
    def summarize_by_diameter_and_type(schedule: RebarSchedule) -> Dict[str, Dict]:
        """
        Get summary statistics grouped by diameter AND type/location.
        This matches the original CLI tool's behavior for text-based annotations.
        
        Returns dict with structure:
        {
            '8_döşeme_alt': {
                'diameter': 8,
                'location': 'döşeme_alt',
                'total_quantity': 959,
                'total_length_cm': 542155,
                'total_length_m': 5421.55,
                'total_weight_kg': 2141.51,
            },
            ...
        }
        """
        summary: Dict[str, Dict] = {}
        
        for item in schedule.items:
            # Create key from diameter and location (type)
            location = item.location or 'unknown'
            key = f"{item.diameter}_{location}"
            
            if key not in summary:
                summary[key] = {
                    'diameter': item.diameter,
                    'location': location,
                    'total_quantity': 0,
                    'total_length_cm': 0,  # Track in cm like original tool
                    'total_length_m': 0.0,
                    'total_weight_kg': 0.0,
                    'unit_weight': UNIT_WEIGHTS.get(item.diameter, 0.0),
                }
            
            summary[key]['total_quantity'] += item.quantity
            # item.length is in mm, convert to cm for tracking
            length_cm = item.length / 10
            summary[key]['total_length_cm'] += item.quantity * length_cm
            summary[key]['total_length_m'] += item.total_length_m
            summary[key]['total_weight_kg'] += item.weight_kg
        
        return summary
    
    @staticmethod
    def get_diameter_type_breakdown(schedule: RebarSchedule) -> List[Dict]:
        """
        Get detailed breakdown by diameter AND type for text-based annotations.
        Matches the original CLI tool's output format.
        Returns a list sorted by diameter then type.
        """
        summary = CalculationService.summarize_by_diameter_and_type(schedule)
        
        result = []
        # Sort by diameter first, then by location name
        for key in sorted(summary.keys(), key=lambda x: (int(x.split('_')[0]), x.split('_', 1)[1] if '_' in x else '')):
            data = summary[key]
            result.append({
                'diameter': data['diameter'],
                'diameter_str': f'ø{data["diameter"]}',
                'location': data['location'],
                'quantity': data['total_quantity'],
                'total_length_m': round(data['total_length_m'], 2),
                'unit_weight_kg_m': data['unit_weight'],
                'total_weight_kg': round(data['total_weight_kg'], 2),
            })
        
        return result
