"""Extract the mechanical inputs from the v1.4.27 circuit and its tsci GLB.

    python extract-board.py board.circuit.json board.glb > board-v1.4.27.json

Bounds are [xmin, ymin, zmin, xmax, ymax, zmax] in mm, with z=0 at the PCB top.
"""

import hashlib
import json
import struct
import sys
from pathlib import Path


def glb_components(path, top_z):
    with path.open("rb") as f:
        magic, version, _, length, chunk = struct.unpack("<4sIII4s", f.read(20))
        assert (magic, version, chunk) == (b"glTF", 2, b"JSON")
        gltf = json.loads(f.read(length))
    components = {}
    for node in gltf["nodes"]:
        meta = node.get("extras", {}).get("tscircuit", {})
        if "pcb_component_id" not in meta:
            continue
        # tsci 0.0.3288 bakes rotation and scale into the mesh of each root node.
        assert not {"matrix", "rotation", "scale", "children"}.intersection(node)
        tx, ty, tz = node["translation"]
        primitives = gltf["meshes"][node["mesh"]]["primitives"]
        positions = [gltf["accessors"][p["attributes"]["POSITION"]] for p in primitives]
        lo = [min(p["min"][i] for p in positions) for i in range(3)]
        hi = [max(p["max"][i] for p in positions) for i in range(3)]
        # GLB [-x, z, y] -> circuit [x, y, z].
        components[meta["pcb_component_id"]] = [
            -hi[0] - tx,
            lo[2] + tz,
            lo[1] + ty - top_z,
            -lo[0] - tx,
            hi[2] + tz,
            hi[1] + ty - top_z,
        ]
    return components


def main(circuit_file, glb_file):
    circuit = json.loads(circuit_file.read_bytes())
    (board,) = (r for r in circuit if r["type"] == "pcb_board")
    meshes = glb_components(glb_file, board["thickness"] / 2)
    sources = {r["source_component_id"]: r for r in circuit if r["type"] == "source_component"}
    installed = {}
    names = {}
    for part in (r for r in circuit if r["type"] == "pcb_component"):
        source = sources.get(part.get("source_component_id"))
        if not source or part.get("do_not_place"):
            continue
        name, pid = source["name"], part["pcb_component_id"]
        names[pid] = name
        if pid in meshes:
            bounds = meshes[pid]
        elif name == "L_AVDD":
            # This 0603 ferrite has no mesh. Allow a 2.5 mm square, 1.5 mm high.
            x, y = part["center"]["x"], part["center"]["y"]
            bounds = [x - 1.25, y - 1.25, 0, x + 1.25, y + 1.25, 1.5]
        else:
            raise ValueError(f"No envelope for {name}")
        installed[name] = [round(v, 4) for v in bounds]
    holes = sorted(
        [r["x"], r["y"], r["hole_diameter"]]
        for r in circuit
        if r["type"] == "pcb_hole" and not r.get("pcb_component_id")
    )
    tails = [
        [names[r["pcb_component_id"]], round(r["x"], 4), round(r["y"], 4)]
        for r in circuit
        if r["type"] == "pcb_plated_hole" and r.get("pcb_component_id") in names
    ]
    result = {
        "release_id": "8cff026e-34ab-465d-a41c-977395c7cd01",
        "circuit_sha256": hashlib.sha256(circuit_file.read_bytes()).hexdigest(),
        "pcb_size_mm": [board["width"], board["height"], board["thickness"]],
        "rear_holes_mm": holes,
        "through_hole_pins_mm": tails,
        "bounds_from_pcb_top_mm": dict(sorted(installed.items())),
    }
    # Keep one component per line so a changed dimension is easy to review.
    print("{")
    for key, value in list(result.items())[:-1]:
        print(f'  "{key}": {json.dumps(value)},')
    print('  "bounds_from_pcb_top_mm": {')
    rows = [
        f"    {json.dumps(name)}: {json.dumps(bounds)}"
        for name, bounds in result["bounds_from_pcb_top_mm"].items()
    ]
    print(",\n".join(rows))
    print("  }\n}")


if __name__ == "__main__":
    main(*map(Path, sys.argv[1:]))
