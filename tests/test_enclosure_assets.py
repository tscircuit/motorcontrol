"""Check that the public enclosure catalog serves complete, correctly sized CAD."""
from collections import Counter
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import struct
import unittest


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "dist/assets/nema17-enclosure"


class Links(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.urls = set()
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if name in ("src", "href") and value:
                self.urls.add(value)


class EnclosureAssetsTest(unittest.TestCase):
    def test_removed_wordmark_variant_and_card_images_are_not_published(self):
        page = (ROOT / "dist/assets.html").read_text()
        self.assertNotIn("enclosure-recessed", page)
        self.assertNotIn("<img", page.split("</header>", 1)[1])  # Catalog cards stay text-only.
        for filename in ("tscircuit-nema17-top-recessed-v4.stl",
                         "tscircuit-nema17-top-recessed-v4.step",
                         "recessed-preview.webp", "laser-preview.webp",
                         "sticker-preview.webp", "base-preview.webp"):
            self.assertFalse((ASSETS / filename).exists())
        self.assertTrue((ROOT / "mechanical/nema17-enclosure/build-cad.py").is_file())

    def test_tsx_page_keeps_source_only_material_out_of_dist(self):
        page = (ROOT / "dist/assets.html").read_text()
        self.assertIn("Generated from src/assets-page.tsx", page)
        self.assertTrue((ROOT / "src/assets-page.tsx").is_file())
        self.assertTrue((ROOT / "src/enclosure-catalog.tsx").is_file())
        for filename in ("fit-notes.txt", "bolt-clearance.json", "label-source-v6.json"):
            self.assertFalse((ASSETS / filename).exists())
            self.assertNotIn(f"assets/nema17-enclosure/{filename}", page)
        self.assertTrue((ROOT / "mechanical/nema17-enclosure/fit-notes.txt").is_file())

    def test_download_links_mesh_dimensions_and_integrity(self):
        catalog = json.loads((ASSETS / "catalog.json").read_text())
        links = Links((ROOT / "dist/assets.html").read_text()).urls
        self.assertEqual({p["id"] for p in catalog["parts"]},
                         {"plain", "sticker", "rounded-jst", "bottom"})
        for part in catalog["parts"]:
            with self.subTest(part=part["id"]):
                for kind in ("stl", "step"):
                    name = part[kind]
                    self.assertIn(f"assets/nema17-enclosure/{name}", links)
                    self.assertTrue((ASSETS / name).is_file())
                for kind in ("stl", "step"):
                    name = part[kind]
                    data = (ASSETS / name).read_bytes()
                    self.assertEqual(hashlib.sha256(data).hexdigest(),
                                     catalog["sha256"][name])
                data = (ASSETS / part["stl"]).read_bytes()
                count = struct.unpack_from("<I", data, 80)[0]
                self.assertGreater(count, 0)
                self.assertEqual(len(data), 84 + count * 50)
                vertices = []
                for index in range(count):
                    triangle = struct.unpack_from("<12fH", data, 84 + index * 50)
                    vertices.extend([triangle[3:6], triangle[6:9], triangle[9:12]])
                bounds = [max(v[i] for v in vertices) - min(v[i] for v in vertices)
                          for i in range(3)]
                footprint = part.get("footprint_mm", catalog["footprint_mm"])
                for actual, expected in zip(bounds, [*footprint, part["height_mm"]]):
                    self.assertAlmostEqual(actual, expected, places=4)
                self.assertTrue((ASSETS / part["step"]).read_bytes().startswith(b"ISO-10303-21;"))

    def test_rounded_jst_lid_has_a_revision_specific_preview(self):
        catalog = json.loads((ASSETS / "catalog.json").read_text())
        part = next(part for part in catalog["parts"] if part["id"] == "rounded-jst")
        self.assertEqual(part["board_revision"], "1.0.45")
        page = (ROOT / "dist/assets.html").read_text()
        self.assertIn('data-enclosure-preview="rounded-jst"', page)
        self.assertIn('id="enclosure-preview-rounded-jst"', page)
        self.assertIn("PCB v1.0.45 fit-test draft.", page)
        self.assertIn("48.5 × 42 × 15.2 mm", page)

    def test_rounded_jst_stl_is_watertight(self):
        catalog = json.loads((ASSETS / "catalog.json").read_text())
        part = next(part for part in catalog["parts"] if part["id"] == "rounded-jst")
        stl = (ASSETS / part["stl"]).read_bytes()
        edges = Counter()
        for (ax, ay, az, bx, by, bz, cx, cy, cz) in (
            struct.unpack_from("<9f", stl, offset + 12)
            for offset in range(84, len(stl), 50)
        ):
            vertices = [(ax, ay, az), (bx, by, bz), (cx, cy, cz)]
            self.assertEqual(len(set(vertices)), 3)
            edges.update(tuple(sorted((v, w))) for v, w in zip(vertices, vertices[1:] + vertices[:1]))
        self.assertTrue(edges)
        self.assertEqual(set(edges.values()), {2})

    def test_local_asset_links_and_label_provenance(self):
        links = Links((ROOT / "dist/assets.html").read_text()).urls
        for url in links:
            if url.startswith("assets/nema17-enclosure/"):
                self.assertTrue((ROOT / "dist" / url).is_file(), url)
        source = json.loads((ROOT / "mechanical/nema17-enclosure/label-source-v6.json").read_text())
        self.assertEqual(source["repository"], "tscircuit/product-packaging")
        self.assertEqual([r["text"] for r in source["layout"]["rows"]][:2],
                         ["NEMA17 USB-PD", "Stepper driver & controller"])
        self.assertEqual(hashlib.sha256((ASSETS / "tscircuit-nema17-sticker-v6.pdf").read_bytes()).hexdigest(),
                         source["sha256"]["label.pdf"])
