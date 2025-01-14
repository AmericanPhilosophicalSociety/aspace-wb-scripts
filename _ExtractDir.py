'''
metadata extraction from directory
'''
import os
import _ConvertData

def FileCount(directorypath, fileextension=""):
    # returns a count of the number of files, with optional limitation for extension
    files = [x for x in os.listdir(directorypath) if os.path.isfile(os.path.join(directorypath, x))]
    # ignore Thumbs.db
    if 'Thumbs.db' in files:
        files.remove('Thumbs.db')
    if fileextension:
        files = [x for x in files if os.path.splitext(x)[1] == fileextension]
    return len(files)

def FileList(directorypath, extensions=False):
    # returns a list of file names, with extension optional
    files = [x for x in os.listdir(directorypath) if os.path.isfile(os.path.join(directorypath, x))]
    # ignore Thumbs.db
    if 'Thumbs.db' in files:
        files.remove('Thumbs.db')
    if extensions:
        return files
    else:
        return [os.path.splitext(x)[0] for x in files]
    
def FileTypes(directorypath):
    # returns a list of filetypes within directory
    # get list of files
    files = [x for x in os.listdir(directorypath) if os.path.isfile(os.path.join(directorypath, x))]
    # ignore Thumbs.db
    if 'Thumbs.db' in files:
        files.remove('Thumbs.db')
    # reduce to only the extension
    files = [os.path.splitext(x)[1] for x in files]
    # get unique in list
    files = _ConvertData.UniqueInList(files)
    return files
    
def SubDirectoriesList(directorypath):
    return [x for x in os.listdir(directorypath) if os.path.isdir(os.path.join(directorypath, x))]

def SubDirectoriesCount(directorypath):
    return len(SubDirectoriesList(directorypath))