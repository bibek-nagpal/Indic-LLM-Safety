"""Run repository tests with external networking blocked.

Windows asyncio needs a loopback socketpair for its event-loop wakeup pipe.
Allow only loopback networking; no DNS lookup/connection to an external host.
The new Phase G tests additionally block all sockets and use HTTP MockTransport.
"""
import socket

import pytest


def main():
    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex
    original_lookup = socket.getaddrinfo

    def local(address):
        if not isinstance(address, tuple) or address[0] not in ("127.0.0.1", "::1", "localhost"):
            raise RuntimeError("offline regression: external network forbidden")

    def connect(sock,address):
        local(address)
        return original_connect(sock,address)

    def connect_ex(sock,address):
        local(address)
        return original_connect_ex(sock,address)

    def lookup(host,*args,**kwargs):
        local((host,0))
        return original_lookup(host,*args,**kwargs)

    socket.socket.connect = connect
    socket.socket.connect_ex = connect_ex
    socket.getaddrinfo = lookup
    return pytest.main(["tests","-q"])


if __name__ == "__main__":
    raise SystemExit(main())
