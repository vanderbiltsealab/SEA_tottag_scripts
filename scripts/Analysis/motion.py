import pandas as pd
import numpy as np
import os
import sys
from sortedcontainers import SortedDict
# import matplotlib.dates as md
# import matplotlib.pyplot as plt
from datetime import datetime, tzinfo, timedelta
df = pd.read_table('03_SS_20210109.LOG', sep = '\'')

# print(df)

mot = [] # motion list
times = [] # times list
recording_device = 0
logfile = '03_SS_20210109.LOG'
def find_motion(data):
    with open(logfile) as f:
        for line in f:
            if ((line.find('HEADER') != -1) and (line.find('Device: ') != -1)):
                recording_device = line[(line.find('Device: ')+8):].rstrip('\n')

            elif (line[0] == '#') and (line.find('MOTION CHANGE: ') != -1) and (line.find('Timestamp: ') != -1):
                times.append(int(line[(line.find('Timestamp: ')+11):].rstrip('\n')))
                mot.append(1 if (line[(line.find('MOTION CHANGE: ')+15):line.find('; ')] == 'IN MOTION') else 0)
            # elif (line.find('HEADER') != -1) and (line.find('Device: ') != -1) and (line.find('Timestamp: ') != -1):
            #     recording_device = line[(line.find('Device: ')+8):line.find(', Date:')]
            #     timestamp = int(line[(line.find('Timestamp: ')+11):].rstrip('\n'))
            #     logfile_date = datetime.utcfromtimestamp(timestamp)
        d = {'Timestamp': times, 'Motion': mot, 'Device': recording_device}
        d = pd.DataFrame(d).sort_values(by=['Timestamp']) # this correctly orders based off 'Timestamp'!

        print(d)
        return d

logfile_03 = find_motion(logfile)

logfile_03.to_csv('motion_file_03.csv', index = False)
