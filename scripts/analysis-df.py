import os
import sys
import pandas as pd
import numpy as np
from sortedcontainers import SortedDict
# documentation on sortedContainers: http://www.grantjenks.com/docs/sortedcontainers/
# some variables
OUT_OF_RANGE_CODE = 999999
inRangeDist = 915  # 3ft = 915mm
device_id = ""

# DATAFILE = sys.argv[1]
# MOTION1 = sys.argv[2]
# MOTION2 = sys.argv[3]
# MOTION3 = sys.argv[4]
# MOTION = sys.argv[2:]

DATAFILE = "4A@05-15.LOG"
MOTION = ["4A@05-15-motion.csv", "50@05-15-motion.csv", "51@05-15-motion.csv"]
MOTION1 = "4A@05-15-motion.csv"
MOTION2 = "50@05-15-motion.csv"
MOTION3 = "51@05-15-motion.csv"

# get device id
with open(DATAFILE) as f:
    tag = f.readline()
    if tag.strip():
        tag = tag.strip("\n ' '")
        device_id = tag.split()[6].split(',')[0][:-1]

# read in log file to data frame
df = pd.read_csv(DATAFILE, comment="#", names=["timestamp", "Other_Device", "distance"], sep="\t")

# iterate through 'device' column and get a list of all the devices
device_lst = []
for device in df['Other_Device']:
    if device not in device_lst:
        device_lst.append(device)

# create a list of data frames
df_lst = []

# create a data frame for each device
for device in device_lst:
    df_lst.append(df[df.Other_Device == device])


# this works like filter
# device[0] = df.query('Device=="c0:98:e5:42:00:50"')

# add a new column to end of data frame called 'in_range'
for df in df_lst:
    df = df.assign(in_range=0)

# if within touching range, 'in_range' is 1, otherwise 0
for df in df_lst:
    # a couple of ways to convert from true/false to 1/0
    # 1. replace for whole data frame
    # device1_df = device1_df.replace({True: 1, False: 0})
    # 2. loc
    # device1_df.loc[df.dist < 915, 'in_range'] = 1
    # device1_df.loc[df.dist >= 915, 'in_range'] = 0
    # 3. apply
    # df["in_range"] = df.apply(lambda row: row["distance"] < 915, axis=1).astype(int)

    df["in_range"] = df.apply(lambda row: row["distance"] < 915, axis=1)
    df.insert(1, "Device", device_id)


timestamp_col = 0
device_col = 1
other_device_col = 2
dist_col = 3
in_range_col = 4


for df in df_lst:

    # init two arrays to hold values
    timestamp = []
    in_range = []

    # go through data frame and put data in 'timestamp' and 'in_range' column into arrays
    for j in range(len(df)):
        timestamp.append(df.iloc[[j], [timestamp_col]].values[0][0])
        in_range.append(df.iloc[[j], [in_range_col]].values[0][0])

    # fill the check_in array(same lengths as timestamp) with -1s
    check_in = [-1 for i in range(len(timestamp))]

    # variables used for loop below
    index = 0
    check_num = 0

    # add in check_in count to the check_in array
    while index in range(len(timestamp)):
        print(check_num)
        if in_range[index]:
            t = int(timestamp[index])

            count = 1
            tmpT = t
            i = index
            first = True
            add_to_beginning = False
            check_num_update = False

            while index != len(timestamp) - 1 and in_range[index + 1] and (tmpT + 1) == int(timestamp[index + 1]):
                count = count + 1
                if first:
                    track_beginning = i
                    first = False
                if count >= 2:
                    if not check_num_update:
                        check_num = check_num + 1
                        check_num_update = True
                    check_in[index + 1] = check_num
                    if not add_to_beginning:
                        check_in[track_beginning] = check_num
                        add_to_beginning = True
                index = index + 1
                tmpT = tmpT + 1
            index = index + 1
        else:
            index = index + 1

    # append a new 'check_in' col to data frame
    df["check_in"] = check_in
    print(len(timestamp), len(check_in))


df_lst[0].to_csv("d1", sep="\t")
df_lst[1].to_csv("d2", sep="\t")
df_lst[2].to_csv("d3", sep="\t")

whole = pd.concat(df_lst)
whole = pd.DataFrame(whole).sort_values(by=['timestamp'])
whole.dropna(axis=0, how='any', thresh=None, subset=None, inplace=False)

# get all timestamps
all_timestamp = []
for i in range(len(whole.index)):
    all_timestamp.append(whole.iloc[[i], [0]].values[0][0])

motion_lst = []
count = 1
for motion_file in MOTION:
    motion_lst.append(pd.read_csv(motion_file, comment="T",
                                  names=["timestamp", "motion"+str(count), "Other_Device"], sep=","))
    count += 1

time = pd.DataFrame(all_timestamp, columns=["timestamp"])
merged = whole
count = 1
for df in motion_lst:
    df = pd.merge(time, df, on=["timestamp"], how="outer")
    df.fillna(method="ffill", inplace=True)
    del df["Other_Device"]
    df = df.drop_duplicates(subset=['timestamp']).dropna(subset=['motion'+str(count)])
    df = pd.DataFrame.astype(self=df, dtype=int)
    merged = pd.merge(merged, df, on=['timestamp'])
    count += 1


merged.to_csv("merged", sep="\t")
print(len(df_lst[0].index))
print(len(df_lst[1].index))
print(len(df_lst[2].index))
print(len(whole.index))
