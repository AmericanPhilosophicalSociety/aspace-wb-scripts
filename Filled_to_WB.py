'''
WORKING - needs more testing
takes a filled xlsx sheet (from this process) and outputs a Workbench sheet
'''

import os
import pandas
import argparse
import _ExtractDir, _ConvertData, _CSV, _Validate

FILESTOUPLOAD_DIR = "files_to_upload"
METADATA_DIR = "metadata"
CV_DIR = "_CVs"
HEADERS_DIR = "_headers"
ISO639_FILENAME = "iso639.csv"
SINGLE_FILEABSOLUTEPREFIX = "/mnt/ingest/data/"

'''
mappings -
field_model to field_resource_type transformation
field_model to field_display_hints transformation
both could go in _ConvertData.py
'''
ModelToResourceType = {
    "Collection": "Collection",
    "Audio": "Sound",
    "Image": "Still Image",
    "Page": "Text",
    "Paged Content": "Collection",
    "Digital Document": "Collection",
    "Video": "Moving Image"
    }

# Digital Document is interpreted from Create_Fillable as PDF
# Image can be produced from a jpg or a tif. if it's a problem to use Open Seadragon for jpg, change this.
ModelToDisplayHints = {
    "Digital Document": "PDFjs",
    "Image": "Open Seadragon"
}

'''
command line arguments
required, positional: single/book, source file
'''
print('Checking command line arguments - expected: [single/book] [filled file.xlsx]...')

CLParser = argparse.ArgumentParser()
CLParser.add_argument('type', type=str, choices=('single', 'book'))
CLParser.add_argument('filled_file', type=str)
CLargs = CLParser.parse_args()
# assign arguments
WBType = CLargs.type
FILLED_FILENAME = CLargs.filled_file
if FILLED_FILENAME not in _ExtractDir.FileList(METADATA_DIR, extensions=True):
    raise OSError("Folder " + METADATA_DIR + " does not appear to contain " + FILLED_FILENAME + ". Check.")
WB_FILENAME = os.path.splitext(FILLED_FILENAME)[0] + "_WB-OUTPUT.csv"

print('... command line arguments parsed ...')

'''
load xlsx to pandas DataFrame then dictionary
'''
print('Loading data from xlsx file ...')

# dtype=str makes sure that nothing is read as a number
inputDF = pandas.read_excel(os.path.join(METADATA_DIR, FILLED_FILENAME), dtype=str)
# swap nan in dataframe for empty strings
inputDF = inputDF.fillna('')
# find out how many records we have. this is stored in shape.
inputRows = inputDF.shape[0]
# make the inputDF dictionary
inputDict = inputDF.to_dict(orient='list')

print('... xlsx file loaded ...')

'''
check headers against required fields
'''
# grab input headers to list
headers = list(inputDict.keys())
# grab csvs to lists
headers_allValid = _CSV.CSVColToList(os.path.join(HEADERS_DIR, "_allValid.csv"), 0)
headers_downfilling = _CSV.CSVColToList(os.path.join(HEADERS_DIR, "_downfilling.csv"), 0)
# required headers depend on single vs book
if WBType == 'single':
    headers_required = _CSV.CSVColToList(os.path.join(HEADERS_DIR, "_requiredSingle.csv"), 0)
elif WBType == 'book':
    headers_required = _CSV.CSVColToList(os.path.join(HEADERS_DIR, "_requiredBook.csv"), 0)

# check that the headers are valid
for header in headers:
    if header not in headers_allValid:
        raise ValueError("Input spreadsheet has an invalid column: " + header)
# check all the headers for the WBType are present
# note that this isn't ALL the Workbench output fields, as some are autofilled
for header in headers_required:
    if header not in headers:
        raise ValueError("Input spreadsheet is missing a required column: " + header)

print('... xlsx file headers look like ones we expect ...')

'''
check that required fields contain the necessary data
'''
for header in headers_required:
    if header in headers_downfilling:
        # raise error if the first value in a downfilling column is not present
        if not inputDict[header][0]:
            raise ValueError("Input spreadsheet needs to have at least the first row filled in column: " + header)
    else:
        # raise error if any of the rows are empty
        if "" in inputDict[header]:
            raise ValueError("Column " + header + " in input spreadsheet needs to be completely filled.")
        
print("... all required columns have the right amount of data ...")

print('Populating data begins ...')
'''
populate autofilling columns in the input dictionary
'''
print('Filling in gaps in required fields that fill downwards ...')

for header in headers_downfilling:
    # grab a list of the data
    values = inputDict[header]
    # for each, if empty, fill with previous value
    for index, value in enumerate(values):
        if value == "":
            values[index] = values[index - 1]
    # give this list back to the dictionary
    inputDict[header] = values

print("... gaps filled.")
print("Populating other fields ...")

'''
make an output dictionary to use, filling it in by checking the presence of each field from headers
as we've already established we have all the required headers, this should now be smoothe
'''

WBDict = dict()

# id, parent id, member of (for easy reading)
WBDict["id"] = [i + 1 for i in range(inputRows)]
WBDict["parent_id"] = ["" for i in range(inputRows)]
if "coll_node" in headers:
    WBDict["field_member_of"] = [str(x) for x in inputDict["coll_node"]]

# everything that gets singularly copied over

if "file" in headers:
    if WBType == 'book':
        WBDict["file"] = inputDict["file"]
    elif WBType == 'single':
        WBDict["file"] = [SINGLE_FILEABSOLUTEPREFIX + file for file in inputDict["file"]]

if "WB_total_scans" in headers:
    WBDict["total_scans"] = inputDict["WB_total_scans"]

if "coll_title" in headers:
    WBDict["field_collection2"] = inputDict["coll_title"]

if "coll_callno" in headers:
    WBDict["field_parent_collection_call_num"] = inputDict["coll_callno"]

if "coll_url" in headers:
    WBDict["field_collection_url"] = inputDict["coll_url"]

if "cuid" in headers:
    WBDict["field_local_identifier"] = inputDict["cuid"]

if "title" in headers:
    WBDict["title"] = inputDict["title"]
    WBDict["field_metadata_title"] = inputDict["title"]

if "datecreated_edtf" in headers:
    WBDict["field_edtf_date_created"] = inputDict["datecreated_edtf"]

if "datecreated_text" in headers:
    WBDict["field_date_created_text"] = inputDict["datecreated_text"]

if "scopecontents" in headers:
    WBDict["field_description_long"] = inputDict["scopecontents"]

if "othernotes" in headers:
    WBDict["field_note"] = inputDict["othernotes"]

if "medium" in headers:
    WBDict["field_original_format"] = inputDict["medium"]

if "extent" in headers:
    WBDict["field_extent"] = inputDict["extent"]
    
if "datedigitized" in headers:
    WBDict["field_date_digitized"] = inputDict["datedigitized"]

if "cnairsubject" in headers:
    WBDict["field_cnair_subject"] = inputDict["cnairsubject"]

if "location_name" in headers:
    WBDict["field_geographic_subject"] = inputDict["location_name"]

if "related_note" in headers:
    WBDict["field_related_materials_note"] = inputDict["related_note"]

if "related_title" in headers:
    WBDict["field_mods_relateditem_titleinfo"] = inputDict["related_title"]

if "related_url" in headers:
    WBDict["field_related_resource_url"] = inputDict["related_url"]

if "WB_field_model" in headers:
    WBDict["field_model"] = inputDict["WB_field_model"]

if "WB_field_digital_origin" in headers:
    WBDict["field_digital_origin"] = inputDict["WB_field_digital_origin"]

# fields that undergo transformation

# language - code becomes Language (code)
# an improvement would be: accept either language name or language code
# could be moved to _ConvertData
if "iso639_code" in headers:
    WBDict["field_language"] = []
    # create dictionary of iso639 csv, swap so code comes first
    ISO639Dict = _CSV.TwoColumnCSVToDict(os.path.join(CV_DIR, ISO639_FILENAME))
    ISO639Dict = {value: key for key, value in ISO639Dict.items()}
    for i in range(inputRows):
        if inputDict["iso639_code"][i]:
            WBDict["field_language"].append(
                "|".join([_ConvertData.LanguageAndISO639CodeToWBLanguage(ISO639Dict[j], j) for j in str(inputDict["iso639_code"][i]).split("|")])
            )
        else:
            WBDict["field_language"].append("")

# agent
if "agent_name" and "agent_role" and "agent_type" in headers:
    WBDict["field_linked_agent"] = []
    for i in range(inputRows):
        if inputDict["agent_name"][i]:
            agent_name = str(inputDict["agent_name"][i]).split("|")
            agent_role = str(inputDict["agent_role"][i]).split("|")
            # if agent_type contains things, split and convert as normal, otherwise make all "person":
            if inputDict["agent_type"][i]:
                agent_type = str(inputDict["agent_type"][i]).split("|")
                agent_type = [_ConvertData.AgentTypeAbbreviationToFull(x) for x in agent_type]
            else:
                agent_type = ["person" for k in range(len(agent_name))]
            WBDict["field_linked_agent"].append(
                "|".join(
                    [_ConvertData.AgentRelatorAndTypeToWBAgent(
                        agent = agent_name[j],
                        relatorCode = agent_role[j],
                        agentType = agent_type[j]
                        ) for j in range(len(agent_name))
                        ]
                    )
                )
        else:
            WBDict["field_linked_agent"].append("")

# delete any blank columns and send these to the user in case this was an error
# exception added for parent_id since we want it to show early but it's necessary
blankColumns = []
for key, value in WBDict.items():
    if _Validate.ListIsAllEmpty(value):
        if key != "parent_id":
            blankColumns.append(key)
if len(blankColumns) > 0:
    for key in blankColumns:
        WBDict.pop(key)
    print("The following columns were empty and have been deleted, to conform work Workbench requirements of no empty columns. Rerun this script if this was an error.")
    print(blankColumns)

# other autopopulated fields
# reformatting quality 
WBDict["field_reformatting_quality"] = ["Preservation" for i in range(inputRows)]
# resource type - depends on model
WBDict["field_resource_type"] = []
for modelName in inputDict["WB_field_model"]:
    resourceType = ModelToResourceType.get(modelName)
    if resourceType:
        WBDict["field_resource_type"].append(resourceType)
    else:
        WBDict["field_resource_type"].append("")
# display hints - depends on model (only applies to certain Single objects, and required for book even though it's empty)
if WBType == 'book':
    WBDict["field_display_hints"] = ["" for i in range(inputRows)]
elif WBType == 'single':
    WBDict["field_display_hints"] = []
    for modelName in inputDict["WB_field_model"]:
        displayHint = ModelToDisplayHints.get(modelName)
        if displayHint:
            WBDict["field_display_hints"].append(displayHint)
        else:
            WBDict["field_display_hints"].append("")
    if _Validate.ListIsAllEmpty(WBDict["field_display_hints"]):
        WBDict.pop("field_display_hints")
# field_weight - blank, book only
if WBType == 'book':
    WBDict["field_weight"] = ["" for i in range(inputRows)]

# completely ignored as we don't know what we're doing with them: "access_type", "access_note"

print("... all fields populated.")
'''
export our WB csv
'''
_CSV.DictToCSV(WBDict, os.path.join(METADATA_DIR, WB_FILENAME))
print("Generated Workbench file. Check and make any other modifications before using: " + METADATA_DIR + "\\" + WB_FILENAME)