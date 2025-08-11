'''

    SensorNode
    Server Files for
    Motion Sensor for Connector S2
    TNB Technologies, LLC

'''

import gc
from sensorNodeUtils import readSettingsFile,getSettingValueFromSettingsJson,getSensorNodeDeviceName,checkValue,addToSettingsStruct,getIntFromString,setHtmlBuffer
from globals import SETTINGS_FILE,HA_MOTION_SENSOR_NAME_DEFAULT,MOTION_SENSOR_ENABLED_DEFAULT,MOTION_SENSOR_ACTIVE_DURATION_DEFAULT,MOTION_SENSOR_ACTIVE_DURATION_MINIMUM

def processMotionPost(raw_text):
    motionEnabledValue = None
    motionNameValue = None
    motionTimeValue = None
    #
    #	Now look for 'Motion-Enabled=' in response
    #
    nameSplit = raw_text.split("Motion-Enabled=")
    if len(nameSplit)==2:
        motionEnabledValue = nameSplit[1].split("\r")[0]
        print("\nFound Motion Sensor Enable = \n",motionEnabledValue)
    print(" ")
    #
    #	Now look for 'Text-Motion-Name=' in response
    #
    nameSplit = raw_text.split("Text-Motion-Name=")
    if len(nameSplit)==2:
        motionNameValue = nameSplit[1].split("\r")[0]
        print("\nFound Motion Sensor Friendly Name Value = \n",motionNameValue)
    print(" ")
    #
    #	Now look for 'Text-Motion-Time=' in response
    #
    nameSplit = raw_text.split("Text-Motion-Time=")
    if len(nameSplit)==2:
        motionTimeValueString = nameSplit[1].split("\r")[0]
        motionTimeValue = getIntFromString(motionTimeValueString)
        if motionTimeValue == None: motionTimeValue = MOTION_SENSOR_ACTIVE_DURATION_DEFAULT
        print("\nFound Motion Sensor Active Time Value = \n",motionTimeValue)
    print(" ")
    if checkValue(motionNameValue):
        #settingsStruct['motion_friendly_name'] = motionNameValue
        addToSettingsStruct('motion_friendly_name',motionNameValue)
    if checkValue(motionEnabledValue):
        #settingsStruct['MOTION_SENSOR_ENABLED'] = motionEnabledValue
        addToSettingsStruct('MOTION_SENSOR_ENABLED',motionEnabledValue)
    if checkValue(motionTimeValue):
        if motionTimeValue < MOTION_SENSOR_ACTIVE_DURATION_MINIMUM:
            motionTimeValue = MOTION_SENSOR_ACTIVE_DURATION_MINIMUM
        #settingsStruct['MOTION_SENSOR_ACTIVE_DURATION'] = motionTimeValue
        addToSettingsStruct('MOTION_SENSOR_ACTIVE_DURATION',motionTimeValue)
        
def motionPage():
    print("\n\n---> Inside motionPage...")
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
    motionSensorFname = getSettingValueFromSettingsJson(jsonStruct,'motion_friendly_name',HA_MOTION_SENSOR_NAME_DEFAULT)
    motionSensorEnabled = getSettingValueFromSettingsJson(jsonStruct,'MOTION_SENSOR_ENABLED',MOTION_SENSOR_ENABLED_DEFAULT)
    motionSensorActiveDurationTime = getSettingValueFromSettingsJson(jsonStruct,'MOTION_SENSOR_ACTIVE_DURATION',MOTION_SENSOR_ACTIVE_DURATION_DEFAULT)
    motionActiveMinimum = MOTION_SENSOR_ACTIVE_DURATION_MINIMUM
    
    buffer = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta http-equiv="Content-type" content="text/html;charset=utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body>
    <h1>Motion Sensor Settings</h1>
    <p class="dotted">{deviceName}</p>
    <br>
    <br>
    <form method="POST" action="/motion" class="wifi-form" enctype="text/plain" align=left >
        <br>
        <div class="wifi-form">
            <label for="Text-Motion-Enable">Motion Sensor Enable:</label>
            <select name="Motion-Enabled" id="Text-Motion-Enable">
                 <option value="">Select One</option>
                 <option value="False">Disabled</option>
                 <option value="True">Enabled</option>
            </select>
        </div>
        <br>
        <div class="wifi-form">
            <label for="Text-Motion-Name">Motion Sensor Friendly Name:</label>
            <input type="text" name="Text-Motion-Name" label="NAME" placeholder="{motionSensorFname}" >
        </div>
        <br>
        <div class="wifi-form">
            <label for="Text-Motion-Time">Sensor Active Time (Secs):</label>
            <input type="text" name="Text-Motion-Time" label="NAME" placeholder="{motionSensorActiveDurationTime}" >
            <label for="Text-Motion-Time">(Minimum = {motionActiveMinimum})</label>
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
    print("leaving motionPage...")
