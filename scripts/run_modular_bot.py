#!/usr/bin/env python3
"""
Launcher script for the modular bot client
"""
import os
import sys

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import and run the modular bot client
from core.modular_bot_client import main

if __name__ == "__main__":
    sys.exit(main())
