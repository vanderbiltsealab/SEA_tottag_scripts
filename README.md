# SEA_tottag_scripts
This is a repository that contains python scripts for analyzing TotTag proximity data. The `analysis.py` script is the main script that you should be running, and the Past_scripts folder contains previous versions of the `analysis.py` script as well as other scripts that was merged into `analysis.py`(You can check out the README file in the Past_scripts folder to learn more about them).

## How to install packages
To install the necessary packages for running the scripts in this repository, you can run the following command:

`pip install -r requirements.txt`

## About `analysis.py`
This script accepts a group of raw log files. It performs averaging (also see `Past_scripst/tottagAverager.py`), smoothing (also see `Past_scripst/tottagSmoother.py`), motion analysis (also see `Past_scripst/motion.py`), and proximity data analysis on the group of log files, and it outputs averaging results, smoothing results, motion data results, as well as final merged result for each log file in the group. 

The final merged result is a csv file containing a data frame that includes the columns "timestamp", "device1", "device2", "distance"(between device1 and device 2), "check-in"(whether two devices are within check-in range for over 2 seconds), and motion status of each device, at all timestamps for each raw log file.

## Running `analysis.py`

This script accepts an integer that specifies the smooth value and the names of all log files in a group (can be as many as you want). It outputs 4 files for each log file in the group, including averaged file, smoothed file, motion data file, and merged analysis result. 

The command to run this script looks like:

`python3 analysis.py smooth_val logfile1 logfile2 logfile3 ...`

An example command:

`python3 analysis.py 3 4A@07-12.LOG 50@07-12.LOG 51@07-12.LOG 54@07-12.LOG`

### IMPORTANT NOTE
Sometimes there can be misprints in the raw log files which stop the analysis process. When this happens, the code will exit and prints a message that tells you which line in which log file had the error. You will need to go to that log file and manually comment out the line by adding a `#` at the front of that line.
