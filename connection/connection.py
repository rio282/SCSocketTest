import socket
from abc import abstractmethod
from typing import Final
from logging import log, debug, error, INFO, DEBUG, ERROR


class Connection:
    def __init__(self, port: int):
        # assign port
        port = default_port if port == "" else port  # if nothing is supplied, we assign the default port
        if not self.is_valid_port(port):
            error(f"{port} is not a valid port number.")
            return
        self.port: Final[int] = port

        # connection settings
        self.buffer: Final[int] = 1024
        self.encoding_format: Final[str] = "ISO-8859-1"

        # request headers
        self.file_header: Final[str] = "FILE::HEADER"
        self.client_disconnect_request: Final[str] = "REQ::SERVER:DISCONNECT_SELF"
        self.server_close_request: Final[str] = "REQ::SERVER::CLOSE"

    @staticmethod
    def get_ip() -> str:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0)
        try:
            # doesn't even have to be reachable
            s.connect(("10.255.255.255", 1))
            ip = s.getsockname()[0]
        except Exception:
            ip = "127.0.0.1"
        finally:
            s.close()
        return ip

    @staticmethod
    def is_valid_ipv4(ip: str) -> bool:
        try:
            socket.inet_aton(ip)
            return True
        except socket.error:
            return False

    @staticmethod
    def is_valid_port(port: int) -> bool:
        try:
            if not isinstance(port, int):
                raise ValueError()
            return 1 <= port <= 65535
        except:
            return False

    @staticmethod
    def flush_socket(sock: socket.socket) -> None:
        f = sock.makefile()
        f.flush()

    # abstracts
    @abstractmethod
    def create_socket(self) -> None:
        raise NotImplementedError()

    @abstractmethod
    def close_connection(self) -> None:
        raise NotImplementedError()


default_port: Final[int] = 55555
localhost: Final[str] = Connection.get_ip()
