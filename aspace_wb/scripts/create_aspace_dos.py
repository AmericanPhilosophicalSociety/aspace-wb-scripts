'''
Simple script to take your Workbench's nodes output (.csv file) and generate an Excel file with all of ArchivesSpace's nodes fields
this can be used in an ArchivesSpace bulk update upload or however you want
'''
import os
import pandas
import argparse
from ..utils import default_specs as c
from ..utils import convert_data
from ..utils import use_CSVs

'''
Parse command line arguments
    required, positional: nodes file (csv)
'''
print('Checking command line arguments - expected: [nodes csv file] ...')

cl_parser = argparse.ArgumentParser()
cl_parser.add_argument('nodes_file', type=str)
cl_args = cl_parser.parse_args()
NODES_FILE = cl_args.nodes_file

# check existence of file
if not os.path.exists(os.path.join(c.METADATA_DIR, NODES_FILE)):
    raise OSError("Nodes file " + str(NODES_FILE) + " not found in directory " + str(c.METADATA_DIR))

# create output filename
OUTPUT_FILENAME = os.path.splitext(NODES_FILE)[0] + "_NODES-OUTPUT.xlsx"

print("... command line arguments okay ...")

'''
Load the nodes
'''

print("Loading nodes ...")

# load node file to a dictionary

nodes_pandas_DF = use_CSVs.CSV_to_pandas_dataframe(os.path.join(c.METADATA_DIR, NODES_FILE), header=True)
nodes_dict = nodes_pandas_DF.to_dict(orient="list")
nodes = nodes_dict['node_id']

print('... nodes loaded. Creating derived fields ...')

'''
Populate data
'''
digital_object_id = []
digital_object_title = []
digital_object_publish = []
file_version_file_uri = []
file_version_caption = []
file_version_publish = []

for node in nodes:
    AS_DO_dict = convert_data.diglib_node_to_AS_DO(node)
    digital_object_id.append(AS_DO_dict['digital_object_id'])
    digital_object_title.append(AS_DO_dict['digital_object_title'])
    digital_object_publish.append(AS_DO_dict['digital_object_publish'])
    file_version_file_uri.append(AS_DO_dict['file_version_file_uri'])
    file_version_caption.append(AS_DO_dict['file_version_caption'])
    file_version_publish.append(AS_DO_dict['file_version_publish'])

# create output dictionary
output_dict = {
    'id': nodes_dict['id'],
    'title': nodes_dict['title'],
    'digital_object_id': digital_object_id,
    'digital_object_title': nodes_dict['title'], # opting for title instead of id as title, reflecting guidance of late 2024. previously: digital_object_title
    'digital_object_publish': digital_object_publish,
    'file_version_file_uri': file_version_file_uri,
    'file_version_caption': file_version_caption,
    'file_version_publish': file_version_publish
}

# added this for some clarity for when titles are identical
if 'field_local_identifier' in nodes_dict:
    output_dict['field_local_identifier'] = nodes_dict['field_local_identifier']
if 'url_alias' in nodes_dict:
    output_dict['url_alias'] = nodes_dict['url_alias']

'''
Generate output xlsx
'''
output_pandas_DF = pandas.DataFrame(data=output_dict)
output_pandas_DF.to_excel(os.path.join(c.METADATA_DIR, OUTPUT_FILENAME), index=False)
print('Done. Created file: ' + os.path.join(c.METADATA_DIR, OUTPUT_FILENAME))