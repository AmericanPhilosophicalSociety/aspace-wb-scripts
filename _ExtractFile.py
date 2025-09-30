# metadata extraction from files

import os
import re
import mutagen
import mutagen.id3
import moviepy.editor as mv

def unix_time_created(filepath):
    '''
    returns the lowest of created, modified, accessed
    hopefully one of these would be the date the digital file is created, but it needs human validation
    '''
    unix = min(os.path.getctime(filepath), os.path.getmtime(filepath), os.path.getatime(filepath))
    return int(unix)
    
def audio_duration_seconds(filepath):
    '''
    returns the duration in seconds of an audio file (which formats?)
    '''
    file = mutagen.File(filepath)
    length = file.info.length
    return int(length)

def pdf_page_count(filepath):
    '''
    not yet coded but a good idea once we start ingesting PDFs
    '''
    pass
    
def video_duration_seconds(filepath):
    '''
    returns the duration in seconds of a video file (which formats?)
    '''
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

def audio_id3_tags(filepath):
    '''
    dump list of audio tags
    can be used for debugging or analyzing files
    '''
    tags = mutagen.id3.ID3(filepath)
    return tags