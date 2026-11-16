"""
CLI entry point for create_fillable command
"""


def main():
    """Entry point that calls the original Create_Fillable.py script"""
    # Import and run the original script
    from aspace_wb.scripts import create_fillable #NOQA
    create_fillable.run_script()


if __name__ == "__main__":
    main()
