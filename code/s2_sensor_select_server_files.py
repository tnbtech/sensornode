'''

    SensorNode
    Server Files for
    S2 Sensor Selection

    TNB Technologies, LLC

'''

import gc
from sensorNodeUtils import readSettingsFile,getSettingValueFromSettingsJson,getSensorNodeDeviceName,checkValue,addToSettingsStruct,setHtmlBuffer
from globals import SETTINGS_FILE
from adafruit_httpserver import Response

def processS2SensorPost(raw_text):
    #
    #
    #
    s2MotionSensorEnabled = False
    s2TempSensorEnabled = False
    s2WaterSensorEnabled = False
    s2SensorTypeValue = None
    #
    #   Now look for 'S2-Type=' in response
    #
    nameSplit = raw_text.split("S2-Type=")
    if len(nameSplit)==2:
        s2SensorTypeValue = nameSplit[1].split("\r")[0]
        print("\nFound S2 Type = \n",s2SensorTypeValue)
    print(" ")
    if checkValue(s2SensorTypeValue):
        addToSettingsStruct('s2_sensor_type',s2SensorTypeValue)
    #
    #	then load proper html and return that page
    #
    if s2SensorTypeValue == "TEMP":
        from temp_sensor_server_files import s2TempPage
        s2TempPage()
    elif s2SensorTypeValue == "WATER":
        from water_sensor_server_files import s2WaterPage
        s2WaterPage()
    elif s2SensorTypeValue == "MOTION":
        from motion_sensor_server_files import motionPage
        motionPage()
    else:
        from new_base_page_server_files import newBasePage
        newBasePage()
    '''
    #
    #	then return html
    #
    return Response(request, getHtmlBuffer(),content_type='text/html')
    '''
    
    
