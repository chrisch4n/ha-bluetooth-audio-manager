"""Link quality of a connected speaker without a scan.

BlueZ reports RSSI on D-Bus only during discovery, and a discovery burst on
the adapter that carries the A2DP streams disturbs every one of them (#319),
so the app no longer scans while audio runs.  For a speaker that is already
connected the kernel can ask the controller directly: the Bluetooth
management interface's *Get Connection Information* command
(``MGMT_OP_GET_CONN_INFO``) runs HCI *Read RSSI* and *Read Transmit Power
Level* on the existing link.  That needs no radio time and does not touch
discovery.

Meaning of the values for a BR/EDR (classic) link such as A2DP:

* ``rssi`` is **not** dBm.  The controller reports how far the received
  signal lies outside its "golden receive power range": 0 = inside the range
  (good), negative = that many dB below it (weak), positive = above it.
* ``tx_power`` is the current transmit power of this adapter on the link in
  dBm.  With power control a weak link makes the adapter transmit harder, so
  a value at or near ``max_tx_power`` also points to a weak link.

127 means "not available" for any of the three and is returned as None.

The socket is the management channel (``HCI_CHANNEL_CONTROL``) — not a raw
HCI device socket — and needs CAP_NET_ADMIN (the app has it).
"""

from __future__ import annotations

import ctypes
import errno
import os
import select
import socket
import struct
import time

AF_BLUETOOTH = 31
BTPROTO_HCI = 1
HCI_CHANNEL_CONTROL = 3
HCI_DEV_NONE = 0xFFFF

MGMT_OP_GET_CONN_INFO = 0x0031
MGMT_EV_CMD_COMPLETE = 0x0001
MGMT_EV_CMD_STATUS = 0x0002
BDADDR_BREDR = 0x00
INVALID = 127

MGMT_STATUS = {
    0x02: "not connected",
    0x0D: "invalid parameters",
    0x11: "invalid index",
    0x14: "permission denied",
}


class ConnInfoError(OSError):
    """The management interface did not deliver connection information."""


def hci_index(adapter_path: str) -> int:
    """``/org/bluez/hci2`` (or ``hci2``) → 2."""
    name = adapter_path.rstrip("/").rsplit("/", 1)[-1]
    if not name.startswith("hci") or not name[3:].isdigit():
        raise ValueError(f"not an HCI adapter: {adapter_path}")
    return int(name[3:])


def build_request(index: int, address: str) -> bytes:
    """Command packet: header (opcode, index, length) + address (LE) + type."""
    bdaddr = bytes(int(part, 16) for part in reversed(address.split(":")))
    if len(bdaddr) != 6:
        raise ValueError(f"not a Bluetooth address: {address}")
    params = bdaddr + bytes([BDADDR_BREDR])
    return struct.pack("<HHH", MGMT_OP_GET_CONN_INFO, index, len(params)) + params


def _signed(value: int) -> int | None:
    value = value - 256 if value > 127 else value
    return None if value == INVALID else value


def parse_reply(packet: bytes, index: int) -> dict | None:
    """The reply to our command, or None for any other management event.

    Raises ConnInfoError when the kernel rejects the command.
    """
    if len(packet) < 6:
        return None
    event, ev_index, length = struct.unpack_from("<HHH", packet)
    body = packet[6:6 + length]
    if ev_index != index or event not in (MGMT_EV_CMD_COMPLETE, MGMT_EV_CMD_STATUS):
        return None
    if len(body) < 3:
        return None
    opcode, status = struct.unpack_from("<HB", body)
    if opcode != MGMT_OP_GET_CONN_INFO:
        return None
    if status == 0x14:
        raise PermissionError("management interface: permission denied")
    if status != 0:
        raise ConnInfoError(MGMT_STATUS.get(status, f"mgmt status 0x{status:02x}"))
    if event != MGMT_EV_CMD_COMPLETE or len(body) < 3 + 7 + 3:
        raise ConnInfoError("short reply")
    rssi, tx, tx_max = body[10], body[11], body[12]
    return {"rssi": _signed(rssi), "tx_power": _signed(tx), "max_tx_power": _signed(tx_max)}


def _fail(err: int, what: str) -> OSError:
    if err in (errno.EPERM, errno.EACCES):
        return PermissionError(err, f"{what}: {os.strerror(err)}")
    return ConnInfoError(err, f"{what}: {os.strerror(err)}")


def _open_control_socket() -> socket.socket:
    # Python's socket module cannot bind an HCI socket to a channel other
    # than RAW, so open and bind it with libc and wrap the descriptor.
    libc = ctypes.CDLL(None, use_errno=True)
    fd = libc.socket(AF_BLUETOOTH, socket.SOCK_RAW | socket.SOCK_CLOEXEC, BTPROTO_HCI)
    if fd < 0:
        raise _fail(ctypes.get_errno(), "socket(AF_BLUETOOTH)")
    addr = struct.pack("<HHH", AF_BLUETOOTH, HCI_DEV_NONE, HCI_CHANNEL_CONTROL)
    if libc.bind(fd, ctypes.c_char_p(addr), len(addr)) < 0:
        err = ctypes.get_errno()
        os.close(fd)
        raise _fail(err, "bind(HCI_CHANNEL_CONTROL)")
    # Pass the family: without it Python calls getsockname() to find it,
    # which a management (control channel) socket rejects with EBADFD.
    return socket.socket(AF_BLUETOOTH, socket.SOCK_RAW, BTPROTO_HCI, fileno=fd)


def get_conn_info(adapter_path: str, address: str, timeout: float = 2.0) -> dict:
    """Blocking query; run it in an executor.  Raises ConnInfoError/ValueError."""
    index = hci_index(adapter_path)
    request = build_request(index, address)
    with _open_control_socket() as sock:
        sock.send(request)
        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ConnInfoError("no reply from the management interface")
            ready, _, _ = select.select([sock], [], [], remaining)
            if not ready:
                continue
            reply = parse_reply(sock.recv(512), index)
            if reply is not None:
                return reply
