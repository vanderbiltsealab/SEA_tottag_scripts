import os
import sys
import pandas as pd
from sortedcontainers import SortedDict
# documentation on sortedContainers: http://www.grantjenks.com/docs/sortedcontainers/
# some variables
OUT_OF_RANGE_CODE = 999999
inRangeDist = 915  # 3ft = 915mm
# x = 2

# argv is the array of command line arguments after 'python3' starting at index 0
# the command line argument would be "python analysis.py DATAFILE INTEGER"
# x is used for step2 where we determine a interval of x seconds before and after the checkin
# DATAFILE = sys.argv[1]
# x = int(sys.argv[2])


# a list of the three log files that we are currently using
logFiles = ["03_SS_20210109.LOG", "06_ZS_20210109.LOG", "07_VS_20210109.LOG"]

# this is currently useless
def process_all1(log_files):
    # mDict: key of mDict is tuple that looks like (), where tag1 is the tag of the device of the current log
    # file; values associated with each key is an array of tuples that looks like: (timestamp, )
    mDict = {}
    idList = []
    for script in log_files:
        with open(script) as f:
            # the following string operation gets the ID for the current device
            tag = f.readline()
            header = tag
            if tag.strip():  # strip will remove all leading and trailing whitespace such as '\n' or ' ' by default
                tag = tag.strip("\n ' '")
                totTagID = tag.split()[6].split(',')[0]
                print("tottagID: " + totTagID)
                # add this device tag to the idList
                idList.append(totTagID)
            # start going through each line of the log file and separate in range and out of range data
            for line in f:
                # if line is not a comment
                if line[0] != '#':
                    # tokens is a list where tokens[0] is timestamp, tokens[1] is device ID, and tokens[2] is measurement
                    # the list is obtained by calling the split function on the string, in this case the function will split
                    # line based on tabs
                    tokens = line.split('\t')
                    # check for out of range code (999999)
                    # if int(tokens[2]) != OUT_OF_RANGE_CODE:
                    # check to make sure that we haven't already processed this device
                    if tokens[1] not in idList:
                        # if proximity data is within check in range (3ft/915mm)
                        if int(tokens[2]) <= inRangeDist:
                            # use the setdefault function that initialize an array if the key has not yet been
                            # add into the dictionary, or append to the end of the array if the key already exists
                            # each key is associated with an array of tuples that has the form -
                            # (timestamp, distance, boolean value of whether in checkin range)
                            mDict.setdefault((tokens[1], totTagID), []).append((tokens[0], int(tokens[2]), True))
                            # same as above;
                        else:
                            mDict.setdefault((tokens[1], totTagID), []).append((tokens[0], int(tokens[2]), False))
    return mDict


# this is currently useless as well
def process_all2(mDict):
    # After filtering through the data for proximity data that is within checkin range, now we determine
    # the appropriate checkins
    for key in mDict:
        # this value keeps track where we are in the array associated with each key
        index = 0
        # this variable keeps count of valid checkins
        check_num = 0
        # loop through the array of tuples associated with each key in the dictionary
        while index in range(len(mDict[key])):
            # mDcit[key][index][2] is the boolean value in the tuple that indicates whether proximity data
            # is within 3 ft
            if mDict[key][index][2]:
                # below are some variables that will be used in the while loop; the while loop
                # will check for appropriate check-ins (within 3ft for over 2 seconds). if an checkin is
                # found, an additional element will be added to the original tuple for that timestamp
                # the additional element is the check-num that keeps count of the checkins that occurred between
                # each pair of device

                # let t be the timestamp value in the current tuple
                t = int(mDict[key][index][0])
                # keep count of consecutive timestamps in the array
                # this variable keeps count of the number of consecutive timestamps that have proximity
                # measurements within 3ft
                count = 1
                # keep a tmp variable for the current timestamp and index of the current tuple
                # tmpT = t
                i = index
                # first is a boolean value that indicates whether this timestamp is the start of the
                # checkin period (first timestamp in the series of consecutive timestamps)
                first = True
                # this boolean value keeps track of whether we have added the check-num value to the
                # tuple if a proper check-in is found
                addToBeginning = False
                # this boolean value indicates whether the count of proper checkins have been updated
                # (whether the check_num variable from above have been updated)
                checknumUpdate = False

                # here is the body of the while loop; we are checking 1. whether proximity is within 3ft;
                # 2. whether we are at the end of the list; 3. whether
                # mDict[key][index][2] is the boolean value that indicates whether proximity measurement is within
                # 3ft;
                while mDict[key][index][2] and index != len(mDict[key]) - 1:
                    # and (tmpT + 1) == int(mDict[key][index + 1][0]):
                    # if this is the first timestamp in the consecutive series, let the trackBeginning variable
                    # store the index of the start of this checkin period (the starting timestamp)
                    if first:
                        trackBeginning = i
                        first = False
                    # if in range for over 2 seconds (count >= 2)
                    if count >= 2:
                        # a checkin has occurred, and check_num needs to be updated by 1 if haven't already
                        if not checknumUpdate:
                            check_num = check_num + 1
                            checknumUpdate = True
                        # append check_num to original array
                        mDict[key][index] = mDict[key][index] + (check_num,)
                        # this is appending check_num to the first timestamp in the sequence (we did not append
                        # check_num to the first tuple of this checkin because count was 1 by then)
                        if not addToBeginning:
                            mDict[key][trackBeginning] = mDict[key][trackBeginning] + (check_num,)
                            addToBeginning = True
                    # increment by 1
                    count = count + 1
                    index = index + 1
                    # tmpT = tmpT + 1
                index = index + 1
            # if not in checkin range, just go to next index (next tuple)
            else:
                index = index + 1


# step 1 of processing log file - creating dictionaries with the tuple (device 2, device1) as key, key is associated
# with arrays of tuples that has the form (timestamp, proximity, within 2 ft or not(boolean value))
def process_single1(script):
    mDict = {}
    with open(script) as f:
        # the following string operation gets the ID for the current device
        tag = f.readline()
        header = tag
        if tag.strip():  # strip will remove all leading and trailing whitespace such as '\n' or ' ' by default
            tag = tag.strip("\n ' '")
            totTagID = tag.split()[6].split(',')[0]
        # start going through each line of the log file and separate in range and out of range data
        for line in f:
            # if line is not a comment
            if line[0] != '#':
                # tokens is a list where tokens[0] is timestamp, tokens[1] is device ID, and tokens[2] is measurement
                # the list is obtained by calling the split function on the string, in this case the function will split
                # line based on tabs
                tokens = line.split('\t')
                # check for out of range code (999999)
                # if int(tokens[2]) != OUT_OF_RANGE_CODE:
                # if proximity data is within check in range (3ft/915mm)
                if int(tokens[2]) <= inRangeDist:
                    # use the setdefault function that initialize an array if the key has not yet been
                    # add into the dictionary, or append to the end of the array if the key already exists
                    # each key is associated with an array of tuples that has the form -
                    # (timestamp, distance, boolean value of whether in checkin range)
                    mDict.setdefault((tokens[1], totTagID), []).append((tokens[0], int(tokens[2]), True))
                    # same as above;
                else:
                    mDict.setdefault((tokens[1], totTagID), []).append((tokens[0], int(tokens[2]), False))
    return mDict
    # device2 & device1 | timestamp & proximity & 2ft?


# step 2 of processing
def process_single2(mDict):
    # After filtering through the data for proximity data that is within checkin range, now we determine
    # the appropriate checkins
    for key in mDict:
        # this value keeps track where we are in the array associated with each key
        index = 0
        # this variable keeps count of valid checkins
        check_num = 0
        # loop through the array of tuples associated with each key in the dictionary
        while index in range(len(mDict[key])):
            # mDcit[key][index][2] is the boolean value in the tuple that indicates whether proximity data
            # is within 3 ft
            if mDict[key][index][2]:
                # below are some variables that will be used in the while loop; the while loop
                # will check for appropriate check-ins (within 3ft for over 2 seconds). if an checkin is
                # found, an additional element will be added to the original tuple for that timestamp
                # the additional element is the check-num that keeps count of the checkins that occurred between
                # each pair of device

                # let t be the timestamp value in the current tuple
                t = int(mDict[key][index][0])
                # keep count of consecutive timestamps in the array
                # this variable keeps count of the number of consecutive timestamps that have proximity
                # measurements within 3ft
                count = 1
                # keep a tmp variable for the current timestamp and index of the current tuple
                # tmpT = t
                i = index
                # first is a boolean value that indicates whether this timestamp is the start of the
                # checkin period (first timestamp in the series of consecutive timestamps)
                first = True
                # this boolean value keeps track of whether we have added the check-num value to the
                # tuple if a proper check-in is found
                addToBeginning = False
                # this boolean value indicates whether the count of proper checkins have been updated
                # (whether the check_num variable from above have been updated)
                checknumUpdate = False

                # here is the body of the while loop; we are checking 1. whether proximity is within 3ft;
                # 2. whether we are at the end of the list; 3. whether
                # mDict[key][index][2] is the boolean value that indicates whether proximity measurement is within
                # 3ft;
                while mDict[key][index][2] and index != len(mDict[key]) - 1:
                    # and (tmpT + 1) == int(mDict[key][index + 1][0]):
                    # if this is the first timestamp in the consecutive series, let the trackBeginning variable
                    # store the index of the start of this checkin period (the starting timestamp)
                    if first:
                        trackBeginning = i
                        first = False
                    # if in range for over 2 seconds (count >= 2)
                    if count >= 2:
                        # a checkin has occurred, and check_num needs to be updated by 1 if haven't already
                        if not checknumUpdate:
                            check_num = check_num + 1
                            checknumUpdate = True
                        # append check_num to original array
                        mDict[key][index] = mDict[key][index] + (check_num,)
                        # this is appending check_num to the first timestamp in the sequence (we did not append
                        # check_num to the first tuple of this checkin because count was 1 by then)
                        if not addToBeginning:
                            mDict[key][trackBeginning] = mDict[key][trackBeginning] + (check_num,)
                            addToBeginning = True
                    # increment by 1
                    count = count + 1
                    index = index + 1
                    # tmpT = tmpT + 1
                index = index + 1
            # if not in checkin range, just go to next index (next tuple)
            else:
                index = index + 1
    return mDict


def print_dict(dict):
    outfile = "mDict_check"
    s = open(outfile, "w+")
    # print out dictionary for checking ...
    for key in dict:
        s.write(str(key) + "\n")
        for index in range(len(dict[key])):
            s.write("\t" + str(dict[key][index]) + "\n")


def sort_data(mDict):
    # in sorted dictionaries, the keys are sorted in order
    # create a sorted dictionary where the keys are (timestamp, main device) and values associated with each
    # key is an arrays of tuples with the form
    # (other device, proximity, check_num(if constitute checkin), whether this is a checkin)
    sd = SortedDict()
    for key in mDict:
        for index in range(len(mDict[key])):
            # if the size of the tuple is 3, it means that this is not a checkin since a
            # checknum value was not appended, so add the corresponding tuple into the array
            if len(mDict[key][index]) == 3:
                # mDict[key][index][0] is the timestamp, key[0] is the first device tag
                sd.setdefault((mDict[key][index][0], key[0]), []). \
                    append((key[1], mDict[key][index][1], "false"))
            # if the size of the tuple is r, it means that this is a checkin since a
            # checknum value was appended
            if len(mDict[key][index]) == 4:
                sd.setdefault((mDict[key][index][0], key[0]), []). \
                    append((key[1], mDict[key][index][1], mDict[key][index][3], "true"))
    return sd


def sort_data_timestamp(dict):
    sd = SortedDict()
    for key in dict:
        for index in range(len(dict[key])):
            if len(dict[key][index]) == 3:
                sd.setdefault(dict[key][index][0], []).append(((key[1], key[0]), dict[key][index][1], False, -1))
            elif len(dict[key][index]) == 4:
                sd.setdefault(dict[key][index][0], []).append(((key[1], key[0]), dict[key][index][1], True, dict[key][index][3]))
    return sd


mDict = process_single2(process_single1("07_VS_20210109.LOG"))
sd = sort_data_timestamp(mDict)
print_dict(sd)


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
#df1 = pd.DataFrame(list(sd.items()), columns=['key', 'data'])
#df2 = pd.DataFrame(list(sdMotion.items()), columns=['key', 'data'])
# merge data on key - add in motions data if df1 and df2 has the same value in the 'key' column
#df = pd.merge(df1, df2, on=['key'])
# this is printing the merged data frame to output file
#tfile = open('test.txt', 'w+')
#tfile.write(df.to_string())
#tfile.close()


