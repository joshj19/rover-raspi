import serial
ser = serial.Serial('/dev/ttyACM0', 9600)
ser.open()
ser.flush()
s = "on"
while True:
   input = ser.readline()
   print input