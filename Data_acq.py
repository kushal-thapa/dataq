#!/usr/bin/env python3
#****************************************************************************#
#                                                                            #
#                                                                            #
#                          Step I: Data Collection                           #
#                                                                            #
#                                                                            #
#****************************************************************************#
#
import argparse
import serial
import time
import sys
import numpy as np
from scipy.io import wavfile
from datetime import date, datetime
import array as arr

# Is there a better way to do this?
from dataq_utilities.serial_commands import dataq
DataQ = dataq()

print('Using Python: {:1d}.{:1d}'
      .format(sys.version_info[0], sys.version_info[1]))
#
#****************************************************************************#
#
# Parse Command Line Arguments
#
parser = argparse.ArgumentParser(description='DI-1100')
parser.add_argument('-c', '--channel', default=[0,1,2], type=int,
                    help='Channel [0,1,2,3]', required=False)
parser.add_argument('-r', '--rate', default=10000, type=int,
                    help='Sampling Rate (sps)', required=False)
parser.add_argument('-t', '--time', default=20, type=float,
                    help='Length (sec)', required=False)
parser.add_argument('-D', '--debug', default=0, type=int,
                    help='Debug level', required=False)
parser.add_argument('-n', '--nsamp', default=0, type=int,
                    help='Length (samples)', required=False)

args = parser.parse_args()

channel = args.channel
desired_rate = args.rate
acq_duration = args.time
DEBUG = args.debug
nsamp_acq = args.nsamp
if (nsamp_acq != 0):
    acq_duration = nsamp_acq / desired_rate
#
#****************************************************************************#
#
# Finding a DataQ device and setting it up
#
ser = serial.Serial()
ser.port = DataQ.discover_device()
if (ser.port == None):
    print('No DataQ devices found. Exiting')
    sys.exit()
else:
    print("Found a DataQ device on", ser.port)
    # seems to be insensitive to baud rate, so use big one
    ser.baudrate = '1382400'
    ser.timeout = 0
    ser.open()

DataQ.send_command(ser, 'info 1', False)      # Device model number
DataQ.send_command(ser, 'stop', False)        # Stop scanning
DataQ.send_command(ser, 'encode 0', False)    # Binary output
DataQ.send_command(ser, 'ps 0', False)        # Packet size is 16 bytes
DataQ.send_command(ser, 'dec 1', False)       # Primary decimation factor
DataQ.send_command(ser, 'deca 1', False)      # Secondary decimation factor
DataQ.send_command(ser, 'filter 0 0', False)  # filter arg0 arg1 where arg0-
#channel number & arg1- 0,1,2 or 3 (last point, average, max, min resp.)
DataQ.send_command(ser, 'filter 1 0', False)
DataQ.send_command(ser, 'filter 2 0', False)

slist = channel
DataQ.config_scan_list(ser, slist)

# Set up the sampling rate
decimation_factor = 1
Fs = DataQ.sampling_rate(ser, desired_rate, decimation_factor)
Max_Samples = int(Fs * acq_duration)

print('')
print('** Acquiring:')
print('\t From channel {} at {} Hz'.format(slist, Fs))
print('\t {} seconds, {} samples'.format(acq_duration, Max_Samples))
print('\t decimation factor: {}'.format(decimation_factor))
print('')
#
#****************************************************************************#
#
# Reading samples from serial port
#
nsamp_acq = 0
scale_factor = 10 / 32768

#waiting = arr.array('I')
raw_samples=bytearray()
num_samp_per_read=32    # best if Max_Samples/num_samp_per_read is integer
num_bytes_per_read=6*num_samp_per_read

DataQ.send_command(ser, 'start', True)
start = time.time()
while (nsamp_acq < Max_Samples/num_samp_per_read):
    if (ser.inWaiting() >= num_bytes_per_read):
        # how many bytes waiting on link?
        #waiting.append(ser.inWaiting())

        raw_samples=raw_samples+ser.read(num_bytes_per_read)
        nsamp_acq = nsamp_acq+1

stop = time.time()
DataQ.send_command(ser, 'stop', False)
time.sleep(1)
ser.flushInput()
ser.close()
Acq_time = stop-start
print('Acquisition time: {} seconds'.format(Acq_time))

# np.savetxt("waiting.txt",waiting,fmt="%s")  # Saving the 'waiting' array as .txt file
#
#****************************************************************************#
#
# Saving the read data
#
# Typecasting
raw_samples = raw_samples[0:Max_Samples*6]   # necessary if Max_Samples/num_samp_per_read is not integer
xx = memoryview(raw_samples)
yy = xx.cast('h',shape=[Max_Samples,len(channel)])
samples_int16_resized = np.array(yy, dtype=np.int16, copy=False, ndmin=2)

# Writing to a WAV file
date = str(date.today())
sampling_rate = str(desired_rate)
channels = ''.join(map(str, channel))
sequence_length = str(Max_Samples)
currentDT = datetime.now()
time = currentDT.strftime("%H-%M-%S")
filename = (date+'_'+'SR'+sampling_rate+'_'+'SL'+sequence_length+'_'+'CH'+
            channels+'_'+time+'.wav')
wavfile.write(filename, desired_rate, samples_int16_resized)

if (DEBUG == 1):
     for n in range(0,Max_Samples):
        print('s[{}] : {:2.4f} \t 0b|{:016b} \t 0x|{:04d}'.
              format(n,samples_int16_resized[n],raw_samples[n]))

sys.exit()