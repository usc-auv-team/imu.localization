import serial
#import OSC
import math, re, socket, select, string, struct, sys, threading, time, types, array, errno, inspect
global NTP_epoch
from calendar import timegm
NTP_epoch = timegm((1900,1,1,0,0,0)) # NTP time started in 1 Jan 1900
del timegm

global NTP_units_per_second
NTP_units_per_second = 0x100000000 # about 232 picoseconds

replies=[]
def sensorsHandler(add, tags, args):
	print add + str(args)

def quaternionHandler(add, tags, args):
    print add + str(args)

def batteryHandler(add, tags, args):
	#print add + str(args)
	#return add + str(args)
	pass
def humidityHandler(add,tags,args):
	pass
def temperatureHandler(add,tags,args):
	pass
callbacks={"/sensors":sensorsHandler,"/quaternion":quaternionHandler,"/battery":batteryHandler,"/humidity":humidityHandler,"/temperature":temperatureHandler}
def _readString(data):
	"""Reads the next (null-terminated) block of data
	"""
	length   = string.find(data,"\0")
	nextData = int(math.ceil((length+1) / 4.0) * 4)
	return (data[0:length], data[nextData:])
def _readTimeTag(data):
	"""Tries to interpret the next 8 bytes of the data
	as a TimeTag.
	 """
	high, low = struct.unpack(">LL", data[0:8])
	if (high == 0) and (low <= 1):
		time = 0.0
	else:
		time = int(NTP_epoch + high) + float(low / NTP_units_per_second)
	rest = data[8:]
	return (time, rest)
def decodeOSC(data):
	"""Converts a binary OSC message to a Python list. 
	"""
	table = {"i":_readInt, "f":_readFloat, "s":_readString, "b":_readBlob, "d":_readDouble, "t":_readTimeTag}
	decoded = []
	address,  rest = _readString(data)
	if address.startswith(","):
		typetags = address
		address = ""
	else:
		typetags = ""

	if address == "#bundle":
		time, rest = _readTimeTag(rest)
		decoded.append(address)
		decoded.append(time)
		while len(rest)>0:
			length, rest = _readInt(rest)
			print("length="+str(length))
			decoded.append(decodeOSC(rest[:length]))
			rest = rest[length:]

	elif len(rest)>0:
		if not len(typetags):
			typetags, rest = _readString(rest)
		decoded.append(address)
		decoded.append(typetags)
		print("This is TypeTags:"+typetags)
		if typetags.startswith(","):
			
			for tag in typetags[1:]:
				value, rest = table[tag](rest)
				decoded.append(value)
	return decoded
def _readBlob(data):
	"""Reads the next (numbered) block of data
	"""
	length   = struct.unpack(">i", data[0:4])[0]
	nextData = int(math.ceil((length) / 4.0) * 4) + 4
	return (data[4:length+4], data[nextData:])

def _readInt(data):
	"""Tries to interpret the next 4 bytes of the data
	as a 32-bit integer. """
	
	if(len(data)<4):
		print "Error: too few bytes for int", data, len(data)
		rest = data
		integer = 0
	else:
		integer = struct.unpack(">i", data[0:4])[0]
		rest	= data[4:]

	return (integer, rest)

def _readLong(data):
	"""Tries to interpret the next 8 bytes of the data
	as a 64-bit signed integer.
	 """

	high, low = struct.unpack(">ll", data[0:8])
	big = (long(high) << 32) + low
	rest = data[8:]
	return (big, rest)



def _readFloat(data):
	"""Tries to interpret the next 4 bytes of the data
	as a 32-bit float. 
	"""
	
	if(len(data)<4):
		print "Error: too few bytes for float", data, len(data)
		rest = data
		float = 0
	else:
		float = struct.unpack(">f", data[0:4])[0]
		rest  = data[4:]

	return (float, rest)

def _readDouble(data):
	"""Tries to interpret the next 8 bytes of the data
	as a 64-bit float. 
	"""
	
	if(len(data)<8):
		print "Error: too few bytes for double", data, len(data)
		rest = data
		float = 0
	else:
		float = struct.unpack(">d", data[0:8])[0]
		rest  = data[8:]

	return (float, rest)
OSCtrans = string.maketrans("{,}?","(|).")
def getRegEx(pattern):
	"""Compiles and returns a 'regular expression' object for the given address-pattern.
	"""
	# Translate OSC-address syntax to python 're' syntax
	pattern = pattern.replace(".", r"\.")		# first, escape all '.'s in the pattern.
	pattern = pattern.replace("(", r"\(")		# escape all '('s.
	pattern = pattern.replace(")", r"\)")		# escape all ')'s.
	pattern = pattern.replace("*", r".*")		# replace a '*' by '.*' (match 0 or more characters)
	pattern = pattern.translate(OSCtrans)		# change '?' to '.' and '{,}' to '(|)'
	
	return re.compile(pattern)
def dispatchMessage(pattern, tags, data):
	global callbacks
	expr = getRegEx(pattern)
	replies = []
	matched = 0
	for addr in callbacks.keys():
		match = expr.match(addr)
		if match and (match.end() == len(addr)):
			reply = callbacks[addr](pattern, tags, data)
			matched += 1
			replies.append(reply)
	
	return replies

def _unbundle(decoded):
	global replies
	"""Recursive bundle-unpacking function"""
	if decoded[0] != "#bundle":
		replies += dispatchMessage(decoded[0], decoded[1][1:], decoded[2:])
		return

	now = time.time()
	timetag = decoded[1]
	if (timetag > 0.) and (timetag > now):
		time.sleep(timetag - now)
	
	for msg in decoded[2:]:
		_unbundle(msg)
	
def handle(packet):
	"""Handle incoming OSCMessage
	"""
	decoded = decodeOSC(packet)
	if not len(decoded):
		return
	
	_unbundle(decoded)


rs232 = serial.Serial(
    port = 'COM3',
    baudrate = 115200,
    parity = serial.PARITY_NONE,
    stopbits = serial.STOPBITS_ONE,
    bytesize = serial.EIGHTBITS,
    timeout = 1
)
# hexstring="2f 7175 6174 6572 6e69 6f6e 002c 6666 6666 0000 003f 764e b83b d250 053d 1460 e13e 870d 0a0d 0a14 c0"
# to_string=bytearray.fromhex(hexstring)
# decoded=decodeOSC(to_string)
# print "##########################################"
# print "##########################################"
# print decoded
buffer = bytes()  # .read() returns bytes right?
while True:
    if rs232.in_waiting > 0:
    	buffer+=rs232.read()

    	if(buffer.find(b'/sensors',0,len(buffer))!=-1):
    		a=buffer.find(b'/sensors',0,len(buffer))
    		print "Sensors"
    		buffer=buffer[a:]
    		buffer+=rs232.read(65)
    		decoded=decodeOSC(buffer)
    		print decoded
    	if(buffer.find(b'/quaternion',0,len(buffer))!=-1):
    		a=buffer.find(b'/quaternion',0,len(buffer))
    		buffer=buffer[a:]
    		buffer+=rs232.read(40)
    		decoded=decodeOSC(buffer)
    		print "Quaternion"
    		print decoded

