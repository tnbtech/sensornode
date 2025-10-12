'''

    SensorNode
    Server Files for
    New Base Page

    TNB Technologies, LLC

'''
import gc
from sensorNodeUtils import readSettingsFile,getSettingValueFromSettingsJson,getSensorNodeDeviceName,checkValue,addToSettingsStruct,getIntFromString,setHtmlBuffer
from sensorNodeUtils import getPicoAPSSID,getSettingsStruct,getHtmlBuffer
from globals import SETTINGS_FILE,HA_S2_TEMP_SENSOR_NAME_DEFAULT,S2_TEMP_SENSOR_ENABLED_DEFAULT,homeAssistantUrl,SLE_JUMPER_ENABLES
from globals import VERSION,STATUS_UPDATE_INTERVAL_DEFAULT,STATUS_UPDATE_INTERVAL_MINIMUM,STATUS_UPDATE_INTERVAL_MAXIMUM

def newBasePage():
    print("\n\n---> Inside newBasePage...")
    deviceName = getSensorNodeDeviceName()
    accessPointID = getPicoAPSSID()
    print("sensornodeDeviceName = ",deviceName)
    print("access point ID = ",accessPointID)
    settingsStruct = getSettingsStruct()
    status,jsonStruct = readSettingsFile(SETTINGS_FILE)
    if status == 0:
        print("read json from disk - json:\n",jsonStruct)
        # read was ok
    else:
        # nothing there - create empty dir
        jsonStruct = {}
    ssid = getSettingValueFromSettingsJson(jsonStruct,'ssid',None)
    ha_url_prefix = getSettingValueFromSettingsJson(jsonStruct,'HA_URL_PREFIX',homeAssistantUrl)
    sle_enables = getSettingValueFromSettingsJson(jsonStruct,'SLE_JUMPER_ENABLES',SLE_JUMPER_ENABLES)
    stored_s2_sensor_selection = getSettingValueFromSettingsJson(jsonStruct,'s2_sensor_type',None)
    snName = getSettingValueFromSettingsJson(jsonStruct,'SENSORNODE_NAME','')
    wifiCheckIpAdd = getSettingValueFromSettingsJson(jsonStruct,'WIFI_CHECK_ADD',None)
    statusUpdateIntervalString = getSettingValueFromSettingsJson(jsonStruct,'STATUS_UPDATE_INTERVAL',STATUS_UPDATE_INTERVAL_DEFAULT)
    statusUpdateIntervalInt = getIntFromString(statusUpdateIntervalString)
    if statusUpdateIntervalInt == None: statusUpdateIntervalInt = STATUS_UPDATE_INTERVAL_DEFAULT
    statusUpdateIntervalMin = STATUS_UPDATE_INTERVAL_MINIMUM
    statusUpdateIntervalmax = STATUS_UPDATE_INTERVAL_MAXIMUM
    
    if 's2_sensor_type' in settingsStruct:
        current_s2_sensor_selection = settingsStruct['s2_sensor_type']
    else:
        current_s2_sensor_selection = None
    if ssid == None:
        ssidEntry = "Enter SSID here"
    else:
        ssidEntry = ssid        
    if ha_url_prefix == None:
        urlPrefixEntry = "Enter HA URL Prefix here"
    else:
        urlPrefixEntry = ha_url_prefix
    if wifiCheckIpAdd == None:
        wifiCheckEntry = "Enter IP Add here"
    else:
        wifiCheckEntry = wifiCheckIpAdd

    print("got all settings...")
    gc.collect()
    freeMem = gc.mem_free()
    print("\nFree Memory before html declare = ",freeMem,"\n\n")
    buffer = getHtmlBuffer()
    buffer = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta http-equiv="Content-type" content="text/html;charset=utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body>
    <h1>SensorNode Configuration Server</h1>
    <p class="dotted">{deviceName}</p>
    <p class="dotted">SSID: {accessPointID}</p>
    <p class="dotted">SW Version: {VERSION}</p>
    <h4>Sensor Settings<h4>
    <a href='/contact'>Connector S1 - Contact Sensor Settings</a>
    <br>
    <h5>NOTE: Connector S2 Can Support ONE of Three Types of Sensors</h5>
    <p class="dotted">Stored S2 Type Selection: {stored_s2_sensor_selection}</p>
    <p class="dotted">Current S2 Type Selection: {current_s2_sensor_selection}</p>
    <form method="POST" action="/s2SensorSelect" class="s2-sensor-form" enctype="text/plain" align=left >
        <div class="s2-sensor-form">
            <label for="S2-Sensor-Type">Connector S2 - Select Sensor Type:</label>
            <select name="S2-Type" id="S2-Sensor-Type">
                 <option value="">Select One</option>
                 <option value="MOTION">Motion</option>
                 <option value="TEMP">Temp</option>
                 <option value="WATER">Water</option>
            </select>
        </div>
        <br>
        <div class="s2-sensor-form">
            <input type="submit" value="Go to S2 Sensor Settings">
        </div>
    </form>
    <h4>General Settings</h4>
    <form method="POST" action="/" class="wifi-form" enctype="text/plain" align=left >
        <div class="wifi-form">
            <label for="Text-SSID">Wifi - SSID:</label>
            <input type="text" name="Text-SSID" placeholder="{ssidEntry}">
        </div>
        <br>
        <div class="wifi-form">
            <label for="Text-PW">Wifi - Password:</label>
            <input type="password" name="Text-PW" label="PW" placeholder="Enter PW Here">
        </div>
        <br>
        <input type="checkbox" id="wifi-check" name="WIFI-CHECK-ENABLED" value="True" checked/>
        <label for="WIFI-CHECK-ENABLED"> Wifi Periodic Check</label>
        <br>
        <br>
        <div class="wifi-form">
            <label for="Wifi-Check-IP-Add">Wifi Check IP Address:</label>
            <input type="text" name="Wifi-Check-IP-Add" label="WIFI_CHECK_IP_ADD" placeholder="{wifiCheckEntry}">
        </div>
        <br>
        <div class="wifi-form">
            <label for="URL-Prefix">HA URL:</label>
            <input type="text" name="URL-Prefix" label="URL_PREFIX" placeholder="{urlPrefixEntry}">
        </div>
        <br>
        <div class="wifi-form">
            <label for="HA-LLAT">HA LLAT:</label>
            <input type="password" name="HA-LLAT" label="HA_LLAT" placeholder="Paste HA LLAT Here">
        </div>
        <br>
        <input type="checkbox" id="status-update" name="STATUS-UPDATE-ENABLED" value="True" checked/>
        <label for="STATUS-UPDATE-ENABLED"> Send Periodic Status Updates</label>
        <br>
        <br>
        <div class="wifi-form">
            <label for="Status-Update-Interval">Status Update Interval (sec):</label>
            <input type="text" name="Status-Update-Interval" label="STATUS_UPDATE_INTERVAL" placeholder="{statusUpdateIntervalInt}">
            <label for="Status-Update-Interval">(Min = {statusUpdateIntervalMin}, Max = {statusUpdateIntervalmax})</label>
        </div>
        <br>
        <div class="wifi-form">
            <label for="Text-SLE-Enables">Status Light Enables:</label>
            <select name="SLE-Enables" id="Text-SLE-Enables">
                 <option value="">Select One</option>
                 <option value="EXT">External LED Only</option>
                 <option value="INT">Internal LED Only</option>
                 <option value="BOTH">Both LEDs</option>
            </select>
        </div>
        <br>
        <div class="wifi-form">
            <label for="Text-Name">SensorNode Name Suffix: </label>
            <input type="text" name="Text-Name" label="Name" placeholder="{snName}">
        </div>
        <h5>Hit 'Submit and Restart' to store your selections and restart:<h5>
        <div class="wifi-form">
            <input type="submit" value="Submit and Restart">
        </div>
        <br>
    </form>
    <br>
    <br>
    <a href='/counts'>Diagnostics</a>
    <br>

    </body></html>

    """
    setHtmlBuffer(buffer)
    gc.collect()
    freeMem = gc.mem_free()
    print("\nFree Memory after html declare = ",freeMem,"\n\n")
    print("settingsStruct:\n",settingsStruct)
    print("\n\n---> leaving basepage and returning base html...\n\n")