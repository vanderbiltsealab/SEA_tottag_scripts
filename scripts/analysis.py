import os
import sys
import pandas as pd
from sortedcontainers import SortedDict
# documentation on sortedContainers: http://www.grantjenks.com/docs/sortedcontainers/
# some variables
OUT_OF_RANGE_CODE = 999999
inRangeDist = 915  # 3ft = 915mm

# argv is the array of command line arguments after 'python3' starting at index 0
# the command line argument would be "python analysis.py DATAFILE Motion1 Motion2 Motion3"
DATAFILE = sys.argv[1]
MOTION1 = sys.argv[2]
MOTION2 = sys.argv[3]
MOTION3 = sys.argv[4]


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


# step 2 of processing - After filtering through the data for proximity data that is within checkin range,
# now we determine the appropriate checkins
# This function returns a dictionary that is similar to the previous function, but it will append a check_num
# to the tuples that constitutes as an appropriate checkin
# e.g. appropriate checkin: (key)device2 & device 1 | timestamp & proximity & 2ft? & check_num
#      not checkin: (key)device2 & device 1 | timestamp & proximity & 2ft?
def process_single2(mDict):
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


# this function goes through the dictionary and reorganize it so the the keys are just timestamps
def sort_data_on_timestamp(mDict):
    sd = SortedDict()
    for key in mDict:
        for index in range(len(mDict[key])):
            if len(mDict[key][index]) == 3:
                sd.setdefault(int(mDict[key][index][0]), []).\
                    append((key, mDict[key][index][1], -1, "false"))
            elif len(mDict[key][index]) == 4:
                sd.setdefault(int(mDict[key][index][0]), []).\
                    append((key, mDict[key][index][1], mDict[key][index][3], "true"))
    return sd


# filling in 1s and 0s for the motions file
def motion_analysis(file):
    sdMotion = SortedDict()
    with open(file) as m:  # the idea here is to have a reference array so we know what the next line will be
        # when comparing timestamps below vvvvvv
        time_array = []  # contains timestamps
        for line in m:
            if line[0] == "T":
                continue  # this moves onto the second line
            # creating our helper_array list

            tokens = line.split(",")
            time = tokens[0]
            # print("this it time " + str(time))
            # device = (tokens[2].split("\n"))[0]

            time_array.append(time)
        print(len(time_array))
        # print(time_array[0])  # type str

    # this is where we will be comparing timestamps and will need time_array as a reference array for help ^^^^^^
    with open(file) as n:
        helper_index = 1  # this starts off as index+1 compared to .csv file
        total_count = 0
        for line in n:
            if line[0] == "T":
                continue  # this moves onto the second line
            # print("## i get here ##")
            # split line by comma
            tokens = line.split(",")
            time = tokens[0]
            time = int(time)
            motion = tokens[1]
            motion = int(motion)
            device = (tokens[2].split("\n"))[0]

            ### notes:
            '''
            fill in between the timestamps present in the .csv files, will do this by
            checking if time+1 is not present then insert a new array that looks like this:
            (timestamp+1, device, motion), where motion is 0 or 1
            then insert this array pattern into sdMotion until time+1 is present or lines run out.

            1) figure out what the first line is (this is either motion 1 or 0
            first need to figure out how to tell what the next line will be:
            what we could do is get an array of timestamps before our processing begins => reference array (time_array)
            '''

            ########### DEBUGGING ###########
            # print(time + " " + motion)

            # 1)
            if motion == 0:  # fill in with 0s until next 1
                # check time+time_offset to the index of our helper_array[index+1]
                # this compares our time+offset to the next timestamp in the helper_array
                # if not equal then fill in with entries of the same device, motion, and
                # incrementing timestamp until time+n == helper_array[time+1]

                motion = 0
                time_offset = 0
                # our starting time is same time as time_array's 0th element
                # so we start comparing time+1 to time_array[1] as second comparison
                # the first loop is simply inserting the initial time we started on where motion is 0

                ########### DEBUGGING ###########
                # print(time + time_offset)
                # print(time_array[helper_index])

                if helper_index >= len(time_array):  # Lets us break out if our index for time_array equals length
                    # of time_array
                    break
                while str(time + time_offset) != time_array[helper_index]:
                    if time_offset > 4000:  # infinite loop going on... doing this to stop it... fix logic
                        break
                    # create entries that fill in with either 1s or 0s
                    # this is adding the key (time, device) to the dictionary if this key did not exist before,
                    # and if the key already exist, it will append the motions data to the end of the array
                    # print(motion)
                    sdMotion.setdefault((time + time_offset, device), []).append(motion)
                    # print(time+time_offset)
                    # sdMotion.setdefault((time + time_offset, device), motion)  # maybe try this next
                    time_offset += 1
                helper_index += 1  # we've successfully processed one timestamp in .csv
                total_count += 1  # total count of timestamps counted in .csv

            elif motion == 1:
                motion = 1
                time_offset = 0
                # sdMotion.setdefault((time, device), []).append(motion) # insert first tuple that reads motion == 1
                # sdMotion.setdefault((time, device), motion)
                if helper_index >= len(time_array):
                    break
                while str(time + time_offset) != time_array[helper_index]:

                    ########### DEBUGGING ###########
                    if time_offset > 4000:  # infinite loop going on... doing this to stop it... fix logic
                        break
                    # print("time offset: {}".format(time_offset))
                    sdMotion.setdefault((time + time_offset, device), []).append(motion)
                    # sdMotion.setdefault((time + time_offset, device), motion)
                    time_offset += 1

                    # if time == 1610217561:
                    #     break
                helper_index += 1
                total_count += 1
    # i reorganized the dictionary so that the keys are only the timestamp
    sdNew = SortedDict()
    for key in sdMotion:
        for index in range(len(sdMotion[key])):
            # sdNew.setdefault(int(key[0]), []).append(sdMotion[key])
            sdNew[int(key[0])] = sdMotion[key]
    return sdNew


# in this function we are passing in three motion file dictionaries that results from the motion_analysis() function
# also passing in the dictionary that we obtained from analysing the logfile data
def merge_dataframe(motion1, motion2, motion3, prox_data):
    # converting to data frame where the first column is the keys of the dictionary and the second column is the data
    # so for example, dfMotions03 have timestamps as its first column and the motion data as second column
    df_motion01 = pd.DataFrame(list(motion1.items()), columns=['key', 'motion'+MOTION1[12:14]])
    df_motion02 = pd.DataFrame(list(motion2.items()), columns=['key', 'motion'+MOTION2[12:14]])
    df_motion03 = pd.DataFrame(list(motion3.items()), columns=['key', 'motion'+MOTION3[12:14]])
    df = pd.DataFrame(list(prox_data.items()), columns=['key', 'data'])
    df_merge = pd.merge(df, df_motion03, on=['key'])
    # merge the data frames on timestamps
    df_merge = pd.merge(df_merge, df_motion02, on=['key'])
    df_merge = pd.merge(df_merge, df_motion01, on=['key'])
    # write to output file
    filename = 'Merged_' + DATAFILE[0:14] + ".txt"
    tfile = open(filename, 'w+')
    tfile.write(df_merge.to_string())
    tfile.close()


# first process log file by calling the two process functions
mDict = process_single2(process_single1(DATAFILE))

# then call sort_data_on_timestamp to reorganize the dictionaries so that the keys are timestamps
sd = sort_data_on_timestamp(mDict)

# call motion analysis on all three motions csv file to get three dictionaries of motion data
motion01 = motion_analysis(MOTION1)
motion02 = motion_analysis(MOTION2)
motion03 = motion_analysis(MOTION3)

# finally call the merge function to merge all the data
merge_dataframe(motion01, motion02, motion03, sd)
