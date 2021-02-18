import os
import sys
from sortedcontainers import SortedDict
# documentation on sortedContainers: http://www.grantjenks.com/docs/sortedcontainers/

# some variables
OUT_OF_RANGE_CODE = 999999
DATAFILE = "03_SS_20210109.LOG"
inRangeDist = 915  # 3ft = 915mm
x = 2

# argv is the array of command line arguments after 'python3' starting at index 0
# DATAFILE = sys.argv[1]
# x = sys.argv[2]

# ************************************************************************ #
# ------ Step1-1: filter out timestamps where proximity is within 3ft ------ #
# ************************************************************************ #

# insideDict and outsideDict are both dictionaries of arrays of tuples. Each key in both
# dictionaries are device tags, and each key is associated with an array of tuples.
# Each tuple is a pair of values where the first value is the timestamp where proximity
# is within(for insideDict) or outside(for outsideDict) 3ft, and the second value is the
# actual proximity data
insideDict = {}
outsideDict = {}
with open(DATAFILE) as f:
    # the following string operation gets the ID for the current device
    tag = f.readline()
    header = tag
    if tag.strip():  # strip will remove all leading and trailing whitespace such as '\n' or ' ' by default
        tag = tag.strip("\n ' '")
        totTagID = tag.split()[6].split(',')[0]
        print("tottagID: " + totTagID)
        # date = tag.split()[8].split(',')[0]
        # timeOfDate = tag.split()[9].split(',')[0]
        # timeStamp = tag.split()[11].split(',')[0]
        # format is tag.split()[7th thing separated by spaces].split(',')[from 0th column of string til next ',']
        # .split() documentation: https://python-reference.readthedocs.io/en/latest/docs/str/split.html

        # print statements used for understanding split ###
        # print('this is totTagID after tag.split()[6].split(',')[0]:', totTagID)
        # print('this is date after tag.split()[8].split(',')[0]:', date)
        # print('this is timeOfDate after tag.split()[9].split(',')[0]:', timeOfDate)
        # print('this is timeStamp after tag.split()[11].split(',')[0]:', timeStamp)
    # start going through each line of the log file and separate in range and out of range data
    for line in f:
        # if line is not a comment
        if line[0] != '#':
            # tokens is a list where tokens[0] is timestamp, tokens[1] is device ID, and tokens[2] is measurement
            tokens = line.split('\t')

            # the time stamp here is in seconds!
            # 1604574620 is Thursday, November 5, 2020 11:10:21AM

            # check for out of range code
            if int(tokens[2]) != OUT_OF_RANGE_CODE:
                # if proximity is within range (3ft/915mm)
                if int(tokens[2]) <= inRangeDist:
                    timeStampInCheckInRange = tokens[0]
                    totTagIDInCheckInRange = tokens[1]
                    distanceInCheckInRange = int(tokens[2])

                    # if this device is not added as a key to the dictionary yet, create an array for this device
                    # and add in the tuple of (timestamp, distance); otherwise, append the tuple to the end of the array
                    if totTagIDInCheckInRange not in insideDict:
                        insideDict[totTagIDInCheckInRange] = [(timeStampInCheckInRange, distanceInCheckInRange)]
                    else:
                        insideDict[totTagIDInCheckInRange].append((timeStampInCheckInRange, distanceInCheckInRange))
                # same as above; adding keys and tuples to outsideDict
                else:
                    if tokens[1] not in outsideDict:
                        outsideDict[tokens[1]] = [(tokens[0], int(tokens[2]))]
                    else:
                        outsideDict[tokens[1]].append((tokens[0], int(tokens[2])))

#for key in insideDict:
    #print(str(key))
    #for index in range(len(insideDict[key])):
        #print("\t" + str(insideDict[key][index]))
# ********************************************************************************************* #
# ------ Step1-2: filter out timestamps where proximity is within range for over 2 seconds ------ #
# ********************************************************************************************* #

# filtered is a dictionary of arrays of tuples. The keys of the filtered dictionary
# is the device tags, and each tag is associated with an array of tuples where the first element in the tuple is the
# timestamp that counts as valid check-ins (within 3ft range for over 2 seconds), and the second element in the tuple
# is the proximity data at that check-in timestamp
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
        i = index
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
                filtered[key] = [(t, insideDict[key][i][1])]
            else:
                filtered[key].append((t, insideDict[key][i][1]))
        # go to next index location after the previous consecutive group of timestamps
        index = index + 1

# print out dictionary for checking ...
# for key in filtered:
#     print(str(key))
#     for index in range(len(filtered[key])):
#        print("\t" + str(filtered[key][index]))

# print out final result
print("Time\t\tTag\t\t\t\t\t\tProx(ft)\tCheck_Occur\tCheck_num")
for key in filtered:
    for index in range(len(filtered[key])):
        dist = float(0.00328 * filtered[key][index][1])
        print(str(filtered[key][index][0]) + "\t" + str(key) + "\t" + str("{:10.4f}".format(dist)) + "\t\t1\t\t\t" + str(index+1))
        # print(str(filtered[key][index][0]) + "\t" + str(key) + "\t" + str(filtered[key][index][1]) + "\t\t1\t\t\t" + str(index+1))

# *********************************************************************************** #
# ------ Step2: get a list of time range of x seconds before and after checkin ------ #
# *********************************************************************************** #

# x = 2 # test

# sec is a dictionary of arrays of tuples; each key is the tag of a device, and
# each key maps to an array of tuples that represents a range of x seconds before
# a checkin and x seconds after the checkin, i.e. (timestamp - x, timestamp + x)
sec = {}
# go through the filtered dictionary and append tuples to the array
for key in filtered:
    for index in range(len(filtered[key])):
        timestamp = int(filtered[key][index][0])
        checkinRange = (timestamp - x, timestamp + x)
        if key not in sec:
            sec[key] = [checkinRange]
        else:
            sec[key].append(checkinRange)

# print out dictionary for checking ...
# for key in sec:
#    print(str(key))
#    for index in range(len(sec[key])):
#        print("\t" + str(sec[key][index]))


# turns out from files below that logic i wrote only gives singular entries

# file1 = open('inCheckInRange.txt', 'w')
# # file2 = open('outCheckInRange.txt', 'w')
# #
# file1.writelines(insideDict)
# # file2.writelines(outCheckInRange)
# #
# file1.close()
# file2.close()
