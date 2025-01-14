'''
WORKING
simple script to take your Workbench's nodes output (.csv file) and generate an Excel file with all of ArchivesSpace's nodes fields
this can be used in an ArchivesSpace bulk update upload or however you want
'''
import os
import pandas
import argparse
import _ExtractDir, _ConvertData, _CSV

METADATA_DIR = "metadata"

# command line: nodes file

print('Checking command line arguments - expected: [nodes csv file] ...')

CLParser = argparse.ArgumentParser()
CLParser.add_argument('nodes_file', type=str)
CLargs = CLParser.parse_args()
NODESFILE = CLargs.nodes_file

metadataFiles = _ExtractDir.FileList(METADATA_DIR, extensions=True)
if NODESFILE not in metadataFiles:
    raise OSError("Nodes file " + str(NODESFILE) + " not found in directory " + str(METADATA_DIR))

OUTPUT_FILENAME = os.path.splitext(NODESFILE)[0] + "_NODES-OUTPUT.xlsx"

print("... command line arguments okay ...")
print("Loading nodes ...")

# load node file to a dictionary

nodesPandasDF = _CSV.CSVToPandasDF(os.path.join(METADATA_DIR, NODESFILE), header=True)
nodesDict = nodesPandasDF.to_dict(orient="list")
nodes = nodesDict['node_id']

print('... nodes loaded. Creating derived fields ...')

# populate data

digital_object_id = []
digital_object_title = []
digital_object_publish = []
file_version_file_uri = []
file_version_caption = []
file_version_publish = []

for node in nodes:
    ASDODict = _ConvertData.DigLibNodeToASDO(node)
    digital_object_id.append(ASDODict['digital_object_id'])
    digital_object_title.append(ASDODict['digital_object_title'])
    digital_object_publish.append(ASDODict['digital_object_publish'])
    file_version_file_uri.append(ASDODict['file_version_file_uri'])
    file_version_caption.append(ASDODict['file_version_caption'])
    file_version_publish.append(ASDODict['file_version_publish'])

# create dictionary

outputDict = {
    'id': nodesDict['id'],
    'title': nodesDict['title'],
    'digital_object_id': digital_object_id,
    'digital_object_title': nodesDict['title'], # opting for title instead of id as title, reflecting guidance of late 2024. previously: digital_object_title
    'digital_object_publish': digital_object_publish,
    'file_version_file_uri': file_version_file_uri,
    'file_version_caption': file_version_caption,
    'file_version_publish': file_version_publish
}

# output to xlsx

outputPandasDF = pandas.DataFrame(data=outputDict)
outputPandasDF.to_excel(os.path.join(METADATA_DIR, OUTPUT_FILENAME), index=False)
print('Done. Created file: ' + METADATA_DIR + '\\' + OUTPUT_FILENAME)