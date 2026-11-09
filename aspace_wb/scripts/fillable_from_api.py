from asnake.client import ASnakeClient
from asnake.aspace import ASpace
from dotenv import load_dotenv
import os
import pprint
import time
import csv
import pandas as pd
import aspace_wb.utils.default_specs as c
import aspace_wb.utils.validate as validate
from argparse import ArgumentParser
from importlib.resources import files as import_file
from aspace_wb.data import fields
from aspace_wb.scripts.create_fillable import process_fields

"""
TO RUN

wb-from-api book --fields cnairbook_subjects --AS as-refs.csv


PROCESS

run process to create initial sheet from filesystem
fill in aspace nodes to that sheet
run process on that sheet to pull additional info from AS API


NEXT STEPS

get rid of as_ref column, change to as_url?

try getting rid of ASnake dependency

check that I haven't broken create_fillable

do a version where you pass a series/collection ID and it does this on all the nodes


CURRENTLY USED IN CREATE_FILLABLE BUT NOT ACCOUNTED FOR HERE

field_related_materials_note -> note/relatedmaterial/0/content [find an example with this]

field_note -> odd, bioghist, accruals, dimensions, altformavail, phystech, physdesc, processinfo, separatedmaterial

extent? [add in brackets for scanned page numbers?]
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

def create_args():
    #TODO: is book/single relevant here?
    '''
    Parse command line arguments
        optional: --fields name of fields file to use
    '''

    cl_parser = ArgumentParser()

    cl_parser.add_argument('type', type=str, choices=('single', 'book'), help="Workbench upload type: 'book' (an object with multiple pages) or 'single' (a graphic, audio, or video object)") 

    FIELD_CHOICES = list(import_file(fields).glob('*.csv'))
    FIELD_CHOICES = sorted([f.name.replace('.csv', '') for f in FIELD_CHOICES if f.is_file()])
    cl_parser.add_argument('--fields', type=str, choices=FIELD_CHOICES, help="Name of CSV file containing list of fields to include in your Workbench sheet (omitting .csv extension). Choose from options above")

    #TODO: possible to read in as either?
    #TODO: find a way to skip over the description row? maybe ok to just skip over first row if as_ref column is blank?
    cl_parser.add_argument('--AS', required=True, type=str, help="Name (with .csv or .xlsx extension) of the spreadsheet including your ArchivesSpace refs")

    return cl_parser.parse_args()


def process_args(cl_args):
    # can be book or single - each one requires slightly different fields
    WB_type = cl_args.type

    if cl_args.fields:
        fields_in_use = process_fields(WB_type, cl_args.fields)
    else:
        # give all fields if no --fields argument
        fields_in_use = c.WB_FIELDS_ALL

    AS_FILENAME = cl_args.AS
    AS_file = os.path.join(c.METADATA_DIR, AS_FILENAME)
    # confirm the file exists as stated
    if not os.path.exists(AS_file):
        raise FileNotFoundError(f"Spreadsheet '{AS_FILENAME}' not found in /{c.METADATA_DIR}. Check file name and location and try again.")
        
    print('... command line arguments parsed ...')

    return fields_in_use, AS_file

# create a dict representing one row, with a key for each field
def create_one_row(fields_in_use):
    row_dict = {}

    # modify fields_in_use so that, if present, field_linked_agent gets split into its components
    if 'field_linked_agent' in fields_in_use:
        insert_index = fields_in_use.index('field_linked_agent')
        fields_in_use.insert(insert_index, 'field_linked_agent_NAME')
        fields_in_use.insert(insert_index + 1, 'field_linked_agent_RELATOR')
        fields_in_use.insert(insert_index + 2, 'field_linked_agent_TYPE')
        fields_in_use.remove('field_linked_agent')

    for field in fields_in_use:
        row_dict[field] = None

    return row_dict

def get_date(record, wb_dict):
    #TODO: can a record have multiple dates? necessary to iterate through?
    if "dates" not in record:
        date = None
    else:
        if len(record["dates"]) > 1:
            print("WARNING: more than one date present in record. Only the first will be processed.")
        
        if len(record["dates"]) == 0:
            date = None
        elif record["dates"][0]["date_type"] == "single":
            date = record["dates"][0]["expression"]
        elif record["dates"][0]["date_type"] == "inclusive":
            # attempt to construct valid EDTF from date range
            date = f"{record["dates"][0]["begin"]}/{record["dates"][0]["end"]}"
        else:
            print("WARNING: Weird date type detected! Check manually")
            date = None

    # if date is valid EDTF, fill to field_edtf_date_created
    if date:
        try:
            validate.EDTF(date)
            field_edtf_date_created = date
            field_date_created_text = None
        # if not valid EDTF, fill to field_date_created_text
        except:
            field_edtf_date_created = None
            field_date_created_text = date
    else:
        field_edtf_date_created = None
        field_date_created_text = None

    wb_dict["field_edtf_date_created"] = field_edtf_date_created
    wb_dict["field_date_created_text"] = field_date_created_text

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
    if not restrictions_bool:
        for ancestor in record["ancestors"]:
            ancestor_id = ancestor["ref"].split("/")[-1]

            # search a subcollection (level: series, ref: archival_objects), subseries (level: collection, ref: archival_objects), or collection (level: collection, ref: resources)
            if "archival_objects" in ancestor["ref"]:
                parent_series = aspace.repositories(2).archival_objects(ancestor_id).json()
                restrictions_bool = is_restricted(parent_series)
            elif "resources" in ancestor["ref"]:
                parent_collection = aspace.resources(int(ancestor_id))

                # method above unpredictably can return either a dict or a JSON object - convert to dict if the latter
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


def get_record_info(record_id, wb_dict_template):
    record = aspace.repositories(2).archival_objects(record_id).json()
    wb_dict = wb_dict_template.copy()
    # print(record)
    # print(type(record))

    # TODO: should this be title instead? difference is that display_string includes a date at the end
    wb_dict["title"] = record["display_string"]

    get_date(record, wb_dict)

    # TODO: check if this exists in the data
    if "component_id" in record:
        wb_dict["field_local_identifier"] = record["component_id"]
    else:
        wb_dict["field_local_identifier"] = None

    wb_dict["as_ref"], wb_dict["field_collection_url"] = get_collection_id(record)

    wb_dict["field_collection2"], wb_dict["field_parent_collection_call_num"] = get_collection_name(wb_dict["as_ref"])

    wb_dict["field_access_terms"] = get_field_access_terms(record)

    wb_dict["field_description_long"] = get_description(record)

    wb_dict["field_subject"] = get_subjects(record)

    get_linked_agents(record, wb_dict)

    # pprint.pprint(wb_dict)
    print(f"Record created: {wb_dict["title"]}")
    time.sleep(3)

    return wb_dict

def add_wb_fillable_data(row, new_record):
    # if some metadata has already been generated by wb_fillable, populate it now
    fields_from_wb_fillable = ["file", "field_model", "field_access_terms", "field_display_hints", "field_internet_media_type", "field_extent", "field_date_digitized"]

    for field in fields_from_wb_fillable:
        if field in row:
            if field != "field_access_terms":
                new_record[field] = row[field]
            # special handling for field_access_terms: don't overwrite values that have already been filled from ArchivesSpace
            #TODO: is this desired behavior? something else needed for audio collections?
            else:
                access_terms_already_filled = False
                if "field_access_terms" in new_record:
                    if new_record["field_access_terms"]:
                        access_terms_already_filled = True
                if not access_terms_already_filled:
                    new_record[field] = row[field]

def process_row(row, records, wb_dict_template):
    try:
        new_record = get_record_info(row['as_ref'], wb_dict_template)

        add_wb_fillable_data(row, new_record)

        records.append(new_record)

        return records
    except KeyError:
        print("'as_ref' column not found in sheet. Make sure your AS refs are in your sheet and try again.")
    except Exception as e:
        print(f"Something went wrong while processing row {row['as_ref']}: {e}")

def create_df(fields_in_use, AS_file):
    records = []
    wb_dict_template = create_one_row(fields_in_use)

    # slightly different logic to read in CSV or AS refs OR .xlsx created by wb-fillable
    if ".csv" in AS_file:
        with open(AS_file, mode='r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                records = process_row(row, records, wb_dict_template)
    elif ".xlsx" in AS_file:
        input_df = pd.read_excel(AS_file)
        input = input_df.to_dict(orient="records")

        is_first_row = True
        for row in input:
            # if this is a description row created by wb-fillable, skip it
            # as a rough proxy, check if the value entered for "file" matches the description for that field
            if is_first_row:
                if "file" in row:
                    if row["file"] == dict(c.WB_FIELDS_ORDERED_WITH_DESCRIPTION)["file"]:
                        is_first_row = False
                        continue
            else:
                records = process_row(row, records, wb_dict_template)
                is_first_row = False
            
    else:
        print("WARNING: Invalid file extension in input file")

    # INPUT_FILE = "as-refs.csv"
    # input_path = os.path.join(c.METADATA_DIR, INPUT_FILE)

    # print(records)

    # populate description for each field
    descriptions_dict = {}
    all_descriptions = dict(c.WB_FIELDS_ORDERED_WITH_DESCRIPTION)
    # all_fields = c.WB_FIELDS_ALL
    # print(all_fields)

    # iterate through one example dict to get a description for each field
    for key in records[0].keys():
        if key in all_descriptions:
            descriptions_dict[key] = all_descriptions[key]
        else:
            descriptions_dict[key] = None

    records.insert(0, descriptions_dict)

    df = pd.DataFrame(records)

    # order by order in all_fields
    # fields_in_df = df.columns.tolist()
    # final_field_order = []

    # for field in c.WB_FIELDS_ALL:
    #     if field in fields_in_use:
    #         final_field_order.append(field)

    # for field in fields_in_use:
    #     if field not in final_field_order:
    #         final_field_order.append(field)

    # df = df.reindex(columns=final_field_order)
    print(df)

    return df

def write_file(df):
    '''
    Create Pandas dataframe from final_dict, then write to Excel sheet
    '''
    print('Creating output file ...')

    #TODO: better file name
    FILE_NAME = "output.xlsx"

    # settings/logic copied from aspace-wb-scripts
    pd_ExcelWriter = pd.ExcelWriter(
        os.path.join(c.METADATA_DIR, FILE_NAME),
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

def run_script_api():
    print("code is running")
    cl_args = create_args()
    fields_in_use, AS_file = process_args(cl_args)

    df = create_df(fields_in_use, AS_file)
    write_file(df)