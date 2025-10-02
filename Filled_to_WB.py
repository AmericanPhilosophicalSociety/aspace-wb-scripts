'''
Takes a filled spreadsheet and outputs a Workbench sheet
Assumes a fully valid, checked against Validate_Filled.py, spreadsheet
'''

import os
import pandas
from argparse import ArgumentParser
import _Constants_and_Mappings as c
import _ExtractDir, _ConvertData, _CSV, _Validate

HEADERS_DIR = "_headers"

'''
Parse command line arguments
    required, positional: Workbench upload type (single/book)
    required, positional: filled file
'''
print('(Make sure you ran "Validate_Filled.py" before performing this)')
print('Checking command line arguments - expected: [single/book] [filled file.xlsx]...')

# parse arguments

cl_parser = ArgumentParser()
cl_parser.add_argument('type', type=str, choices=('single', 'book'))
cl_parser.add_argument('filled_file', type=str)
cl_args = cl_parser.parse_args()

# assign arguments to variables:

# WB_type from type
WB_type = cl_args.type

# FILLED_FILENAME from filled_file
FILLED_FILENAME = cl_args.filled_file
# check existence
if not os.path.exists(os.path.join(c.METADATA_DIR, FILLED_FILENAME)):
    raise OSError("Folder " + c.METADATA_DIR + " does not appear to contain " + FILLED_FILENAME + ". Check.")
# create output filename from this
WB_FILENAME = os.path.splitext(FILLED_FILENAME)[0] + "_WB-OUTPUT.csv"

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
    if 'id' in INPUT_FIELDS:
        WB_dict["id"] = [i + 1 for i in range(INPUT_ROW_COUNT)]

    # file - book/single distinction
    if 'file' in INPUT_FIELDS:
        if WB_type == 'book':
            WB_dict["file"] = input_dict["file"]
        elif WB_type == 'single':
            WB_dict["file"] = [c.file_SINGLE_PREFIX + file for file in input_dict["file"]]

    # url_alias
    if "url_alias" in INPUT_FIELDS:
        WB_dict["url_alias"] = input_dict["url_alias"]
        for url_alias in WB_dict["url_alias"]:
            # if url_alias is present, i.e. not an empty string, prefix to it
            if url_alias:
                url_alias = c.url_alias_PREFIX + str(url_alias)

    # field_language
    # if present, convert either language name or code name to string
    if "field_language" in INPUT_FIELDS:
        WB_dict["field_language"] = []
        for i in range(INPUT_ROW_COUNT):
            if input_dict["field_language"][i]:
                languages = input_dict["field_language"][i].split("|")
                WB_dict["field_language"].append(
                    "|".join(
                        [_ConvertData.language_name_or_ISO639_code_to_WB_language(language) for language in languages]
                        )
                )
            else:
                WB_dict["field_language"].append("")

    # field_linked_agent
    # calls function from _ConvertData on the values
    if "field_linked_agent_NAME" and "field_linked_agent_ROLE" and "field_linked_agent_TYPE" in INPUT_FIELDS:
        WB_dict["field_linked_agent"] = []
        for i in range(INPUT_ROW_COUNT):
            if input_dict["agent_name"][i]:
                # get the full
                WB_dict.append(_ConvertData.agents_info_to_WB_agent(
                    input_dict["field_linked_agent_NAME"][i],
                    input_dict["field_linked_agent_ROLE"][i],
                    input_dict["field_linked_agent_TYPE"][i]
                    ))
            else:
                WB_dict["field_linked_agent"].append("")
        # a miserable thing to do: delete these fields so they don't confuse us when we try to add other fields
        del input_dict['field_linked_agent_NAME']
        del input_dict['field_linked_agent_ROLE']
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
    pass

def _add_required_empty_fields():
    '''
    dependent on 
    '''
    pass


'''
make an output dictionary to use, filling it in by checking the presence of each field from headers
as we've already established we have all the required headers, this should now be smoothe
'''



# id, parent id, member of (for easy reading)
WB_dict["parent_id"] = ["" for i in range(INPUT_ROW_COUNT)]
if "coll_node" in INPUT_FIELDS:
    WB_dict["field_member_of"] = [str(x) for x in input_dict["coll_node"]]

# everything that gets singularly copied over

if "WB_total_scans" in INPUT_FIELDS:
    WB_dict["total_scans"] = input_dict["WB_total_scans"]

if "coll_title" in INPUT_FIELDS:
    WB_dict["field_collection2"] = input_dict["coll_title"]

if "coll_callno" in INPUT_FIELDS:
    WB_dict["field_parent_collection_call_num"] = input_dict["coll_callno"]

if "coll_url" in INPUT_FIELDS:
    WB_dict["field_collection_url"] = input_dict["coll_url"]

if "cuid" in INPUT_FIELDS:
    WB_dict["field_local_identifier"] = input_dict["cuid"]

if "title" in INPUT_FIELDS:
    WB_dict["title"] = input_dict["title"]
    WB_dict["field_metadata_title"] = input_dict["title"]

if "datecreated_edtf" in INPUT_FIELDS:
    WB_dict["field_edtf_date_created"] = input_dict["datecreated_edtf"]

if "datecreated_text" in INPUT_FIELDS:
    WB_dict["field_date_created_text"] = input_dict["datecreated_text"]

if "scopecontents" in INPUT_FIELDS:
    WB_dict["field_description_long"] = input_dict["scopecontents"]

if "othernotes" in INPUT_FIELDS:
    WB_dict["field_note"] = input_dict["othernotes"]

if "medium" in INPUT_FIELDS:
    WB_dict["field_original_format"] = input_dict["medium"]

if "extent" in INPUT_FIELDS:
    WB_dict["field_extent"] = input_dict["extent"]
    
if "datedigitized" in INPUT_FIELDS:
    WB_dict["field_date_digitized"] = input_dict["datedigitized"]

if "cnairsubject" in INPUT_FIELDS:
    WB_dict["field_cnair_subject"] = input_dict["cnairsubject"]

if "location_name" in INPUT_FIELDS:
    WB_dict["field_geographic_subject"] = input_dict["location_name"]

if "related_note" in INPUT_FIELDS:
    WB_dict["field_related_materials_note"] = input_dict["related_note"]

if "related_title" in INPUT_FIELDS:
    WB_dict["field_mods_relateditem_titleinfo"] = input_dict["related_title"]

if "related_url" in INPUT_FIELDS:
    WB_dict["field_related_resource_url"] = input_dict["related_url"]

if "WB_field_model" in INPUT_FIELDS:
    WB_dict["field_model"] = input_dict["WB_field_model"]

if "WB_field_digital_origin" in INPUT_FIELDS:
    WB_dict["field_digital_origin"] = input_dict["WB_field_digital_origin"]


# delete any blank columns and send these to the user in case this was an error
# exception added for parent_id since we want it to show early but it's necessary
blankColumns = []
for key, value in WB_dict.items():
    if _Validate.list_is_all_empty(value):
        if key != "parent_id":
            blankColumns.append(key)
if len(blankColumns) > 0:
    for key in blankColumns:
        WB_dict.pop(key)
    print("The following columns were empty and have been deleted, to conform work Workbench requirements of no empty columns. Rerun this script if this was an error.")
    print(blankColumns)

print("... all fields populated.")

'''
TO DO - add BLANKS
'''

'''
rearrange WBDict to match preferred column order for checking
'''
print("Rearranging fields ...")
# grab final order to list depending on WBType
###BS
if WB_type == 'single':
    headers_WBFinalOrder = _CSV.CSV_col_to_list(os.path.join(HEADERS_DIR, "_WBFinalOrderSingle.csv"), 0)
elif WB_type == 'book':
    headers_WBFinalOrder = _CSV.CSV_col_to_list(os.path.join(HEADERS_DIR, "_WBFinalOrderBook.csv"), 0)

# if a Workbench field is not present in headers_WBFinalOrder, inform user and terminate
missingWBFinalOrderFields = [key for key in WB_dict if key not in headers_WBFinalOrder]
if missingWBFinalOrderFields:
    raise ValueError("The following fields are present in the output Workbench dictionary but not within the appropriate the WBFinalOrder csv file in " + HEADERS_DIR + ". This may be a new field. Check with colleagues. " + str(missingWBFinalOrderFields))

# reorder
WBDictOrdered = {key: WB_dict[key] for key in headers_WBFinalOrder if key in WB_dict}

print("... fields rearranged.")

'''
export our WB csv
'''
_CSV.dict_to_CSV(WBDictOrdered, os.path.join(c.METADATA_DIR, WB_FILENAME))
print("Generated Workbench file. Check and make any other modifications before using: " + c.METADATA_DIR + "\\" + WB_FILENAME)