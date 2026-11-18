"""Install a bundled NEMA17 image over the controller's USB DATA port."""
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time

import serial
from serial.tools import list_ports

IMAGES = Path(__file__).resolve().parent / "images"
MANIFEST = json.loads((IMAGES / "manifest.json").read_text())


def ports():
    return [p for p in list_ports.comports() if p.vid is not None]


def open_port(path):
    if not any(p.device == path for p in ports()):
        raise ValueError("USB serial device is no longer available.")
    return serial.Serial(path, 115200, timeout=0.10, write_timeout=1,
                         exclusive=True if os.name == "posix" else None)


def command(port, name, command_id):
    port.write((json.dumps({"id": command_id, "cmd": name}) + "\n").encode())


def exchange(port, name, command_id):
    port.reset_input_buffer()
    command(port, name, command_id)
    status = None
    acknowledged = False
    deadline = time.monotonic() + 4
    while time.monotonic() < deadline:
        line = port.read_until(b"\n", size=65536)
        try:
            msg = json.loads(line)
        except (ValueError, UnicodeError):
            continue
        if not isinstance(msg, dict):
            continue
        if msg.get("type") == "telemetry" and msg.get("device_id"):
            status = msg
        if msg.get("type") == "ack" and msg.get("id") == command_id:
            if not msg.get("ok"):
                raise ValueError(msg.get("error") or "Command rejected.")
            acknowledged = True
        if acknowledged and (name != "status" or status):
            return status
    raise ValueError(f"The controller did not acknowledge {name}. Check DATA and close other dashboards.")


def check_board(status):
    entry = MANIFEST.get(status.get("board_id"))
    if not entry or status.get("firmware") != "native-c-pio" or not status.get("device_id"):
        raise ValueError("No matching firmware is bundled for this controller.")
    version = status.get("firmware_version", "")
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("Could not identify the running firmware version.")
    if tuple(map(int, version.split("."))) > tuple(map(int, entry["version"].split("."))):
        raise ValueError("This board runs newer firmware than the bundled image.")
    return entry


def inspect_board(path):
    with open_port(path) as port:
        status = exchange(port, "status", 741)
    entry = check_board(status)
    return {"board": status["board_id"], "device": status["device_id"],
            "current": status["firmware_version"], "target": entry["version"],
            "build": entry["build"]}


def boot_drives():
    if os.name == "nt":
        import ctypes
        roots = [Path(f"{letter}:/") for letter in "DEFGHIJKLMNOPQRSTUVWXYZABC"
                 if ctypes.windll.kernel32.GetDriveTypeW(f"{letter}:\\") == 2]
    else:
        import getpass
        user = getpass.getuser()
        parents = [Path("/Volumes")] if sys.platform == "darwin" else [
            Path("/media", user), Path("/run/media", user), Path("/mnt")]
        roots = [p for parent in parents if parent.is_dir() for p in parent.iterdir()
                 if os.path.ismount(p)]
    found = []
    for root in roots:
        try:
            with (root / "INFO_UF2.TXT").open("rb") as info:
                lines = info.read(4096).splitlines()
            if b"Board-ID: RPI-RP2" in lines:
                found.append(root)
        except OSError:
            continue
    return found


def wait_for(find, timeout, error):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = find()
        if result:
            return result
        time.sleep(0.25)
    raise ValueError(error)


def single_drive(usb_id):
    found = boot_drives()
    if len(found) > 1:
        raise ValueError("Multiple RP2 drives appeared. No image was written.")
    if not found or any((p.serial_number or "").lower() == usb_id for p in ports()):
        return None
    return found[0]


def flash(path, expected):
    devices = ports()
    selected = next((p for p in devices if p.device == path), None)
    if not selected or sum(p.vid == 0x2e8a for p in devices) != 1 or selected.vid != 0x2e8a:
        raise ValueError("Leave only the selected RP2040 controller connected by DATA.")
    if boot_drives():
        raise ValueError("Disconnect existing RP2 boot drives before starting.")
    with open_port(path) as port:
        status = exchange(port, "status", 742)
        entry = check_board(status)
        if (status["device_id"], status["board_id"]) != (expected["device"], expected["board"]):
            raise ValueError("The controller changed. Identify it again.")
        usb_id = (selected.serial_number or "").lower()
        if not usb_id or usb_id != status["device_id"].lower():
            raise ValueError("USB serial number does not match the controller identity.")
        image = (IMAGES / entry["file"]).read_bytes()
        if hashlib.sha256(image).hexdigest() != entry["sha256"]:
            raise ValueError("The bundled firmware failed its integrity check.")
        exchange(port, "stop", 743)
        command(port, "bootloader", 744)
    root = wait_for(lambda: single_drive(usb_id), 25, "RPI-RP2 did not mount. Check DATA and the recovery instructions.")
    flush_error = None
    with (root / "MOTOR.UF2").open("xb", buffering=0) as dest:
        for start in range(0, len(image), 16384):
            chunk = image[start:start + 16384]
            if dest.write(chunk) != len(chunk):
                raise IOError("Incomplete UF2 transfer. Keep PWR disconnected.")

        try:
            os.fsync(dest.fileno())
        except OSError as error:
            # The ROM can eject as soon as the last block arrives. Readback decides success.
            flush_error = error

    def reconnect():
        for p in ports():
            if (p.serial_number or "").lower() != usb_id or p.vid != selected.vid:
                continue
            try:
                with open_port(p.device) as port:
                    return exchange(port, "status", 745)
            except (OSError, ValueError):
                pass
        return None

    detail = f" USB flush reported {flush_error}." if flush_error else ""
    result = wait_for(reconnect, 35, "Unable to verify the transfer." + detail +
                      " Reconnect DATA and check the running version before using PWR.")
    for key, value in {"device_id": status["device_id"], "board_id": status["board_id"],
                       "firmware_version": entry["version"], "firmware_build": entry["build"]}.items():
        if result.get(key) != value:
            raise ValueError("The restarted controller did not report the expected identity and build.")
    return f"Verified {entry['version']} · {entry['build']} on {status['device_id']}."
