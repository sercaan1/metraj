#!/usr/bin/env python3
"""
Installation Test Script
Run this to verify all modules are properly installed and importable.

Usage:
    python test_install.py
"""

import sys
import os

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


def test_imports():
    """Test that all modules can be imported"""
    print("Testing module imports...")
    print("-" * 50)
    
    modules = [
        ("domain", "Domain models"),
        ("domain.models", "RebarItem, RebarSchedule"),
        ("domain.constants", "UNIT_WEIGHTS, STANDARD_DIAMETERS"),
        ("config", "Configuration"),
        ("config.settings", "AppSettings"),
        ("config.patterns", "Regex patterns"),
        ("parsers", "Parsers"),
        ("parsers.dxf_parser", "DXFParser"),
        ("parsers.poz_block_parser", "PozBlockParser"),
        ("parsers.text_annotation_parser", "TextAnnotationParser"),
        ("analyzers", "Analyzers"),
        ("analyzers.rebar_analyzer", "RebarAnalyzer"),
        ("services", "Services"),
        ("services.takeoff_service", "TakeoffService"),
        ("services.calculation_service", "CalculationService"),
        ("exporters", "Exporters"),
        ("exporters.console_exporter", "ConsoleExporter"),
        ("exporters.excel_exporter", "ExcelExporter"),
        ("cli", "CLI"),
        ("utils", "Utilities"),
    ]
    
    success = 0
    failed = 0
    
    for module_name, description in modules:
        try:
            __import__(module_name)
            print(f"  ✓ {module_name:40} - {description}")
            success += 1
        except ImportError as e:
            print(f"  ✗ {module_name:40} - FAILED: {e}")
            failed += 1
    
    print("-" * 50)
    print(f"Results: {success} passed, {failed} failed")
    
    return failed == 0


def test_dependencies():
    """Test that external dependencies are installed"""
    print("\nTesting external dependencies...")
    print("-" * 50)
    
    deps = [
        ("ezdxf", "DXF file parsing"),
        ("pandas", "Data handling"),
        ("openpyxl", "Excel export"),
        ("rich", "Console output"),
    ]
    
    success = 0
    failed = 0
    
    for module_name, description in deps:
        try:
            __import__(module_name)
            print(f"  ✓ {module_name:40} - {description}")
            success += 1
        except ImportError as e:
            print(f"  ✗ {module_name:40} - NOT INSTALLED: {e}")
            failed += 1
    
    print("-" * 50)
    print(f"Results: {success} passed, {failed} failed")
    
    if failed > 0:
        print("\nTo install missing dependencies, run:")
        print("  pip install -r requirements.txt")
    
    return failed == 0


def test_basic_functionality():
    """Test basic functionality"""
    print("\nTesting basic functionality...")
    print("-" * 50)
    
    try:
        from domain import RebarItem, RebarSchedule, UNIT_WEIGHTS
        
        # Create a test item
        item = RebarItem(
            diameter=12,
            length=1000,  # 1 meter in mm
            quantity=10,
            shape="STRAIGHT"
        )
        
        # Check calculations
        assert item.total_length_m == 10.0, "Length calculation failed"
        assert item.unit_weight == 0.888, "Unit weight lookup failed"
        assert abs(item.weight_kg - 8.88) < 0.01, "Weight calculation failed"
        
        print(f"  ✓ RebarItem calculations working correctly")
        print(f"    - 10 bars of ø12, 1m each = {item.weight_kg:.2f} kg")
        
        # Test schedule
        schedule = RebarSchedule(project_name="Test")
        schedule.add_item(item)
        
        assert len(schedule.items) == 1, "Schedule add_item failed"
        assert abs(schedule.total_weight_kg - 8.88) < 0.01, "Schedule weight failed"
        
        print(f"  ✓ RebarSchedule working correctly")
        print(f"    - Total weight: {schedule.total_weight_kg:.2f} kg")
        
        print("-" * 50)
        print("Basic functionality: PASSED")
        return True
        
    except Exception as e:
        print(f"  ✗ Error: {e}")
        print("-" * 50)
        print("Basic functionality: FAILED")
        return False


def main():
    print("=" * 50)
    print("Steel Quantity Takeoff - Installation Test")
    print("=" * 50)
    print(f"Python version: {sys.version}")
    print(f"Project root: {PROJECT_ROOT}")
    print()
    
    all_passed = True
    
    all_passed &= test_dependencies()
    all_passed &= test_imports()
    all_passed &= test_basic_functionality()
    
    print()
    print("=" * 50)
    if all_passed:
        print("ALL TESTS PASSED! Installation is correct.")
        print("=" * 50)
        print("\nYou can now run:")
        print("  python main.py analyze your_drawing.dxf")
        return 0
    else:
        print("SOME TESTS FAILED! Please check the errors above.")
        print("=" * 50)
        return 1


if __name__ == '__main__':
    sys.exit(main())
