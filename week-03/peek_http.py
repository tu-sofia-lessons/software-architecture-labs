"""See the protocol: send one raw HTTP GET over a TCP socket and print both sides byte for byte.

Usage (with file_server.py running):
    python peek_http.py /courses/1/materials
    python peek_http.py /courses/1/materials/lecture01.txt
"""
import sys
if sys.version_info < (3, 10):
    sys.exit("Нужен е Python 3.10+ / Python 3.10+ is required (you have %d.%d)." % sys.version_info[:2])
try:
    sys.stdout.reconfigure(errors="replace")      # consoles without UTF-8 (e.g. cp1251) must not crash
except (AttributeError, ValueError):
    pass

import socket

HOST, PORT = "127.0.0.1", 8102


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "/courses/1/materials"
    request = f"GET {path} HTTP/1.1\r\nHost: {HOST}:{PORT}\r\nConnection: close\r\n\r\n"
    print("----- REQUEST (what urllib sends for you) -----")
    print(request.replace("\r\n", "\\r\\n\n"))
    with socket.create_connection((HOST, PORT), timeout=5) as sock:
        sock.sendall(request.encode("ascii"))
        response = b""
        while chunk := sock.recv(4096):
            response += chunk
    print("----- RESPONSE (what urllib parses for you) -----")
    print(response.decode("utf-8", errors="replace").replace("\r\n", "\\r\\n\n"))


if __name__ == "__main__":
    main()
