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


def face_crosses_xy(triangle, x, y):
    edges = zip(triangle, triangle[1:] + triangle[:1])
    cross = [(a[0] - x) * (b[1] - y) - (a[1] - y) * (b[0] - x) for a, b in edges]
    return abs(sum(cross)) > 1e-9 and (min(cross) >= 0 or max(cross) <= 0)


class EnclosureAssetsTest(unittest.TestCase):
    def test_nema14_wago_downloads_and_pin_relief(self):
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
                footprint = part.get("footprint_mm", catalog["footprint_mm"])
                for axis, expected in enumerate([*footprint, part["height_mm"]]):
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
                    self.assertEqual(footprint, [38.25, 38.25])
                    roof = max(v[2] for v in vertices)
                    for x, y in ((0, 0), (-19.65, 4.5), (0.6, 19.65)):
                        self.assertTrue(any(face_crosses_xy(t, x, y) for t in triangles
                                            if all(abs(v[2] - roof) < 1e-4 for v in t)))
                    for x in (-13, 13):
                        for y in (-13, 13):
                            for radius in (1.6, 3.05):
                                sample_x = x + math.copysign(radius, x)
                                heights = [v[2] for t in triangles
                                           if face_crosses_xy(t, sample_x, y) for v in t]
                                self.assertAlmostEqual(max(heights), roof - 8.10, places=4)
                    for x in (-6.0, -2.0, 2.0, 6.0):
                        for y in (-15.0, -10.0, -5.2):
                            self.assertFalse(any(face_crosses_xy(t, x, y) for t in triangles
                                                 if min(v[2] for v in t) >= 13.92))
                if part["id"] == "bottom":
                    self.assertEqual(part["height_mm"], 5.8)
                    z_levels = {round(v[2], 4) for v in vertices}
                    self.assertEqual(z_levels, {-6.6, -4.3, -0.8})
                    holes = [(0, 0, 11.3)] + [
                        (x, y, 3.1) for x in (-13, 13) for y in (-13, 13)
                    ]
                    for cx, cy, radius in holes:
                        self.assertAlmostEqual(
                            min(math.hypot(x - cx, y - cy) for x, y, _ in vertices),
                            radius,
                            places=3,
                        )
                        self.assertFalse(any(face_crosses_xy(t, cx, cy) for t in triangles))

                    # The two WAGO pin positions outside the center bore need
                    # the recess above the flat motor-facing side.
                    for x in (-1.3, 5.7):
                        for dx in (-0.9, 0, 0.9):
                            for dy in (-0.9, 0, 0.9):
                                hit_levels = {
                                    round(v[2], 4) for t in triangles
                                    if face_crosses_xy(t, x + dx, -12.05 + dy) for v in t
                                }
                                if math.hypot(x + dx, -12.05 + dy) >= 11.3:
                                    self.assertIn(-4.3, hit_levels)
                                self.assertLessEqual(max(hit_levels, default=-6.6), -4.3)

    def test_nema17_flat_top_downloads_flat_face_and_led_holes(self):
        assets = ROOT / "dist/assets/nema17-flat-top-enclosure"
        catalog = json.loads((assets / "catalog.json").read_text())
        page = (ROOT / "dist/assets.html").read_text()
        links = Links(page).urls
        self.assertIn("NEMA17 flat-top controller enclosure", page)
        self.assertEqual(catalog["board_revision"], "1.0.58")
        self.assertEqual(catalog["footprint_mm"], [45.3, 45.32])
        self.assertEqual(catalog["mounting_pitch_mm"], 31)
        self.assertEqual({part["id"] for part in catalog["parts"]}, {"top", "bottom"})
        bolts = [(x, y) for x in (-15.5, 15.5) for y in (-15.5, 15.5)]
        leds = [(-18.0, 11.5), (-14.9, -7.9)]  # D_PWR, D_STATUS on PCB v1.0.58
        for part in catalog["parts"]:
            with self.subTest(part=part["id"]):
                for kind in ("stl", "step"):
                    name = part[kind]
                    self.assertIn(f"assets/nema17-flat-top-enclosure/{name}", links)
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
                for axis, expected in enumerate([*catalog["footprint_mm"], part["height_mm"]]):
                    size = max(v[axis] for v in vertices) - min(v[axis] for v in vertices)
                    self.assertAlmostEqual(size, expected, places=4)

                def levels(x, y):
                    return sorted({round(v[2], 3) for t in triangles
                                   if face_crosses_xy(t, x, y)
                                   and max(v[2] for v in t) - min(v[2] for v in t) < 1e-4
                                   for v in t})

                # Bolt bores run through both parts.
                for x, y in bolts:
                    self.assertFalse(any(face_crosses_xy(t, x, y) for t in triangles))
                if part["id"] == "top":
                    # Assembly coordinates: PCB top at 5.0, flat top at 12.3.
                    self.assertAlmostEqual(min(v[2] for v in vertices), 5.0, places=4)
                    # The roof is one 1.4 mm slab: flat outside, flat inside.
                    for x, y in ((0, 0), (10, 5), (-10, 5), (18, 0), (0, -9), (-18, 0), (0, 18)):
                        self.assertEqual(levels(x, y), [10.9, 12.3])
                    # Nothing stands above the top face.
                    self.assertAlmostEqual(max(v[2] for v in vertices), 12.3, places=4)
                    # A clear line of sight straight up from each LED...
                    for x, y in leds:
                        self.assertFalse(any(face_crosses_xy(t, x, y) for t in triangles))
                        # ...through a Ø1.5 mm hole, with roof all round it.
                        for angle in range(0, 360, 45):
                            dx, dy = math.cos(math.radians(angle)), math.sin(math.radians(angle))
                            self.assertEqual(levels(x + 0.6 * dx, y + 0.6 * dy), [])
                            self.assertEqual(levels(x + 0.9 * dx, y + 0.9 * dy)[-1], 12.3)
                    # Screw heads seat 3.7 mm below the top face.
                    for x, y in bolts:
                        self.assertEqual(levels(x + 2.5, y)[-1], 8.6)
                if part["id"] == "bottom":
                    self.assertAlmostEqual(min(v[2] for v in vertices), 0.0, places=4)
                    # Ø22.6 mm rotor opening, 1 mm insulating floor around it.
                    self.assertFalse(any(face_crosses_xy(t, 0, 0) for t in triangles))
                    self.assertAlmostEqual(
                        min(math.hypot(x, y) for x, y, _ in vertices), 11.3, places=2)
                    for x, y in ((0, 14), (14, 0), (0, -14), (-14, 0)):
                        self.assertEqual(levels(x, y), [0.0, 1.0])
                    # The PCB rests on the four bolt sleeves, 3.4 mm up.
                    for x, y in bolts:
                        self.assertEqual(levels(x - math.copysign(2.6, x), y), [0.0, 3.4])

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
