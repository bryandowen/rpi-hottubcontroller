# The entire purpose of this class is to be instantiated by the
# hot tub controller routine so that it can set all relays to OFF
# on destriction - i.e., if the program exits due to an exception
# or some such. We don't want to heat the hot tub past 104, and
# don't want the heater/jets running indefinitely while unattended.

import RPi.GPIO as GPIO

PIN_LIST = [29, 31, 33, 35, 37]
PIN_OFF = GPIO.HIGH

class RelaySafety:
	def __del__(self):
		GPIO.setmode(GPIO.BOARD)
		GPIO.setwarnings(False)
		GPIO.setup(PIN_LIST, GPIO.OUT)
		GPIO.output(PIN_LIST, PIN_OFF)
        	print("Relays turned OFF")
