import time
import shutil
import os
from PyQt5 import QtCore

from .Device_Communicator import Device_Communicator
from .FTIR_Config_File import Load_FTIR_Config

class Omnic_Controller( QtCore.QObject ):
	"""Interface with Omnic Windows NT Computer"""
	Device_Connected = QtCore.pyqtSignal(str,str)
	Device_Disconnected = QtCore.pyqtSignal(str,str)

	def __init__( self, configuration_file, parent ):
		super().__init__( parent )
		self.got_file_over_tcp = False
		self.settings = {}

		self.response_function = lambda file_name, file_contents : None
		self.ip_range = configuration_file['Omnic_Communicator']['ip_range']
		try:
			self.device_communicator = Device_Communicator( parent, identifier_string=configuration_file['Omnic_Communicator']['Listener_Type'], listener_address=None,
												  port=configuration_file['Omnic_Communicator']['Listener_Port'], timeout_ms=120000 )
			self.device_communicator.Reply_Recieved.connect( lambda message, device : self.ParseMessage( message ) )
			self.device_communicator.File_Recieved.connect( lambda file_name, file_contents, device : self.ParseFile( file_name, file_contents ) )
			self.device_communicator.Device_Connected.connect( lambda peer_identifier : self.Device_Connected.emit( peer_identifier, "Wifi" ) )
			self.device_communicator.Device_Disconnected.connect( lambda peer_identifier : self.Device_Disconnected.emit( peer_identifier, "Wifi" ) )
		except:
			self.device_communicator = None
			raise Exception( "Issue setting up network listener, please make sure computer is connected to a router" )


	def ParseMessage( self, message ):
		if message == 'Ping':
			return
		#split_values = message.split(' ')
		#name = split_values[0]
		#value = ' '.join( split_values[1:] )
		#self.settings[ name ] = value
		#print( message )

	def ParseFile( self, file_name, file_contents ):
		if file_name.lower() == "settingsfile.exp":
			self.settings = Load_FTIR_Config( file_contents )
			return
		self.response_function( file_name, file_contents )
		self.got_file_over_tcp = True
		pass

	def Update( self ):
		if( self.device_communicator.No_Devices_Connected() ):
			self.device_communicator.Poll_LocalIPs_For_Devices( self.ip_range )

	def SendFile( self, file_path ):
		file = open( file_path, 'r' )
		file_contents = file.read()
		file.close()

		self.device_communicator.Send_Command( "FILE " + str(len(file_contents)) + "\n" + file_contents )

	def Measure_Sample( self, measurement_name ):
		print( "Starting measurement: " + measurement_name )
		self.SendFile( "GetBackground.command" )

	def Set_Response_Function( self, response_function ):
		self.response_function = response_function

	def Request_Settings( self ):
		print( "Getting Settings" )
		self.SendFile( "SaveSettingsFile.command" ) # Make sure the settings file is saved as settings_file.exp (case insensitive) to get it the right place

	def ParseConfigFile( self ):
		pass