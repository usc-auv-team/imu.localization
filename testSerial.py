import serial
from time import clock
import numpy as np
import math, struct
from collections import deque
ini_an=0.0
ini_ae=0.0
ini_ad=0.0
ini_vn=0.0
ini_ve=0.0
ini_vd=0.0
ini_dn=0.0
ini_de=0.0
ini_dd=0.0
#callbacks={"/sensors":sensorsHandler,"/quaternion":quaternionHandler,"/battery":batteryHandler,"/humidity":humidityHandler,"/temperature":temperatureHandler}
def _readString(data):
	"""Reads the next (null-terminated) block of data
	"""
	length   = data.find(b'\x00')
	nextData = int(math.ceil((length+1) / 4.0) * 4)
	return (data[0:length], data[nextData:])

def get_Roll_Pitch_Yaw(eulers):
	return eulers[-1]

def get_displacement(earths):
	an,ae,ad=earths[-1]
	vn=ini_vn+((an+ini_an)/2.0)*(1/200)
	ve=ini_ve+((ae+ini_ae)/2.0)*(1/200)
	vd=ini_vd+((ad+ini_ad)/2.0)*(1/200)
	dn=ini_dn+((vn+ini_vn)/2.0)*(1/200)
	de=ini_de+((ve+ini_ve)/2.0)*(1/200)
	dd=ini_dd+((vd+ini_vd)/2.0)*(1/200)
	ini_an=an
	ini_ae=ae
	ini_ad=ad
	ini_vn=vn
	ini_ve=ve
	ini_vd=vd
	ini_dn=dn
	ini_de=de
	ini_dd=dd
	return (dn,de,dd)

def decodeOSC(data):
	"""Converts a binary OSC message to a Python list. 
	"""
	table = {105:_readInt, 102:_readFloat, 115:_readString, 98:_readBlob, 100:_readDouble}
	decoded = []
	address,  rest = _readString(data)
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
		if typetags.startswith(b','):
			
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
earths=deque(maxlen=50)
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
    	displacement_north,displacement_east,displacement_down=get_displacement(earths)
    	
 			# Get 3 True acceleration then pop() first and append() last