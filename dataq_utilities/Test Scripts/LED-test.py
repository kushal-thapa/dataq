#!/usr/bin/env python

import time
import serial
import sys
import argparse

from dataq_utilities.serial_commands import dataq
DataQ = dataq()

print('Using Python: {:1d}.{:1d}'
      .format(sys.version_info[0], sys.version_info[1]))

#
# Parse Command Line Arguments
#
parser = argparse.ArgumentParser(
    description='Blinks LEDs on DataQ device')
parser.add_argument('-c', '--color', default='dum', type=str,
                    help='Color', required=False)
parser.add_argument('-t', '--timeout', default=2, type=int,
                    help='Length of time', required=False)

args = parser.parse_args()
color = args.color.lower()
timeout = args.timeout

#
# Set up the serial port
#
ser = serial.Serial()
ser.port = DataQ.discover_device()
if (ser.port == False):
    print('No DataQ devices found. Exiting')
    sys.exit()
else:
    print("Found a DataQ device on", ser.port)
    ser.baudrate = '115200'
    ser.timeout = 100
    ser.open()

#
# Exercise the LEDs
#
LED = ['black', 'blue', 'green', 'cyan',
       'red', 'magenta', 'yellow', 'white']

if (color == 'dum'):
    blink = ['blue', 'green', 'red', 'white']
else:
    blink = [color]

for color in blink:
    print('Blinking: {}'.format(color))
    ledi = LED.index(color)
    command = 'led {}'.format(ledi)
    DataQ.send_command(ser, command, True)
    time.sleep(timeout)

#
# Reset to yellow
#
ledi = LED.index('yellow')
command = 'led {}'.format(ledi)
DataQ.send_command(ser, command, True)
