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
# convert the 'distance' column to numeric values
df["distance"] = pd.to_numeric(df["distance"])

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
    df["in_range"] = df.apply(lambda row: row["distance"] < 915, axis=1).astype(int)
    df.insert(1, "Device", device_id)

# out to csv
df_lst[0].to_csv("d1", index=None)


