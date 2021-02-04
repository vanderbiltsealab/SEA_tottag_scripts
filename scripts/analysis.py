import os
import sys
from sortedcontainers import SortedDict
OUT_OF_RANGE_CODE = 999999
DATAFILE = "03_SS_20210109.LOG"

mDict = {}
inRange = 3 / 0.003281
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
            if int(tokens[2]) != OUT_OF_RANGE_CODE:
                # dist = float(tokens[2]) * 0.003281
                if float(tokens[2]) <= float(inRange):
                    nTag = tokens[1]
                    if nTag not in mDict:
                        mDict[nTag] = [(tokens[0], tokens[2])]
                    else:
                        mDict[nTag].append((tokens[0], tokens[2]))
#for key in mDict:
#    print(str(key))
#    for index in range(len(mDict[key])):
#       print("\t" + str(mDict[key][index]))

nDict = {}
for key in mDict:
    index = 0
    while index in range(len(mDict[key])):
        t = int(mDict[key][index][0])
        count = 1
        tmpT = t
        while index != len(mDict[key])-1 and (int)(tmpT + 1) == (int)(mDict[key][index+1][0]):
            count = count + 1
            index = index + 1
            tmpT = tmpT + 1
        if count >= 2:
            if key not in nDict:
                nDict[key] = [t]
            else:
                nDict[key].append(t)
        index = index + 1

for key in nDict:
    print(str(key))
    for index in range(len(nDict[key])):
        print("\t" + str(nDict[key][index]))
