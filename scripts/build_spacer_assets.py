"""Regenerate the printable spacer STLs using OpenSCAD."""
import json
from pathlib import Path
import subprocess

ASSETS = Path(__file__).resolve().parents[1] / "dist" / "assets"
PART = "backface-spacer-4mm"
DIMENSIONS = (
    "face", "pitch", "screw_clearance", "rotor_clearance", "sleeve_od", "corner_clip"
)


def main():
    frames = json.loads((ASSETS / f"{PART}.json").read_text())
    for frame in frames:
        destination = ASSETS / f"nema{frame['nema']}-{PART}.stl"
        overrides = [arg for name in DIMENSIONS for arg in ("-D", f"{name}={frame[name]}")]
        subprocess.run(
            ["openscad", "--export-format", "binstl", "-o", str(destination),
             *overrides, str(ASSETS / f"{PART}.scad")],
            check=True,
        )


if __name__ == "__main__":
    main()
