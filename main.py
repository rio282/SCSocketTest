#!/usr/bin/env python3
import os
import sys
import argparse
from typing import Final

from util.ModuleInstaller import install_modules
from connection.server import Server
from connection.client import Client
from connection.connection import default_port

app_id: Final[str] = "PACKET_SERVICE_COMMUNICATOR"


def main(argv) -> None:
    exit_code: int = 0
    try:
        if argv.server and not argv.client:  # if we want to run the server and not client
            print(f"[i] Default port: {default_port}")
            port = input("Server port you want to use: ")
            server = Server(port)
            server.start_server()
        else:
            server_address = input("Sever address: ")
            print(f"[i] Default port: {default_port}")
            port = input("Server port: ")
            client = Client(server_address, port)
            client.connect()
    except Exception as e:
        print("Error: ", e)
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
    main(args)
