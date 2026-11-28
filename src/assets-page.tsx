import { SiteHeader } from "./site-header";
import {
  enclosureCatalog,
  nema14EnclosureCatalog,
  nema17FlatTopEnclosureCatalog,
  nema23EnclosureCatalog,
} from "./enclosure-catalog";
import type { EnclosurePart } from "./enclosure-catalog";

const linkClass = "text-blue-700 underline";
const assetRoot = "assets/nema17-enclosure/";

function EnclosurePartRow({
  part,
  root,
  idPrefix,
  dimensions,
}: {
  part: EnclosurePart;
  root: string;
  idPrefix: string;
  dimensions: string;
}) {
  const previewId = `${idPrefix}-preview-${part.id}`;
  return (
    <li className="px-4 py-3" id={`${idPrefix}-${part.id}`}>
      <h3 className="text-sm font-semibold">{part.title}</h3>
      <p className="mt-1 text-xs text-slate-600">
        {dimensions} {part.notes}
      </p>
      <div className="mt-2 flex flex-wrap items-center gap-3 text-sm">
        <a className={linkClass} href={root + part.stl} download>
          STL · {part.title}
        </a>
        <a className={linkClass} href={root + part.step} download>
          STEP · {part.title}
        </a>
        <button
          type="button"
          className="rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm hover:bg-slate-50"
          data-enclosure-preview={part.id}
          aria-expanded="false"
          aria-controls={previewId}
        >
          Preview
        </button>
      </div>
      <div id={previewId} className="mt-3" hidden>
        <div
          data-enclosure-model=""
          className="relative h-64 overflow-hidden rounded-md border border-slate-200 bg-white sm:h-80"
        />
        <p
          data-enclosure-status=""
          role="status"
          className="mt-2 text-xs text-slate-600"
        >
          Drag the model to rotate; scroll to zoom.
        </p>
      </div>
    </li>
  );
}

function EnclosureSection() {
  return (
    <section aria-labelledby="enclosure-heading" className="mt-5">
      <h2
        id="enclosure-heading"
        className="text-2xl font-semibold tracking-tight"
      >
        NEMA17 controller enclosure
      </h2>
      <p className="mt-1 text-sm text-slate-600">
        42 × 42 mm · 31 mm bolt pitch · PCB v{enclosureCatalog.board_revision}{" "}
        fit-test draft. Confirm the actual board and motor before printing a
        batch.
      </p>
      <p className="mt-3 text-sm text-slate-600">
        For a flat outer face, choose <strong>Plain top cover</strong>. Print
        its exterior face down; inspect the slicer before adding supports. The
        bottom housing replaces the old spacer.
      </p>
      <ul
        aria-label="NEMA17 enclosure parts"
        className="mt-5 divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white"
      >
        {enclosureCatalog.parts.map((part) => (
          <EnclosurePartRow
            key={part.id}
            part={part}
            root={assetRoot}
            idPrefix="enclosure"
            dimensions={`42 × 42 × ${part.height_mm} mm · Ø3.6 mm bores.`}
          />
        ))}
      </ul>
      <p className="mt-3 flex flex-wrap gap-3 text-sm">
        <a
          className={linkClass}
          href={assetRoot + "tscircuit-nema17-sticker-v6.pdf"}
          download
        >
          Label PDF
        </a>
        <a
          className={linkClass}
          href={assetRoot + "tscircuit-nema17-sticker-sheet-v6.pdf"}
          download
        >
          60-up label sheet PDF
        </a>
        <a
          className={linkClass}
          href="https://github.com/tscircuit/motorcontrol/tree/main/mechanical/nema17-enclosure"
        >
          Native CadQuery source
        </a>
        <a
          className={linkClass}
          href="https://tscircuit-nema17-enclosure.anassoftwaredev.chatgpt.site/"
        >
          Full assembly viewer
        </a>
      </p>
      <p className="mt-3 text-xs text-slate-600">
        These STEP/STL files are unchanged v4 CAD exports. Their native CadQuery
        model remains the source for geometry.
      </p>
    </section>
  );
}

function Nema17FlatTopEnclosureSection() {
  const catalog = nema17FlatTopEnclosureCatalog;
  const footprint = catalog.footprint_mm.join(" × ");
  return (
    <section aria-labelledby="nema17-flat-top-enclosure-heading" className="mt-5">
      <h2
        id="nema17-flat-top-enclosure-heading"
        className="text-2xl font-semibold tracking-tight"
      >
        NEMA17 flat-top controller enclosure
      </h2>
      <p className="mt-1 text-sm text-slate-600">
        {footprint} mm · {catalog.mounting_pitch_mm} mm bolt pitch · PCB v
        {catalog.board_revision} fit-test draft
      </p>
      <p className="mt-3 text-sm text-slate-600">
        The top is a single flat face, so the motor can stand on it and a label
        can go on it. The two parts meet at the PCB surface and wall in the
        board on every side, which makes them 1.5 mm wider than the PCB all
        round. Print the cover with its top face on the bed.
      </p>
      <ul
        aria-label="NEMA17 flat-top enclosure parts"
        className="mt-5 divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white"
      >
        {catalog.parts.map((part) => (
          <EnclosurePartRow
            key={part.id}
            part={part}
            root="assets/nema17-flat-top-enclosure/"
            idPrefix="nema17-flat-top-enclosure"
            dimensions={`${footprint} × ${part.height_mm} mm.`}
          />
        ))}
      </ul>
      <p className="mt-3 text-sm text-slate-600">
        Both LEDs show through notches in the blank wall opposite the JST
        connector, and through holes in the top. The status LED&apos;s top hole
        is inside the area a centered 38.1 × 19.05 mm label covers; its side
        notch stays open.{" "}
        <a
          className={linkClass}
          href="https://github.com/tscircuit/motorcontrol/tree/main/mechanical/nema17-flat-top-enclosure"
        >
          Native CadQuery source and fit notes
        </a>
      </p>
    </section>
  );
}

function Nema14EnclosureSection() {
  const catalog = nema14EnclosureCatalog;
  const footprint = catalog.footprint_mm.join(" × ");
  return (
    <section aria-labelledby="nema14-enclosure-heading" className="mt-5">
      <h2 id="nema14-enclosure-heading" className="text-2xl font-semibold tracking-tight">
        NEMA14 WAGO controller enclosure
      </h2>
      <p className="mt-1 text-sm text-slate-600">
        {footprint} mm motor footprint · {catalog.mounting_pitch_mm} mm bolt pitch · Fit-test draft
      </p>
      <ul
        aria-label="NEMA14 WAGO enclosure parts"
        className="mt-5 divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white"
      >
        {catalog.parts.map((part) => (
          <EnclosurePartRow
            key={part.id}
            part={part}
            root="assets/nema14-enclosure/"
            idPrefix="nema14-enclosure"
            dimensions={`${part.footprint_mm?.join(" × ") ?? footprint} × ${part.height_mm} mm.`}
          />
        ))}
      </ul>
      <p className="mt-3 text-sm text-slate-600">
        The USB-C collars project 3.05 mm past two motor edges. They fit the
        modeled 12.7 × 7.8 mm plug bodies. The rear bay gives access to the
        WAGO push tabs with the cover installed.{" "}
        <a
          className={linkClass}
          href="https://github.com/tscircuit/motorcontrol/tree/main/mechanical/nema14-enclosure"
        >
          Native FreeCAD model and fit notes
        </a>
      </p>
    </section>
  );
}

function Nema23EnclosureSection() {
  const catalog = nema23EnclosureCatalog;
  const footprint = catalog.footprint_mm.join(" × ");
  return (
    <section aria-labelledby="nema23-enclosure-heading" className="mt-5">
      <h2 id="nema23-enclosure-heading" className="text-2xl font-semibold tracking-tight">
        NEMA23 WAGO-style controller enclosure
      </h2>
      <p className="mt-1 text-sm text-slate-600">
        For the PCB marked REV N / PROTOTYPE, v{catalog.board_revision}. Assembled size{" "}
        {footprint} × 26.9 mm. Rear bolt pattern {catalog.mounting_pitch_mm.join(" × ")} mm.
        Physical fit is unverified.
      </p>
      <p className="mt-3 text-sm">
        <a className={linkClass} href={"assets/nema23-enclosure/" + catalog.print_plate} download>
          Download both parts arranged for printing (3MF)
        </a>
      </p>
      <ul
        aria-label="NEMA23 enclosure parts"
        className="mt-5 divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white"
      >
        {catalog.parts.map((part) => (
          <EnclosurePartRow
            key={part.id}
            part={part}
            root="assets/nema23-enclosure/"
            idPrefix="nema23-enclosure"
            dimensions={`${footprint} × ${part.height_mm} mm.`}
          />
        ))}
      </ul>
      <p className="mt-3 flex flex-wrap gap-3 text-sm">
        <a className={linkClass} href="https://tscircuit.com/imrishabh18/nema-23-stepper-controller?version=1.4.27#pcb">
          PCB layout
        </a>
        <a className={linkClass} href="https://github.com/tscircuit/motorcontrol/tree/6ee5f9df746d5c56fac4f6b3d0d1657d905501a8/mechanical/nema23-enclosure">
          Assembly drawing, fasteners and CAD source
        </a>
      </p>
    </section>
  );
}

function SpacerSection() {
  return (
    <>
      <h2 className="mt-5 text-2xl font-semibold tracking-tight">
        Backface spacers
      </h2>
      <p className="mt-1 text-sm text-slate-600">
        4 mm backface spacers for NEMA 8–34 and a 10 mm option for NEMA 17. Each
        has a 1 mm base and four sleeves with 45° corner cuts; total height
        includes the base.
      </p>
      <ul
        id="assets"
        aria-label="Printable models"
        className="mt-5 divide-y divide-slate-200 rounded-lg border border-slate-200 bg-white"
      />
      <p
        id="catalog-status"
        role="status"
        className="mt-3 text-sm text-slate-600"
      >
        Loading assets…
      </p>
      <p className="mt-4 text-xs text-slate-600">
        Compare the hole pitch and clearances with your motor before printing.{" "}
        <a
          className={linkClass}
          href="assets/backface-spacer-4mm.scad"
          download
        >
          OpenSCAD source
        </a>
      </p>
    </>
  );
}

function SpacerTemplate() {
  return (
    <template id="asset-row">
      <li>
        <div className="flex flex-wrap items-center justify-between gap-x-4 gap-y-2 px-4 py-3">
          <div className="min-w-0">
            <h2 className="text-sm font-semibold" />
            <p
              data-dimensions=""
              className="mt-0.5 text-xs tabular-nums text-slate-600"
            />
          </div>
          <div className="flex shrink-0 items-center gap-3 text-sm">
            <a
              data-download=""
              className="rounded-md px-2 py-1.5 font-medium text-blue-700 hover:bg-blue-50"
              download
            >
              STL
            </a>
            <button
              type="button"
              aria-expanded="false"
              className="w-24 rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm font-medium hover:bg-slate-50"
            >
              Preview
            </button>
          </div>
        </div>
        <div
          data-panel=""
          hidden
          className="border-t border-slate-200 bg-slate-50 p-3 sm:p-4"
        >
          <div
            data-model=""
            className="relative h-64 overflow-hidden rounded-md border border-slate-200 bg-white sm:h-80"
          >
            <p
              data-preview-status=""
              role="status"
              className="absolute inset-x-0 top-3 text-center text-sm text-slate-600"
            />
          </div>
          <div className="mt-2 flex flex-wrap justify-between gap-1 text-xs text-slate-600">
            <p>Drag to rotate · Scroll or pinch to zoom</p>
            <a data-drawing="" className={linkClass}>
              Motor drawing
            </a>
          </div>
        </div>
      </li>
    </template>
  );
}

export function AssetsPage() {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="color-scheme" content="light" />
        <title>Assets · Motorcontrol</title>
        <link rel="stylesheet" href="assets/viewer.css" />
        <link rel="stylesheet" href="site-nav.css" />
        <script defer src="site-nav.js" />
        <script type="importmap">
          {JSON.stringify({
            imports: { three: "./vendor/three/three.module.min.js" },
          })}
        </script>
      </head>
      <body className="min-h-screen bg-slate-50 text-slate-900 antialiased">
        <SiteHeader page="assets.html" />
        <main className="mx-auto max-w-4xl px-4 py-8 sm:px-6">
          <h1 className="text-2xl font-semibold tracking-tight">Assets</h1>
          <p className="mt-1 text-sm text-slate-600">
            Download printable motor spacers and controller enclosures.
          </p>
          <EnclosureSection />
          <Nema17FlatTopEnclosureSection />
          <Nema14EnclosureSection />
          <Nema23EnclosureSection />
          <SpacerSection />
        </main>
        <SpacerTemplate />
        <script type="module" src="assets-viewer.js" />
        <script type="module" src="enclosure-assets.js" />
      </body>
    </html>
  );
}
