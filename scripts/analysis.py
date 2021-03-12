import os
import sys
import pandas as pd
from sortedcontainers import SortedDict
# documentation on sortedContainers: http://www.grantjenks.com/docs/sortedcontainers/
# some variables
OUT_OF_RANGE_CODE = 999999
inRangeDist = 915  # 3ft = 915mm
#x = 2

# argv is the array of command line arguments after 'python3' starting at index 0
# the command line argument would be "python analysis.py DATAFILE INTEGER"
# x is used for step2 where we determine a interval of x seconds before and after the checkin
#DATAFILE = sys.argv[1]
#x = int(sys.argv[2])

# ************************************************************************ #
# ------ Step1-1: filter out timestamps where proximity is within 3ft ------ #
# ************************************************************************ #

# mDict: key of mDict is pair of device tags, where tag1 is the tag of the device of the current log
# file; values associated with each key is an array of tuples that looks like: (timestamp, )
mDict = {}
# this is just for my own convenience
logFiles = ["03_SS_20210109.LOG", "06_ZS_20210109.LOG", "07_VS_20210109.LOG"]
for script in logFiles:
    with open(script) as f:
        # the following string operation gets the ID for the current device
        tag = f.readline()
        header = tag
        if tag.strip():  # strip will remove all leading and trailing whitespace such as '\n' or ' ' by default
            tag = tag.strip("\n ' '")
            totTagID = tag.split()[6].split(',')[0]
            print("tottagID: " + totTagID)
        # start going through each line of the log file and separate in range and out of range data
        for line in f:
            # if line is not a comment
            if line[0] != '#':
                # tokens is a list where tokens[0] is timestamp, tokens[1] is device ID, and tokens[2] is measurement
                tokens = line.split('\t')
                # check for out of range code
                if int(tokens[2]) != OUT_OF_RANGE_CODE:
                    # if proximity is within range (3ft/915mm)
                    if int(tokens[2]) <= inRangeDist:
                        # if this device is not added as a key to the dictionary yet, create an array for this device
                        # and add in the tuple of (timestamp, distance);
                        # otherwise, append the tuple to the end of the array
                        mDict.setdefault((tokens[1], totTagID), []).append((tokens[0], int(tokens[2]), True))
                    # same as above;
                    else:
                        mDict.setdefault((tokens[1], totTagID), []).append((tokens[0], int(tokens[2]), False))


# ********************************************************************************************* #
# ------ Step1-2: filter out timestamps where proximity is within range for over 2 seconds ------ #
# ********************************************************************************************* #
for key in mDict:
    index = 0
    # loop through array of tuples for current device
    check_num = 0
    while index in range(len(mDict[key])):
        # if data is within 3ft
        if mDict[key][index][2]:
            # let t be the current timestamp
            t = int(mDict[key][index][0])
            # keep count of consecutive timestamps in the array
            count = 1
            # keep a tmp variable for timestamp
            tmpT = t
            i = index
            # while index haven't reached the end of array && next timestamp is in the array
            # (loop through consecutive timestamps)
            first = True
            addToBeginning = False
            checknumUpdate = False
            # go through consecutive series of in range data
            while mDict[key][index][2] and index != len(mDict[key]) - 1 \
                    and (tmpT + 1) == int(mDict[key][index + 1][0]):
                # if this is the first timestamp in the consecutive series
                if first:
                    trackBeginning = i
                    first = False
                # if in range for over 2 seconds (count >= 2)
                if count >= 2:
                    # update check_num for each checkin
                    if not checknumUpdate:
                        check_num = check_num + 1
                        checknumUpdate = True
                    # append check_num to original array
                    mDict[key][index] = mDict[key][index] + (check_num, )
                    # this is appending check_num to the first timestamp in the sequence
                    if not addToBeginning:
                        mDict[key][trackBeginning] = mDict[key][trackBeginning] + (check_num, )
                        addToBeginning = True
                # increment by 1
                count = count + 1
                index = index + 1
                tmpT = tmpT + 1
            index = index + 1
        # if not in checkin range, just go to next index
        else:
            index = index + 1


# printing dictionary to output file just for checking
outfile1 = "out1"
s1 = open(outfile1, "w+")
# print out dictionary for checking ...
for key in mDict:
    s1.write(str(key) + "\n")
    for index in range(len(mDict[key])):
        s1.write("\t" + str(mDict[key][index]) + "\n")


# create a sorted dictionary where the keys are (timestamp, device) and values are arrays of
# [distance, within 3ft or not, check_num(if constitute checkin)]
sd = SortedDict()
for key in mDict:
    for index in range(len(mDict[key])):
        if len(mDict[key][index]) == 3:
            sd.setdefault((mDict[key][index][0], key[0]), []).\
                append((key[1], mDict[key][index][1]))
        if len(mDict[key][index]) == 4:
            sd.setdefault((mDict[key][index][0], key[0]), []).\
                append((key[1], mDict[key][index][1], mDict[key][index][3]))


# printing dictionary to output file just for checking
outfile2 = "out2"
s2 = open(outfile2, "w+")
# print out dictionary for checking ...
for key in mDict:
    s2.write(str(key) + "\n")
    for index in range(len(mDict[key])):
        s2.write("\t" + str(mDict[key][index]) + "\n")


# TODO: Processing Motions Data Here!
# create sorted dict sdMotion for motion data where the key is (timestamp, main device),
# and value is motion value
sdMotion = SortedDict()
# here's a list of names of the motions data file from Amanda's scripts
listFiles = ["06_motions.csv", "03_motions.csv", "07_motions.csv"]
for scripts in listFiles:
    with open(scripts) as m:
        for line in m:
            # split line by comma
            tokens = line.split(",")
            time = tokens[0]
            motion = tokens[1]
            device = (tokens[2].split("\n"))[0]
            # this is adding the key (time, device) to the dictionary if this key did not exist before,
            # and if the key already exist, it will append the motions data to the end of the array
            sdMotion.setdefault((time, device), []).append(motion)


# convert dictionaries to Pandas DataFrame,
# can print out the data frames to see what they look like
df1 = pd.DataFrame(list(sd.items()), columns=['key', 'data'])
df2 = pd.DataFrame(list(sdMotion.items()), columns=['key', 'data'])
# merge data on key - add in motions data if df1 and df2 has the same value in the 'key' column
df = pd.merge(df1, df2, on=['key'])
# this is printing the merged data frame to output file
tfile = open('test.txt', 'w+')
tfile.write(df.to_string())
tfile.close()


