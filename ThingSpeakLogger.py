import urllib
import urllib2
import csv

# TODO: In connection routine, log errors to file, not console

# Set up URL constants
URL_BASE = "https://api.thingspeak.com"
# Data channel (write from Pi => ThingSpeak)
DATA_CHANNEL_ID = "390541"
DATA_WRITE_KEY = "V8EHPSCX44R9FUUU"
URL_DATA_WRITE = URL_BASE + "/update?api_key=" + DATA_WRITE_KEY
# Control channel (read from ThingSpeak => Pi)
CONTROL_CHANNEL_ID = "390551"
CONTROL_READ_KEY = "T7WUFMLHQT7RVOKT"
URL_CONTROL_READ = URL_BASE + "/channels/" + CONTROL_CHANNEL_ID + "/feeds.csv?api_key=" + CONTROL_READ_KEY + "&results=1"


class ThingSpeakReadError(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)

def ReadControl(): # implement this for the "control" half of HotTubController
        print("Reading: " + URL_CONTROL_READ)
        responseCode, contents = _SendRequest(URL_CONTROL_READ)
        if responseCode < 200 or responseCode >= 300:
		print("Read operation failed.")
		raise ThingSpeakReadError("Unable to read from ThingSpeak")
	else:
		contentsReader = csv.DictReader(contents.split("\n"))
		for row in contentsReader:
			responseRow = row
		return responseRow # There is definitely a better way to do this. Unfortunately I don't know it yet. :-\

def WriteData(temperature, pinStates, alertMessage, tempRate):
	pinNameValuePairs = _Correlate(pinStates) # Correlate pin data with ThingSpeak fieldnames
	writeUrl = _ConstructUrl(temperature, pinNameValuePairs, alertMessage, tempRate) # Construct URL for data logging call
	print("Writing: " + writeUrl)
	responseCode, contents = _SendRequest(writeUrl) # Make call to data logging service, capture output

def _Correlate(pinStates): # line up pin states with ThingSpeak fieldnames (return in tuples)
	fieldMappings = [("jets", "field2"), ("light", "field3"), ("heater", "field4"), ("coldblower", "field5"), ("hotblower", "field6")]
	#print("Pre-sort:")
	#print("fieldMappings: " + str(fieldMappings))
	#print("pinStates: " + str(pinStates))
	fieldMappings.sort(key=lambda tup: tup[0])
	pinStates.sort(key=lambda tup: tup[0])
	#print("Post-sort:")
	#print("fieldMappings: " + str(fieldMappings))
	#print("pinStates: " + str(pinStates))
	pinNameValuePairs = []
	for idx in range(len(fieldMappings)):
		pinNameValuePairs.append((fieldMappings[idx][1], pinStates[idx][1]))
	pinNameValuePairs.sort(key=lambda tup: tup[0])
	#print("zipped: " + str(pinNameValuePairs))
	return pinNameValuePairs

def _ConstructUrl(temperature, pinStates, alertMessage, tempRate):
        write_url = URL_DATA_WRITE + "&field1=" + urllib.quote_plus(str(temperature)) + "&"
        write_url += urllib.urlencode(pinStates)
	write_url += "&field7=" + urllib.quote_plus(alertMessage)
	write_url += "&field8=" + urllib.quote_plus(str(tempRate))
	return write_url

def _SendRequest(writeUrl):
        request = urllib2.Request(writeUrl)
	try:
	        connection = urllib2.urlopen(request)
	        responseCode = connection.getcode()
        	contents = connection.read()
		connection.close()
		return responseCode, contents
        except Exception as e:
		print("Error writing " + writeUrl)
		print(e)
		return 0, 0

