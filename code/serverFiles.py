'''

    WebPage Files for SensorNode Setup/Config WebServer
    
    
'''

from sensorNodeUtils import readSettingsFile,getSettingValueFromSettingsJson,getSettingsStruct,getSensorNodeDeviceName,getPicoAPSSID
from globals import SETTINGS_FILE,SLE_JUMPER_ENABLES,homeAssistantUrl,VERSION,HA_MOTION_SENSOR_NAME_DEFAULT,MOTION_SENSOR_ENABLED_DEFAULT
from globals import MOTION_SENSOR_ACTIVE_DURATION_DEFAULT,MOTION_SENSOR_ACTIVE_DURATION_MINIMUM,HA_CONTACT_SENSOR_NAME_DEFAULT
from globals import CONTACT_SENSOR_ENABLED_DEFAULT,CONTACT_SENSOR_CLOSED_DURATION_DEFAULT,CONTACT_SENSOR_CLOSED_DURATION_MINIMUM,font_family
from globals import HA_S2_TEMP_SENSOR_NAME_DEFAULT,S2_TEMP_SENSOR_ENABLED_DEFAULT,HA_S2_WATER_SENSOR_NAME_DEFAULT,S2_WATER_SENSOR_ENABLED_DEFAULT,
from globals import S2_WATER_SENSOR_ACTIVE_DURATION_DEFAULT,S2_WATER_SENSOR_ACTIVE_DURATION_MINIMUM
from sensorNodeUtils import checkValue,addToSettingsStruct,getIntFromString,getHtmlBuffer,setHtmlBuffer
import gc


def processContactPost(raw_text):
    contactEnabledValue = None
    contactNameValue = None
    contactTimeValue = None
    #
    #	Now look for 'Contact-Enabled=' in response
    #
    nameSplit = raw_text.split("Contact-Enabled=")
    if len(nameSplit)==2:
        contactEnabledValue = nameSplit[1].split("\r")[0]
        print("\nFound Contact Sensor Enable = \n",contactEnabledValue)
    print(" ")
    #
    #	Now look for 'Text-Contact-Name=' in response
    #
    nameSplit = raw_text.split("Text-Contact-Name=")
    if len(nameSplit)==2:
        contactNameValue = nameSplit[1].split("\r")[0]
        print("\nFound Contact Sensor Friendly Name Value = \n",contactNameValue)
    print(" ")
    #
    #	Now look for 'Text-Contact-Time=' in response
    #
    nameSplit = raw_text.split("Text-Contact-Time=")
    if len(nameSplit)==2:
        contactTimeValueString = nameSplit[1].split("\r")[0]
        contactTimeValue = getIntFromString(contactTimeValueString)
        if contactTimeValue == None: contactTimeValue = CONTACT_SENSOR_CLOSED_DURATION_DEFAULT
        print("\nFound Contact Sensor Duration Time Value = \n",contactTimeValue)
    print(" ")
    if checkValue(contactNameValue):
        #settingsStruct['contact_friendly_name'] = contactNameValue
        addToSettingsStruct('contact_friendly_name',contactNameValue)
    if checkValue(contactEnabledValue):
        #settingsStruct['CONTACT_SENSOR_ENABLED'] = contactEnabledValue
        addToSettingsStruct('CONTACT_SENSOR_ENABLED',contactEnabledValue)
    if checkValue(contactTimeValue):
        if contactTimeValue < CONTACT_SENSOR_CLOSED_DURATION_MINIMUM:
            contactTimeValue = CONTACT_SENSOR_CLOSED_DURATION_MINIMUM
        #settingsStruct['CONTACT_SENSOR_CLOSED_DURATION'] = contactTimeValue
        addToSettingsStruct('CONTACT_SENSOR_CLOSED_DURATION',contactTimeValue)

def basePage():
    print("\n\n---> Inside basePage...")
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
    pw = getSettingValueFromSettingsJson(jsonStruct,'pw',None)
    ha_url_prefix = getSettingValueFromSettingsJson(jsonStruct,'HA_URL_PREFIX',homeAssistantUrl)
    sle_enables = getSettingValueFromSettingsJson(jsonStruct,'SLE_JUMPER_ENABLES',SLE_JUMPER_ENABLES)
    if ssid == None:
        ssidEntry = "Enter SSID here"
    else:
        ssidEntry = ssid
    if pw == None:
        pwEntry = "Enter Password here"
    else:
        pwEntry = pw        
    if ha_url_prefix == None:
        urlPrefixEntry = "Enter HA URL here"
    else:
        urlPrefixEntry = ha_url_prefix
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
    <h1>SensorNode Server</h1>
    <p class="dotted">{deviceName}</p>
    <p class="dotted">ID: {accessPointID}</p>
    <p class="dotted">SW Version: {VERSION}</p>
    <br>
    <a href='/contact'>Contact Sensor Settings</a>
    <br>
    <br>
    <a href='/motion'>Motion Sensor Settings</a>
    <br>
    <br>
    <br>
    <form method="POST" action="/" class="wifi-form" enctype="text/plain" align=left >
        <div class="wifi-form">
            <label for="Text-SSID">Wifi - SSID:</label>
            <input type="text" name="Text-SSID" placeholder="{ssidEntry}">
        </div>
        <br>
        <div class="wifi-form">
            <label for="Text-PW">Wifi - Password:</label>
            <input type="text" name="Text-PW" label="PW" placeholder="{pwEntry}">
        </div>
        <br>
        <div class="wifi-form">
            <label for="Text-SLE-Enables">SLE Jumper Enables:</label>
            <select name="SLE-Enables" id="Text-SLE-Enables">
                 <option value="">Select One</option>
                 <option value="EXT">External LED Only</option>
                 <option value="INT">Internal LED Only</option>
                 <option value="BOTH">Both LEDs</option>
            </select>
        </div>
        <br>
        <div class="wifi-form">
            <label for="URL-Prefix">HA URL Prefix:</label>
            <input type="text" name="URL-Prefix" label="URL_PREFIX" placeholder="{urlPrefixEntry}">
        </div>
        <br>
        <br>
        <br>
        <br>
        <div class="wifi-form">
            <input type="submit" value="Submit and Restart">
        </div>
        <br>
    </form>


    </body></html>

    """
    setHtmlBuffer(buffer)
    gc.collect()
    freeMem = gc.mem_free()
    print("\nFree Memory after html declare = ",freeMem,"\n\n")
    print("settingsStruct:\n",settingsStruct)
    print("\n\n---> leaving basepage and returning base html...\n\n")

def contactPage():
    print("\n\n---> Inside contactPage...")
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
    contactSensorFriendlyName = getSettingValueFromSettingsJson(jsonStruct,'contact_friendly_name',HA_CONTACT_SENSOR_NAME_DEFAULT)
    contactSensorEnabled = getSettingValueFromSettingsJson(jsonStruct,'CONTACT_SENSOR_ENABLED',CONTACT_SENSOR_ENABLED_DEFAULT)
    contactSensorClosedDurationTime = getSettingValueFromSettingsJson(jsonStruct,'CONTACT_SENSOR_CLOSED_DURATION',CONTACT_SENSOR_CLOSED_DURATION_DEFAULT)
    contactClosedMin = CONTACT_SENSOR_CLOSED_DURATION_MINIMUM
    
    buffer = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta http-equiv="Content-type" content="text/html;charset=utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body>
    <h1>Contact Sensor Settings</h1>
    <p class="dotted">{deviceName}</p>
    <br>
    <form method="POST" action="/contact" class="wifi-form" enctype="text/plain" align=left >
        <br>
        <div class="wifi-form">
            <label for="Text-Contact-Enable">Contact Sensor Enable:</label>
            <select name="Contact-Enabled" id="Text-Contact-Enable">
                 <option value="">Select One</option>
                 <option value="False">Disabled</option>
                 <option value="True">Enabled</option>
            </select>
        </div>
        <br>
        <div class="wifi-form">
            <label for="Text-Contact-Name">Contact Sensor Friendly Name:</label>
            <input type="text" name="Text-Contact-Name" label="NAME" placeholder="{contactSensorFriendlyName}" >
        </div>
        <br>
        <div class="wifi-form">
            <label for="Text-Contact-Time">Sensor Closed Time (Secs):</label>
            <input type="text" name="Text-Contact-Time" label="NAME" placeholder="{contactSensorClosedDurationTime}" >
            <label for="Text-Contact-Time">(Minimum = {contactClosedMin})</label>
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
    print("leaving contactPage...")


def successPage():
    print("\n\nInsde success page...\n\n")
    
    buffer = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta http-equiv="Content-type" content="text/html;charset=utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
    html{{font-family: {font_family}; background-color: lightgrey;
    display:inline-block; margin: 0px auto; text-align: center;}}
      h1{{color: rgb(0,155,0); width: 200; word-wrap: break-word; padding: 2vh; font-size: 35px;}}
      p{{font-size: 1.5rem; width: 200; word-wrap: break-word;}}
      .button{{font-family: {font_family};display: inline-block;
      background-color: black; border: none;
      border-radius: 4px; color: white; padding: 16px 40px;
      text-decoration: none; font-size: 30px; margin: 2px; cursor: pointer;}}
      p.dotted {{margin: auto;
      width: 75%; font-size: 25px; text-align: center;}}
    </style>
    </head>
    <body>
    <title>SensorNode Server</title>
    <h1>SensorNode Server</h1>
    <br>
    <h1>SUCCESS</h1>
    <br>
    <p class="dotted">SensorNode will now restart using new settings and connect to local wifi network</p>
    </body></html>
    """
    setHtmlBuffer(buffer)
    gc.collect()
    print("leaving successPage...")

def failPage(failure_message):
    
    buffer = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta http-equiv="Content-type" content="text/html;charset=utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
    html{{font-family: {font_family}; background-color: lightgrey;
    display:inline-block; margin: 0px auto; text-align: center;}}
      h1{{color: rgb(255,255,255); width: 200; word-wrap: break-word; padding: 2vh; font-size: 35px;}}
      p{{font-size: 1.5rem; width: 200; word-wrap: break-word;}}
      .button{{font-family: {font_family};display: inline-block;
      background-color: black; border: none;
      border-radius: 4px; color: white; padding: 16px 40px;
      text-decoration: none; font-size: 30px; margin: 2px; cursor: pointer;}}
      p.dotted {{margin: auto;
      width: 75%; font-size: 25px; text-align: center;}}
    </style>
    </head>
    <body>
    <title>SensorNode Server</title>
    <h1>SensorNode Server</h1>
    <br>
    <h1>ERROR</h1>
    <br>
    <p class="dotted">{failure_message}</p>

    </body></html>
    """
    setHtmlBuffer(buffer)
    gc.collect()
    print("leaving failPage...")


