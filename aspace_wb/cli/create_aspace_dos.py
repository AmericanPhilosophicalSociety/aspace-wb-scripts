"""
CLI entry point for create_aspace_dos command
"""


def main():
    """Entry point that calls the original Create_ASpace_DOs.py script"""
    # Import and run the original script
    from aspace_wb.scripts import create_aspace_dos  # NOQA
    # The original script runs on import, so we don't need to call anything


if __name__ == "__main__":
    main()
