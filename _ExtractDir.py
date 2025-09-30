'''
metadata extraction from directory
'''
import os
import _ConvertData

def file_count(directorypath, fileextension=""):
    '''
    returns a count of the number of files, with optional limitation for extension
    '''
    files = [x for x in os.listdir(directorypath) if os.path.isfile(os.path.join(directorypath, x))]
    # ignore Thumbs.db
    if 'Thumbs.db' in files:
        files.remove('Thumbs.db')
    if fileextension:
        files = [x for x in files if os.path.splitext(x)[1] == fileextension]
    return len(files)

def file_list(directorypath, extensions=False):
    '''
    returns a list of file names, with extension optional
    '''
    files = sorted([x for x in os.listdir(directorypath) if os.path.isfile(os.path.join(directorypath, x))])
    # ignore Thumbs.db
    if 'Thumbs.db' in files:
        files.remove('Thumbs.db')
    if extensions:
        return files
    else:
        return [os.path.splitext(x)[0] for x in files]
    
def unique_extensions(directorypath):
    '''
    returns a list of unique extensions within directory
    '''
    # get list of files
    files = [x for x in os.listdir(directorypath) if os.path.isfile(os.path.join(directorypath, x))]
    # ignore Thumbs.db
    if 'Thumbs.db' in files:
        files.remove('Thumbs.db')
    # reduce to only the extension
    extensions = [os.path.splitext(x)[1] for x in files]
    # get unique in list
    extensions = _ConvertData.unique_in_list(extensions)
    return extensions
    
def subdirectories_list(directorypath):
    return sorted([x for x in os.listdir(directorypath) if os.path.isdir(os.path.join(directorypath, x))])

def subdirectories_count(directorypath):
    return len(subdirectories_list(directorypath))