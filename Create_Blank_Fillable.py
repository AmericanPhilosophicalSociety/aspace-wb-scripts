'''
Creates a blank fillable .xlsx file based on provided field names.
For situations where one is adding progressively to a Workbench sheet, rather than starting with a defined list of files.

Maintenance note:
Most of this file is copied directly from Create_Fillable.py.
For the present, this seems easier than adapting Create_Fillable.py to ignore most steps.

INITIALLY APPEARS TO BE WORKING
'''

import os
import pandas
import re
from argparse import ArgumentParser
from datetime import datetime
import default_specs as c
import utilities.extract_dir as extract_dir
import utilities.use_CSVs as use_CSVs

'''
Parse command line arguments
    required, positional: Workbench upload type (book/single)
    optional: --fields name of fields file to use
'''

# parse arguments

print('Checking command line arguments\nExpected: [book/single] [optional: --fields fields_file_to_use] ...')

cl_parser = ArgumentParser()
cl_parser.add_argument('type', type=str, choices=('single', 'book')) 
cl_parser.add_argument('--fields', type=str, choices=extract_dir.file_list(c.FIELDS_DIR, extensions=False))
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


# make output filename based on fields_in_use
TIME = datetime.now().strftime("%Y%m%d_%H-%M-%S")
FILLABLE_FILENAME = FIELDS_TITLE + "_" + TIME + "_FILLABLE.xlsx"

print('... command line arguments parsed ...')


'''
Expand prepop_dict to include all fields, and adding description row, resulting in final_dict
'''

# create a dictionary of all fields from fields_in_use, copying the structure of prepop_dict, with appropriate number of records
final_dict = {
    key: [''] for key in fields_in_use
}
# add definitions row
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