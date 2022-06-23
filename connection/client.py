import os
import sys
from abc import ABC
from typing import List

from connection.connection import *
from util import FileHandler, Format, Crypto


class Client(Connection, ABC):
    def __init__(self, server_address: str, port: int):
        super().__init__(port)
        server_address = localhost if server_address == "" else server_address  # if no address is supplied: use localhost
        if not self.is_valid_ipv4(server_address):
            print(f"{server_address} is not a valid ipv4 address.")
        self.server_address: Final[str] = server_address
        self.client_socket: Final[socket.socket] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self) -> None:
        # connect
        print(f"Connecting to server {self.server_address} on port {self.port}")
        self.client_socket.connect((self.server_address, self.port))

        # use client terminal
        while True:
            try:
                # handle request
                outgoing = input(f'CLIENT_<{self.address_to_id((localhost, "_ID"))}(You)>~$ ')
                valid_command = self._command_handler(outgoing.split(" "))
                if not valid_command:
                    continue

                # handle server response
                response = self.client_socket.recv(self.buffer).decode(self.encoding_format)
                if response:
                    print(f"[SERVER] {response}")
                print()
            except Exception as ex:
                if isinstance(ex, socket.timeout):
                    self.flush_socket(self.client_socket)
                    print("[CLIENT] No server response. Flushed socket.")
                    continue
                print("[CLIENT] Client error:", ex)
                return

    def disconnect(self) -> None:
        # close connection
        self.flush_socket(self.client_socket)
        self.client_socket.close()
        print(f"[CLIENT] Disconnected from server {self.server_address}:{self.port}")

    def _command_handler(self, tokens: List[str]) -> bool:
        # commands
        cmd_text = ["text", "t"]
        cmd_encrypted_text = ["enc_text", "et"]
        cmd_file = ["file", "f"]
        cmd_disconnect = ["disconnect", "dc"]

        # command & other tokens
        cmd = tokens[0]
        tokens = tokens[1:]
        if cmd == "":  # if we get no command we just return
            return False

        # actual commands
        if cmd in cmd_text:
            self._send_tokens(tokens)
        elif cmd in cmd_encrypted_text:
            self._send_tokens(Crypto.encrypt(tokens))
        elif cmd in cmd_file:
            return self._send_file(" ".join(tokens))
        elif cmd in cmd_disconnect:
            print(f"[CLIENT] Disconnecting from server {self.server_address}...")
            self.client_socket.send(bytes(self.client_disconnect_request, self.encoding_format))
            self.flush_socket(self.client_socket)
            self.client_socket.close()
            print("[CLIENT] Disconnected from server.")
            print("Cya soon!")
            sys.exit(0)
        else:
            print(f"[!] Command \'{cmd}\' unknown.")
            return False
        return True

    def _send_tokens(self, tokens: List[str]) -> None:
        self.client_socket.send(bytes(" ".join(str(token) for token in tokens), encoding=self.encoding_format))

    def _send_file(self, file_path: str) -> bool:
        # check if file exists
        file_path = file_path.replace("\"", "")
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            print(f"[CLIENT] File {file_path} does not exist.")
            return False

        # set file properties
        file_name = str(os.path.basename(file_path.encode("unicode_escape"))).replace("b\'", "").replace("\'", "")
        file_size = os.path.getsize(file_path)
        print(f"[CLIENT] Uploading file with size {Format.file_size(file_size)}")

        # send file header
        self.client_socket.send(bytes(f"{self.file_header}:<{file_name}+{file_size}>", self.encoding_format))

        # send file data
        read = 0
        for chunk in FileHandler.read_chunks(file_path, self.buffer):
            self.client_socket.send(chunk)
            read += len(chunk)

            # print out data update
            sys.stdout.write("\033[2K\033[1G")
            print(
                f"[CLIENT] Outgoing: {Format.file_size(read)}/{Format.file_size(file_size)} ({(read / file_size * 100):.2f}%)",
                end="\r")
        print(f"[CLIENT] Outgoing: {Format.file_size(file_size)}/{Format.file_size(file_size)} (100.00%)")
        return True
