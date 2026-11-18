// Only the local companion includes this adapter. USB access belongs to the native process.
(() => {
  const launch = new URLSearchParams(location.hash.slice(1)).get("desktop");
  if (launch) {
    sessionStorage.setItem("motorcontrol-key", launch);
    history.replaceState(null, "", location.pathname + location.search);
  }
  const token = sessionStorage.getItem("motorcontrol-key") || "";
  const sessions = new Set();
  const serial = new EventTarget();

  async function call(operation, data = {}, keepalive = false) {
    const response = await fetch("/api/" + operation, {
      method: "POST", keepalive,
      headers: {"Content-Type": "application/json", "X-Motorcontrol": token},
      body: JSON.stringify(data)
    });
    if (response.status === 403) throw Error("Open Motorcontrol Desktop again to start a session.");
    const body = await response.json();
    if (!response.ok) throw Error(body.error || "Desktop connection failed.");
    return body.result;
  }

  async function choose() {
    const devices = await call("ports");
    if (!devices.length) throw Error("No USB serial controllers found. Check the DATA cable and try again.");
    const dialog = document.createElement("dialog");
    dialog.innerHTML = '<form method="dialog"><h2>Choose a USB controller</h2><label>Controller <select></select></label><p><button value="cancel">Cancel</button> <button value="ok">Select</button></p></form>';
    const select = dialog.querySelector("select");
    for (const device of devices) select.add(new Option(device.label + " · " + device.path, device.path));
    document.body.append(dialog);
    const result = new Promise(resolve => dialog.addEventListener("close", resolve, {once: true}));
    dialog.showModal();
    await result;
    dialog.remove();
    if (dialog.returnValue !== "ok") throw new DOMException("No board selected.", "NotFoundError");
    return select.value;
  }

  class NativePort {
    constructor(path) { this.path = path; }
    async open({baudRate}) {
      if (baudRate !== 115200) throw Error("This dashboard requires 115200 baud.");
      const key = await call("open", {path: this.path});
      this.key = key;
      sessions.add(key);
      let reading = true;
      this.readable = new ReadableStream({
        pull: async controller => {
          try {
            while (reading) {
              const bytes = await call("read", {key});
              if (bytes && reading) {
                controller.enqueue(Uint8Array.from(atob(bytes), c => c.charCodeAt(0)));
                return;
              }
            }
          } catch (error) {
            if (!reading) return;
            controller.error(error);
            const event = new Event("disconnect");
            event.port = this;
            serial.dispatchEvent(event);
          }
        },
        cancel: () => { reading = false; }
      });
      this.writable = new WritableStream({
        write: bytes => call("write", {key, bytes: btoa(String.fromCharCode(...bytes))})
      });
    }
    async setSignals({dataTerminalReady, requestToSend}) {
      // The host establishes these signals when it opens the device.
      if (!dataTerminalReady || requestToSend) throw Error("Unsupported serial signals.");
    }
    async close() {
      if (!this.key) return;
      const key = this.key;
      this.key = this.readable = this.writable = null;
      sessions.delete(key);
      await call("close", {key});
    }
  }
  serial.requestPort = async () => new NativePort(await choose());
  Object.defineProperty(navigator, "serial", {value: serial});
  addEventListener("pagehide", () => {
    for (const key of sessions) void call("close", {key}, true).catch(() => {});
  });
  setInterval(() => void call("ping").catch(() => {}), 30000);

  function firmwareControls() {
    const block = document.createElement("section");
    block.innerHTML = '<h2>Update a NEMA17 controller</h2><p>Stop motion and disconnect all dashboards. Unplug PWR. Leave only this controller connected by DATA through verification.</p><button id="selectNativeBoard">Identify controller</button><p role="status" aria-live="polite"></p><button id="writeNativeBoard" hidden>Install firmware</button>';
    document.getElementById("desktop-download")?.remove();
    document.querySelector("main h1").after(block);
    const select = block.querySelector("#selectNativeBoard");
    const write = block.querySelector("#writeNativeBoard");
    const status = block.querySelector('[role="status"]');
    let path, expected;
    select.onclick = async () => {
      write.hidden = true;
      select.disabled = true;
      try {
        path = await choose();
        status.textContent = "Reading controller identity…";
        expected = await call("identify", {path});
        status.textContent = expected.board + " · " + expected.device + " · running " +
          expected.current + " → install " + expected.target + " (" + expected.build + ")";
        write.hidden = false;
      } catch (error) { status.textContent = error.message; }
      finally { select.disabled = false; }
    };
    write.onclick = async () => {
      if (!confirm("PWR disconnected and only this controller attached? Install firmware " + expected.target + " on " + expected.device + "?")) return;
      select.disabled = write.disabled = true;
      status.textContent = "Entering bootloader, copying firmware and checking the restarted controller. Keep DATA connected.";
      try { status.textContent = await call("flash", {path, expected}); }
      catch (error) { status.textContent = error.message; }
      finally { select.disabled = write.disabled = false; write.hidden = true; }
    };
  }

  addEventListener("DOMContentLoaded", () => {
    if (location.pathname === "/firmware.html") firmwareControls();
    const bar = document.createElement("footer");
    bar.className = "native-footer";
    bar.innerHTML = '<img src="/_desktop/logo.png" alt="tscircuit" width="74"> <span>Motorcontrol Desktop · Native USB</span> <button type="button">Quit desktop</button>';
    bar.querySelector("button").onclick = async () => {
      try {
        await call("quit");
        bar.textContent = "Motorcontrol Desktop closed. You can close this tab.";
      } catch (error) { alert(error.message); }
    };
    const css = document.createElement("link");
    css.rel = "stylesheet"; css.href = "/_desktop/desktop.css";
    document.head.append(css);
    document.body.append(bar);
  });
})();
