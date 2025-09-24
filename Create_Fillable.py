import os
import pandas
import re
from argparse import ArgumentParser
import _Constants_and_Mappings as c
import _ExtractDir, _ExtractFile, _ConvertData, _CSV, _Validate


'''
Parse command line arguments
    required, positional: Workbench upload type (book/single)
    optional: name of fields file to use
    optional: AS file to aid in populating metadata
    optional: alternate file path
'''
print('Checking command line arguments\nExpected: [book/single] [optional: --fields fields_file_to_use] [optional: --AS ArchivesSpacefile.xlsx] [optional: --filefolder alternate/file/directory/path] ...')

# parse arguments - see above for listing

cl_parser = ArgumentParser()
cl_parser.add_argument('type', type=str, choices=('single', 'book')) 
cl_parser.add_argument('--fields', type=str, choices=_ExtractDir.FileList(c.FIELDS_DIR, EXTENSIONS=False))
cl_parser.add_argument('--AS', type=str)
cl_parser.add_argument('--filefolder', type=str)
cl_args = cl_parser.parse_args()

# assign arguments to variables:

# WB_type from 'type'
WB_type = cl_args.type

# fields_in_use from 'fields'
if cl_args.fields:
    fields_in_use = _CSV.CSVColToList(os.path.join(c.FIELDS_DIR, cl_args.fields, ".csv"), 0)
elif not cl_args.fields:
    fields_in_use = c.WB_FIELDS_ALL

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

print('... command line arguments parsed ...')

'''
Check our files and generate a listing of these as media_list, depending on WB_type
'''
print("Checking files ...")

# may be convenient here to grab extension to a variable so we can call it later

if WB_type == 'book':
    _Validate.files_in_book(FILES_DIR)
    print("Book note: script does not check exact padding. Padding needs to be 3 digits if <1000, 4+ digits if >=1000 files.")
    media_list = _ExtractDir.FileList(FILES_DIR, extensions=True)
elif WB_type == 'single':
    _Validate.files_in_single(FILES_DIR)
    media_list = _ExtractDir.SubDirectoriesList(FILES_DIR)

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

def file_metadata_to_WB_fields_SINGLE():

    # file
    prepop_dict['file'] = media_list

    # extent, field_model, field_access_terms, field_display_hints, field_resource_type
    # all from c.extension_to_WB_field
    # NEXT BIT - THIS IS NOT IT
    _extent = []
    for file in media_list:
        extension = os.path.splitext(file)[1]
        file = os.path.join(FILES_DIR, file)
        if extension in WB_field_model_EXTENSIONS['Audio']:
            extent = _ExtractFile.AudioDurationSeconds(file)
            extent = _ConvertData.SecondsToHHMMSS(extent)
        elif extension in WB_field_model_EXTENSIONS['Digital Document']:
            extent = _ExtractFile.PDFPageCount(file)
        elif extension in WB_field_model_EXTENSIONS['Image']:
            extent = '1p.'
        elif extension in WB_field_model_EXTENSIONS['Video']:
            extent = _ExtractFile.VideoDurationSeconds(file)
            extent = _ConvertData.SecondsToHHMMSS(extent)
        _extent.append(extent)
    prepop_dict['extent'] = _extent

def file_metadata_to_WB_fields_BOOK():

    # file
    prepop_dict['file'] = media_list

    # extent
    # gets mapped to total_scans as-is, and the extent field which can be separately edited
    _extent = [_ExtractDir.FileCount(os.path.join(FILES_DIR, directory)) for directory in media_list]
    prepop_dict['total_scans'] = _extent
    prepop_dict['extent'] = [str(e) + "p." for e in _extent]

    # field_model
    prepop_dict['WB_field_model'] = [c.DEFAULT_BOOK_field_model for i in range(records_count)]



'''
start the prepopulation process

1. info from files
'''
print('prepopulating info from files ...')


# WB_field_model
# identifies field_model based on type or the file EXTENSIONS
if 'WB_field_model' in fields_in_use:
    if WB_type == 'book':
        prepop_dict['WB_field_model'] = ['Paged Content' for i in range(records_count)]
    elif WB_type == 'single':
        WB_field_model_prepop = []
        for file in media_list:
            extension = os.path.splitext(file)[1]
            for key, value in WB_field_model_EXTENSIONS.items():
                if extension in value:
                    WB_field_model_prepop.append(key)
        prepop_dict['WB_field_model'] = WB_field_model_prepop

# datedigitized
# a guess based on the date created as stored in the files
if 'datedigitized' in fields_in_use:
    if WB_type == 'single':
        datedigitized_prepop = [_ExtractFile.DateCreatedUnix(os.path.join(c.FILESTOUPLOAD_DIR, f)) for f in media_list]
        datedigitized_prepop = [_ConvertData.UnixToEDTFYear(d) for d in datedigitized_prepop]
        prepop_dict['datedigitized'] = datedigitized_prepop
    elif WB_type == 'book':
        datedigitized_prepop = []
        for folder in media_list:
            candidates = []
            for file in _ExtractDir.FileList(os.path.join(c.FILESTOUPLOAD_DIR, folder), EXTENSIONS=True):
                candidate = _ExtractFile.DateCreatedUnix(os.path.join(c.FILESTOUPLOAD_DIR, folder, file))
                candidate = _ConvertData.UnixToEDTFYear(candidate)
                candidates.append(candidate)
            datedigitized_prepop.append(min(candidates))
        prepop_dict['datedigitized'] = datedigitized_prepop

print('... prepopulation from files done ...')

'''
2. ArchivesSpace data prepopulation (if using)
'''

if use_AS:
    print('prepopulating info from ArchivesSpace file ...')

    if 'cuid' in fields_in_use:
        prepop_dict['cuid'] = AS_dict['component_id']

    if 'title' in fields_in_use:
        prepop_dict['title'] = AS_dict['title']

    if 'related_note' in fields_in_use:
        prepop_dict['related_note'] = AS_dict['note/relatedmaterial/0/content']

    # date created
    if 'datecreated_edtf' or 'datecreated_text' in fields_in_use:
        datecreatedTuple = [
            _ConvertData.ASDateToWBDate(AS_dict['dates/0/expression'][i], AS_dict['dates/0/begin'][i], AS_dict['dates/0/end'][i])
            for i in range(records_count)
        ]

        if 'datecreated_edtf' in fields_in_use:
            prepop_dict['datecreated_edtf'] = [x[0] for x in datecreatedTuple]

        if 'datecreated_text' in fields_in_use:
            prepop_dict['datecreated_text'] = [x[1] for x in datecreatedTuple]

    # scopecontents - concatenates scopecontent and abstract
    if 'scopecontents' in fields_in_use:
        scopecontentsTypes = ('scopecontent', 'abstract')
        scopecontentsValues = []
        for key, value in AS_dict.items():
            for x in scopecontentsTypes:
                regexMatch = r'^note\/' + x + r'(.*)content$'
                if re.match(regexMatch, key):
                    scopecontentsValues.append(value)
        # join string values at same indices within scopecontentsValues
        scopecontents_prepop = _ConvertData.ConcatenateStringsInLists(scopecontentsValues)
        # strip newlines
        scopecontents_prepop = [_ConvertData.RemoveLinebreaks(x) for x in scopecontents_prepop]
        prepop_dict['scopecontents'] = scopecontents_prepop

    # othernotes - concatenates a longer list of other descriptions
    if 'othernotes' in fields_in_use:
        othernotesTypes = ('odd','bioghist','accruals','dimensions','altformavail','phystech','physdesc','processinfo','separatedmaterial')
        # create a list of lists of other value types
        othernotesValues = []
        for key, value in AS_dict.items():
            for x in othernotesTypes:
                regexMatch = r'^note\/' + x + r'(.*)content$'
                if re.match(regexMatch, key):
                    othernotesValues.append(value)
        # join string values at same indices within scopecontentsValues
        othernotes_prepop = _ConvertData.ConcatenateStringsInLists(othernotesValues)
        # strip newlines
        othernotes_prepop = [_ConvertData.RemoveLinebreaks(x) for x in othernotes_prepop]
        prepop_dict['othernotes'] = othernotes_prepop

    if 'agent_name' in fields_in_use:
        agents_prepop = []
        for i in range(records_count):
            agents = '|'.join(
                _ConvertData.AgentsFromASAO(AS_dict['ref_id'][i], AS_dict['title'][i])
            )
            agents_prepop.append(agents)
        prepop_dict['agent_name'] = agents_prepop

    if 'access_type' or 'access_note' in fields_in_use:
        # access_type, access_note - just makes a flag if anything exists in these fields
        # currently (2024/12) we don't know how we're dealing with access restrictions, so this just adds some warnings to be deleted
        # get all lists of values that match the key string
        accessrestrictValues = []
        for key, value in AS_dict.items():
            if re.match(r'^note\/accessrestrict', key):
                accessrestrictValues.append(value)
        # fill warning or None depending on if there's a value
        accessrestrictValuesExist = []
        for i in range(records_count):
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
        
        if 'access_type' in fields_in_use:
            prepop_dict['access_type'] = access_type_prepop
        
        if 'access_note' in fields_in_use:
            prepop_dict['access_note'] = access_note_prepop

    print('... prepopulating ArchivesSpace data done ...')


'''
3. Other Workbench-specific
'''

# we assume 'Reformatted digital', user can change if necessary
if 'WB_field_digital_origin' in fields_in_use:
    prepop_dict['WB_field_digital_origin'] = ['Reformatted digital' for i in range(records_count)]

'''
output our fillable file
'''
print('... creating output file ...')

# populate then concatenate DataFrames
outputPandAS_pd_dataframe = pandas.concat([pandas.DataFrame(columns=fields_in_use), pandas.DataFrame(data=prepop_dict)], ignore_index=True)

# make fillable filename based on AS or just fields_in_use
if use_AS:
    FILLABLE_FILENAME = os.path.splitext(AS_FILENAME)[0] + "_FILLABLE.xlsx"
else:
    FILLABLE_FILENAME = HEADERS_NAME + "_FILLABLE.xlsx"

# export into metadataDirectory
# index=False ensures not writing the index column
outputPandAS_pd_dataframe.to_excel(os.path.join(c.METADATA_DIR, FILLABLE_FILENAME), index=False)

print('Done. Created file: ' + c.METADATA_DIR + '\\' + FILLABLE_FILENAME)