"""Serve the bundled Motorcontrol dashboards with operating-system serial I/O."""
import base64
import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import secrets
import sys
import threading
import time
from urllib.parse import unquote, urlsplit
import webbrowser

import firmware

HERE = Path(__file__).resolve().parent
WEB = (HERE if getattr(sys, "frozen", False) else HERE.parent) / "dist"
WEB = WEB.resolve()
UI = (HERE / "ui").resolve()


class Desktop:
    def __init__(self):
        self.lock = threading.RLock()
        self.sessions = {}
        self.updating = False
        self.active = time.monotonic()

    def close(self, key):
        with self.lock:
            session = self.sessions.pop(key, None)
            if session:
                with session["write"]:
                    port = session["port"]
                    try:
                        firmware.command(port, "stop", 748)
                    except OSError:
                        pass
                    finally:
                        port.close()

    def handle(self, op, data):
        self.active = time.monotonic()
        if op == "ping":
            return True
        if op == "ports":
            return [{"path": p.device, "label": p.product or p.description}
                    for p in firmware.ports()]
        if op == "open":
            with self.lock:
                path = data["path"]
                if self.updating or any(s["port"].port == path for s in self.sessions.values()):
                    raise ValueError("This controller is in use. Disconnect its other dashboard.")
                port = firmware.open_port(path)
                try:
                    port.rts = False
                    port.dtr = True
                except Exception:
                    port.close()
                    raise
                key = secrets.token_urlsafe(20)
                self.sessions[key] = {"port": port, "read": threading.Lock(),
                                      "write": threading.Lock(), "seen": self.active}
                return key
        if op in ("identify", "flash"):
            with self.lock:
                if self.sessions or self.updating:
                    raise ValueError("Disconnect every dashboard before updating.")
                self.updating = True
            try:
                if op == "identify":
                    return firmware.inspect_board(data["path"])
                return firmware.flash(data["path"], data["expected"])
            finally:
                with self.lock:
                    self.updating = False
                    self.active = time.monotonic()
        if op == "close":
            self.close(data["key"])
            return True
        if op not in ("read", "write"):
            raise ValueError("Unknown operation.")
        with self.lock:
            s = self.sessions.get(data["key"])
            if not s:
                raise ValueError("Controller disconnected.")
            s["seen"] = self.active
        port = s["port"]
        try:
            if op == "read":
                with s["read"]:
                    chunk = port.read(min(65536, port.in_waiting) or 1)
                    return base64.b64encode(chunk).decode("ascii")
            with s["write"]:
                return port.write(base64.b64decode(data["bytes"], validate=True))
        except OSError:
            self.close(data["key"])
            raise


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def reply(self, code, content, kind):
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "frame-ancestors 'none'; object-src 'none'; base-uri 'self'; script-src 'self' 'unsafe-inline'")
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self):
        if self.headers.get("Host") != self.server.host:
            return self.send_error(403)
        path = unquote(urlsplit(self.path).path)
        root = UI if path.startswith("/_desktop/") else WEB
        tail = path.removeprefix("/_desktop/") if root == UI else path.lstrip("/") or "index.html"
        file = (root / tail).resolve()
        if not file.is_relative_to(root) or not file.is_file():
            return self.send_error(404)
        content = file.read_bytes()
        if file.suffix == ".html":
            content = content.replace(b"<head>", b'<head><script src="/_desktop/bridge.js"></script>', 1)
        self.reply(200, content, mimetypes.guess_type(file.name)[0] or "application/octet-stream")

    def do_POST(self):
        if (self.headers.get("Host") != self.server.host or
                self.headers.get("Origin") != "http://" + self.server.host or
                not secrets.compare_digest(self.headers.get("X-Motorcontrol", ""), self.server.token)):
            return self.send_error(403)
        try:
            size = int(self.headers.get("Content-Length", 0))
            if not 0 < size <= 131072 or not self.path.startswith("/api/"):
                return self.send_error(400)
            data = json.loads(self.rfile.read(size))
            op = self.path.removeprefix("/api/")
            if op == "quit":
                with self.server.desktop.lock:
                    if self.server.desktop.updating:
                        raise ValueError("Wait for the firmware update to finish.")
                    self.server.stopping.set()
                result = True
            else:
                result = self.server.desktop.handle(op, data)
            body = {"result": result}
            code = 200
        except (ValueError, KeyError, OSError, TypeError) as error:
            body, code = {"error": str(error)}, 400
        self.reply(code, json.dumps(body).encode(), "application/json")


def make_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.host = f"127.0.0.1:{server.server_port}"
    server.token = secrets.token_urlsafe(32)
    server.desktop = Desktop()
    server.stopping = threading.Event()
    return server


def main():
    server = make_server()
    url = f"http://{server.host}/#desktop={server.token}"
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        if "--smoke-test" in sys.argv:
            from urllib.request import urlopen
            assert b"/_desktop/bridge.js" in urlopen(url.split("#")[0]).read()
            assert firmware.MANIFEST
            return
        webbrowser.open(url)
        while not server.stopping.wait(1):
            state = server.desktop
            with state.lock:
                now = time.monotonic()
                for key, session in list(state.sessions.items()):
                    if now - session["seen"] > 8:
                        state.close(key)
                if not state.updating and now - state.active > 180:
                    break
    finally:
        server.shutdown()
        for key in list(server.desktop.sessions):
            server.desktop.close(key)
        server.server_close()


if __name__ == "__main__":
    main()
