'''
Takes a filled spreadsheet and outputs a Workbench sheet
Assumes a fully valid, checked against Validate_Filled.py, spreadsheet
'''

import os
import pandas
from argparse import ArgumentParser
from aspace_wb.utils import default_specs as c
from aspace_wb.utils import convert_data, use_CSVs, validate


'''
Parse command line arguments
    required, positional: Workbench upload type (single/book)
    required, positional: filled file
'''
print("(Make sure you ran Validate_Filled.py before performing this. Go back and run that if you didn't.)")
print('Checking command line arguments - expected: [single/book] [filled file.xlsx]...')

# parse arguments

cl_parser = ArgumentParser()
cl_parser.add_argument('type', type=str, choices=('single', 'book'), help="Workbench upload type: 'book' (an object with multiple pages) or 'single' (a graphic, audio, or video object)")
cl_parser.add_argument('filled_file', type=str, help="Name of your validated, simplified Workbench sheet (with .xlsx extension)")
cl_args = cl_parser.parse_args()

# assign arguments to variables:

# WB_type from type
WB_type = cl_args.type

# FILLED_FILENAME from filled_file
FILLED_FILENAME = cl_args.filled_file
# check existence
if not os.path.exists(os.path.join(c.METADATA_DIR, FILLED_FILENAME)):
    raise OSError(f"Workbench sheet {FILLED_FILENAME} not found in folder {c.METADATA_DIR}. Check file name and location and try again.")

print('... command line arguments parsed ...')

'''
Load xlsx to pandas DataFrame then dictionary
results in input_dict to use
'''
print('Loading data from spreadsheet file ...')

# create dataframe from Excel
# 1. dtype=str makes sure that nothing is read as a number
# 2. skiprows=[1] skips the description row
input_pd_dataframe = pandas.read_excel(os.path.join(c.METADATA_DIR, FILLED_FILENAME), dtype=str, skiprows=[1])
# swap nan in dataframe for empty strings
input_pd_dataframe = input_pd_dataframe.fillna('')
# find out how many records we have. this is stored in shape.
INPUT_ROW_COUNT = input_pd_dataframe.shape[0]
# make dictionary to use
input_dict = input_pd_dataframe.to_dict(orient='list')
INPUT_FIELDS = list(input_dict.keys())

print('... spreadsheet file loaded ...')


'''
Define functions to fill WB_dict from input_dict
'''
# create the dictionary to fill
WB_dict = dict()


def _prefill_downfilling_fields():
    '''
    Fill all downfilling fields
    '''
    for f in c.WB_FIELDS_DOWNFILLING:
        # grab a list of the data
        values = input_dict[f]
        # for each, if empty, fill with previous value
        for index, value in enumerate(values):
            if value == "":
                values[index] = values[index - 1]
        # give this list back to the dictionary
        input_dict[f] = values


def _add_complex_fields():

    # id
    WB_dict["id"] = [i + 1 for i in range(INPUT_ROW_COUNT)]

    # file - book/single distinction
    if 'file' in INPUT_FIELDS:
        if WB_type == 'book':
            WB_dict["file"] = input_dict["file"]
        elif WB_type == 'single':
            WB_dict["file"] = [c.file_SINGLE_PREFIX + file for file in input_dict["file"]]

    # title, field_metadata_title
    if 'title' in INPUT_FIELDS:
        WB_dict["title"] = input_dict["title"]
        WB_dict["field_metadata_title"] = input_dict["title"]

    # url_alias
    if "url_alias" in INPUT_FIELDS:
        url_aliases_with_prefixes = []
        for url_alias in input_dict["url_alias"]:
            # if url_alias is present, i.e. not an empty string, prefix to it, otherwise just place empty string
            if url_alias:
                url_aliases_with_prefixes.append(c.url_alias_PREFIX + str(url_alias))
            else:
                url_aliases_with_prefixes.append("")
        WB_dict["url_alias"] = url_aliases_with_prefixes

    # field_language
    # convert either language name or code name to string
    if "field_language" in INPUT_FIELDS:
        WB_dict["field_language"] = []
        for i in range(INPUT_ROW_COUNT):
            if input_dict["field_language"][i]:
                #languages = input_dict["field_language"][i].split("|")
                WB_dict["field_language"].append(
                    "|".join([convert_data.language_name_or_ISO639_code_to_WB_language(language) for language in input_dict["field_language"][i].split("|")])
                )
            else:
                WB_dict["field_language"].append("")

    # field_linked_agent
    # calls function from _ConvertData on the values
    if "field_linked_agent_NAME" in INPUT_FIELDS and "field_linked_agent_RELATOR" in INPUT_FIELDS and "field_linked_agent_TYPE" in INPUT_FIELDS:
        WB_dict["field_linked_agent"] = []
        for i in range(INPUT_ROW_COUNT):
            if input_dict["field_linked_agent_NAME"][i]:
                # supply the converted name, relator, type
                WB_dict["field_linked_agent"].append(convert_data.agents_info_to_WB_agent(
                    input_dict["field_linked_agent_NAME"][i],
                    input_dict["field_linked_agent_RELATOR"][i],
                    input_dict["field_linked_agent_TYPE"][i]
                    ))
            else:
                # supply nothing
                WB_dict["field_linked_agent"].append("")
        # a miserable thing to do: delete these fields so they don't confuse us when we try to add other fields
        del input_dict['field_linked_agent_NAME']
        del input_dict['field_linked_agent_RELATOR']
        del input_dict['field_linked_agent_TYPE']


def _add_unchanging_fields():
    '''
    maps every other field present in input_dict directly to WB_dict
    '''
    for k, v in input_dict.items():
        if k not in WB_dict:
            WB_dict[k] = v

def _delete_empty_fields():
    '''
    delete any field that is empty
    '''
    empty_fields = []
    # create the list of empty fields
    for key, value in WB_dict.items():
        if validate.list_is_all_empty(value):
            empty_fields.append(key)
    # if there are empty fields, delete them and flag this to the user
    if empty_fields:
        for key in empty_fields:
            WB_dict.pop(key)
        print(f"The following columns were empty and have been deleted. Rerun this script if this was an error: {str(empty_fields)}")

def _add_required_empty_fields():
    '''
    add empty fields depending on the WB_type
    '''
    # select empty fields based on WB_type
    if WB_type == 'single':
        empty_to_add = c.WB_FIELDS_EXPORT_KEEP_EMPTY_SINGLE
    elif WB_type == 'book':
        empty_to_add = c.WB_FIELDS_EXPORT_KEEP_EMPTY_BOOK
    # add these, if not already present, and flag this to user
    empty_added = []
    for f in empty_to_add:
        if f not in WB_dict.keys():
            WB_dict[f] = ["" for i in range(INPUT_ROW_COUNT)]
            empty_added.append(f)
    if empty_added:
        print(f"The following columns were added to be purposefully blank for upload: {str(empty_added)}")


'''
Execute the functions to fill WB_dict in the correct order
'''

print("Populating fields from spreadsheet file ...")

_prefill_downfilling_fields()
_add_complex_fields()
_add_unchanging_fields()
_delete_empty_fields()
_add_required_empty_fields()

print("... fields populated.")

'''
Rearrange WB_dict to match column order as preferred by Center for Digital Scholarship
'''

print("Rearranging fields to match preferred output order ...")

WB_dict_ordered = {key: WB_dict[key] for key in c.WB_FIELDS_ALL if key in WB_dict}

print("... fields rearranged.")

'''
Export our WB csv
'''
# create output filename
WB_FILENAME = f"{os.path.splitext(FILLED_FILENAME)[0]}_wb-to-wb"
FILE_EXTENSION = ".csv"

# if file already exists, append a counter to prevent overwriting
while os.path.exists(os.path.join(c.METADATA_DIR, f"{WB_FILENAME}{FILE_EXTENSION}")):
    filename_split = WB_FILENAME.split("_")
    if filename_split[-1].isdigit():
        counter = int(filename_split[-1]) + 1
        WB_FILENAME = f"{"_".join(filename_split[:-1])}_{counter}"
    else:
        WB_FILENAME += "_2"

FILENAME_FULL = f"{WB_FILENAME}{FILE_EXTENSION}"

use_CSVs.dict_to_CSV(WB_dict_ordered, os.path.join(c.METADATA_DIR, FILENAME_FULL))
print(f"SUCCESS. Generated Workbench file: {os.path.join(c.METADATA_DIR, FILENAME_FULL)}")

'''
Post-completion reminders to user
'''
print("REMINDERS:")
print("\tCheck and make any other modifications before submitting.")
print("\tIf using Excel/Libreoffice, import all fields as type 'text'.")
# flag if a field_member_of value is blank
if "field_member_of" in INPUT_FIELDS:
    if "" in WB_dict["field_member_of"]:
        print("\tOne or more rows has no value for field_member_of. Don't forget to add in a row for its parent!")