import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFile, writeFile } from "node:fs/promises";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { AssetsPage } from "../src/assets-page";
import { enclosureCatalog } from "../src/enclosure-catalog";

async function main(): Promise<void> {
  for (const part of enclosureCatalog.parts) {
    for (const filename of [part.stl, part.step]) {
      const bytes = await readFile(`dist/assets/nema17-enclosure/${filename}`);
      assert.equal(
        createHash("sha256").update(bytes).digest("hex"),
        enclosureCatalog.sha256[filename],
        filename,
      );
    }
  }
  await writeFile(
    "dist/assets.html",
    "<!doctype html>\n<!-- Generated from src/assets-page.tsx; edit the TSX source. -->\n" +
      renderToStaticMarkup(createElement(AssetsPage)) +
      "\n",
  );
  await writeFile(
    "dist/assets/nema17-enclosure/catalog.json",
    JSON.stringify(enclosureCatalog, null, 2) + "\n",
  );
}

void main().catch((error: unknown) => {
  console.error(error);
  process.exitCode = 1;
});
