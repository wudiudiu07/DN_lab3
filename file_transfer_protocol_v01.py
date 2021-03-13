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

CMD = { "PUT": 1, "GET" : 2 }

MSG_ENCODING = "utf-8"
    
########################################################################
# SERVER
########################################################################

class Server:

    HOSTNAME = "127.0.0.1"
    BROADCAST_PORT = 30000
    PORT = 50000 #TCP port
    RECV_SIZE = 1024
    BACKLOG = 5

    FILE_NOT_FOUND_MSG = "Error: Requested file is not available!"

    # This is the file that the client will request using a GET.
    REMOTE_FILE_NAME = "remotefile.txt"

    def __init__(self):
        #outoput the current directory
        print("List of files available for sharing:")
        list_files = os.listdir(os.getcwd())
        for file in list_files:
            if os.path.isfile(file):
               print(file)
        #self.create_listen_socket()
        #self.process_connections_forever()
        self.create_listen_UDP()
        self.connections_UDP_forever()
    
    ##UDP packet - Service Discovery Port
    ##create UDP packets
    def create_listen_UDP(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) #UDP socket (family,type)
            self.socket.bind((Server.HOSTNAME, Server.BROADCAST_PORT))#(Local_IP,Local_Port)
            print("Listening for service discovery messages on SDP port {port}".format(port_num = Server.BROADCAST_PORT))
        except Exception as msg:
            print(msg)
            exit()
    
    ##Listens for UDP packet; Receive message SERVICE DISCOVERY
    def connections_UDP_forever(self)：
        try:
            while True:
                bytesAddressPair = self.socket.recvfrom(Server.RECV_SIZE)
                data = bytesAddressPair[0]
                address = bytesAddressPair[1]
                if (data.decode('utf-8') == "Service Discovery"):
                    #data_to_send = str.encode("Zishu's File Sharing Service")
                    #print("message content:{}".format(data))
                    #print("client IP address:{}".format(address))
                    self.socket.sendto("Zishu's File Sharing Service".encode('utf-8'), address)
                    self.create_listen_socket()
                    self.process_connections_forever()
        except KeyboardInterrupt:
            print()
        finally:
            self.socket.close()
    
    
    
    ###TCP -- File Sharing Port 30001
    def create_listen_socket(self):
        try:
            # Create the TCP server listen socket in the usual way.
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((Server.HOSTNAME, Server.PORT))
            self.socket.listen(Server.BACKLOG)
            print("Listening on port {} ...".format(Server.PORT))
        except Exception as msg:
            print(msg)
            exit()

    def process_connections_forever(self):
        try:
            while True:
                self.connection_handler(self.socket.accept())
        except KeyboardInterrupt:
            print()
        finally:
            self.socket.close()

    def connection_handler(self, client):
        connection, address = client
        print("-" * 72)
        print("Connection received from {}.".format(address))

        # Read the command and see if it is a GET.
        cmd = int.from_bytes(connection.recv(CMD_FIELD_LEN), byteorder='big')
        if cmd != CMD["GET"]:
            print("GET command not received!")
            return

        # The command is good. Now read and decode the requested
        # filename.
        filename_bytes = connection.recv(Server.RECV_SIZE)
        filename = filename_bytes.decode(MSG_ENCODING)

        # Open the requested file and get set to send it to the
        # client.
        try:
            file = open(filename, 'r').read()
        except FileNotFoundError:
            print(Server.FILE_NOT_FOUND_MSG)
            connection.close()                   
            return

        # Encode the file contents into bytes, record its size and
        # generate the file size field used for transmission.
        file_bytes = file.encode(MSG_ENCODING)
        file_size_bytes = len(file_bytes)
        file_size_field = file_size_bytes.to_bytes(FILE_SIZE_FIELD_LEN, byteorder='big')

        # Create the packet to be sent with the header field.
        pkt = file_size_field + file_bytes
        
        try:
            # Send the packet to the connected client.
            connection.sendall(pkt)
            # print("Sent packet bytes: \n", pkt)
            print("Sending file: ", Server.REMOTE_FILE_NAME)
        except socket.error:
            # If the client has closed the connection, close the
            # socket on this end.
            print("Closing client connection ...")
            connection.close()
            return

########################################################################
# CLIENT
########################################################################

class Client:

    RECV_SIZE = 10

    # Define the local file name where the downloaded file will be
    # saved.
    LOCAL_FILE_NAME = "localfile.txt"

    def __init__(self):
        self.get_socket()
        self.connect_to_server()
        self.get_file()

    def get_socket(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except Exception as msg:
            print(msg)
            exit()

    def connect_to_server(self):
        try:
            self.socket.connect((Server.HOSTNAME, Server.PORT))
        except Exception as msg:
            print(msg)
            exit()

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






