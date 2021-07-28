import pandas as pd
import sys

"""
Command to run this script looks like: python3 motion.py LOGFILE

This script accepts a raw log file and outputs a data frame that contains all MOTION CHANGES
in the raw log file.

The main function in this script is incorporated into the final analysis script
"""

mot = []  # motion list
times = []  # times list
recording_device = 0
# This script accepts 1 user input which is the name of the raw log file to process
LOGFILE = sys.argv[1]

def find_motion(data):
    with open(data) as f:
        # the following string operation gets the ID for the current device
        tag = f.readline()
        header = tag
        if tag.strip():  # strip will remove all leading and trailing whitespace such as '\n' or ' ' by default
            tag = tag.strip("\n ' '")
            totTagID = tag.split()[6].split(',')[0]

        for line in f:
            if ((line.find('HEADER') != -1) and (line.find('Device: ') != -1)):
                recording_device = line[(line.find('Device: ')+8):].rstrip('\n')

            elif (line[0] == '#') and (line.find('MOTION CHANGE: ') != -1) and (line.find('Timestamp: ') != -1):
                times.append(int(line[(line.find('Timestamp: ')+11):].rstrip('\n')))
                mot.append(1 if (line[(line.find('MOTION CHANGE: ')+15):line.find('; ')] == 'IN MOTION') else 0)

        d = {'Timestamp': times, 'Motion': mot, 'Device': totTagID}
        d = pd.DataFrame(d).sort_values(by=['Timestamp']) # this correctly orders based off 'Timestamp'!
        return d


logfile = find_motion(LOGFILE)
filename = LOGFILE[:-4] + '-motion.csv'
logfile.to_csv(filename, index=False)
