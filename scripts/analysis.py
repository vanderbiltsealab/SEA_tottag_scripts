import os
import sys
from sortedcontainers import SortedDict

OUT_OF_RANGE_CODE = 999999

DATAFILE = "03_SS_20210109.LOG"

mDict = {}
with open(DATAFILE) as f:
    tag = f.readline()
    header = tag
    if tag.strip():  # strip will remove all leading and trailing whitespace such as '\n' or ' ' by default
        tag = tag.strip("\n ' '")
        tag = tag.split()[6].split(',')[0]
    sd = SortedDict()
    for line in f:
        if line[0] != '#':
            tokens = line.split('\t')
            if int(tokens[2]) != OUT_OF_RANGE_CODE :
                if float(tokens[2]) <= 3.0:
                    nTag = tokens[1]
                    if nTag not in mDict:
                        mDict[nTag] = [(tokens[0], tokens[2])]
                    else:
                        mDict[nTag].append((tokens[0], tokens[2]))
print(mDict)



