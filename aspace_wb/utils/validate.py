"""
Functions for validating fields
These all take a single instance of something

EDTF standard defined here: https://www.loc.gov/standards/datetime/
"""

try:
    import edtf_validate.valid_edtf
except ImportError:
    edtf_validate = None
import re
import math

try:
    import pandas
except ImportError:
    pandas = None
import os
from ..core import specs as c
from . import extract_dir, extract_file

"""
Functions
"""


def nan(input):
    """
    returns True if nan, False if not
    """
    hiimnan = False
    if isinstance(input, float):
        if math.isnan(input):
            hiimnan = True
    return hiimnan


def agent_type(input):
    agent_types = ("p", "c", "f", "person", "corporate_body", "family")
    if input in agent_types:
        return True
    else:
        raise ValueError("field_linked_agent_TYPE not valid: " + str(input))


def CNAIR_culture(input):
    if input in c.CNAIR_SUBJECTS:
        return True
    else:
        raise ValueError(
            "CNAIR subject "
            + str(input)
            + " not in current csv. CSV may be outdated. If a new term, contact CNAIR."
        )


def EDTF(input):
    # checks EDTF standard 2019. no discrimination for levels but this is possible with the library.
    input = str(input)
    if edtf_validate.valid_edtf.is_valid(input):
        return True
    else:
        raise ValueError("EDTF date not valid: " + str(input))


def directory_contains_only_subdirectories(directory_path):
    """
    Returns True if directory contains only subdirectories, and is not empty
    """
    if extract_dir.subdirectories_count(directory_path) == 0:
        raise OSError(
            "Folder "
            + str(directory_path)
            + " contains no directories. Please put your directories with their files in."
        )
    elif extract_dir.file_count(directory_path):
        raise OSError(
            "Folder "
            + str(directory_path)
            + " contains files, not just folders. Move files into book subfolders."
        )
    else:
        return True


def directory_contains_only_files(directory_path):
    """
    Returns True if directory contains only files, and is not empty
    """
    if extract_dir.file_count(directory_path) == 0:
        raise OSError(
            "Folder "
            + str(directory_path)
            + " contains no files. Please place files there."
        )
    elif extract_dir.subdirectories_count(directory_path):
        raise OSError(
            "Folder "
            + str(directory_path)
            + " contains folders. It should only contain files."
        )
    else:
        return True


def directory_name_for_book(directory_name):
    """
    Returns True if directory name in book is only alphanumeric and underscore
    """
    if re.match(r"^\w+$", directory_name):
        return True
    else:
        raise OSError(
            "Folder "
            + str(directory_name)
            + " is not just alphanumeric and underscores. Please revise."
        )


def filename_for_book(directory_name, filename_noext):
    """
    Given a directory name and filename, returns True if filename is only directory + hyphen + numbers
    """
    if not string_is_match_then_hyphen_then_numbers(filename_noext, directory_name):
        raise OSError(
            "File "
            + str(filename_noext)
            + " does not match expected: parent directory + hyphen + numbers. Check all files."
        )
    else:
        return True


def filename_for_single(filename_noext):
    """
    Returns True if filename matches rules for single uploads
    """
    if re.match(r"^[a-zA-Z0-9-_]+$", filename_noext):
        return True
    else:
        raise OSError(
            "File "
            + str(filename_noext)
            + " is not just alphanumeric, underscore, hyphen."
        )


def filename_padding_amount(filename_noext, number_of_files):
    """
    Given a filename and the number of files, return True if the padding is correct
    padding is 3 digits for under 1000, 4+ digits for over
    This is implemented assuming having already passed filename_for_book
    """
    filename_suffix = filename_noext.split("-")[1]
    if number_of_files < 1000:
        if len(filename_suffix) == 3:
            return True
    elif number_of_files < 10000:
        if len(filename_suffix) == 4:
            return True
    elif number_of_files < 100000:
        if len(filename_suffix) == 5:
            return True
    elif number_of_files < 1000000:  # is this enough
        if len(filename_suffix) == 6:
            return True
    raise OSError(
        "File "
        + str(filename_noext)
        + " has wrong padding for a directory of "
        + str(number_of_files)
        + " files."
    )


def ISO8601_date(input):
    # taking assumed EDTF date, check if it's a level 0 date - YYYY, YYYY-MM, YYYY-MM-DD
    # (this also would work for any arbitrary string)
    # this is the only value for a date string allowed by ArchivesSpace's date representation in Begin or End field
    input = str(input)
    date_matches = ["^\d\d\d\d$", "^\d\d\d\d-\d\d$", "^\d\d\d\d-\d\d-\d\d$"]
    dates_match = False
    for match in date_matches:
        if re.match(match, input):
            dates_match = True
    if dates_match:
        return True
    else:
        raise ValueError(
            input
            + " is not an ISO 8601 date (= EDTF level 0 'Date') (= YYYY, YYYY-MM, YYYY-MM-DD)"
        )


def language(input):
    """
    Supply code OR language, validate these
    """
    if input in c.LANGUAGE_CODES:
        return True
    elif input in c.LANGUAGE_NAMES:
        return True
    else:
        raise ValueError("Language code or name " + str(input) + " not in ISO639 file.")


def list_is_all_empty(input):
    # for each item in the input list, check it's not a NaN and then check if it's anything
    # if any are anything, return false, else return true (list is all empty)
    for x in input:
        if not pandas.isna(x):
            if x:
                return False
    return True


def list_is_single_value_then_NaN(input):
    # returns True if a list provided is just one single value then NaN.
    # used to allow user to avoid copy-pasting a value into every row if it's always the same.
    # this doesn't really fit into this file but couldn't think where else to put it.
    #
    # we assume it's true
    list_is_indeed_single_value_then_NaN = True
    # if there's something other than NaN in the first value ...
    if not pandas.isna(input[0]):
        # and all the rest of the values are nothing ...
        for x in input[1:]:
            # update if we get a non-NaN value
            if not pandas.isna(x):
                list_is_indeed_single_value_then_NaN = False
        # return the value
        return list_is_indeed_single_value_then_NaN
    else:
        return False


def list_is_single_value_then_empty_string(input):
    # exactly the same as above except empty string, in data that does not contain nan
    # we assume it's true
    list_is_indeed_single_value_then_empty_string = True
    # if there's something in the first value ...
    if input[0]:
        # and all the rest of the values are nothing ...
        for x in input[1:]:
            # update if we get a non-NaN value
            if x:
                list_is_indeed_single_value_then_empty_string = False
        # return the value
        return list_is_indeed_single_value_then_empty_string
    else:
        return False


def piped_fields_same_length(input1, input2):
    # returns True if two pipe-separated fields are the same length
    # this is for cases where we mix the fields, e.g. agents (agent_name, agent_role)
    if len(input1.split("|")) == len(input2.split("|")):
        return True
    else:
        raise ValueError(
            "These two pipe-separated fields need to have the same number of values to be matched correctly: "
            + str(input1)
            + " AND "
            + str(input2)
        )


def relator_code(input):
    if input in c.RELATOR_CODES:
        return True
    else:
        raise ValueError("Relator code " + str(input) + " not in relators csv.")


def string_is_match_then_hyphen_then_numbers(full_string, beginning_to_match):
    """
    validate files in a book object
    returns True if full_string = beginning_to_match-numbers
    """
    split_string = full_string.split("-")
    if len(split_string) != 2:
        return False
    if split_string[0] != beginning_to_match:
        return False
    if not string_is_numeric(split_string[1]):
        return False
    return True


def string_is_numeric(input):
    if re.match(r"^\d+$", input):
        return True
    else:
        return False
