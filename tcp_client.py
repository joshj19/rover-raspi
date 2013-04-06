#FIXME: This doesn't close its connections!!!!

import serial
import socket
import Queue
import thread
import threading
import time
import json

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
    newPort.open()
    newPort.flush()
    serialPorts.append(newPort)
  print "USB Serial connections initialized"

#Create client socket connection to base station server  
def startSocket():
  global dataSocket
  dataSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  dataSocket.connect((HOST, PORT)) #Connect to the base station's server socket
  dataSocket.settimeout(SOCKET_TIMEOUT)
  print "Socket successfully connected to server"
  print dataSocket

#Starts the producer and consumer threads, socket thread
def startThreads():
  startedThreads = []
  
  sThread = threading.Thread(target=socketThread, args=())
  sThread.start()
  startedThreads.append(sThread)
  
  cThread = threading.Thread(target=commandConsumer, args=())
  cThread.start()
  startedThreads.append(cThread)
  
  #dThread = threading.Thread(target=dataProducer, args=())
  #dThread.start()
  #startedThreads.append(dThread)
  
  return startedThreads

#The function used by the command queue consumer thread
def commandConsumer():
  #TODO
  global commandQueue
  with safeprint:
    print "command queue in consumer thread:"
    print commandQueue
  while not shutdown:
    try:
      command = commandQueue.get(block = False) #Pop a command off the queue
    except Queue.Empty:
      pass
    else:
      handleCommand(command)#Handle the command (Send to microcontroller)

#The function used by the data queue producer thread
def dataProducer():
  #TODO
  global dataQueue
  while not shutdown:
    for port in serialPorts:
      data = readData(port)
      dataQueue.put(data)

#The server socket thread function
def socketThread():
  global commandQueue
  global dataSocket
  global dataQueue
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
    except Queue.Empty:
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
  #with safeprint:
    #print(command)
  #serialPorts[0].write(command + "\n")
  #serialPorts[0].flush()
  pass
  
#The function which reads data from a serial port
def readData(port):
  #TODO
  #Handle the data. The microcontroller will probably be sending raw ASCII data at this point
  #We can serialize it to JSON/BSON here
  newLine = port.readline()
  id = int(newLine[0:2])#get the launchpad id
  newLine = newLine[3, len(newLine)]#strip out the id and delimeter
  if id == 1:
    parseLaunchpad1(newLine)
  elif id == 2:
    parseLaunchpad2(newLine)
  elif id == 3:
    parseLaunchpad3(newLine)
  elif id == 4:
    parseLaunchpad4(newLine)
  elif id == 5:
    parseLaunchpad5(newLine)
  elif id == 6:
    parseLaunchpad6(newLine)
  elif id == 7:
    parseLaunchpad7(newLine)
  else:
    log('Microcontroller id error. ID: ' + id + ' Data: ' + newLine)
    

#Parse data from launchpad #1
def parseLaunchpad1(data):
  global dataQueue
  allTempData = data.split(',')
  for tempData in allTempData:
    sensorTempMapping = tempData.split(:)#returns array with id and temperature reading
    id = int(sensorTempMapping[0])
    temperature = float(sensorTempMapping[1])
    #Example:
    #{"type":"temp", "source_id": 1, "temp": 72.5, "units": "F"}
    dataArray = {'type': 'temp', 'source_id': id, 'temp': temperature}
    dataQueue.put(json.dumps(dataArray))
    

def log(string)
  with safeprint:
    print string
    
#main thread
if __name__ == '__main__':
  print "command queue in main:"
  print commandQueue
  print dataQueue
  startSerial()
  startSocket()
  threads = startThreads()
  
  for waitfor in threads: waitfor.join()
  #time.sleep(20)#FIXME: This will only allow 20 minutes of executable time before crash; should actually use a join call
  #main thread exits here
  with safeprint:
    print "Exiting main thread..."