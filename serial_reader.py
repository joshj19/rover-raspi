import serial
ser = serial.Serial('/dev/usbdev1.5', 9600)
ser.open()
ser.flush()
s = "on"
while True:
   input = serial.readline()
   print input