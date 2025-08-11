'''

    SensorNode
    Server Files for
    Diagnostic Counts Display

    TNB Technologies, LLC

'''

import gc
from sensorNodeUtils import readSettingsFile,getSettingValueFromSettingsJson,getSensorNodeDeviceName,checkValue,addToSettingsStruct,setHtmlBuffer,getBoolSetting
from globals import SETTINGS_FILE,HA_S2_TEMP_SENSOR_NAME_DEFAULT,S2_TEMP_SENSOR_ENABLED_DEFAULT,S2_TEMP_SENSOR_SAMPLING_INTERVAL_DEFAULT,S2_TEMP_SENSOR_MIN_SAMPLING_INTERVAL
from globals import REPORT_COUNTS_DEFAULT

            
def countsPage():
    print("\n\n---> Inside countsPage...")
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
    reportCountsText = "NO"
    reportCounts = getBoolSetting('REPORT_COUNTS',REPORT_COUNTS_DEFAULT,jsonStruct)
    if reportCounts == True:
        reportCountsText = "YES"
    else:
        reportCountsText = "NO"
    rebootCount = getSettingValueFromSettingsJson(jsonStruct,'REBOOT_COUNT',0)
    wifiErrorsCount = getSettingValueFromSettingsJson(jsonStruct,'WIFI_ERRORS_COUNT',0)
    sendDataCount = getSettingValueFromSettingsJson(jsonStruct,'SEND_DATA_COUNT',0)
    sendDataErrorsCount = getSettingValueFromSettingsJson(jsonStruct,'SEND_DATA_ERRORS_COUNT',0)
    gc.collect()
    
    buffer = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta http-equiv="Content-type" content="text/html;charset=utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body>
    <h1>Diagnostics</h1>
    <p class="dotted">{deviceName}</p>
    <br>
    <h3>If Diagnostics are enabled, updated count values will be stored in NV memory.</h3>
    <br>
    <p class="dotted">Diagnostics Currently Enabled: {reportCountsText}</p>
    <form method="POST" action="/changeReportCountsSetting" class="diagnosticSettingsForm" enctype="text/plain" align=left >
        <div class="diagnosticSettingsForm">
            <label for="diagnosticSetting">Select Diagnostics On/Off:</label>
            <select name="diagOnOff" id="diagnosticSetting">
                 <option value="">Select One</option>
                 <option value="False">Diagnostics OFF</option>
                 <option value="True">Diagnostics ON</option>
            </select>
        </div>
        <br>
        <div class="diagnosticSettingsForm">
            <input type="submit" value="Confirm Diagnostics Setting">
        </div>
    </form>
    <br>
    <p class="dotted">Reboot Count: {rebootCount}</p>
    <form method="POST" action="/clearRebootCount" class="wifi-form" enctype="text/plain" align=left >
        <div class="wifi-form">
            <input type="submit" value="Clear Reboot Count">
        </div>
    </form>
    <br>
    <p class="dotted">Wifi Error Count: {wifiErrorsCount}</p>
    <form method="POST" action="/clearWifiErrorsCount" class="wifi-form" enctype="text/plain" align=left >
        <div class="wifi-form">
            <input type="submit" value="Clear Wifi Errors Count">
        </div>
    </form>
    <br>
    <p class="dotted">Send Data Count: {sendDataCount}</p>
    <form method="POST" action="/clearSendDataCount" class="wifi-form" enctype="text/plain" align=left >
        <div class="wifi-form">
            <input type="submit" value="Clear Send Data Count">
        </div>
    </form>
    <br>
    <p class="dotted">Send Data Error Count: {sendDataErrorsCount}</p>
    <form method="POST" action="/clearSendDataErrorsCount" class="wifi-form" enctype="text/plain" align=left >
        <div class="wifi-form">
            <input type="submit" value="Clear Send Data Errors Count">
        </div>
    </form>
    <br>
    <br>
    <br>
    <a href='/'>Click Here to go back to Home Page</a>
    </body></html>
    """
    setHtmlBuffer(buffer)
    gc.collect()

    #return htmlBuffer
