#
#	BOOT.PY
#
import board
import digitalio
import storage
#
#	Sets up Pico to be able to write to internal storage if GPIO 14 is LOW
#
switch = digitalio.DigitalInOut(board.GP14)
switch.direction = digitalio.Direction.INPUT
switch.pull = digitalio.Pull.UP

storage.remount("/",switch.value)

