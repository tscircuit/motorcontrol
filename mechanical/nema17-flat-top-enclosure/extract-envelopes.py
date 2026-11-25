"""Per-component bounding boxes from the board's GLB export.

    tsci export board.circuit.json -f glb          # writes board.glb
    python extract-envelopes.py board.glb > component-envelopes-v1.0.58.json

GLB node names are `<component name>_<6 hex>`. Output is in circuit
coordinates (mm): PCB origin at the board centre, PCB mid-plane at z = 0, so
the top copper side is z = +0.8 on a 1.6 mm board.
"""
import json
import re
import sys

import numpy as np
import trimesh

scene = trimesh.load(sys.argv[1])
boxes = {}
for node in scene.graph.nodes_geometry:
    transform, geometry = scene.graph[node]
    match = re.fullmatch(r"(.+)_[0-9a-f]{6}", node)
    if not match or match[1] == "Box0":      # Box0 is the bare board
        continue
    points = trimesh.transform_points(scene.geometry[geometry].vertices, transform)
    # glTF is Y-up and mirrored against circuit X.
    points = np.column_stack([-points[:, 0], points[:, 2], points[:, 1]])
    lo, hi = boxes.get(match[1], (points.min(0), points.max(0)))
    boxes[match[1]] = (np.minimum(lo, points.min(0)), np.maximum(hi, points.max(0)))

print(json.dumps([{"name": name, "min": np.round(lo, 4).tolist(), "max": np.round(hi, 4).tolist()}
                  for name, (lo, hi) in boxes.items()], indent=1))
