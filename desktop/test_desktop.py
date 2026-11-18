import base64
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from urllib import error, request

import firmware
import motorcontrol


class Board:
    def __init__(self):
        self.profile = "rp2040_drv8825_pd"
        self.uid = "aabbddee12345678"
        self.version = "1.0.17"
        self.build = "old"
        self.device = SimpleNamespace(device="testUSB", vid=0x2e8a, serial_number=self.uid)
        self.commands = []
        self.lines = []
        self.boot = False
        self.bad_ack = False
        self.port = self.device.device

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def close(self):
        pass

    def reset_input_buffer(self):
        self.lines = []

    def write(self, data):
        msg = json.loads(data)
        cmd = msg["cmd"]
        self.commands.append(cmd)
        if cmd == "status":
            self.lines.append({"type": "telemetry", "firmware": "native-c-pio", "device_id": self.uid,
                               "board_id": self.profile, "firmware_version": self.version,
                               "firmware_build": self.build})
        if cmd == "bootloader":
            self.boot = True
        self.lines.append({"type": "ack", "ok": not self.bad_ack, "id": msg["id"]})
        return len(data)

    def read_until(self, *_, **__):
        return json.dumps(self.lines.pop(0)).encode() + b"\n" if self.lines else b""


@contextmanager
def simulated_kit(test, *, corrupt_readback=False):
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        board = Board()
        entry = firmware.MANIFEST[board.profile]

        def devices():
            written = root / "MOTOR.UF2"
            if board.boot and written.is_file():
                test.assertEqual(hashlib.sha256(written.read_bytes()).hexdigest(), entry["sha256"])
                board.boot = False
                board.version = entry["version"]
                board.build = "incorrect" if corrupt_readback else entry["build"]
            return [] if board.boot else [board.device]

        with patch.object(firmware, "open_port", return_value=board), \
             patch.object(firmware, "ports", side_effect=devices), \
             patch.object(firmware, "boot_drives", side_effect=lambda: [root] if board.boot else []):
            yield board


class UpdateTests(unittest.TestCase):
    def test_bundled_images(self):
        for board_id, entry in firmware.MANIFEST.items():
            buf = (firmware.IMAGES / entry["file"]).read_bytes()
            self.assertEqual(hashlib.sha256(buf).hexdigest(), entry["sha256"])
            payload = b"".join(buf[i+32:i+288] for i in range(0, len(buf), 512))
            for value in (board_id, entry["build"], entry["version"]):
                self.assertIn(value.encode() + b"\0", payload)

    def test_identify_stop_flash_and_verify(self):
        with simulated_kit(self) as board:
            expected = firmware.inspect_board(board.port)
            self.assertIn("Verified", firmware.flash(board.port, expected))
            self.assertEqual(board.commands, ["status", "status", "stop", "bootloader", "status"])

    def test_mismatched_readback_is_failure(self):
        with simulated_kit(self, corrupt_readback=True) as board:
            with self.assertRaisesRegex(ValueError, "expected identity and build"):
                firmware.flash(board.port, firmware.inspect_board(board.port))

    def test_refuse_unknown_profile_downgrade_or_replacement(self):
        with simulated_kit(self) as board:
            expected = firmware.inspect_board(board.port)
            board.profile = "other"
            with self.assertRaisesRegex(ValueError, "No matching"):
                firmware.flash(board.port, expected)
            board.profile = expected["board"]
            board.version = "9.0.0"
            with self.assertRaisesRegex(ValueError, "newer"):
                firmware.flash(board.port, expected)
            board.version = "1.0.17"
            board.uid = "replacement"
            with self.assertRaisesRegex(ValueError, "changed"):
                firmware.flash(board.port, expected)
            self.assertNotIn("bootloader", board.commands)

    def test_ambiguous_drive_and_negative_ack(self):
        with simulated_kit(self) as board:
            expected = firmware.inspect_board(board.port)
            with patch.object(firmware, "boot_drives", return_value=[Path(".")]):
                with self.assertRaisesRegex(ValueError, "existing RP2"):
                    firmware.flash(board.port, expected)
            with patch.object(firmware, "boot_drives", return_value=[Path("a"), Path("b")]):
                with self.assertRaisesRegex(ValueError, "Multiple RP2"):
                    firmware.single_drive(board.uid)
            board.bad_ack = True
            with self.assertRaisesRegex(ValueError, "rejected"):
                firmware.flash(board.port, expected)
            self.assertNotIn("bootloader", board.commands)


class LocalTransportTests(unittest.TestCase):
    def setUp(self):
        self.server = motorcontrol.make_server()
        self.url = "http://" + self.server.host
        self.worker = threading.Thread(target=self.server.serve_forever)
        self.worker.start()

    def tearDown(self):
        self.server.shutdown()
        self.worker.join()
        self.server.server_close()

    def call(self, op, data, **headers):
        headers = {"Origin": self.url, "X-Motorcontrol": self.server.token, **headers}
        req = request.Request(self.url + "/api/" + op, data=json.dumps(data).encode(), headers=headers)
        with request.urlopen(req) as response:
            return json.load(response)["result"]

    def test_all_dashboard_pages_and_serial_boundaries(self):
        for page in motorcontrol.WEB.glob("*.html"):
            html = request.urlopen(self.url + "/" + page.name).read()
            self.assertIn(b"/_desktop/bridge.js", html)
        for headers in ({"Origin": "https://example.com"}, {"X-Motorcontrol": "wrong"},
                        {"Host": "other.example"}):
            with self.assertRaises(error.HTTPError) as refused:
                self.call("ports", {}, **headers)
            self.assertEqual(refused.exception.code, 403)
        with simulated_kit(self) as board:
            key = self.call("open", {"path": board.port})
            with self.assertRaises(error.HTTPError):
                self.call("identify", {"path": board.port})
            with self.assertRaises(error.HTTPError):
                self.call("open", {"path": board.port})
            data = base64.b64encode(b'{"cmd":"status","id":42}\n').decode()
            self.call("write", {"key": key, "bytes": data})
            self.call("close", {"key": key})
            self.assertEqual(board.commands, ["status", "stop"])


if __name__ == "__main__":
    unittest.main()
