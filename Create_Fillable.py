'''
Creates a fillable xlsx file
'''

import os
import pandas
import re
from argparse import ArgumentParser
from datetime import datetime
import default_specs as c
import utilities.extract_dir as extract_dir
import utilities.extract_file as extract_file
import utilities.convert_data as convert_data
import utilities.use_CSVs as use_CSVs
import utilities.validate as validate


'''
Parse command line arguments
    required, positional: Workbench upload type (book/single)
    optional: --fields name of fields file to use
    optional: --AS AS file to aid in populating metadata
    optional: --filefolder alternate file path
'''
print('Checking command line arguments\nExpected: [book/single] [optional: --fields fields_file_to_use] [optional: --AS ArchivesSpacefile.xlsx] [optional: --filefolder alternate/file/directory/path] ...')

# parse arguments - see above for listing

cl_parser = ArgumentParser()
cl_parser.add_argument('type', type=str, choices=('single', 'book')) 
cl_parser.add_argument('--fields', type=str, choices=extract_dir.file_list(c.FIELDS_DIR, extensions=False))
cl_parser.add_argument('--AS', type=str)
cl_parser.add_argument('--filefolder', type=str)
cl_args = cl_parser.parse_args()

# assign arguments to variables:

# WB_type from 'type'
WB_type = cl_args.type

# fields_in_use from 'fields'
# make into a list, and make FIELDS_TITLE for reference later in making our output file
if cl_args.fields:
    FIELDS_TITLE = cl_args.fields
    fields_in_use = use_CSVs.CSV_col_to_list(os.path.join(c.FIELDS_DIR, cl_args.fields + ".csv"), 0)
    # validate fields - could move to _Validate function
    # validate fields following type
    if WB_type == 'single':
        for x in c.WB_FIELDS_REQUIRED_AT_INPUT_SINGLE:
            if x not in fields_in_use:
                raise ValueError("Fix your fields file. Missing required field: " + str(x))
    elif WB_type == 'book':
        for x in c.WB_FIELDS_REQUIRED_AT_INPUT_BOOK:
            if x not in fields_in_use:
                raise ValueError("Fix your fields file. Missing required field: " + str(x))
    # validate fields against all fields
    for x in fields_in_use:
        if x not in c.WB_FIELDS_ALL:
            raise ValueError("Fix your fields file. Contains erroneous field: " + str(x))
elif not cl_args.fields:
    # give all fields if no --fields argument
    FIELDS_TITLE = 'all_fields'
    fields_in_use = c.WB_FIELDS_ALL
# modify fields_in_use so that, if present, field_linked_agent gets split into its components
# by adding the fields, then removing 'field_linked_agent'
# if we did not do this now, when inserting these fields into the dictionary later they'd get added to the end
# and the dictionary would require reconstructing to keep the user's requested field order
if 'field_linked_agent' in fields_in_use:
    insert_index = fields_in_use.index('field_linked_agent')
    fields_in_use.insert(insert_index, 'field_linked_agent_NAME')
    fields_in_use.insert(insert_index + 1, 'field_linked_agent_ROLE')
    fields_in_use.insert(insert_index + 2, 'field_linked_agent_TYPE')
    fields_in_use.remove('field_linked_agent')
    

# use_AS from 'AS'
if cl_args.AS:
    use_AS = True
    AS_FILENAME = cl_args.AS
    # confirm the file exists as stated
    if not os.path.exists(os.path.join(c.METADATA_DIR, AS_FILENAME)):
        raise OSError("Folder " + c.METADATA_DIR + " does not appear to contain " + AS_FILENAME + ", which is a renamed ArchivesSpace Bulk Update spreadsheet. Check.")
else:
    use_AS = False

# FILES_DIR from filefolder if supplied, otherwise uses defaults
if cl_args.filefolder:
    FILES_DIR = cl_args.filefolder
    # confirm the directory exists
    if not os.path.exists(FILES_DIR):
        raise OSError("Folder " + FILES_DIR + " does not appear to exist.")
    if not os.path.isdir(FILES_DIR):
        raise OSError("Path " + FILES_DIR + " is not a directory.")
else:
    FILES_DIR = c.FILESTOUPLOAD_DIR

# make output filename based on AS or just fields_in_use
TIME = datetime.now().strftime("%Y%m%d_%H-%M-%S")
if use_AS:
    FILLABLE_FILENAME = os.path.splitext(AS_FILENAME)[0] + "_" + FIELDS_TITLE + "_" + TIME + "_FILLABLE.xlsx"
else:
    FILLABLE_FILENAME = FIELDS_TITLE + "_" + TIME + "_FILLABLE.xlsx"


print('... command line arguments parsed ...')

'''
Check our files and generate a listing of these as media_list, depending on WB_type
'''
print("Checking files ...")

# may be convenient here to grab extension to a variable so we can call it later

if WB_type == 'book':
    validate.files_in_book(FILES_DIR)
    print("Book note: script does not check exact padding. Padding needs to be 3 digits if <1000, 4+ digits if >=1000 files.")
    media_list = extract_dir.subdirectories_list(FILES_DIR)
elif WB_type == 'single':
    validate.files_in_single(FILES_DIR)
    media_list = extract_dir.file_list(FILES_DIR, extensions=True)

print("... files look okay ...")

'''
If using ArchivesSpace file, check that this file looks okay by comparing to media_list
Put number of records into records_count for easy access
'''

if use_AS:
    AS_pd_dataframe = pandas.read_excel(os.path.join(c.METADATA_DIR, AS_FILENAME), header=1)
    AS_dict = AS_pd_dataframe.to_dict(orient="list")
    # confirm that the list of media matches the number of records in AS
    records_count = AS_pd_dataframe.shape[0]
    if len(media_list) != records_count:
        raise OSError("ArchivesSpace file has " + str(records_count) + " records. " + FILES_DIR + " has " + str(len(media_list)) + " directories (if book)/files (if single). Correct the mismatch. Check that you left AS's two header rows including the machine names!")
    print('... ArchivesSpace file loaded okay ...')
else:
    records_count = len(media_list)


'''
Define functions to call for populating our dictionary
'''
prepop_dict = {}

def _file_metadata_to_WB_fields_SINGLE():
    '''
    fills the following fields from file metadata:
    file, field_model, field_resource_type, field_access_terms, field_display_hints, field_extent, field_date_digitized
    '''

    # file
    prepop_dict['file'] = media_list

    # extent, field_model, field_access_terms, field_display_hints, field_resource_type
    # all from c.extension_to_WB_field
    for d in c.extension_to_WB_field:
        # find the dictionary containing the correct extension
        if d['extension'] == os.path.splitext(media_list[0])[1]:
            # from this dictionary, populate ...
            # required fields
            prepop_dict['field_model'] = [d['field_model'] for i in range(records_count)]
            prepop_dict['field_resource_type'] = [d['field_resource_type'] for i in range(records_count)]
            # optional fields dependent on extension
            if d['field_access_terms']:
                prepop_dict['field_access_terms'] = [d['field_access_terms'] for i in range(records_count)]
            if d['field_display_hints']:
                prepop_dict['field_display_hints'] = [d['field_display_hints'] for i in range(records_count)]
            # mimetype is skipped for now pending field creation
            # use field_model to calculate extent - Image not required, Digital Document (.pdf) not yet coded
            if d['field_model'] == 'Audio':
                # get audio duration in seconds, convert to hh:mm:ss representation
                prepop_dict['field_extent'] = [
                    convert_data.seconds_to_HHMMSS(extract_file.audio_duration_seconds(os.path.join(FILES_DIR, file))) for file in media_list
                ]
            elif d['field_model'] == 'Video':
                # get video duration in seconds, convert to hh:mm:ss representation
                prepop_dict['field_extent'] = [
                    convert_data.seconds_to_HHMMSS(extract_file.video_duration_seconds(os.path.join(FILES_DIR, file))) for file in media_list
                ]

    # field_date_digitized
    # get date creation estimate, convert to year
    prepop_dict['field_date_digitized'] = [
        convert_data.unix_time_to_EDTF_year(
            extract_file.unix_time_created(os.path.join(FILES_DIR, file))
            ) for file in media_list
    ]

    
def _file_metadata_to_WB_fields_BOOK():
    '''
    fills the following fields from file metadata:
    file, field_model, field_resource_type, total_scans, field_extent, field_date_digitized
    '''

    # file
    prepop_dict['file'] = media_list

    # field_model
    prepop_dict['field_model'] = [c.field_model_BOOK for i in range(records_count)]

    # field_resource_type
    prepop_dict['field_resource_type'] = [c.field_resource_type_BOOK for i in range(records_count)]

    # extent
    # gets mapped to total_scans as-is, and the extent field which can be separately edited
    _extent = [extract_dir.file_count(os.path.join(FILES_DIR, directory)) for directory in media_list]
    prepop_dict['total_scans'] = _extent
    prepop_dict['field_extent'] = [str(e) + "p." for e in _extent]

    # field_date_digitized
    # get date creation estimate, convert to year, for every file in every folder and pick the lowest in each
    _field_date_digitized = []
    for folder in media_list:
        candidates = []
        for file in extract_dir.file_list(os.path.join(FILES_DIR, folder), extensions=True):
            candidate = extract_file.unix_time_created(os.path.join(FILES_DIR, folder, file))
            candidate = convert_data.unix_time_to_EDTF_year(candidate)
            candidates.append(candidate)
        _field_date_digitized.append(min(candidates))
    prepop_dict['field_date_digitized'] = _field_date_digitized


def _AS_metadata_to_WB_fields():
    '''
    fills the following fields from ArchivesSpace metadata:
    field_local_identifier, title, field_related_materials_note, field_edtf_date_created, field_date_created_text, field_description_long, field_note, field_linked_agent
    '''

    if 'field_local_identifier' in fields_in_use:
        prepop_dict['field_local_identifier'] = AS_dict['component_id']

    if 'title' in fields_in_use:
        prepop_dict['title'] = AS_dict['title']

    if 'field_related_materials_note' in fields_in_use:
        prepop_dict['field_related_materials_note'] = AS_dict['note/relatedmaterial/0/content']

    if 'field_edtf_date_created' or 'field_date_created_text' in fields_in_use:
        datecreatedTuple = [
            convert_data.AS_date_to_WB_date(AS_dict['dates/0/expression'][i], AS_dict['dates/0/begin'][i], AS_dict['dates/0/end'][i])
            for i in range(records_count)
        ]
        prepop_dict['field_edtf_date_created'] = [x[0] for x in datecreatedTuple]
        prepop_dict['field_date_created_text'] = [x[1] for x in datecreatedTuple]

    if 'field_description_long' in fields_in_use:
        # should this instead be in _ConvertData? do i still need to give it all the data so run the regex? any significant advantage if that's the case?
        description_values = []
        # merge all the fields that match 'scopecontent' or 'abstract' in AS
        for key, value in AS_dict.items():
            for x in ('scopecontent', 'abstract'):
                regex_match = r'^note\/' + x + r'(.*)content$'
                if re.match(regex_match, key):
                    description_values.append(value)
        # join string values at same indices within scopecontentsValues
        _field_description_long = convert_data.concatenate_strings_in_lists(description_values)
        # strip newlines
        _field_description_long = [convert_data.remove_linebreaks(x) for x in _field_description_long]
        # place in dictionary
        prepop_dict['field_description_long'] = _field_description_long

    if 'field_note' in fields_in_use:
        # as field_description_long - should this instead be in _ConvertData?
        # merge all the other note types in AS
        notes_values = []
        for key, value in AS_dict.items():
            for x in ('odd','bioghist','accruals','dimensions','altformavail','phystech','physdesc','processinfo','separatedmaterial'):
                regex_match = r'^note\/' + x + r'(.*)content$'
                if re.match(regex_match, key):
                    notes_values.append(value)
        # join string values at same indices within scopecontentsValues
        _field_note = convert_data.concatenate_strings_in_lists(notes_values)
        # strip newlines
        _field_note = [convert_data.remove_linebreaks(x) for x in _field_note]
        # place in dictionary
        prepop_dict['field_note'] = _field_note

    if 'field_linked_agent_NAME' and 'field_linked_agent_ROLE' and 'field_linked_agent_TYPE' in fields_in_use:
        # created earlier from user-supplied 'field_linked_agent'
        # create names list from ArchivesSpace's AO-Agents report
        _field_linked_agent_NAME = []
        for i in range(records_count):
            agents = '|'.join(
                convert_data.agents_from_AS_AO(AS_dict['ref_id'][i], AS_dict['title'][i])
            )
            _field_linked_agent_NAME.append(agents)
        prepop_dict['field_linked_agent_NAME'] = _field_linked_agent_NAME
        prepop_dict['field_linked_agent_ROLE'] = ['' for i in range(records_count)]
        prepop_dict['field_linked_agent_TYPE'] = ['' for i in range(records_count)]

    # access restriction - flag to user if something exists
    # previous version (very long and complicated) placed a warning in each record, but the user can be asked to look
    access_values = []
    # populate lists of access notes
    for key, value in AS_dict.items():
        if re.match(r'^note\/accessrestrict', key):
            access_values.append(value)
    # if any are not empty, raise warning
    access_issue_flag = False
    for a in access_values:
        if not validate.list_is_all_empty(a):
            access_issue_flag = True
    if access_issue_flag:
        print('!! WARNING !! One or more records contain an access restriction note in ArchivesSpace. Check the ArchivesSpace xlsx file to determine if any of the objects need to be restricted from public view.')

def _WB_uniform_fields():
    '''
    fills the following fields from uniform values:
    field_digital_origin, field_reformatting_quality
    '''

    if 'field_digital_origin' in fields_in_use:
        prepop_dict['field_digital_origin'] = [c.field_digital_origin for i in range(records_count)]

    if 'field_reformatting_quality' in fields_in_use:
        prepop_dict['field_reformatting_quality'] = [c.field_reformatting_quality for i in range(records_count)]


'''
Execute functions to fill out the dictionary
results in filled prepop_dict
'''

print('Populating fields ...')

if WB_type == 'single':
    _file_metadata_to_WB_fields_SINGLE()
elif WB_type == 'book':
    _file_metadata_to_WB_fields_BOOK()
if use_AS:
    _AS_metadata_to_WB_fields()
_WB_uniform_fields()

print('... fields populated ...')

'''
Expand prepop_dict to include all fields, and adding description row, resulting in final_dict
'''

# create a dictionary of all fields from fields_in_use, copying the structure of prepop_dict, with appropriate number of records
final_dict = {
    key: ['' for i in range(records_count)] for key in fields_in_use
}
# merge this with prepop_dict, keeping prepop_dict values
final_dict.update(prepop_dict)
# now that we have a merged dictionary, add definitions row
# first, get our field:description tuples as a dictionary
fields_descriptions_dict = dict(c.WB_FIELDS_ORDERED_WITH_DESCRIPTION)
# then for each key in prepop_dict, insert the description into the value list
for k, v in final_dict.items():
    v.insert(0, fields_descriptions_dict[k])

'''
Create Pandas dataframe from final_dict
'''
print('Creating output file ...')

# create the Pandas dataframe
output_pd_dataframe = pandas.DataFrame(final_dict)

'''
Decorate and export the output file

This line works to just create our output file but it doesn't look nice
output_pd_dataframe.to_excel(os.path.join(c.METADATA_DIR, FILLABLE_FILENAME), index=False) # index=False means no index column created

Instead, we do ... too much

Tried to implement this but could not get it to format both header and description row nicely:
https://xlsxwriter.readthedocs.io/example_pandas_header_format.html

Instead, opted to just format the description row

'''
pd_ExcelWriter = pandas.ExcelWriter(
    os.path.join(c.METADATA_DIR, FILLABLE_FILENAME),
    engine="xlsxwriter"
)
output_pd_dataframe.to_excel(
    pd_ExcelWriter, sheet_name="Workbench",
    startrow=0,
    header=True,
    index=False
)
pd_ExcelWriter_book = pd_ExcelWriter.book
pd_ExcelWriter_sheet = pd_ExcelWriter.sheets["Workbench"]
pd_description_format = pd_ExcelWriter_book.add_format(
    {
        # we can add formatting for our description row here
        # use anything defined in here: https://xlsxwriter.readthedocs.io/format.html#format-methods-and-format-properties
        'italic': True,
        'text_wrap': True,
        'valign': 'vcenter',
        'center_across': True,
        'border': 1,
        'bg_color': "#ECEBD8"
    }
)
# write the formatting
# set description row to use pd_description_format
CELL_HEIGHT_DESCRIPTION = 40
pd_ExcelWriter_sheet.set_row(1, CELL_HEIGHT_DESCRIPTION, pd_description_format)
# set cell width to something reasonable. there is no such thing as autofit all cells.
CELL_WIDTH = 30
pd_ExcelWriter_sheet.set_column(0,output_pd_dataframe.shape[1]-1,CELL_WIDTH)
# close to write the file
pd_ExcelWriter.close()
'''
End
'''
print('Done. Created file: ' + c.METADATA_DIR + '\\' + FILLABLE_FILENAME)