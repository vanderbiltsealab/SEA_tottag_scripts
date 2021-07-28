import os
import sys
import pandas as pd

"""
Command to run this script looks like: python3 analysis-df-ver2.py DATAFILE MOTION1 MOTION2 MOTION3 ...

This script does not include initial motion process, averaging, nor smoothing. 

The final output of this script does keep count of check-in numbers but uses 1/0 to identify whether checkin 
occurs or not.

It does not fill in all timestamps from the start of the DATAFILE to its end but only includes those where
proximity data exists.
"""

# some variables
OUT_OF_RANGE_CODE = 999999
inRangeDist = 915  # 3ft = 915mm
device_id = ""

# DATAFILE is the first input variable
DATAFILE = sys.argv[1]
# MOTION is a list of however many motion file that the user input
MOTION = sys.argv[2:]

# get list device tags of the devices in motion files
# used for naming columns later
motion_name = []
for file_name in MOTION:
    motion_name.append(file_name[0:2])

# get device id
with open(DATAFILE) as f:
    tag = f.readline()
    if tag.strip():
        tag = tag.strip("\n ' '")
        device_id = tag.split()[6].split(',')[0]

# read in log file to data frame
df = pd.read_csv(DATAFILE, comment="#", names=["timestamp", "Other_Device", "distance"], sep="\t")

# iterate through 'device' column and get a list of all the devices
device_lst = []
for device in df['Other_Device']:
    if device not in device_lst:
        device_lst.append(device)

# create a list of data frames
df_lst = []

# create a data frame for each device pair
for device in device_lst:
    df_lst.append(df[df.Other_Device == device])

# add a new column to end of each data frame called 'in_range'
# initialize all values to 0
for df in df_lst:
    df = df.assign(in_range=0)

# Use these variables to keep track of index of the columns
timestamp_col = 0
other_device_col = 2
dist_col = 3
in_range_col = 4

# loop through list of data frames and do a lot of things
for df in df_lst:

    # if within touching range, 'in_range' is 1, otherwise 0
    df["in_range"] = df.apply(lambda row: row["distance"] < inRangeDist, axis=1)

    # insert a column at col index 1 called Device
    # values of this column are the device id of THIS device
    df.insert(1, "Device", device_id)


for df in df_lst:

    # init two arrays to hold values
    timestamp = []
    in_range = []

    # go through data frame and put data in 'timestamp' and 'in_range' column into arrays
    for j in range(len(df)):
        timestamp.append(df.iloc[[j], [timestamp_col]].values[0][0])
        in_range.append(df.iloc[[j], [in_range_col]].values[0][0])

    # fill the check_in array(same lengths as timestamp) with -1s
    check_in = [0 for i in range(len(timestamp))]

    # variables used for loop below
    index = 0
    check_num = 1  # keep the count of the number of checkins

    # modify check_in array so that it shows the right check_num
    while index in range(len(timestamp)):
        # check if within checkin range
        if in_range[index]:

            # t keeps track of current timestamp
            t = int(timestamp[index])

            # initialize some variables
            count = 1
            tmpT = t
            i = index
            first = True  # whether this is the beginning of a potential checkin
            add_to_beginning = False
            # check_num_update = False

            # if within checkin range for next consecutive timestamp
            while index != len(timestamp) - 1 and in_range[index + 1] and (tmpT + 1) == int(timestamp[index + 1]):

                count = count + 1

                # if this is the beginning of a potential checkin, keep track of this index
                if first:
                    track_beginning = i
                    first = False

                # if we have 2 consecutive seconds within checkin range, update check_in array
                if count >= 2:

                    # update check_in array
                    check_in[index + 1] = check_num

                    # the check_in val at the start timestamp of the checkin need to be updated
                    if not add_to_beginning:
                        check_in[track_beginning] = check_num
                        add_to_beginning = True
                index = index + 1
                tmpT = tmpT + 1
            index = index + 1
        else:
            index = index + 1

    # append a new 'check_in' col to data frame
    # content of this column is the values of the check_in array
    df["check_in"] = check_in

# out to csv for debugging purposes
# df_lst[0].to_csv("d1", sep="\t")
# df_lst[1].to_csv("d2", sep="\t")
# df_lst[2].to_csv("d3", sep="\t")

# concat data frames for pairs of devices
whole = pd.concat(df_lst)
# sort values of the new, big data frame by timestamp
whole = pd.DataFrame(whole).sort_values(by=['timestamp'])
# remove empty(NA) values
whole.dropna(axis=0, how='any', thresh=None, subset=None, inplace=False)


# -----From here, we will start to add in motions data...----------

# create a list to hold data frames for all motions files
# one data frame will be created for each motions file
motion_lst = []
# count is a variable used to access index of the
# 'motion_name' array at the beginning
count = 0
# loop through the list of motion files the user entered
# create a data frame for each one
for motion_file in MOTION:
    motion_lst.append(pd.read_csv(motion_file, comment="T",
                                  names=["timestamp", "motion"+str(motion_name[count]), "Other_Device"], sep=","))
    count += 1

# start_lst is a list of all the start values of the motion files
start_lst = []
end_lst = []

# go through motion data frames and get start and end values
for motion_df in motion_lst:
    start_lst.append(motion_df.iloc[[0], [0]].values[0][0])
    end_lst.append(motion_df.iloc[[len(motion_df.index) - 1], [0]].values[0][0])


# all_timestamp is all the timestamps from the smallest start value to largest end value
all_timestamp = list(range(min(start_lst), max(end_lst), 1))


# create a data frame of timestamps using the previously obtained 'all_timestamp' array
time = pd.DataFrame(all_timestamp, columns=["timestamp"])
# start to process motion data and merge with proximity data
merged = whole
# count is still used for accessing name list and name columns
count = 0
# go through the motion data frames in the list
for df in motion_lst:

    # merge the 'time' data frame with motion data frame
    # we are merging on 'timestamp' column
    # "outer" means that we are doing an exclusive merge
    df = pd.merge(time, df, on=["timestamp"], how="outer")

    # since we only have motions data for times when motion changed, need to fill in missing motions data
    # "ffill" allow us to do a forward filling; fill empty space with the latest known value
    df.fillna(method="ffill", inplace=True)

    # delete unnecessary columnn
    del df["Other_Device"]

    # drop_duplicates: there were duplicate timestamps, so we want to remove them
    # dropna: this remove NA values
    df = df.drop_duplicates(subset=['timestamp']).dropna(subset=['motion'+str(motion_name[count])])

    # convert data type to int
    # (if we do not do this, motion data value would be floating point type)
    df = pd.DataFrame.astype(self=df, dtype=int)

    # merge motion data to previous data frame,
    # this will add a motions column to end of original data frame
    merged = pd.merge(merged, df, on=['timestamp'])

    count += 1

# remove in-range col, not needed in final result
del merged["in_range"]

# out file
outf_name = DATAFILE[:-4] + "-merged.csv"
merged.to_csv(outf_name, sep="\t")
