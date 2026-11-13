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

function addSpacer(frame, height) {
  const row = template.content.cloneNode(true);
  const part = `NEMA ${frame.nema} · ${height} mm`;
  const modelPath = `assets/nema${frame.nema}-backface-spacer-${height}mm.stl`;
  row.querySelector("h2").textContent = `${part} backface spacer`;
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
  panel.id = `preview-nema${frame.nema}-${height}mm`;
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
  const catalogs = await Promise.all([4, 10].map(async (height) => {
    const response = await fetch(`assets/backface-spacer-${height}mm.json`);
    if (!response.ok) throw new Error(`Asset list: HTTP ${response.status}`);
    return { height, frames: await response.json() };
  }));
  catalogs.forEach(({ height, frames }) => frames.forEach((frame) => addSpacer(frame, height)));
  catalogStatus.hidden = true;
} catch (error) {
  catalogStatus.textContent = "Could not load the asset list. Try reloading the page.";
  console.error(error);
}
