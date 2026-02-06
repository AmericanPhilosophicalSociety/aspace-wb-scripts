"""
CLI entry point for create_fillable command
"""

import sys
import os

# Add the project root to Python path to import original script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


def main():
    """Entry point that calls the original Create_Fillable.py script"""
    # Import and run the original script
    import Create_Fillable
    # The original script runs on import, so we don't need to call anything


if __name__ == "__main__":
    main()
