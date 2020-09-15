#
# This is a library for DataQ interface functions.
#
# At some point it will include a collection of "serial" interfaces as
# well as "USB" interfaces, all of which use the same set of command
# and data parsing routines.
#

import serial.tools.list_ports
import serial
import time
import usb.core

class dataq:
    def __init__(self):
        ''' Constructor for this class '''
        self.functions = ['discover_device',
                         'config_scan_list',
                         'send_command',
                         'find_device']

    def show(self):
        print('DataQ serial commands')
        for fcn in self.functions:
            print('\t {}'.format(fcn))
                        

    #
    # Tweaked version of "discovery()"
    # From DI-1100-serial
    #
    # Returns a serial port object
    #
    # Discover DATAQ Instruments devices and models.  Note that if
    # multiple devices are connected, only the device discovered first is
    # used. We leave it to you to ensure that it's a DI-1100.
    #
    
    def discover_device(self):
        # Get a list of active com ports to scan for possible DATAQ
        # Instruments devices
        available_ports = list(serial.tools.list_ports.comports())
        # Will eventually hold the com port of the detected device, if any
        hooked_port = ""
        for p in available_ports:
            # Do we have a DATAQ Instruments device?
            if ("VID:PID=0683" in p.hwid):
                # Yes!  Dectect and assign the hooked com port
                hooked_port = p.device
                return(hooked_port)
                break

    #
    # Tweaked version of "config_scn_lst()"
    # From DI-1100-serial
    #
    # Returns nothing
    #

    def config_scan_list(self, ser, slist):
        # Scan list position must start with 0 and increment sequentially
        position = 0
        for item in slist:
            dataq.send_command(self, ser, "slist " + str(position) + " " + str(item), False)
            # Add the channel to the logical list.
            position += 1

    #
    # Tweaked version of "send_cmd()"
    # From DI-1100-serial
    #
    # Returns values from serial port
    #

    def send_command(self, ser, command, acquiring):
        ser.write((command+'\r').encode())
        time.sleep(.1)
        if not(acquiring):
            # Echo commands if not acquiring
            while True:
                if(ser.inWaiting() > 0):
                    while True:
                        try:
                            s = ser.readline().decode()
                            s = s.strip('\n')
                            s = s.strip('\r')
                            s = s.strip(chr(0))
                            break
                        except:
                            continue
                    # This "if" is at the level of the "while"
                    if s != "":
                        print('Cmd / Echo: {} / {}'.format(command, s))
                        break

    #
    # Tweaked version of the original "findProdPort()"
    # From LED-test
    #
    # Returns a string
    #

    def find_device(self):
        # find USB devices
        device = usb.core.find(find_all=True)
        # loop through devices and check the hexadecimal form of each
        # one's product id
        for cfg in device:
            regPID = hex(cfg.idVendor)
            
            # find a match with the target vendor id. Up to you to ensure
            # it's a compatible model.
            if regPID == '0x683':
                uid = cfg.idProduct
                
                # search through COM Ports and find location of connected
                # product
                p_list = serial.tools.list_ports.comports()
                
                for com in p_list:
                    #ser1 = serial.Serial('COM9', 38400, timeout=100)
                    if com.pid == uid:
                        serID = str(com.device)
                        return serID

    #
    # Sets the sampling rate using DataQ's weird approach
    #
    # Returns actual sampling rate
    #

    def sampling_rate(self, ser, desired_rate, decimation_factor):
        #
        # Define sample rate = 1 Hz, where decimation_factor = 1000:
        # 60,000,000/(srate) = 60,000,000 / 60000 / decimation_factor = 1 Hz
        #
        Big_Number = 60000000        
        srate_value = int(Big_Number / desired_rate / decimation_factor)
        srate_command = '{}{}'.format('srate ', srate_value)
        
        dataq.send_command(self, ser, srate_command, False)
        dataq.send_command(self, ser, 'srate', False)

        Fs = int(60000000 / srate_value / decimation_factor)
        
        return Fs
