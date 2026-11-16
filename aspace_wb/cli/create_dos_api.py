"""
CLI entry point for create_dos_api command
"""


def main():
    """Entry point that calls the original Create_ASpace_DOs.py script"""
    # Import and run the original script
    from aspace_wb.scripts import create_dos_api  # NOQA
    create_dos_api.run_script()


if __name__ == "__main__":
    main()
