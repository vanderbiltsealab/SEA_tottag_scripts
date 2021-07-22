import os
import sys
import pandas as pd
import numpy as np
from sortedcontainers import SortedDict

OUT_OF_RANGE_CODE = 999999
# smoothVal = int(sys.argv[1])
# logs = sys.argv[2:]
logfile_date = None
logs = ["logfiles/4A@07-12.LOG", "logfiles/50@07-12.LOG", "logfiles/51@07-12.LOG", "logfiles/54@07-12.LOG"]
averaged_logs = []
smoothed_logs = []
smoothVal = 3
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

                    if find.strip():  # strip will remove all leading and trailing whitespace such as '\n' or ' ' by default
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


DATAFILE = smoothed_logs[0]
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


def get_device_id(file):
    with open(file) as f:
        tag = f.readline()
        tag = tag.strip("\n ' '")
        return tag.split()[6].split(',')[0][:-1]


# for i in range(1):
for indx in range(len(logs)):
    df_lst = []
    # get id of current device(the one we are analysing)
    cur_device_id = get_device_id(logs[indx])

    # get a list of the other devices

    other_device_lst = []
    # first get a list of all devices by looping through raw log files, reading its first line,
    # and getting device ids with string operations
    for f in logs:
        other_device_lst.append(get_device_id(f))
    # remove id of cur device from list to obtain a list of other devices
    other_device_lst.remove(cur_device_id)

    # create a data frame for raw cur log file and smoothed cur log file
    raw_df = pd.read_csv(logs[indx], comment="#", names=["timestamp", "device2", "distance"], sep="\t")
    smoothed_df = pd.read_csv(smoothed_logs[indx], comment="#", names=["timestamp", "device2", "distance"], sep="\t")

    # use max and min timestamp to get a list of all timestamps that we want in the final result
    # fixme: in 50@07-12.LOG, there are still motion data after it stops recording position changes,
    #  do we still want those?
    # fixme: if we do want those, need to change the min to the min of motion_timestamp & [timestamp] min
    time_range = list(range(raw_df["timestamp"].min(), raw_df["timestamp"].max() + 1, 1))
    # print("min: " + str(time_range[0]))
    # print("max: " + str(time_range[-1]))

    device1_lst = []
    device1_lst = np.full(len(time_range), cur_device_id)

    lst = []
    for other_device in other_device_lst:
        d = {'timestamp': time_range, 'device1': cur_device_id, 'device2': other_device}
        lst.append(pd.DataFrame(d))

    for k in range(len(lst)):
        other_device = other_device_lst[k]
        lst[k] = pd.merge(lst[k], smoothed_df, on=["timestamp", "device2"], how="outer")
        cur_df = lst[k]
        lst[k] = cur_df[cur_df['device2'] == other_device]

    # just to keep track of column index
    timestamp_col = 0
    other_device_col = 2
    dist_col = 3
    in_range_col = 4

    for df in lst:
        # if within touching range, 'in_range' is 1, otherwise 0
        df["in_range"] = df.apply(lambda row: row["distance"] < inRangeDist, axis=1)

    for df in lst:
        # init two arrays to hold values
        timestamp = df["timestamp"].tolist()
        in_range = df["in_range"].tolist()

        # fill the check_in array(same lengths as timestamp) with -1s
        check_in = [0 for num in range(len(timestamp))]

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
        df_lst.append(df)

    # concat data frames for pairs of devices
    whole = pd.concat(df_lst)
    # sort values of the new, big data frame by timestamp
    whole = pd.DataFrame(whole).sort_values(by=['timestamp'])

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

    start_lst = []
    end_lst = []
    # go through motion data frames and get start and end values
    for motion_df in motion_lst:
        start_lst.append(motion_df["timestamp"].min())
        end_lst.append(motion_df["timestamp"].max())

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
        # df = df.drop_duplicates(subset=['timestamp']).dropna(subset=['motion'+str(motion_name[count])])

        # convert data type to int
        # (if we do not do this, motion data value would be floating point type)
        # df = pd.DataFrame.astype(self=df, dtype=int)

        # merge motion data to previous data frame,
        # this will add a motions column to end of original data frame
        merged = pd.merge(merged, df, on=['timestamp'], how="outer")
        merged = pd.DataFrame(merged).sort_values(by=['timestamp'])
        count += 1

    # remove in-range col, not needed in final result
    del merged["in_range"]
    print("Producing merged file " + str(indx + 1) + " ...")
    outf_name = str(logs[indx])[:-4] + "-merged.csv"
    merged.to_csv(outf_name, sep="\t", index=False)


