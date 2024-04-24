# System imports
import socket
import time

########### Socket Server Configs ###########
# SERVER_IP = '172.20.10.4'
# SERVER_IP = '10.0.0.39'
SERVER_IP = '10.0.0.38'
SERVER_PORT = 8001
SLEEP_TIME = 15
OUTPUT_FILE = 'message_log.txt'
MAX_RECONNECT_ATMPS = 10
SLEEP_TIME_IN_BETWEEN_CONNECT_ATMPS = 5
SLEEP_TIME_TO_READ_DATA = 5

########### WQM DESCENT CONFIGS ###########
WQM_DESCENT_TIME = 8000 # ms

########### data selection idx Configs ###########
DELTA_T = 80 # ms
DATA_TIME_STEPS = WQM_DESCENT_TIME // DELTA_T
WQM_SPEED = 0.001 # ft/ms


def parse_data(data_buffer):
	#Handles the data buffer with the elapsed time
	# print(f'This is the buffer {data_buffer}')
	i, time1, time2 = 0, '', ''
	while data_buffer[i].isdigit() or data_buffer[i] == '.':
		time1 += data_buffer[i] 
		i += 1
	i = 255
	while data_buffer[i].isdigit() or data_buffer[i] == '.':
		time2 += data_buffer[i]
		i += 1
	print(f'Time 1: {time1}\t Time 2: {time2}')
	return float(time1), float(time2)

class WQM:
	
	def __init__(self, server_ip, server_port, output_file):
		
		self.server_ip = server_ip
		self.server_port = server_port
		self.output_file = output_file
		self.state, self.eTime1, self.eTime2 = 0, 0, 0
		self.dataIndex1, self.dataIndex2 = -1, -1
		self.SCC_received, self.DC_ongoing, self.ET_received, self.D_received = False, False, False, False
		self.DCP_completed = False

	def _connect_to_wqm(self):

		try: 
			self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			self.client_socket.connect((self.server_ip, self.server_port))
			print(f"Connected to the server at {self.server_ip}:{self.server_port}")
			self.connected = True
			self._set_state()
		except Exception as error:
			print("Error: ", error)

	def _close_client_socket(self):
		try:
			print("Attempting to close client socket")
			self.client_socket.close()
			self.connected = False
			if self.SCC_received:
				self.DC_ongoing = True
			# self._set_state()
			print("Client socket closed")
		except Exception as error:
			print("Error: ", error)

	def _send_message_to_wqm(self, message=""):
		# message = input("Enter a message or 'exit'")	
		# if message.lower() == 'exit':
			# quit()
		# self.client_socket.sendall(f"{message}".encode('utf-8'))
		try:
			if not self.connected:
				return
			if self.state == 1:
				message = "START_COLLECTION"
			elif self.state == 2:
				self._close_client_socket()
				return
			elif self.state == 3:
				message = "SEND_ELAPSED_TIMES"
			elif self.state == 4:
				self._send_indexes_to_wqm()
				return
			elif self.state == 5:
				message = "MISSION_FINISHED"
				self.DCP_completed = True
			self.client_socket.sendall(f"{message}".encode('utf-8'))
			print(f"Sent: {message}")

		except Exception as error:
			print(f"Error: {error}")
			self.connected = False
			self._set_state()

	def _read_message_from_wqm(self):
		try:
			if not self.connected:
				self._set_state()
				return;
			data = self.client_socket.recv(1024)
			print(data)
			decoded_data = data.decode()
			# print(f"Message: {data}")
			if len(decoded_data) == 0:
				print("No message received")
			elif decoded_data == "Pre_DC":
				print("Received Pre_DC message")
			
			elif decoded_data == "Starting DC":
				print("Received Starting DC message")
				self.SCC_received = True
				self._close_client_socket()
				print(f"WQM Descent started, sleeping for {WQM_DESCENT_TIME} [ms]")
			
			elif decoded_data == "Post_DC":
				print("Received Post_DC message")
				self.SCC_received = True
				self.DC_performed = True

			elif decoded_data[0] == "B":
				self.eTime1, self.eTime2 = parse_data(decoded_data[1:])
				self.dataIndex1, self.dataIndex2 = self._wqm_data_selection(self.eTime1, self.eTime2)
				self.dataIndex1 = int(self.dataIndex1)
				self.dataIndex2 = int(self.dataIndex2)
				print(f"The requested indexes are {self.dataIndex1} and {self.dataIndex2}")
				self.SCC_received = True
				self.DC_performed = True
				self.ET_received = True

			elif decoded_data[0] == "C":
				if not self.D_received:
					decoded_data = decoded_data[1:]
					with open(OUTPUT_FILE, 'a', encoding="utf-8") as file:
						file.write("\n")  # Add a newline character
						file.write(decoded_data)
						print(data.decode('utf-8'))
						time.sleep(SLEEP_TIME_TO_READ_DATA) # Might be able to remove
						file.close()
					self.SCC_received = True
					self.DC_performed = True
					self.ET_received = True
					self.D_received = True
				else:
					print("Data already stored")
			elif (decoded_data == "ESP32_Restarted"):
				print("ESP32 reset, need to restart mission")
				self.SCC_received = False
				self.DC_performed = False
				self.ET_received = False
				self.D_received = False
				self.DC_ongoing = False
			else:
				print("Message not readable")

		except Exception as error:
			print(f"Error: {error}")
			self.connected = False
		self._set_state()

	def _send_indexes_to_wqm(self):
		data_string = 'T' + str(self.dataIndex1) + ' ' + str(self.dataIndex2) # Concatenate the bytes into a single buffer
		self.client_socket.send(data_string.encode())
		print(f"Sent {data_string}")
		
	def _set_state(self):
		prevState = self.state
		if self.D_received and self.connected:
			self.state = 5
		elif self.ET_received and self.connected:
			self.state = 4
		elif self.DC_ongoing and self.connected:
			self.state = 3
		elif self.SCC_received and self.connected:
			self.state = 2
		elif self.connected:
			self.state = 1
		else:
			self.state = 0
		
		if prevState != self.state:
			print(f"Raspberry Pi in state {self.state}")

	def _get_state(self):
		return self.state 

	def _get_DCP_completed(self):
		return self.DCP_completed
		
	def _wqm_data_selection(self, descent_start_to__water_time, mission_time):

		# t_0 = wqm received message to begin descent
		# t_1 = wqm enters water
		# t_2 = wqm exist water

		# Calculating the wqm deployment mission time and descent_depth
		descent_start_to__water_time = descent_start_to__water_time*1000
		mission_time = mission_time * 1000
		descent_time = mission_time / 2
		descent_depth = WQM_SPEED * descent_time

		# Calculating depth to save data from
		depth_data_wanted = 1 / 3 * descent_depth
		
		# Returning idxs of selected data
		data_idx_1 = ( depth_data_wanted / WQM_SPEED + descent_start_to__water_time ) // DELTA_T
		data_idx_2 = ( (2 / 3 * descent_depth + descent_depth) / WQM_SPEED + descent_start_to__water_time ) // DELTA_T
		 
		return data_idx_1, data_idx_2

	def deploy(self):

		while not self._get_DCP_completed():

			if self._get_state() == 0:
				
				print("Not connected to server")
				self._connect_to_wqm()

			else:

				print("Currently connected server")
				if self._get_state() == 4:

					print("Giving time for buffer to store all water quality data")
					time.sleep(2)

				self._read_message_from_wqm()
				self._send_message_to_wqm()
