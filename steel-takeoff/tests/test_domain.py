"""
Unit Tests for Domain Models
"""

import unittest
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from domain import RebarItem, RebarSchedule, UNIT_WEIGHTS, RebarShape, RebarType


class TestRebarItem(unittest.TestCase):
    """Tests for RebarItem model"""
    
    def test_total_length_calculation(self):
        """Test total length calculation"""
        item = RebarItem(diameter=12, length=1000, quantity=10, shape=RebarShape.STRAIGHT)
        self.assertEqual(item.total_length_m, 10.0)  # 10 * 1000mm = 10m
    
    def test_unit_weight_lookup(self):
        """Test unit weight lookup"""
        item = RebarItem(diameter=12, length=1000, quantity=1, shape=RebarShape.STRAIGHT)
        self.assertEqual(item.unit_weight, 0.888)
    
    def test_weight_calculation(self):
        """Test weight calculation"""
        item = RebarItem(diameter=12, length=1000, quantity=10, shape=RebarShape.STRAIGHT)
        expected_weight = 10.0 * 0.888  # 10m * 0.888 kg/m
        self.assertAlmostEqual(item.weight_kg, expected_weight, places=3)
    
    def test_invalid_diameter(self):
        """Test that invalid diameter returns zero unit weight"""
        item = RebarItem(diameter=99, length=1000, quantity=1, shape=RebarShape.STRAIGHT)
        self.assertEqual(item.unit_weight, 0)


class TestRebarSchedule(unittest.TestCase):
    """Tests for RebarSchedule model"""
    
    def setUp(self):
        self.schedule = RebarSchedule(project_name="Test Project")
    
    def test_add_item(self):
        """Test adding items"""
        item = RebarItem(diameter=12, length=1000, quantity=10, shape=RebarShape.STRAIGHT)
        self.schedule.add_item(item)
        self.assertEqual(len(self.schedule.items), 1)
    
    def test_merge_item_same_position(self):
        """Test merging items with same position"""
        item1 = RebarItem(diameter=12, length=1000, quantity=5, position="1", shape=RebarShape.STRAIGHT)
        item2 = RebarItem(diameter=12, length=1000, quantity=3, position="1", shape=RebarShape.STRAIGHT)
        
        self.schedule.merge_item(item1)
        self.schedule.merge_item(item2)
        
        self.assertEqual(len(self.schedule.items), 1)
        self.assertEqual(self.schedule.items[0].quantity, 8)
    
    def test_merge_item_different_position(self):
        """Test that different positions are not merged"""
        item1 = RebarItem(diameter=12, length=1000, quantity=5, position="1", shape=RebarShape.STRAIGHT)
        item2 = RebarItem(diameter=12, length=1000, quantity=3, position="2", shape=RebarShape.STRAIGHT)
        
        self.schedule.merge_item(item1)
        self.schedule.merge_item(item2)
        
        self.assertEqual(len(self.schedule.items), 2)
    
    def test_total_weight(self):
        """Test total weight calculation"""
        item1 = RebarItem(diameter=12, length=1000, quantity=10, shape=RebarShape.STRAIGHT)  # 8.88 kg
        item2 = RebarItem(diameter=16, length=1000, quantity=10, shape=RebarShape.STRAIGHT)  # 15.78 kg
        
        self.schedule.add_item(item1)
        self.schedule.add_item(item2)
        
        expected = (10 * 0.888) + (10 * 1.578)
        self.assertAlmostEqual(self.schedule.total_weight_kg, expected, places=2)
    
    def test_by_diameter_grouping(self):
        """Test grouping by diameter"""
        self.schedule.add_item(RebarItem(diameter=12, length=1000, quantity=5, shape=RebarShape.STRAIGHT))
        self.schedule.add_item(RebarItem(diameter=12, length=500, quantity=3, shape=RebarShape.STRAIGHT))
        self.schedule.add_item(RebarItem(diameter=16, length=1000, quantity=2, shape=RebarShape.STRAIGHT))
        
        by_dia = self.schedule.by_diameter()
        
        self.assertEqual(len(by_dia[12]), 2)
        self.assertEqual(len(by_dia[16]), 1)


class TestUnitWeights(unittest.TestCase):
    """Tests for unit weight constants"""
    
    def test_common_diameters_present(self):
        """Test that common diameters are defined"""
        common = [8, 10, 12, 14, 16, 18, 20, 22, 25, 28, 32]
        for dia in common:
            self.assertIn(dia, UNIT_WEIGHTS)
    
    def test_weights_are_positive(self):
        """Test that all weights are positive"""
        for dia, weight in UNIT_WEIGHTS.items():
            self.assertGreater(weight, 0)
    
    def test_weights_increase_with_diameter(self):
        """Test that weights increase with diameter"""
        diameters = sorted(UNIT_WEIGHTS.keys())
        for i in range(len(diameters) - 1):
            self.assertLess(
                UNIT_WEIGHTS[diameters[i]], 
                UNIT_WEIGHTS[diameters[i + 1]]
            )


if __name__ == '__main__':
    unittest.main()
