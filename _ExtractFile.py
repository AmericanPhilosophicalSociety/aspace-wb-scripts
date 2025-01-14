# metadata extraction from files

import os
import re
import mutagen
import mutagen.id3
import moviepy.editor as mv

def DateCreatedUnix(filepath):
    # returning the lowest of created and modified
    # hopefully one of these would be the date the digital file is created, but it needs human validation
    unix = min(os.path.getctime(filepath), os.path.getmtime(filepath))
    return int(unix)
    
def AudioDurationSeconds(filepath):
    file = mutagen.File(filepath)
    length = file.info.length
    return int(length)

def PDFPageCount(filepath):
    # not yet coded
    return
    
def VideoDurationSeconds(filepath):
    video = mv.VideoFileClip(filepath)
    duration = int(video.duration)
    # have to explicitly close VideoFileClip to avoid error "[WinError 6] The handle is invalid"
    # see https://github.com/Zulko/moviepy/issues/823 
    video.close()
    return duration
    
def FileName(filepath):
    return os.path.splitext(filepath)[0]

def FileType(filepath):
    # outputs type with .
    return os.path.splitext(filepath)[1]

def AudioTags(filepath):
    # dump list of audio tags
    tags = mutagen.id3.ID3(filepath)
    return tags

# this is now no longer necessary - configuring all Recording, Program numbers as just a unique identifier
def AudioRecordingNumberProgramNumber(filepath):
    last5 = FileName(filepath)[-5:]
    # check that last 5 follows correct format, otherwise return error
    if not re.match("[0-9][0-9]\-[0-9][0-9]", last5):
        raise ValueError("file does not end in format: digit digit hyphen digit digit")
    return (last5[:2], last5[-2:])