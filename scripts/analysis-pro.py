import os
import sys
import numpy as np
import pandas as pd
from sortedcontainers import SortedDict

OUT_OF_RANGE_CODE = 999999
smoothVal = int(sys.argv[1])
logs = sys.argv[2:]
# logs = ["4F@03-20.LOG", "50@03-20.LOG", "51@03-20.LOG"]
averaged_logs = []
smoothed_logs = []
# smoothVal = 3
inRangeDist = 915  # 3ft = 915mm
device_id = ""
# First file input is the one that we will analyse
MOTION = []

print("Processing...")

# average
for i in logs:

    outFile = i[:-4] + "-averaged.log"
    s = open(outFile,"w+")
    averaged_logs.append(outFile)

    with open(i) as f:

        tag = f.readline()
        header = tag

        if tag.strip(): # strip will remove all leading and trailing whitespace such as '\n' or ' ' by default
            tag = tag.strip("\n ' '")
            tag = tag.split()[6].split(',')[0]
        sd = SortedDict()

        for line in f:
            # if line is not a comment, or if line does not contain any hashtags
            if line[0] != '#' and line.find('#') == -1:
                tokens = line.split('\t')
                if (int(tokens[2]) != OUT_OF_RANGE_CODE):
                    #if (int(tokens[0]) >= int(vals[0]) and int(tokens[0]) <= int(vals[1])):
                    sd.setdefault(tokens[0], {}).setdefault(tokens[1], []).append(tokens[2].rstrip('\n'))

        for x in logs:

            if (x != i):
                with open(x) as w:
                    find = w.readline()

                    if find.strip(): # strip will remove all leading and trailing whitespace such as '\n' or ' ' by default
                        find = find.strip("\n ' '")
                        find = find.split()[6].split(',')[0]

                    for row in w:
                        # if line is not a comment, or if line does not contain any hashtags
                        if row[0] != '#' and row.find('#') == -1:
                            token = row.split('\t')
                            if token[1] == tag:
                                if int(token[2]) != OUT_OF_RANGE_CODE:
                                    # if int(token[0]) >= int(vals[0]) and int(token[0]) <= int(vals[1]):
                                    sd.setdefault(token[0], {}).setdefault(find, []).append(token[2].rstrip('\n'))
                w.close()

        totalVal = 0
        s.write(header)

        for time in sd:
            for tag in sd[time]:
                for val in sd[time][tag]:
                    totalVal += int(val)
                s.write(time+'\t'+tag+'\t'+str(int(totalVal/len(sd[time][tag])))+'\n')
                totalVal = 0

    f.close()


# class to handle the moving average.
# works kind of like a queue, keeping smoothVal values stored
class SmoothedGroup:

    def __init__(self, time, mote, val, size, s):
        self.stamps = []
        self.data = []

        self.size = size
        self.stamps.append(time)
        self.data.append(val)
        self.mote = mote
        self.lastTime = time
        self.outfile = s

    def addVal(self, time, val):
        self.stamps.insert(0, time)
        self.data.insert(0, val)
        self.lastTime = time
        if len(self.data) >= self.size:
            self.average()

    def clear(self):
        self.stamps = []
        self.data = []

# helper method to average and write out the line. Pops oldest value off
    def average(self):
        averageVal = 0
        index = int(self.size/2)
        for i in range(0, self.size):
            averageVal += self.data[i]
        self.data.pop()
        self.stamps.pop()
        averageVal /= self.size
        # used to be int(averageVal)/25.4.12
        self.outfile.write(str(self.stamps[index])+"\t"+self.mote+"\t"+str(round((int(averageVal)), 2))+"\n")


# Smooth
for i in averaged_logs:

    outFile = i[:-13] + "-smoothed.log"
    s = open(outFile, "w+")
    smoothed_logs.append(outFile)
    first = {}
    classDict = {}

    with open(i) as f:
        s.write(f.readline())

        for line in f:

            if line[0] != '#' and line.find('#') == -1:
                tokens = line.split('\t')
                # this if only operates on the first recording from each mote.
                # serves to initialize the class
                if first.setdefault(tokens[1], True) and int(tokens[2]) != OUT_OF_RANGE_CODE:
                    classDict[tokens[1]] = classDict.setdefault(tokens[1], SmoothedGroup(int(tokens[0]), tokens[1], int(tokens[2]), smoothVal, s))
                    first[tokens[1]] = False
                elif int(tokens[2]) != OUT_OF_RANGE_CODE:
                    # checks here for time skips
                    timeDiff = int(tokens[0]) - classDict[tokens[1]].lastTime

                    if timeDiff == 1:
                        classDict[tokens[1]].addVal(int(tokens[0]), int(tokens[2]))
                    # If the skip is small, fills in time with current value
                    elif 1 < timeDiff <= smoothVal:
                        for i in range(classDict[tokens[1]].lastTime + 1, int(tokens[0]) + 1):
                            classDict[tokens[1]].addVal(i, int(tokens[2]))
                    # If the skip is larger than the smoothVal, it starts the buffer over
                    else:
                        classDict[tokens[1]].clear()
                        classDict[tokens[1]].addVal(int(tokens[0]), int(tokens[2]))
        f.close()
    s.close()

# smoothed_logs = ["test/4F@03-20-smoothed.LOG", "test/50@03-20-smoothed.LOG", "test/51@03-20-smoothed.LOG"]
dataframe_lst = []
device_id_lst = []
min_time = []
max_time = []


def get_device_tag(file):
    with open(file) as f:
        tag = f.readline()
        tag = tag.strip("\n ' '")
        return tag.split()[6].split(',')[0]


# Get Motion Data
mot = []  # motion list
times = []  # times list
recording_device = 0


def find_motion(data):
    with open(data) as f:
        # the following string operation gets the ID for the current device
        tag = f.readline()
        header = tag
        if tag.strip():  # strip will remove all leading and trailing whitespace such as '\n' or ' ' by default
            tag = tag.strip("\n ' '")
            totTagID = tag.split()[6].split(',')[0]

        for line in f:
            if (line.find('HEADER') != -1) and (line.find('Device: ') != -1):
                recording_device = line[(line.find('Device: ')+8):].rstrip('\n')

            elif (line[0] == '#') and (line.find('MOTION CHANGE: ') != -1) and (line.find('Timestamp: ') != -1) \
                    and line[3:].find("#") == -1:
                times.append(int(line[(line.find('Timestamp: ')+11):].rstrip('\n')))
                mot.append(1 if (line[(line.find('MOTION CHANGE: ')+15):line.find('; ')] == 'IN MOTION') else 0)
            # elif (line.find('HEADER') != -1) and (line.find('Device: ') != -1) and (line.find('Timestamp: ') != -1):
            #     recording_device = line[(line.find('Device: ')+8):line.find(', Date:')]
            #     timestamp = int(line[(line.find('Timestamp: ')+11):].rstrip('\n'))
            #     logfile_date = datetime.utcfromtimestamp(timestamp)
        d = {'Timestamp': times, 'Motion': mot, 'Device': totTagID}
        d = pd.DataFrame(d).sort_values(by=['Timestamp'])  # this correctly orders based off 'Timestamp'!
        filename = LOGFILE[:-4] + '-motion.csv'
        d.to_csv(filename, index=False)
        return filename


# Call function on every input logfile
for LOGFILE in logs:
    file = find_motion(LOGFILE)
    MOTION.append(file)


# Now Do Analysis
# get list device tags of the devices in motion files
# used for naming columns later
motion_name = []
for file_name in MOTION:
    motion_name.append(file_name[0:2])

# go through each raw log file and create dataframe for each, also gather a list of all devices involved
for file in logs:

    dataframe_lst.append(pd.read_csv(file, comment="#", names=["timestamp", "Other_Device", "distance"], sep="\t"))

    with open(file) as f:
        tag = f.readline()
        tag = tag.strip("\n ' '")
        device_id_lst.append(tag.split()[6].split(',')[0])


# getting the largest and smallest timestamp val in each raw log file dataframe
for dataframe in dataframe_lst:
    min_time.append(dataframe["timestamp"].min())
    max_time.append(dataframe["timestamp"].max())

# use max and min timestamp to get a list of all timestamps that we want in the final result
time_range = list(range(min(min_time), max(max_time), 1))

# device1_lst is a list of lists, each sublist is a list with same values - the device tag,
# with lengths same as time_range
device1_lst = []
for device in device_id_lst:
    for i in range(len(logs) - 1):
        device1_lst.append(np.full(len(time_range), device))

# sep_dict is a dictionary where keys are device tags, and each tag is associated with a list of dataframes where the
# device2 column will be later filled with all the other devices
# e.g. devices are 4f, 50, 51; then keys of this dict will be 4f, 50, and 51; 4f will be associated
# with a list of 2 dataframes with 'device2' column being 50 and 51
sep_dict = {}
n = len(device_id_lst) * (len(device_id_lst) - 1)

device1_lst = []
for device_id in device_id_lst:
    device1_lst.append(np.full(len(time_range), device_id))


for i in range(len(device_id_lst)):
    for j in range(2):
        d = {'timestamp': time_range, 'device1': device1_lst[i]}
        sep_dict.setdefault(device_id_lst[i], []).append(pd.DataFrame(d))

# adding 'device2' columns to the dataframes
tmp = device_id_lst.copy()
for key in sep_dict:
    tmp.remove(key)
    for i in range(len(sep_dict[key])):
        sep_dict[key][i] = sep_dict[key][i].assign(device2=tmp[i])
    tmp = device_id_lst.copy()

# creating data frames for smoothed log files and merging with data frames in the sep_dict
smoothed_df_lst = []
for file in smoothed_logs:
    cur_device_id = get_device_tag(file)
    smoothed_df = pd.read_csv(file, comment="#", names=["timestamp", "device2", "distance"], sep="\t")
    for i in range(len(sep_dict[cur_device_id])):
        sep_dict[cur_device_id][i] = pd.merge(sep_dict[cur_device_id][i], smoothed_df, on=["timestamp", "device2"], how="outer")

# just to keep track of column index
timestamp_col = 0
other_device_col = 2
dist_col = 3
in_range_col = 4

# adding an in_range column to each data frame where value is
# 1 when distance is within 3 feet and 0 otherwise
df_lst = []
for key in sep_dict:
    for i in range(len(sep_dict[key])):
        # if within touching range, 'in_range' is 1, otherwise 0
        sep_dict[key][i]["in_range"] = sep_dict[key][i].apply(lambda row: row["distance"] < inRangeDist, axis=1)

        # insert a column at col index 1 called Device
        # values of this column are the device id of THIS device
        # df_lst.append(sep_dict[key][i])

# creating the check_in column where value is 1 when distance is within 3 feet for at least 2 seconds
for key in sep_dict:
    for k in range(len(sep_dict[key])):

        # init two arrays to hold values
        timestamp = sep_dict[key][k]["timestamp"].tolist()
        in_range = sep_dict[key][k]["in_range"].tolist()

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
        sep_dict[key][k]["check_in"] = check_in
        df_lst.append(sep_dict[key][k])

# concat data frames for pairs of devices
whole = pd.concat(df_lst)
# sort values of the new, big data frame by timestamp
whole = pd.DataFrame(whole).sort_values(by=['timestamp'])
# remove empty(NA) values

whole.to_csv("before_motionaaa.csv", sep="\t", index=None)

for key in sep_dict:
    for i in range(len(sep_dict[key])):
        print(sep_dict[key][i])


# ---------------------------------------------------------
# ---------------------------------------------------------

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


# create a data frame of timestamps using the previously obtained 'all_timestamp' array
time = pd.DataFrame(time_range, columns=["timestamp"])
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
    # df = df.drop_duplicates(subset=['timestamp']).dropna(subset=['motion'+str(motion_name[count])])

    # convert data type to int
    # (if we do not do this, motion data value would be floating point type)
    # df = pd.DataFrame.astype(self=df, dtype=int)

    # merge motion data to previous data frame,
    # this will add a motions column to end of original data frame
    merged = pd.merge(merged, df, on=['timestamp'], how="outer")
    merged = pd.DataFrame(merged).sort_values(by=['timestamp'])
    count += 1


# This part is necessary because when doing a 'outer' merge in the previous look,
# null values are being introduced in many columns. Since int does not support N/A
# values, pandas does an automatic conversion from int to float.
# These few lines of code fills null values with numeric values and convert them back to int
"""
for name in motion_name:
    col_name = "motion" + name
    merged[col_name].fillna(888888, inplace=True)
    merged[col_name] = pd.DataFrame.astype(self=merged[col_name], dtype=int)


merged["check_in"].fillna(888888, inplace=True)
merged["check_in"] = pd.DataFrame.astype(self=merged["check_in"], dtype=int)
"""
# remove in-range col, not needed in final result

del merged["in_range"]

merged.dropna(subset=['device1'], inplace=True)

# out file
outf_name = "merged.csv"
merged.to_csv(outf_name, sep="\t", index=False)
print("Finished.")