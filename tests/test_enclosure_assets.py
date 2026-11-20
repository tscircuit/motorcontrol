"""Check that the public enclosure catalog serves complete, correctly sized CAD."""
import hashlib
from html.parser import HTMLParser
import json
import math
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
    def test_nema14_wago_downloads_and_flat_spacer(self):
        assets = ROOT / "dist/assets/nema14-enclosure"
        catalog = json.loads((assets / "catalog.json").read_text())
        page = (ROOT / "dist/assets.html").read_text()
        links = Links(page).urls
        self.assertIn("NEMA14 WAGO controller enclosure", page)
        self.assertEqual(catalog["footprint_mm"], [35.2, 35.2])
        self.assertEqual(catalog["mounting_pitch_mm"], 26)
        self.assertEqual({part["id"] for part in catalog["parts"]}, {"top", "bottom"})
        for part in catalog["parts"]:
            with self.subTest(part=part["id"]):
                for kind in ("stl", "step"):
                    name = part[kind]
                    self.assertIn(f"assets/nema14-enclosure/{name}", links)
                    data = (assets / name).read_bytes()
                    self.assertEqual(hashlib.sha256(data).hexdigest(),
                                     catalog["sha256"][name])
                self.assertTrue((assets / part["step"]).read_bytes().startswith(b"ISO-10303-21;"))
                mesh = (assets / part["stl"]).read_bytes()
                count = struct.unpack_from("<I", mesh, 80)[0]
                self.assertGreater(count, 0)
                self.assertEqual(len(mesh), 84 + count * 50)
                triangles = [
                    [record[3:6], record[6:9], record[9:12]]
                    for record in struct.iter_unpack("<12fH", mesh[84:])
                ]
                vertices = [vertex for triangle in triangles for vertex in triangle]
                for axis, expected in enumerate([35.2, 35.2, part["height_mm"]]):
                    size = max(v[axis] for v in vertices) - min(v[axis] for v in vertices)
                    self.assertAlmostEqual(size, expected, places=4)
                corners = {}
                for x, y, z in vertices:
                    key = (round(x, 3), round(y, 3))
                    corners[key] = max(corners.get(key, z), z)
                for x in (-17.6, 17.6):
                    for y in (-17.6, 17.6):
                        self.assertIn((x, y), corners)
                        if part["id"] == "top":
                            self.assertAlmostEqual(corners[x, y], 17.48 if y < 0 else 10.35,
                                                   places=4)
                if part["id"] == "bottom":
                    self.assertEqual(part["height_mm"], 3.3)
                    self.assertEqual(len({round(v[2], 4) for v in vertices}), 2)
                    holes = [(0, 0, 11.3)] + [
                        (x, y, 3.1) for x in (-13, 13) for y in (-13, 13)
                    ]
                    for cx, cy, radius in holes:
                        self.assertAlmostEqual(
                            min(math.hypot(x - cx, y - cy) for x, y, _ in vertices),
                            radius,
                            places=3,
                        )
                        for triangle in triangles:
                            # A projected face covering the axis would block this hole.
                            cross = [
                                (a[0] - cx) * (b[1] - cy) - (a[1] - cy) * (b[0] - cx)
                                for a, b in zip(triangle, triangle[1:] + triangle[:1])
                            ]
                            self.assertFalse(abs(sum(cross)) > 1e-9
                                             and (min(cross) >= 0 or max(cross) <= 0))

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
                         {"plain", "sticker", "bottom"})
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
                for actual, expected in zip(bounds, [42, 42, part["height_mm"]]):
                    self.assertAlmostEqual(actual, expected, places=4)
                self.assertTrue((ASSETS / part["step"]).read_bytes().startswith(b"ISO-10303-21;"))

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
