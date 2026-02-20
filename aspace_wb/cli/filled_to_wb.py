"""
CLI entry point for filled_to_wb command
"""


def main():
    """Entry point that calls the original Filled_to_WB.py script"""
    # Import and run the original script
    from aspace_wb.scripts import filled_to_wb  # NOQA
    # The original script runs on import, so we don't need to call anything


if __name__ == "__main__":
    main()
