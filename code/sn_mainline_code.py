'''


    SensorNode Mainline Code
    
    TNB Technologies, LLC
    
    Tom Berarducci
    
'''

from globals import homeAssistantUrl,VERSION,HA_MOTION_SENSOR_NAME_DEFAULT,MOTION_SENSOR_ENABLED_DEFAULT,HTTP_TIMEOUT,STATUS_UPDATE_INTERVAL_MINIMUM,STATUS_UPDATE_INTERVAL_MAXIMUM
from globals import MOTION_SENSOR_ACTIVE_DURATION_DEFAULT,MOTION_SENSOR_ACTIVE_DURATION_MINIMUM,HA_CONTACT_SENSOR_NAME_DEFAULT,WIFI_CHECK_ENABLE_DEFAULT
from globals import CONTACT_SENSOR_ENABLED_DEFAULT,CONTACT_SENSOR_CLOSED_DURATION_DEFAULT,CONTACT_SENSOR_CLOSED_DURATION_MINIMUM,STATUS_UPDATE_INTERVAL_DEFAULT
from globals import AP_PW, WIFI_RETRY_DURATION,HA_S2_TEMP_SENSOR_NAME_DEFAULT,S2_TEMP_SENSOR_ENABLED_DEFAULT,HA_S2_WATER_SENSOR_NAME_DEFAULT
from globals import S2_WATER_SENSOR_ENABLED_DEFAULT,S2_WATER_SENSOR_ACTIVE_DURATION_DEFAULT,S2_WATER_SENSOR_ACTIVE_DURATION_MINIMUM,S2_TEMP_SENSOR_MIN_SAMPLING_INTERVAL
from globals import STATUS_UPDATE_ACTIVE_DURATION_DEFAULT,LED_BLINK_DURATION_WD_ENABLED,LED_BLINK_DURATION_WD_DISABLED
from globals import INTERNET_CONNECTIVITY_CHECK_DURATION,WAIT_TIME_TICK,SENSORNODE_TYPE,S2_SENSOR_TYPE_DEFAULT,S2_TEMP_SENSOR_SAMPLING_INTERVAL_DEFAULT

import adafruit_ahtx0
import adafruit_requests
from sensorNodeUtils import wifi_reconnect,getSettingValueFromSettingsJson,getSleJumperEnables,Timer,getPicoIdShort,wd_feed,getPicoID,getSensorNodeDeviceName,getBoolSetting
from sensorNodeUtils import getWifiSSID,getWifiPW,countLedTicks,turnOnWatchDog,updateCountSetting,getWatchDogIsRunning,getReportCounts, restartIntoStationMode,restartIntoAPMode
import gc
import board
import digitalio
import socketpool
import wifi
import ssl
import time
import ipaddress
import busio

ANALOG_SENSOR_MAX_UPDATE_INTERVAL = 300		# max amt of time (secs) between updates for analog sensors (e.g. temp, humidity) to HA

#******************************************* I2C bus peripherals ******************************************

#****************************************** I2C INTERNAL TEMP,HUMIDITY SENSORS ********************************
#
#	Currently the only I2C peripherals supported are AHT20 temp and humidity sensors
#

TEMP_HUMID_UPDATE_ENABLED_DEFAULT = True

TEMP_HUMID_MAX_UPDATE_INTERVAL = ANALOG_SENSOR_MAX_UPDATE_INTERVAL		# even if readings do not change, sensor values will send updates to HA this often

TEMP_HUMID_SAMPLING_INTERVAL = 60		# how often we look at these sensors (sec)

INTERNAL_TEMP_SENSOR_URL_SUFFIX_BASE = "sensor.internal_temperature_"

INTERNAL_TEMP_SENSOR_NAME_DEFAULT = "I2C Temperature"

INTERNAL_HUMID_SENSOR_URL_SUFFIX_BASE = "sensor.internal_humidity_"

INTERNAL_HUMID_SENSOR_NAME_DEFAULT = "I2C Humidity"

INTERNAL_TEMP_VARIANCE_MIN = 0.5

INTERNAL_HUMID_VARIANCE_MIN = 0.5

#******************************************* Sensor Enables ***********************************************
#
#	By default, all sensors are DISABLED. To enable them, you must boot up into Access point mode and set the appropriate settings in the
#	sensornode settings webpage by attaching your phone to the sensornode AP wifi.
#	Optionally, you can change the default settings below from False to True for each sensor you want to enable
#
#	NOTE: If optional power monitor installed, it must be enabled explicity by pulling POWER_MONITOR_PRESENT_LOW low on board (see below)
#
#*************************************** SensorNode DEFINES ***********************************************

SENSORNODE_ACTIVE_VALUE_DEFAULT = "on"

SENSORNODE_ONLINE_VALUE_DEFAULT = "online"

SENSORNODE_CLOSED_DURATION_DEFAULT = 2		# number of secs sensor will remain closed for HA

SENSORNODE_URL_SUFFIX_BASE = "binary_sensor.sensornode_"		# this will be appended to end of URL

SENSORNODE_NAME_DEFAULT = "not set"	# this will be the friendly name for HA

#*************************************** S2 MOTION SENSOR DEFINES ***********************************************

MOTION_SENSOR_INACTIVE_VALUE_DEFAULT = "off"

MOTION_SENSOR_ACTIVE_VALUE_DEFAULT = "on"

MOTION_SENSOR_ONLINE_VALUE_DEFAULT = "online"

HA_MOTION_SENSOR_URL_BASE = "binary_sensor.motion_"		# this will be appended to end of URL

MOTION_SENSOR_ACTIVE_BOOLEAN_LEVEL = False				# when motion is detected, this value is sent to HA to indicate 'on'

MOTION_SENSOR_INACTIVE_BOOLEAN_LEVEL = True

#*************************************** S2 WATER SENSOR DEFINES ***********************************************

S2_WATER_SENSOR_INACTIVE_VALUE_DEFAULT = "off"

S2_WATER_SENSOR_ACTIVE_VALUE_DEFAULT = "on"

S2_WATER_SENSOR_ONLINE_VALUE_DEFAULT = "online"

HA_S2_WATER_SENSOR_URL_BASE = "binary_sensor.water_"		# this will be appended to end of URL

S2_WATER_SENSOR_ACTIVE_BOOLEAN_LEVEL = True				# when water is detected, this value is sent to HA to indicate 'on'

S2_WATER_SENSOR_INACTIVE_BOOLEAN_LEVEL = False

#*************************************** S2 TEMP SENSOR DEFINES ***********************************************

S2_TEMP_SENSOR_ONLINE_VALUE_DEFAULT = "online"

S2_TEMP_SENSOR_MAX_UPDATE_INTERVAL = ANALOG_SENSOR_MAX_UPDATE_INTERVAL			# Even if temp does not change, sensor will update this often (secs)

HA_S2_TEMP_SENSOR_URL_BASE = "sensor.s2_temperature_"

S2_TEMP_SENSOR_VARIANCE_MIN = 0.5						# Dynamic updates will only occur if temp reading varies by this much (fahrenheit)

#*************************************** Dry CONTACT SENSOR DEFINES ***********************************************

CONTACT_SENSOR_INACTIVE_VALUE_DEFAULT = "off"

CONTACT_SENSOR_ACTIVE_VALUE_DEFAULT = "on"

CONTACT_SENSOR_ONLINE_VALUE_DEFAULT = "online"

HA_CONTACT_SENSOR_URL_BASE = "binary_sensor.contact_"	# this will be appended to end of URL

CONTACT_SENSOR_ACTIVE_BOOLEAN_LEVEL = False				# when contact is active, this value is sent to HA to indicate 'on'

CONTACT_SENSOR_INACTIVE_BOOLEAN_LEVEL = True


#****************************************** Sensor S1 -Dry Contact Sensor - Latch ****************************************************
#
#	S1 Sensor - Contact Closure LATCH - captures state of sensor S1 (dry contact only) using f/f
#
#	NOTE: Dry Contact sensor S1 must be configured and enabled using web-server AP settings screen
#
#	GPIO 15 - Pull this pin LOW to indicate contact closure has been registered by the D-Type F/F
#

contact_sensor_latch_Q = digitalio.DigitalInOut(board.GP15)
contact_sensor_latch_Q.switch_to_input(pull=digitalio.Pull.UP)

#
#	Sensor - Contact Closure RAW value
#
#	GPIO 10 - this pin is attached directly to sensor term block pulled LOW - will be pulled HIGH when sensor is closed
#
#	if LEVEL sensing - then this pin tells state of the contact directly
#
contact_sensor_direct = digitalio.DigitalInOut(board.GP10)
contact_sensor_direct.switch_to_input(pull=digitalio.Pull.DOWN)

#
#	Sensor Input Latch Control Pins
#
#	Sensor Input Latch RESET
#
#	GPIO 12 - OUTPUT - Set this pin to HIGH to RESET/CLEAR Sensor Input Latch F/F Q pin
#
contact_sensor_latch_reset = digitalio.DigitalInOut(board.GP12)
contact_sensor_latch_reset.direction = digitalio.Direction.OUTPUT
#
#	Sensor Input Latch SET
#
#	GPIO 17 - OUTPUT - Set this pin to HIGH to SET Sensor Input LATCH Flip-Flop Q pin
#
contact_sensor_latch_set = digitalio.DigitalInOut(board.GP17)
contact_sensor_latch_set.direction = digitalio.Direction.OUTPUT
#
#****************************************************************************************************************

#****************************************** Sensor S2 Latch ****************************************************
#
#	S2 Sensor - Connector S2 output LATCH - captures state of sensor S2 output using f/f
#
#	NOTE: Currently, connector S2 can host ONE of THREE possible sensors: Motion, Water, or Temperature, depending upon configuration
#
#	Sensor must be configured and enabled using web-server AP settings screens
#
#	GPIO 28 - Pull this pin LOW to indicate contact closure has been registered by the D-Type F/F
#

s2_sensor_latch_Q = digitalio.DigitalInOut(board.GP28)
s2_sensor_latch_Q.switch_to_input(pull=digitalio.Pull.UP)

#
#	Sensor Input Latch Control Pins
#
#	Sensor Input Latch RESET
#
#	GPIO 27 - OUTPUT - Set this pin to HIGH to RESET/CLEAR Sensor Input Latch F/F Q pin
#
s2_sensor_latch_reset = digitalio.DigitalInOut(board.GP27)
s2_sensor_latch_reset.direction = digitalio.Direction.OUTPUT
#
#	Sensor Input Latch SET
#
#	GPIO 26 - OUTPUT - Set this pin to HIGH to SET Sensor Input LATCH Flip-Flop Q pin
#
s2_sensor_latch_set = digitalio.DigitalInOut(board.GP26)
s2_sensor_latch_set.direction = digitalio.Direction.OUTPUT
#
#****************************************************************************************************************

#
#	INPUT PWR DETECT - GPIO 18
#
#	On some boards, optional circuit to detect if power has been cut (using supercaps to maintain power for short period during outage)
#
#	GPIO 18 - this pin will be LOW if power is OUT
#

DETECT_POWER_OUTAGE = True

power_is_out_pin = digitalio.DigitalInOut(board.GP18)
power_is_out_pin.switch_to_input(pull=digitalio.Pull.DOWN)

#
#	GPIO 19 - Presence Detect for Power Monitor Ckt - if this pin is pulled LOW the circuit exists, if NOT then it doesn't
#

power_monitor_presence_detect_pin = digitalio.DigitalInOut(board.GP19)
power_monitor_presence_detect_pin.switch_to_input(pull=digitalio.Pull.UP)

POWER_MONITOR_PRESENT_LOW = power_monitor_presence_detect_pin.value

def consoleUpdate(rebootNum):
    global globalIPAddress,globalWifiErrorCount,globalSentCount,globalErrorCount,checkWifiConnectionEnabled,statusUpdatesEnabled
    #
    #	periodic status update to console
    #
    freeMem = gc.mem_free()
    if getReportCounts():
        print("\n\nFree Memory: ",freeMem," - IP Add: ",globalIPAddress," - Global Wifi Error Count = ",globalWifiErrorCount," - Global Send Data Count = ",globalSentCount," - Global Send Data Error Count = ",globalErrorCount," - Reboot Count = ",rebootNum,"\n")
    else:
        print("\n\nDIAGNOSTICS ARE OFF")
        print("\nFree Memory: ",freeMem," - IP Add: ",globalIPAddress)
    if not checkWifiConnectionEnabled:
        print("\nWIFI CHECKS DISABLED\n")
    if not statusUpdatesEnabled:
        print("\nSTATUS UPDATES DISABLED\n")

def getS2TempSensorValue(sensor,units="F"):
    #
    #	fetches latest temp
    #    
    tempC = sensor.temperature
    if units == "C":
        return tempC
    else:
        tempF = round(centigradeToFahrenheit(tempC),1)
        return tempF


def buildDataObject(base_params,specific_params):
    #
    #	takes params objects and builds them into proper attribute object to be transmitted to HA
    #
    # create return object and add base params to it
    returnObject = {
        "attributes":{
            "unique_id":base_params["unique_id"],
            "firmware_version":base_params["firmware_version"],
            "name":base_params["name"],
            }
        }
    # add required items
    returnObject["state"] = specific_params["state"]
    returnObject["attributes"]["friendly_name"] = specific_params["friendly_name"]
    returnObject["attributes"]["type"] = specific_params["type"]
    # now check for optional items and include them if avail
    if "unit_of_measurement" in specific_params:
        returnObject["attributes"]["unit_of_measurement"] = specific_params["unit_of_measurement"]
    if "ip_ad" in specific_params:
        returnObject["attributes"]["ip_Add"] = specific_params["ip_ad"]
    if "wifi_errors" in specific_params:
        returnObject["attributes"]["wifi_errors"] = specific_params["wifi_errors"]
    if "send_data_count" in specific_params:
        returnObject["attributes"]["send_data_count"] = specific_params["send_data_count"]
    if "send_data_errors" in specific_params:
        returnObject["attributes"]["send_data_errors"] = specific_params["send_data_errors"]
    if "reboot_count" in specific_params:
        returnObject["attributes"]["reboot_count"] = specific_params["reboot_count"]
    #
    #	add sensor-specific attributes if avail
    #
    # contact sensor closed duration
    if "closed_duration" in specific_params:
        returnObject["attributes"]["min_active_duration_(sec)"] = specific_params["closed_duration"]
    # motion sensor active duration
    if "active_duration" in specific_params:
        returnObject["attributes"]["active_duration_(sec)"] = specific_params["active_duration"]
    # analog (e.g. temp/humid) sensor sampling interval
    if "sampling_interval" in specific_params:
        returnObject["attributes"]["sampling_interval_(sec)"] = specific_params["sampling_interval"]
    # sensornode device status update interval
    if "status_update_interval" in specific_params:
        returnObject["attributes"]["status_update_interval_(sec)"] = specific_params["status_update_interval"]
    return returnObject
    
def checkWifiConnection():
    #
    #	checks to see if wifi is still connected, and if not tries to reconnect. If reconnection fails, then
    #	system reboots into AP Mode
    #
    global ssid,pw,globalWifiErrorCount,globalIPAddress,checkWifiIPAdd

    def reconnect(ssid,pw):
        wd_feed()
        status,ipAddress = wifi_reconnect(ssid,pw)
        wd_feed()
        if status == 0:
            print("Reconnected to Wifi")
            globalIPAddress = ipAddress
            return 0
        else:
            print("\n\n---> Wifi reconnect attempt failed - restarting into AP mode...")
            restartIntoAPMode()
            
    wd_feed()
    print("\nChecking Wifi Connection...\n")
    error = False
    if wifi.radio.connected:
        #
        #	OPTIONAL additional wifi connectivity test
        #	if you have set WIFI_CHECK_IP_ADD in settings and ENABLED wificheck,
        #	THEN this code will PING that add to help ensure the radio is connected
        #
        ipv4 = ipaddress.ip_address(checkWifiIPAdd)
        print("Attempting to PING ipv4 = ",ipv4)
        wd_feed()
        try:
            pingResult = wifi.radio.ping(ipv4)*1000
        except:
            wd_feed()
            print("\n\n---> WIFI PING FAILED\n\n")
            print("\nWifi is NOT Connected after PING attempt - attempting to reconnect to wifi...\n")
            globalWifiErrorCount += 1
            if getReportCounts():
                wd_feed()
                print("\nUpdating NV storage with diagnostic data...\n")
                updateCountSetting('WIFI_ERRORS_COUNT',globalWifiErrorCount)
                print("\nDone w NV update\n\n")
            return reconnect(ssid,pw)
        else:
            wd_feed()
            print("Wifi PING Succeeded")
            print("Connected to Wifi")
            return 0

            
    else:
        print("\n\n---> ERROR Wifi NOT Connected - attempting to reconnect to wifi...\n")
        globalWifiErrorCount += 1
        if getReportCounts():
            print("\nUpdating ith diagnostic data...\n")
            updateCountSetting('WIFI_ERRORS_COUNT',globalWifiErrorCount)
            print("\nDone w NV update\n\n")
        return reconnect(ssid,pw)
            
        
def setUpS2Sensor(sensor_type,motion_en,water_en,temp_en):
    global s2_direct,s2_temp_sensor
    s2_direct = None
    s2_temp_sensor = None
    #
    #	S2 Sensor - Depending upon which TYPE of sensor is attached to S2 connector, the DATA pin of the connector will
    #	be used DIFFERENTLY:
    #
    #				**** ONLY ONE SENSOR CAN BE ENABLED AT ANY TIME AND CODE WILL ENFORCE THIS REQUIREMENT ****
    #
    #	MOTION - If motion sensor is attached the data pin will be used to clock (rising-edge triggered) a f/f
    #	WATER - if water sensor is attachd, the data pin will be read directly by the pico (active high - pulled down GPIO input)
    #	TEMP - if DS18B20 type temperature sensor is attached, the data pin will be read by pico using ds18b20 library
    #
    
    #
    #	Now use S2 Sensor Type value to modify all S2 Sensor Enables, ensuring that only ONE enable is true
    #
    s2MotionSensorEnabled = s2WaterSensorEnabled = s2TempSensorEnabled = False

    if sensor_type == 'MOTION':
        print("\n\n---> S2 MOTION SENSOR SELECTED\n\n")
        s2MotionSensorEnabled = motion_en
        s2WaterSensorEnabled = s2TempSensorEnabled = False
    elif sensor_type == 'WATER':
        print("\n\n---> S2 WATER SENSOR SELECTED\n\n")
        s2WaterSensorEnabled = water_en
        s2MotionSensorEnabled = s2TempSensorEnabled = False
    elif sensor_type == 'TEMP':
        print("\n\n---> S2 TEMP SENSOR SELECTED\n\n")
        s2TempSensorEnabled = temp_en
        s2MotionSensorEnabled = s2WaterSensorEnabled = False
    else:
        print("\n\n---> NO S2 SENSORS SELECTED\n\n")
        
    #
    #	if MOTION enabled, set up s2 direct and return
    #
    if s2MotionSensorEnabled:
        #
        #	Sensor - S2 Sensor DIRECT value
        #
        #	GPIO 20 - this pin is attached directly to sensor term block pulled LOW
        #
        #	if LEVEL sensing - then this pin tells state of the contact directly
        #
        s2_direct = digitalio.DigitalInOut(board.GP20)
        s2_direct.switch_to_input(pull=digitalio.Pull.DOWN)
        return 0,s2MotionSensorEnabled,s2WaterSensorEnabled,s2TempSensorEnabled
    #
    #	if WATER enabled, then configure GP20 as INPUT
    #
    elif s2WaterSensorEnabled:
        #
        #	Sensor - S2 Sensor DIRECT value
        #
        #	GPIO 20 - this pin is attached directly to sensor term block pulled LOW
        #
        #	if LEVEL sensing - then this pin tells state of the contact directly
        #
        s2_direct = digitalio.DigitalInOut(board.GP20)
        s2_direct.switch_to_input(pull=digitalio.Pull.DOWN)
        return 0,s2MotionSensorEnabled,s2WaterSensorEnabled,s2TempSensorEnabled
    elif s2TempSensorEnabled:
        #
        #	if TEMP enabled, configure GP20 as ds18b20 input pin
        #
        import adafruit_ds18x20
        from adafruit_onewire.bus import OneWireBus
        try:
            sensor_bus = OneWireBus(board.GP20)
            devices = sensor_bus.scan()
        except:
            print("\n\n---> ERROR ONE-WIRE BUS NOT FOUND - aborting.\n\n")
            s2TempSensorEnabled = False
            return -1,s2MotionSensorEnabled,s2WaterSensorEnabled,s2TempSensorEnabled
        else:
            print("\n---> Found S2 Temp Sensor Bus\n")
            print("devices: ",devices)
            if len(devices) == 1:
                s2_temp_sensor = adafruit_ds18x20.DS18X20(sensor_bus, devices[0])
                print("\nsetUpS2Sensor - correctly configured s2_temp_sensor...\n")
                return 0,s2MotionSensorEnabled,s2WaterSensorEnabled,s2TempSensorEnabled
            elif len(devices) == 0:
                print("\n\n---> ERROR in setUpS2Sensor - temp sensor enabled but cannot find sensor\n\n")
                s2TempSensorEnabled = False
                return -1,s2MotionSensorEnabled,s2WaterSensorEnabled,s2TempSensorEnabled
            else:
                print("ALERT - setUpS2Sensor - MORE than one temp sensor found - num sensors found = ",number_of_temp_sensors)
                s2TempSensorEnabled = False
                return -1,s2MotionSensorEnabled,s2WaterSensorEnabled,s2TempSensorEnabled
    else:
        print("No S2 Sensor Enabled")
        return 0,s2MotionSensorEnabled,s2WaterSensorEnabled,s2TempSensorEnabled
    
def calcNoTicksNormalMode():
    if getWatchDogIsRunning():
        noTicks = int(LED_BLINK_DURATION_WD_ENABLED/WAIT_TIME_TICK)
    else:
        noTicks = int(LED_BLINK_DURATION_WD_DISABLED/WAIT_TIME_TICK)
    return noTicks

def signalPowerOFF(dataStruct,ssid,pw,powerSensorTargetUrl):
    #
    #	Optional power detect circuit - signal Host if power goes down
    #
    print("\n\nPOWER IS OFF\n\n")
    print("sending OFF to host...")
    sendSensorData("off",ssid,pw,dataStruct,powerSensorTargetUrl)
    print("\n\nSuccessfully Sent Power OFF to Host\n\n")
    
def signalPowerON(dataStruct,ssid,pw,powerSensorTargetUrl):
    #
    #	sends 'power on' signal to host
    #
    print("\n\nPOWER IS ON\n\n")
    print("sending ON to host...")
    sendSensorData("on",ssid,pw,dataStruct,powerSensorTargetUrl)
    print("\n\nSuccessfully Sent Power ON to Host\n\n")
    
def detectI2cPeripherals():
    #
    #	determines if I2C peripherals are present and returns enables and update intervals
    #
    global tempHumidSensor
    tempHumidSensor = None
    i2cAvailable = False
    print("\nChecking for installed I2C Peripherals...\n")
    SCL = board.GP1
    SDA = board.GP0
    try:
        i2c = busio.I2C(SCL,SDA)
    except:
        print("\nI2C Bus Not Available.\n")
    else:
        print("\n\nFOUND I2C BUS\n\n")
        i2cAvailable = True
    i2cUpdateEnabled = False
    if i2cAvailable:
        #
        #	look for temp/humid sensor on i2c bus
        #
        try:
            tempHumidSensor = adafruit_ahtx0.AHTx0(i2c)
        except:
            return i2cUpdateEnabled
        else:
            if TEMP_HUMID_UPDATE_ENABLED_DEFAULT:
                print("AHT20")
                i2cUpdateEnabled = True
    return i2cUpdateEnabled

def getTempHumidReadings():
    # gets latest temp and humid readings
    global tempHumidSensor
    tempC = tempHumidSensor.temperature
    humidity = round(tempHumidSensor.relative_humidity,1)
    tempF = round(centigradeToFahrenheit(tempC),1)
    return tempF,humidity

def centigradeToFahrenheit(tempC):
    # converts centigrade to fahrenheit
    outTemp = tempC*9/5 + 32
    return outTemp

def getSensorNodeType(contactEnabled,s2MotionEnabled,internalTempHumidEnabled,powerMonitorEnabled,s2TempEnabled,s2WaterEnabled):
    #
    #	determines type value to report to HA based upon installed and enabled sensors
    #
    
    def addSensorValue(sensorString,returnString,slashNumber):
        # adds appropriate sensor string to type descriptor string
        if sensorString != "":
            returnString += sensorString
            if slashNumber > 0:
                returnString += "/"
                slashNumber -= 1
        
        return returnString,slashNumber
    
    
    returnType = SENSORNODE_TYPE+" - "
    contactString = s2MotionString = tempHumidString = powerString = s2TempString = s2WaterString = ""
    noSensors = 0
    if contactEnabled:
        contactString = "Contact"
        noSensors += 1
    if s2MotionEnabled:
        s2MotionString = "S2-Motion"
        noSensors += 1
    if internalTempHumidEnabled:
        tempHumidString = "I2CTemp/I2CHumid"
        noSensors += 1
    if powerMonitorEnabled:
        powerString = "Power"
        noSensors += 1
    if s2TempEnabled:
        s2TempString = "S2-Temp"
        noSensors += 1
    if s2WaterEnabled:
        s2WaterString = "S2-Water"
        noSensors += 1
    noSlashes = noSensors - 1
    
    # now build the type descriptor string
    
    if noSensors == 0:
        returnType += "No Sensors Found"
    else:
        returnType,noSlashes = addSensorValue(contactString,returnType,noSlashes)
        returnType,noSlashes = addSensorValue(s2MotionString,returnType,noSlashes)
        returnType,noSlashes = addSensorValue(tempHumidString,returnType,noSlashes)
        returnType,noSlashes = addSensorValue(powerString,returnType,noSlashes)
        returnType,noSlashes = addSensorValue(s2TempString,returnType,noSlashes)
        returnType,noSlashes = addSensorValue(s2WaterString,returnType,noSlashes)
    
    return returnType



def resetS2SensorInputLatch():
    #
    #	clears S2 sensor input latch
    #
    s2_sensor_latch_reset.value = False
    s2_sensor_latch_reset.value = True
    s2_sensor_latch_reset.value = False

def setS2SensorInputLatch():
    #
    #	sets S2 sensor input latch
    #
    s2_sensor_latch_set.value = False
    s2_sensor_latch_set.value = True
    s2_sensor_latch_set.value = False

def resetContactSensorInputLatch():
    #
    #	clears sensor input d flip-flop Q output and gets it ready for another reading
    #
    # 	NOTE: reset input in active HIGH
    contact_sensor_latch_reset.value = False
    contact_sensor_latch_reset.value = True
    contact_sensor_latch_reset.value = False

def setContactSensorInputLatch():
    #
    #	SETS sensor input d flip-flop Q output and gets it ready for another reading
    #
    # 	NOTE: set input in active HIGH
    contact_sensor_latch_set.value = False
    contact_sensor_latch_set.value = True
    contact_sensor_latch_set.value = False

def computeTimeBackoff(seed):
    #
    #	Computes variable time delay amt using Integer Seed value - used for variable time backoff to retry send data operations
    #
    minDelay = 1
    maxDelay = 3
    minSeed = 1
    maxSeed = 5
    if seed < minSeed: seed = minSeed
    if seed > maxSeed: seed = maxSeed
    delayIncrement = (maxDelay - minDelay)/(maxSeed - minSeed)
    delay = minDelay + (seed-1) * (delayIncrement)
    print("Inside compute Time Backoff - seed = ",seed,"\n")
    print("delay computed = ",delay,"seconds\n")
    if delay < minDelay: delay = minDelay
    if delay > maxDelay: delay = maxDelay
    return delay

def httpPost(targetUrl,headers,jsonData):
    #
    #	Posts data to HA
    #
    wd_feed()
    try: 
        response = requests.post(targetUrl,headers=headers,json=jsonData,timeout=HTTP_TIMEOUT)
    except:
        wd_feed()
        print("Error in Send Data")
        try:
            print("Status Code = ",response.status_code,"\n")
        except:
            print("Status Code unavailable\n")
        return -1
    else:
        wd_feed()
        print("Status Code = ",response.status_code,"\n")
        # if we don't get successful status code - RESTART
        if response.status_code <= 199 or response.status_code >= 300:
            if response.status_code >= 400 or response.status_code <= 499:
                print("\n\n---> ERROR unavailable IP Add response from server - Response Code = ",response.status_code,"\n\nRESTARTING INTO AP MODE...\n\n")
                restartIntoAPMode()
            else:
                print("\n\nALERT: Unknown Illegal Status Code Received - Status Code = ",response.status_code,"\n\nRESTARTING Pico...\n\n")
                restartIntoStationMode()
        else:
            print("HTTP POST Successful\n")
            return 0
        
def retrySendData(timeDelay,targetUrl,headers,sensorData):
    #
    #	retries sending data to HA using variable time delay
    #
    global requests
    wd_feed()
    time.sleep(timeDelay)
    wd_feed()
    print("\nRETRYING SEND DATA with Time Delay = ",timeDelay,"Seconds...\n")
    # post data to ha
    status = httpPost(targetUrl,headers,sensorData)
    wd_feed()
    return status   

def sendSensorData(sensorValue,ssid,pw,sensorData,targetUrl):
    global headers,requests,globalErrorCount,globalSentCount,checkWifiConnectionEnabled
    #
    #	Sends sensor data to HA
    #
    #	If send fails, it first checks wifi connection - if wifi is not connected several retries are made to connect to wifi, if all of them fail, pico is restarted
    #	if wifi connection is verified, then it retries send data operation using variable time backoff each time for up to 5 retries - if all retries fail, pico is restarted
    #
    
    def sendOKStatusAndReturn():
        global globalSentCount
        wd_feed()
        gc.collect()
        print("\nSensor Data Sent Successfully\n")
        globalSentCount += 1
        if getReportCounts():
            print("\nUpdating NV storage with diagnostic data...\n")
            updateCountSetting('SEND_DATA_COUNT',globalSentCount)
            print("\nDone w NV update\n\n")
        wd_feed()

    wd_feed()
    sensorData = setData(sensorValue,sensorData)
    gc.collect()
    print("\nSending Sensor Data for sensor: ",sensorData['attributes']['friendly_name']," with data = ",sensorData['state'])
    print("targetUrl: ",targetUrl)
    # post data to ha
    wd_feed()
    status = httpPost(targetUrl,headers,sensorData)
    wd_feed()
    if status !=0:
        print("\n\n---> ERROR in sendSensorData - could not complete transmission successfully...\n\n")
        if checkWifiConnectionEnabled:
            okWifiStatus = checkWifiConnection()
            wd_feed()
            if okWifiStatus == 0:
                print("\nWifi Connection OK\n")
            else:
                print("\n\nERROR - Wifi NOT Connected - RESTARTING PICO\n\n")
                # restart Pico
                restartIntoStationMode()
        wd_feed()
        error = True
        errorCount = 1
        while errorCount < 5:
            print("\n\n---> ERROR sending data - RETRYING SEND - Error Count = ",errorCount,"\n\n")
            timeBackoff = computeTimeBackoff(errorCount)
            print("retrying send with timeBackoff = ",timeBackoff,"seconds...")
            status = retrySendData(timeBackoff,targetUrl,headers,sensorData)
            wd_feed()
            if status != 0:
                errorCount += 1
            else:
                print("\n--> Error corrected - data sent successfully.\n")
                error = False
                break
        # log error count if enabled
        globalErrorCount += errorCount
        if getReportCounts():
            print("\nUpdating NV storage with diagnostic data...\n")
            wd_feed()
            updateCountSetting('SEND_DATA_ERRORS_COUNT',globalErrorCount)
            wd_feed()
            print("\nDone w NV update\n\n")
        print("\n\n---> Global Send Data Error Count = ",globalErrorCount,"\n")
        if error == True:
            #
            #	if get here that means after several retries, still did not send data properly - so RESTART PICO
            #
            wd_feed()
            print("\n\n---> ERROR in sendSensorData - send data persists after ",errorCount," retries - RESTARTING PICO...\n\n")
            # restart Pico
            restartIntoStationMode()
        else:
            sendOKStatusAndReturn()

    else:
        print("\n\nSensor Data Successfully Sent to HA\n\n")
        sendOKStatusAndReturn()


def setData(value,dataStruct):
    global contactSensorInactiveValue,contactSensorActiveValue,contactSensorOnlineValue
    global s2MotionSensorInactiveValue,s2MotionSensorActiveValue,s2MotionSensorOnlineValue
    global s2WaterSensorInactiveValue,s2WaterSensorActiveValue,s2WaterSensorOnlineValue
    # sets sensor value based upon sensor value
    # NOTE: sensor contact closure is ACTIVE LOW
    
    sensorType = dataStruct['attributes']['type']

    #print("\nInside setData - value = ",value,", type = ",sensorType,"\n")

    if sensorType == 'Contact':
        #print("found CONTACT sensor type")
        if value == True:
            dataStruct['state'] = contactSensorInactiveValue
        elif value == False:
            dataStruct['state'] = contactSensorActiveValue
        else:
            dataStruct['state'] = contactSensorOnlineValue
    elif sensorType == 'Motion':
        #print("found MOTION sensor type")
        if value == True:
            dataStruct['state'] = s2MotionSensorInactiveValue
        elif value == False:
            dataStruct['state'] = s2MotionSensorActiveValue
        else:
            dataStruct['state'] = s2MotionSensorOnlineValue
    elif sensorType == "Temperature":
        #print("found TEMPERATURE sensor type")
        dataStruct['state'] = value
    elif sensorType == "Humidity":
        #print("found HUMIDITY sensor type")
        dataStruct['state'] = value
    elif sensorType.find("SensorNode") != -1:
        # type string contains 'sensornode' indicating it's the sensornode device
        #print("found SENSORNODE sensor type")
        dataStruct['state'] = value
    elif sensorType.find("Water") != -1:
        # WATER sensor
        if value == True:
            dataStruct['state'] = s2WaterSensorActiveValue
        elif value == False:
            dataStruct['state'] = s2WaterSensorInactiveValue
        else:
            dataStruct['state'] = s2WaterSensorOnlineValue
    else:
        # if we don't have defined sensor type translation, then simply send value in 'state'
        dataStruct['state'] = value
    return dataStruct

def main_loop_code(ipAd,reboot_count,jsonDataStruct={}):
    #
    #	MAIN SensorNode Runtime Loop
    #
    #
    global contactSensorInactiveValue,contactSensorActiveValue,contactSensorOnlineValue,ssid,pw,globalIPAddress,checkWifiConnectionEnabled,checkWifiIPAdd
    global s2MotionSensorInactiveValue,s2MotionSensorActiveValue,s2MotionSensorOnlineValue,tempHumidSensor,s2_direct,s2_temp_sensor,globalErrorCount,globalSentCount
    global headers,sensor_data,requests,globalWifiErrorCount,s2WaterSensorInactiveValue,s2WaterSensorActiveValue,s2WaterSensorOnlineValue,statusUpdatesEnabled
    print("\n\n---> RUNNING MAIN LOOP CODE\n\n")
    gc.enable()
    gc.collect()
    freeMem = gc.mem_free()
    print("\nFree Memory upon code startup = ",freeMem,"\n\n")
    globalIPAddress = ipAd
    ssid = getWifiSSID()
    pw = getWifiPW()

    gc.collect()
    freeMem = gc.mem_free()
    print("\nFree Memory after global HTML buffer initialization = ",freeMem,"\n\n")
    # initialize S1/contact sensor latch set,reset pins to inactive
    contact_sensor_latch_set.value = False
    contact_sensor_latch_reset.value = False
    # initialize S2 sensor latch
    setS2SensorInputLatch()
    # initialize contact sensor latch Q value depending upon state of direct input
    print("Upon Startup - contact sensor direct value: ",contact_sensor_direct.value,", contact_sensor_latch_Q = ",contact_sensor_latch_Q.value)
    if contact_sensor_direct.value == True and contact_sensor_latch_Q.value == True:
        # contact is CLOSED upon startup, but f/f is set, so clear it
        resetContactSensorInputLatch()
    elif contact_sensor_direct.value == False and contact_sensor_latch_Q.value == False:
        # contact is OPEN upon startup, but f/f is cleared, so set it
        setContactSensorInputLatch()
    contactSensorFriendlyName = None
    #
    #	GET SENSOR SETTINGS
    #

    #
    #	Dry Contact Sensor Settings
    #
    contactSensorFriendlyName = getSettingValueFromSettingsJson(jsonDataStruct,'contact_friendly_name',HA_CONTACT_SENSOR_NAME_DEFAULT)
    contact_sensor_url_suffix = getSettingValueFromSettingsJson(jsonDataStruct,'HA_CONACT_SENSOR_URL_BASE',HA_CONTACT_SENSOR_URL_BASE)
    contactSensorInactiveValue = getSettingValueFromSettingsJson(jsonDataStruct,'CONTACT_SENSOR_INACTIVE_VALUE',CONTACT_SENSOR_INACTIVE_VALUE_DEFAULT)
    contactSensorActiveValue = getSettingValueFromSettingsJson(jsonDataStruct,'CONTACT_SENSOR_ACTIVE_VALUE',CONTACT_SENSOR_ACTIVE_VALUE_DEFAULT)
    contactSensorOnlineValue = getSettingValueFromSettingsJson(jsonDataStruct,'CONTACT_SENSOR_ONLINE_VALUE',CONTACT_SENSOR_ONLINE_VALUE_DEFAULT)
    contact_sensor_closed_duration = getSettingValueFromSettingsJson(jsonDataStruct,'CONTACT_SENSOR_CLOSED_DURATION',CONTACT_SENSOR_CLOSED_DURATION_DEFAULT)
    contactSensorEnabled = getBoolSetting('CONTACT_SENSOR_ENABLED',CONTACT_SENSOR_ENABLED_DEFAULT,jsonDataStruct)    
    #
    #	S2 Motion Sensor Settings
    #
    s2MotionSensorFriendlyName = getSettingValueFromSettingsJson(jsonDataStruct,'motion_friendly_name',HA_MOTION_SENSOR_NAME_DEFAULT)
    motion_sensor_url_suffix = getSettingValueFromSettingsJson(jsonDataStruct,'HA_MOTION_SENSOR_URL_BASE',HA_MOTION_SENSOR_URL_BASE)
    s2MotionSensorInactiveValue = getSettingValueFromSettingsJson(jsonDataStruct,'MOTION_SENSOR_INACTIVE_VALUE',MOTION_SENSOR_INACTIVE_VALUE_DEFAULT)
    s2MotionSensorActiveValue = getSettingValueFromSettingsJson(jsonDataStruct,'MOTION_SENSOR_ACTIVE_VALUE',MOTION_SENSOR_ACTIVE_VALUE_DEFAULT)
    s2MotionSensorOnlineValue = getSettingValueFromSettingsJson(jsonDataStruct,'MOTION_SENSOR_ONLINE_VALUE',MOTION_SENSOR_ONLINE_VALUE_DEFAULT)
    motion_sensor_active_duration = getSettingValueFromSettingsJson(jsonDataStruct,'MOTION_SENSOR_ACTIVE_DURATION',MOTION_SENSOR_ACTIVE_DURATION_DEFAULT)
    if motion_sensor_active_duration < MOTION_SENSOR_ACTIVE_DURATION_MINIMUM:
        motion_sensor_active_duration = MOTION_SENSOR_ACTIVE_DURATION_MINIMUM
    s2MotionSensorEnabled = getBoolSetting('MOTION_SENSOR_ENABLED',MOTION_SENSOR_ENABLED_DEFAULT,jsonDataStruct)
    #
    #	S2 Water Sensor Settings
    #
    s2WaterSensorFriendlyName = getSettingValueFromSettingsJson(jsonDataStruct,'s2_water_friendly_name',HA_S2_WATER_SENSOR_NAME_DEFAULT)
    s2Water_sensor_url_suffix = getSettingValueFromSettingsJson(jsonDataStruct,'HA_S2_WATER_SENSOR_URL_BASE',HA_S2_WATER_SENSOR_URL_BASE)
    s2WaterSensorInactiveValue = getSettingValueFromSettingsJson(jsonDataStruct,'S2_WATER_SENSOR_INACTIVE_VALUE',S2_WATER_SENSOR_INACTIVE_VALUE_DEFAULT)
    s2WaterSensorActiveValue = getSettingValueFromSettingsJson(jsonDataStruct,'S2_WATER_SENSOR_ACTIVE_VALUE',S2_WATER_SENSOR_ACTIVE_VALUE_DEFAULT)
    s2WaterSensorOnlineValue = getSettingValueFromSettingsJson(jsonDataStruct,'S2_WATER_SENSOR_ONLINE_VALUE',S2_WATER_SENSOR_ONLINE_VALUE_DEFAULT)
    s2WaterSensorEnabled = getBoolSetting('S2_WATER_SENSOR_ENABLED',S2_WATER_SENSOR_ENABLED_DEFAULT,jsonDataStruct)
    #
    #	S2 Temp Sensor Settings
    #
    s2TempSensorFriendlyName = getSettingValueFromSettingsJson(jsonDataStruct,'s2Temp_friendly_name',HA_S2_TEMP_SENSOR_NAME_DEFAULT)
    s2Temp_sensor_url_suffix = getSettingValueFromSettingsJson(jsonDataStruct,'HA_S2_TEMP_SENSOR_URL_BASE',HA_S2_TEMP_SENSOR_URL_BASE)
    s2TempSensorOnlineValue = getSettingValueFromSettingsJson(jsonDataStruct,'S2_TEMP_SENSOR_ONLINE_VALUE',S2_TEMP_SENSOR_ONLINE_VALUE_DEFAULT)
    s2TempSensorEnabled = getBoolSetting('S2_TEMP_SENSOR_ENABLED',S2_TEMP_SENSOR_ENABLED_DEFAULT,jsonDataStruct)
    s2TempSensorSamplingInterval = getSettingValueFromSettingsJson(jsonDataStruct,'S2_TEMP_SENSOR_SAMPLING_INTERVAL',S2_TEMP_SENSOR_SAMPLING_INTERVAL_DEFAULT)
    if s2TempSensorSamplingInterval < S2_TEMP_SENSOR_MIN_SAMPLING_INTERVAL:
        s2TempSensorSamplingInterval = S2_TEMP_SENSOR_MIN_SAMPLING_INTERVAL
    #
    #	get S2 Sensor Type from Settings JSON and, depending upon that value, modify S2 sensor enables so that only ONE S2 Sensor is enabled
    #
    s2SensorType = getSettingValueFromSettingsJson(jsonDataStruct,'s2_sensor_type',S2_SENSOR_TYPE_DEFAULT)
    print("\n\nS2 Sensor Type from Settings: ",s2SensorType,"\n\n")
    #
    #
    #
    #	S2 Sensor - configure sensor 
    #
    # 	This func makes sure only ONE s2 sensor is enabled and configured at once
    #
    status,s2MotionSensorEnabled,s2WaterSensorEnabled,s2TempSensorEnabled = setUpS2Sensor(s2SensorType,s2MotionSensorEnabled,s2WaterSensorEnabled,s2TempSensorEnabled)
    if status != 0:
        print("\n\n---> ERROR - setUpS2Sensor returned an ERROR!! \n\n")
        
    #
    #	SensorNode NAME Suffix Setting - If set, this text will be APPENDED to the END of the declared sensornode name transmitted to HA
    #
    snNameSuffix = getSettingValueFromSettingsJson(jsonDataStruct,'SENSORNODE_NAME','')
    print("SensorNode Name Suffix: ",snNameSuffix)
    
    #
    #	read stored diagnostic count values from settings json (reboot count already read in)
    #
    globalErrorCount = getSettingValueFromSettingsJson(jsonDataStruct,'SEND_DATA_ERRORS_COUNT',0)
    globalSentCount = getSettingValueFromSettingsJson(jsonDataStruct,'SEND_DATA_COUNT',0)
    globalWifiErrorCount = getSettingValueFromSettingsJson(jsonDataStruct,'WIFI_ERRORS_COUNT',0)
        
    gc.collect()
    #
    #	detect i2c devices attached
    #
    print("\n\nI2C Devices:")
    #
    #	i2c temp/humidity Sensor Settings
    #

    tempHumidUpdateEnabled = detectI2cPeripherals()
    if tempHumidUpdateEnabled:
        print("Detected Temperature/Humidity internal sensors:\n")
        tempF,humidity = getTempHumidReadings()
        print("Temp: ",tempF," deg F")
        print("Humid: ",humidity,"%")
        print("\n\n")
    else:
        print("\nTemp/Humidity Sensor Not Available.\n")
    #
    #	Detect POWER MONITOR CIRCUIT and set powerMonitorEnabled accordingly
    #
    if DETECT_POWER_OUTAGE and not POWER_MONITOR_PRESENT_LOW:
        powerMonitorEnabled = True
        print("\n\nPower Monitor Detected and Enabled\n\n")
    else:
        powerMonitorEnabled = False
        print("\nPower Monitor NOT Detected\n")
        
    #
    #	SensorNode Device Settings
    #
    sensornodeFriendlyName = getSettingValueFromSettingsJson(jsonDataStruct,'sensornode_friendly_name',SENSORNODE_NAME_DEFAULT)
    #
    #	general settings
    #    
    ha_url_prefix = getSettingValueFromSettingsJson(jsonDataStruct,'HA_URL_PREFIX',homeAssistantUrl)
    homeAssistantUrl_base = ha_url_prefix+"/api/states/"
    homeAssistantLongLivedAccessToken = getSettingValueFromSettingsJson(jsonDataStruct,'HA_LLAT',None)
    if homeAssistantLongLivedAccessToken == None:
        #
        #	ERROR - can't find LLAT for HA - must restart into AP mode until it is entered by user
        #
        print("\n\n---> ERROR - Cannot Find HA LLAT - Restarting into AP Mode...\n\n")
        restartIntoAPMode()

    print("\nAfter reading settings - \n")
    print("SensorNode Name Suffix: ",snNameSuffix)
    print("contact sensor enabled: ",contactSensorEnabled)
    print("contactSensorFriendlyName: ",contactSensorFriendlyName)
    print("contactSensorInactiveValue: ",contactSensorInactiveValue)
    print("contactSensorActiveValue: ",contactSensorActiveValue)
    print("contactSensorOnlineValue: ",contactSensorOnlineValue)
    print("contact_sensor_closed_duration: ",contact_sensor_closed_duration)
    print("s2 motion sensor enabled: ",s2MotionSensorEnabled)
    print("motionSensorFriendlyName: ",s2MotionSensorFriendlyName)
    print("motionSensorInactiveValue: ",s2MotionSensorInactiveValue)
    print("motionSsensorActiveValue: ",s2MotionSensorActiveValue)
    print("motionSensorOnlineValue: ",s2MotionSensorOnlineValue)
    print("motion_sensor_active_duration",motion_sensor_active_duration)
    print("sle jumper enables: ",getSleJumperEnables())
    print("tempHumidUpdateEnabled: ",tempHumidUpdateEnabled)
    print("s2 water sensor enabled: ",s2WaterSensorEnabled)
    print("s2 temp sensor enabled: ",s2TempSensorEnabled)
    print("s2 temp sensor sampling interval: ",s2TempSensorSamplingInterval)
    print("s2 sensor type: ",s2SensorType)
    print("reboot count: ",reboot_count)
    print("globalErrorCount: ",globalErrorCount)
    print("globalSentCount: ",globalSentCount)
    print("globalWifiErrorCount: ",globalWifiErrorCount)
    print("\n\n")
        
    # calculate number of timer ticks required to count intervals
    status_led_ticks = calcNoTicksNormalMode()
    connectivity_check_ticks = int(INTERNET_CONNECTIVITY_CHECK_DURATION/WAIT_TIME_TICK)

    print("status led ticks = ",status_led_ticks)
    print("connectivity check ticks = ",connectivity_check_ticks)
    #
    #	Get optional Wifi Check settings
    #
    checkWifiConnectionSetting = getBoolSetting('WIFI_CHECK_ENABLED',WIFI_CHECK_ENABLE_DEFAULT,jsonDataStruct)
    print("\nCheck Wifi Setting = ",checkWifiConnectionSetting)
    checkWifiIPAdd = getSettingValueFromSettingsJson(jsonDataStruct,'WIFI_CHECK_ADD',None)
    print("\nCheck Wifi IP add set to ",checkWifiIPAdd,"\n")
    checkWifiOK = False
    if checkWifiIPAdd != None and checkWifiIPAdd != "" and checkWifiIPAdd != " ":
        checkWifiOK = True
    if checkWifiConnectionSetting and checkWifiOK:
        checkWifiConnectionEnabled = True
    else:
        checkWifiConnectionEnabled = False
    print("\nCheck Wifi Connection Enable = ",checkWifiConnectionEnabled,"\n")
    
    #
    #	Get status update parameters
    #
    statusUpdatesEnabled = getBoolSetting('SEND_STATUS_UPDATES',True,jsonDataStruct)
    print("\nstatusUpdatesEnabled = ",statusUpdatesEnabled)
    statusUpdateInterval = getSettingValueFromSettingsJson(jsonDataStruct,'STATUS_UPDATE_INTERVAL',STATUS_UPDATE_INTERVAL_DEFAULT)
    #	compute interval from bounds
    if statusUpdateInterval < STATUS_UPDATE_INTERVAL_MINIMUM:
        statusUpdateInterval = STATUS_UPDATE_INTERVAL_MINIMUM
    elif statusUpdateInterval > STATUS_UPDATE_INTERVAL_MAXIMUM:
        statusUpdateInterval = STATUS_UPDATE_INTERVAL_MAXIMUM
    print("\nstatusUpdateInterval = ",statusUpdateInterval)
    status_update_active_duration = getSettingValueFromSettingsJson(jsonDataStruct,'STATUS_UPDATE_ACTIVE_DURATION',STATUS_UPDATE_ACTIVE_DURATION_DEFAULT)
    print("\nstatus_update_active_duration: ",status_update_active_duration)

    #
    #	Setup Timers
    #
    
    # status update timer
    
    # set a timer to fire once every statusUpdateInterval to update status
    if statusUpdatesEnabled:
        # status update timer
        statusUpdateTimer = Timer()
        statusUpdateTimer.timeDelay = statusUpdateInterval
        statusUpdateTimer.clearTimer()
        # status update active duration timer
        statusUpdateActiveDurationTimer = Timer()
        statusUpdateActiveDurationTimer.timeDelay = status_update_active_duration
    
    # contact closure timer
    if contactSensorEnabled:
        contactClosureTimer = Timer()
        contactClosureTimer.timeDelay = contact_sensor_closed_duration

    # temp/humid sensor timer
    if tempHumidUpdateEnabled:
        tempHumidSensorTimer = Timer()
        tempHumidSensorTimer.timeDelay = TEMP_HUMID_MAX_UPDATE_INTERVAL
        tempHumidSensorSamplingTimer = Timer()
        tempHumidSensorSamplingTimer.timeDelay = TEMP_HUMID_SAMPLING_INTERVAL

    
    # Wifi Check Timer
    if checkWifiConnectionEnabled:
        wifiCheckTimer = Timer()
        wifiCheckTimer.timeDelay = WIFI_RETRY_DURATION*5		# Periodically check wifi connection during normal operation
        wifiCheckTimer.clearTimer()
    else:
        print("\n\n---> Wifi Check Disabled - Enter valid Local IP add in settings for WIFI_CHECK_IP_ADD, and click checkbox for wifi checks to enable\n\n")

    picoIDShort = getPicoIdShort()
    picoID = getPicoID()
    sensorNodeDeviceName = getSensorNodeDeviceName()
    if snNameSuffix != '':
        sensorNodeDeviceName = sensorNodeDeviceName+' - '+snNameSuffix
        
    homeAssistantUrl_sensornode = homeAssistantUrl_base+SENSORNODE_URL_SUFFIX_BASE+picoIDShort
    
    homeAssistantUrl_contact = homeAssistantUrl_base+contact_sensor_url_suffix+picoIDShort
    homeAssistantUrl_motion = homeAssistantUrl_base+motion_sensor_url_suffix+picoIDShort
    homeAssistantUrl_s2_water = homeAssistantUrl_base+s2Water_sensor_url_suffix+picoIDShort
    homeAssistantUrl_s2_temp = homeAssistantUrl_base+s2Temp_sensor_url_suffix+picoIDShort
    
    # OPTIONAL power monitor url
    if powerMonitorEnabled:
        POWER_MONITOR_URL_BASE = homeAssistantUrl_base+"binary_sensor.power_"
        homeAssistantUrl_power = POWER_MONITOR_URL_BASE+picoIDShort
    
    
    if tempHumidUpdateEnabled:
        homeAssistantUrl_internal_temp = homeAssistantUrl_base+INTERNAL_TEMP_SENSOR_URL_SUFFIX_BASE+picoIDShort
        homeAssistantUrl_internal_humidity = homeAssistantUrl_base+INTERNAL_HUMID_SENSOR_URL_SUFFIX_BASE+picoIDShort
    

    print("\n\nhomeAssistantUrl_sensornode: ",homeAssistantUrl_sensornode)
    print("homeAssistantUrl_contact: ",homeAssistantUrl_contact)
    print("homeAssistantUrl_motion: ",homeAssistantUrl_motion)
    print("homeAssistantUrl_s2_water: ",homeAssistantUrl_s2_water)
    print("homeAssistantUrl_s2_temp: ",homeAssistantUrl_s2_temp)
    if powerMonitorEnabled:
        print("homeAssistantUrl_power: ",homeAssistantUrl_power)
    if tempHumidUpdateEnabled:
        print("homeAssistantUrl_internal_temp: ",homeAssistantUrl_internal_temp)
        print("homeAssistantUrl_internal_humidity: ",homeAssistantUrl_internal_humidity)
    print("\n")
    #
    #	Set up socketpool, requests session
    #
    pool = socketpool.SocketPool(wifi.radio)
    wd_feed()   
    requests = adafruit_requests.Session(pool,ssl.create_default_context())
    #
    #	parameters for REST CALL to HA
    #
    headers = {
        "Authorization":"Bearer "+homeAssistantLongLivedAccessToken,
        "Content-Type":"application/json",
        }
    #
    #	Build Data Objects for HA Sensors
    #
    #
    #	attributes that are common to all elements
    #
    base_object_params = {
        "unique_id":picoID,
        "firmware_version":VERSION,
        "name":sensorNodeDeviceName,
        }
    
    #
    #	attributes specific to each element
    #
    contact_sensor_specific_params = {
        "state": "off",
        "friendly_name":contactSensorFriendlyName+" - "+picoIDShort,
        "type":"Contact",
        "closed_duration":contact_sensor_closed_duration,
        }
    
    contact_sensor_data_object = buildDataObject(base_object_params,contact_sensor_specific_params)
    
    if sensornodeFriendlyName == "not set":
        sensornodeFriendlyName = sensorNodeDeviceName
        
    if getReportCounts():
        sensornode_specific_params = {
            "state":"off",
            "friendly_name":sensornodeFriendlyName,
            "type":getSensorNodeType(contactSensorEnabled,s2MotionSensorEnabled,tempHumidUpdateEnabled,powerMonitorEnabled,s2TempSensorEnabled,s2WaterSensorEnabled),
            "ip_ad":str(globalIPAddress),
            "wifi_errors": globalWifiErrorCount,
            "send_data_errors": globalErrorCount,
            "send_data_count": globalSentCount,
            "reboot_count": reboot_count,
            }
    else:
        sensornode_specific_params = {
            "state":"off",
            "friendly_name":sensornodeFriendlyName,
            "type":getSensorNodeType(contactSensorEnabled,s2MotionSensorEnabled,tempHumidUpdateEnabled,powerMonitorEnabled,s2TempSensorEnabled,s2WaterSensorEnabled),
            "ip_ad":str(globalIPAddress),
            }
    if statusUpdatesEnabled:
        # Add status update duration
        sensornode_specific_params["status_update_interval"] = statusUpdateInterval
    else:
        # Add 'disabled' if not enabled
        sensornode_specific_params["status_update_interval"] = "Status Updates Disabled"
    
    sensornode_device_data_object = buildDataObject(base_object_params,sensornode_specific_params)

    internal_temp_sensor_specific_params = {
        "state":0.0,
        "friendly_name":INTERNAL_TEMP_SENSOR_NAME_DEFAULT+" - "+picoIDShort,
        "type":"Temperature",
        "unit_of_measurement":"°F",
        }
    
    internal_temp_sensor_data_object = buildDataObject(base_object_params,internal_temp_sensor_specific_params)
    
    internal_humid_sensor_specific_params = {
        "state":0.0,
        "friendly_name":INTERNAL_HUMID_SENSOR_NAME_DEFAULT+" - "+picoIDShort,
        "type":"Humidity",
        "unit_of_measurement":"%",
        }
    
    internal_humid_sensor_data_object = buildDataObject(base_object_params,internal_humid_sensor_specific_params)
    
    # 	Build Data Object for S2 Connector Sensor (depending upon type selected in settings and board Jumper J3)
    
    if s2MotionSensorEnabled:
        motion_sensor_specific_params = {
            "state": "off",
            "friendly_name": s2MotionSensorFriendlyName+" - "+picoIDShort,
            "active_duration": motion_sensor_active_duration,
            "type":"Motion",
            }
        
        motion_sensor_data_object = buildDataObject(base_object_params,motion_sensor_specific_params)
    elif s2TempSensorEnabled:
        s2_temp_sensor_specific_params = {
            "state":0.0,
            "friendly_name":s2TempSensorFriendlyName+" - "+picoIDShort,
            "type":"Temperature",
            "unit_of_measurement":"°F",
            "sampling_interval":s2TempSensorSamplingInterval,
            }
        
        s2_temp_sensor_data_object = buildDataObject(base_object_params,s2_temp_sensor_specific_params)
    elif s2WaterSensorEnabled:
        s2_water_sensor_specific_params = {
            "state":"off",
            "friendly_name":s2WaterSensorFriendlyName+" - "+picoIDShort,
            "type":"Water",
            }
        
        s2_water_sensor_data_object = buildDataObject(base_object_params,s2_water_sensor_specific_params)
    
    #
    #	OPTIONAL Power Monitor Data object
    #
    power_monitor_sensor_specific_params = {
        "state":"on",
        "friendly_name":"Power Monitor - "+picoIDShort,
        "type":"Power",
        }
    
    power_monitor_sensor_data_object = buildDataObject(base_object_params,power_monitor_sensor_specific_params)

    print("\nSending initial sensor data...\n")
    #
    #	Initialize All Sensors
    #
    contactClosureActive = False
    motionDetected = False
    statusUpdateActive = False
    s2WaterDetected = False
    error = False
    #
    # 	send initial values and save those values upon startup
    #
    #
    #	sensornode device
    #
    print("Sending SensorNode device initial status update...")
    wd_feed()
    # initially send 'online' to server before sending actual sensor value - params: sensorValue,ssid,pw,sensorData,targetUrl)
    print("sending online for sensornode")
    sendSensorData(SENSORNODE_ONLINE_VALUE_DEFAULT,ssid,pw,sensornode_device_data_object,homeAssistantUrl_sensornode)
    wd_feed()
    # now send actual value
    print("sending ",SENSORNODE_ACTIVE_VALUE_DEFAULT,"for sensornode")
    sendSensorData(SENSORNODE_ACTIVE_VALUE_DEFAULT,ssid,pw,sensornode_device_data_object,homeAssistantUrl_sensornode)
    print("\nSensornode device status update completed successfully.\n")
    #
    #	Contact Sensor
    #
    if contactSensorEnabled:
        print("initial contact_sensor_latch_Q value = ",contact_sensor_latch_Q.value)
        print("contact sensor direct value: ", contact_sensor_direct.value)
        wd_feed()
        # send actual value of contact sensor latch to HA
        sendSensorData(contact_sensor_latch_Q.value,ssid,pw,contact_sensor_data_object,homeAssistantUrl_contact)
        if contact_sensor_latch_Q.value == False:
            # unit powered up when contact was closed - set active and turn on timer
            contactClosureActive = True
            contactClosureTimer.clearTimer()
        print("\ncontact sensor status update completed successfully.\n")

    #
    #	set up s2 sensor timer based upon sensor type
    #
    s2SensorTimer = Timer()
    if s2MotionSensorEnabled:
        s2SensorTimer.timeDelay = motion_sensor_active_duration
    elif s2TempSensorEnabled:
        # set up special max delay timer when using s2 temp sensor
        s2TempSensorMaxDelayTimer = Timer()
        s2TempSensorMaxDelayTimer.timeDelay = S2_TEMP_SENSOR_MAX_UPDATE_INTERVAL
        # use regular s2 timer for update rate
        s2SensorTimer.timeDelay = s2TempSensorSamplingInterval
    #
    #	S2 Sensor
    #
    if s2MotionSensorEnabled:
        # send current sensor status upon startup
        if s2_direct.value == True:
            # motion present
            print("\n\n----> **** Detected Motion upon Startup ****\n")
            motionDetected = True
            sendSensorData(MOTION_SENSOR_ACTIVE_BOOLEAN_LEVEL,ssid,pw,motion_sensor_data_object,homeAssistantUrl_motion)
            print("motion sensor status updated to HA")
            s2SensorTimer.clearTimer()
        else:
            # motion not present
            print("\nNO MOTION DETECTED upon startup\n")
            sendSensorData(MOTION_SENSOR_INACTIVE_BOOLEAN_LEVEL,ssid,pw,motion_sensor_data_object,homeAssistantUrl_motion)
        # reset motion sensor latch upon startup
        setS2SensorInputLatch()
    elif s2TempSensorEnabled:
        wd_feed()
        print("Inside elif s2TempSensorEnabled...")
        # start collecting temp data and send first sample
        previous_s2_temp = getS2TempSensorValue(s2_temp_sensor,units="F")
        print("S2 Temp: ",previous_s2_temp,"degrees F")
        sendSensorData(previous_s2_temp,ssid,pw,s2_temp_sensor_data_object,homeAssistantUrl_s2_temp)
        print("\ns2 temp sensor status update completed successfully.\n")
    elif s2WaterSensorEnabled:
        wd_feed()
        # send current sensor status upon startup
        if s2_direct.value == True:
            print("\n\n**** WATER DETECTED UPON STARTUP ****\n")
            s2WaterDetected = True
            sendSensorData(S2_WATER_SENSOR_ACTIVE_BOOLEAN_LEVEL,ssid,pw,s2_water_sensor_data_object,homeAssistantUrl_s2_water)
            print("water status updated to HA")
        else:
            print("\nNO WATER DETECTED upon startup\n")
            s2WaterDetected = False
            sendSensorData(S2_WATER_SENSOR_INACTIVE_BOOLEAN_LEVEL,ssid,pw,s2_water_sensor_data_object,homeAssistantUrl_s2_water)
            print("water status updated to HA")
        # reset input latch
        setS2SensorInputLatch()
    #
    #	Internal I2C Temp, Humid Sensors (AHT20)
    #
    previousTemp = None
    previousHumid = None
    if tempHumidUpdateEnabled:
        # if enabled, start temp humid update timers
        tempHumidSensorTimer.clearTimer()
        tempHumidSensorSamplingTimer.clearTimer()
        temp,humid = getTempHumidReadings()
        print("Temp: ",temp,", Humid: ",humid)
        previousTemp = temp
        previousHumid = humid
        #
        # send initial temp data
        #
        wd_feed()
        #  send actual value
        sendSensorData(temp,ssid,pw,internal_temp_sensor_data_object,homeAssistantUrl_internal_temp)
        print("\ninternal temp sensor status update completed successfully.\n")
        #
        #	send initial humidity data
        #
        wd_feed()
        #  send actual value
        sendSensorData(humid,ssid,pw,internal_humid_sensor_data_object,homeAssistantUrl_internal_humidity)
        print("\ninternal humidity sensor status update completed successfully.\n")

    #
    #	Power Monitor
    #
    if powerMonitorEnabled:
        wd_feed()
        # initially only send 'online' to server 
        sendSensorData('online',ssid,pw,power_monitor_sensor_data_object,homeAssistantUrl_power)
        wd_feed()
        print("\nmotion sensor status update completed successfully.\n")
         

    # then loop, checking sensor for changes, only send data when state changes, then wait sensor_closed_duration sec before checking again    

    ledTicks = status_led_ticks
    connTicks = connectivity_check_ticks
    
    print("\nStarting Sensor Loop...\n")
    
    powerOffSignaled = False
    powerOnSignaled = False

    gc.collect()
    
    time.sleep(1)
    
    consoleUpdate(reboot_count)
    
    #
    #	MAIN LOOP - Continually Scan for Sensor activity and act accordingly forever
    #
    loopCount = 0
    while error == False:
        wd_feed()
        gc.collect()
        #freeMem = gc.mem_free()
        #print("Free Memory: ",freeMem)
        #
        #	Detect when sensors ACTUATE
        #
        
        if powerMonitorEnabled:
            if power_is_out_pin.value == False and powerOffSignaled == False:
                # if pwr goes out signal to HA EVEN IF STATUS UPDATE IS ACTIVE
                powerOffSignaled = True
                powerOnSignaled = False
                signalPowerOFF(power_monitor_sensor_data_object,ssid,pw,homeAssistantUrl_power)
                wd_feed()
                status_led_ticks = int(.1/WAIT_TIME_TICK)
            elif power_is_out_pin.value == True and powerOnSignaled == False and statusUpdateActive == False:
                # WAIT until status update is over before proceeding
                powerOnSignaled = True
                powerOffSignaled = False
                signalPowerON(power_monitor_sensor_data_object,ssid,pw,homeAssistantUrl_power)
                wd_feed()
                status_led_ticks = calcNoTicksNormalMode()
        
        if contactSensorEnabled and statusUpdateActive == False:
            if contact_sensor_latch_Q.value == False:
                #
                #	Contact has been triggered
                #
                #	DO NOT PROCEED if status update is currently in progress - skip until it is completed.
                #
                if contactClosureActive == False:
                    #
                    #	Contact Closure ACTIVE
                    #
                    print("\n\n----> **** Contact Sensor is CLOSED **** \n")
                    # when CLOSED ensure ON signal stays active for min duration time and set active to true
                    contactClosureActive = True
                    sendSensorData(contact_sensor_latch_Q.value,ssid,pw,contact_sensor_data_object,homeAssistantUrl_contact)
                    print("contact sensor status updated to HA")
                else:
                    print("\nContact Still Closed...\n")
                setContactSensorInputLatch()
                contactClosureTimer.clearTimer()

        if s2MotionSensorEnabled and statusUpdateActive == False:
            if s2_sensor_latch_Q.value == False or s2_direct.value == True:
                #
                #	Motion Sensor ACTIVE
                #
                #	DO NOT PROCEED if status update is currently in progress - skip until it is completed.
                #
                if motionDetected == False:
                    # only do this ONCE
                    print("\n\n----> **** Detected Motion ****\n")
                    motionDetected = True
                    sendSensorData(MOTION_SENSOR_ACTIVE_BOOLEAN_LEVEL,ssid,pw,motion_sensor_data_object,homeAssistantUrl_motion)
                    print("motion sensor status updated to HA")
                else:
                    print("M",end="")
                setS2SensorInputLatch()
                s2SensorTimer.clearTimer()

        elif s2WaterSensorEnabled:
            s2_water_sensor_value = s2_direct.value
            if s2_water_sensor_value == True and statusUpdateActive == False:
                #
                #	Water Sensor ACTIVE
                #
                #	DO NOT PROCEED if status update is currently in progress - skip until it is completed.
                #
                if s2WaterDetected == False:
                    # only print this ONCE
                    print("\n\n----> **** Detected WATER ****\n")
                else:
                    print(".",end="")
                s2WaterDetected = True
                sendSensorData(S2_WATER_SENSOR_ACTIVE_BOOLEAN_LEVEL,ssid,pw,s2_water_sensor_data_object,homeAssistantUrl_s2_water)
                print("water status updated to HA")
            
        time.sleep(WAIT_TIME_TICK)
        wd_feed()
        #
        #	update all counters and act on them if necessary, while petting watchdog
        #
        ledTicks = countLedTicks(ledTicks,status_led_ticks)
        wd_feed()
        #
        #	ACTIVATE status updates - send 'online' periodically to tell host that sensorNode is still operational
        #
        #	SensorNode device will be updated to HA in this fashion
        #
        #	All DIGITAL sensors (e.g. contact, motion, water) will send current sensor value (active/inactive) every update interval 
        #
        #	Analog sensors (e.g. temp, humid) will update periodically using ANALOG_SENSOR_MAX_UPDATE_INTERVAL so they are not included here
        #
        if statusUpdatesEnabled:
            if statusUpdateTimer.isItTime():
                statusUpdateTimer.clearTimer()
                statusUpdateActiveDurationTimer.clearTimer()
                statusUpdateActive = True
                nowTime = time.time()
                print("\n\n---> ",nowTime,": Status Update Timer Fired!\nSending Periodic update to HA\n\n")
                print("Free Memory = ",freeMem,"\n\n")
                # send update for sensorNode device
                sendSensorData(SENSORNODE_ONLINE_VALUE_DEFAULT,ssid,pw,sensornode_device_data_object,homeAssistantUrl_sensornode)
                if powerMonitorEnabled:
                    # send update for power monitor device
                    sendSensorData('online',ssid,pw,power_monitor_sensor_data_object,homeAssistantUrl_power)
                    wd_feed()
                if contactSensorEnabled:
                    # resend current status of contact sensor as update
                    if contactClosureActive:
                        sendSensorData(CONTACT_SENSOR_ACTIVE_BOOLEAN_LEVEL,ssid,pw,contact_sensor_data_object,homeAssistantUrl_contact)
                    else:
                        sendSensorData(CONTACT_SENSOR_INACTIVE_BOOLEAN_LEVEL,ssid,pw,contact_sensor_data_object,homeAssistantUrl_contact)
                    wd_feed()
                if s2MotionSensorEnabled:
                    # resend current status of motion detector to HA as update
                    if motionDetected == True:
                        sendSensorData(MOTION_SENSOR_ACTIVE_BOOLEAN_LEVEL,ssid,pw,motion_sensor_data_object,homeAssistantUrl_motion)
                    else:
                        sendSensorData(MOTION_SENSOR_INACTIVE_BOOLEAN_LEVEL,ssid,pw,motion_sensor_data_object,homeAssistantUrl_motion)
                    wd_feed()
                if s2WaterSensorEnabled:
                    # resend current status of water sensor to HA as update
                    if s2WaterDetected == True:
                        sendSensorData(S2_WATER_SENSOR_ACTIVE_BOOLEAN_LEVEL,ssid,pw,s2_water_sensor_data_object,homeAssistantUrl_s2_water)
                    else:
                        sendSensorData(S2_WATER_SENSOR_INACTIVE_BOOLEAN_LEVEL,ssid,pw,s2_water_sensor_data_object,homeAssistantUrl_s2_water)
                wd_feed()
        #
        #	Detect when to terminate active time for each sensor (minimum active time)
        #
        if contactSensorEnabled:
            if contactClosureActive == True and contactClosureTimer.isItTime() == True and contact_sensor_latch_Q.value == True:
                # if timer has fired, and latch indicates no more pulses, then test direct value to determine if contact is settled open or closed
                if contact_sensor_direct.value == False:
                    print("\n\n----> **** Contact Sensor is OPEN. ****\n") 
                    # if direct value indicates contact is OPEN then wait debounce time and
                    sendSensorData(contact_sensor_latch_Q.value,ssid,pw,contact_sensor_data_object,homeAssistantUrl_contact)
                    print("contact sensor status updated to HA")
                    contactClosureActive = False
                else:
                    print("\n\n----> **** Contact Sensor Remains Closed after Timer Fired - Resetting Timer... ****\n")
                    contactClosureTimer.clearTimer()
                wd_feed()
        if s2MotionSensorEnabled:
            if motionDetected == True and s2SensorTimer.isItTime() == True and s2_sensor_latch_Q.value == True and s2_direct.value == False:
                print("\n\n----> **** Motion Stopped. ****\n")
                sendSensorData(MOTION_SENSOR_INACTIVE_BOOLEAN_LEVEL,ssid,pw,motion_sensor_data_object,homeAssistantUrl_motion)
                motionDetected = False

        if s2WaterSensorEnabled:
            s2_water_sensor_value = s2_direct.value
            if s2WaterDetected == True and s2_water_sensor_value == False:
                print("\n\n----> **** Water No Longer Detected. ****\n")
                sendSensorData(S2_WATER_SENSOR_INACTIVE_BOOLEAN_LEVEL,ssid,pw,s2_water_sensor_data_object,homeAssistantUrl_s2_water)
                s2WaterDetected = False

        #
        #	Terminate ONLINE status update after statue update timer fires
        #
        if statusUpdatesEnabled:
            if statusUpdateActive == True and statusUpdateActiveDurationTimer.isItTime() == True:
                statusUpdateTimer.clearTimer()
                statusUpdateActive = False
                #
                #	Update sensornode attributes
                #
                sensornode_specific_params["ip_ad"] = str(globalIPAddress)
                # only send count data if enabled
                if getReportCounts():
                    sensornode_specific_params["wifi_errors"] = globalWifiErrorCount
                    sensornode_specific_params["send_data_errors"] = globalErrorCount
                    sensornode_specific_params["send_data_count"] = globalSentCount
                    sensornode_device_data_object = buildDataObject(base_object_params,sensornode_specific_params)
                #
                #	and send active value to clear online status update
                #
                sendSensorData(SENSORNODE_ACTIVE_VALUE_DEFAULT,ssid,pw,sensornode_device_data_object,homeAssistantUrl_sensornode)
                if powerMonitorEnabled:
                    # clear update for power monitor device
                    if powerOffSignaled == True:
                        pwrMessage = "off"
                    else:
                        pwrMessage = "on"
                    sendSensorData(pwrMessage,ssid,pw,power_monitor_sensor_data_object,homeAssistantUrl_power)
                print("Successfully sent status update...")
                
        if s2TempSensorEnabled and s2SensorTimer.isItTime():
            #
            #	S2 Temp Sensor - sample sensor value every time s2SensorTimer fires if enabled
            #
            #	- if temp varies by more than specified VARIANCE_MIN or s2 max delay timer has fired, send latest temp reading
            #
            #print("\nPrevious S2 Temp = ",previous_s2_temp)
            current_s2_temp = getS2TempSensorValue(s2_temp_sensor,units="F")
            wd_feed()
            #print("Current S2 Temp = ",current_s2_temp)
            deltaTemp = abs(current_s2_temp-previous_s2_temp)
            s2SensorTimer.clearTimer()
            
            if deltaTemp >= S2_TEMP_SENSOR_VARIANCE_MIN or s2TempSensorMaxDelayTimer.isItTime():
                print("\n\ns2 temp sensor -  sending updated temp value...")
                print("S2 Temp: ",current_s2_temp,"degrees F")
                print("Delta = ",deltaTemp,"\n")
                s2TempSensorMaxDelayTimer.clearTimer()
                previous_s2_temp = current_s2_temp
                sendSensorData(current_s2_temp,ssid,pw,s2_temp_sensor_data_object,homeAssistantUrl_s2_temp)
                print("\ns2 temp sensor update completed successfully.\n")
            
                
        if tempHumidUpdateEnabled and tempHumidSensorSamplingTimer.isItTime():
            #
            #	I2C Temp/Humid sensors
            #
            #	- update whenever changes by more than VARIANCE_MIN AND temp/humid sampling timer has fired OR if max delay has fired then update always
            #
            temp,humid = getTempHumidReadings()
            wd_feed()
            #print("\n\npreviousTemp: ",previousTemp,", previousHumid: ",previousHumid,"\n\n")
            if abs(temp-previousTemp) >= INTERNAL_TEMP_VARIANCE_MIN or tempHumidSensorTimer.isItTime():
                previousTemp = temp
                print("\n\nI2C Temp check - previous temp = ",previousTemp,", current temp = ",temp,"\n")
                sendSensorData(temp,ssid,pw,internal_temp_sensor_data_object,homeAssistantUrl_internal_temp)

            if abs(humid-previousHumid) >= INTERNAL_HUMID_VARIANCE_MIN or tempHumidSensorTimer.isItTime():
                previousHumid = humid
                print("\n\nI2C Humid check - previous humid = ",previousHumid,", current humid = ",humid,"\n")
                sendSensorData(humid,ssid,pw,internal_humid_sensor_data_object,homeAssistantUrl_internal_humidity)

            if tempHumidSensorTimer.isItTime():
                tempHumidSensorTimer.clearTimer()			# reset max delay timer for next event interval
            tempHumidSensorSamplingTimer.clearTimer()		# reset timer for next sampling interval
                    
        if checkWifiConnectionEnabled:
            if wifiCheckTimer.isItTime() and statusUpdateActive == False:
                print("\n*************************************\n")
                print("\n---> Wifi Check Timer fired...")
                # reset wifi check timer
                wifiCheckTimer.clearTimer()
                wifiStatus = checkWifiConnection()
                if wifiStatus != 0:
                    print("\n\n---> ERROR - checkWifiConnection returned error but did NOT reboot\n\n")
                else:
                    print("Wifi OK\n")
                print("\n*************************************\n")
              
        loopCount += 1
        if loopCount %1000 == 0:
            gc.collect()
            freeMem = gc.mem_free()
            consoleUpdate(reboot_count)
        elif loopCount%10 == 0:
            print(".",end=" ")
