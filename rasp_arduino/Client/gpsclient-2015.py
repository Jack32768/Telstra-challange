#! /usr/bin/python

import os
from gps import *
from time import *
import time
import threading
import sys

import subprocess
import urllib2
import re
import json
import serial

import traceback

import base64

####################
# Global Variables #
####################

teamname = "Team Insoma"  # Change value to reflect your team name

# Telstra VM Server Info
TelstraVMServerUrl = "http://58.162.144.156/api/position"  # Target M2M server for JSON upload
DELAY = 6 # Seconds. Delay between GPS fixes.
uploadfreq = 6 #Sets upload rate = (DELAY*uploadfreq) after JSON post.
uploadcounter = uploadfreq
gpsd = None #seting the global variable
#For the serial port
serial_USB = "/dev/ttyACM"+str(input("port:ttyACM")) #USB serial interface on Rasp
baud_rate = 9600
serial_delay = 1 # Second(e) between reloading serail value
serialPort = None # Port with in the scope of program
serial_th = None # Polling thread
outFile = "AccData.txt"
dispfra = []
upload_length  = 0

############3##############
# Code set up GPS thread #
##########################
# Written by Dan Mandle http://dan.mandle.me September 2012
# License: GPL 2.0

class GpsPoller(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    global gpsd #bring it in scope
    gpsd = gps(mode=WATCH_ENABLE) #starting the stream of info
    self.current_value = None
    self.running = True #setting the thread running to true

  def run(self):
    global gpsd
    while gpsp.running:
      gpsd.next() #this will continue to loop and grab EACH set of gpsd info to clear the buffer


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
        self.flush = False #flush data


    def run (self):
        global serialPort
        global dispfra
        global upload_length
        while serial_th.running :
            dispfra.append(GetDisplace())


######################################################
# Code to handle uploading collected data to servers #
######################################################

def UploadJsonTelstraVM(targetUrl, latitude, longitude, timedateUTC, cpuID, displayString, cpuTEMP, dispfra):
    """Uploads data via Json POST to Telstra VM Server"""
    print "[ -- ] Posting data to Telstra VM Server"
    arbitraryText = "UTC Timestamp is " + str(timedateUTC)
    #print "       DisplayString:", str(displayString), " ArbitraryText:", str(arbitraryText)
    #print "       Posting GPS coordinates lat:", str(latitude), "and long:", str(longitude)
    #print "       cpuID:", str(cpuID)
    postdata = json.dumps({
                    "cpuID":str(cpuID),
                    "displayString": str(displayString),
                    "latitude": str(latitude),
                    "longitude": str(longitude),
                    "arbitraryText": str(arbitraryText),
                    "displacement": str(dispfra)
    })
    headers = {"Content-Type": "application/json"}
    print "     URL: ", targetUrl
    print "     Headers: ", headers
    print "     Body: ", postdata
    req = urllib2.Request(targetUrl, postdata, headers)
    req.get_method = lambda: 'POST'
    response = urllib2.urlopen(req)
    UploadResult = response.getcode()
    if UploadResult == 200:
        print "[ OK ] Upload Successful"
    else:
        print "[FAIL] Upload HTTP Error", UploadResult
    return UploadResult


########################
# Code to extract time #
########################

def getTimeUTC(r):
    """Extract time from GPS response and format for transmission to server"""
    #print "Extracting time from response"
    # Example Time: 2015-04-09T06:46:05.640Z
    z =  re.search('(\d+)-(\d+)-(\d+)T([\:\:\d]+)', r)

    if not z:
        return None
    else:
        # Now convert.
        yearUTC = z.group(1)
        monthUTC = z.group(2)
        dayUTC = z.group(3)
        timeUTC = z.group(4)
        timedateUTC = str(yearUTC) + "-" + str(monthUTC)  + "-" + str(dayUTC) + " " + str(timeUTC)
        # Example timedateUTC = 2015-04-09 06:46:05
        return timedateUTC

		
##########################################################
# Code to extract and format CPU ID information from Pi  #
##########################################################
	
def GetCPUid():
    """Queries Raspberry Pi for its unique CPU ID"""
    commandoutput = subprocess.Popen(["/bin/cat", "/proc/cpuinfo"], stdout=subprocess.PIPE)
    commandresult = commandoutput.communicate()[0]
    z =  re.search('Serial\s+\:\s+(.*)$', commandresult, re.MULTILINE)
    if z:
        #print ' CPU ID: ', z.group(1)
        return z.group(1)
    else:
        print '[FAIL] Unable to get CPU ID'
        return 0

def GetCPUtemp():
    """Queries Raspberry Pi for its unique CPU ID"""
    commandoutput = subprocess.Popen(["vcgencmd", "measure_temp"], stdout=subprocess.PIPE)
    commandresult = commandoutput.communicate()[0]
    z =  re.search('temp=([\.\d]+)', commandresult, re.MULTILINE)
    if z:
        #print ' CPU Temp: ', z.group(1)
        return z.group(1)
    else:
        print '[FAIL] Unable to get CPU ID'
        return 0


##########################################################
# Code to get one basic displacement from sensor on Pi   #
##########################################################
def GetDisplace():
    global serial_delay
    global serial_th
    accData = []
    try:
        serialPort.flushInput()
        serialPort.write("start")
        if serialPort.readline() == "ready\r\n":
            d = serialPort.readline()
            #print dprint
            return d
    except:
        print "ooooooops,GetDisplace gone wrong"
#############################################
# Main program loop with exception handlers #
#############################################

def main():
  global uploadcounter
  global uploadfreq
  global gpsp
  global serial_th
  global dispfra
  print '[ -- ] Starting Telstra University Challenge GPS Client 2015'
  print '[ -- ] Creating GPS Poller Thread'
  gpsp = GpsPoller() # create the thread
  serial_th = SerialPoller() #Creat the thread instance
  try:
    gpsp.start() # start it up
    #time.sleep(10) #It may take a second or two to get good data
    serial_th.start()
    while True:
      #os.system('clear') #optional
      latitude = gpsd.fix.latitude
      longitude = gpsd.fix.longitude
      #latitude = "nan"
      #longitude = "nan"

      timedateUTC = getTimeUTC(gpsd.utc)
      cpuID = GetCPUid()
      cpuTEMP = GetCPUtemp()
      print "creating a thread"
      print '----------------------------------------'
      print '[    ]', teamname, ' Time UTC:', timedateUTC
      print '[    ] CPU ID:', cpuID, ' CPU Temp:', cpuTEMP
      print '[    ] Latitude:', str(latitude), ' Longitude:', str(longitude), ' Altitude (m):', gpsd.fix.altitude
      #print '[    ] eps', gpsd.fix.eps
      #print '[    ] epx', gpsd.fix.epx
      #print '[    ] epv', gpsd.fix.epv
      #print '[    ] ept', gpsd.fix.ept
      print '[    ] Speed (m/s):', gpsd.fix.speed, ' Climb:', gpsd.fix.climb
      print '[    ] Track', gpsd.fix.track
      print '[    ] Mode', gpsd.fix.mode
      #print ' '
      ##print '[    ] Sats', gpsd.satellites
      print '[    ] Satellites (total of', len(gpsd.satellites) , ' in view)'
      #print '[    ] Accelerate:', str(dispfra)
      #for i in gpsd.satellites:
      #    print '\t', i
      print uploadcounter
      if uploadcounter >= uploadfreq:
        if (str(latitude) == "nan") or (str(longitude) == "nan") or (latitude < 1):
            print '[ -- ] No GPS fix so don''t upload GPS'
            upload_length = len(dispfra)
            #print "uplen", upload_length
            try:
              print len(dispfra)
              UploadJsonTelstraVM(TelstraVMServerUrl, "nan", "nan", timedateUTC, cpuID, teamname, cpuTEMP, dispfra)
              print "Flushing serial data length:",upload_length
              del dispfra[0:upload_length]
              print len(dispfra)
              upload_length = 0
            except:
              print "Error in transmit displacement"
            uploadcounter = 1
        else:
          #print '[ -- ] Upload Data' 
          serial_th.flush = True
          try:
            UploadJsonTelstraVM(TelstraVMServerUrl, str(latitude), str(longitude), timedateUTC, cpuID, teamname, cpuTEMP, 'nan')
          except urllib2.HTTPError as e:
            # Capture HTTPError errors
            print " "
            print "******************************"
            print "Exception detected (HTTPError)"
            print "Code:", e.code
            print "Reason:", e.reason
            print "******************************"
            pass
          except urllib2.URLError as e:
            # Capture URLError errors
            print " "
            print "*****************************"
            print "Exception detected (URLError)"
            print "Reason:", e.reason
            print "*****************************"
            print "[ -- ] Check Raspberry Pi and modem have assigned IP addresses"
            pass
          uploadcounter = 1
      else:
        upload_length = len(dispfra)
        #print "uplen", upload_length
        try:
          print len(dispfra)
          if (str(latitude) == "nan") or (str(longitude) == "nan") or (latitude < 1):
              UploadJsonTelstraVM(TelstraVMServerUrl, "nan", "nan", timedateUTC, cpuID, teamname, cpuTEMP, dispfra)
          print "Flushing serial data length:",upload_length
          del dispfra[0:upload_length]
          print len(dispfra)
          upload_length = 0
        except:
          print "Error in transmit displacement"
        uploadcounter = uploadcounter + 1
        time.sleep(DELAY)
        continue
	  

  except OSError as e:
    # Capture OS command line errors
    print " "
    print "****************************"
    print "Exception detected (OSError)"
    print "****************************"
    print e.errno
    print e.filename
    print e.strerror
    traceback.print_exc(file=sys.stdout)
    print "****************************"
    gpsp.running = False
    gpsp.join(30) # wait for the thread to finish what it's doing
    if gpsp.is_alive():
        gpsp.run = False
        print "Warning Timeout unable to join to gpsp thread"
        # Reset the gpsd
        os.system('sudo killall gpsd') 
        time.sleep(1)
        os.system('sudo gpsd /dev/ttyUSB0 -F /var/run/gpsd.sock')
        time.sleep(1)
    print "Done.\nExiting."
    sys.exit()
  except Exception as e:
    print " "
    print "******************"
    print "Exception detected"
    print "******************"
    print type(e)
    print e
    traceback.print_exc(file=sys.stdout)
    print "******************"
    gpsp.running = False
    gpsp.join(30) # wait for the thread to finish what it's doing
    if gpsp.is_alive():
        gpsp.run = False
        print "Warning Timeout unable to join to gpsp thread"
        # Reset the gpsd
        os.system('sudo killall gpsd')
        time.sleep(1)
        os.system('sudo gpsd /dev/ttyUSB0 -F /var/run/gpsd.sock')
        time.sleep(1)
    print "Done.\nExiting."
    sys.exit()
  except KeyboardInterrupt:
    print " "
    print "******************************"
    print "Exception (Keyboard Interrupt)"
    print "******************************"
    print "Killing Thread..."
    gpsp.running = False
    gpsp.join(30) # wait for the thread to finish what it's doing
    if gpsp.is_alive():
        gpsp.run = False
        print "Warning Timeout unable to join to gpsp thread"
        # Reset the gpsd
        os.system('sudo killall gpsd')
        time.sleep(1)
        os.system('sudo gpsd /dev/ttyUSB0 -F /var/run/gpsd.sock')
        time.sleep(1)
    print "Done.\nExiting."
    sys.exit()
  except:
    print " "
    print "*******************"
    print "Exception (Unknown)"
    print "*******************"
    traceback.print_exc(file=sys.stdout)
    print "*******************"
    print "Killing Thread..."
    gpsp.running = False
    gpsp.join(30) # wait for the thread to finish what it's doing
    if gpsp.is_alive():
        gpsp.run = False
        print "Warning Timeout unable to join to gpsp thread"
        # Reset the gpsd
        os.system('sudo killall gpsd')
        time.sleep(1)
        os.system('sudo gpsd /dev/ttyUSB0 -F /var/run/gpsd.sock')
        time.sleep(1)
    print "Done.\nExiting."
    sys.exit()

if __name__ == "__main__":
    main()

