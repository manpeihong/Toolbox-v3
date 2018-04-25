try:
	import serial
except:
	print( 'Need to install PySerial, run: pip install PySerial' )
	exit()

import re
import glob
import sys
import numpy as np
from time import sleep

from PyQt5 import QtCore

from .Device_Communicator import Device_Communicator

class Temperature_Controller( QtCore.QObject ):
	"""Interface with serial com port to control temperature"""
	Temperature_Changed = QtCore.pyqtSignal(float)
	Device_Connected = QtCore.pyqtSignal(str,str)
	Device_Disconnected = QtCore.pyqtSignal(str,str)

	def __init__( self, configuration_file, parent=None ):
		super().__init__( parent )
		success = False
		self.serial_connection = None

		try:
			self.device_communicator = Device_Communicator( parent, identifier_string=configuration_file['Temperature_Controller']['Listener_Type'], listener_address=None,
												  port=configuration_file['Temperature_Controller']['Listener_Port'] )
			self.device_communicator.Poll_LocalIPs_For_Devices( configuration_file['Temperature_Controller']['ip_range'] )
			success = True
			self.device_communicator.Reply_Recieved.connect( lambda message, device : self.ParseMessage( message ) )
			self.device_communicator.Device_Connected.connect( lambda peer_identifier : self.Device_Connected.emit( peer_identifier, "Wifi" ) )
			self.device_communicator.Device_Disconnected.connect( lambda peer_identifier : self.Device_Disconnected.emit( peer_identifier, "Wifi" ) )

		except:
			self.device_communicator = None

		if( not success ):
			raise Exception( "Issue connecting to wifi with given configuration.ini, please make sure it is connected" )

		self.current_temperature = None
		self.setpoint_temperature = None
		self.partial_serial_message = ""
		self.past_temperatures = []
		self.stable_temperature_sample_count = 20

	def Attempt_Serial_Connection( self ):
		for port in GetAvailablePorts():
			try:
				self.serial_connection = serial.Serial(port, 115200, timeout=0)
				self.Device_Connected.emit( str(port), "Serial" )
				return True
			except:
				pass

		return False

	def Update( self ):
		if( self.device_communicator.No_Devices_Connected() ):
			self.device_communicator.Poll_LocalIPs_For_Devices( '192.168.1-2.2-254' )
			if not self.serial_connection:
				self.Attempt_Serial_Connection()

		if self.serial_connection is not None:
			if not self.device_communicator.No_Devices_Connected():
				self.serial_connection.close()
				self.serial_connection = None
			else:
				try:
					temp = self.serial_connection.readline()
					self.partial_serial_message += temp.decode("utf-8", "ignore")
					split_into_messages = self.partial_serial_message.split( '\n' )
					self.partial_serial_message = split_into_messages[ -1 ]
					for message in split_into_messages[:-1]:
						self.ParseMessage( message )

				except serial.SerialTimeoutException:
					pass
					#print('Data could not be read')
				except serial.serialutil.SerialException:
					self.serial_connection.close()
					self.serial_connection = None

	def Set_Temperature_In_K( self, temperature_in_k ):
		print( "Setting output temperature to " + str(temperature_in_k) )
		temperature_in_c = temperature_in_k - 273.15
		self.setpoint_temperature = temperature_in_k
		message = ("Set Temp " + str(temperature_in_c) + ";\n")
		if self.serial_connection is not None:
			self.serial_connection.write( message.encode() )

		self.device_communicator.Send_Command( message )

	def Turn_On( self ):
		print( "Turning PID On" )
		message = ("turn on;\n")
		if self.serial_connection is not None:
			self.serial_connection.write( message.encode() )

		self.device_communicator.Send_Command( message )

	def Turn_Off( self ):
		print( "Turning PID Off" )
		message = ("turn off;\n")
		if self.serial_connection is not None:
			self.serial_connection.write( message.encode() )

		self.device_communicator.Send_Command( message )

	def Get_Temperature_In_K( self ):
		return self.current_temperature

	def ParseMessage( self, message ):
		pattern = re.compile( r'Temperature = (-?\d+(\.\d+)?([eE][-+]?\d+?)?)' ) # Grab any properly formatted floating point number
		debug_pattern = re.compile( r"Temperature setpoint changed to " );
		m = pattern.match( message )
		if( m ):
			self.current_temperature = float( m.group( 1 ) ) + 273.15
			self.Temperature_Changed.emit( self.current_temperature )
			self.past_temperatures.append( self.current_temperature )
			if( len(self.past_temperatures) > self.stable_temperature_sample_count ):
				self.past_temperatures = self.past_temperatures[-self.stable_temperature_sample_count:]
		elif( debug_pattern.match( message ) ):
			print( message )

	def Temperature_Is_Stable( self ):
		if( len(self.past_temperatures) < self.stable_temperature_sample_count ):
			return False
		error = np.array( self.past_temperatures ) - self.setpoint_temperature
		deviation = np.std( error )
		average_error = np.mean( error )
		if( abs(average_error) < .5 and deviation < 0.2 ):
			return True
		else:
			return False

# Function from: https://stackoverflow.com/questions/12090503/listing-available-com-ports-with-python/14224477#14224477
def GetAvailablePorts():
	""" Lists serial port names

		:raises EnvironmentError:
			On unsupported or unknown platforms
		:returns:
			A list of the serial ports available on the system
	"""
	if sys.platform.startswith('win'):
		ports = ['COM%s' % (i + 1) for i in range(256)]
	elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
		# this excludes your current terminal "/dev/tty"
		ports = glob.glob('/dev/tty[A-Za-z]*')
	elif sys.platform.startswith('darwin'):
		ports = glob.glob('/dev/tty.*')
	else:
		raise EnvironmentError('Unsupported platform')

	result = []
	for port in ports:
		try:
			s = serial.Serial(port)
			s.close()
			result.append(port)
		except (OSError, serial.SerialException):
			pass
	return result

