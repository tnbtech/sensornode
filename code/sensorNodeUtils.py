'''


    SensorNode Utilities
    
    
'''
from microcontroller import watchdog as wdt
from watchdog import WatchDogMode
import json
from microcontroller import cpu as micro_cpu
import digitalio
import board
import time
import wifi
from microcontroller import reset as micro_reset

from globals import SETTINGS_FILE,WIFI_RECONNECT_TRIES,START_UP_MODE_DEFAULT
#
#	Global Variables - avail for use by all modules
#
watchDogIsRunning = False
settingsStruct = {}
sensornodeDeviceName = "unknown"
pico_AP_SSID = "unknown"
pico_ID_Short = "unknown"
pico_ID = "unknown"
htmlBuffer = "NOT INITIALIZED"
PICO_UID_BASE = "SN-2-"
AP_SSID_BASE = "SensorNode-"
WIFI_SSID = None
WIFI_PW = None
sleJumperEnables = None
report_counts = False


#	on-board led

onBoardLed = digitalio.DigitalInOut(board.LED)
onBoardLed.direction = digitalio.Direction.OUTPUT

#	External Status LED enable switch
#
#	GPIO 11 - Status LED Enable Input
#	Actuate switch to enable Status LED(s) based upon value of SLE_JUMPER_ENABLES
#
status_led_enable = digitalio.DigitalInOut(board.GP11)
status_led_enable.switch_to_input(pull=digitalio.Pull.UP)
#
#	External Status LED Pin
#
#	GPIO 9 - Drive this pin LOW to turn ON external status LED

status_led = digitalio.DigitalInOut(board.GP9)
status_led.direction = digitalio.Direction.OUTPUT

#
#	FORCE AP MODE START
#	
#	GPIO pin to force start in AP mode - allows user to change settings even if wifi creds are present
#
#	GPIO 13 - Pull this pin LOW to FORCE into AP Mode
#

force_AP_mode_pin = digitalio.DigitalInOut(board.GP13)
force_AP_mode_pin.switch_to_input(pull=digitalio.Pull.UP)

#
#	Watchdog timer enable - uses pin 16 to control
#
#
#	When enabled, watchdog will reboot pico if not fed every 8 seconds
#	To enable watchdog timer, GPIO Pin 16 must be pulled LOW
#
#
#
#	GPIO 16 - Pull this pin LOW to ENABLE WDT
#
wd_enable = digitalio.DigitalInOut(board.GP16)
wd_enable.switch_to_input(pull=digitalio.Pull.UP)

#
#	GPIO 14 - FSW Pin - Must be pulled DOWN to write to NV storage on Pico
#
switch = digitalio.DigitalInOut(board.GP14)
switch.direction = digitalio.Direction.INPUT
switch.pull = digitalio.Pull.UP

def getBoolSetting(settingName,settingDefault,jsonSettingData):
    #
    #	establishes boolean setting from setting file or default
    #
    settingText = getSettingValueFromSettingsJson(jsonSettingData,settingName)
    if settingText == None:
        settingBoolValue = settingDefault
    elif settingText == "False":
        settingBoolValue = False
    else:
        settingBoolValue = True
    return settingBoolValue

def getReportCounts():
    global report_counts
    return report_counts

def setReportCounts(setting):
    global report_counts
    report_counts = setting

def turnOnWatchDogIfEnabled():
    #
    #	Look at wd_enable pin (GPIO 16) and turn on wdt if enabled
    #
    global watchDogIsRunning
    if not wd_enable.value:
        turnOnWatchDog()
        wd_feed()
    else:
        watchDogIsRunning = False
        print("\nwatchdog timer disabled\n")

def getStoredErrorCountValues(struct):
    #
    #	used to read error and count values from settings json in stored memory to survive restarts
    #
    wifiErrors = getSettingValueFromSettingsJson(struct,'WIFI_ERROR_COUNT',0)
    sendDataErrors = getSettingValueFromSettingsJson(struct,'SEND_DATA_ERRORS',0)
    sendDataCount = getSettingValueFromSettingsJson(struct,'SEND_DATA_COUNT',0)
    return wifiErrors,sendDataErrors,sendDataCount

def getSleJumperEnables():
    global sleJumperEnables
    return sleJumperEnables

def setSleJumperEnables(value):
    global sleJumperEnables
    sleJumperEnables = value

def getWifiSSID():
    global WIFI_SSID
    return WIFI_SSID

def getWifiPW():
    global WIFI_PW
    return WIFI_PW

def getPicoID():
    global pico_ID
    return pico_ID

def setPicoID(value):
    global pico_ID
    pico_ID = value

def getPicoIdShort():
    global pico_ID_Short
    return pico_ID_Short

def setPicoIdShort(value):
    global pico_ID_Short
    pico_ID_Short = value

def connectToWifi(ssid,pw):
    print()
    print("Connecting to WiFi...")
    print("ssid: ",ssid,", pw: ",pw)
    wd_feed()
    #wifi.radio.start_station()
    wifi.radio.hostname = "sensornode"
    try:
        wifi.radio.connect(ssid,pw)
    except Exception as e:
        print("\nCannot connect to wifi - exception: ",e)
        return -1,None
    else:
        print("wifi connected - done w wifi connect")
    wd_feed()
    
    #pool = socketpool.SocketPool(wifi.radio)

    print("My MAC addr: ",[hex(i) for i in wifi.radio.mac_address])

    myIpAddress = wifi.radio.ipv4_address
    print("My IP address: ",myIpAddress)

    return 0,myIpAddress

def wifi_reconnect(ssid,pw):
    #
    #	attempts to connect to wifi WIFI_RECONNECT_TRIES times
    # 	if successful returns 0
    #	if fail returns -1
    #
    # will retry this many times before signalling failure
    if ssid == None or pw == None:
        # do not attempt if either ssid or pw is none
        return -1,None
    retry_number = 0
    wifi_success = False
    ipAd = None
    while retry_number < WIFI_RECONNECT_TRIES and wifi_success == False:
        wd_feed()
        print("WiFi Connect Attempt #",retry_number)
        try:
            status,ipAd = connectToWifi(ssid,pw)
        except:
            print("\n\n---> ERROR cannot connect to Wifi\n\n")
            wd_feed()
        else:
            if wifi.radio.connected and status == 0:
                wifi_success = True
        retry_number += 1
    # try one last time
    wd_feed()
    if wifi_success == False:
        wd_feed()
        print("Trying wifi access one last time...")
        try:
            status,ipAd = connectToWifi(ssid,pw)
        except:
            print("ERROR attempting to connect to wifi last time - rebooting into ap mode")
            return -1,None
        else:
            wd_feed()
            if not wifi.radio.connected or status == -1:
                print("\n\n---> ERROR cannot connect to Wifi - Going into Access Point Mode...\n\n")
                return -1,None
            else:
                return 0,ipAd
    else:
        return 0,ipAd


def getForceAPModePinValue():
    return force_AP_mode_pin.value

def isAPModeRequired():
    #
    #	determines if it's necessary to restart into access point mode or not
    #	returns TRUE if AP mode restart is required, otherwise returns  FALSE
    #
    global WIFI_SSID,WIFI_PW
    wd_feed()
    status,ssid,pw,startUpMode = getWifiCreds()
    print("After getWifiCreds - status = ",status,", ssid = ",ssid,", pw = ",pw,", startUpMode = ",startUpMode)
    WIFI_SSID = ssid
    WIFI_PW = pw
    if startUpMode == None:
        startUpMode = START_UP_MODE_DEFAULT
    if status == -1:
        wd_feed()
        print("\n\n---> ERROR cannot find credentials - Going into Access Point Mode...\n")
        return True,None,None
    elif startUpMode == 'ap':
        print("\n\nDetected StartUpMode = 'ap' - going into access point mode...\n")
        return True,None,None
    else:
        #
        #	Detected Wifi creds AND startUpMode set to 'station'
        #
        #	Check force_ap_mode_pin to see if should force into AP mode
        #	If pin is pulled LOW - then pico will go into AP mode ALWAYS
        #
        if getForceAPModePinValue() == False:
            print("\n\nDetected FORCE AP MODE pin is ACTIVE - going into AP mode...\n\n")
            return True,None,None
        else:
            print("\nFound Credentials - Attempting to connect to wifi...\n")
            print("ssid: ", ssid,", pw: ",pw)
            return False,ssid,pw
        
def updateCountSetting(setting,value):
    # writes new number into json setting - used to update diagnostic counts
    newSettingValue = {setting : value}
    if switch.value == False:
        try:
            writeSettingsFile(newSettingValue)
        except:
            print("\n\n---> ERROR in update Count Setting - cannot write to settings file\n\n")
    else:
        print("---> Alert: FSW Pin is HIGH - cannot write to NV Storage - ignoring.")

def writeSettingsFile(newJsonStruct):
    #
    #	stores new settings in settings.json to survive after reboot
    # 	returns 0 if no error, -1 if failed
    #
    wd_feed()
    print("Inside write settings file")
    print("New settings json:\n",newJsonStruct,"\n")

    # first read already-stored values

    status,oldSettingsJson = readSettingsFile(SETTINGS_FILE)
    if status == 0:
        print("\nOld settings json:\n",oldSettingsJson,"\n")
        # got settings file
        # go through old settings and add them into new settings struct if no new setting found for that element
        for item in oldSettingsJson:
            if not item in newJsonStruct:
                newJsonStruct[item] = oldSettingsJson[item]
            else:
                if newJsonStruct[item] == None:
                    # if None then replace with old item
                    newJsonStruct[item] = oldSettingsJson[item]
        print("\nAbout to write settings file...")
        print("\njsonData to be written to file: \n",newJsonStruct)
        #dummy = input("hit CR to write data to settings file: ")
        wd_feed()
        try:
            with open(SETTINGS_FILE,"w") as f:
                json.dump(newJsonStruct,f)
                f.close
        except Exception as e:
            print("\n\n---> ERROR in writeSettingsFile - exception: ",e,"\n\n")
            setLeds(True)
            return -1
        else:
            print("completed.")
            return 0
    else:
        print("\nCannot find settings file - aborting...\n")
        return -1
    
def restartPico():
    # this stmt will restart system immediately
    print("\n\nRESTARTING PICO IN 10 SEC\n\n")
    # if not watchdog timer (if enabled) should reboot pico now
    time.sleep(10)
    micro_reset()


def restartIntoStationMode():
    #
    #	sets start up mode env variable to 'station' and restarts pico
    #
    # set json setting for statup mode to 'station'
    errorStatus = writeDataToSettings()
    print("\n\n---> Inside restartIntoStationMode - restarting system...\n\n")
    restartPico()

def restartIntoAPMode():
    #
    #	sets start up mode env variable to 'ap' and restarts pico
    #
    # update creds file with startUpMode = 'ap'
    errorStatus = writeDataToSettings('ap')
    restartPico()

def writeDataToSettings(startUpMode='station',dataStruct={}):
    #
    #	writes dataStruct to settings json file while keeping watchdog timer fed
    #
    #	returns error = false if everything is ok
    #
    #	returns error = true if fails
    #
    error = False
    wd_feed()
    print("\nInside writeDataToSettings...")
    # add in station or ap mode to startup next time in - default is station
    dataStruct['startUpMode'] = startUpMode
    print("dataStruct: ",dataStruct)
    try:
        status = writeSettingsFile(dataStruct)
        #writeCredsFile(ssidValue,pwValue,nameValue,'station')
    except:
        wd_feed()
        print("\n\n---> ERROR writeSettingsFile failed.\n\n")
        error = True
    else:
        wd_feed()
        if status != 0:
            error = True
    return error

def countLedTicks(counter,initialTickValue):
    #
    #	counts down led ticks - when reaches zero, toggles led and keeps wd petted
    #
    #print("Inside countLedTicks...counter = ",counter,", initialTickValue = ",initialTickValue)
    wd_feed()
    counter -= 1
    if counter <= 0:
        toggleLed(onBoardLed)
        counter = initialTickValue
    return counter

class Timer:
    def __init__(self):
        # defaults to 1 hr if not set otherwise
        wd_feed()
        self.timerStartTime = time.time()
        self.timeDelay = 3600
        
    def setTimeDelay(self,timeInSecs):
        # timer time delay in secs
        self.timeDelay = timeInSecs
        
    def clearTimer(self):
        # sets start of timer to current time
        wd_feed()
        self.timerStartTime = time.time()
    
    def isItTime(self):
        # checks to see if timeDelay has elapsed since timerStartTime and returns True if so else returns False
        wd_feed()
        if time.time() - self.timerStartTime >= self.timeDelay: return True
        else: return False

def getWifiCreds():
    #
    #	gets credentials from stored file
    #	if no creds, returns NONE
    #
    wd_feed()
    if WIFI_SSID == None and WIFI_PW == None:
        #print("\nCannot Find Wifi Creds in Constants\n")
        ssid = None
        pw = None
        startUp = None
        #
        #	check SETTINGS_FILE
        #
        wd_feed()
        status,dataJson = readSettingsFile(SETTINGS_FILE)
        if status == 0:
            ssid = getParam(dataJson,'ssid')
            pw = getParam(dataJson,'pw')
            startUp = getParam(dataJson,'startUpMode')

        if ssid == None or pw == None:
            #
            #	can't find creds - return error
            #
            return -1,None,None,startUp
        else:
            #
            #	found them so return them
            #
            return 0,ssid,pw,startUp
    #
    #	Use defined constants for now
    #
    else:
        return 0,WIFI_SSID,WIFI_PW,START_UP_MODE_DEFAULT

def setLeds(ledSetting=False):
    sle_jumper_enables = getSleJumperEnables()
    # turns ON enabled Leds
    # status led enable is LOW TRUE
    if status_led_enable.value == False:
        if sle_jumper_enables == "INT" or sle_jumper_enables == "BOTH":
            onBoardLed.value = ledSetting
        else:
            onBoardLed.value = False
        if sle_jumper_enables == "EXT" or sle_jumper_enables == "BOTH":
            status_led.value = not ledSetting
        else:
            status_led.value = True
    else:
        onBoardLed.value = False
        status_led.value = True
    
def toggleLed(led):
    # toggles LED based upon value of status_led_enable jumper and sle_jumper_enables
    if status_led_enable.value == False:
        # pull down jumper will ENABLE leds according to sle_jumper_enables when present
        if onBoardLed.value == True or status_led.value == False:
            setLeds(False)
        else:
            setLeds(True)
    else:
        setLeds(False)

def getPicoUID():
    #
    #	forms unique id for pico
    #
    myMac = micro_cpu.uid
        
    myID = ""
    
    for index in range(len(myMac)):
        myID += str(myMac[index])
            
    myUniqueId = PICO_UID_BASE+myID
    myShortID = myUniqueId[len(myUniqueId)-4:]
    
    return myUniqueId,myShortID

def getAPSSID():
    #
    #	forms unique id for pico ap
    #
    myMac = micro_cpu.uid
        
    myUniqueId = ""
    for index in range(len(myMac)):
        myUniqueId += str(myMac[index])
            
    newAPssid = AP_SSID_BASE+myUniqueId
    
    return newAPssid

def getIntFromString(inputString):
    #
    #	attempts to get int value from string
    #	if not possible, return None
    #
    intValue = None
    try:
        intValue = int(inputString)
    except:
        print("---> ERROR in getIntFromString -  value NOT an integer! Setting to None...")
        intValue = None
    else:
        intValue = int(inputString)
    return intValue

def checkValue(value):
    #
    #	checks for legal value
    #
    if value != None and value != '' and value != ' ':
        return True
    else: return False

def getHtmlBuffer():
    global htmlBuffer
    return htmlBuffer

def setHtmlBuffer(buffer):
    global htmlBuffer
    htmlBuffer = buffer

def setPicoAPSSID(apId):
    global pico_AP_SSID
    pico_AP_SSID = apId

def getPicoAPSSID():
    global pico_AP_SSID
    return pico_AP_SSID

def getSensorNodeDeviceName():
    global sensornodeDeviceName
    return sensornodeDeviceName

def setSensorNodeDeviceName(name):
    global sensornodeDeviceName
    sensornodeDeviceName = name

def addToSettingsStruct(prop,value):
    tempStruct = getSettingsStruct()
    tempStruct[prop] = value
    setSettingsStruct(tempStruct)

def getSettingsStruct():
    global settingsStruct
    return settingsStruct

def setSettingsStruct(struct):
    global settingsStruct
    settingsStruct = struct

def getParam(jsonStruct,paramName):
    #
    #	looks through json to find paramName, if found returns it
    #	if not returns None
    #
    parameter = None
    if paramName in jsonStruct:
        retreivedParam = jsonStruct[paramName]
        #print("Inside getParam - retreivedParam = ",retreivedParam)
        if retreivedParam != "" and retreivedParam != " ":
            #print("returning retreivedParam = ",retreivedParam)
            parameter = retreivedParam
    return parameter

def getSettingValueFromSettingsJson(settingJson,settingName,settingDefaultValue=None):
    #
    #	looks in settingJson struct for settingName, and if it finds corresponding value, returns it
    #	if settingName is not there, then it returns settingDefaultValue instead
    #
    settingValue = getParam(settingJson,settingName)
    if settingDefaultValue == None:
        return settingValue
    elif settingValue != None:
        return settingValue
    else:
        return settingDefaultValue

def turnOnWatchDog():
    global watchDogIsRunning
    print("\n\nWATCHDOG TIMER IS ENABLED\n\n")
    wdt.timeout = 8
    wdt.mode = WatchDogMode.RESET
    watchDogIsRunning = True

def getWatchDogIsRunning():
    global watchDogIsRunning
    return watchDogIsRunning


def wd_feed():
    global watchDogIsRunning
    if watchDogIsRunning:
        wdt.feed()

def readSettingsFile(filename):
    #
    #	reads settings from disk for use
    #
    wd_feed()
    try:
        with open(filename,"r") as f:
            jsonData = json.load(f)
            f.close
    except:
        wd_feed()
        print("\n\n---> ERROR cannot read SETTINGS_FILE\n\n")
        return -1,None
    else:
        wd_feed()
        print("\n\nRead Json Data from disk")
        print("jsonData: ",jsonData)
        return 0,jsonData