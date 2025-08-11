'''

    SensorNode
    Server Files for
    Temperature Sensor for Connector S2
    Based upon DS18B20 Dallas Semi one-wire protocol
    using adafruit library
    TNB Technologies, LLC

'''

import gc
from sensorNodeUtils import readSettingsFile,getSettingValueFromSettingsJson,getSensorNodeDeviceName,checkValue,addToSettingsStruct,getIntFromString,setHtmlBuffer
from globals import SETTINGS_FILE,HA_S2_TEMP_SENSOR_NAME_DEFAULT,S2_TEMP_SENSOR_ENABLED_DEFAULT,S2_TEMP_SENSOR_SAMPLING_INTERVAL_DEFAULT,S2_TEMP_SENSOR_MIN_SAMPLING_INTERVAL

def processTempPost(raw_text):
    s2TempEnabledValue = None
    s2TempNameValue = None
    s2TempSamplingIntValue = None
    #
    #   Now look for 's2Temp-Enabled=' in response
    #
    nameSplit = raw_text.split("s2Temp-Enabled=")
    if len(nameSplit)==2:
        s2TempEnabledValue = nameSplit[1].split("\r")[0]
        print("\nFound S2 Temp Sensor Enable = \n",s2TempEnabledValue)
    print(" ")
    #
    #   Now look for 'Text-s2Temp-Name=' in response
    #
    nameSplit = raw_text.split("Text-s2Temp-Name=")
    if len(nameSplit)==2:
        s2TempNameValue = nameSplit[1].split("\r")[0]
        print("\nFound S2 Temp Sensor Friendly Name Value = \n",s2TempNameValue)
    print(" ")
    #
    #   Now look for 'Text-s2Temp-Sampling-Interval=' in response
    #
    nameSplit = raw_text.split("Text-Sampling-Interval=")
    if len(nameSplit)==2:
        s2TempSamplingIntValueString = nameSplit[1].split("\r")[0]
        s2TempSamplingIntValue = getIntFromString(s2TempSamplingIntValueString)
        if s2TempSamplingIntValue == None: s2TempSamplingIntValue = S2_TEMP_SENSOR_SAMPLING_INTERVAL_DEFAULT
        print("\nFound S2 Temp Sensor Sampling Interval Value = \n",s2TempSamplingIntValue)
    print(" ")
    print(" ")
    if checkValue(s2TempNameValue):
        #settingsStruct['motion_friendly_name'] = motionNameValue
        addToSettingsStruct('s2Temp_friendly_name',s2TempNameValue)
    if checkValue(s2TempEnabledValue):
        #settingsStruct['MOTION_SENSOR_ENABLED'] = motionEnabledValue
        addToSettingsStruct('S2_TEMP_SENSOR_ENABLED',s2TempEnabledValue)
    if checkValue(s2TempSamplingIntValue):
        if s2TempSamplingIntValue < S2_TEMP_SENSOR_MIN_SAMPLING_INTERVAL:
            s2TempSamplingIntValue = S2_TEMP_SENSOR_MIN_SAMPLING_INTERVAL
        addToSettingsStruct('S2_TEMP_SENSOR_SAMPLING_INTERVAL',s2TempSamplingIntValue)
        
def s2TempPage():
    print("\n\n---> Inside s2TempPage...")
    gc.collect()
    freeMem = gc.mem_free()
    print("\nFree Memory = ",freeMem,"\n\n")
    deviceName = getSensorNodeDeviceName()
    status,jsonStruct = readSettingsFile(SETTINGS_FILE)
    if status == 0:
        print("read json from disk - json:\n",jsonStruct)
        # read was ok
    else:
        # nothing there - create empty dir
        jsonStruct = {}
    s2TempSensorFname = getSettingValueFromSettingsJson(jsonStruct,'s2Temp_friendly_name',HA_S2_TEMP_SENSOR_NAME_DEFAULT)
    s2TempSensorEnabled = getSettingValueFromSettingsJson(jsonStruct,'S2_TEMP_SENSOR_ENABLED',S2_TEMP_SENSOR_ENABLED_DEFAULT)
    s2TempSensorSamplingInterval = getSettingValueFromSettingsJson(jsonStruct,'S2_TEMP_SENSOR_SAMPLING_INTERVAL',S2_TEMP_SENSOR_SAMPLING_INTERVAL_DEFAULT)
    s2TempSensorMinSamplingInterval = S2_TEMP_SENSOR_MIN_SAMPLING_INTERVAL
    gc.collect()
    buffer = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta http-equiv="Content-type" content="text/html;charset=utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body>
    <h1>S2 Temp Sensor Settings</h1>
    <p class="dotted">{deviceName}</p>
    <br>
    <br>
    <form method="POST" action="/s2Temp" class="wifi-form" enctype="text/plain" align=left >
        <br>
        <div class="wifi-form">
            <label for="Text-s2Temp-Enable">S2 Temp Sensor Enable:</label>
            <select name="s2Temp-Enabled" id="Text-s2Temp-Enable">
                 <option value="">Select One</option>
                 <option value="False">Disabled</option>
                 <option value="True">Enabled</option>
            </select>
        </div>
        <br>
        <div class="wifi-form">
            <label for="Text-s2-Temp-Name">S2 Temp Sensor Friendly Name:</label>
            <input type="text" name="Text-s2Temp-Name" label="NAME" placeholder="{s2TempSensorFname}" >
        </div>
        <br>
        <div class="wifi-form">
            <label for="Text-Sampling-Interval">Sensor Sampling Interval (Secs):</label>
            <input type="text" name="Text-Sampling-Interval" label="NAME" placeholder="{s2TempSensorSamplingInterval}" >
            <label for="Text-Sampling-Interval">(Minimum = {s2TempSensorMinSamplingInterval})</label>
        </div>
        <br>
        <div class="wifi-form">
            <input type="submit" value="Submit and return to Main Page">
        </div>

    </form>
    </body></html>
    """
    setHtmlBuffer(buffer)
    gc.collect()

    #return htmlBuffer