# aspace-wb-scripts

Scripts to aid American Philosophical Society (APS) staff in preparing CSV files for ingest into Islandora 8 using [Workbench](https://github.com/mjordan/islandora_workbench). Scripts are provided for the following tasks:

+ Generate a simplified, fillable version of a Workbench sheet with some data prepopulated (from your media files and, optionally, from an ArchivesSpace bulk update spreadsheet)
+ Validate that you have filled in your simplified Workbench sheet correctly
+ Convert your simplified Workbench sheet into a final Workbench sheet in the format required for Digital Library ingest
+ After your files have been ingested, use your Workbench output CSV to create ArchivesSpace digital objects

For fuller explanation of the Workbench fields, see the [APS Digital Library Metadata Guidelines](https://americanphilosophicalsociety.github.io/APS_digitization/metadata/).

# Installation

[copied from David's pull request instructions. this will need to be revised for regular users who aren't doing development on the code, but leaving it until we figure out how we want the process to work]

In your terminal, navigate to your Desktop and run the following command to clone this code from Github.

Clone the repo for local development:

```bash
git clone git@github.com:AmericanPhilosophicalSociety/aspace-wb-scripts.git
cd aspace-wb-scripts
```

Create a python virtual environment and install the package for local use:

On Windows:

```
python -m venv .venv
.\.venv\Scripts\activate
```

On Linux/WSL:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the version for local development:

```
pip install -e .
```

Create the required directories ```files_to_upload``` and ```metadata```:

```
mkdir files_to_upload
mkdir metadata
```

## Get updates

To get the most recent version of this code, ```cd``` to the directory containing your code and run:

```
git pull
```

# Usage

## Access appropriate directory

If you haven't done so already, ```cd``` into the directory where the package is installed, filling in your username and the appropriate path. Then activate your virtual environment.

In Windows PowerShell:

```
cd C:\Users\username\Desktop\aspace-wb-scripts
.venv\Scripts\activate
```

In VSCode terminal or Git Bash:

```
cd C:/Users/username/Desktop/aspace-wb-scripts
.venv/Scripts/activate
```

## Prepare necessary files

### Prepare media files (required)

+ Copy your media files into ```files_to_upload```. Do NOT run the script directly on files in the Digital Library Staging Area.
+ Your files should be named according to [CDS guidelines](https://americanphilosophicalsociety.github.io/APS_digitization/metadata/#file).

(If your files are too large to copy, see below for how to specify an alternate file path.)

### Prepare bulk update spreadsheet (recommended)

If the collection you're ingesting already has a finding aid, you can follow these steps to populate additional data from ArchivesSpace.

+ Download an ArchivesSpace bulk update spreadsheet: in the staff interface on ArchivesSpace, find the collection you're working on and click "More" -> "Bulk Update Spreadsheet". Select as many series as you want to include. Under "Column types to include in spreadsheet," leave everything checked. Click "Download Spreadsheet."
+ In Excel, unprotect the sheet. Keep the first two rows (field human-readable names and field machine names), and one row for each object you will be ingesting. Delete any additional rows.
    + **Note**: the row order in this spreadsheet must be identical to the file order in files_to_upload.
+ Move your revised bulk update spreadsheet into ```/metadata```.

## Run scripts

This code provides you with a set of command line utilities that can be used to perform various Workbench-related tasks. These are designed to be used in sequence.

Some of these commands take optional **flags**, which give the scripts additional information about how to process your data. Flags are parameters like ```--fields``` or ```--filefolder``` that you can include in your commands, usually followed by some other piece of information such as a file name or variable. For more information and examples, see the sections below.

### Create fillable spreadsheet (```wb-fillable``` or ```wb-blank```)

Creates a simplified version of a Workbench spreadsheet, with some data prepopulated. Data is pulled from media files, with the option to add additional data from an ArchivesSpace bulk update spreadsheet.

| Information | Acceptable input | Required? | Flag | Example
| --- | --- | --- | --- | --- |
| Workbench upload type | ```book``` (an object with multiple pages) or ```single``` (a graphic, audio, or video object) | Yes | |  book |
| Fields to include | Name of a .csv file containing a list of fields to include. Omit the .csv extension. You can create your own custom list (see below) or use one of the preset options: ```example_minimum_book```, ```example_minimum_single```, ```cnairaudio```, ```cnairbook```, or ```cnairimage```. If no list of fields is specified, all valid Workbench fields will be included. | Recommended | ```--fields```  | example_minimum_book |
| Bulk update spreadsheet | Name (with .xlsx extension) of an adapted ArchivesSpace bulk update spreadsheet file | Recommended | ```--AS```  | update.xlsx
| Path to media folder | Location of the folder containing your media files. Only necessary if you haven't copied these files into ```/files_to_upload```. Use forward slashes and if any directory names contain spaces, surround them in quotes. | No | ```--filefolder```  | C:/Users/yshiroma/Desktop/"Files to Upload" |

Example command with minimum required information:

```bash
wb-fillable book
```

Example command with all flags:

```bash
wb-fillable book --fields fields_file --AS archivesspace_file.xlsx --filefolder C:/Users/username/Desktop/"Folder Name"
```

**To create a blank spreadsheet with a particular set of fields, without drawing any information from media files** run the following command:

```bash
wb-blank book --fields fields_file 
```

Check in ```/metadata``` that your output has been created successfully. It should be named ```output_wb-fillable``` or ```output_wb-blank```, depending on which script you used (with 'output' replaced by the name of your ArchivesSpace bulk update sheet if you provided one).

### Manually fill spreadsheet

Depending on your input, different Workbench fields will be prepopulated in ```output_wb-fillable```. Your spreadsheet will also include a row of help text below the field names indicating what information needs to be entered and which values have been auto-generated.

Fill out the remaining fields according to standard Workbench guidelines, with a few exceptions:

+ ```id```, ```parent_id```, ```field_weight```, ```field_display_hints```, and ```field_metadata_title``` are omitted in ```output_wb_fillable``` because they will be filled in automatically later by ```wb-to-wb```
+ For any field marked "Fills down," you can fill in a value only once and it will be auto-filled to any blank cell below it in that column
+ ```field_language``` can be entered as an ISO639 language name or code
+ ```field_linked_agent``` is broken out into ```field_linked_agent_NAME```, ```field_linked_agent_ROLE```, and ```field_linked_agent_TYPE```, making it possible to enter these pieces of information separately. If there are multiple linked agents, entries should be pipe-separated.

For example, consider the following ```field_linked_agent``` entry from a standard Workbench sheet:

> relators:cre:person:Nussbaum, Martha, 1947-|relators:pbl:corporate_body:American Philosophical Society

The examples below show how this same data would be entered into ```output_wb-fillable```.

| Field | Description | Example |
| --- | --- | --- |
| ```field_linked_agent_NAME``` | Name, in Library of Congress subject heading format | Nussbaum, Martha, 1947-\|American Philosophical Society |
| ```field_linked_agent_ROLE``` | Relator code, from list of Default Relationship Types | cre\|pbl |
| ```field_linked_agent_TYPE``` | Type of linked agent (```person```, ```corporate_body```, or ```family```), or an abbreviation (```p```, ```c```, or ```f```). If left blank, all entires are assumed to be persons. | person\|corporate_body |


### Validate spreadsheet (```wb-validate```)

Validates that certain fields have been entered correctly in ```output_wb-fillable```.

| Information | Acceptable input | Required? | Example |
| --- | --- | --- | --- |
| Workbench upload type | ```book``` (an object with multiple pages) or ```single``` (a graphic, audio, or video object) | Yes |  book |
| Name of your simplified workbench sheet | Name (with .xlsx extension) of your simplified Workbench sheet | Yes |  output_wb-filled.xlsx |

Run ```wb-validate```:

```bash
wb-validate book output_wb-filled.xlsx
```

This process will check the following:

+ All field names are valid
+ Titles are unique
+ Titles are given a URL alias when needed (NOTE: script does not check whether the provided URL alias is valid)
+ Relator codes and linked agent types are valid, and match the number of names listed in ```field_linked_agent_NAME```
+ Dates in ```field_edtf_date_created``` are valid
+ Correct control terms are used in ```field_cnair_subject``` and ```field_language```

Any errors will be printed to the console for you to fix manually. This script does NOT output any new files.


### Convert simplified Workbench sheet to final Workbench sheet (```wb-to-wb```)

Creates a .csv file for use by Workbench from the filled .xlsx file.

| Information | Acceptable input | Required? | Example
| --- | --- | --- | --- |
| Workbench upload type | ```book``` (an object with multiple pages) or ```single``` (a graphic, audio, or video object) | Yes |  book |
| Name of your validated, simplified Workbench sheet | File name (with .xlsx extension) | Yes |  output_wb-filled.xlsx |

Run ```wb-to-wb``` to generate the output Workbench .csv:

```bash
wb-to-wb book output_wb-filled.xlsx
```

This will output a file titled ```output_wb-to-wb.csv``` in the ```/metadata``` directory (with 'output' replaced by the name of your original input file). Check this output by opening it in Google Sheets, Excel, or your code editor. If everything looks good, you're ready to copy your .csv and media files over to the Digital Library server, following the standard ingest process.

**Note**: This process assumes that you will be adding objects to existing nodes within the Digital Library. If you are creating a new collection instead, you will need to manually enter it then adjust the values in ```id``` and ```parent_id```. See the [Digital Library metadata guidelines](https://americanphilosophicalsociety.github.io/APS_digitization/metadata/#parent) for more information.

### Create ArchivesSpace digital objects (```wb-create-dos```)

After your media files have been ingested, use your Workbench output CSV to generate the metadata needed to create digital objects in ArchivesSpace.

| Information | Acceptable input | Required? | Example
| --- | --- | --- | --- |
| Name of your Workbench output CSV | File name (with .csv extension) | Yes | 2026-02-13_output_YDS.csv |

Run the following command:

```bash
wb-create-dos workbench_output.csv
```

This will output a file titled ```output_wb-create-dos.csv``` in the ```/metadata``` directory (with 'output' replaced by the name of your original input file). You can then copy/paste information from this CSV into an ArchivesSpace bulk update spreadsheet to create digital object links. For full guidelines, see [here](https://americanphilosophicalsociety.github.io/APS_digitization/digitization/#instructions-for-archivesspace).

**Note:** ArchivesSpace bulk update sheets expire after one week. The bulk update process will also fail if any associated records have been updated via the staff interface since the bulk update sheet was downloaded. If this happens, you will need to download a new version of the ArchivesSpace spreadsheet, or create the Digital Objects manually in the ArchivesSpace staff user interface.

# User customization

The ```/fields``` directory contains .csv files with lists of Workbench fields required for differnt upload types (e.g. book or single) and different media types (e.g. audio or image). These are selected by the ```--fields``` in ```workbench-fillable``` and ```workbench-blank```.

To create your own customized list of fields, follow these instructions:

- Duplicate and rename "example_minimum.book.csv" or "example_minimum_single.csv". Keep the .csv extension. These files contain the minimum fields required when running ```wb-fillable```.
- Add any other fields you need and rearrange to your liking.

**Note**: when auto-filling data from an ArchivesSpace bulk update spreadsheet, only fields included in your list can be auto-filled. See the function '_AS_metadata_to_WB_fields' in ```wb-fillable``` for which fields are attempted.

# Maintenance

Any new Workbench fields should be added to ```utilities/default_specs.py```:
- Add the field name, and optional description, as a tuple to WB_FIELDS_ORDERED_WITH_DESCRIPTION. Without being here, the presence of these fields will cause an error.
- If these fields are required, add them to the appropriate previous WB_FIELDS_ tuples

There are a few controlled vocabularies within /CVs/ that require occasional updates, in decreasing order of frequency:
- agents_in_AS.csv contains a row for every single ArchivesSpace Archival Object that uses an Agent. This is formatted as: name, archival_object_title, archival_object_ref_id. This can be exported using a custom report in ArchivesSpace. Update frequency: approximately monthly, to reflect new/updated finding aid data.
- cnair_subject.csv is a list of CNAIR subjects (subject terms only). The main vocabulary is at [Airtable](https://airtable.com/apph1jZcKY5ZIa42M/shrmPmyg5ZOOtyTWt) and CNAIR staff can export a .csv. Individual changes could also be hand-edited. Update frequency: whenever CNAIR changes its subjects.
- iso639.csv contains 3-letter language codes and language names from the ISO639 standard. Update frequency: infrequent, check annually if any changes were made. Previously this file was generated using utils/ISO639json_to_CSV.py (see instructions within that file), though this did not account for the newer change to prefer ISO639-2b codes where different.
- relator.csv contains relator names and codes from the Library of Congress's controlled vocabulary. Update frequency: infrequent (if ever), given the unlikelihood of significant changes. LOC provides a .tsv file [here](https://id.loc.gov/vocabulary/relators.html) that can be adapted.

ArchivesSpace's Bulk Update Spreadsheet is unlikely to change in fundamental structure, but field names may change. Check for other data that could be mapped to Workbench fields. 

# Testing

Testing/sample data is currently lacking. This should include sample media for various types, and sample spreadsheets.

# Omissions/assumptions/known issues

- There is currently no way to validate field entry against Islandora controlled vocabularies themselves unless they are explicitly downloaded into /CVs/ and code added to validate them (in ```wb-validate``` calling a function in utils/validate.py)
- Agents from ArchivesSpace must currently come from a custom report where the maximum (50k rows, we need something close to 80k) is overridden using the browser inspect tool. An API call could be an improvement. There is currently [a ticket](https://archivesspace.atlassian.net/browse/ANW-2376) with ArchivesSpace to include agents (and all subjects and all other fields) in the spreadsheet.

# To do

- Replace language vocabulary with one that uses ISO639-2B where different to ISO639-3 (~20 cases). Probably necessary to replace the json extraction with something that uses the ISO639 library. Alternatively, have an ISO639-2B vocabulary of these differences and reference that, as they are unlikely to change. Temporary fix was to just edit the iso639.csv file to use 2B for a few languages.
- To avoid duplication, the functionality of ```wb-blank``` (which is ```wb-fillable``` but bypassing any file metadata) could be incorporated into ```wb-fillable``` using a flag, e.g. --blank. This would require putting the file checking and metadata extraction into dedicated functions.
- After upgrade to ArchivesSpace v4, adapt Bulk Update Spreadsheet instructions and check for any discrepency between old and new sheets.
- reorder output of ```wb-create-dos``` so all AS-entry fields are to the right

# Contributing

This library is under active development and welcomes contributions. Please work from the existing issues before submitting a pull request.

## Installation for development

Clone the repo for local development:

```bash
git clone git@github.com:AmericanPhilosophicalSociety/aspace-wb-scripts.git
cd aspace-wb-scripts
```

Create a python virtual environment and install the package for local use:

On Windows:

```
python -m venv .venv
.\.venv\Scripts\activate
```

On Linux/WSL:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the version for local development:

```
pip install -e .
```

Create a new git branch for your work, replacing ```new-feature``` with a descriptive branch name:

```
git branch new-feature
git checkout new-feature
```

