import pandas as pd
import sys


mot = [] # motion list
times = [] # times list
recording_device = 0
LOGFILE = sys.argv[1]


def find_motion(data, d_tag):
    with open(data) as f:
        # the following string operation gets the ID for the current device
        tag = f.readline()
        header = tag
        if tag.strip():  # strip will remove all leading and trailing whitespace such as '\n' or ' ' by default
            tag = tag.strip("\n ' '")
            totTagID = tag.split()[6].split(',')[0]
            d_tag = totTagID[15:17]

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
        d = {'Timestamp': times, 'Motion': mot, 'Device': totTagID}
        d = pd.DataFrame(d).sort_values(by=['Timestamp']) # this correctly orders based off 'Timestamp'!
        return d, d_tag


device_tag = ''
lst = find_motion(LOGFILE, device_tag)
logfile_03 = lst[0]
filename = LOGFILE[:-4] + '_motion.csv'
logfile_03.to_csv(filename, index=False)
