# TODO:
# - Implement things like target "as of"
# - See what happens if I shoot start.sh and python in the head - do relays stay on?
# - Allow for maintenance schedule, and recurring target temps (e.g., 8am every weekday)
# - Mobile app to read temp and actuator state
# - Mobile app to allow setting of target temp
# - Mobile app to allow manual setting of relay states (exclude heater?)
# - Mobile app to allow management of maintenance schedule
# - Mobile app to allow management of recurring temperature targets
# - This app to accommodate all of those
# - Safety net: If we aren't able to contact ThingSpeak for <1h?> shut down everything
# - Or... have a safety net config as well - what do I do if I'm out of communication?
# - Rewire relays in series (not parallel) so we can manually shut off at the top side

import time
import sys
import Relays
import RelaySafety
import Thermometer
import ThingSpeakLogger
import Queue

# "Constants"
DEBUG = True
READING_DELAY = 58 # seconds
TEMP_LIMIT = 103.5 # safety limit
TEMP_TARGET = 102.0
UPPER_TEMP_SLOP = LOWER_TEMP_SLOP = 0.5 # temperature regulation window
HEATING_TEMP_DIP_DELAY = 5 # delay after heater-on before temp stops falling
SUITABLE_SAMPLE_SIZE = 10 # number of readings before we trust heatRate()

safety = RelaySafety.RelaySafety() # Shuts off relays if app crashes

def main():
	Relays.Init() # all relays off
	s = HotTubState()
	while True:
		setAlert(s, "") # reset on each new loop iteration; TODO: Consider removing this
		s.temperature = Thermometer.read_temp()
		s.q.enqueue(s.temperature)
		s.tempRate = heatRate(s)

		if s.temperature >= TEMP_LIMIT:
			debug("s.temperature >= TEMP_LIMIT")
			setAlert(s, "Temperature exceeds " + str(TEMP_LIMIT) + "!")
			shutDown(s)

		readCommands(s)

		if s.isSafe and s.q.size() >= SUITABLE_SAMPLE_SIZE: # will not be if TEMP_LIMIT triggered block above

			if s.isHeaterOn:
				if s.q.size() > HEATING_TEMP_DIP_DELAY: # don't react if heating for less than N cycles
					if s.tempRate >= 9.0:
						setAlert(s, "Heat rate exceeds 9deg/hr!")
						shutDown(s)
					elif s.tempRate >= 5 and s.tempRate < 8:
							setAlert(s, "Heating normally")
					elif s.tempRate >= 1 and s.tempRate < 5:
						setAlert(s, "Cover likely open (heating slowly)")
					else: # < 1
						setAlert(s, "Heating too slowly (check over-temp button, make sure thermometer is in hot tub)")
						shutDown(s)
				else:
					setAlert(s, "Waiting for heating temperature dip delay")

			else: # Heater not on
				if s.tempRate > 2.5:
					setAlert(s, "Should be cooling but is heating > 1deg/hr!")
					# shutDown(s) -- we're not going to panic over this
				elif s.tempRate < 1 and s.tempRate >= -2:
					setAlert(s, "Cooling normally")
				elif s.tempRate < -2 and s.tempRate >= -6:
					setAlert(s, "Cover likely open (cooling quickly)")
				elif s.tempRate < -10:
					setAlert(s, "Cooling > 10 deg/hr! (make sure thermometer is in hot tub)")
					shutDown(s)

		# Temperature regulation routine:
		if s.isSafe: # Could be set to unsafe in rate blocks above
			if s.temperature >= s.targetTemperature + UPPER_TEMP_SLOP:
				heaterOff(s)
			elif s.temperature <= s.targetTemperature - LOWER_TEMP_SLOP:
				heaterOn(s)

		if s.q.size() < SUITABLE_SAMPLE_SIZE: # q may have been reset above
			setAlert(s, "Waiting for suitable sample size in temperature queue")

		if not s.isSafe:
			debug("HotTubController is in shutdown state")

		logTemperature(s)

		# <debug>
		debug(s)
		debug("=============================================================")
		# </debug>
		sys.stdout.flush()
		time.sleep(READING_DELAY) # TODO: Some alternative to "time.sleep()"?
		s.cycleCounter += 1

# Functions
def setAlert(s, alert):
	debug("setAlert()")
	s.alertMessage = alert
	debug(alert)

def logTemperature(s):
	debug("logTemperature()")
	pinStates = Relays.GetAllStates()
	ThingSpeakLogger.WriteData(s.temperature, pinStates, s.alertMessage, s.tempRate)

def readCommands(s):
	# Read target state from ThingSpeak
	# Set s.targetTemperature
	# Set other things (jets, light, etc.)
	# TODO: When a target temperature is set (non-zero), that overrides heater on/off state
	debug("readCommand()")
	commandDictionary = ThingSpeakLogger.ReadControl()
	s.targetTemperature = float(commandDictionary["field1"])
	s.targetJetsState = commandDictionary["field2"] == "1"
	s.targetLightState = commandDictionary["field3"] == "1"
	s.targetHeaterState = commandDictionary["field4"] == "1"
	s.targetColdBlowerState = commandDictionary["field5"] == "1"
	s.targetHotBlowerState = commandDictionary["field6"] == "1"
	debug("targetTemperature: " + str(s.targetTemperature))
	debug("targetJetsState: " + str(s.targetJetsState))
	debug("targetLightState: " + str(s.targetLightState))
	debug("targetHeaterState: " + str(s.targetHeaterState))
	debug("targetColdBlowerState: " + str(s.targetColdBlowerState))
	debug("targetHotBlowerState: " + str(s.targetHotBlowerState))

def heaterOn(s):
	debug("heaterOn()")
	if s.isSafe and not s.isHeaterOn:
		Relays.HeaterOn()
		s.q.drain()
		s.cycleCounter = 1
		s.isHeaterOn = True

def heaterOff(s):
	debug("heaterOff()")
	if s.isHeaterOn:
		Relays.HeaterOff()
		s.q.drain()
		s.cycleCounter = 1
		s.isHeaterOn = False

def shutDown(s):
	debug("shutDown()")
	heaterOff(s)
	s.isSafe = False

def heatRate(s):
	debug("heatRate()")
	# s.q.inspect()[0] - s.q.inspect()[s.q.size() - 1]) * (float(60)/s.q.size()) # Non-full queue will return lower-resolution results; 60/q.size() is to extrapolate per-hour
	if s.q.size() < 2:
		return 0
	else:
		maxSampleSize = 4
		hourSeconds = 3600.0 # (60 * 60)
		writePeriod = READING_DELAY + 2 # (2 == writeLag)
		sliceSize = min(maxSampleSize, s.q.size() - 1)
		debug("s.q.inspect(): " + str(s.q.inspect()))
		debug("sliceSize: " + str(sliceSize))
		heatFromSlice = s.q.inspect()[(0 - sliceSize):]
		debug("heatFromSlice (s.q.inspect()[" + str(0 - sliceSize) + ":]: " + str(heatFromSlice))
		heatToSlice = s.q.inspect()[:sliceSize]
		debug("heatToSlice (s.q.inspect()[:" + str(sliceSize) + "]:" + str(heatToSlice))
		heatFrom = sum(heatFromSlice) / float(len(heatFromSlice))
		heatTo = sum(heatToSlice) / float(len(heatToSlice))
		debug("heatFrom: " + str(heatFrom))
		debug("heatTo: " + str(heatTo))
		debug("Heat Rise: " + str(heatTo - heatFrom))
		measurementPeriod = s.q.size() - sliceSize
		debug("measurementPeriod: " + str(measurementPeriod))
		return (heatTo - heatFrom) * (hourSeconds / (writePeriod * measurementPeriod))
		# Avg windows overlap by 1 reading (~1 minute), so extrapolate to 1 hr

def debug(v):
	if DEBUG:
		print("[" + str(v) + "]")

class HotTubState:
	def __init__(self):
		self.temperature = 0.0
		self.q = Queue.Queue(32)
		self.cycleCounter = 1
		self.isHeaterOn = False
		self.tempRate = 0
		self.alertMessage = ""
		self.isSafe = True
		self.targetTemperature = TEMP_TARGET
		self.targetJetsState = False
		self.targetLightState = False
		self.targetHeaterState = False
		self.targetColdBlowerState = False
		self.targetHotBlowerState = False

	def __repr__(self):
		return "temperature: " + str(self.temperature) + "\nq.size(): " + str(self.q.size()) + "\nq: " + str(self.q.inspect()) + "\ncycleCounter: " + str(self.cycleCounter) + "\nisHeaterOn: " + str(self.isHeaterOn) + "\ntempRate: " + str(self.tempRate) + "\nalertMessage: " + self.alertMessage + "\nisSafe: " + str(self.isSafe)

# Bootstrapping function -- allows us to declare functions at end of file :-\
if __name__ == '__main__':
	main()

