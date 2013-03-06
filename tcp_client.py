#FIXME: This doesn't close its connections!!!!

import serial
import socket
import Queue
import thread

serialPortAddresses = ['/dev/ttyACM0'] #all USB device addresses listed here
serialPorts = [] #all serial connections

dataSocket = None #Network socket

BAUD = 9600 #USB microcontroller connnection baud rate
READ_TIMEOUT = 0.1 #0.1 second timeout on read opperations
HOST = 'r04jpjwxc.device.mst.edu' #FIXME: replace with proper address
PORT = 55555 #FIXME: we need to pick a port to opperate on
SOCKET_BUFF_SIZE = 1024 #FIXME: May need to change this
SOCKET_TIMEOUT = 0.05 #Timeout for reading data from the socket

commandQueue = Queue.Queue(0)#global, cross-thread data queue for command data
dataQueue = Queue.Queue(0)#global, cross-thread data queue for sensor data

safeprint = thread.allocate_lock()

shutdown = False


#==============================================================================

#Create USB connections to microcontrollers
def startSerial():
  for address in serialPortAddresses:
    newPort = serial.Serial(address, BAUD)
    newPort.timeout = READ_TIMEOUT
    serialPorts.append(newPort)
  print "USB Serial connections initialized"

#Create client socket connection to base station server  
def startSocket():
  dataSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  dataSocket.connect((HOST, PORT)) #Connect to the base station's server socket
  dataSocket.settimeout(SOCKET_TIMEOUT)
  print "Socket successfully connected to server"
  print dataSocket

#Starts the producer and consumer threads, socket thread
def startThreads():
  thread.start_new_thread(socketThread, ())
  thread.start_new_thread(commandConsumer, ())
  #thread.start_new_thread(dataProducer, ())

#The function used by the command queue consumer thread
def commandConsumer():
  #TODO
  while not shutdown:
    try:
      command = commandQueue.get(block = False) #Pop a command off the queue
    except queue.Empty:
      pass
    else:
      handleCommand(command)#Handle the command (Send to microcontroller)

#The function used by the data queue producer thread
def dataProducer():
  #TODO
  while not shutdown:
    for port in serialPorts:
      data = readData(port)
      dataQueue.put(data)

#The server socket thread function
def socketThread():
  while not shutdown:
    #read commands from the socket, write it to the queue
    try:
      command = dataSocket.recv(SOCKET_BUFF_SIZE)
    except socket.timeout:
      pass
    else:
      commandQueue.put(command)
    
    #read data from the queue write it to the socket
    try:
      data = dataQueue.get(block = False) #Pop sensor data off the queue
    except queue.Empty:
      pass
    else:
      #write sensor data to the socket
      try:
        dataSocket.sendall(data)
      except socket.error:
        pass
        #TODO: print error to console

#The function which handles commands
def handleCommand(command):
  #TODO
  with safeprint:
    print(command)
  
#The function which reads data from a serial port
def readData(port):
  #TODO
  #Handle the data. The microcontroller will probably be sending raw ASCII data at this point
  #We can serialize it to JSON/BSON here
  pass

#main thread
if __name__ == '__main__':
  print commandQueue
  print dataQueue
  startSerial()
  startSocket()
  startThreads()
  #main thread exits here