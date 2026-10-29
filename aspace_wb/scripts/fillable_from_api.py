from asnake.client import ASnakeClient
from asnake.aspace import ASpace
from dotenv import load_dotenv
import os
import pprint
import time
import csv
import pandas as pd

"""
TO DO

port to as-wb-scripts
get actual descriptions from as-wb-scripts files
preserve any columns already entered
populate fields from fields list (if nothing entered, use all)
at end: sort columns into preferred order

get it working in command line

sort as it will be in file system? does it matter?
try getting rid of ASnake dependency

CURRENTLY USED IN CREATE_FILLABLE

field_related_materials_note -> note/relatedmaterial/0/content [find an example with this]

field_note -> odd, bioghist, accruals, dimensions, altformavail, phystech, physdesc, processinfo, separatedmaterial

extent? [add in brackets for scanned page numbers?]

PROCESS

run process to create initial sheet from filesystem
fill in aspace nodes to that sheet
run process on that sheet to pull additional info from AS API

offer a version where you pass a series/collection ID and it does this on all the nodes

NEXT STEPS

how does this work for subseries/subcollection?

get this integrated into aspace-wb-scripts
rework some fields to use Paul's logic (date validation, esp. field_note)

try on backlog?

PR

do version that gets all child nodes for a collection/series
"""

# presets - copy into aspace-wb-scripts presets
collection_url_prefix = "https://as.amphilsoc.org"

# load environment and set variables
load_dotenv()

username = os.environ.get('ASPACE_USERNAME')
password = os.environ.get('ASPACE_PASSWORD')
base_url = os.environ.get('ASPACE_URL')

client = ASnakeClient(baseurl=base_url,
                      username=username,
                      password=password)
client.authorize()

aspace = ASpace()

# HELPER FUNCTIONS

def get_date(record):
    #TODO: can a record have multiple dates? necessary to iterate through?
    #TODO: can a record have non-EDTF dates that would appear in field_date_created_text?
    # Paul wrote logic for this already- see AS_date_to_WB_date in convert_data
    if "dates" in record:
        if len(record["dates"]) > 1:
            print("WARNING: more than one date present in record. Only the first will be processed.")
        elif len(record["dates"]) == 0:
            return None

        if record["dates"][0]["date_type"] == "single":
            return record["dates"][0]["expression"]
        elif record["dates"][0]["date_type"] == "inclusive":
            return f"{record["dates"][0]["begin"]}/{record["dates"][0]["end"]}"
        else:
            print("WARNING: date present in record but could not be processed.")
            return None
    else:
        return None

def get_collection_id(record):
    ancestors = record["ancestors"]

    for ancestor in ancestors:
        # check both of these conditions because some collections (e.g. Franklin) have archival objects that are collection parents
        if ancestor["level"] == "collection" and "/resources/" in ancestor["ref"]:
            collection_url_suffix = ancestor["ref"]
            collection_url = f"{collection_url_prefix}{collection_url_suffix}"

            collection_id = collection_url_suffix.split("/")[-1]

            return [collection_id, collection_url]

    print("WARNING: Parent collection not found. Enter info manually.")
    return [None, None]

def get_collection_name(collection_id):
    collection = aspace.resources(int(collection_id)).json()
    # print(collection)

    field_collection2 = collection["title"]
    field_parent_collection_call_num = collection["id_0"]
    return [field_collection2, field_parent_collection_call_num]

def is_restricted(record_to_search):
    # this seems to be set to false even in items that are restricted, but try it just in case
    if "restrictions_apply" in record_to_search:
        if record_to_search["restrictions_apply"]:
            return True

    # top-level collections have this field
    if "restrictions" in record_to_search:
            if record_to_search["restrictions"]:
                return True

    # check fields within "notes" that could indicate presence of a restriction
    if "notes" in record_to_search:
        for note in record_to_search["notes"]:
            if "type" in note:
                if note["type"] == "accessrestrict":
                    return True

            if "rights_restriction" in note:
                if note["rights_restriction"]:
                    return True
                
    return False

def get_field_access_terms(record):
    restrictions_bool = is_restricted(record)

    # if no record-level restrictions, check for restrictions in parents
    #TODO: does this work for subseries?
    #TODO: necessary to check top-level collection? are these ever restricted, and if so what would that look like?
    if not restrictions_bool:
        for ancestor in record["ancestors"]:
            ancestor_id = ancestor["ref"].split("/")[-1]

            # search a collection (level: series, ref: archival_objects), subseries (level: collection, ref: archival_objects), or collection (level: collection, ref: resources)
            if "archival_objects" in ancestor["ref"]:
                parent_series = aspace.repositories(2).archival_objects(ancestor_id).json()
                restrictions_bool = is_restricted(parent_series)
            elif "resources" in ancestor["ref"]:
                parent_collection = aspace.resources(int(ancestor_id))

                # method above unpredictable can return either a dict or a JSON object - convert to dict if the latter
                if not isinstance(parent_collection, dict):
                    # print("converting from json")
                    parent_collection = parent_collection.json()
                
                restrictions_bool = is_restricted(parent_collection)
            else:
                print(f"Warning: weird ancestor not accounted for. {ancestor["level"]}")
            if restrictions_bool:
                break
                
    if restrictions_bool:
        return "Admin-only access"
    else:
        return "N/A"

def get_description(record):
    notes_list = []
    for note in record["notes"]:
        if note["type"] == "scopecontent" or note["type"] == "abstract":
            # TODO: do I need to loop through subnotes?
            notes_list.append(note["subnotes"][0]["content"])

    return " ".join(notes_list).strip()

def get_subjects(record):
    subjects = record["subjects"]

    subjects_list = []

    # {'ref': '/subjects/1744'}
    for subject in subjects:
        subject_dict = client.get(subject["ref"]).json()
        subjects_list.append(subject_dict["title"])

    if subjects_list:
        return "|".join(subjects_list)
    else:
        return None


def get_linked_agents(record, wb_dict):
    names = []
    relators = []
    types = []

    for agent in record["linked_agents"]:
        agent_record = client.get(agent["ref"]).json()
        # print(agent_record)

        # TODO: necessary to iterate names instead of just taking first item?
        names.append(agent_record["names"][0]["primary_name"])

        relators.append(agent["role"])

        if agent_record["agent_type"] == "agent_person":
            types.append("person")
        elif agent_record["agent_type"] == "agent_family":
            types.append("family")
        elif agent_record["agent_type"] == "agent_corporate_entity":
            types.append("corporate_body")
        else:
            print("Something went wrong while determining field_linked_agent_TYPE")
            types.append("FIX ME MANUALLY")

    if len(names) == len(relators) and len(relators) == len(types):
        pass
    else:
        print("WARNING: unequal number of names, relators, and types. Check manually.")

    wb_dict["field_linked_agent_NAME"] = "|".join(names)
    wb_dict["field_linked_agent_RELATOR"] = "|".join(relators)
    wb_dict["field_linked_agent_TYPE"] = "|".join(types)

    # return {
    #         "field_linked_agent_NAME": "|".join(names),
    #         "field_linked_agent_RELATOR": "|".join(relators),
    #         "field_linked_agent_TYPE": "|".join(types)
    #     }

def get_record_info(record_id):
    record = aspace.repositories(2).archival_objects(record_id).json()
    # print(record)
    # print(type(record))
    wb_dict = {}

    # TODO: should this be title instead? difference is that display_string includes a date at the end
    wb_dict["title"] = record["display_string"]

    wb_dict["date"] = get_date(record)

    # TODO: check if this exists in the data
    if "component_id" in record:
        wb_dict["field_local_identifier"] = record["component_id"]
    else:
        wb_dict["field_local_identifier"] = None

    wb_dict["collection_id"], wb_dict["collection_url"] = get_collection_id(record)

    wb_dict["field_collection2"], wb_dict["field_parent_collection_call_num"] = get_collection_name(wb_dict["collection_id"])

    wb_dict["field_access_terms"] = get_field_access_terms(record)

    wb_dict["field_description_long"] = get_description(record)

    wb_dict["subjects"] = get_subjects(record)

    get_linked_agents(record, wb_dict)

    # pprint.pprint(wb_dict)
    print(f"Record created: {wb_dict["title"]}")
    time.sleep(3)

    return wb_dict

def create_wb_dicts():
    records = []

    with open('as-refs.csv', mode='r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            try:
                records.append(get_record_info(row['as_ref']))
            except Exception as e:
                print(f"Something went wrong while processing row {row['as_ref']}: {e}")

    # print(records)

    # populate description for each field
    descriptions_dict = {}
    for key in records[0].keys():
        descriptions_dict[key] = "Dummy description"

    records.insert(0, descriptions_dict)

    df = pd.DataFrame(records)
    # df = df.fillna(None)
    print(df)

    return df

def write_file(df):
    '''
    Create Pandas dataframe from final_dict, then write to Excel sheet
    '''
    print('Creating output file ...')

    FILE_NAME = "output.xlsx"

    # settings/logic copied from aspace-wb-scripts
    pd_ExcelWriter = pd.ExcelWriter(
        FILE_NAME,
        engine="xlsxwriter"
    )
    df.to_excel(
        pd_ExcelWriter, sheet_name="Workbench",
        startrow=0,
        header=True,
        index=False
    )
    #TODO: version in aspace-wb-scripts centers and bolds header row. This doesn't despite using the same code copy/pasted. Not sure what's going on here
    pd_ExcelWriter_book = pd_ExcelWriter.book
    pd_ExcelWriter_sheet = pd_ExcelWriter.sheets["Workbench"]
    pd_header_format = pd_ExcelWriter_book.add_format(
            {
                # we can add formatting for our description row here
                # use anything defined in here: https://xlsxwriter.readthedocs.io/format.html#format-methods-and-format-properties
                'valign': 'vcenter',
                'align': 'center',
                'border': 1,
                'bold': True,
            }
        )
    pd_description_format = pd_ExcelWriter_book.add_format(
        {
            # we can add formatting for our description row here
            # use anything defined in here: https://xlsxwriter.readthedocs.io/format.html#format-methods-and-format-properties
            'italic': True,
            'text_wrap': True,
            'valign': 'vcenter',
            'align': 'center',
            'border': 1,
            'bg_color': "#ECEBD8"
        }
    )
    # write the formatting
    # set description row to use pd_description_format
    CELL_HEIGHT_DESCRIPTION = 60
    pd_ExcelWriter_sheet.set_row(1, CELL_HEIGHT_DESCRIPTION, pd_description_format)
    pd_ExcelWriter_sheet.set_row(0, None, pd_header_format)
    # set cell width to something reasonable. there is no such thing as autofit all cells.
    CELL_WIDTH = 30
    pd_ExcelWriter_sheet.set_column(0,df.shape[1]-1,CELL_WIDTH)
    # close to write the file
    pd_ExcelWriter.close()

def run_script():
    df = create_wb_dicts()
    write_file(df)

run_script()