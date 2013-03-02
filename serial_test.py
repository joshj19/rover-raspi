import serial
ser = serial.Serial('/dev/ttyACM0', 9600)
s = "on"
while s != "quit":
   input = raw_input('LED~ ')
   ser.write(input)