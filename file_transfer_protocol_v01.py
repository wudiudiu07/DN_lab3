#!/usr/bin/env python3

########################################################################
#
# GET File Transfer
#
# When the client connects to the server, it immediately sends a
# 1-byte GET command followed by the requested filename. The server
# checks for the GET and then transmits the file. The file transfer
# from the server is prepended by an 8 byte file size field. These
# formats are shown below.
#
# The server needs to have REMOTE_FILE_NAME defined as a text file
# that the client can request. The client will store the downloaded
# file using the filename LOCAL_FILE_NAME. This is so that you can run
# a server and client from the same directory without overwriting
# files.
#
########################################################################

import socket
import argparse
import os
import threading

########################################################################

# Define all of the packet protocol field lengths. See the
# corresponding packet formats below.
CMD_FIELD_LEN = 1 # 1 byte commands sent from the client.
FILE_SIZE_FIELD_LEN  = 8 # 8 byte file size field.

# Packet format when a GET command is sent from a client, asking for a
# file download:

# -------------------------------------------
# | 1 byte GET command  | ... file name ... |
# -------------------------------------------

# When a GET command is received by the server, it reads the file name
# then replies with the following response:

# -----------------------------------
# | 8 byte file size | ... file ... |
# -----------------------------------

# Define a dictionary of commands. The actual command field value must
# be a 1-byte integer. For now, we only define the "GET" command,
# which tells the server to send a file.

CMD = {"GET": 1, "PUT" : 2, "LIST": 3}

MSG_ENCODING = "utf-8"
SCAN_CMD = "SERVICE DISCOVERY"
    
########################################################################
# SERVER
########################################################################

class Server:

    PORT = 30001 #TCP port

    ALL_IF_ADDRESS = "0.0.0.0"
    SERVICE_SCAN_PORT = 30000

    MSG = "Zishu's File Sharing Service"
    MSG_ENCODED = MSG.encode(MSG_ENCODING)

    RECV_SIZE = 1024
    BACKLOG = 5

    FILE_NOT_FOUND_MSG = "Error: Requested file is not available!"

    # This is the file that the client will request using a GET.
    REMOTE_FILE_NAME = "remotefile.txt"

    def __init__(self):
        self.thread_list = []
        self.show_local_files()
        self.create_listen_UDP()
        self.create_listen_TCP()
        self.discovery_thread = threading.Thread(target=self.service_announcement)
        self.discovery_thread.daemon = True
        self.discovery_thread.start()
        self.process_connections_forever()
    
    #outoput the current directory
    def show_local_files(self):
        print("List of files available for sharing:")
        list_files = os.listdir(os.getcwd())
        for file in list_files:
            if os.path.isfile(file):
               print(file)

    ##UDP packet - Service Discovery Port
    ##create UDP packets
    def create_listen_UDP(self):
        try:
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #UDP socket (family,type)
            self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.udp_socket.bind((Server.ALL_IF_ADDRESS, Server.SERVICE_SCAN_PORT))#(Local_IP,Local_Port)
            print(f"Listening for service discovery messages on SDP port {Server.SERVICE_SCAN_PORT}")
        except Exception as msg:
            print(msg)
            exit()

    ###TCP -- File Sharing Port 30001
    def create_listen_TCP(self):
        try:
            # Create the TCP server listen socket in the usual way.
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.tcp_socket.bind((Server.ALL_IF_ADDRESS, Server.PORT))
            self.tcp_socket.listen(Server.BACKLOG)
            print(f"Listening for file sharing connections on port {Server.PORT}.")
        except Exception as msg:
            print(msg)
            exit()
    
    ##Listens for UDP packet; Receive message SERVICE DISCOVERY
    def service_announcement(self):
        try:
            while True:
                recvd_bytes, address = self.udp_socket.recvfrom(Server.RECV_SIZE)
            
                # Decode the received bytes back into strings.
                recvd_str = recvd_bytes.decode(MSG_ENCODING)

                # Check if the received packet contains a service scan
                # command.
                if SCAN_CMD in recvd_str:
                    # Send the service advertisement message back to
                    # the client.
                    self.udp_socket.sendto(Server.MSG_ENCODED, address)
                    
        except Exception as msg:
            print(msg)
        except KeyboardInterrupt:
            print()
        finally:
            print("Closing udp server socket ...")
            self.udp_socket.close()
            exit(1)

    ###TCP -- Receiver connections from client
    def process_connections_forever(self):
        try:
            while True:
                new_client = self.tcp_socket.accept()
                new_thread = threading.Thread(target=self.connection_handler, args=(new_client,))
                self.thread_list.append(new_thread)
                new_thread.daemon = True
                new_thread.start()

        except Exception as msg:
            print(msg)
        except KeyboardInterrupt:
            print()
        finally:
            print("Closing tcp server socket ...")
            self.tcp_socket.close()
            exit(1)

    ###TCP -- Handle connections from client
    def connection_handler(self, client):
        connection, address = client
        print(f"Connection received from address {address[0]} on port {address[1]}.")

        while True:
            try:
                recvd_bytes = connection.recv(Server.RECV_SIZE)
            
                if len(recvd_bytes) == 0:
                    print("Closing client connection ... ")
                    connection.close()
                    break

                # Read the command and see if it is a GET.
            #     cmd = int.from_bytes(connection.recv(CMD_FIELD_LEN), byteorder='big')
            #     if cmd == CMD['LIST']:
            #         pass
            #     elif cmd == CMD['PUT']:
            #         pass
            #     elif cmd == CMD['GET']:
            #         pass

            #     # The command is good. Now read and decode the requested
            #     # filename.
            #     filename_bytes = connection.recv(Server.RECV_SIZE)
            #     filename = filename_bytes.decode(MSG_ENCODING)

            #     # Open the requested file and get set to send it to the
            #     # client.
            #     try:
            #         file = open(filename, 'r').read()
            #     except FileNotFoundError:
            #         print(Server.FILE_NOT_FOUND_MSG)
            #         connection.close()                   
            #         return

            #     # Encode the file contents into bytes, record its size and
            #     # generate the file size field used for transmission.
            #     file_bytes = file.encode(MSG_ENCODING)
            #     file_size_bytes = len(file_bytes)
            #     file_size_field = file_size_bytes.to_bytes(FILE_SIZE_FIELD_LEN, byteorder='big')

            #     # Create the packet to be sent with the header field.
            #     pkt = file_size_field + file_bytes
                
            #     try:
            #         # Send the packet to the connected client.
            #         connection.sendall(pkt)
            #         # print("Sent packet bytes: \n", pkt)
            #         print("Sending file: ", Server.REMOTE_FILE_NAME)
            #     except socket.error:
            #         # If the client has closed the connection, close the
            #         # socket on this end.
            #         print("Closing client connection ...")
            #         connection.close()
            #         return
            except KeyboardInterrupt:
                print()
                print("Closing client connection ... ")
                connection.close()
                break

########################################################################
# CLIENT
########################################################################

class Client:

    RECV_SIZE = 1024  

    BROADCAST_ADDRESS = "255.255.255.255"
    SERVICE_PORT = 30000
    ADDRESS_PORT = (BROADCAST_ADDRESS, SERVICE_PORT)

    SCAN_CYCLES = 1
    SCAN_TIMEOUT = 5

    SCAN_CMD_ENCODED = SCAN_CMD.encode(MSG_ENCODING)

    # Define the local file name where the downloaded file will be
    # saved.
    LOCAL_FILE_NAME = "localfile.txt"

    def __init__(self):
        self.get_socket_UDP()
        self.get_socket_TCP()
        self.run()

    def run(self):
        print("Please input your commands here")
        try:
            while True:
                user_input = input("> ")
                if user_input == 'scan':
                    self.scan_for_service()
                elif user_input == 'llist':
                    self.show_local_files()
                elif user_input.startswith('Connect'):
                    if len(user_input.split()) != 3:
                        print('Invalid input. Connect <IP address> <port>')
                    else:
                        server_address = user_input.split()
                        self.connect_to_server(server_address[1], int(server_address[2]))
                elif user_input == 'bye':
                    self.close_connection()
        except KeyboardInterrupt:
            print("Quit the client")

    def get_socket_UDP(self):
        try:
            # Create an IPv4 UDP socket.
            self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            # Set socket layer socket options.
            self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Arrange to send a broadcast service discovery packet.
            self.udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

            # Set the socket for a socket.timeout if a scanning recv
            # fails.
            self.udp_socket.settimeout(Client.SCAN_TIMEOUT);

        except Exception as msg:
            print(msg)
            exit()

    def get_socket_TCP(self):
        try:
            self.tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except Exception as msg:
            print(msg)
            exit()

    def scan_for_service(self):
        # Collect our scan results in a list.
        scan_results = []

        # Repeat the scan procedure a preset number of times.
        for i in range(Client.SCAN_CYCLES):

            # Send a service discovery broadcast.       
            self.udp_socket.sendto(Client.SCAN_CMD_ENCODED, Client.ADDRESS_PORT)
        
            while True:
                # Listen for service responses. So long as we keep
                # receiving responses, keep going. Timeout if none are
                # received and terminate the listening for this scan
                # cycle.
                try:
                    recvd_bytes, address = self.udp_socket.recvfrom(Client.RECV_SIZE)
                    recvd_msg = recvd_bytes.decode(MSG_ENCODING)

                    # Record only unique services that are found.
                    if (recvd_msg, address) not in scan_results:
                        scan_results.append((recvd_msg, address))
                        continue
                # If we timeout listening for a new response, we are
                # finished.
                except socket.timeout:
                    break

        # Output all of our scan results, if any.
        if scan_results:
            for result in scan_results:
                print(f'{result[0]} found at IP address/port {result[1][0]}, {result[1][1]}')
        else:
            print("No service found.")

    def connect_to_server(self, host, port):
        try:
            self.tcp_socket.connect((host, port))
        except Exception as msg:
            print(msg)
            exit()

    def close_connection(self):
        try:
            self.tcp_socket.close()
        except Exception as msg:
            print(msg)
            exit(1)

    def socket_recv_size(self, length):
        bytes = self.socket.recv(length)
        if len(bytes) < length:
            self.socket.close()
            exit()
        return(bytes)
            
    def get_file(self):

        # Create the packet GET field.
        get_field = CMD["GET"].to_bytes(CMD_FIELD_LEN, byteorder='big')

        # Create the packet filename field.
        filename_field = Server.REMOTE_FILE_NAME.encode(MSG_ENCODING)

        # Create the packet.
        pkt = get_field + filename_field

        # Send the request packet to the server.
        self.socket.sendall(pkt)

        # Read the file size field.
        file_size_bytes = self.socket_recv_size(FILE_SIZE_FIELD_LEN)
        if len(file_size_bytes) == 0:
               self.socket.close()
               return

        # Make sure that you interpret it in host byte order.
        file_size = int.from_bytes(file_size_bytes, byteorder='big')

        # Receive the file itself.
        recvd_bytes_total = bytearray()
        try:
            # Keep doing recv until the entire file is downloaded. 
            while len(recvd_bytes_total) < file_size:
                recvd_bytes_total += self.socket.recv(Client.RECV_SIZE)

            # Create a file using the received filename and store the
            # data.
            print("Received {} bytes. Creating file: {}" \
                  .format(len(recvd_bytes_total), Client.LOCAL_FILE_NAME))

            with open(Client.LOCAL_FILE_NAME, 'w') as f:
                f.write(recvd_bytes_total.decode(MSG_ENCODING))
        except KeyboardInterrupt:
            print()
            exit(1)
        # If the socket has been closed by the server, break out
        # and close it on this end.
        except socket.error:
            self.socket.close()

    def show_local_files(self):
        list_files = os.listdir(os.getcwd())
        for file in list_files:
            if os.path.isfile(file):
               print(file)
            
########################################################################

if __name__ == '__main__':
    roles = {'client': Client,'server': Server}
    parser = argparse.ArgumentParser()

    parser.add_argument('-r', '--role',
                        choices=roles, 
                        help='server or client role',
                        required=True, type=str)

    args = parser.parse_args()
    roles[args.role]()

########################################################################






