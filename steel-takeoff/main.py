#!/usr/bin/env python3
"""
Steel Quantity Takeoff
Main entry point for the application

IMPORTANT: This file handles the Python path setup so all modules can be found.
"""

import sys
import os

# ==============================================================================
# CRITICAL FIX: Add project root to Python path BEFORE any other imports
# This solves "ModuleNotFoundError: No module named 'domain'"
# ==============================================================================
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Now we can safely import our modules
from cli import main as cli_main


if __name__ == '__main__':
    sys.exit(cli_main())
