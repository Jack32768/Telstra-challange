#! /usr/bin/python
__author__ = 'Jack'
##########
#For PY2 #
##########
print "Testing to creat a thread"

import time
import threading
import serial
import sys
from time import *
import time
import threading

import subprocess
import urllib2
import re
import json

import traceback

import base64



############
#Global Var#
############
serial_USB = "/dev/ttyACM0" #USB serial interface on Rasp
baud_rate = 9600
serial_delay = 1 # Second(e) between reloading serail value
serialPort = None # Port with in the scope of program
serialp = None # Polling thread
outFile = "AccData.txt"
#uploadfreq = 6

#############################
# Code set up Serial thread #
#############################

class SerialPoller (threading.Thread):
#    super(SerialPoller, self).__init__(self)
    def __init__ (self):
        threading.Thread.__init__(self)
        global serialPort, serrialPort,serial_USB, baud_rate # bring it into scope
        serialPort = serial.Serial (serial_USB, baud_rate) #initiallize
        self.current_value = None
        self.running = True #setting the thread to running

    def run (self):
        global serialPort
        if not serialPort.readable() :
            print 'Port %s not ready to be read' %serial_USB

#############################################
# Main program loop #########################
#############################################

def main ():
    global serial_delay
    global serialp
    global serialPort
    print "creating a thread"
    serialp = SerialPoller() #Creat the thread instance
    accData = []
    accTMP = []
    try:
        #serialp.start()
        #print "wait 5 s"
        #while True: # main loop
        for x in range(0,16):
            serialPort.flushInput()
            serialPort.write("start")
            time.sleep(0.002)
            print "start ok"
            if serialPort.readline() == "ready\r\n":
                print "ready to receive"
                d = serialPort.readline()
                #print "Raw data: ",x,"=",d
                #d = re.findall(r"[+-]? *(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", d)
                print "Processed data: ",d
                accData.append(d)
                time.sleep(0.199)
        print accData
        #x = np.append(x,data)
        f = open(outFile,'w')
        print outFile,"opend successfully"
        json.dump(accData,f)
        f.close()
        print outFile,"saved successfully"
        #sys.exit()
        #print data
        #del data[:]
        #x = 0

    except:
        print "ooooooops,Serial gone wrong"


if __name__ == "__main__":
    sys.exit(main())
