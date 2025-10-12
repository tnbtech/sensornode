'''


    SensorNode Access Point Server Code
    
    sn_server_code.py
    
    by TNB Technologies, LLC
    
    Tom Berarducci
    
    2024
    
    
'''

from sensorNodeUtils import setHtmlBuffer,getHtmlBuffer,setLeds,getAPSSID,wd_feed,setSettingsStruct,getWifiCreds,Timer,countLedTicks,addToSettingsStruct,getIntFromString
from sensorNodeUtils import restartIntoStationMode,restartIntoAPMode,writeDataToSettings,checkValue,getSettingsStruct,getForceAPModePinValue,writeSettingsFile
from sensorNodeUtils import signalErrorCondition
from globals import AP_PW, LED_BLINK_DURATION_AP_ENABLED,WAIT_TIME_TICK,WIFI_RETRY_DURATION,S2_SENSOR_CONFIGURATION,STATUS_UPDATE_INTERVAL_MINIMUM,STATUS_UPDATE_INTERVAL_MAXIMUM
from globals import STATUS_UPDATE_INTERVAL_DEFAULT
import socketpool
import wifi
import gc
import time
from microcontroller import cpu as micro_cpu
import board
import digitalio
from microcontroller import reset as micro_reset


# these must be global
from adafruit_httpserver import Server, Request, Response, POST
pool = socketpool.SocketPool(wifi.radio)
server = Server(pool, "/static", debug=True)

#
#	Pico Web Server Declares
#

SERVER_HOST_ADD = "192.168.4.1"

# HTML Page Viewport settings

WIDTH = 128
HEIGHT = 64
offset_y = 5


def initializeGlobalBuffer():
    #
    #	initializes global buffer for home html page, reused over and over to save RAM
    #
    gc.collect()
    freeMem = gc.mem_free()
    print("Inside initialilzeGlobalBuffer - Free Memory = ",freeMem)
    print("\n\n---> Importing basePage file...\n\n")
    #from serverFiles import basePage
    gc.collect()
    freeMem = gc.mem_free()
    print("After import - Free Memory = ",freeMem)
    struct = {}
    setSettingsStruct(struct)
    #htmlBuffer = basePage()
    #setHtmlBuffer(basePage())
    
#
#	Server Pages
#
@server.route("/")
def base(request: Request):  # pylint: disable=unused-argument
    #  serve the HTML f string
    #  with content type text/html
    global wifiRetryTimer
    print("\n\nInside BASE...")
    gc.collect()
    wd_feed()
    freeMem = gc.mem_free()
    # if you get here that means someone is attempting to access the server, so INCREASE wifi retry to 5 times normal interval to give them time
    try:
        wifiRetryTimer.timeDelay = WIFI_RETRY_DURATION * 5
        wifiRetryTimer.clearTimer()
    except:
        print("Inside BASE - cannot set wifi retry timer - ignoring.")
    else:
        print("wifi retry timer started and set to ",WIFI_RETRY_DURATION*5,"seconds")
    print("\nFree Memory before base page is returned = ",freeMem,"\n\n")
    #setHtmlBuffer(basePage())
    if S2_SENSOR_CONFIGURATION == "OLD":
        from serverFiles import basePage
        basePage()
    else:
        from new_base_page_server_files import newBasePage
        newBasePage()
    return Response(request, getHtmlBuffer(), content_type='text/html')


@server.route("/contact")
def contact(request: Request):
    # serve contact sensor settings page
    from serverFiles import contactPage
    gc.collect()
    wd_feed()
    contactPage()
    return Response(request, getHtmlBuffer(), content_type='text/html')

@server.route("/motion")
def motion(request: Request):
    # serve motion sensor settings page
    from motion_sensor_server_files import motionPage
    gc.collect()
    wd_feed()
    motionPage()
    return Response(request, getHtmlBuffer(), content_type='text/html')

@server.route("/s2Water")
def s2Water(request: Request):
    # serve s2 water sensor settings page
    from water_sensor_server_files import s2WaterPage
    gc.collect()
    wd_feed()
    s2WaterPage()
    return Response(request, getHtmlBuffer(), content_type='text/html')

@server.route("/s2Temp")
def s2Temp(request: Request):
    # serve s2 temp sensor settings page
    from temp_sensor_server_files import s2TempPage
    gc.collect()
    wd_feed()
    s2TempPage()
    return Response(request, getHtmlBuffer(), content_type='text/html')


@server.route("/counts")
def counts(request: Request):
    # present stored count values and enable their management
    gc.collect()
    wd_feed()
    from countsPage_server_files import countsPage
    countsPage()
    return Response(request, getHtmlBuffer(), content_type='text/html')


#
#	Server POST Routines
#
@server.route("/", POST)
def processPost(request: Request):
    global readyToReset
    print("\nRecieved POST\n")
    wd_feed()
    #  get the raw text
    raw_text = request.raw_request.decode("utf8")
    print("\nRaw Text: \n\n",raw_text,"\n")
    #print("json data:\n\n",request.json(),"\n\n")
    #print("form data:\n\n",request.form_data,"\n\n")
    ssidValue = None
    pwValue = None
    suffixValue = None
    prefixValue = None
    sleEnablesValue = None
    snNameValue = None
    llatValue = None
    wifiCheckEnabled = None
    wifiCheckAdd = None
    statusUpdateEnabled = None
    statusUpdateInterval = None
    #
    #	Parse response for expected values
    #
    #
    #	First look for 'Text-SSID=' in response
    #
    ssidSplit = raw_text.split("Text-SSID=")
    print("\n\nssidSplit: ",ssidSplit,", ssidSplit length = ",len(ssidSplit))
    if len(ssidSplit)==2:
        #print("ssidSplit: ",ssidSplit)
        ssidValue = ssidSplit[1].split("\r")[0]
        print("\nFound SSID Value = \n",ssidValue)
    #
    #	Now look for 'Text-PW=' in response
    #
    pwSplit = raw_text.split("Text-PW=")
    if len(pwSplit)==2:
        pwValue = pwSplit[1].split("\r")[0]
        print("\nFound PW Value = \n",pwValue)
    #
    #	Now look for 'Url-suffix=' in response
    #
    nameSplit = raw_text.split("URL-Suffix=")
    if len(nameSplit)==2:
        suffixValue = nameSplit[1].split("\r")[0]
        print("\nFound URL suffix Value = \n",suffixValue)
    print(" ")
    #
    #	Now look for 'Url-prefix=' in response
    #
    nameSplit = raw_text.split("URL-Prefix=")
    if len(nameSplit)==2:
        prefixValue = nameSplit[1].split("\r")[0]
        print("\nFound URL prefix Value = \n",prefixValue)
    print(" ")
    #
    #	Now look for 'SLE-Enables=' in response
    #
    nameSplit = raw_text.split("SLE-Enables=")
    if len(nameSplit)==2:
        sleEnablesValue = nameSplit[1].split("\r")[0]
        print("\nFound URL suffix Value = \n",sleEnablesValue)
    print(" ")
    #
    #	Now look for 'Text-Name=' in response
    #
    nameSplit = raw_text.split("Text-Name=")
    if len(nameSplit)==2:
        snNameValue = nameSplit[1].split("\r")[0]
        print("\nFound SensorNode Name = \n",snNameValue)
    print(" ")
    #
    #	Now look for 'HA-LLAT=' in response
    #
    nameSplit = raw_text.split("HA-LLAT=")
    if len(nameSplit)==2:
        llatValue = nameSplit[1].split("\r")[0]
        print("\nFound LLAT = \n",llatValue)
    print(" ")
    #
    #	Now look for 'WIFI-CHECK-ENABLED' in response
    #
    nameSplit = raw_text.split("WIFI-CHECK-ENABLED=")
    if len(nameSplit)==2:
        wifiCheckEnabled = "True"
    else:
        wifiCheckEnabled = "False"
    print("\nFound WIFI-CHECK-ENABLED = \n",wifiCheckEnabled)
    print(" ")
    #
    #	Now look for 'WIFI_CHECK_IP_ADD=' in response
    #
    nameSplit = raw_text.split("Wifi-Check-IP-Add=")
    if len(nameSplit)==2:
        wifiCheckAdd = nameSplit[1].split("\r")[0]
        print("\nFound WIFI_CHECK_IP_ADD = \n",wifiCheckAdd)
    print(" ")
    #
    #	Now look for 'STATUS-UPDATE-ENABLED' in response
    #
    nameSplit = raw_text.split("STATUS-UPDATE-ENABLED=")
    if len(nameSplit)==2:
        statusUpdateEnabled = "True"
    else:
        statusUpdateEnabled = "False"
    print("\nFound STATUS-UPDATE-ENABLED = \n",statusUpdateEnabled)
    print(" ")
    #
    #	Now look for 'STATUS-UPDATE-INTERVAL=' in response
    #
    nameSplit = raw_text.split("Status-Update-Interval=")
    if len(nameSplit)==2:
        statusUpdateIntervalString = nameSplit[1].split("\r")[0]
        statusUpdateInterval = getIntFromString(statusUpdateIntervalString)
        if statusUpdateInterval == None: statusUpdateInterval = STATUS_UPDATE_INTERVAL_DEFAULT
        print("\nFound Status-Update-Interval = \n",statusUpdateInterval)
    print(" ") 
    
    wd_feed()

    # only add values that are legal
    if checkValue(ssidValue):
        #settingsStruct['ssid'] = ssidValue
        addToSettingsStruct('ssid',ssidValue)
    if checkValue(pwValue):
        #settingsStruct['pw'] = pwValue
        addToSettingsStruct('pw',pwValue)
    if checkValue(suffixValue):
        #settingsStruct['HA_SENSOR_URL_SUFFIX'] = suffixValue
        addToSettingsStruct('HA_SENSOR_URL_SUFFIX',suffixValue)
    if checkValue(prefixValue):
        #settingsStruct['HA_URL_PREFIX'] = prefixValue
        addToSettingsStruct('HA_URL_PREFIX',prefixValue)
    if checkValue(sleEnablesValue):
        #settingsStruct['SLE_JUMPER_ENABLES'] = sleEnablesValue
        addToSettingsStruct('SLE_JUMPER_ENABLES',sleEnablesValue)
    if checkValue(snNameValue):
        addToSettingsStruct('SENSORNODE_NAME',snNameValue)
    if checkValue(llatValue):
        addToSettingsStruct('HA_LLAT',llatValue)
    if checkValue(wifiCheckEnabled):
        addToSettingsStruct('WIFI_CHECK_ENABLED',wifiCheckEnabled)
    if checkValue(wifiCheckAdd):
        addToSettingsStruct('WIFI_CHECK_ADD',wifiCheckAdd)
    if checkValue(statusUpdateEnabled):
        addToSettingsStruct('SEND_STATUS_UPDATES',statusUpdateEnabled)
    if checkValue(statusUpdateInterval):
        if statusUpdateInterval < STATUS_UPDATE_INTERVAL_MINIMUM: statusUpdateInterval = STATUS_UPDATE_INTERVAL_MINIMUM
        if statusUpdateInterval > STATUS_UPDATE_INTERVAL_MAXIMUM: statusUpdateInterval = STATUS_UPDATE_INTERVAL_MAXIMUM
        addToSettingsStruct('STATUS_UPDATE_INTERVAL',statusUpdateInterval)

    # write data and restart
    newStruct = getSettingsStruct()
    errorStatus = writeDataToSettings('station',newStruct)
    #  reload site
    gc.collect()
    wd_feed()
    if errorStatus == True:
        failMess = "Error - Cannot Write to Local Storage."
        from serverFiles import failPage
        failPage("ERROR - Cannot Write to Local Storage")
        #return Response(request, f"{failPage(failMess)}",content_type='text/html')
        return Response(request,getHtmlBuffer(),content_type='text/html')
    else:
        readyToReset = True
        from serverFiles import successPage
        successPage()
        #return Response(request, f"{successPage()}",content_type='text/html')
        return Response(request,getHtmlBuffer(),content_type='text/html')
    
@server.route("/s2Temp",POST)
def s2TempPost(request: Request):
    from temp_sensor_server_files import processTempPost
    gc.collect()
    # handle contact settings
    wd_feed()
    print("\n\n---> Inside /s2Temp Post...")
    raw_text = request.raw_request.decode("utf8")
    print("\nRaw Text: \n\n",raw_text,"\n")
    #print("json data:\n\n",request.json(),"\n\n")
    #print("form data:\n\n",request.form_data,"\n\n")
    
    processTempPost(raw_text)

    wd_feed()
    gc.collect()
    print("\n\n---> leaving /s2Temp Post - serving up basePage...")
    from new_base_page_server_files import newBasePage
    newBasePage()
    return Response(request, getHtmlBuffer(),content_type='text/html')

@server.route("/s2Water",POST)
def s2WaterPost(request: Request):
    from water_sensor_server_files import processWaterPost
    gc.collect()
    # handle contact settings
    wd_feed()
    print("\n\n---> Inside /s2Water Post...")
    raw_text = request.raw_request.decode("utf8")
    print("\nRaw Text: \n\n",raw_text,"\n")
    #print("json data:\n\n",request.json(),"\n\n")
    #print("form data:\n\n",request.form_data,"\n\n")
    
    processWaterPost(raw_text)

    wd_feed()
    gc.collect()
    print("\n\n---> leaving /s2Water Post - serving up basePage...")
    from new_base_page_server_files import newBasePage
    newBasePage()
    return Response(request, getHtmlBuffer(),content_type='text/html')


@server.route("/contact",POST)
def contactPost(request: Request):
    from serverFiles import processContactPost
    gc.collect()
    # handle contact settings
    wd_feed()
    print("Inside contactPost...")
    raw_text = request.raw_request.decode("utf8")
    print("\nRaw Text: \n\n",raw_text,"\n")
    #print("json data:\n\n",request.json(),"\n\n")
    #print("form data:\n\n",request.form_data,"\n\n")
    
    processContactPost(raw_text)

    wd_feed()
    gc.collect()
    print("leaving contactPost - serving up basePage...")
    if S2_SENSOR_CONFIGURATION == "OLD":
        from serverFiles import basePage
        basePage()
    else:
        from new_base_page_server_files import newBasePage
        newBasePage()
    return Response(request,getHtmlBuffer(),content_type='text/html')
    
@server.route("/motion",POST)
def motionPost(request: Request):
    from motion_sensor_server_files import processMotionPost
    gc.collect()
    # handle contact settings
    wd_feed()
    print("\n\n---> Inside /motion Post...")
    raw_text = request.raw_request.decode("utf8")
    print("\nRaw Text: \n\n",raw_text,"\n")
    #print("json data:\n\n",request.json(),"\n\n")
    #print("form data:\n\n",request.form_data,"\n\n")
    
    processMotionPost(raw_text)

    wd_feed()
    gc.collect()
    print("\n\n---> leaving /motion Post - serving up basePage...")
    if S2_SENSOR_CONFIGURATION == "OLD":
        from serverFiles import basePage
        basePage()
    else:
        from new_base_page_server_files import newBasePage
        newBasePage()
    return Response(request, getHtmlBuffer(),content_type='text/html')

@server.route("/s2SensorSelect",POST)
def s2SensorPost(request: Request):
    from s2_sensor_select_server_files import processS2SensorPost
    gc.collect()
    # handle s2 sensor type selection
    wd_feed()
    print("\n\n---> Inside /s2SensorPost...")
    raw_text = request.raw_request.decode("utf8")
    print("\nRaw Text: \n\n",raw_text,"\n")
    #print("json data:\n\n",request.json(),"\n\n")
    #print("form data:\n\n",request.form_data,"\n\n")
    # set html to point to proper s2 sensor page depending upon what is set for s2SensorType field
    processS2SensorPost(raw_text)

    wd_feed()
    gc.collect()
    print("\n\n---> leaving /s2SensorPost...")
    
    #from serverFiles import basePage
    #basePage()
    # then return proper html for page selected
    return Response(request, getHtmlBuffer(),content_type='text/html')


def writeDiagSettingToSettingsFile(count_setting,request):
    # attempts to clear one count setting and reports error if fails
    error = False
    status = 0
    try:
        status = writeSettingsFile(count_setting)
    except:
        error = True
    else:
        if status != 0:
            error = True
    if error == False:
        from countsPage_server_files import countsPage
        countsPage()
    else:
        print("\n\n---> ERROR - settings file write failed.\n\n")
        from serverFiles import failPage
        failPage("Error accessing settings - file system set to read only?")
    

@server.route("/clearRebootCount",POST)
def clearRebootCountPost(request: Request):
    print("Inside clear reboot count post")
    newSetting = {'REBOOT_COUNT':0}
    writeDiagSettingToSettingsFile(newSetting,request)
    return Response(request, getHtmlBuffer(), content_type='text/html')

@server.route("/clearSendDataCount",POST)
def clearSendDataCountPost(request: Request):
    print("Inside clear send data count post")
    newSetting = {'SEND_DATA_COUNT':0}
    writeDiagSettingToSettingsFile(newSetting,request)
    return Response(request, getHtmlBuffer(), content_type='text/html')
    
@server.route("/clearWifiErrorsCount",POST)
def clearWifiErrorsCountPost(request: Request):
    print("Inside clear wifi errors count post")
    newSetting = {'WIFI_ERRORS_COUNT':0}
    writeDiagSettingToSettingsFile(newSetting,request)
    return Response(request, getHtmlBuffer(), content_type='text/html')
    
@server.route("/clearSendDataErrorsCount",POST)
def clearSendDataErrorsPost(request: Request):
    print("Inside clear send data errors count post")
    newSetting = {'SEND_DATA_ERRORS_COUNT':0}
    writeDiagSettingToSettingsFile(newSetting,request)
    return Response(request, getHtmlBuffer(), content_type='text/html')

@server.route("/changeReportCountsSetting",POST)
def changeReportCountsSetting(request: Request):
    print("\nInside toggle report counts setting post")
    raw_text = request.raw_request.decode("utf8")
    print("\nRaw Text: \n\n",raw_text,"\n")
    newSettingValue = False
    newReportCountsSettingText = None
    #
    #   Now look for 'diagOnOff=' in response
    #
    nameSplit = raw_text.split("diagOnOff=")
    if len(nameSplit)==2:
        newSettingValue = nameSplit[1].split("\r")[0]
        print("\nFound diagOnOff Value = \n",newSettingValue)
        if newSettingValue != "True":
            newSettingValue = "False"
    newSetting = {'REPORT_COUNTS':newSettingValue}
    writeDiagSettingToSettingsFile(newSetting,request)
    return Response(request, getHtmlBuffer(),content_type='text/html')
    

def start_server():
    global temp_test,readyToReset,wifiRetryTimer,pool,server
    #
    #	Start Server and listen for connections
    #
    global pool,server
    print("\n\nstarting server..")
    # set default reset mode to normal
    readyToReset = False
    timerDisable = False
    status_led_ticks = int(LED_BLINK_DURATION_AP_ENABLED/WAIT_TIME_TICK)
    ledTicks = status_led_ticks
    # startup the server
    wd_feed()
    # create data structure to write
    tempStruct = {}
    setSettingsStruct(tempStruct)
    #
    #	initialize global html buffer 
    #
    initializeGlobalBuffer()
    try:
        server.start(SERVER_HOST_ADD,80)
        print("Listening on http://%s:80" % SERVER_HOST_ADD)
        #  if the server fails to begin, restart the pico w
    except OSError:
        wd_feed()
        time.sleep(5)
        print("restarting..")
        micro_reset()
    wd_feed()
    clock = time.monotonic() #  time.monotonic() holder for server ping
    
    # check to see if wifi creds exist
    credsExist = False
    status,ssid,pw,startUpMode = getWifiCreds()
    if status == 0:
        # if creds exist and are not None
        # then set a timer to fire once every WIFI_RETRY_DURATION to test if wifi back up
        credsExist = True
        wifiRetryTimer = Timer()
        wifiRetryTimer.timeDelay = WIFI_RETRY_DURATION
        wifiRetryTimer.clearTimer()
        print("wifi retry timer started and set to ",WIFI_RETRY_DURATION,"seconds")

    while True:
        wd_feed()
        try:
            time.sleep(WAIT_TIME_TICK)
            # TBD DON"T THINK WE NEED THESE $ LINES???
            #  every 30 seconds, ping some local address & update temp reading
            if (clock + 30) < time.monotonic():
                temp_test = micro_cpu.temperature
                clock = time.monotonic()
            #  poll the server for incoming/outgoing requests
            ledTicks = countLedTicks(ledTicks,status_led_ticks)
            wd_feed()
            server.poll()
            wd_feed()
            if readyToReset:
                time.sleep(2)
                print("\n\nSetting env startup var to 'station' and restarting now...")
                restartIntoStationMode()
            elif credsExist:
                # reboot and retry every retry interval if force ap is not applied
                if wifiRetryTimer.isItTime() and getForceAPModePinValue() == True:
                    print("\n\nDetected Creds Exist and wifi retry timeout has occurred. Force AP Mode is NOT active. Setting startup mode to 'station' and restarting ...\n\n")
                    restartIntoStationMode()
        # pylint: disable=broad-except
        except Exception as e:
            print(e)
            continue
        
def stop_AP():
    #
    #	stops the access point by rebooting pico
    #
    print("stopping the access point...")
    time.sleep(10)
    micro_reset()
    
def start_AP(ssid,pw):
    #
    #	starts pico Access Point using ssid and pw
    #
    print("starting up access point...")
    print("\nusing ssid = ",ssid,", pw = ",pw,"\n")
    if not wifi.radio.ap_active:
        try:
            wifi.radio.start_ap(ssid=ssid,password=pw)
        except Exception as e:
            print("\n\n---> ERROR Attempting to start AP - Exception: ",e)
            signalErrorCondition()
            restartIntoAPMode()
    print("AP Started")



def goIntoAccessPointMode():
    #
    #	puts up wifi access point with html form
    #	to allow user to log in and input local ssid,pw params
    #
    #print("\n\nInside goIntoAccessPointMode...\n\n")
    setLeds(True)
    mySSID = getAPSSID()
    print("---> Inside goIntoAccessPointMode - mySSID = ",mySSID,"\n\n")
    wd_feed()
    start_AP(mySSID,AP_PW)  
    wd_feed()
    start_server()
    
