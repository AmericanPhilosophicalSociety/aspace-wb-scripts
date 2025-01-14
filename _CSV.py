# utilities for manipulating CSV files

import pandas

def CSVToPandasDF(filepath, header=None):
    # get a CSV and load it into a Pandas DataFrame
    if not header:
        return pandas.read_csv(filepath, header=None)
    else:
        return pandas.read_csv(filepath)
    
def CSVColToList(filepath, col):
    fullCSV = pandas.read_csv(filepath, header=None)
    colList = fullCSV[col].tolist()
    return colList
    
def ValueInCSVCol(filepath, col, valueToCheck):
    # checks if a value is in the column specified, returns True if so
    fullCSV = pandas.read_csv(filepath, header=None)
    colList = fullCSV[col].tolist()
    if valueToCheck in colList:
        return True
    else:
        return False
    
def NeighborFromValueInCSVCol(filepath, valueToCheck, colToCheck, colToOutput):
    # finds value in first designated column. returns value from second designated column.
    fullCSV = pandas.read_csv(filepath, header=None)
    colToCheckList = fullCSV[colToCheck].tolist()
    colToOutputList = fullCSV[colToOutput].tolist()
    # use index to find the index where the value is, and return 
    return colToOutputList[colToCheckList.index(valueToCheck)]

def TwoColumnCSVToDict(filepath):
    # takes a two-column CSV and converts it to a dictionary of key:value pairs
    # if the CSV has more than two columns it just does the first two
    fullCSV = pandas.read_csv(filepath, header=None)
    col1 = fullCSV[0].tolist()
    col2 = fullCSV[1].tolist()
    output = {}
    for i in range(len(col1)):
        output[col1[i]] = col2[i]
    return output

def TuplesToCSV(tuples, outputFilename):
    # from a list of tuples, output a CSV file
    # no index and no header
    # get number of columns
    cols = len(tuples[0])
    # create a dictionary from the tuples, with generic header 0 onwards
    dataDict = {}
    for i in range(cols):
        colList = [x[i] for x in tuples]
        dataDict.update({str(i): colList})
    print(dataDict)
    # create a DataFrame, the dictionary that Pandas uses to store its data
    pandasDataFrame = pandas.DataFrame(dataDict)
    # save the csv
    pandasDataFrame.to_csv(str(outputFilename), index=False, header=False)

def DictToCSV(dictionary, outputFilename, header=1):
    # from a dictionary, get a CSV
    # no index
    # header=1 gets header from dictionary key. header=None has no header
    pandasDataFrame = pandas.DataFrame(dictionary)
    pandasDataFrame.to_csv(str(outputFilename), index=False, header=header)