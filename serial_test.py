import serial
ser = serial.Serial('/dev/ttyACM0', 9600)
ser.open()
ser.flush()
s = "on"
while s != "quit":
   input = raw_input('LED~ ')
   print input
   ser.write(input + "\n")
   ser.flush()