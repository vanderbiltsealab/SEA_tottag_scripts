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

# mDict: key of mDict is tuple that looks like (), where tag1 is the tag of the device of the current log
# file; values associated with each key is an array of tuples that looks like: (timestamp, )
mDict = {}
# this is a list used to keep track of the main device that we have processed. this is used to make sure
# that we don't have two sets of data for two devices (make sure we don't have both 01&02 and 02&01)
idList = []
# a list of the three log files that we are currently using
logFiles = ["03_SS_20210109.LOG", "06_ZS_20210109.LOG", "07_VS_20210109.LOG"]
for file in logFiles:
    with open(file) as f:
        # the following string operation gets the ID for the current device
        tag = f.readline()
        header = tag
        if tag.strip():  # strip will remove all leading and trailing whitespace such as '\n' or ' ' by default
            tag = tag.strip("\n ' '")
            totTagID = tag.split()[6].split(',')[0]
            ### debugging
            # print("tottagID: " + totTagID)

            # add this device tag to the idList
            idList.append(totTagID)
        # start going through each line of the log file and separate in range and out of range data
        for line in f:


            # print("this is line[0]: {}".format(line))
            ### debugging notes:
            '''
            from the print statement above we can see that each line is read from a device without a straighforward order
            what we see is that timestamp: 1610201937 is thousands of lines into each logFile... why?
            i think i know why... my little terminal on the bottom can only output so many numbers lol makes sense that 
            they wouldnt be from the very top, butonly show from the most recent to oldest... but still doesn't explain
            the discrepancy in where we find the timestamp in each of the files. i finally get what the data kind of looks like
            logfile03 has data from 06 and 07 and same for the others... 
            
            we may have to include lines that start like:
            "### MOTION CHANGE: STATIONARY; Timestamp: ..." 
            into our final calculations... this will make the data less jumpy and will give us another
            dimension into what our data looks like
            
            not all lines that start with "#' are merely comments
            '''

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
                        # use the setdefault function that initializes an array if the key has not yet been
                        # added into the dictionary, or append to the end of the array if the key already exists
                        # each key is associated with an array of tuples that has the form -
                        # (timestamp, distance, boolean value of whether in checkin range)
                        mDict.setdefault((tokens[1], totTagID), []).append((tokens[0], int(tokens[2]), True))
                        # same as above;
                    else:
                        mDict.setdefault((tokens[1], totTagID), []).append((tokens[0], int(tokens[2]), False))
# all of the data is presented as a dual-key key-pair

# the size of mDict is 7 meaning the number of key-value pairs present in the dictionary, but shouldnt there by only 6?
# print((mDict))
# from one of the outputs i noticed there was a device numbered: c0:98:e5:42:01:ff, this would explain by size is 7

# mDict has all the time stamps we need... this is where we're really starting from


# After filtering through the data for proximity data that is within checkin range, now we determine
# the appropriate checkins
for key in mDict:
    # this value keeps track where we are in the array associated with each key
    index = 0
    # this variable keeps count of valid checkins
    check_num = 0
    # loop through the array of tuples associated with each key in the dictionary
    while index in range(len(mDict[key])):
        # mDict[key][index][2] is the boolean value in the tuple that indicates whether proximity data
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
                    #and (tmpT + 1) == int(mDict[key][index + 1][0]):
                # if this is the first timestamp in the consecutive series, let the trackBeginning variable
                # store the index of the start of this checkin period (the starting timestamp)

                if first: # start of an inRange sequence
                    trackBeginning = i #index of beginning
                    first = False # no longer first in the sequence for key value
                # if in range for over 2 seconds (count >= 2)
                if count >= 2:
                    # a checkin has occurred, and check_num needs to be updated by 1 if haven't already
                    if not checknumUpdate:
                        check_num = check_num + 1
                        checknumUpdate = True
                    # append check_num to original array
                    mDict[key][index] = mDict[key][index] + (check_num, )



                    # this is appending check_num to the first timestamp in the sequence (we did not append
                    # check_num to the first tuple of this checkin because count was 1 by then)
                    if not addToBeginning:
                        mDict[key][trackBeginning] = mDict[key][trackBeginning] + (check_num, )
                        addToBeginning = True

                # increment by 1
                count = count + 1 # if count is not greater than or equal to 2 seconds (ONLY ON FIRST LOOP)
                index = index + 1 # look at next key
                # tmpT = tmpT + 1
            index = index + 1 # if in checkin range, go to next index (next tuple)
        # if not in checkin range, just go to next index (next tuple)
        else:
            index = index + 1


# printing dictionary to output file just for checking
outfile1 = "out1"
s1 = open(outfile1, "w+")
# print out dictionary for checking ...
for key in mDict:
    s1.write("hello" + str(key) + "\n")
    for index in range(len(mDict[key])):
        s1.write("\t" + str(mDict[key][index]) + "\n")


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
            sd.setdefault((mDict[key][index][0], key[0]), []).\
                append((key[1], mDict[key][index][1], "false"))
            # key[1] is the other device id
            # mDict[key][index][1] is the distance between them

        # if the size of the tuple is 4, it means that this is a checkin since a
        # checknum value was appended
        if len(mDict[key][index]) == 4:
            sd.setdefault((mDict[key][index][0], key[0]), []).\
                append((key[1], mDict[key][index][1], mDict[key][index][3], "true"))


# printing dictionary to output file just for checking
outfile2 = "out2"
s2 = open(outfile2, "w+")
# print out dictionary for checking ...
for key in sd:
    s2.write(str(key) + "\n")
    for index in range(len(sd[key])):
        s2.write("\t" + str(sd[key][index]) + "\n")


# TODO: Processing Motions Data Here!
# create sorted dict sdMotion for motion data where the key is (timestamp, main device),
# and value is motion value
sdMotion = SortedDict()
# here's a list of names of the motions data file from Amanda's scripts
# listFiles = ["03_motions.csv", "06_motions.csv", "07_motions.csv"]

listFiles = ["03_motions.csv"] # testing only one for now
for file in listFiles:
    with open(file) as m: # the idea here is to have a reference array so we know what the next line will be
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
            if motion == 0: # fill in with 0s until next 1
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

                if helper_index >= len(time_array): # Lets us break out if our index for time_array equals length
                    # of time_array
                    break
                while str(time + time_offset) != time_array[helper_index]:
                    if time_offset > 4000: # infinite loop going on... doing this to stop it... fix logic
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
                    if time_offset > 4000: # infinite loop going on... doing this to stop it... fix logic
                        break
                    # print("time offset: {}".format(time_offset))
                    sdMotion.setdefault((time + time_offset, device), []).append(motion)
                    # sdMotion.setdefault((time + time_offset, device), motion)
                    time_offset += 1

                    # if time == 1610217561:
                    #     break
                helper_index += 1
                total_count += 1


# printing dictionary to output file just for checking
outfile3 = "out3"
s3 = open(outfile3, "w+")
# print out dictionary for checking ...
for key in sdMotion:
    s3.write(str(key) + "\n")
    for index in range(len(sdMotion[key])):
        s3.write("\t" + str(sdMotion[key][index]) + "\n")


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
