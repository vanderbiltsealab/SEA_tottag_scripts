import os
import sys
import pandas as pd
import numpy as np
from sortedcontainers import SortedDict
# documentation on sortedContainers: http://www.grantjenks.com/docs/sortedcontainers/
# some variables
OUT_OF_RANGE_CODE = 999999
inRangeDist = 915  # 3ft = 915mm

DATAFILE = "4A@05-15.LOG"
MOTION1 = "4A@05-15-motion.csv"
MOTION2 = "50@05-15-motion.csv"
MOTION3 = "51@05-15-motion.csv"


df = pd.read_csv(DATAFILE, comment="#", names=["timestamp", "device", "dist"], sep="\t")
df.to_csv("checkcheck", index=None)
df["dist"] = pd.to_numeric(df["dist"])

def convert(b):
    if b:
        return 1
    else:
        return 0


# this works like filter
device1_df = df.query('device=="c0:98:e5:42:00:50"')


# iterate through column
device_lst = []
for device in df['device']:
    print(device)
    if device not in device_lst:
        device_lst.append(device)

# assign new col
device1_df = device1_df.assign(in_range=0)

# a couple of ways to convert from true/false to 1/0
# 1. replace for whole data frame
# device1_df = device1_df.replace({True: 1, False: 0})
# 2. loc
device1_df.loc[df.dist < 915, 'in_range'] = 1
device1_df.loc[df.dist >= 915, 'in_range'] = 0
# 3. apply
# device1_df["in_range"] = df.apply(lambda row: row["dist"] < 915, axis=1).astype(int)

device1_df.to_csv("d1")

