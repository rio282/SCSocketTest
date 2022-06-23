#!/usr/bin/env python3
import os
import sys
import argparse
from typing import Final
import logging
from logging import log, debug, error, INFO, DEBUG, ERROR
from datetime import datetime

from util.ModuleInstaller import install_modules
from connection.server import Server
from connection.client import Client
from connection.connection import default_port

app_id: Final[str] = "PACKET_SERVICE_COMMUNICATOR"


def setup_logger():
    filename = "%Y-%d-%m %H-%M-%S"
    filename = f"LOG__{datetime.strftime(datetime.now(), filename)}.log".replace(" ", "__")
    logging.basicConfig(level=logging.INFO, filename=f"./logs/{filename}", filemode="w+",
                        format="[%(asctime)-15s] (%(levelname)s) %(message)s")


def main(argv) -> None:
    exit_code: int = 0
    try:
        print(f"[i] Default port: {default_port}")
        if argv.server and not argv.client_socket:  # if we want to run the server and not client
            port = input("Server port you want to use: ")
            server = Server(port)
            server.start_server()
        else:
            server_address = input("Sever address: ")
            port = input("Server port: ")
            client = Client(server_address, port)
            client.connect()
    except Exception as e:
        error("Error: ", e)
        exit_code = 1
    finally:
        os.system("pause")
        sys.exit(exit_code)


if __name__ == "__main__":
    assert sys.version_info >= (3, 8, 0), "Python version too low (3.8.0 >= VERSION >= LATEST)."

    parser = argparse.ArgumentParser(description="Used to initiate Server or Client program.")
    parser.add_argument("--client", "-c", action="store_true",
                        help="Used to start the program as a Client (Enabled by default).")
    parser.add_argument("--server", "-s", action="store_true", help="Used to start the program as a Server.")
    args = parser.parse_args()

    # check for installed modules
    install_modules()
    setup_logger()
    main(args)
