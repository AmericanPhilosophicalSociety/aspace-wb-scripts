# aspace-wb-scripts

Scripts to aid American Philosophical Society (APS) staff in preparing CSV files for ingesting files into Islandora 8 using [Workbench](https://github.com/mjordan/islandora_workbench). It can autofill metadata from the media to be uploaded, as well as from metadata within ArchivesSpace's Bulk Update Spreadsheet. It aims to reduce the need for memorization of some Workbench vocabularies, and to reduce or remove the need for copy-pasting between systems.

For fuller explanation of the Workbench fields, see the [APS Digital Library Metadata Guidelines](https://americanphilosophicalsociety.github.io/APS_digitization/metadata/).

THIS BRANCH IS AN ALPHA VERSION, NOT FULLY TESTED.

# Installation

to be written. In short:
- clone from Github
- create Python virtual environment using Python3.7 or higher (which version exactly? we need dictionaries to maintain order, hence 3.7. this was written using Python3.11)
- install requirements.txt into this venv
- create empty directories 'files_to_upload' and 'metadata'

# Usage

There are four files reflecting a typical order of usage:
- Create_Fillable.py creates a .xlsx file containing Workbench field names, derived from files that are to be uploaded. Optional flags:
    - --fields, recommended: name (no .csv extension) of fields file to use. These lists are customizable.
    - --AS, recommended: name (with .xlsx extension) of an adapted ArchivesSpace Bulk Update Spreadsheet file.
    - --filefolder: alternate directory for the location of media files to upload. This is usually only necessary when the files are too big to copy over into the local /files_to_upload/ directory, so may instead be on an external harddrive or alternate server.
- Validate_Filled.py validates a few of the fields in the filled .xlsx file
- Filled_to_WB.py exports the .csv file for use by Workbench from the filled .xlsx file
- Create_ASpace_DOs.py creates information to populate ArchivesSpace Digital Objects from Workbench's output .csv

Example:
1. Put correctly-named files into /files_to_upload/.
2. If using ArchivesSpace Bulk Update Spreadsheet, download and rename it (TO ADD: download instructions), put this into /metadata/, removing all but the first two rows (field names and field machine names), then ONE row for each object to be uploaded. Make sure the order in the ArchivesSpace sheet reflects the order of your files in /files_to_upload/.
3. Run Create_Fillable.py with appropriate flags:
```
python Create_Fillable.py book --fields fields --AS archivesspace_file.xlsx --filefolder "C:/Users/user/Documents/book_files"
```
4. Check the file that was generated in /metadata/, and fill in remaining fields. At this point you can copy your media files across to the upload server.
5. Run Validate_Filled.py, editing the file and running again if any errors were raised:
```
python Validate_Filled.py book filled_file.xlsx
```
6. Run Filled_to_WB.py to generate the output Workbench .csv:
```
python Filled_to_WB.py book filled_file.xlsx
```
7. Check the output Workbench .csv (open in Excel/Libreoffice with "text" as data type), and rename and copy this .csv over to the upload server.
8. Once the Workbench upload is complete, you can get a spreadsheet with fields for attaching ArchivesSpace's Digital Object (either via the Bulk Update Spreadsheet or the staff user interface) by running Create_ASpace_DOs.py on the .csv that Workbench produces:
```
python Create_ASpace_DOs.py workbench_output.csv
```

The argument 'book' or 'single' refers to the Workbench upload type and is a required positional argument in Create_Fillable.py, Validate_Filled.py and Filled_to_WB.py.

# User customization

The /fields/ directory contains .csv files that are lists of Workbench fields that can be used by Create_Fillable.py. This is highly recommended, as without these as called by the --fields flag, every available field will be output. Each project, department or individual user can create their own lists of fields for their use. It is recommended to have different lists of fields for each Workbench upload type (book/single) as well as optionally for different media within single (audio, video, photos etc.). See existing examples.

To create a new set of fields:
- Create a new .csv file within /fields/ and open with a text editor.
- Paste the fields, one on each line without quotes, from default_specs.py tuple "WB_FIELDS_REQUIRED_AT_INPUT_SINGLE" (if type 'single') or "WB_FIELDS_REQUIRED_AT_INPUT_BOOK" (if type 'book'). These are the required fields.
- Add fields from default_specs.py variable "WB_FIELDS_ALL", and rearrange to your liking.

Note that any fields omitted will not be autofilled from ArchivesSpace's spreadsheet.

# Maintenance

Any new Workbench fields should be added to default_specs.py:
- Add the field name, and optional description, as a tuple to WB_FIELDS_ORDERED_WITH_DESCRIPTION. Without being here, the presence of these fields will cause an error.
- If these fields are required, add them to the appropriate previous WB_FIELDS_ tuples

There are a few controlled vocabularies within /CVs/ that require occasional updates, in decreasing order of frequency:
- agents_in_AS.csv contains a row for every single ArchivesSpace Archival Object that uses an Agent. This is formatted as: name, archival_object_title, archival_object_ref_id. This can be exported using a custom report in ArchivesSpace. Update frequency: approximately monthly, to reflect new/updated finding aid data.
- cnair_subject.csv is a list of CNAIR subjects (subject terms only). The main vocabulary is at [Airtable](https://airtable.com/apph1jZcKY5ZIa42M/shrmPmyg5ZOOtyTWt) and CNAIR staff can export a .csv. Individual changes could also be hand-edited. Update frequency: whenever CNAIR changes its subjects.
- iso639.csv contains 3-letter language codes and language names from the ISO639 standard. Update frequency: infrequent, check annually if any changes were made. This file can be generated using /utilities/ISO639json_to_CSV.py (see instructions within that file)
- relator.csv contains relator names and codes from the Library of Congress's controlled vocabulary. Update frequency: infrequent (if ever), given the unlikelihood of significant changes. LOC provides a .tsv file [here](https://id.loc.gov/vocabulary/relators.html) that can be adapted.

ArchivesSpace's Bulk Update Spreadsheet is unlikely to change in fundamental structure, but field names may change. Check for other data that could be mapped to Workbench fields. 

# Testing

Testing/sample data is currently lacking. This should include sample media for various types, and sample spreadsheets.

# Omissions/assumptions

- This process assumes that a user is adding objects to existing nodes within the Digital Library. Creating a new collection node requires modifying the output Workbench .csv file after this process.
- Validate_Filled.py currently does not check for appropriate degree of padding of book page numbers (3 digits 1-999, 4 digits 1000-9999, etc).
- There is currently no way to validate field entry against Islandora controlled vocabularies themselves unless they are explicitly downloaded into /CVs/ and code added to validate them (in Validate_Filled.py calling a function in validate.py)
- mimetype is a future Workbench field, with a placeholder in default_specs.py variable extension_to_WB_field, and would need to be added to Create_Fillable.py
- Agents from ArchivesSpace must currently come from a custom report where the maximum (50k rows, we need something close to 80k) is overridden using the browser inspect tool. An API call could be an improvement. There is currently [a ticket](https://archivesspace.atlassian.net/browse/ANW-2376) with ArchivesSpace to include agents (and all subjects and all other fields) in the spreadsheet.

# To do

- Replace language vocabulary with one that uses ISO639-2B where different to ISO639-3 (~20 cases). Probably necessary to replace the json extraction with something that uses the ISO639 library. Alternatively, have an ISO639-2B vocabulary of these differences and reference that, as they are unlikely to change.