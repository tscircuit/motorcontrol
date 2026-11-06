const catalogStatus = document.querySelector("#catalog-status");
const list = document.querySelector("#assets");
const template = document.querySelector("#asset-row");
let openPreview;

function closePreview() {
  if (!openPreview) return;
  const { button, panel, controller } = openPreview;
  controller.abort();
  button.textContent = "Preview";
  button.setAttribute("aria-expanded", "false");
  panel.hidden = true;
  openPreview = undefined;
}

function addSpacer(frame) {
  const row = template.content.cloneNode(true);
  const part = `NEMA ${frame.nema}`;
  const modelPath = `assets/nema${frame.nema}-backface-spacer-4mm.stl`;
  row.querySelector("h2").textContent = `${part} · backface-spacer-4mm`;
  row.querySelector("[data-dimensions]").textContent =
    `${frame.pitch} mm pitch · Ø${frame.screw_clearance} mm screw holes · Ø${frame.rotor_clearance} mm center`;

  const download = row.querySelector("[data-download]");
  download.href = modelPath;
  download.setAttribute("aria-label", `Download ${part} STL`);
  row.querySelector("[data-drawing]").href = frame.drawing;

  const button = row.querySelector("button");
  const panel = row.querySelector("[data-panel]");
  const host = row.querySelector("[data-model]");
  const status = row.querySelector("[data-preview-status]");
  panel.id = `preview-nema${frame.nema}`;
  button.setAttribute("aria-controls", panel.id);
  button.addEventListener("click", async () => {
    const wasOpen = openPreview?.button === button;
    closePreview();
    if (wasOpen) return;

    const controller = new AbortController();
    openPreview = { button, panel, controller };
    button.textContent = "Close";
    button.setAttribute("aria-expanded", "true");
    panel.hidden = false;
    status.textContent = "Loading 3D model…";

    try {
      const { showStl } = await import("./stl-preview.js");
      await showStl(host, modelPath, part, controller.signal);
      if (!controller.signal.aborted) status.textContent = "";
    } catch (error) {
      if (!controller.signal.aborted) {
        status.textContent = "3D preview unavailable. You can still download the STL.";
        console.error(error);
      }
    }
  });

  list.append(row);
}

try {
  const response = await fetch("assets/backface-spacer-4mm.json");
  if (!response.ok) throw new Error(`Asset list: HTTP ${response.status}`);
  const frames = await response.json();
  frames.forEach(addSpacer);
  catalogStatus.hidden = true;
} catch (error) {
  catalogStatus.textContent = "Could not load the asset list. Try reloading the page.";
  console.error(error);
}
