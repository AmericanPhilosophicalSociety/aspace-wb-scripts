'''
WORKING
creates a fillable spreadsheet for a specific type (book/single) and set of headers
headers reads from the _headers folder, and headers will include a couple of WB-specific fields so we can extract them now
'''


import os
import pandas
import re
import argparse
import _ExtractDir, _ExtractFile, _ConvertData, _CSV, _Validate

FILESTOUPLOAD_DIR = "files_to_upload" # to use a different directory, just change, doubling \
METADATA_DIR = "metadata"
HEADERS_DIR = "_headers"

# extensions to create specific field_model values
WB_field_model_extensions = {
    'Audio': ['.wav', '.mp3'],
    'Digital Document': ['.pdf'],
    'Image': ['.tif', 'tiff', '.jpg', '.jpeg'],
    'Video': ['.mp4', '.mov', '.mts']
}
# put all the above into a list for easy access
allowedFileTypes = []
for x in WB_field_model_extensions.values():
    if len(x) > 1:
        for y in x:
            allowedFileTypes.append(y)
    else:
        allowedFileTypes.append(x[0])


'''
command line arguments
required, positional: type (book/single), headers
optional: AS file to aid in populating metadata
'''
print('Checking command line arguments - expected: [book/single] [headers] [optional: --AS ArchivesSpacefile.xlsx] ...')

headerCandidates = _ExtractDir.FileList(HEADERS_DIR, extensions=False)
# argument parser
CLParser = argparse.ArgumentParser()
CLParser.add_argument('type', type=str, choices=('single', 'book'))
CLParser.add_argument('headers', type=str, choices=headerCandidates)
CLParser.add_argument('--AS', type=str)
CLargs = CLParser.parse_args()
# assign arguments
WBType = CLargs.type
HEADERS_NAME = CLargs.headers
HEADERS_FILENAME = HEADERS_NAME + ".csv"
if CLargs.AS:
    AS_FILENAME = CLargs.AS
    if AS_FILENAME not in _ExtractDir.FileList(METADATA_DIR, extensions=True):
        raise OSError("Folder " + METADATA_DIR + " does not appear to contain " + AS_FILENAME + ", which is a renamed ArchivesSpace Bulk Update spreadsheet. Check.")
    useAS = True
else:
    useAS = False
# make fillable filename based on AS or just headers
if useAS:
    FILLABLE_FILENAME = os.path.splitext(AS_FILENAME)[0] + "_FILLABLE.xlsx"
else:
    FILLABLE_FILENAME = HEADERS_NAME + "_FILLABLE.xlsx"

print('... command line arguments parsed ...')
'''
check files are okay
'''
if WBType == 'book':
    _Validate.FilesAreOkay_Book(FILESTOUPLOAD_DIR, allowedFileTypes)
    print("Book note: script does not check exact padding. Padding needs to be 3 digits if <1000, 4+ digits if >=1000 files.")
elif WBType == 'single':
    for filetype in _ExtractDir.FileTypes(FILESTOUPLOAD_DIR):
        if filetype not in allowedFileTypes:
            raise OSError("Folder " + str(FILESTOUPLOAD_DIR) + " contains unexpected files including type: " + str(filetype))
print("... files look okay ...")

'''
grab file or folder list
'''
if WBType == 'single':
    mediaList = _ExtractDir.FileList(FILESTOUPLOAD_DIR, extensions=True)
elif WBType == 'book':
    mediaList = _ExtractDir.SubDirectoriesList(FILESTOUPLOAD_DIR)
if not mediaList:
    raise OSError('No folders or files found in folder ' + FILESTOUPLOAD_DIR + ', put your folders or files here')

print('... file/folder list created ...')

'''
if using AS: load ArchivesSpace xlsx to pandas DataFrame then to a dictionary
'''
if useAS:
    ASDF = pandas.read_excel(os.path.join(METADATA_DIR, AS_FILENAME), header=1)
    ASDict = ASDF.to_dict(orient="list")
    # confirm that the list of media matches the number of records in AS
    recordsCount = ASDF.shape[0]
    if len(mediaList) != recordsCount:
        raise OSError("ArchivesSpace file has " + str(recordsCount) + " records. " + FILESTOUPLOAD_DIR + " has " + str(len(mediaList)) + " directories (if book)/files (if single). Correct the mismatch. Check that you left AS's two header rows including the machine names!")
    print('... ArchivesSpace file loaded okay ...')
else:
    recordsCount = len(mediaList)

'''
get headers into dataframe for dynamically populating
'''
headers = _CSV.CSVColToList(os.path.join(HEADERS_DIR, HEADERS_FILENAME), 0)
# some header checks
if 'WB_field_model' not in headers:
    raise ValueError("Include 'WB_field_model' in your headers file as this gets filled now")
if WBType == 'book':
    if 'WB_total_scans' not in headers:
        raise ValueError("A book needs to have 'WB_total_scans' field")
outputPandasDF = pandas.DataFrame(columns=headers)
prepopDict = {}

print('... headers put into a Pandas dataframe ...')
'''
start the prepopulation process

1. info from files
'''
print('prepopulating info from files ...')
# file
if 'file' in headers:
    prepopDict['file'] = mediaList

# extent
if 'extent' in headers:
    if WBType == 'book':
        # if book, extent is just a file count
        # extent gets mapped to total_scans as-is, and the extent field which can be separately edited
        extent_prepop = [_ExtractDir.FileCount(os.path.join(FILESTOUPLOAD_DIR, directory)) for directory in mediaList]
        prepopDict['WB_total_scans'] = extent_prepop
        extent_prepop_paged = [str(e) + "p." for e in extent_prepop]
        prepopDict['extent'] = extent_prepop_paged
    elif WBType == 'single':
        # if single, extent depends on the extension
        extent_prepop = []
        for file in mediaList:
            extension = os.path.splitext(file)[1]
            file = os.path.join(FILESTOUPLOAD_DIR, file)
            if extension in WB_field_model_extensions['Audio']:
                extent = _ExtractFile.AudioDurationSeconds(file)
                extent = _ConvertData.SecondsToHHMMSS(extent)
            elif extension in WB_field_model_extensions['Digital Document']:
                extent = _ExtractFile.PDFPageCount(file)
            elif extension in WB_field_model_extensions['Image']:
                extent = '1p.'
            elif extension in WB_field_model_extensions['Video']:
                extent = _ExtractFile.VideoDurationSeconds(file)
                extent = _ConvertData.SecondsToHHMMSS(extent)
            extent_prepop.append(extent)
        prepopDict['extent'] = extent_prepop

# WB_field_model
# identifies field_model based on type or the file extensions
if 'WB_field_model' in headers:
    if WBType == 'book':
        prepopDict['WB_field_model'] = ['Paged Content' for i in range(recordsCount)]
    elif WBType == 'single':
        WB_field_model_prepop = []
        for file in mediaList:
            extension = os.path.splitext(file)[1]
            for key, value in WB_field_model_extensions.items():
                if extension in value:
                    WB_field_model_prepop.append(key)
        prepopDict['WB_field_model'] = WB_field_model_prepop

# datedigitized
# a guess based on the date created as stored in the files
if 'datedigitized' in headers:
    if WBType == 'single':
        datedigitized_prepop = [_ExtractFile.DateCreatedUnix(os.path.join(FILESTOUPLOAD_DIR, f)) for f in mediaList]
        datedigitized_prepop = [_ConvertData.UnixToEDTFYear(d) for d in datedigitized_prepop]
        prepopDict['datedigitized'] = datedigitized_prepop
    elif WBType == 'book':
        datedigitized_prepop = []
        for folder in mediaList:
            candidates = []
            for file in _ExtractDir.FileList(os.path.join(FILESTOUPLOAD_DIR, folder), extensions=True):
                candidate = _ExtractFile.DateCreatedUnix(os.path.join(FILESTOUPLOAD_DIR, folder, file))
                candidate = _ConvertData.UnixToEDTFYear(candidate)
                candidates.append(candidate)
            datedigitized_prepop.append(min(candidates))
        prepopDict['datedigitized'] = datedigitized_prepop

print('... prepopulation from files done ...')

'''
2. ArchivesSpace data prepopulation (if using)
'''

if useAS:
    print('prepopulating info from ArchivesSpace file ...')

    if 'cuid' in headers:
        prepopDict['cuid'] = ASDict['component_id']

    if 'title' in headers:
        prepopDict['title'] = ASDict['title']

    if 'related_note' in headers:
        prepopDict['related_note'] = ASDict['note/relatedmaterial/0/content']

    # date created
    if 'datecreated_edtf' or 'datecreated_text' in headers:
        datecreatedTuple = [
            _ConvertData.ASDateToWBDate(ASDict['dates/0/expression'][i], ASDict['dates/0/begin'][i], ASDict['dates/0/end'][i])
            for i in range(recordsCount)
        ]

        if 'datecreated_edtf' in headers:
            prepopDict['datecreated_edtf'] = [x[0] for x in datecreatedTuple]

        if 'datecreated_text' in headers:
            prepopDict['datecreated_text'] = [x[1] for x in datecreatedTuple]

    # scopecontents - concatenates scopecontent and abstract
    if 'scopecontents' in headers:
        scopecontentsTypes = ('scopecontent', 'abstract')
        scopecontentsValues = []
        for key, value in ASDict.items():
            for x in scopecontentsTypes:
                regexMatch = r'^note\/' + x + r'(.*)content$'
                if re.match(regexMatch, key):
                    scopecontentsValues.append(value)
        # join string values at same indices within scopecontentsValues
        scopecontents_prepop = _ConvertData.ConcatenateStringsInLists(scopecontentsValues)
        # strip newlines
        scopecontents_prepop = [_ConvertData.RemoveLinebreaks(x) for x in scopecontents_prepop]
        prepopDict['scopecontents'] = scopecontents_prepop

    # othernotes - concatenates a longer list of other descriptions
    if 'othernotes' in headers:
        othernotesTypes = ('odd','bioghist','accruals','dimensions','altformavail','phystech','physdesc','processinfo','separatedmaterial')
        # create a list of lists of other value types
        othernotesValues = []
        for key, value in ASDict.items():
            for x in othernotesTypes:
                regexMatch = r'^note\/' + x + r'(.*)content$'
                if re.match(regexMatch, key):
                    othernotesValues.append(value)
        # join string values at same indices within scopecontentsValues
        othernotes_prepop = _ConvertData.ConcatenateStringsInLists(othernotesValues)
        # strip newlines
        othernotes_prepop = [_ConvertData.RemoveLinebreaks(x) for x in othernotes_prepop]
        prepopDict['othernotes'] = othernotes_prepop

    if 'agent_name' in headers:
        agents_prepop = []
        for i in range(recordsCount):
            agents = '|'.join(
                _ConvertData.AgentsFromASAO(ASDict['ref_id'][i], ASDict['title'][i])
            )
            agents_prepop.append(agents)
        prepopDict['agent_name'] = agents_prepop

    if 'access_type' or 'access_note' in headers:
        # access_type, access_note - just makes a flag if anything exists in these fields
        # currently (2024/12) we don't know how we're dealing with access restrictions, so this just adds some warnings to be deleted
        # get all lists of values that match the key string
        accessrestrictValues = []
        for key, value in ASDict.items():
            if re.match(r'^note\/accessrestrict', key):
                accessrestrictValues.append(value)
        # fill warning or None depending on if there's a value
        accessrestrictValuesExist = []
        for i in range(recordsCount):
            accessFlag = False
            # make the flag True if there's something in one of the note/accessrestrict fields for the record, otherwise maintain False
            for j in accessrestrictValues:
                if not pandas.isna(j[i]):
                    accessFlag = True
            # append the True/False value
            accessrestrictValuesExist.append(accessFlag)
        # put the warning in every record
        accessFlagNote = '!! Access condition exists that will not be copied over until setting access is resolved.'
        access_type_prepop = []
        for x in accessrestrictValuesExist:
            if x == True:
                access_type_prepop.append(accessFlagNote)
            else:
                access_type_prepop.append("")
        access_note_prepop = access_type_prepop
        # send user warning too
        if True in accessrestrictValuesExist:
            print(accessFlagNote)
        
        if 'access_type' in headers:
            prepopDict['access_type'] = access_type_prepop
        
        if 'access_note' in headers:
            prepopDict['access_note'] = access_note_prepop

    print('... prepopulating ArchivesSpace data done ...')


'''
3. Other Workbench-specific
'''

# we assume 'Reformatted digital', user can change if necessary
if 'WB_field_digital_origin' in headers:
    prepopDict['WB_field_digital_origin'] = ['Reformatted digital' for i in range(recordsCount)]

'''
output our fillable file
'''
print('... creating output file ...')

# populate then concatenate DataFrames
prepopPandasDF = pandas.DataFrame(data=prepopDict)
outputPandasDF = pandas.concat([outputPandasDF, prepopPandasDF], ignore_index=True)

# export into metadataDirectory
# index=False ensures not writing the index column
outputPandasDF.to_excel(os.path.join(METADATA_DIR, FILLABLE_FILENAME), index=False)

print('Done. Created file: ' + METADATA_DIR + '\\' + FILLABLE_FILENAME)