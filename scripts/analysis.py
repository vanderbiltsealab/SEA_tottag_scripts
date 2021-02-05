import os
import sys
from sortedcontainers import SortedDict

OUT_OF_RANGE_CODE = 999999

# DATAFILE = "03_SS_20210109.LOG"
# a more robust version of the above line would be to accept an argument as the
# log file as shown below
DATAFILE = sys.argv[1] # argv is the array of command line arguments after 'python3'
# starting at index 0

insideDict = {}
outsideDict = {}
with open(DATAFILE) as f:
    tag = f.readline()
    header = tag
    if tag.strip():  # strip will remove all leading and trailing whitespace such as '\n' or ' ' by default
        tag = tag.strip("\n ' '")
        print('this is header', tag)
        totTagID = tag.split()[6].split(',')[0]
        # date = tag.split()[8].split(',')[0]
        #  timeOfDate = tag.split()[9].split(',')[0]
        # timeStamp = tag.split()[11].split(',')[0]
        # format is tag.split()[7th thing separated by spaces].split(',')[from 0th column of string til next ',']
        # .split() documentation: https://python-reference.readthedocs.io/en/latest/docs/str/split.html

        ### print statements used for understanding split ###
        # print('this is totTagID after tag.split()[6].split(',')[0]:', totTagID)
        # print('this is date after tag.split()[8].split(',')[0]:', date)
        # print('this is timeOfDate after tag.split()[9].split(',')[0]:', timeOfDate)
        # print('this is timeStamp after tag.split()[11].split(',')[0]:', timeStamp)

    sd = SortedDict()
    # documentation on sortedContainers: http://www.grantjenks.com/docs/sortedcontainers/
    for line in f:
        if line[0] != '#':
            tokens = line.split('\t')
            # print(tokens) # this is a list of [timeStamp1, totTagID1, distance1],...
            # ...[timeStampN, totTagIDN, distanceN]

            # the time stamp here is in seconds!
            # 1604574620 is Thursday, November 5, 2020 11:10:21AM

            # print(tokens[2]) # this is column array of timeStamps

            if int(tokens[2]) != OUT_OF_RANGE_CODE:
                # if float(tokens[2]) <= 3.0: # this is checking is tokens[2] is <= 3mm
                # should be 914.4 (=3 ft), but lets make it 915.
                # type should be int as well, better not to introduce rounding error of any kind
                if int(tokens[2]) <= 915:
                    # nTag = tokens[1] # nTag is a column array of totTagIDs

                    timeStampinCheckInRange = tokens[0] # this column array is 1:1
                    # correspondence with inCheckInRange

                    totTagIDinCheckInRange = tokens[1]

                    distanceInCheckInRange = tokens[2] # assuming operations are matrix-wise,
                    # this should give us token totTagIDs exclusively inside 3ft
                    # above line of code DOES give us column exclusively inside 3ft.

                    # if nTag not in mDict: # if totTagID Column array not in mDict,
                    if totTagIDinCheckInRange not in insideDict:
                    # for key nTag set value to [timeStamp, distance] or if its
                    # in mDict append value [timeStamp, distance]
                        # mDict[nTag] = [(tokens[0], tokens[2])]
                        insideDict[totTagIDinCheckInRange] = [(timeStampinCheckInRange,
                                                               distanceInCheckInRange)]
                    else:
                        # mDict[nTag].append((tokens[0], tokens[2]))
                        # mDict[inCheckInRange[1]].append((inCheckInRange[0], inCheckInRange[2]))
                        insideDict[totTagIDinCheckInRange].append((timeStampinCheckInRange,
                                                                   distanceInCheckInRange))
                else:
                    timeStampOutCheckInRange = tokens[0]
                    totTagIDOutCheckInRange = tokens[1]
                    distanceOutCheckInRange = tokens[2]
                    # print('this is outCheckInRange', outCheckInRange) ## works as
                    # intended

                    # next step is to differentiate them by timeStamp since they
                    # are unique!


filtered = {}
for key in insideDict:
    index = 0
    # loop through array of tuples for current device
    while index in range(len(insideDict[key])):
        # let t be the current timestamp
        t = int(insideDict[key][index][0])
        # keep count of consecutive timestamps in the array
        count = 1
        # keep a tmp variable for timestamp
        tmpT = t
        # while index haven't reached the end of array && next timestamp is in the array
        # (loop through consecutive timestamps)
        while index != len(insideDict[key])-1 \
                and (tmpT + 1) == (int)(insideDict[key][index+1][0]):
            # increment count, index and tmpT
            count = count + 1
            index = index + 1
            tmpT = tmpT + 1
        # if device is within range for at least 2 seconds
        if count >= 2:
            # add this timestamp to a dictionary of filtered inRange timestamps
            if key not in filtered:
                filtered[key] = [t]
            else:
                filtered[key].append(t)
        # go to next index location after the previous consecutive group of timestamps
        index = index + 1


# print out dictionary for checking ...
# for key in filtered:
#    print(str(key))
#    for index in range(len(filtered[key])):
#        print("\t" + str(filtered[key][index]))

# print(mDict.get("c0:98:e5:42:01:05"))
# print(mDict.get("c0:98:e5:42:01:06"))

# turns out from files below that logic i wrote only gives singular entries

# file1 = open('inCheckInRange.txt', 'w')
# # file2 = open('outCheckInRange.txt', 'w')
# #
# file1.writelines(insideDict)
# # file2.writelines(outCheckInRange)
# #
# file1.close()
# file2.close()

# print(mDict)