# Past Scripts
This folder contains previous versions of the analysis script as well as averager, smoother, and motion script that was incorporated in the analysis script.

## `tottagAverager.py`
This script takes at least 3 arguments: the starting Unix timestamp, the ending Unix timestamp, and a list of every log file that you would like to average together. The data is averaged across timestamps by dyad, so the measured value at a certain timestamp from one TotTag is averaged with the value at the same timestamp from its companion TotTag. 

The script can be run like so:

`python tottagAverager.py START_TIME_VAL END_TIME_VAL LOG_FILE_1 LOG_FILE_2...`

## `tottagSmoother.py`
This script takes at least 2 arguments: the number of data points over which to smooth, followed by a list of every log file you would like to smooth. The smoother works by taking a moving average with a width of SMOOTHING_VAL. When it encounters a gap in the data greater than the aforementioned value, the smoothing buffer is cleared and it starts over after the gap.

To run the script, enter:

`python tottageSmoother.py SMOOTHING_VAL AVERAGED_LOG_FILE_1 AVERAGED_LOG_FILE_2...`

## `tottagStats.py`
This script produces summary statistics on the smoothed log file. The statistics it outputs are the amount of time each dyad spent within 3ft of one another, the amount of time the TotTags were in range of one another, and the number of times a dyad re-enters 3ft after leaving it for at least 30 seconds. 

The input for this script is simply a single log file:

`python tottagStats.py SMOOTHED_LOG_FILE_1`

## `tottag-motion.ipynb` & `motion.py`
This script analyse raw log files and extract motion data from them. It produces a data frame with 3 columns - "timestamp", "motion", and "device_id". Note that the results returned from this script only includes motion data at points of motion changes (rows in raw log files that records motion status changes), not motion data at all timestamps. Full motion data needs to be filled out for later processing. 

The command to run the `motion.py` script: 

`python3 motion.py LOGFILE`

## `analysis-dict.py`

Unlike later scripts that mainly use pandas data frames to process data, this script mainly uses dictionaries 
to process data. And since that introduced some back and forth logic into the script, and pandas also provides some 
predefined functions that are useful for our processing, we switched to using data frames for most of the processing.

This script does not include initial motion process, averaging, nor smoothing. 

The final output of this script numbers check-in occurrences. 

It does not fill in all timestamps from the start of the DATAFILE to its end but only includes those where
proximity data exists.

Command to run this script looks like: 

`python3 analysis-dict.py DATAFILE MOTION1 MOTION2 MOTION3 ...`

## `analysis-df-ver1.py`
This script does not include initial motion process, averaging, nor smoothing. 

The final output of this script numbers check-in occurrences. 

It does not fill in all timestamps from the start of the DATAFILE to its end but only includes those where
proximity data exists

Command to run this script looks like:

`python3 analysis-df-ver1.py DATAFILE MOTION1 MOTION2 MOTION3 ...`

## `analysis-df-ver2.py`

This script does not include initial motion process, averaging, nor smoothing. 

The final output of this script does keep count of check-in numbers but uses 1/0 to identify whether checkin 
occurs or not.

It does not fill in all timestamps from the start of the DATAFILE to its end but only includes those where
proximity data exists.

Command to run this script looks like:

`python3 analysis-df-ver2.py DATAFILE MOTION1 MOTION2 MOTION3 ...`

## `analysis-df-ver3.py`

This script includes averaging, smoothing, and initial motion analysis. 

The final output of this script numbers check-in occurrences. 

It does not fill in all timestamps from the start of the DATAFILE to its end but only includes those where
proximity data exists.

Command to run this script looks like: 

`python3 analysis-df-ver4.py smooth_val logfile1 logfile2 logfile3`

## `analysis-df-ver4.py`

This script includes averaging, smoothing, and initial motion analysis. 

The final output of this script does keep count of check-in numbers but 
uses 1/0 to identify whether checkin occurs or not.

The output of this script combines result from analyzing all logfiles in the input group. 
e.g., if input logfiles include data from device a, b, c, then result of this script includes 
data between a&b, a&c, b&a, b&c, c&a, c&b at all timestamps(note: fill in all numbers between start and end timestamp
regardless of whether motion/proximity data exists)

We are not using this version because the final output for this version is too large for further processing.

Command to run this script looks like: 

`python3 analysis-df-ver4.py smooth_val logfile1 logfile2 logfile3`