import os
import sys
import socket
from typing import Final
from pathlib import Path

from util import FileHandler, Crypto, Format
from util.Windows import Windows


def is_ipv4(ip: str) -> bool:
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False


def is_valid_port(port: int) -> bool:
    return 1 <= port <= 65535


def get_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


def flush_socket(sock: socket.socket):
    f = sock.makefile()
    f.flush()


localhost: Final[str] = get_ip()
default_port: Final[int] = 55555
buffer: Final[int] = 1024
encoding_format: Final[str] = "ISO-8859-1"
socket_timeout: Final[float] = 5.5 * 60  # in seconds

file_header: Final[str] = "FILE::HEADER"
server_close: Final[str] = "SERVER::CLOSE"

downloads_folder: Final[str] = str(Path.home() / "Downloads")
windows: Final[Windows] = Windows()

bs: Final[str] = "\\"


class Client:
    def __init__(self) -> None:
        self.connected = False
        self.host_ip = ""
        self.port = ""
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.settimeout(socket_timeout)

    def _connect(self, tokens: []) -> None:
        if len(tokens) == 0:
            print("[!] Command usage:")
            print("\tconnect host ip")
            print("\tconnect host:ip")
            return

        # split host_ip and port
        if ":" in tokens[0]:
            self.host_ip = tokens[0][:tokens[0].find(":")]
            self.port = int(tokens[0][tokens[0].find(":") + 1:])
        else:
            self.host_ip = tokens[0]
            self.port = int(tokens[1])

        # try to connect
        try:
            print(f"[*] Attempting to establish connection with server {self.host_ip}:{self.port}")

            self.client.connect((self.host_ip, self.port))
            self.connected = True

            print(f"[*] Connected to server {self.host_ip}:{self.port}")
        except:
            self.connected = False
            print(f"[!] Could not connect to server {self.host_ip}:{self.port}")

    def _disconnect(self):
        if not self.connected:  # check if connected to a server
            print("[i] Bro... You\'re not even connected to a server. What are you smoking rn?")
            return

        # close connection
        self.client.close()
        self.connected = False
        print(f"[!] Disconnected from server {self.host_ip}:{self.port}")

    def use(self) -> None:
        print("[!] Not connected to a server yet...")

        # create and send data to server
        while True:
            try:
                # handle request
                outgoing = input("CLIENT_<You>~$ ")
                command_fired = self._command_handler(outgoing.split(" "))
                if not self.connected or not command_fired:
                    continue

                # handle server response
                response = self.client.recv(buffer).decode(encoding_format)
                if response:
                    print(f"__Server: {response}")
                print()
            except Exception as ex:
                if isinstance(ex, socket.timeout):
                    flush_socket(self.client)
                    print("[!] No server response. Flushed socket.")
                    continue
                print("[!] Client error:", ex)
                return

    def _command_handler(self, tokens: [str]) -> bool:
        cmd = tokens[0]
        tokens = tokens[1:]
        cmd_connect = ["connect", "c"]
        cmd_disconnect = ["disconnect", "dc"]
        cmd_text = ["text", "t"]
        cmd_encrypted_text = ["enc_text", "et"]
        cmd_file = ["file", "f"]
        cmd_exit = ["exit", "quit", "q"]

        if cmd == "":  # if we get no command we just return
            return False
        elif cmd in cmd_connect:
            self._connect(tokens)
            return True
        elif cmd in cmd_disconnect:
            self._disconnect()
            return True

        # actual commands
        if not self.connected:
            return False
        elif cmd in cmd_text:
            self._send_tokens(tokens)
        elif cmd in cmd_encrypted_text:
            self._send_tokens(Crypto.encrypt(tokens))
        elif cmd in cmd_file:
            self._send_file(" ".join(tokens))
        elif cmd in cmd_exit:
            self.client.send(bytes(server_close, encoding_format))
            self.client.close()
            sys.exit(0)
        else:
            print(f"[!] Command \'{cmd}\' unknown.")
            return False
        return True

    def _send_tokens(self, tokens: [str]) -> None:
        self.client.send(bytes(" ".join(str(token) for token in tokens), encoding=encoding_format))

    def _send_file(self, file_path: str) -> None:
        file_path = file_path.replace("\"", "")
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            print(f"[!] File {file_path} does not exist.")
            return

        file_name = str(os.path.basename(file_path.encode("unicode_escape"))).replace("b\'", "").replace("\'", "")
        file_size = os.path.getsize(file_path)
        print(f"[*] Uploading file with size {Format.file_size(file_size)}")

        # send header
        self.client.send(bytes(f"{file_header}:<{file_name}+{file_size}>", encoding_format))

        # send file data
        read = 0
        for chunk in FileHandler.read_chunks(file_path, buffer):
            self.client.send(chunk)
            read += len(chunk) / buffer

            # print out data update
            sys.stdout.write("\033[2K\033[1G")
            print(
                f"[i] Outgoing: {Format.file_size(read * buffer)}/{Format.file_size(file_size)} ({((read * buffer) / file_size * 100):.2f}%)",
                end="\r")
        print(f"[i] Outgoing: {Format.file_size(file_size)}/{Format.file_size(file_size)} (100.00%)")


class Server:
    allowed_connections: Final[int] = 1

    def __init__(self, port: int) -> None:
        self.port = port
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((localhost, port))
        self.client_socket = socket.socket()
        self.client_id = ""

    def host(self) -> None:
        print(f"[*] Server address: {localhost}:{self.port}")
        print(f"[*] Listening on port {self.port} for an incoming connection...")
        self.server.listen(self.allowed_connections)

        # accept client connection
        self.client_socket, client_address = self.server.accept()
        self.client_id = f"CLIENT_{client_address[0].replace('.', '')}"
        print(f"[!] Received incoming connection from: {client_address[0]}")

        # send data back so the client knows that they've connected
        self.client_socket.send(bytes(
            f"Connection established between client({client_address[0]}) and server({localhost}) on port {self.port}",
            encoding_format))

        while True:
            try:
                # handle data
                incoming = self.client_socket.recv(buffer)
                self._handle_incoming_data(incoming)
            except socket.timeout:
                print("[!] Client socket was closed.")
                print("[!] Reinitializing server socket...")
                # flush and close server
                flush_socket(self.client_socket)
                flush_socket(self.server)
                self.client_socket.close()
                self.server.close()

                self.__init__(self.port)  # re init server class
            except Exception as ex:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                print(
                    f"[!] Server error({type(ex).__name__}): '{ex}' on line {exc_tb.tb_frame.f_code.co_filename[exc_tb.tb_frame.f_code.co_filename.find(f'{bs}'):]}:{exc_tb.tb_lineno}")
                del (exc_type, exc_obj, exc_tb)
                return

    def _handle_incoming_data(self, incoming: bytes) -> None:
        decoded_data = str(incoming.decode(encoding_format))

        # if file
        if decoded_data.startswith(file_header):
            file_name = decoded_data[decoded_data.find("<") + 1:decoded_data.find("+")]
            file_size = int(decoded_data[decoded_data.find("+") + 1:decoded_data.find(">")])
            print(f"[!] Received header for file: \'{file_name}\' with size {Format.file_size(file_size)}")

            temp_file_path = f"{downloads_folder}\\download_{file_name}"
            temp_file = open(file=temp_file_path, mode="ab")
            temp_file.truncate(0)

            read = 0
            while read < file_size:
                data = self.client_socket.recv(buffer)
                if not data:
                    continue

                # write to file if possible
                temp_file.write(data)
                read += len(data)

                # print out data read
                sys.stdout.write("\033[2K\033[1G")
                print(
                    f"[i] Incoming: {Format.file_size(read)}/{Format.file_size(file_size)} ({(read / file_size * 100):.2f}%)",
                    end="\r")
            temp_file.close()

            print()  # goto next line cuz prev was still open
            print(f"[!] Downloaded file to: \'{temp_file_path}\' ({Format.file_size(file_size)})")
            windows.notification("File download complete!",
                                 f"Downloaded file to: \'{temp_file_path}\' ({Format.file_size(file_size)})",
                                 FileHandler.open_file, temp_file_path)
            self.client_socket.send(
                bytes(f"Uploaded file \'{file_name}\' ({Format.file_size(file_size)}) to server!", encoding_format))
        elif decoded_data == server_close:
            self.server.close()
            sys.exit(0)
        else:  # if its just plain text
            print(f"{self.client_id}: {decoded_data}")
            self.client_socket.send(bytes("Received text (OK)!", encoding_format))
