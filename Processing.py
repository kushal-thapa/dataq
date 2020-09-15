#!/usr/bin/env python3
#****************************************************************************#
#                                                                            #
#                                                                            #
#                          Step II Data Processing                           #
#                                                                            #
#                                                                            #
#****************************************************************************#
#
import matplotlib.pyplot as plt
import numpy as np
import scipy as sp
from scipy import signal
from scipy.io import wavfile
from scipy.fftpack import fft, fftfreq
import argparse
import sys
plt.style.use('classic')

print('Using Python: {:1d}.{:1d}'
      .format(sys.version_info[0], sys.version_info[1]))
#
#****************************************************************************#
#
# Parse Command Line Arguments
#
parser = argparse.ArgumentParser(
    description='Processing input file')
#parser.add_argument('-i', '--input', default='dum', type=str,
#                    help='Input file (WAV)', required=True)
parser.add_argument('-f', '--frame', default=1024, type=int,
                    help='FFT frame length', required=False)
parser.add_argument('-o', '--overlap', default=25, type=int,
                    help='Frame overlap (75 pct max)', required=False)
parser.add_argument('-z', '--zeropad', default=4, type=int,
                    help='Zero pad multiplier', required=False)
parser.add_argument('-w', '--window', default='hann', type=str,
                    help='Window function', required=False)
parser.add_argument('-C', '--colormap', default='inferno', type=str,
                    help='Plot filename', required=False)

args = parser.parse_args()

zeropad = args.zeropad
frame = args.frame
overlap = min(args.overlap, 75)
cmap = args.colormap
window_type = args.window

wavefile = '2020-09-14_SR10000_SL200000_CH012_11-25-49.wav'
#wavefile = args.input
if (wavefile == 'dum'):
    print('Error: need input filename')
    sys.exit()
else:
    rate,received_data=wavfile.read(wavefile)

# Validate window
valid_windows = ['boxcar', 'triang', 'hann', 'hamming',
                 'blackman', 'bartlett', 'nuttall']
if window_type not in valid_windows:
    print('** ERROR: bad window type. Try: \n', valid_windows)
    sys.exit()

if (zeropad == 0):
    NFFT = frame
else:
    NFFT = 2 ** int(np.ceil(np.log2(np.abs(frame*zeropad))))
#
#****************************************************************************#
#
# Displaying information from filename
#
"""
filename = wavefile
split_filename = filename.split( "_" ) 
date = split_filename[0] 
sampling_rate_raw = split_filename[1]
sampling_rate_raw = sampling_rate_raw.split("-")
sampling_rate = sampling_rate_raw[1]
acquisition_time = split_filename[2] 
channels_raw = split_filename[3]
channels_raw = channels_raw.split("-")
channels = channels_raw[1]
print('Date:',date)
print('Sampling rate:',sampling_rate)
print('Total acquisiton time:',acquisition_time)
print('Channels used:',channels)
"""
 
# Seperating the channels
chan_1=received_data[:,0]
chan_2=received_data[:,1]
chan_3=received_data[:,2]

# Taking the embedded digital info from channel 1
mask = 0xFFFC
chan_1_masked = np.bitwise_and(chan_1,mask)

# Floating the sample values
scale_factor = 10 / 32768
chan_1_float = np.int16(chan_1_masked) * scale_factor
chan_2_float = np.array(chan_2) * scale_factor
chan_3_float = np.array(chan_3) * scale_factor
#
#****************************************************************************#
#
# Time plot
#
acq_duration = len(chan_1) / rate
t = sp.arange(0, acq_duration, 1/rate)

plt.figure(1,figsize=(12,7))

plt.plot(t,chan_1_float,color='blue',linewidth='1',label='chan_1')
plt.plot(t,chan_2_float,color='red',linewidth='1',label='chan_2')
plt.plot(t,chan_3_float,color='green',linewidth='1',label='chan_3')
plt.xlabel('Time[s]')
plt.ylabel('Amplitude[V]')
plt.legend(loc='upper right')
plt.title('Time Plot',size='xx-large')
plt.grid()

plt.show()
#
#****************************************************************************#
#
# Spectrum
#
def spectrum(y):
    nfft=int(4*(2**(np.ceil(np.log2(len(y))))))
    Y=fft(y,nfft)
    F=fftfreq(nfft,1/rate)
    F=F[0:nfft//2]
    Y=20*np.log10(abs(Y[0:nfft//2]))
    return Y, F

YY1,F1=spectrum(chan_1_float)
YY2,F2=spectrum(chan_2_float)
YY3,F3=spectrum(chan_3_float)

plt.figure(2,figsize=(12,7))
plt.suptitle('Spectrum Graph',size='xx-large')

plt.subplot(3,1,1)
plt.plot(F1,YY1,color='blue')
plt.grid()

plt.subplot(3,1,2)
plt.plot(F2,YY2,color='red')
plt.grid()

plt.subplot(3,1,3)
plt.plot(F3,YY3,color='green')
plt.xlabel('Frequency [Hz]')
plt.grid()

plt.show()
#
#****************************************************************************#
#
# Spectrogram
#
if frame > len(chan_1_float):
    frame = len(chan_1_float)
    print('Frame length was longer than the data.')
    print('Thus, the new frame length is equal to the length of the data.')
    
def spectrogram(data,channel_name):
    #channel_descrp = [ k for k,v in locals().iteritems() if v == data][0]
    frame_overlap = int((overlap/100)*frame)
    freqs, times, Sx = signal.spectrogram(data,
                                      fs=rate,
                                      window=window_type,
                                      nperseg=frame,
                                      noverlap=frame_overlap,
                                      nfft=NFFT,
                                      detrend=False,
                                      return_onesided=True,
                                      mode='magnitude',
                                      scaling='spectrum')
    f, ax = plt.subplots(figsize=(12, 7))
    ax.pcolormesh(times,freqs / 1000,10*np.log10(Sx),cmap=cmap)
    annotation = '"{}" @ {} s/sec ({} s/frame @ {} overlap + {}, fft @ {})'.format(channel_name,
                                                                               rate,
                                                                               frame,
                                                                               frame_overlap,
                                                                               window_type,
                                                                               NFFT)
    ax.set_ylabel('frequency (kHz)', fontsize=14)
    ax.set_xlabel('time (s)', fontsize=14)
    ax.set_title(annotation, fontsize=18)
    plt.show()

# Plotting spectrograms for our data from three channels
spectrogram(chan_1_float,'Channel 1')
spectrogram(chan_2_float,'Channel 2')
spectrogram(chan_3_float,'Channel 3')

sys.exit()
