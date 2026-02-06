# AGENTS.md

This file contains guidelines for agentic coding agents working in the aspace-wb-scripts repository.

## Overview

This is a Python project for American Philosophical Society (APS) staff to prepare CSV files for ingesting files into Islandora 8 using Workbench. The project automates metadata extraction from media files and ArchivesSpace Bulk Update Spreadsheets.

## Development Commands

### Environment Setup
```bash
# Create virtual environment (Python 3.7+ required, preferably 3.11)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create required directories
mkdir -p files_to_upload metadata CVs fields
```

### Running Scripts
```bash
# Main workflow - run in order:
python Create_Fillable.py book --fields fields --AS archivesspace_file.xlsx
python Validate_Filled.py book filled_file.xlsx
python Filled_to_WB.py book filled_file.xlsx
python Create_ASpace_DOs.py workbench_output.csv

# Create blank template
python Create_Blank_Fillable.py book --fields fields
```

### Testing
No formal testing framework is currently configured. The project lacks comprehensive test coverage. Testing is done manually by running the scripts with sample data.

### Code Quality
No linting or formatting tools are currently configured. Consider setting up:
- `flake8` or `pylint` for linting
- `black` for code formatting
- `pytest` for testing

## Code Style Guidelines

### Imports
- Group imports in this order: standard library, third-party, local modules
- Use absolute imports for local modules (e.g., `import utilities.validate as validate`)
- Keep import aliases short and descriptive
- Import only what you need from modules

### Formatting
- Use 4 spaces for indentation (never tabs)
- Maximum line length: 100 characters (follow existing patterns)
- Use triple quotes for docstrings
- Add blank lines between top-level function definitions

### Naming Conventions
- **Variables**: snake_case (e.g., `WB_type`, `fields_in_use`)
- **Functions**: snake_case (e.g., `CSV_col_to_list`, `unix_time_created`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `FILESTOUPLOAD_DIR`, `WB_FIELDS_REQUIRED`)
- **Files**: snake_case.py for modules, PascalCase.py for main scripts
- **Classes**: PascalCase (rarely used in this codebase)

### Error Handling
- Use specific exception types (ValueError, FileNotFoundError, etc.)
- Include descriptive error messages with context
- Use raise ValueError() for validation errors with the field name and reason
- Wrap file operations in try-except blocks where appropriate

### Documentation
- Add docstrings to all functions explaining purpose, parameters, and return values
- Use triple quotes (''') for docstrings
- Add inline comments for complex logic or business rules
- Include TODO comments for future improvements

### File Structure Patterns
- Main scripts in root directory (e.g., `Create_Fillable.py`)
- Utility modules in `utilities/` directory
- Configuration and constants in `default_specs.py`
- Field definitions in `fields/` directory as CSV files
- Controlled vocabularies in `CVs/` directory

## Project-Specific Patterns

### Argument Parsing
- Use `argparse.ArgumentParser()` for command-line interfaces
- Define choices for restricted options (e.g., `choices=('single', 'book')`)
- Include descriptive help text and expected usage examples

### Data Processing
- Use pandas for spreadsheet operations
- Use openpyxl for Excel file handling
- Process files in batches when possible
- Validate inputs before processing

### File Path Handling
- Use `os.path.join()` for cross-platform compatibility
- Define directory constants in `default_specs.py`
- Use forward slashes in user-facing examples even on Windows

### Metadata Extraction
- Use mutagen for audio file metadata
- Use moviepy for video file metadata
- Extract file timestamps using os.path functions
- Handle missing metadata gracefully with defaults

## Working with Controlled Vocabularies

The project uses several controlled vocabularies stored in CSV files:
- `iso639.csv` - Language codes (ISO 639 standard)
- `cnair_subject.csv` - CNAIR subject terms
- `relator.csv` - Library of Congress relator codes
- `agents_in_AS.csv` - ArchivesSpace agents

When updating vocabularies:
1. Verify the format matches existing files
2. Update `default_specs.py` if field structure changes
3. Test with sample data to ensure compatibility

## Common Patterns to Follow

### Validation Functions
```python
def function_name(input):
    """Brief description"""
    if condition:
        return True
    else:
        raise ValueError("Descriptive error message: " + str(input))
```

### File Processing
```python
# Check file existence first
if not os.path.exists(filepath):
    raise FileNotFoundError("File not found: " + filepath)

# Process file with error handling
try:
    result = process_file(filepath)
except Exception as e:
    raise ValueError(f"Error processing {filepath}: {str(e)}")
```

### CSV Operations
```python
# Use utilities.use_CSVs for consistent CSV handling
import utilities.use_CSVs as use_CSVs
data_list = use_CSVs.CSV_col_to_list(filepath, column_index)
```

## When Making Changes

1. **Check existing patterns first** - Look at similar functions before implementing new ones
2. **Update constants** - Add new fields to `default_specs.py` if needed
3. **Consider dependencies** - Check if new packages need to be added to requirements.txt
4. **Test manually** - Run the complete workflow with sample data
5. **Document changes** - Update README.md if workflow changes

## Directory Structure Notes

```
aspace-wb-scripts/
├── Create_Fillable.py          # Main fillable spreadsheet creator
├── Validate_Filled.py          # Validation script
├── Filled_to_WB.py            # Workbench CSV exporter
├── Create_ASpace_DOs.py       # ArchivesSpace DO creator
├── default_specs.py           # Constants and field definitions
├── requirements.txt           # Python dependencies
├── utilities/                 # Reusable utility modules
├── fields/                    # Field definition CSV files
├── CVs/                       # Controlled vocabulary files
├── files_to_upload/          # Media files directory (user-created)
└── metadata/                  # Output directory (user-created)
```