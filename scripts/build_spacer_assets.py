"""Regenerate the printable spacer STLs using OpenSCAD."""
import json
from pathlib import Path
import subprocess

ASSETS = Path(__file__).resolve().parents[1] / "dist" / "assets"
HEIGHTS = (4, 10)
SOURCE = ASSETS / "backface-spacer-4mm.scad"
DIMENSIONS = (
    "face", "pitch", "screw_clearance", "rotor_clearance", "sleeve_od", "corner_clip"
)


def main():
    for height in HEIGHTS:
        part = f"backface-spacer-{height}mm"
        frames = json.loads((ASSETS / f"{part}.json").read_text())
        for frame in frames:
            destination = ASSETS / f"nema{frame['nema']}-{part}.stl"
            overrides = [arg for name in DIMENSIONS for arg in ("-D", f"{name}={frame[name]}")]
            subprocess.run(
                ["openscad", "--export-format", "binstl", "-o", str(destination),
                 "-D", f"total_height={height}", *overrides, str(SOURCE)],
                check=True,
            )


if __name__ == "__main__":
    main()
