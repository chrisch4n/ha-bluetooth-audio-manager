"""Link quality without a scan: mgmt Get Connection Information."""

import struct
import unittest

from bt_audio_manager.bluez import conn_info as ci

ADDR = "41:42:00:00:10:59"


def reply(index, status=0, rssi=0, tx=4, tx_max=10, event=ci.MGMT_EV_CMD_COMPLETE, opcode=ci.MGMT_OP_GET_CONN_INFO):
    body = struct.pack("<HB", opcode, status)
    if event == ci.MGMT_EV_CMD_COMPLETE:
        body += bytes(reversed([0x41, 0x42, 0, 0, 0x10, 0x59])) + bytes([0])
        body += bytes([rssi & 0xFF, tx & 0xFF, tx_max & 0xFF])
    return struct.pack("<HHH", event, index, len(body)) + body


class PacketTest(unittest.TestCase):

    def test_hci_index(self):
        self.assertEqual(ci.hci_index("/org/bluez/hci2"), 2)
        self.assertEqual(ci.hci_index("hci10"), 10)
        with self.assertRaises(ValueError):
            ci.hci_index("/org/bluez")

    def test_request_layout(self):
        pkt = ci.build_request(2, ADDR)
        self.assertEqual(struct.unpack_from("<HHH", pkt), (0x0031, 2, 7))
        self.assertEqual(pkt[6:12], bytes([0x59, 0x10, 0, 0, 0x42, 0x41]))  # little endian
        self.assertEqual(pkt[12], ci.BDADDR_BREDR)

    def test_reply_values_signed_and_invalid(self):
        self.assertEqual(ci.parse_reply(reply(2, rssi=-6, tx=10, tx_max=10), 2),
                         {"rssi": -6, "tx_power": 10, "max_tx_power": 10})
        self.assertEqual(ci.parse_reply(reply(2, rssi=127, tx=127, tx_max=127), 2),
                         {"rssi": None, "tx_power": None, "max_tx_power": None})

    def test_other_events_are_skipped(self):
        self.assertIsNone(ci.parse_reply(reply(1), 2))  # other adapter
        self.assertIsNone(ci.parse_reply(reply(2, opcode=0x0004), 2))  # other command
        self.assertIsNone(ci.parse_reply(struct.pack("<HHH", 0x000B, 2, 0), 2))  # device connected event
        self.assertIsNone(ci.parse_reply(b"\x01", 2))

    def test_errors(self):
        with self.assertRaises(ci.ConnInfoError):
            ci.parse_reply(reply(2, status=0x02), 2)  # not connected
        with self.assertRaises(PermissionError):
            ci.parse_reply(reply(2, status=0x14, event=ci.MGMT_EV_CMD_STATUS), 2)


if __name__ == "__main__":
    unittest.main()
