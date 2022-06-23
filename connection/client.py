import os
import sys
import socket
from logging import log, debug, error, INFO, DEBUG, ERROR

import Connection as c
from util import FileHandler, Crypto, Format


class Client:
    def __init__(self):
        self.client = socket.socket()

    # private
    def _send_tokens(self, tokens: [str]) -> None:
        self.client.send(bytes(" ".join(str(token) for token in tokens), encoding=c.encoding_format))

    def _send_file(self, file_path: str) -> None:
        file_path = file_path.replace("\"", "")
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            log(INFO, f"File {file_path} does not exist.")
            return

        file_name = str(os.path.basename(file_path.encode("unicode_escape"))).replace("b\'", "").replace("\'", "")
        file_size = os.path.getsize(file_path)
        log(INFO, f" Uploading file with size {Format.file_size(file_size)}")

        # send header
        self.client.send(bytes(f"{c.file_header}:<{file_name}+{file_size}>", c.encoding_format))

        # send file data
        read = 0
        for chunk in FileHandler.read_chunks(file_path, c.buffer):
            self.client.send(chunk)
            read += len(chunk)

            # print out data update
            sys.stdout.write("\033[2K\033[1G")
            log(INFO,
                f"[i] Outgoing: {Format.file_size(read)}/{Format.file_size(file_size)} ({(read / file_size * 100):.2f}%)",
                end="\r")
        log(INFO, f"[i] Outgoing: {Format.file_size(file_size)}/{Format.file_size(file_size)} (100.00%)")
