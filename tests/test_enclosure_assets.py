"""Check that the public enclosure catalog serves complete, correctly sized CAD."""
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
    def test_download_links_mesh_dimensions_and_integrity(self):
        catalog = json.loads((ASSETS / "catalog.json").read_text())
        links = Links((ROOT / "dist/assets.html").read_text()).urls
        self.assertEqual({p["id"] for p in catalog["parts"]},
                         {"plain", "sticker", "recessed", "bottom"})
        for part in catalog["parts"]:
            with self.subTest(part=part["id"]):
                for kind in ("stl", "step", "preview"):
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
        source = json.loads((ASSETS / "label-source-v6.json").read_text())
        self.assertEqual(source["repository"], "tscircuit/product-packaging")
        self.assertEqual([r["text"] for r in source["layout"]["rows"]][:2],
                         ["NEMA17 USB-PD", "Stepper driver & controller"])
        self.assertEqual(hashlib.sha256((ASSETS / "tscircuit-nema17-sticker-v6.pdf").read_bytes()).hexdigest(),
                         source["sha256"]["label.pdf"])
