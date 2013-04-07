import serial
ser = serial.Serial('/dev/ttyACM0', 9600)
ser.open()
ser.write('1')
ser.flush()
s = "on"
while True:
   input = ser.readline()
   print input