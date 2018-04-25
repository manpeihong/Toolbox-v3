from PyQt5 import QtNetwork, QtCore
#from PyQt5 import QtGui, QtCore, QtWidgets, QtChart, QtNetwork


def Sanitize_SQL( raw_string ):
	# Got regex from https://stackoverflow.com/questions/9651582/sanitize-table-column-name-in-dynamic-sql-in-net-prevent-sql-injection-attack
	if( ';' in raw_string ):
		return ""

	re = QtCore.QRegularExpression( '''^[\p{L}{\p{Nd}}$#_][\p{L}{\p{Nd}}@$#_]*$''' );
	match = re.match( raw_string );
	hasMatch = match.hasMatch();

	if( hasMatch ):
		return raw_string
	else:
		return ""


class Device:
	def __init__( self, pSocket ):
		self.pSocket = pSocket
		self.raw_data_stream = b""

class Device_Communicator( QtCore.QObject ):
	Device_Connected = QtCore.pyqtSignal(str)
	Device_Disconnected = QtCore.pyqtSignal(str)
	Reply_Recieved = QtCore.pyqtSignal(str, Device)
	File_Recieved = QtCore.pyqtSignal(str, bytes, Device)

	def __init__( self, parent, identifier_string, listener_address, port, timeout_ms=5000 ):
		super().__init__( parent )
		#self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
		self.timeout_ms = timeout_ms
		self.port_for_ping = int(port)
		self.active_connections = {}
		self.tcp_server = QtNetwork.QTcpServer()
		self.udp_socket = QtNetwork.QUdpSocket()
		self.identifier_string = identifier_string
		if not listener_address or listener_address == '':
			listener_address = QtNetwork.QHostAddress.AnyIPv4
		if( not self.Listen_For_Replies( listener_address ) ):
			raise Exception( "Failed to find local network " + listener_address.toString() )


	def No_Devices_Connected( self ):
		return not self.active_connections

	def Poll_LocalIPs_For_Devices( self, ip_range ):
		potential_ip_addresses = Convert_IP_Range_To_List( ip_range )
		possible_duplicates = [key.split( ':' )[0] for key in self.active_connections.keys()]

		for ip in [x for x in potential_ip_addresses if x not in possible_duplicates]:
			self.udp_socket.writeDatagram( self.identifier_string.encode(), QtNetwork.QHostAddress(ip), self.port_for_ping )


	def Send_Command( self, command, device = None ):
		if device:
			with_newline = command + '\n'
			device.pSocket.write( QtCore.QByteArray( with_newline.encode('utf-8') ) );
		else:
			for key, device in self.active_connections.items():
				self.Send_Command( command, device )


	def Keep_Retrying_TCP_Connection( self ):
		result = self.tcp_server.listen( ip_to_listen_on, self.port_for_ping )
		if result == False:
			QtCore.QTimer.singleShot( 1000, self, self.Keep_Retrying_TCP_Connection )

	def Listen_For_Replies( self, ip_to_listen_on ):
		result = self.tcp_server.listen( ip_to_listen_on, self.port_for_ping )
		if( not result ):
			return False

		self.tcp_server.destroyed.connect( self.Keep_Retrying_TCP_Connection )

		self.tcp_server.newConnection.connect( self.Handle_New_Connection )

		# Ping connections to test for them disconnecting unexpectedly
		timer = QtCore.QTimer( self )
		timer.timeout.connect( lambda : self.Send_Command( "PING" ) )
		timer.start( 2000 )

		return True

	def Handle_New_Connection( self ):
		new_pSocket = self.tcp_server.nextPendingConnection()
		peer_ip = new_pSocket.peerAddress().toString()
		peer_port = int( new_pSocket.peerPort() )

		peer_identifier = peer_ip + ":" + str( peer_port );
		self.active_connections[ peer_identifier ] = Device( pSocket = new_pSocket )
		connected_device = self.active_connections[ peer_identifier ]
		print( QtCore.QDateTime.currentDateTime().toString() + ": Response from {}:{}".format( peer_ip, peer_port ) )
		# Tell TCP socket to timeout if unexpectedly disconnected
		new_pSocket.setSocketOption( QtNetwork.QAbstractSocket.KeepAliveOption, 1 );

		new_pSocket.disconnected.connect( lambda : self.Socket_Disconnected(peer_identifier) )
		new_pSocket.readyRead.connect( lambda : self.Read_From_Socket(peer_identifier) )
		self.Device_Connected.emit( peer_identifier )
		connected_device.timer = QtCore.QTimer()
		connected_device.timer.setSingleShot( True )
		connected_device.timer.timeout.connect( lambda : self.Socket_Disconnected( peer_identifier ) )
		connected_device.timer.start( self.timeout_ms )

	def Socket_Disconnected( self, peer_identifier ):
		if peer_identifier in self.active_connections.keys():
			print( self.active_connections.keys() )
			socket_to_close = self.active_connections[ peer_identifier ].pSocket
			del self.active_connections[ peer_identifier ]
			socket_to_close.close() # this line calls Socket_Disconnected again, so must delete key first to avoid double calling
			print( "Disconnected with: " + peer_identifier )
			self.Device_Disconnected.emit( peer_identifier )

	def Read_From_Socket( self, peer_identifier ):
		connected_device = self.active_connections[ peer_identifier ]
		connected_device.timer.setInterval( self.timeout_ms )

		data = connected_device.pSocket.readAll()
		connected_device.raw_data_stream += bytes(data)
		#connected_device.raw_data_stream = split_by_line[-1]

		pure_text_messages = []

		# This chunk will extract any files being written over the socket
		re = QtCore.QRegularExpression( '''^FILE\s*"([^\\<>:;,?"*|/]+)"\s*(\d+)$''' );
		rerun = True
		while rerun:
			rerun = False
			split_by_line = connected_device.raw_data_stream.split( b'\n' )
			for index,line in enumerate( split_by_line[:-1] ):
				try:
					if line == b"Ping":
						continue
					else:
						match = re.match( line.decode() );
				except:
					continue
				if not match.hasMatch():
					pure_text_messages.append( line )
					continue

				file_name = match.captured( 1 )
				size_of_file = int(match.captured( 2 ))
				size_of_header = len(line) + 1
				connected_device.raw_data_stream = b'\n'.join( split_by_line[index:] )
				if( len(connected_device.raw_data_stream) >= size_of_header + size_of_file ):
					self.File_Recieved.emit( file_name, connected_device.raw_data_stream[size_of_header:size_of_header + size_of_file], connected_device )
					connected_device.raw_data_stream = connected_device.raw_data_stream[size_of_header + size_of_file:]
					rerun = True # Make sure there were no other interesting messages

				break

		for one_line in pure_text_messages:
			self.Reply_Recieved.emit( one_line.decode(), connected_device )

def Convert_IP_Range_To_List( ip_range ):
	return Recursive_Convert_IP_Range_To_List( ip_range, 0 )

def Recursive_Convert_IP_Range_To_List( ip_range, position ):
	if( position == 4 ):
		return [ ip_range ]

	split_ip = ip_range.split( "." );
	element_range = split_ip[ position ].split( "-" )

	if( len(element_range) == 1 ):
		element_range[ 0 ] = min( 255, max( 0, int(element_range[ 0 ]) ) )
		return Recursive_Convert_IP_Range_To_List( ip_range, position + 1 )
	elif( len(element_range) == 2 ):
		element_range[ 0 ] = min( 255, max( 0, int(element_range[ 0 ]) ) )
		element_range[ 1 ] = min( 255, max( 0, int(element_range[ 1 ]) ) )
		if element_range[ 0 ] > element_range[ 1 ]:
			temp = element_range[ 0 ]
			element_range[ 0 ] = element_range[ 1 ]
			element_range[ 1 ] = temp
		big_list = []
		for i in range( element_range[ 0 ], element_range[ 1 ] + 1 ):
			split_ip[ position ] = str(i)
			ip_with_this_i = '.'.join( split_ip )
			big_list += Recursive_Convert_IP_Range_To_List( ip_with_this_i, position + 1 )

		return big_list

	return []
