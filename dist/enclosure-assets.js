"use strict";
let active;
function closeEnclosurePreview() {
    if (!active)
        return;
    active.controller.abort();
    active.button.textContent = "Preview";
    active.button.setAttribute("aria-expanded", "false");
    active.panel.hidden = true;
    active = undefined;
}
for (const button of document.querySelectorAll("[data-enclosure-preview]")) {
    const row = button.closest("li");
    const panel = document.getElementById(button.getAttribute("aria-controls") ?? "");
    const host = panel?.querySelector("[data-enclosure-model]");
    const status = panel?.querySelector("[data-enclosure-status]");
    const image = panel?.querySelector("img");
    const download = row?.querySelector('a[href$=".stl"]');
    if (!panel || !host || !status || !image || !download)
        continue;
    button.addEventListener("click", async () => {
        const wasOpen = active?.button === button;
        closeEnclosurePreview();
        if (wasOpen)
            return;
        const controller = new AbortController();
        active = { button, panel, controller };
        button.textContent = "Close";
        button.setAttribute("aria-expanded", "true");
        panel.hidden = false;
        host.hidden = false;
        image.hidden = false;
        status.textContent = "Loading 3D model…";
        try {
            const moduleUrl = "./stl-preview.js";
            const { showStl } = await import(moduleUrl);
            await showStl(host, download.href, row?.querySelector("h3")?.textContent ?? "enclosure", controller.signal);
            if (controller.signal.aborted)
                return;
            image.hidden = true;
            status.textContent = "Drag to rotate · Scroll or pinch to zoom";
        }
        catch (error) {
            if (controller.signal.aborted)
                return;
            host.hidden = true;
            status.textContent = "3D preview unavailable. The reference image and STEP/STL downloads are still available.";
            console.error(error);
        }
    });
}
window.addEventListener("pagehide", closeEnclosurePreview);
