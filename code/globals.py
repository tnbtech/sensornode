'''

    SensorNode GLOBAL DECLARES
    ..
    
'''

VERSION = "1.06"

AP_PW = "Sensor.N0de"

#
#	WIFI RETRY/CHECK
#
#	In AP mode, will retry to connect every interval if creds exist (if FORCE_AP is set this will NOT happen)
#	in Normal mode, will perform WIFI connect CHECK every FIVE TIMES THIS INTERVAL as long as LOCAL_WIFI_IP_TEST URL is NOT 'None' otherwise will do nothing
#

WIFI_RETRY_DURATION = 60

SETTINGS_FILE = "settings.json"

SLE_JUMPER_ENABLES = "BOTH"			# SLE jumper - possible values: INT, EXT, BOTH controls which LEDS are enabled by Jumper

#
#	DEFAULT Home Assistant URL - used if nothing is input into config server settings
#
homeAssistantUrl = "http://homeassistant.local:8123"

REPORT_COUNTS_DEFAULT = False			# enables storing of diagnostic data in NV memory and viewing this data on 'diagnostics' webpage when in AP mode

#
#	Connector S2 Sensor
#
#	On earlier models, only motion sensing is available. On later models, this connector can accomodate motion, temp, OR water sensors.
#
#	This option must be ENABLED BEFORE the newer sensors can be used, as follows:
#
#	OLD = Only Motion sensor is supported (default)
#	NEW = Board supports Motion, Temp, or Water sensors (must be board REV 2.41 or HIGHER)
#
#	NOTE: When using 'New' configuration, board jumper J3 must also be set properly for either 'temp' or 'motion/water' to support these sensors     
#

S2_SENSOR_CONFIGURATION = "NEW"

# this will be the DEFAULT S2 Sensor type if none is stored in NV Memory

S2_SENSOR_TYPE_DEFAULT = "MOTION"

# S2 Temp Sensor Declares

HA_S2_TEMP_SENSOR_NAME_DEFAULT = "S2 Temp Sensor"
S2_TEMP_SENSOR_ENABLED_DEFAULT = False
S2_TEMP_SENSOR_MIN_SAMPLING_INTERVAL = 10			# secs minimum between readings of the s2 temp sensor value
S2_TEMP_SENSOR_SAMPLING_INTERVAL_DEFAULT = 30		# secs between temp readings on S2 temp sensor

# S2 Water Sensor Delcares

HA_S2_WATER_SENSOR_NAME_DEFAULT = "S2 Water Sensor"
S2_WATER_SENSOR_ENABLED_DEFAULT = False
S2_WATER_SENSOR_ACTIVE_DURATION_DEFAULT = 2
S2_WATER_SENSOR_ACTIVE_DURATION_MINIMUM = 2

# S2 Motion Sensor Declares

HA_MOTION_SENSOR_NAME_DEFAULT = "Motion Sensor"	# this will be the friendly name for HA
MOTION_SENSOR_ENABLED_DEFAULT = False
MOTION_SENSOR_ACTIVE_DURATION_DEFAULT = 10		# number of secs sensor will remain closed for HA
MOTION_SENSOR_ACTIVE_DURATION_MINIMUM = 2

# S1 Dry Contact Sensor Declares

HA_CONTACT_SENSOR_NAME_DEFAULT = "Contact Sensor"	# this will be the friendly name for HA
CONTACT_SENSOR_ENABLED_DEFAULT = False
CONTACT_SENSOR_CLOSED_DURATION_DEFAULT = 2		# number of secs sensor will remain closed for HA
CONTACT_SENSOR_CLOSED_DURATION_MINIMUM = 2

SWITCH_DEBOUNCE_DELAY_TIME = 0.1

#  font for HTML
font_family = "monospace"

#************************************** GENERAL DEFINES *************************************************

SENSORNODE_TYPE = "SensorNode"

STATUS_UPDATE_ACTIVE_DURATION_DEFAULT = 2 	# number of secs 'online' signal will be active

START_UP_MODE_DEFAULT = "station"

SEND_STATUS_UPDATES = True		# if this is True then sensornode will send 'online' periodically on ALL devices

STATUS_UPDATE_INTERVAL_DEFAULT = 900	# number of secs between status updates

STATUS_UPDATE_INTERVAL_MINIMUM = 30			# min update duration is 30 sec

STATUS_UPDATE_INTERVAL_MAXIMUM = 86400		# max update duration = 1 day

LED_BLINK_DURATION_WD_ENABLED = 0.3			# number of secs in between activity Led Blinks - WD ENABLED

LED_BLINK_DURATION_WD_DISABLED = 1			# number of secs in between activity Led Blinks - WD DISABLED

LED_BLINK_DURATION_AP_ENABLED = .1			# fast blink - AP is ON - WAITING FOR INPUT

INTERNET_CONNECTIVITY_CHECK_DURATION = 300	# number of secs between connectivity checks

WAIT_TIME_TICK = 0.1			# number of secs for each wait tick

HTTP_TIMEOUT = 7							# max timeout for all http posts to HA

WIFI_RECONNECT_TRIES = 5 		# no of retries to connect before going into AP MODE

WIFI_CHECK_ENABLE_DEFAULT = False


