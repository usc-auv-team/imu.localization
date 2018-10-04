import serial

rs232 = serial.Serial(
    port = '/dev/ttyACM1',
    baudrate = 115200,
    parity = serial.PARITY_NONE,
    stopbits = serial.STOPBITS_ONE,
    bytesize = serial.EIGHTBITS,
    timeout = 1
)


buffer = bytes()  # .read() returns bytes right?
while True:
    if rs232.in_waiting > 0:
        buffer += rs232.read()
        try:
            complete = buffer[:buffer.index(b'}')+1]  # get up to '}'
            buffer = buffer[buffer.index(b'}')+1:]  # leave the rest in buffer
        except ValueError:
            continue  # Go back and keep reading
        print('buffer=', complete)
        ascii = buffer.decode('ascii')
        print('ascii=', ascii)
