import sys
import pandas as pd

# command line input: python logfile_name
logfile = sys.argv[1]
device_tag = logfile[:2]
print(device_tag)
with open(logfile) as f:
    mot = []  # motion list
    times = []  # times list
    recording_device = 0
    for line in f:
        if (line.find('HEADER') != -1) and (line.find('Device: ') != -1):
            recording_device = line[(line.find('Device: ') + 8):].rstrip('\n')

        elif (line[0] == '#') and (line.find('MOTION CHANGE: ') != -1) and (line.find('Timestamp: ') != -1):
            times.append(int(line[(line.find('Timestamp: ') + 11):].rstrip('\n')))
            mot.append(1 if (line[(line.find('MOTION CHANGE: ') + 15):line.find('; ')] == 'IN MOTION') else 0)
    d = {'Timestamp': times, 'Motion': mot, 'Device': recording_device}
    d = pd.DataFrame(d).sort_values(by=['Timestamp'])  # this correctly orders based off 'Timestamp'!
    filename = "motion_file_" + device_tag + ".csv"
    d.to_csv(filename, index=False)
