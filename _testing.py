import os
import _ExtractFile, _ExtractDir, _ConvertData, _Validate, _CSV
'''
tags = ExtractFile.AudioTags("test.mp3")
for k, v in tags.items():
    print(k, v)
print(
    Validate.ISO639_name("donghat")
)'''
'''
testing WriteAudioTags function:

tagsDict = {
    "COMM": "housed at the APS in Philadelphia",
    "TALB": "Mss.Rec.29 Tlingit Songs",
    "TDRC": "1953",
    "TIT2": "01-02 The recording number 2 is this one",
    "TPE1": "De Laguna, Frederica, some of it"
}

WriteFile.WriteAudioTags("test.mp3", tagsDict)

# then check it worked

print(ExtractFile.AudioTags("test.mp3"))
'''
'''
testDict = {
    'bread': [0,1,2],
    'cheesebread': [3,4,5],
    '3': [4,None,4],
    '4': [5,5,5]
}

_CSV.DictToCSV(testDict, "test1.csv")'''
'''
a = "2020-02-03"
b = "1985-04-12T23:20:30"

print(_Validate.EDTFLevel0Date(a))
print(_Validate.EDTFLevel0Date(b))'''
'''
a = ['soup1', float('nan'), float('nan'), float('nan'), float('nan')]

print(_Validate.ListIsSingleValueThenNaN(a))
'''
'''a = "egg|ham|leg"
b = "a|b|c"
c = "a|b|c|d"

print(_Validate.PipedFieldsSameLength(a, b))
print(_Validate.PipedFieldsSameLength(a, c))'''
'''
input = [[None, 'samdwich', 0, 'queinch'], ['sanrd', None, 'sandfbm', 'auqquuiiiiench']]
print(_ConvertData.ConcatenateStringsInLists(input))'''

'''
filepath = "C:\\Users\\psutherland\\Documents\\Guise local copy\\"
files = _ExtractDir.FileList(filepath, extensions=True)
for file in files:
    print(file)
files = [filepath + x for x in files]
extents = [_ExtractFile.VideoDurationSeconds(y) for y in files]
hhmmss = [_ConvertData.SecondsToHHMMSS(z) for z in extents]
for stamp in hhmmss:
    print(stamp)
'''
'''
filepath = "C:\\Users\\psutherland\\Documents\\Guise local copy\\APS_MssSMsColl47_Wright-2022-08-03_2.mov"
extent = _ExtractFile.VideoDurationSeconds(filepath)
hhmmss = _ConvertData.SecondsToHHMMSS(extent)
print(extent, hhmmss)'''
'''
fileDir = "\\\\cnair01\\CNAIR\\Digitized\\audio\\CNAIR Audio - GeorgeBlood_2024-01\\Silverstein working copies\\test"
a = _ExtractDir.FileList(fileDir, extensions=True)[0]
print(_ExtractFile.AudioDurationSeconds(os.path.join(fileDir,a)))'''
'''
print(_ConvertData.ASDateToWBDate("2014-2015", "", ""))
print(_ConvertData.ASDateToWBDate("2014", "2014", "2014"))
print(_ConvertData.ASDateToWBDate("", "2014", "2015"))
print(_ConvertData.ASDateToWBDate("2014-2015", "2014", "2015"))
print(_ConvertData.ASDateToWBDate("n.d.", "", ""))'''
