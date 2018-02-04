# Hot tub relay controller
#
# Hot tub controls are:
#   - Light
#   - Heater
#   - Jets
#   - Cool Air Blower ("CoolBlower")
#   - Hot Air Blower ("HotBlower")
#
# Raspberry Pi pins referenced in this program are BOARD pins (by board pin #), not BCM pins (named pins)
# TODO: Noodle with PIN_* to match reality

import RPi.GPIO as GPIO

# Set up constants
PIN_LIGHT      = 31
PIN_HEATER     = 29
PIN_JETS       = 37
PIN_COOLBLOWER = 35
PIN_HOTBLOWER  = 33
PIN_ON = GPIO.LOW
PIN_OFF = GPIO.HIGH
PIN_DATA = [("light", PIN_LIGHT), ("heater", PIN_HEATER), ("jets", PIN_JETS), ("coldblower", PIN_COOLBLOWER), ("hotblower", PIN_HOTBLOWER)]
pin_unzip = list(zip(*PIN_DATA)) # split into "columns"
PIN_LIST = pin_unzip[1] # Grab a list of just pin #s (for batch initialization)

# Initialize
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
GPIO.setup(PIN_LIST, GPIO.OUT)

def Init():
	GPIO.output(PIN_LIST, PIN_OFF)

def LightOn():
	SetState(PIN_LIGHT, PIN_ON)

def LightOff():
	SetState(PIN_LIGHT, PIN_OFF)

def HeaterOn():
	SetState(PIN_HEATER, PIN_ON)

def HeaterOff():
	SetState(PIN_HEATER, PIN_OFF)

def JetsOn():
	SetState(PIN_JETS, PIN_ON)

def JetsOff():
	SetState(PIN_JETS, PIN_OFF)

def ColdBlowerOn():
	SetState(PIN_COOLBLOWER, PIN_ON)

def ColdBlowerOff():
	SetState(PIN_COOLBLOWER, PIN_OFF)

def HotBlowerOn():
	SetState(PIN_HOTBLOWER, PIN_ON)

def HotBlowerOff():
	SetState(PIN_HOTBLOWER, PIN_OFF)

def ToggleLight():
	ToggleState(PIN_LIGHT)

def TottleHeater():
	ToggleState(PIN_HEATER)

def TottleJets():
	ToggleState(PIN_JETS)

def ToggleCoolBlower():
	ToggleState(PIN_COOLBLOWER)

def ToggleHotBlower():
	ToggleState(PIN_HOTBLOWER)

def ToggleState(pin):
	current_state = GetState(pin)
	if (current_state == GPIO.ON):
		SetState(pin, GPIO.OFF)
	else:
		SetState(pin, GPIO.ON)

def GetState(pin):
	current_state = GPIO.input(pin) # Can do this without setting to input!
	if (current_state == PIN_ON):
		return 1
	else:
		return 0

def GetAllStates():
	pinStates = []
	for pin in PIN_DATA:
		pinStates.append((pin[0], GetState(pin[1])))
	return pinStates

def SetState(pin, state):
	GPIO.output(pin, state)

