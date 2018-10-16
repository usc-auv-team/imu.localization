import serial
from time import clock
import numpy as np
import math, re, socket, select, string, struct, sys, threading, time, types, array, errno, inspect
global NTP_epoch
from calendar import timegm
NTP_epoch = timegm((1900,1,1,0,0,0)) # NTP time started in 1 Jan 1900
del timegm

global NTP_units_per_second
NTP_units_per_second = 0x100000000 # about 232 picoseconds

replies=[]
#callbacks={"/sensors":sensorsHandler,"/quaternion":quaternionHandler,"/battery":batteryHandler,"/humidity":humidityHandler,"/temperature":temperatureHandler}
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
			decoded.append(decodeOSC(rest[:length]))
			rest = rest[length:]

	elif len(rest)>0:
		if not len(typetags):
			typetags, rest = _readString(rest)
		decoded.append(address)
		decoded.append(typetags)
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
		rest = data
		float = 0
	else:
		float = struct.unpack(">d", data[0:8])[0]
		rest  = data[8:]

	return (float, rest)

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
buffer = bytes()
count=0
start=clock()  # .read() returns bytes right?
while clock()-start <1:
    if rs232.in_waiting > 0:
    	buffer+=rs232.read()
    	if(buffer.find(b'/earth',0,len(buffer))!=-1):
    		a=buffer.find(b'/earth',0,len(buffer))
    		buffer=buffer[a:]
    		buffer+=rs232.read(36)
    		decoded=decodeOSC(buffer)
    		earths.append(decoded[2:])
    	if(buffer.find(b'/quaternion',0,len(buffer))!=-1):
    		count+=1
    		a=buffer.find(b'/quaternion',0,len(buffer))
    		buffer=buffer[a:]
    		buffer+=rs232.read(40)
    		decoded=decodeOSC(buffer)
    		result = decoded[2:]
    		qw = result[0]
    		qx = result[1]
    		qy = result[2]
    		qz = result[3]
    		rotationMatrix = np.matrix([[1-2*qy**2-2*qz**2,2*qx*qy-2*qz*qw,2*qx*qz+2*qy*qw],
                            [2*qx*qy+2*qz*qw,1-2*qx**2-2*qz**2,2*qy*qz-2*qx*qw],
                            [2*qx*qz-2*qy*qw,2*qy*qz+2*qx*qw,1-2*qx**2-2*qy**2]])
    		trueAcceleration = np.matmul(np.linalg.inv(rotationMatrix), np.matrix([[0],[0],[.3]]))
 			# Get 3 True acceleration then pop() first and append() last