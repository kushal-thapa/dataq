#!/usr/bin/env python
#
# This script interfaces with the DataQ DI-1100 acquisition device to
# obtain some samples from its analog inputs.
#
# Inputs:
#   c: analog channel (0,1,2,3)
#   t: time duration / length (sec)
#   r: sampling rate (samples/sec)
#   n: number of samples (overrides time)
#   d: decimation factor (number of samples to average)
#   D: debug level (0,1,2)
#   w: filename for output wavefile
#

import argparse
import serial
import time
import sys
import array as arr
import matplotlib.pylab as plt
import scipy as sp
from scipy import signal
from scipy.fftpack import fft, fftfreq
import numpy as np
import array as arr

# Is there a better way to do this?
from dataq_utilities.serial_commands import dataq
DataQ = dataq()

print('Using Python: {:1d}.{:1d}'
      .format(sys.version_info[0], sys.version_info[1]))

#
# Parse Command Line Arguments
#
parser = argparse.ArgumentParser(description='DI-1100')
parser.add_argument('-c', '--channel', default=0, type=int,
                    help='Channel [0,1,2,3]', required=False)
parser.add_argument('-r', '--rate', default=2000, type=int,
                    help='Sampling Rate (sps)', required=False)
parser.add_argument('-t', '--time', default=0.001, type=float,
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
# Find a DataQ device and set it up
#
ser = serial.Serial()
ser.port = DataQ.discover_device()
if (ser.port == False):
    print('No DataQ devices found. Exiting')
    sys.exit()
else:
    print("Found a DataQ device on", ser.port)
    # seems to be insensitive to baud rate, so use big one
    ser.baudrate = '1382400'
    ser.timeout = 0
    ser.open()

DataQ.send_command(ser, 'stop', False)
DataQ.send_command(ser, 'encode 0', False)
DataQ.send_command(ser, 'ps 0', False)
DataQ.send_command(ser, 'info 9', False)
DataQ.send_command(ser, 'dec 1', False)
DataQ.send_command(ser, 'deca 1', False)
DataQ.send_command(ser, 'filter 0', False)

slist = [channel]
DataQ.config_scan_list(ser, slist)

#
# Set up the sampling rate
#
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
# Read samples from serial port
#

nsamp_acq = 0
scale_factor = 10 / 32768

samples = arr.array('i')
waiting = arr.array('I')

DataQ.send_command(ser, 'start', True)
start = time.time()

while (nsamp_acq < Max_Samples):
    while (ser.inWaiting() > 2):
        # how many bytes waiting on link?
        waiting.append(ser.inWaiting())

        # read next sample & append to array
        result = int.from_bytes(ser.read(2),
                                byteorder='little',
                                signed=True)

        samples.append(result)

        # give per-second indicator
        if (nsamp_acq % Fs == 0):
            print('sample: {}'.format(nsamp_acq))

        nsamp_acq = nsamp_acq+1

#
# Shut down the device
#
stop = time.time()
DataQ.send_command(ser, 'stop', False)
time.sleep(1)
ser.flushInput()
ser.close()

mask = 0xFFFC
floatval = np.bitwise_and(samples[0:Max_Samples],mask) * scale_factor

print('Acquisition time: {} seconds'.format(stop-start))

if (DEBUG == 1):
    for n in range(0,Max_Samples):
        print('s[{}] : {:2.4f} \t 0b|{:016b} \t 0x|{:04d}'
              .format(n,floatval[n],samples[n],samples[n])) 


#
# Time plot
#
t = sp.arange(0, acq_duration, 1/Fs)
y = floatval

plt.style.use('classic')

fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1)

ax1.set_axisbelow(True)
ax1.minorticks_on()
ax1.grid(which='major',
         linestyle='-',
         linewidth='0.5',
         color='red')
ax1.grid(which='minor',
         linestyle=':',
         linewidth='0.5',
         color='gray')
ax1.tick_params(which='both',
                top='off',
                left='off',
                right='off',
                bottom='off')

mm = 1.1 * max(y)
mn = min(y)
if (mn < 0):
    mn = 1.1 * mn
else:
    mn = 0.9 * mn
ax1.set_xlim(0, acq_duration)
ax1.set_ylim(mn, mm)
annotation = 'time (sec)'
ax1.set_xlabel(annotation)
ax1.set_ylabel('amplitude')
ax1.plot(t,
         y,
         color='blue',
         linewidth='1')

#
# Spectrum
#
zeropad = 4

NFFT = 2 ** int(np.ceil(np.log2(np.abs(len(y)*zeropad))))
scale_correction = 2.0 / NFFT
Y = fft(y, NFFT)
Y = np.absolute(Y[0:NFFT//2])
YY = Y * Y * scale_correction
YY = 10.0 * np.log10(YY)
Ymax = max(YY) + 6
Ymin = Ymax - 80
Ts = 1/Fs
F = fftfreq(NFFT, Ts)
F = F[0:NFFT//2]

#
# Spectrum on second subplot
#
plt.style.use('classic')
ax2.set_axisbelow(True)
ax2.minorticks_on()
ax2.grid(which='major',
         linestyle='-',
         linewidth='0.5',
         color='red')
ax2.grid(which='minor',
         linestyle=':',
         linewidth='0.5',
         color='gray')
ax2.tick_params(which='both',
                top='off',
                left='off',
                right='off',
                bottom='off')

ax2.set_xlim(0, 1/Ts/2)
annotation = 'freq (f)'
ax2.set_xlabel(annotation)
ax2.set_ylabel('magnitude (dB)')
ax2.set_ylim(Ymin, Ymax)
ax2.plot(F,
         YY,
         color='blue',
         linewidth='1')

plt.tight_layout()
plt.show()

sys.exit()
