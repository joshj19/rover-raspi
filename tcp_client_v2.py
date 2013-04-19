#FIXME: This doesn't close its connections!!!!

import serial
import socket
import Queue
import thread
import threading
import time
import json

#TODO:redo this naming scheme
serialPortAddresses = ['/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyACM2', '/dev/ttyACM3', '/dev/ttyACM4', '/dev/ttyACM5', '/dev/ttyACM6', '/dev/ttyACM7'] #all USB device addresses listed here
frontMotorControllerAddress = '/dev/ttyACM2'#front motors microcontroller
rearMotorControllerAddress = '/dev/ttyACM3'#TODO

frontMotorControllerPort = None
rearMotorControllerPort = None
serialPorts = [] #all serial connections

launchpad1 = None;
launchpad2 = None;
launchpad3 = None;
launchpad4 = None;
launchpad5 = None;
launchpad6 = None;
gps = None;
sampleBayServo = None;

dataSocket = None #Network socket

BAUD = 9600 #USB microcontroller connnection baud rate
READ_TIMEOUT = 0.1 #0.1 second timeout on read opperations
HOST = 'r04jpjwxc.device.mst.edu' #FIXME: replace with proper address
#HOST = 'r03tjm6f4.device.mst.edu'
PORT = 55555 #FIXME: we need to pick a port to opperate on
#PORT = 30000
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
    log("Attempting connection on \"" + address + "\"")
    try:
      newPort = serial.Serial(address, BAUD)
      newPort.timeout = READ_TIMEOUT
      newPort.open()
      newPort.write('1')#the microcontroller waits to receive this before its starts writing
      newPort.flush()
      log("Successfully opened serial connection")
      
      identifier = newPort.readline()[0:11]
      if(identifier == "launchpad_1"):
        launchpad1 = newPort
        log("Launchpad 1 connected")
      elif(identifier == "launchpad_2"):
        launchpad2 = newPort
        log("Launchpad 2 connected")
      elif(identifier == "launchpad_3"):
        launchpad3 = newPort
        log("Launchpad 3 connected")
      elif(identifier == "launchpad_4"):
        launchpad4 = newPort
        log("Launchpad 4 connected")
      elif(identifier == "launchpad_5"):
        launchpad5 = newPort
        log("Launchpad 5 connected")
      elif(identifier == "launchpad_6"):
        launchpad6 = newPort
        log("Launchpad 6 connected")
      else:
        log("Unidentified device connected on \"" + address + "\"")
      
      serialPorts.append(newPort)
    except Exception as e:
      log("Connection on \"" + address + "\" failed")
      log(e)

#  =================================================
#  Deprecated motor controller initialization code      
#  try:
#    frontMotorControllerPort = serial.Serial(frontMotorControllerAddress, BAUD)
#    frontMotorControllerPort.timeout = READ_TIMEOUT
#    frontMotorControllerPort.open()
#    
#    rearMotorControllerPort = serial.Serial(rearMotorControllerAddress, BAUD)
#    rearMotorControllerPort.timeout = READ_TIMEOUT
#    rearMotorControllerPort.open()
#  except Exception:
#    log('Failed to connect to motor controllers\' serial port')
#  ============================================================
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
  
  dThread = threading.Thread(target=dataProducer, args=())
  dThread.start()
  startedThreads.append(dThread)
  
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
      commands = command.split('\n')
      for singleCommand in commands:
        commandQueue.put(singleCommand.strip('\n'))
        log("Put this in command queue: " + singleCommand)
    
    #read data from the queue write it to the socket
    try:
      data = dataQueue.get(block = False) #Pop sensor data off the queue
    except Queue.Empty:
      pass
    else:
      #write sensor data to the socket
      try:
        if data is not None and isinstance(data, str):
          dataSocket.sendall(data)
          with safeprint:
            print 'Sent: ' + data
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
  try:
    jsonData = json.loads(command)
    type = jsonData['type']
    log(type)
    if type == 'drive_motor':
      handleDriveMotorCommand(jsonData)#TODO
    elif type == 'box_drop':
      handleBoxDropCommand(jsonData)#TODO
    elif type == 'arm':
      handleArmCommand(jsonData);#TODO
    elif type == 'sample_bay':
      handleSampleBayCommand(jsonData)#TODO
    else:
      log('Command type error. Command: ' + command)
  except Exception as e:
    log("Failed to parse JSON: " + command)
    log(e)
  
#The function which reads data from a serial port
def readData(port):
  #TODO
  #Handle the data. The microcontroller will probably be sending raw ASCII data at this point
  #We can serialize it to JSON/BSON here
  try:
    newLine = port.readline()
    id = int(newLine[0:2])#get the launchpad id
    newLine = newLine[3:]#strip out the id and delimeter
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
  except Exception:
    pass #some sort of error, move on
    

#Parse data from launchpad #1
def parseLaunchpad1(data):
  global dataQueue
  allTempData = data.split(',')
  for tempData in allTempData:
    sensorTempMapping = tempData.split(':')#returns array with id and temperature reading
    id = int(sensorTempMapping[0])
    temperature = float(sensorTempMapping[1])
    #Example:
    #{"type":"temp", "source_id": 1, "temp": 72.5, "units": "F"}
    dataArray = {'type': 'temp', 'source_id': id, 'temp': temperature}
    dataQueue.put(json.dumps(dataArray))
    

#Parse data from launchpad #2
#DEBUG THIS
def parseLaunchpad2(data):
  global dataQueue
  allTempData = data.split(',')
  for tempData in allTempData:
    sensorTempMapping = tempData.split(':')#returns array with id and temperature reading
    id = int(sensorTempMapping[0])
    temperature = float(sensorTempMapping[1])
    #Example:
    #{"type":"temp", "source_id": 1, "temp": 72.5, "units": "F"}
    dataArray = {'type': 'temp', 'source_id': id, 'temp': temperature}
    dataQueue.put(json.dumps(dataArray))
    
#FIXME: this will need to be changed to add the altitude sensor
def parseLaunchpad3(data):
  global dataQueue
  allBatteryData = data.split(',')
  for batteryData in allBatteryData:
    batteryDataMapping = batteryData.split(':')
    id = int(batteryDataMapping[0])
    charge = float(batteryDataMapping[1])
    #Example:
    #{"type":"battery", "source_id": 1, "charge_percent":, 80.5}
    dataArray = {'type': 'battery', 'source_id': id, 'charge': charge}
    dataQueue.put(json.dumps(dataArray))
  
#TODO
def parseLaunchpad4(data):
  #front motor controls; no data to read in
  pass
  
#TODO
def parseLaunchpad5(data):
  #rear motor controls; no data to read in
  pass

#TODO
def parseLaunchpad6(data):
  #auxillary controls; no data to read in
  pass

#TODO
def parseLaunchpad7(data):
  pass

#==============================================================================
#Command handlers

#TODO
def handleDriveMotorCommand(command):
  try:
    #parse data and send to launchpad
    action = command['action']#the type of action the motor should take
    motorID = command['id']#id of the motor
    
    commandString = 'M:0' + int(motorID) + ','#DEBUG
    
    if action == 'slew_axis':
      speed = command['speed']
      commandString += 'SL:' + motorNumFormat(speed)
      
      if motorID == 1 or motorID == 2:
        if launchpad4 is not None:
          log("Writing to lanuchpad4: " + commandString)
          launchpad4.write(commandString)
          launchpad4.flush()
        else:
          log("Unable to handle motor command, controller 4 not initialized.")
      elif motorID == 3 or motorID == 4:
        if launchpad5 is not None:
          launchpad5.write(commandString)
          launchpad5.flush()
        else:
          log("Unable to handle motor command, controller 5 not initialized.")
      
    elif action == 'move_relative':
      pass#TODO
    elif action == 'move_absolute':
      pass#TODO
  except:
    log('Failed to handle motor drive command. Command: ' + command)

#Formats an integer to always utilize four string characters
def motorNumFormat(value):
  string = ''
  if value < 10:
    string += '000' + int(value)
  elif value < 100:
    string += '00' + int(value)
  elif value < 1000:
    string += '0' + int(value)
  else:
    string += int(value)
  return string
    
#TODO
def handleBoxDropCommand(command):
  pass
  
#TODO
def handleArmCommand(command):
  pass
  
#TODO
def handleSampleBayCommand(command):
  pass

#==============================================================================

def log(string):
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