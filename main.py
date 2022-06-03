#!/usr/bin/env python3
import os
import sys
import argparse
from util.ModuleInstaller import install_modules
from typing import Final

app_id: Final[str] = "PACKET_SERVICE_COMMUNICATOR"


def main(argv) -> None:
    try:
        if argv.server and not argv.client:  # if we want to run the server and not client
            os.system("title [SERVER]")
            print(f"[i] Default port: {Connection.default_port}")
            port = input("Server port you want to use: ")

            # check port
            port = Connection.default_port if port == "" else int(port)
            if not Connection.is_valid_port(int(port)):
                print(f"[!] \"{port}\" is not a valid port.")
                main(argv)

            # create server connection for clients to connect to
            connection = Connection.Server(port)
            connection.host()
        else:
            os.system("title [CLIENT]")
            connection = Connection.Client()
            connection.use()
    except Exception as ex:
        print("Error:", ex)
        os.system("pause")
        sys.exit(1)
    finally:
        os.system("pause")
        sys.exit(0)


if __name__ == "__main__":
    assert sys.version_info >= (3, 8, 0), "Python version too low (3.8.0 >= VERSION >= LATEST)."

    parser = argparse.ArgumentParser(description="Used to initiate Server or Client program.")
    parser.add_argument("--client", "-c", action="store_true",
                        help="Used to start the program as a Client (Enabled by default).")
    parser.add_argument("--server", "-s", action="store_true", help="Used to start the program as a Server.")
    args = parser.parse_args()

    # check for installed modules
    install_modules()
    import Connection

    main(args)
