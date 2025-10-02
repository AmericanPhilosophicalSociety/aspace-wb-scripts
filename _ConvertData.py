from datetime import datetime
import re
import pandas
import os
import _Constants_and_Mappings as c
import _Validate, _CSV

'''
on import, get our big CSVs so they're reusable rather than re-loaded into memory every time the function is called
'''
# agents_in_csv has 3 columns: agent, title (of the archival object), refid
AGENTS_PATH = os.path.join(c.CV_DIR, c.AS_AGENTS_FILENAME)
agents_agent = _CSV.CSV_col_to_list(AGENTS_PATH, 0)
agents_titles = _CSV.CSV_col_to_list(AGENTS_PATH, 1)
agents_refids = _CSV.CSV_col_to_list(AGENTS_PATH, 2)

# language
# CSV is formatted language name, code. get two options for easy lookup.
LANGUAGES_PATH = os.path.join(c.CV_DIR, c.ISO639_FILENAME)
languages_name_first = _CSV.two_col_CSV_to_dict(LANGUAGES_PATH)
languages_code_first = {value: key for key, value in languages_name_first.items()}

'''
time/date functions

first few are Unix to date conversion - for precise dates (implied if there is a Unix Epoch time)
'''

def unix_time_to_EDTF_day(unix):
    # returns YYYY-MM-DD of a Unix input
    return datetime.fromtimestamp(unix).strftime('%Y-%m-%d')
    
def unix_time_to_EDTF_month(unix):
    # returns YYYY-MM
    return datetime.fromtimestamp(unix).strftime('%Y-%m')
    
def unix_time_to_EDTF_year(unix):
    # returns YYYY
    return datetime.fromtimestamp(unix).strftime('%Y')

def EDTF_interval_to_begin_end(edtf):
    # takes EDTF interval, returns first and last
    # simple split around /
    edtf = str(edtf)
    if "/" not in edtf:
        return ValueError("Tried to split interval date but " + edtf + " does not appear to be an interval date")
    else:
        return str(edtf).split('/')
    
def begin_end_to_EDTF_interval(begin, end):
    # takes a begin and end date (assuming correctly EDTF formatted individually), returns around /
    return str(begin) + "/" + str(end)
    
def seconds_to_HHMMSS(seconds):
    '''
    returns hh:mm:ss representation of int seconds, under 100 hours
    '''
    # if i accidentally receive a float, this gets very messed up
    seconds = int(seconds)
    # limit to under 100 hours so hh:mm:ss works
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


def text_date_to_ISO8601(input):
    '''
    incomplete, not used. consider using an external library if this is to be expanded.
    convert some common text dates that we use into ISO 8601 dates, which can be plugged directly into AS's date field
    outputs successful ISO 8601 (YYYY-MM-DD) or None
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
    if _Validate.ISO8601_date(input):
        return input
    # discard if there's date uncertainty represented as '?'
    if '?' in input:
        return None
    # check patterns: YYYY space [anything]; YYYY space [anything] space DD
    #YMDmatch = re.compile('^\d\d\d\d(\s)(.*)(\s)\d\d$')
    #if re.fullmatch(YMDmatch, input):


def AS_date_to_WB_date(expression, begin, end):
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
            return (begin_end_to_EDTF_interval(begin, end), "")


'''
other - a big messy list, alphabetized
'''

def agents_info_to_WB_agent(agent_names, agent_relators, agent_types):
    '''
    return the full WB agents piped list from piped components
    '''
    # split all values
    ns = str(agent_names).split("|")
    rs = str(agent_relators).split("|")
    # if type exists, use and convert, otherwise fill 'person'
    if agent_types:
        ts = str(agent_types).split("|")
        ts = [agent_type_abbreviation_to_full(t) for t in ts]
    else:
        ts = ["person" for name in ns]
    # return re-joined agents
    return ".".join(
        [
            agent_info_to_WB_agent_string(
            agent_name = ns[i],
            agent_relator = rs[i],
            agent_type = ts[i]
            )
            for i in range(len(agent_names))
        ]
    )

def agent_info_to_WB_agent_string(agent_name, agent_relator, agent_type):
    '''
    return the string as needed by Workbench for a single agent
    format returned: relators:[relationship type abbreviation]:[type of name]:[authorized or local name]
    '''
    return "relators:" + str(agent_relator) + ":" + str(agent_type) + ":" + str(agent_name)

def agent_type_abbreviation_to_full(agent_type):
    '''
    expands an abbreviated agent type to a full one
    '''
    if agent_type in ("person", "corporate_body", "family"):
        return agent_type
    elif agent_type == "p":
        return "person"
    elif agent_type == "c":
        return "corporate_body"
    elif agent_type == "f":
        return "family"

def agents_from_AS_AO(refid_to_find, title_to_find):
    '''
    takes a refid and title and tries to find matches in the agents_in_AS csv file
    the accuracy relies on agents_in_AS being current, and does not work if there is no title (which occurs in some records, they only have dates)
    '''
    # match instances of refid
    refid_indices = [i for i, e in enumerate(agents_refids) if e == refid_to_find]
    # narrow to ones that match title. this isn't foolproof but it's the closest we can do.
    refid_indices = [i for i in refid_indices if agents_titles[i] == title_to_find]
    # return all agents as a list
    agents = [agents_agent[i] for i in refid_indices]
    return agents

def CNAIR_audio_CUID_to_carrier_id(input):
    '''
    chop off the end hyphen. probably has no use.
    '''
    # uses regex \w to return everything before a hyphen, because a hyphen stops a word
    return re.match("^\w+", input).group(0)

def concatenate_strings_in_lists(input):
    '''
    from a list of equal-length lists, outputs concatenation of each index across lists
    used for combining ArchivesSpace's various notes into one long note
    expected input: list of lists, each containing string or None
    does *not* check if the lists are the same length
    '''
    output = []
    for i in range(len(input[0])):
        individualString = ' '.join(j[i] for j in input if isinstance(j[i], str))
        output.append(individualString)
    return output

def diglib_node_to_AS_DO(input):
    '''
    from a node number as input, generates fields for AS Digital Object creation
    actual implemented use skips this definition of 'title' in favor of WB title
    '''
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

def language_info_to_WB_language_string(language_name, code):
    '''
    takes language name and ISO639 code and returns WB format: language (code)
    '''
    return str(language_name + " (" + code + ")")

def language_name_or_ISO639_code_to_WB_language(input):
    '''
    takes a language name OR an ISO639 code and returns a WB language string
    optionally allow wrong case too?
    '''
    if input in languages_name_first.keys():
        return language_info_to_WB_language_string(input, languages_name_first[input])
    elif input in languages_code_first.values():
        return language_info_to_WB_language_string(languages_code_first[input], input)


def pipe_to_semicolon(input):
    '''
    from a string that is pipe-separated, returns a string that is semi-colon-separated with spaces
    '''
    return input.replace('|', '; ')

def relator_code_to_relator_title(input):
    '''
    unused - code is in relator.csv column 0, title is in 1
    '''
    return _CSV.neighbor_from_value_in_CSV_col(os.path.join(c.CV_DIR, c.RELATOR_CODES_FILENAME), input, 0, 1)

def remove_linebreaks(input):
    '''
    from a string, remove all linebreaks
    '''
    return ' '.join(input.splitlines())

def unique_in_list(input):
    '''
    from a list, returns a list of unique values in the order they first appear
    this is really hacky - dictionary order preserves insertion order. so keep trying to add it to a dictionary and it'll ignore the duplicates.
    '''
    return list(dict.fromkeys(input))