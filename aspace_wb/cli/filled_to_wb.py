"""
CLI entry point for filled_to_wb command
"""

import sys
import os

# Add project root to Python path to import original script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


def main():
    """Entry point that calls the original Filled_to_WB.py script"""
    # Import and run the original script
    import Filled_to_WB
    # The original script runs on import, so we don't need to call anything


if __name__ == "__main__":
    main()
