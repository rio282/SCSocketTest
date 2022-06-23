import sys
import threading
from abc import ABC
from queue import Queue
from typing import List

from connection.connection import *
from util import FileHandler, Format
from util.Windows import Windows

# server settings
allowed_connections: Final[int] = 5
max_server_threads: Final[int] = allowed_connections + 1

# settings for windows etc
windows: Final[Windows] = Windows()
downloads_folder: Final[str] = windows.get_downloads_folder()


# TODO: instead of print use logging.log
class Server(Connection, ABC):
    def __init__(self, port: int) -> None:
        super().__init__(port)
        self.host_address: Final[str] = localhost
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.clients: List[socket.socket] = []
        self.queue: Queue = Queue()

    # public
    def start_server(self) -> bool:
        try:
            print("[SERVER] Starting server...")

            # bind server socket and listen for incoming connections
            self.server_socket.bind((self.host_address, self.port))
            self.server_socket.listen(allowed_connections)

            print(f"[SERVER] Hosting server on {self.host_address}:{self.port}")
            self._wait_for_clients()
        except Exception as e:
            error("Error: ", e)
            return False
        return True

    def close_server(self) -> None:
        print("[SERVER] Closing server...")
        self._send_to_all_clients("[SERVER] Server closed.")
        self.flush_socket(self.server_socket)
        self.server_socket.close()
        print("[SERVER] Closed server.")
        sys.exit(0)

    def _wait_for_clients(self) -> None:
        # wait for clients and handle their connections
        while True:
            try:
                # on new incoming connection
                client_connection, client_address = self.server_socket.accept()  # returns connection with client and its address
                # check if we can handle more incoming connections
                if threading.activeCount() > max_server_threads:
                    print(f"[SERVER] Could not establish connection with client; limit reached ({allowed_connections})")
                    client_connection.send(bytes("Can't connect to server: too many clients.", self.encoding_format))
                    client_connection.close()
                    continue

                # start client thread
                client_thread = threading.Thread(target=self._on_client_connect,
                                                 args=(client_connection, client_address))
                client_thread.start()
            except KeyboardInterrupt:
                print("[!] Detected KeyboardInterrupt!")
                break
        self.close_server()

    def _on_client_connect(self, client_connection: socket.socket, client_address: str) -> None:
        self.clients.append(client_connection)
        print(f"[SERVER] Received incoming connection from {client_address[0]}")
        print(f"[SERVER] Active clients: {len(self.clients)}")
        connected = True
        while connected:
            incoming = str(client_connection.recv(self.buffer).decode(self.encoding_format))
            # disconnect client if we get disconnect request
            if incoming == self.client_disconnect_request:
                self.__on_client_disconnect(client_connection, client_address)
                connected = False
            # server close request
            elif incoming == self.server_close_request:
                self.close_server()
            else:
                self._handle_incoming_packets(incoming, client_connection, client_address)

    def __on_client_disconnect(self, client_connection: socket.socket, client_address: str) -> None:
        client_connection.close()
        self.clients.remove(client_connection)
        print(f"[SERVER] Client {client_address[0]} disconnected.")
        print(f"[SERVER] Active clients: {len(self.clients)}")

    def _send_to_all_clients(self, message: str) -> None:
        for client in self.clients:
            client.send(bytes(message, self.encoding_format))

    def _handle_incoming_packets(self, incoming: str, client_connection: socket.socket, client_address: str) -> None:
        # if file
        if incoming.startswith(self.file_header):
            self._handle_file_download(incoming, client_connection, client_address)
        # if its just plain text
        else:
            print(f"{client_address[0]}: {incoming}")
            client_connection.send(bytes("Received text (OK)!", self.encoding_format))

    def _handle_file_download(self, file_properties: str, client_connection: socket.socket,
                              client_address: str) -> None:
        # read file properties
        file_name = file_properties[file_properties.find("<") + 1:file_properties.find("+")]
        file_size = int(file_properties[file_properties.find("+") + 1:file_properties.find(">")])
        print(f"[!] Received header for file: \'{file_name}\' with size {Format.file_size(file_size)}")

        # create temp file
        temp_file_path = f"{downloads_folder}\\download_{file_name}"
        temp_file = open(file=temp_file_path, mode="ab")
        temp_file.truncate(0)

        # receive data from client until we downloaded the whole file
        read = 0
        while read < file_size:
            data = client_connection.recv(self.buffer)
            if not data:
                continue

            # write to file if possible
            temp_file.write(data)
            read += len(data)

            # print out data read
            sys.stdout.write("\033[2K\033[1G")  # start on the same line
            print(
                f"[SERVER] Client: {client_address[0]} -- Downloading file... {Format.file_size(read)}/{Format.file_size(file_size)} ({(read / file_size * 100):.2f}%)",
                end="\r")
        temp_file.close()

        print()  # goto next line cuz prev was still open

        # give notification that we've downloaded the file
        print(f"[SERVER] Downloaded file to: \'{temp_file_path}\' ({Format.file_size(file_size)})")
        windows.notification(
            "File download complete!",
            f"Downloaded file to: \'{temp_file_path}\' ({Format.file_size(file_size)})",
            FileHandler.open_file,
            temp_file_path
        )

        # tell client we've downloaded their file
        client_connection.send(
            bytes(f"[SERVER] Uploaded file \'{file_name}\' ({Format.file_size(file_size)}) to server!",
                  self.encoding_format))
