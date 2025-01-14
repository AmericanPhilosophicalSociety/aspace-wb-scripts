from datetime import datetime
import re
import pandas
import _Validate, _CSV

'''
on import, get our big CSVs so they're reusable rather than re-loaded into memory every time the function is called
'''
# agents_in_csv has 3 columns: agent, title (of the archival object), refid
agents_path = "_CVs/agents_in_AS.csv"
agents_agent = _CSV.CSVColToList(agents_path, 0)
agents_titles = _CSV.CSVColToList(agents_path, 1)
agents_refids = _CSV.CSVColToList(agents_path, 2)

'''
time/date functions

first few are Unix to date conversion - for precise dates (implied if there is a Unix Epoch time)
'''

def UnixToEDTFDay(unix):
    # returns YYYY-MM-DD of a Unix input
    return datetime.fromtimestamp(unix).strftime('%Y-%m-%d')
    
def UnixToEDTFMonth(unix):
    # returns YYYY-MM
    return datetime.fromtimestamp(unix).strftime('%Y-%m')
    
def UnixToEDTFYear(unix):
    # returns YYYY
    return datetime.fromtimestamp(unix).strftime('%Y')

def EDTFIntervalToBeginEnd(edtf):
    # takes EDTF interval, returns first and last
    # simple split around /
    edtf = str(edtf)
    if "/" not in edtf:
        return ValueError("Tried to split interval date but " + edtf + " does not appear to be an interval date")
    else:
        return str(edtf).split('/')
    
def BeginEndToEDTFInterval(begin, end):
    # takes a begin and end date (assuming correctly EDTF formatted individually), returns around /
    return str(begin) + "/" + str(end)
    
def SecondsToHHMMSS(seconds):
    # if i accidentally receive a float, this gets very messed up
    seconds = int(seconds)
    # returns hh:mm:ss of seconds
    longest = int(100*60*60)
    if seconds >= longest:
        raise ValueError("something is wrong, the seconds supplied - " + str(seconds) + " - is over 100 hours. too many seconds to represent as hh:mm:ss")
    # get the seconds, minutes, hours using simple division
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    # pad all to 2 characters
    h = str(h).zfill(2)
    m = str(m).zfill(2)
    s = str(s).zfill(2)
    return h + ":" + m + ":" + s


def TextDateToISO8601(input):
    '''
    incomplete
    convert some common text dates that we use into ISO 8601 dates, which can be plugged directly into AS's date field
    outputs successful ISO 8601 (YYYY-MM-DD) or None
    currently handles only:
        1849 Aug. 15
    '''
    MONTHS = {
        '01': ['jan', 'jan.', 'january'],
        '02': ['feb', 'feb.', 'february'],
        '03': ['mar', 'mar.', 'march'],
        '04': ['apr', 'apr.', 'april'],
        '05': ['may'],
        '06': ['june'],
        '07': ['july'],
        '08': ['aug', 'aug.', 'august'],
        '09': ['sept', 'sept.', 'september'],
        '10': ['oct', 'oct.', 'october'],
        '11': ['nov', 'nov.', 'november'],
        '12': ['dec', 'dec.', 'december']
        }
    # lowercase, strip out square brackets
    input = input.lower()
    input = re.sub('[\[\]]', '', input)
    print(input)
    # check it's not already an ISO8601 date. this eliminates well-formed YYYY, YYYY-MM, YYYY-MM-DD
    if _Validate.ISO8601Date(input):
        return input
    # discard if there's date uncertainty represented as '?'
    if '?' in input:
        return None
    # check patterns: YYYY space [anything]; YYYY space [anything] space DD
    #YMDmatch = re.compile('^\d\d\d\d(\s)(.*)(\s)\d\d$')
    #if re.fullmatch(YMDmatch, input):


def ASDateToWBDate(expression, begin, end):
    '''
    ! potential for bugs. lots of info in here.
    takes three dates in the format expression, begin, end
    outputs a tuple containing the EDTF date and the text date for use by Workbench
    non-EDTF or null values go into text, otherwise they go into EDTF date
    AS begin and end dates are already in EDTF format so we're okay just to use this as-is
    '''
    # correct the expression, begin, end
    #  turn to None if na
    if pandas.isna(expression):
        expression = None
    if pandas.isna(begin):
        begin = None
    if pandas.isna(end):
        end = None
    #  turn to int if float
    if isinstance(expression, float):
        expression = int(expression)
    if isinstance(begin, float):
        begin = int(begin)
    if isinstance(end, float):
        end = int(end)
    # do the work
    # often 'expression, begin, end' are all the same due to an old migration
    # # if there's an expression, see if it's EDTF-valid and return it
    try:
        _Validate.EDTF(expression)
        return (expression, "")
    except:
        if not begin and not end:
            if not expression:
                # if there's nothing, put "undated" into text
                return ("", "undated")
            else:
                # if it's YYYY-YYYY, change to YYYY/YYYY
                if re.fullmatch(re.compile('^\d\d\d\d-\d\d\d\d$'), expression):
                    expression = expression.replace("-","/")
                    return (expression, "")
                # otherwise put it in text date after changing it to "undated"
                elif expression in ("n.d.", "nd", "N.D.", "ND", "?", "no date"):
                    return ("", "undated")
                else:
                    return ("", expression)
        elif begin and not end:
            # if there's just a beginning, return that to EDTF date
            return (begin, "")
        elif begin and end:
            # if there's both beginning and end, return EDTF of the range to EDTF date
            return (BeginEndToEDTFInterval(begin, end), "")


'''
other - a big messy list, alphabetized
'''

def AgentRelatorAndTypeToWBAgent(agent, relatorCode, agentType):
    # return the string as needed by Workbench
    # provided documentation is: relators:[relationship type abbreviation]:[type of name]:[authorized or local name]
    return "relators:" + str(relatorCode) + ":" + str(agentType) + ":" + str(agent)

def AgentTypeAbbreviationToFull(agentType):
    if agentType in ("person", "corporate_body", "family"):
        return agentType
    elif agentType == "p":
        return "person"
    elif agentType == "c":
        return "corporate_body"
    elif agentType == "f":
        return "family"

def AgentsFromASAO(refidToFind, titleToFind):
    # takes a refid and title and tries to find matches in the agents_in_AS.csv file
    # match instances of refid
    refidIndices = [i for i, e in enumerate(agents_refids) if e == refidToFind]
    # narrow to ones that match title. this isn't foolproof but it's the closest we can do.
    refidIndices = [i for i in refidIndices if agents_titles[i] == titleToFind]
    # return all agents as a list
    agents = [agents_agent[i] for i in refidIndices]
    return agents

def CNAIRAudioCUIDToCarrierID(input):
    # uses regex \w to return everything before a hyphen, because a hyphen stops a word
    return re.match("^\w+", input).group(0)

def ConcatenateStringsInLists(input):
    # from a list of equal-length lists, outputs concatenation of each index across lists
    # used for combining ArchivesSpace's various notes into one long note
    # expected input: list of lists, each containing string or None
    # does *not* check if the lists are the same length
    output = []
    for i in range(len(input[0])):
        individualString = ' '.join(j[i] for j in input if isinstance(j[i], str))
        output.append(individualString)
        '''that replaced: individualString = ""
        for j in input:
            if isinstance(j[i], str):
                individualString += j[i]
                individualString += " "
        individualString.rstrip()'''
    return output

def DigLibNodeToASBulkImportTemplateDO(input):
    # from a node, generates fields for ArchivesSpace's Bulk Import Template Digital Object creation:
    # digital_object_id, digital_object_title, digital_object_link
    nodePrefix = "islandora8_"
    digital_object_id = nodePrefix + str(input)
    digital_object_title = nodePrefix + str(input)
    digital_object_link = "https://diglib.amphilsoc.org/node/" + str(input)
    return digital_object_id, digital_object_title, digital_object_link

def DigLibNodeToASBulkUpdateDO(input):
    # from a node, generates fields for ArchivesSpace's Bulk Update Spreadsheet Digital Object creation:
    # digital_object_id, digital_object_title, digital_object_publish, file_version_file_uri, file_version_caption, file_version_publish
    nodePrefix = "islandora8_"
    digital_object_id = nodePrefix + str(input)
    digital_object_title = nodePrefix + str(input)
    digital_object_publish = "true"
    file_version_file_uri = "https://diglib.amphilsoc.org/node/" + str(input)
    file_version_publish = "true"
    return digital_object_id, digital_object_title, digital_object_publish, file_version_file_uri, file_version_publish

def DigLibNodeToASDO(input):
    # same as above (delete above sometime) but as a dictionary
    # from a node, generates fields for AS Digital Object creation
    nodePrefix = "islandora8_"
    digital_object_id = nodePrefix + str(input)
    digital_object_title = nodePrefix + str(input)
    digital_object_publish = "true"
    file_version_file_uri = "https://diglib.amphilsoc.org/node/" + str(input)
    file_version_caption = ""
    file_version_publish = "true"
    DigitalObject = {
        'digital_object_id': digital_object_id,
        'digital_object_title': digital_object_title,
        'digital_object_publish': digital_object_publish,
        'file_version_file_uri': file_version_file_uri,
        'file_version_caption': file_version_caption,
        'file_version_publish': file_version_publish
    }
    return DigitalObject


def IntToPageExtent(input):
    return str(input) + "p."

def LanguageAndISO639CodeToWBLanguage(languageName, code):
    return str(languageName + " (" + code + ")")

def PipeToSemicolon(input):
    # from a string that is pipe-separated, make a string that is semi-colon-separated with spaces
    return input.replace('|', '; ')

def RelatorCodeToRelatorTitle(input):
    # code is in relator.csv column 0, title is in 1
    return _CSV.NeighborFromValueInCSVCol("_CVs/relator.csv", input, 0, 1)

def RemoveLinebreaks(input):
    # from a string, remove all linebreaks
    return ' '.join(input.splitlines())

def UniqueInList(input):
    # from a list, returns a list of unique values in the order they first appear
    # using this to create list of carriers for audio collection processing
    # this is really hacky - dictionary order preserves insertion order. so keep trying to add it to a dictionary and it'll ignore the duplicates.
    return list(dict.fromkeys(input))