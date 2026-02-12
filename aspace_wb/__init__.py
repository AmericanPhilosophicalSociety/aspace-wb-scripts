"""
ASpace Workbench Scripts Package

This package provides tools for American Philosophical Society (APS) staff to prepare
CSV files for ingesting files into Islandora 8 using Workbench. It automates metadata
extraction from media files and ArchivesSpace Bulk Update Spreadsheets.
"""

__version__ = "0.1.0"
__author__ = "American Philosophical Society"
__email__ = "cds@amphilsoc.org"

from .core.specs import *

__all__ = [
    "FILESTOUPLOAD_DIR",
    "METADATA_DIR",
    "CV_DIR",
    "FIELDS_DIR",
    "AS_AGENTS_FILENAME",
    "ISO639_FILENAME",
    "CNAIR_SUBJECTS_FILENAME",
    "RELATOR_CODES_FILENAME",
    "LANGUAGE_NAMES",
    "LANGUAGE_CODES",
    "CNAIR_SUBJECTS",
    "RELATOR_CODES",
    "VALIDATE_ERROR_PREFIX",
    "AS_DIGITAL_OBJECT_NODE_PREFIX",
    "AS_DIGITAL_OBJECT_FILE_URI_PREFIX",
    "BOOK_TITLE_URL_ALIAS_LENGTH",
    "field_digital_origin",
    "field_reformatting_quality",
    "field_model_BOOK",
    "field_resource_type_BOOK",
    "file_SINGLE_PREFIX",
    "url_alias_PREFIX",
    "WB_FIELDS_REQUIRED_AT_INPUT_SINGLE",
    "WB_FIELDS_REQUIRED_AT_INPUT_BOOK",
    "WB_FIELDS_REQUIRED_AT_WORKBENCH_SINGLE",
    "WB_FIELDS_REQUIRED_AT_WORKBENCH_BOOK",
    "WB_FIELDS_ORDERED_WITH_DESCRIPTION",
    "extension_to_WB_field",
]
