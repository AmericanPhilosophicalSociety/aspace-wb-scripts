"""
CLI entry point for validate_filled command
"""


def main():
    """Entry point that calls the fillable_from_api.py script"""
    # Import and run the original script
    from aspace_wb.scripts import fillable_from_api  # NOQA
    # The original script runs on import, so we don't need to call anything


if __name__ == "__main__":
    main()
