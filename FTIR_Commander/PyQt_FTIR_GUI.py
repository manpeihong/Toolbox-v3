from PyQt5 import QtNetwork, QtCore, QtGui, uic, QtWidgets
import os
import sys
import sqlite3
try:
	import MySQLdb
except:
	print( "Need to install mysql plugin, run: pip install mysqlclient.")
import hashlib
from datetime import datetime
import re
import configparser

import numpy as np
from .Temperature_Controller import Temperature_Controller
from .Omnic_Controller import Omnic_Controller
from .Graph import Graph

__version__ = '1.00'

def resource_path(relative_path):  # Define function to import external files when using PyInstaller.
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


qtCreatorFile = resource_path(os.path.join("FTIR_Commander", "PyQt_FTIR_GUI.ui" )) # GUI layout file.

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class FtirCommanderWindow(QtWidgets.QWidget, Ui_MainWindow):

	#Set_New_Temperature_K = QtCore.pyqtSignal(float)
	#Turn_Off_Temperature_Control = QtCore.pyqtSignal(float)
	def __init__(self, parent, root_window):
		QtWidgets.QWidget.__init__(self, parent)
		Ui_MainWindow.__init__(self)
		self.setupUi(self)

		self.Init_Subsystems()
		self.Connect_Control_Logic()

		self.temperature_graph.set_title("Measured Temperature Next To Sample")
		self.temperature_graph.setContentsMargins(0, 0, 0, 0)


	def Init_Subsystems( self ):
		config = configparser.ConfigParser()
		config.read( resource_path(os.path.join("FTIR_Commander", "configuration.ini" ) ) )

		self.Connect_To_SQL( config )
		self.temp_controller = Temperature_Controller( config, parent=self )
		self.omnic_controller = Omnic_Controller( config, parent=self )
		temp_controller_recheck_timer = QtCore.QTimer( self )
		temp_controller_recheck_timer.timeout.connect( self.temp_controller.Update )
		temp_controller_recheck_timer.start( 500 )
		omnic_recheck_timer = QtCore.QTimer( self )
		omnic_recheck_timer.timeout.connect( lambda : self.omnic_controller.Update() )
		omnic_recheck_timer.start( 500 )
		self.Temp_Controller_Disconnected()
		self.Omnic_Disconnected()
		self.temp_controller.Device_Connected.connect( self.Temp_Controller_Connected )
		self.temp_controller.Device_Disconnected.connect( self.Temp_Controller_Disconnected )
		self.omnic_controller.Device_Connected.connect( self.Omnic_Connected )
		self.omnic_controller.Device_Disconnected.connect( self.Omnic_Disconnected )

		user = config['Omnic_Communicator']['user']
		if user:
			self.user_lineEdit.setText( user )


	def Temp_Controller_Connected( self, identifier, type_of_connection ):
		self.tempControllerConnected_label.setText( str(identifier) + " Connected" )
		self.tempControllerConnected_label.setStyleSheet("QLabel { background-color: rgba(0,255,0,255); color: rgba(0, 0, 0,255) }")

	def Temp_Controller_Disconnected( self ):
		self.tempControllerConnected_label.setText( "Temperature Controller Not Connected" )
		self.tempControllerConnected_label.setStyleSheet("QLabel { background-color: rgba(255,0,0,255); color: rgba(0, 0, 0,255) }")

	def Omnic_Connected( self, ip_address ):
		self.omnicConnected_label.setText( "Omnic Connected at " + str(ip_address) )
		self.omnicConnected_label.setStyleSheet("QLabel { background-color: rgba(0,255,0,255); color: rgba(0, 0, 0,255) }")

	def Omnic_Disconnected( self ):
		self.omnicConnected_label.setText( "Omnic Not Connected" )
		self.omnicConnected_label.setStyleSheet("QLabel { background-color: rgba(255,0,0,255); color: rgba(0, 0, 0,255) }")

	def Connect_Control_Logic( self ):
		self.Stop_Measurment()
		self.quit_early = False
		self.run_pushButton.clicked.connect( self.Start_Measurement )

		self.temp_controller.Temperature_Changed.connect( self.Temperature_Update )

	def Temperature_Update( self, temperature ):
		#print( "Temp: " + str(QtCore.QDateTime.currentDateTime()) )
		#print( "Temp: " + str(temperature) )
		self.temperature_graph.add_new_data_point( QtCore.QDateTime.currentDateTime(), temperature )

	def Connect_To_SQL( self, configuration_file ):
		try:
			if configuration_file['SQL_Server']['database_type'] == "QSQLITE":
				self.sql_conn = sqlite3.connect( configuration_file['SQL_Server']['database_name'] )
			elif configuration_file['SQL_Server']['database_type'] == "QMYSQL":
				self.sql_conn = MySQLdb.connect(host=configuration_file['SQL_Server']['host_location'],db=configuration_file['SQL_Server']['database_name'],
									user=configuration_file['SQL_Server']['username'],passwd=configuration_file['SQL_Server']['password'])
				self.sql_conn.ping( True ) # Maintain connection to avoid timing out
		except sqlite3.Error as e:
			error = QtWidgets.QMessageBox()
			error.setIcon( QtWidgets.QMessageBox.Critical )
			error.setText( e )
			error.setWindowTitle( "Unable to connect to SQL Database" )
			error.exec_()
			print( e )
			return

		Create_Table_If_Needed( self.sql_conn )

	def Turn_Off_Temp( self ):
		if( self.temp_controller ):
			self.temp_controller.Turn_Off()
			self.temperature_graph.setpoint_temperature = None


	def Start_Measurement( self ):
		temp_start, temp_end, temp_step = float(self.lowerTemp_lineEdit.text()), float(self.upperTemp_lineEdit.text()), float(self.stepTemp_lineEdit.text())
		v_start, v_end, v_step = float(self.lowerVoltage_lineEdit.text()), float(self.upperVoltage_lineEdit.text()), float(self.stepVoltage_lineEdit.text())
		
		sample_name = self.sampleName_lineEdit.text()
		user = str( self.user_lineEdit.text() )
		if( sample_name == "" or user == "" ):
			error = QtWidgets.QMessageBox()
			error.setIcon( QtWidgets.QMessageBox.Critical )
			error.setText( "Must enter a sample name and user" )
			error.setWindowTitle( "Error" )
			error.exec_()
			return
		if( self.temp_checkBox.isChecked() ):
			temperatures_to_measure = np.arange( temp_start, temp_end + temp_step, temp_step )
		else:
			temperatures_to_measure = [None]
		if( self.voltage_checkBox.isChecked() ):
			biases_to_measure = np.arange( v_start, v_end + v_step, v_step )
		else:
			biases_to_measure = [None]

		self.run_pushButton.clicked.disconnect()
		self.run_pushButton.setText( "Stop Measurement" )
		self.run_pushButton.setStyleSheet("QPushButton { background-color: rgba(255,0,0,255); color: rgba(0, 0, 0,255); }")
		self.run_pushButton.clicked.connect( self.Stop_Measurment )

		self.omnic_controller.Request_Settings()
		#self.Run_Measurment_Loop( sample_name, user, temperatures_to_measure, biases_to_measure )

	def Stop_Measurment( self ):
		if self.temp_controller is not None:
			self.temp_controller.Turn_Off()

		try: self.run_pushButton.clicked.disconnect() 
		except Exception: pass
		
		self.run_pushButton.setText( "Run Sweep" )
		self.run_pushButton.setStyleSheet("QPushButton { background-color: rgba(0,255,0,255); color: rgba(0, 0, 0,255); }")
		self.run_pushButton.clicked.connect( self.Start_Measurement )
		self.quit_early = True

	def Run_Measurment_Loop( self, sample_name, user, temperatures_to_measure, biases_to_measure ):
		for temperature in temperatures_to_measure:
			for bias in biases_to_measure:
				self.omnic_controller.Set_Response_Function(
					lambda file_name, file_contents :
					Deal_With_FTIR_Data( file_contents, user, self.sql_conn,
							sample_name, temperature, bias ) )

				if( temperature ): # None is ok, just means we don't know the temperature
					self.temp_controller.Set_Temperature_In_K( temperature )
					self.temp_controller.Turn_On()
					self.temperature_graph.setpoint_temperature = temperature

					while( not self.temp_controller.Temperature_Is_Stable() ):
						QtCore.QCoreApplication.processEvents()
						if( self.quit_early ):
							print( "Quitting measurment early" )
							self.Turn_Off_Temp()
							self.omnic_controller.Set_Response_Function(
								lambda file_name, file_contents : None )

							self.quit_early = False
							return
					print( "Temperature stable around: " + str(temperature) + '\n' )

				print( "Starting Measurement\n" )
				self.omnic_controller.Measure_Sample( sample_name )

				while( not self.omnic_controller.got_file_over_tcp ):
					QtCore.QCoreApplication.processEvents()
					#if( self.quit_early ):
					#	self.Quitting_Early.emit()
					#	return

				self.omnic_controller.got_file_over_tcp = False

		self.Turn_Off_Temp()
		self.omnic_controller.Set_Response_Function(
			lambda file_name, file_contents : None )

		print( "Finished Measurment" )
		self.Stop_Measurment()




def Create_Table_If_Needed( sql_conn ):
	cur = sql_conn.cursor()
	try:
		cur.execute("""CREATE TABLE `ftir_measurements` ( `sample_name` TEXT NOT NULL, `time` DATETIME NOT NULL, `measurement_id` TEXT NOT NULL, `temperature_in_k` REAL, `bias_in_v` REAL )""")
	except (MySQLdb.Error, MySQLdb.Warning) as e:
		pass
		#print(e)
	except:
		pass # Will cause exception if they already exist, but that's fine since we are just trying to make sure they exist

	try:
		cur.execute("""CREATE TABLE `raw_ftir_data` ( `measurement_id` TEXT NOT NULL, `wavenumber` REAL NOT NULL, `intensity` REAL NOT NULL );""")
	except:
		pass # Will cause exception if they already exist, but that's fine since we are just trying to make sure they exist

	cur.close()
	return False

def Deal_With_FTIR_Data( ftir_file_contents, user, sql_conn, sample_name, temperature_in_k, bias_in_v ):
	#output_command_file = open( './test_auto.csv', 'w' )
	#output_command_file.write( file_contents )
	#output_command_file.close()

	wave_number = []
	intensity = []
	for line in re.split( '\n|\r', ftir_file_contents.decode() ):
		data_split = line.split(',')
		if len( data_split ) < 2:
			continue
		wave_number.append( data_split[0] )
		intensity.append( data_split[1] )

	m = hashlib.sha256()
	#m.update( 'Test'.encode() )
	m.update( (sample_name + str( datetime.now() ) + ','.join(intensity) ).encode() )
	measurement_id = m.hexdigest()
	meta_data_sql_string = '''INSERT INTO ftir_measurements(sample_name,user,measurement_id,temperature_in_k,bias_in_v,time) VALUES(%s,%s,%s,%s,%s,now())'''
	data_sql_string = '''INSERT INTO raw_ftir_data(measurement_id,wavenumber,intensity) VALUES(%s,%s,%s)'''
	cur = sql_conn.cursor()
	cur.execute( meta_data_sql_string, (sample_name,user,measurement_id,temperature_in_k,bias_in_v) )
	cur.executemany( data_sql_string, zip([measurement_id for x in range(len(wave_number))],wave_number,intensity) )
	sql_conn.commit()


if __name__ == "__main__":
	app = QtWidgets.QApplication(sys.argv)
	window = FtirCommanderWindow()
	window.show()
	sys.exit(app.exec_())

