'''
utilities for manipulating CSV files
some of these might be unused
'''

import pandas

def CSV_to_pandas_dataframe(filepath, header=None):
    # get a CSV and load it into a Pandas DataFrame
    if not header:
        return pandas.read_csv(filepath, header=None)
    else:
        return pandas.read_csv(filepath)
    
def CSV_col_to_list(filepath, col):
    '''
    converts a numbered column (0-) of a csv to a list
    '''
    fullCSV = pandas.read_csv(filepath, header=None, skip_blank_lines=False)
    colList = fullCSV[col].tolist()
    return colList
    
def value_in_csv_col(filepath, col, valueToCheck):
    # checks if a value is in the column specified, returns True if so
    fullCSV = pandas.read_csv(filepath, header=None)
    colList = fullCSV[col].tolist()
    if valueToCheck in colList:
        return True
    else:
        return False
    
def neighbor_from_value_in_CSV_col(filepath, valueToCheck, colToCheck, colToOutput):
    '''
    finds value in first designated column. returns value from second designated column.
    '''
    fullCSV = pandas.read_csv(filepath, header=None)
    colToCheckList = fullCSV[colToCheck].tolist()
    colToOutputList = fullCSV[colToOutput].tolist()
    # use index to find the index where the value is, and return 
    return colToOutputList[colToCheckList.index(valueToCheck)]

def two_col_CSV_to_dict(filepath):
    '''
    takes a two-column CSV and converts it to a dictionary of key:value pairs
    if the CSV has more than two columns it just does the first two
    '''
    full_CSV = pandas.read_csv(filepath, header=None)
    col1 = full_CSV[0].tolist()
    col2 = full_CSV[1].tolist()
    output = {}
    for i in range(len(col1)):
        output[col1[i]] = col2[i]
    return output

def tuples_to_CSV(tuples, outputFilename):
    '''
    from a list of tuples, output a CSV file
    no index and no header
    '''
    # get number of columns
    cols = len(tuples[0])
    # create a dictionary from the tuples, with generic header 0 onwards
    dataDict = {}
    for i in range(cols):
        colList = [x[i] for x in tuples]
        dataDict.update({str(i): colList})
    print(dataDict)
    # create a DataFrame, the dictionary that Pandas uses to store its data
    pandas_dataframe = pandas.DataFrame(dataDict)
    # save the csv
    pandas_dataframe.to_csv(str(outputFilename), index=False, header=False)

def dict_to_CSV(dictionary, outputFilename, header=1):
    '''
    from a dictionary, get a CSV
    no index
    header=1 gets header from dictionary key. header=None has no header
    '''
    pandas_dataframe = pandas.DataFrame(dictionary)
    pandas_dataframe.to_csv(str(outputFilename), index=False, header=header)