'''

    SensorNode
    Server Files for
    Water Sensor for Connector S2
    TNB Technologies, LLC

'''

import gc
from sensorNodeUtils import readSettingsFile,getSettingValueFromSettingsJson,getSensorNodeDeviceName,checkValue,addToSettingsStruct,getIntFromString,setHtmlBuffer
from globals import SETTINGS_FILE,HA_S2_WATER_SENSOR_NAME_DEFAULT,S2_WATER_SENSOR_ENABLED_DEFAULT,S2_WATER_SENSOR_ACTIVE_DURATION_DEFAULT,S2_WATER_SENSOR_ACTIVE_DURATION_MINIMUM

def processWaterPost(raw_text):
    s2WaterEnabledValue = None
    s2WaterNameValue = None
    s2WaterTimeValue = None
    #
    #   Now look for 's2Water-Enabled=' in response
    #
    nameSplit = raw_text.split("s2Water-Enabled=")
    if len(nameSplit)==2:
        s2WaterEnabledValue = nameSplit[1].split("\r")[0]
        print("\nFound S2 Water Sensor Enable = \n",s2WaterEnabledValue)
    print(" ")
    #
    #   Now look for 'Text-s2Water-Name=' in response
    #
    nameSplit = raw_text.split("Text-s2Water-Name=")
    if len(nameSplit)==2:
        s2WaterNameValue = nameSplit[1].split("\r")[0]
        print("\nFound S2 Water Sensor Friendly Name Value = \n",s2WaterNameValue)
    print(" ")
    #
    #   Now look for 'Text-s2Water-Time=' in response
    #
    nameSplit = raw_text.split("Text-s2Water-Time=")
    if len(nameSplit)==2:
        s2WaterTimeValueString = nameSplit[1].split("\r")[0]
        s2WaterTimeValue = getIntFromString(s2WaterTimeValueString)
        if s2WaterTimeValue == None: s2WaterTimeValue = S2_WATER_SENSOR_ACTIVE_DURATION_DEFAULT
        print("\nFound S2 Water Sensor Active Time Value = \n",s2WaterTimeValue)
    print(" ")
    if checkValue(s2WaterNameValue):
        #settingsStruct['motion_friendly_name'] = motionNameValue
        addToSettingsStruct('s2Water_friendly_name',s2WaterNameValue)
    if checkValue(s2WaterEnabledValue):
        #settingsStruct['MOTION_SENSOR_ENABLED'] = motionEnabledValue
        addToSettingsStruct('S2_WATER_SENSOR_ENABLED',s2WaterEnabledValue)
    if checkValue(s2WaterTimeValue):
        if s2WaterTimeValue < S2_WATER_SENSOR_ACTIVE_DURATION_MINIMUM:
            s2WaterTimeValue = S2_WATER_SENSOR_ACTIVE_DURATION_MINIMUM
        #settingsStruct['MOTION_SENSOR_ACTIVE_DURATION'] = motionTimeValue
        addToSettingsStruct('S2_WATER_SENSOR_ACTIVE_DURATION',s2WaterTimeValue)
        
def s2WaterPage():
    print("\n\n---> Inside s2WaterPage...")
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
    s2WaterSensorFname = getSettingValueFromSettingsJson(jsonStruct,'s2Water_friendly_name',HA_S2_WATER_SENSOR_NAME_DEFAULT)
    s2WaterSensorEnabled = getSettingValueFromSettingsJson(jsonStruct,'S2_WATER_SENSOR_ENABLED',S2_WATER_SENSOR_ENABLED_DEFAULT)
    s2WaterSensorActiveDurationTime = getSettingValueFromSettingsJson(jsonStruct,'S2_WATER_SENSOR_ACTIVE_DURATION',S2_WATER_SENSOR_ACTIVE_DURATION_DEFAULT)
    s2WaterSensorActiveMinimum = S2_WATER_SENSOR_ACTIVE_DURATION_MINIMUM
    gc.collect()
    buffer = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta http-equiv="Content-type" content="text/html;charset=utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body>
    <h1>S2 Water Sensor Settings</h1>
    <p class="dotted">{deviceName}</p>
    <br>
    <br>
    <form method="POST" action="/s2Water" class="wifi-form" enctype="text/plain" align=left >
        <br>
        <div class="wifi-form">
            <label for="Text-s2Water-Enable">S2 Water Sensor Enable:</label>
            <select name="s2Water-Enabled" id="Text-s2Water-Enable">
                 <option value="">Select One</option>
                 <option value="False">Disabled</option>
                 <option value="True">Enabled</option>
            </select>
        </div>
        <br>
        <div class="wifi-form">
            <label for="Text-s2Water-Name">S2 Water Sensor Friendly Name:</label>
            <input type="text" name="Text-s2Water-Name" label="NAME" placeholder="{s2WaterSensorFname}" >
        </div>
        <br>
        <div class="wifi-form">
            <label for="Text-s2Water-Time">Sensor Active Time (Secs):</label>
            <input type="text" name="Text-s2Water-Time" label="NAME" placeholder="{s2WaterSensorActiveDurationTime}" >
            <label for="Text-s2Water-Time">(Minimum = {s2WaterSensorActiveMinimum})</label>
        </div>
        <br>
        <br>
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