"""
Metadata extraction from files
"""

import os
from pypdf import PdfReader
import aspace_wb.utils.default_specs as c

try:
    import mutagen
    import mutagen.id3
except ImportError:
    mutagen = None
try:
    import moviepy.editor as mv
except ImportError:
    mv = None


def unix_time_created(filepath):
    """
    returns the lowest of created, modified, accessed
    hopefully one of these would be the date the digital file is created, but it needs human validation
    """
    unix = min(
        os.path.getctime(filepath),
        os.path.getmtime(filepath),
        os.path.getatime(filepath),
    )
    return int(unix)


def audio_duration_seconds(filepath):
    """
    returns the duration in seconds of an audio file (which formats?)
    """
    file = mutagen.File(filepath)
    length = file.info.length
    return int(length)


def count_pdf_pages(filepath):
    """
    Returns number of pages in a PDF
    """
    with open(filepath, 'rb') as file:
        reader = PdfReader(file)
        return len(reader.pages)


def video_duration_seconds(filepath):
    """
    returns the duration in seconds of a video file (which formats?)
    """
    video = mv.VideoFileClip(filepath)
    duration = int(video.duration)
    # have to explicitly close VideoFileClip to avoid error "[WinError 6] The handle is invalid"
    # see https://github.com/Zulko/moviepy/issues/823
    video.close()
    return duration


def file_name(filepath):
    return os.path.splitext(filepath)[0]


def file_extension(filepath):
    return os.path.splitext(filepath)[1]


def construct_output_filename(orig_name, extension, script):
    """
    construct an appropriate name for files output by wb-fillable, wb-to-wb, or wb-create-dos
    appends script name (e.g. _wb-fillable), plus a counter (e.g. _2) if this will cause an existing file to be overwritten
    """
    
    # if this is running on output from wb-fillable, strip that from the file name so we don't end up with a file named _wb-fillable_wb-to-wb
    if "_wb-fillable" in orig_name and orig_name != "_wb-fillable":
        orig_name = orig_name.replace("_wb-fillable", "")
        
    new_name = f"{orig_name}_{script}"
    filepath = os.path.join(c.METADATA_DIR, f"{new_name}{extension}")
    
    while os.path.exists(filepath):
        name_split = new_name.split("_")
        # check that num < 20 as a rough heuristic to avoid changing numbers in file names that end with _{date} or _{node}
        if name_split[-1].isdigit() and int(name_split[-1]) < 20:
            counter = int(name_split[-1]) + 1
            new_name = f"{'_'.join(name_split[:-1])}_{counter}"
        else:
            new_name += "_2"
            
        filepath = os.path.join(c.METADATA_DIR, f"{new_name}{extension}")
    
    return f"{new_name}{extension}"


def audio_id3_tags(filepath):
    """
    dump list of audio tags
    can be used for debugging or analyzing files
    """
    tags = mutagen.id3.ID3(filepath)
    return tags
