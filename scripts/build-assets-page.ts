import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFile, writeFile } from "node:fs/promises";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { SiteHeader } from "../src/site-header";
import { AssetsPage } from "../src/assets-page";
import { enclosureCatalogs } from "../src/enclosure-catalog";

async function main(): Promise<void> {
  for (const [directory, catalog] of Object.entries(enclosureCatalogs)) {
    const root = `dist/assets/${directory}`;
    const downloads = catalog.parts.flatMap((part) => [part.stl, part.step]);
    if (catalog.print_plate) downloads.push(catalog.print_plate);
    for (const filename of downloads) {
      const bytes = await readFile(`${root}/${filename}`);
      assert.equal(
        createHash("sha256").update(bytes).digest("hex"),
        catalog.sha256[filename],
        filename,
      );
    }
    await writeFile(`${root}/catalog.json`, JSON.stringify(catalog, null, 2) + "\n");
  }
  // The dashboards ship as static HTML. Stamp the same navigable header into
  // each one so the links also work before JavaScript loads.
  for (const page of ["index.html", "motor-bench.html", "single-motor.html", "gantry.html",
    "three-axis-gantry.html", "bldc.html", "firmware.html"]) {
    const path = `dist/${page}`;
    const html = await readFile(path, "utf8");
    const header = /<header class="siteHeader">[\s\S]*?<\/header>/;
    assert.match(html, header, `Missing site header in ${page}`);
    await writeFile(path, html.replace(header, renderToStaticMarkup(createElement(SiteHeader, { page }))));
  }
  await writeFile(
    "dist/assets.html",
    "<!doctype html>\n<!-- Generated from src/assets-page.tsx; edit the TSX source. -->\n" +
      renderToStaticMarkup(createElement(AssetsPage)) +
      "\n",
  );
}

void main().catch((error: unknown) => {
  console.error(error);
  process.exitCode = 1;
});
