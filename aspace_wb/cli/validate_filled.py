"""
CLI entry point for validate_filled command
"""


def main():
    """Entry point that calls the original Validate_Filled.py script"""
    # Import and run the original script
    from ..scripts import validate_filled  # NOQA
    # The original script runs on import, so we don't need to call anything


if __name__ == "__main__":
    main()
