import serial
ser = serial.Serial('/dev/ttyACM0', 115200)
ser.open()
ser.flush()
s = "on"
while True:
   input = ser.readline()
   print input