import serial
import OSC
import math, re, socket, select, string, struct, sys, threading, time, types, array, errno, inspect
global NTP_epoch
from calendar import timegm
NTP_epoch = timegm((1900,1,1,0,0,0)) # NTP time started in 1 Jan 1900
del timegm

global NTP_units_per_second
NTP_units_per_second = 0x100000000 # about 232 picoseconds


def _readString(data):
	"""Reads the next (null-terminated) block of data
	"""
	length   = string.find(data,"\0")
	nextData = int(math.ceil((length+1) / 4.0) * 4)
	return (data[0:length], data[nextData:])
def decodeOSC(data):
	"""Converts a binary OSC message to a Python list. 
	"""
	table = {105:_readInt, 102:_readFloat, 115:_readString, 98:_readBlob, 100:_readDouble, 116:_readTimeTag}
	print table.keys()
	decoded = []
	address,  rest = _readString(data)
	print address
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
		print("This is TypeTags:"+typetags)
		if typetags.startswith(","):
			
			for tag in typetags[1:]:
				value, rest = table[tag](rest)
				decoded.append(value)
			print decoded
		else:
			raise OSCError("OSCMessage's typetag-string lacks the magic ','")

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

# rs232 = serial.Serial(
#     port = 'COM3',
#     baudrate = 115200,
#     parity = serial.PARITY_NONE,
#     stopbits = serial.STOPBITS_ONE,
#     bytesize = serial.EIGHTBITS,
#     timeout = 1
# )
hexstring="2362 756e 646c 6500 bc17 d0d5 9b42 4000 0000 0040 2f73 656e 736f 7273 0000 0000 2c66 6666 6666 6666 6666 6600 3ec1 e5b0 bdc8 50d5 be51 56b1 3d9c 926a 3b59 19f2 3f7f bd1f 4181 ded9 4127 7d03 c1b8 5220 447b eefc c023 6275 6e64 6c65 00bc 17d0 d59b 4240 0000 0000 242f 7175 6174 6572 6e69 6f6e 002c 6666 6666 0000 003f 764e b83b d250 053d 1460 e13e 870d 0a0d 0a14 c023 6275 6e64 6c65 00bc 17d0 d5a0 eb90 0000 0000 402f 7365 6e73 6f72 7300 0000 002c 6666 6666 6666 6666 6666 003b ee6e 003d a382 56be 125b 563d 97ab c139 d56c 003f 804c 6641 7d91 7541 2779 1dc1 b846 5444 7bee fcc0 2362 756e 646c 6500 bc17 d0d5 a0eb 9000 0000 0024 2f71 7561 7465 726e 696f 6e00 2c66 6666 6600 0000 3f76 4e97 3bd2 d791 3d14 4aa7 3e87 0b58 c023 6275 6e64 6c65 00bc 17d0 d5a5 f3e0 0000 0000 402f 7365 6e73 6f72 7300 0000 002c 6666 6666 6666 6666 6666 00bd ef29 50bd 1e94 82bd a71e 563d 9890 b63a efa7 943f 7f5f e641 7d91 7541 2779 1dc1 b846 5444 7bee c5c0 2362 756e 646c 6500 bc17 d0d5 a5f3 e000 0000 0024 2f71 7561 7465 726e 696f 6e00 2c66 6666 6600 0000 3f76 4e07 3bd2 d595 3d14 40c3 3e87 0f9d c023 6275 6e64 6c65 00bc 17d0 d5aa fc30 0000 0000 402f 7365 6e73 6f72 7300 0000 002c 6666 6666 6666 6666 6666 00be da60 6c3c a7ba b4be 512d 033d 929f 4f39 be1c 803f 7fde 5c41 7d91 7541 2779 1dc1 b846 5444 7bee c5c0 2362 756e 646c 6500 bc17 d0d5 aafc 3000 0000 0024 2f71 7561 7465 726e 696f 6e00 2c66 6666 6600 0000 3f76 4d39 3bd2 7d92 3d14 36e2 3e87 15ae c023 6275 6e64 6c65 00bc 17d0 d5b0 0480 0000 0000 402f 7365 6e73 6f72 7300 0000 002c 6666 6666 6666 6666 6666 003e c1ab acbd c8e7 97bd a6e9 1a3d 8e62 f03c 13bf 4f3f 7ded 2741 7d91 7541 2779 1dc1 b846 5444 7bee b8c0 2362 756e 646c 6500 bc17 d0d5 b004 8000 0000 0024 2f71 7561 7465 726e 696f 6e00 2c66 6666 6600 0000 3f76 4c7f 3bd2 34a6 3d14 355e 3e87 1b02 c023 6275 6e64 6c65 00bc 17d0 d5b5 0cd0 0000 0000 402f 7365 6e73 6f72 7300 0000 002c 6666 6666 6666 6666 6666 00bd 62a8 a03e 0e3a 0dbd a6e2 c23d 9581 0b3c 151e fa3f 7fa1 7741 7d91 7541 2779 1dc1 b846 5444 7bee b8c0 2362 756e 646c 6500 bc17 d0d5 b50c d000 0000 0024 2f71 7561 7465 726e 696f 6e00 2c66 6666 6600 0000 3f76 4bd5 3bd1 facd 3d14 34cb 3e87 1fe8 c023 6275 6e64 6c65 00bc 17d0 d5ba 1520 0000 0000 402f 7365 6e73 6f72 7300 0000 002c 6666 6666 6666 6666 6666 003d 8be8 38bd 2007 a8be 1232 253d 8c93 a13b ba10 ee3f 8000 7241 84f4 f741 2780 e9c1 b85d ec44 7bee 81c0 2362 756e 646c 6500 bc17 d0d5 ba15 2000 0000 0024 2f71 7561 7465 726e 696f 6e00 2c66 6666 6600 0000 3f76 4b7d 3bd1 ac47 3d14 2bb1 3e87 229a c023 6275 6e64 6c65 00bc 17d0 d5bf 1d68 0000 0000 402f 7365 6e73 6f72 7300 0000 002c 6666 6666 6666 6666 6666 003e 0562 503d a31b a13e 27fa 593d 9292 9d3b eadb dd2f 3f80 1f20 4184 f4f7 4127 80e9 c1b8 5dec 447b ee81 c023 6275 6e64 6c65 00bc 17d0 d5bf 1d68 0000 0000 242f 7175 6174 6572 6e69 6f6e 002c 6666 6666 0000 003f 764c 583b d191 e43d 142f 1e3e 871c 51c0 2362 756e 646c 6500 bc17 d0d5 c425 b800 0000 0040 2f73 656e 736f 7273 0000 0000 2c66 6666 6666 6666 6666 6600 3d8c 1ea8 3da2 f71b be12 21d1 3d8d 8843 3c1c b397 3f80 00df 4184 f4f7 4127 80e9 c1b8 5dec 447b ee8f c023 6275 6e64 6c65 00bc 17d0 d5c4 c6db dc00 0000 0024 2f71 7561 7465 726e 696f 6e00 2c66 6666 6600 0000 3f76 4d55 3bd1 e025 3d14 19ae 3e87 1572 c023 6275 6e64 6c65 00bc 17d0 d5c9 cf18 0000 0000 402f 7365 6e73 6f72 7300 0000 002c 6666 6666 6666 6666 6666 00bd 63ba 503e 0e2e da3d 29ac e03d 8f81 2f3b e96d 0b3f 7f44 a941 81d2 5241 2da2 e1c1 b856 dc44 7bee 8fc0 2362 756e 646c 6500 bc17 d0d5 c9cf 1800 0000 0024 2f71 7561 7465 726e 696f 6e00 2c66 6666 6600 0000 3f76 4c60 3bd1 fa10 3d14 0e8c 3e87 1c9b c023 6275 6e64 6c65 00bc 17d0 d5c9 cf18 0000 0000 1c2f 7465 6d70 6572 6174 7572 6500 0000 002c 6666 0041 f9f3 b641 f34f e0c0 2362 756e 646c 6500 bc17 d0d5 c9cf 1800 0000 0014 2f68 756d 6964 6974 7900 0000 2c66 0000 4201 6500 c023 6275 6e64 6c65 00bc 17d0 d5a9 31b0 0000 0000 382f 6261 7474 6572 7900 0000 002c 6666 6666 7300 0042 bc0d 0a0d 0a00 7f80 0000 4084 e147 4070 0000 4368 6172 6769 6e67 2063 6f6d 706c 6574 6500 0000 c023 6275 6e64 6c65 00bc 17d0 d5ce d760 0000 0000 402f 7365 6e73 6f72 7300 0000 002c 6666 6666 66"
to_string=bytearray.fromhex(hexstring)
decoded=decodeOSC(to_string)
print "##########################################"
print "##########################################"
print decoded
buffer = bytes()  # .read() returns bytes right?
#while True:
    #if rs232.in_waiting > 0:
    	#print(rs232.readline())
    	
    	# """
     #   	buffer += rs232.read()
     #   	print(buffer.decode)
     #    print "########################################## PRINTING BUFFER ####################################################"
     #    #print buffer
     #   # a=buffer.decode("utf-8") 
     #    #print a
     #    try:
     #        complete = buffer[:buffer.index(b'}')+1]
     #        buffer = buffer[buffer.index(b'}')+1:]  # leave the rest in buffer
     #    except ValueError:
     #        continue  # Go back and keep reading
     #    print('buffer=', complete)
     #    a = buffer.decode('ascii')
     #    print('ascii=', a)
    	# """





class OSCAddressSpace:
	def __init__(self):
		self.callbacks = {}
	def addMsgHandler(self, address, callback):
		"""Register a handler for an OSC-address
		  - 'address' is the OSC address-string. 
		the address-string should start with '/' and may not contain '*'
		  - 'callback' is the function called for incoming OSCMessages that match 'address'.
		The callback-function will be called with the same arguments as the 'msgPrinter_handler' below
		"""
		for chk in '*?,[]{}# ':
			if chk in address:
				raise OSCServerError("OSC-address string may not contain any characters in '*?,[]{}# '")
		
		if type(callback) not in (types.FunctionType, types.MethodType):
			raise OSCServerError("Message callback '%s' is not callable" % repr(callback))
		
		if address != 'default':
			address = '/' + address.strip('/')
			
		self.callbacks[address] = callback
		
	def delMsgHandler(self, address):
		"""Remove the registered handler for the given OSC-address
		"""
		del self.callbacks[address]
	
	def getOSCAddressSpace(self):
		"""Returns a list containing all OSC-addresses registerd with this Server. 
		"""
		return self.callbacks.keys()
	
	def dispatchMessage(self, pattern, tags, data, client_address):
		"""Attmept to match the given OSC-address pattern, which may contain '*',
		against all callbacks registered with the OSCServer.
		Calls the matching callback and returns whatever it returns.
		If no match is found, and a 'default' callback is registered, it calls that one,
		or raises NoCallbackError if a 'default' callback is not registered.
		
		  - pattern (string):  The OSC-address of the receied message
		  - tags (string):  The OSC-typetags of the receied message's arguments, without ','
		  - data (list):  The message arguments
		"""
		if len(tags) != len(data):
			raise OSCServerError("Malformed OSC-message; got %d typetags [%s] vs. %d values" % (len(tags), tags, len(data)))
		
		expr = getRegEx(pattern)
		
		replies = []
		matched = 0
		for addr in self.callbacks.keys():
			match = expr.match(addr)
			if match and (match.end() == len(addr)):
				reply = self.callbacks[addr](pattern, tags, data, client_address)
				matched += 1
				if isinstance(reply, OSCMessage):
					replies.append(reply)
				elif reply != None:
					raise TypeError("Message-callback %s did not return OSCMessage or None: %s" % (self.server.callbacks[addr], type(reply)))
					
		if matched == 0:
			if 'default' in self.callbacks:
				reply = self.callbacks['default'](pattern, tags, data, client_address)
				if isinstance(reply, OSCMessage):
					replies.append(reply)
				elif reply != None:
					raise TypeError("Message-callback %s did not return OSCMessage or None: %s" % (self.server.callbacks['default'], type(reply)))
			else:
				raise NoCallbackError(pattern)
		
		return replies

######
#
# OSCRequestHandler classes
#
######
class OSCRequestHandler(DatagramRequestHandler):
	"""RequestHandler class for the OSCServer
	"""
	def setup(self):
		"""Prepare RequestHandler.
		Unpacks request as (packet, source socket address)
		Creates an empty list for replies.
		"""
		(self.packet, self.socket) = self.request
		self.replies = []

	def _unbundle(self, decoded):
		"""Recursive bundle-unpacking function"""
		if decoded[0] != "#bundle":
			self.replies += self.server.dispatchMessage(decoded[0], decoded[1][1:], decoded[2:], self.client_address)
			return
		
		now = time.time()
		timetag = decoded[1]
		if (timetag > 0.) and (timetag > now):
			time.sleep(timetag - now)
		
		for msg in decoded[2:]:
			self._unbundle(msg)
		
	def handle(self):
		"""Handle incoming OSCMessage
		"""
		decoded = decodeOSC(self.packet)
		if not len(decoded):
			return
		
		self._unbundle(decoded)
		
	def finish(self):
		"""Finish handling OSCMessage.
		Send any reply returned by the callback(s) back to the originating client
		as an OSCMessage or OSCBundle
		"""
		if self.server.return_port:
			self.client_address = (self.client_address[0], self.server.return_port)
		
		if len(self.replies) > 1:
			msg = OSCBundle()
			for reply in self.replies:
				msg.append(reply)
		elif len(self.replies) == 1:
			msg = self.replies[0]
		else:
			return
		
		self.server.client.sendto(msg, self.client_address)
