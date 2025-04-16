'''
script to take a CSV of titles and refids
and output this with a column of located agents
this is for formulating titles with agents before
'''

import _ConvertData, _CSV
import sys
import os

print('Expects as first argument: name of CSV (with extension) with first column titles, second column refids.')
CSV = sys.argv[1] # file located in same directory
titles = _CSV.CSVColToList(CSV, 0)
refs = _CSV.CSVColToList(CSV, 1)

agents = [_ConvertData.AgentsFromASAO(refs[i], titles[i]) for i in range(len(titles))]
agents = ['|'.join(x) for x in agents]

outputDict = {
    'titles': titles,
    'refs': refs,
    'agents': agents
}

outputFilename = os.path.splitext(CSV)[0] + "_AGENTS.csv"

_CSV.DictToCSV(outputDict, outputFilename)

print('Exported as: ' + outputFilename)