#!/usr/bin/env python3
"""Link quality of the radiostream speakers, for a command_line sensor.

Angelegt 18.11.2026 von Claude. Runs inside Home Assistant Core, which -
unlike the Bluetooth Audio Manager add-on - lives in the host's network
namespace and may open Bluetooth sockets.  Asks the kernel (Bluetooth
management interface, "Get Connection Information") for each speaker's
connection on every adapter: no scan, no radio time, no effect on audio.

Argument: the JSON of input_text.radiostream_address_map, e.g.
  '{"87_5": "AA:BB:CC:DD:EE:FF", ...}'
Output (stdout, JSON): {"87_5": {"rssi": -2, "tx": 4, "tx_max": 10,
  "adapter": "AA:..."}, "97_0": null, ...}; null = not connected.

rssi on a classic (BR/EDR) link is NOT dBm: dB outside the controller's
golden receive range, 0 = inside (good), negative = weaker.  tx = the
adapter's current transmit power on the link in dBm; close to tx_max
points to a weak link.
"""

import ctypes
import json
import os
import select
import socket
import struct
import sys
import time

AF_BLUETOOTH = 31
BTPROTO_HCI = 1
HCI_CHANNEL_CONTROL = 3
INDEX_NONE = 0xFFFF
OP_READ_INDEX_LIST = 0x0003
OP_READ_INFO = 0x0004
OP_GET_CONN_INFO = 0x0031
EV_CMD_COMPLETE = 0x0001
EV_CMD_STATUS = 0x0002
INVALID = 127


def open_socket():
    libc = ctypes.CDLL(None, use_errno=True)
    fd = libc.socket(AF_BLUETOOTH, socket.SOCK_RAW | socket.SOCK_CLOEXEC, BTPROTO_HCI)
    if fd < 0:
        raise OSError(ctypes.get_errno(), "socket")
    addr = struct.pack("<HHH", AF_BLUETOOTH, INDEX_NONE, HCI_CHANNEL_CONTROL)
    if libc.bind(fd, ctypes.c_char_p(addr), len(addr)) < 0:
        err = ctypes.get_errno()
        os.close(fd)
        raise OSError(err, "bind")
    return socket.socket(fileno=fd)


def command(sock, opcode, index, params=b"", timeout=2.0):
    """Send a mgmt command; return (status, return parameters)."""
    sock.send(struct.pack("<HHH", opcode, index, len(params)) + params)
    deadline = time.monotonic() + timeout
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError(f"no reply to 0x{opcode:04x}")
        if not select.select([sock], [], [], remaining)[0]:
            continue
        pkt = sock.recv(1024)
        if len(pkt) < 9:
            continue
        event, ev_index, length = struct.unpack_from("<HHH", pkt)
        body = pkt[6:6 + length]
        if event not in (EV_CMD_COMPLETE, EV_CMD_STATUS) or ev_index != index:
            continue
        op, status = struct.unpack_from("<HB", body)
        if op == opcode:
            return status, body[3:]


def mac_from_le(raw):
    return ":".join(f"{b:02X}" for b in reversed(raw[:6]))


def signed(value):
    value = value - 256 if value > 127 else value
    return None if value == INVALID else value


def main():
    boxes = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
    result = {key: None for key in boxes}
    with open_socket() as sock:
        status, data = command(sock, OP_READ_INDEX_LIST, INDEX_NONE)
        if status != 0:
            raise OSError(f"index list: status {status}")
        count = struct.unpack_from("<H", data)[0]
        indexes = list(struct.unpack_from(f"<{count}H", data, 2))
        adapters = {}
        for index in indexes:
            status, data = command(sock, OP_READ_INFO, index)
            if status == 0:
                adapters[index] = mac_from_le(data)
        for key, address in boxes.items():
            bdaddr = bytes(int(p, 16) for p in reversed(address.split(":")))
            for index in indexes:
                status, data = command(sock, OP_GET_CONN_INFO, index, bdaddr + b"\x00")
                if status != 0 or len(data) < 10:
                    continue  # 0x02 = not connected on this adapter
                result[key] = {
                    "rssi": signed(data[7]),
                    "tx": signed(data[8]),
                    "tx_max": signed(data[9]),
                    "adapter": adapters.get(index, f"hci{index}"),
                }
                break
    print(json.dumps(result))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # the sensor shows the error instead of a value
        print(json.dumps({"error": f"{type(e).__name__}: {e}"}))
