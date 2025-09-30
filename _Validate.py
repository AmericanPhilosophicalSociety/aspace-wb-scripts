'''
functions for validating fields

if the ones that check /_CVs/ files take too long, I can instead just make a file with tuples/lists. but this seems easier to read and update than a file containing tuples/lists.

EDTF standard defined here: https://www.loc.gov/standards/datetime/

'''

import edtf_validate.valid_edtf
import re
import math
import pandas
import os
import _Constants_and_Mappings as c
import _CSV, _ExtractDir, _ExtractFile

def nan(input):
    '''
    returns True if nan, False if not
    '''
    hiimnan = False
    if isinstance(input, float):
        if math.isnan(input):
            hiimnan = True
    return hiimnan

def agent_type(input):
    agentTypes = ('p', 'c', 'f', 'person', 'corporate_body', 'family')
    if input in agentTypes:
        return True
    else:
        raise ValueError("agent_type not valid: " + str(input))

def CNAIR_culture(input):
    if _CSV.value_in_csv_col("_CVs/cnair_culture.csv", 0, input):
        return True
    else:
        raise ValueError("culture " + str(input) + " not in current cnair_culture csv. if new, you need to update/recreate csv.")

def EDTF(input):
    # checks EDTF standard 2019. no discrimination for levels but this is possible with the library.
    input = str(input)
    if edtf_validate.valid_edtf.is_valid(input):
        return True
    else:
        raise ValueError("EDTF not valid: " + str(input))
    
def files_in_book(topDirectory):
    '''
    CLEAN THIS UP. add extensions checking as separate function, add padding checking.
    confirm that the files to be uploaded for a Book upload follow correct formatting
    '''
    # files directory ...
    directoriesList = _ExtractDir.subdirectories_list(topDirectory)
    # is not empty
    if len(directoriesList) == 0:
        raise OSError("Folder " + str(topDirectory) + " contains no directories. Please put your directories with their files in.")
    # has directories named with just alphanumeric and underscore
    for directory in directoriesList:
        if not string_is_alphanumeric_and_underscore(directory):
            raise OSError("Directory " + topDirectory + "/" + directory + " is not just alphanumeric with underscores. Check all directories.")
    # each directory's files ...
    for directory in directoriesList:
        directoryFiles = _ExtractDir.file_list(os.path.join(topDirectory, directory), extensions=True)
        for file in directoryFiles:
            # has a permitted file extension
            if _ExtractFile.file_extension(file) not in c.EXTENSIONS:
                raise OSError("File " + topDirectory + "/" + directory + "/" + file + " is not in permitted filetypes. Check all files. Check with CDS if more types need to be allowed.")
            # has a name composed of directory name + hyphen + numbers
            # (isolates just the file name, not extension, to hand to validator)
            file = os.path.splitext(file)[0]
            if not string_is_match_then_hyphen_then_numbers(file, directory):
                raise OSError("File " + topDirectory + "/" + directory + "/" + file + " does not follow the correct titling: directory + hyphen + numbers. Check all files.")
    # return True if this all worked out
    return True

def files_in_single(directory):
    # ADD check that the directory is not empty
    extensions_to_check = _ExtractDir.unique_extensions(directory)
    # check we only have one extension
    if len(extensions_to_check) != 1:
        raise OSError("Only one extension allowed. Check that files all have the same extension.")
    # all extensions are valid
    for extension in extensions_to_check:
        if extension not in c.EXTENSIONS:
            raise OSError("Folder " + str(c.FILESTOUPLOAD_DIR) + " contains unexpected files including type: " + str(extension))


def ISO8601_date(input):
    # taking assumed EDTF date, check if it's a level 0 date - YYYY, YYYY-MM, YYYY-MM-DD
    # (this also would work for any arbitrary string)
    # this is the only value for a date string allowed by ArchivesSpace's date representation in Begin or End field
    input = str(input)
    dateMatches = ["^\d\d\d\d$", "^\d\d\d\d-\d\d$", "^\d\d\d\d-\d\d-\d\d$"]
    datesMatch = False
    for match in dateMatches:
        if re.match(match, input):
            datesMatch = True
    if datesMatch:
        return True
    else:
        raise ValueError(input + " is not an ISO 8601 date (= EDTF level 0 'Date') (= YYYY, YYYY-MM, YYYY-MM-DD)")

def ISO639_name(input):
    if _CSV.value_in_csv_col("_CVs/iso639.csv", 0, input):
        return True
    else:
        raise ValueError("language name " + str(input) + " not in iso639")

def ISO639_code(input):
    if _CSV.value_in_csv_col("_CVs/iso639.csv", 1, input):
        return True
    else:
        raise ValueError("language code " + str(input) + " not in iso639")
    
def list_is_all_empty(input):
    # for each item in the input list, check it's not a NaN and then check if it's anything
    # if any are anything, return false, else return true (list is all empty)
    for x in input:
        if not pandas.isna(x):
            if x:
                return False
    return True
    
def list_is_single_value_then_NaN(input):
    # returns True if a list provided is just one single value then NaN.
    # used to allow user to avoid copy-pasting a value into every row if it's always the same.
    # this doesn't really fit into this file but couldn't think where else to put it.
    #
    # we assume it's true
    ListIsIndeedSingleValueThenNan = True
    # if there's something other than NaN in the first value ...
    if not pandas.isna(input[0]):
        # and all the rest of the values are nothing ...
        for x in input[1:]:
            # update if we get a non-NaN value
            if not pandas.isna(x):
                ListIsIndeedSingleValueThenNan = False
        # return the value
        return ListIsIndeedSingleValueThenNan
    else:
        return False
    
def list_is_single_value_then_empty_string(input):
    # exactly the same as above except empty string, in data that does not contain nan
    # we assume it's true
    list_is_indeed_single_value_then_empty_string = True
    # if there's something in the first value ...
    if input[0]:
        # and all the rest of the values are nothing ...
        for x in input[1:]:
            # update if we get a non-NaN value
            if x:
                list_is_indeed_single_value_then_empty_string = False
        # return the value
        return list_is_indeed_single_value_then_empty_string
    else:
        return False
    
def piped_fields_same_length(input1, input2):
    # returns True if two pipe-separated fields are the same length
    # this is for cases where we mix the fields, e.g. agents (agent_name, agent_role)
    if len(input1.split('|')) == len(input2.split('|')):
        return True
    else:
        raise ValueError("These two pipe-separated fields need to have the same number of values to be matched correctly: " + str(input1) + " AND " + str(input2))

def relator_code(input):
    if _CSV.value_in_csv_col(os.path.join(c.CV_DIR, c.RELATOR_CODES_FILENAME), 0, input):
        return True
    else:
        raise ValueError("Relator code " + str(input) + " not in relators csv.")

def string_is_alphanumeric_and_underscore(input):
    # returns True if the input string is only alphanumeric and underscore characters
    if re.match(r'^\w+$', input):
        return True
    else:
        return False
    
def string_is_match_then_hyphen_then_numbers(fullString, beginningToMatch):
    # for validating files in a Book Object
    # returns True if fullString = beginningToMatch-numbers
    splitString = fullString.split('-')
    if len(splitString) != 2:
        return False
    if splitString[0] != beginningToMatch:
        return False
    if not string_is_numeric(splitString[1]):
        return False
    return True
                
def string_is_numeric(input):
    if re.match(r'^\d+$', input):
        return True
    else:
        return False
