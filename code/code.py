'''

    SensorNode code.py startup Code
    
    code.py
    
    TNB Technologies,LLC
    
    Tom Berarducci
    
'''

import gc
gc.enable()
gc.collect()
freeMem = gc.mem_free()
print("Top of code - Free Memory = ",freeMem)


import os
import ipaddress



import json
from sensorNodeUtils import wd_feed,readSettingsFile,getSettingValueFromSettingsJson,wifi_reconnect,updateCountSetting,setLeds
from sensorNodeUtils import setSensorNodeDeviceName,setPicoIdShort,setPicoID,writeSettingsFile,getBoolSetting
from sensorNodeUtils import setPicoAPSSID,getAPSSID,getPicoUID,restartIntoAPMode,isAPModeRequired,turnOnWatchDogIfEnabled
from globals import SETTINGS_FILE,SLE_JUMPER_ENABLES,REPORT_COUNTS_DEFAULT
from sensorNodeUtils import setSleJumperEnables,setReportCounts,getReportCounts

gc.collect()
freeMem = gc.mem_free()
print("after imports freemem = ",freeMem)


DEVICE_NAME_BASE = "SensorNode - "


'''

                SensorNode
                
                S1 - Dry Contact Closure Sensor
                
                S2 - Motion Sensor OR Temp Sensor OR Water Sensor
                
                Support for i2c temp, humidity sensors (AHT20)
                
                WatchDog Timer
            
                Optional Power Monitor
                
                by TNB Technologies, LLC
                
                (c) 2024, All Rights Reserved
                
'''

def main():
    print("\n\nSensorNode Starting up...\n")
    # turn on wdt
    turnOnWatchDogIfEnabled()
    gc.enable()
    #
    #	Read Settings File
    #
    status,jsonDataStruct = readSettingsFile(SETTINGS_FILE)
    #print("\n\nsettings data struct:\n",jsonDataStruct)
    if status != 0:
        # can't find settings file - so create it
        jsonDataStruct = {}
        try:
            with open(SETTINGS_FILE,"w") as f:
                json.dump(jsonDataStruct,f)
                f.close
        except:
            print("\n\n---> ERROR attempting to create empty settings file!! --> Could not write file.\n\n")
        else:
            print("\n\nCould not find settings file - created new empty file in non-volatile storage...\n\n")
            
    # set up led enables
    sle_jumper_enables = getSettingValueFromSettingsJson(jsonDataStruct,'SLE_JUMPER_ENABLES',SLE_JUMPER_ENABLES)
    setSleJumperEnables(sle_jumper_enables)
    # set up leds
    setLeds()
    # turn on enabled leds
    setLeds(True)
    
    #
    #	increment reboot count and restore in nv mem; create it and store if not there
    #
    settings_reboot_count = getSettingValueFromSettingsJson(jsonDataStruct,'REBOOT_COUNT',0)
    # increment and restore it
    settings_reboot_count += 1
    #
    #	get REPORT_COUNTS setting from settings.json and turn on/off diagnostics accordingly
    #
    settings_report_counts = getBoolSetting('REPORT_COUNTS',REPORT_COUNTS_DEFAULT,jsonDataStruct)
    # set it for all modules to access
    setReportCounts(settings_report_counts)
    if getReportCounts(): updateCountSetting('REBOOT_COUNT',settings_reboot_count)


    # get unique id
    picoID,picoIDShort = getPicoUID()
    setPicoIdShort(picoIDShort)
    setPicoID(picoID)
    # AP SSID
    accessPtID = getAPSSID()
    setPicoAPSSID(accessPtID)
    #
    # 	build sensornode device defines from picoID
    #
    print("picoID = ",picoID,", picoIDShort = ",picoIDShort)
    deviceName = DEVICE_NAME_BASE+picoIDShort
    setSensorNodeDeviceName(deviceName)
    #
    #	Check to see if AP Mode is required
    #
    apModeRequired,ssid,pw = isAPModeRequired()
    if apModeRequired:
        print("\n\n---> ACCESS POINT MODE REQUIRED\n\n")
        gc.collect()
        freeMem = gc.mem_free()
        from sn_server_code import goIntoAccessPointMode
        print("Prior to starting AP - Free Memory = ",freeMem)
        goIntoAccessPointMode()
    else:
        print("AP Mode restart NOT required...continuing...")
    #
    #	If AP Mode is NOT required, then attempt to connect to wifi
    #
    wd_feed()
    status,ipAdd = wifi_reconnect(ssid,pw)
    if status == -1:
        #
        #	if cannot connect via WiFi, then restart into AP Mode
        #
        print("\n\n---> ERROR cannot connect to wifi - Restarting into AP Mode...\n\n")
        restartIntoAPMode()
    else:
        print("\nConnected to Wifi\n")
    #
    #	Not in AP Mode - Run SensorNode Main Loop Code
    #
    gc.collect()
    freeMem = gc.mem_free()
    from sn_mainline_code import main_loop_code
    print("Prior to starting Main Loop Code - Free Memory = ",freeMem)
    main_loop_code(ipAdd,settings_reboot_count,jsonDataStruct)
    print("\n\nSensorNode1 Shutting down.\n")
main()
