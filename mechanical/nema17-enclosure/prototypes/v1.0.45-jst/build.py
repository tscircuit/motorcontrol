"""Build and check a draft lid for the pinned v1.0.45 PCB. Dimensions are mm."""

import argparse
import json
import math
import struct
from pathlib import Path

import cadquery as cq
from OCP.BRepBndLib import BRepBndLib
from OCP.Bnd import Bnd_Box


HERE = Path(__file__).resolve().parent
RELEASED_PARTS = HERE.parents[3] / "dist/assets/nema17-enclosure"
PCB_TOP = 5.0
TOP = 20.2
CEILING = TOP - 1.4
OPENING_Y = (-9.55, 0.25)
CORNER_RADIUS = 4.0
ROOF_EDGE_RADIUS = 0.8
BOTTOM_EDGE_RADIUS = 0.25
NOTCH_EDGE_RADIUS = 0.25
HOOD_X = (19.0, 26.0)
HOOD_Y = (-10.95, 1.65)
HOOD_INNER_END = 24.8
SCREW_SEAT = 8.6
WIRE_DIAMETER = 1.6
BEND_RADIUS = 3.0
WIRE_X = 17.25
WIRE_LAUNCH_Z = 14.0
WIRE_TURN_DOWN_X = WIRE_X + BEND_RADIUS + 0.1
WIRE_EXIT_Z = 3.4
WIRE_Y = (-7.65, -5.65, -3.65, -1.65)
MATED_BOTTOM = PCB_TOP + 5.65
MATED_TOP = PCB_TOP + 8.03
TOL = 1e-6
MOUNT_CENTERS = [(x, y) for x in (-15.5, 15.5) for y in (-15.5, 15.5)]


def box(xmin, ymin, zmin, xmax, ymax, zmax):
    return cq.Solid.makeBox(xmax - xmin, ymax - ymin, zmax - zmin,
                            cq.Vector(xmin, ymin, zmin))


def rounded_prism(width, radius, bottom, top):
    return (cq.Workplane("XY", origin=(0, 0, bottom))
            .rect(width, width).extrude(top - bottom).edges("|Z").fillet(radius))


def bounds(shape):
    result = Bnd_Box()
    BRepBndLib.AddOptimal_s(shape.wrapped, result, False, False)
    return result.Get()


def cut_for_bolts(lid):
    for x, y in MOUNT_CENTERS:
        shank = cq.Solid.makeCylinder(1.8, TOP + 0.2, cq.Vector(x, y, 0))
        well = cq.Solid.makeCylinder(3.3, TOP - SCREW_SEAT + 0.1,
                                     cq.Vector(x, y, SCREW_SEAT))
        entry = cq.Solid.makeCone(3.3, 3.5, 0.2, cq.Vector(x, y, TOP - 0.2))
        lid = lid.cut(shank, well, entry)
    return lid


def round_notch(lid):
    edges = []
    for edge in lid.Edges():
        xmin, ymin, zmin, xmax, ymax, zmax = bounds(edge)
        if abs(xmin - 21) > TOL or abs(xmax - 21) > TOL:
            continue
        lip = abs(zmin - CEILING) < TOL and abs(zmax - CEILING) < TOL
        jamb = any(abs(ymin - y) < TOL and abs(ymax - y) < TOL for y in OPENING_Y)
        if lip and ymin >= OPENING_Y[0] - TOL and ymax <= OPENING_Y[1] + TOL:
            edges.append(edge)
        elif jamb and zmax <= CEILING + TOL:
            edges.append(edge)
    assert len(edges) == 3, "the exterior notch needs two jambs and a top lip"
    return lid.fillet(NOTCH_EDGE_RADIUS, edges).clean()


def build_wire_hood():
    x0, x1 = HOOD_X
    y0, y1 = HOOD_Y
    shell = (cq.Workplane("XY", origin=((x0 + x1) / 2, (y0 + y1) / 2, PCB_TOP))
             .rect(x1 - x0, y1 - y0).extrude(TOP - PCB_TOP)
             .edges("|Z").fillet(1.6).edges(">Z").fillet(0.65)
             .edges("<Z").fillet(BOTTOM_EDGE_RADIUS).val())
    # The extension joins the lid along the roof. Keep its cheek walls and
    # end wall outside the PCB outline and leave the underside open.
    board_space = box(x0 - 0.1, y0 - 0.1, PCB_TOP - 0.1, 21, y1 + 0.1, CEILING)
    wire_space = box(x0 - 0.1, OPENING_Y[0], PCB_TOP - 0.1,
                     HOOD_INNER_END, OPENING_Y[1], CEILING)
    return shell.cut(board_space, wire_space)


def build_lid(stock):
    # Keep the original USB-C cuts and lower post reliefs. The lid rounds
    # into the 42 mm base outline, with the wire hood overhanging one side.
    overlap_z, splice_z = 9.80, 9.96
    outer = (rounded_prism(42, CORNER_RADIUS, PCB_TOP, TOP)
             .edges(">Z").fillet(ROOF_EDGE_RADIUS)
             .edges("<Z").fillet(BOTTOM_EDGE_RADIUS).val())
    lower = stock.intersect(box(-22, -22, PCB_TOP - 0.1, 22, 22, splice_z))
    upper = outer.intersect(box(-22, -22, overlap_z, 22, 22, TOP + 0.1))
    cavity = rounded_prism(39.6, CORNER_RADIUS - 1.2, overlap_z - 0.1, CEILING).val()
    upper = upper.cut(cavity, box(19.2, -10.45, overlap_z - 0.1, 20.35, 1.15, 11.35))
    for x, y in MOUNT_CENTERS:
        post = cq.Solid.makeCylinder(4.2, TOP - overlap_z, cq.Vector(x, y, overlap_z))
        upper = upper.fuse(outer.intersect(post))

    # Fill the two narrow jambs along the edges of the old, wider outlet.
    # The centre remains open to the PCB so a pre-crimped cable can lie in
    # place as the lid is lowered.
    jambs = [
        box(20.35, -10.42, PCB_TOP, 21, OPENING_Y[0], 11.4),
        box(20.35, OPENING_Y[1], PCB_TOP, 21, 1.12, 11.4),
    ]
    notch = box(18.5, OPENING_Y[0], PCB_TOP - 0.1, 23, OPENING_Y[1], CEILING)
    lid = lower.fuse(upper, *jambs).intersect(outer).cut(notch).clean()
    return cut_for_bolts(round_notch(lid).fuse(build_wire_hood())).clean()


def wire_envelope(y):
    start = cq.Vector(WIRE_X, y, MATED_TOP)
    rise = cq.Vector(WIRE_X, y, WIRE_LAUNCH_Z)
    angle = math.pi / 4
    midpoint = cq.Vector(WIRE_X + BEND_RADIUS * (1 - math.cos(angle)), y,
                         WIRE_LAUNCH_Z + BEND_RADIUS * math.sin(angle))
    turn_end = cq.Vector(WIRE_X + BEND_RADIUS, y, WIRE_LAUNCH_Z + BEND_RADIUS)
    down_start = cq.Vector(WIRE_TURN_DOWN_X, y, turn_end.z)
    down_mid = cq.Vector(WIRE_TURN_DOWN_X + BEND_RADIUS * math.sin(angle), y,
                         turn_end.z - BEND_RADIUS * (1 - math.cos(angle)))
    down_end = cq.Vector(WIRE_TURN_DOWN_X + BEND_RADIUS, y, WIRE_LAUNCH_Z)
    exit_end = cq.Vector(down_end.x, y, WIRE_EXIT_Z)
    path = cq.Wire.assembleEdges([
        cq.Edge.makeLine(start, rise), cq.Edge.makeThreePointArc(rise, midpoint, turn_end),
        cq.Edge.makeLine(turn_end, down_start), cq.Edge.makeThreePointArc(down_start, down_mid, down_end),
        cq.Edge.makeLine(down_end, exit_end),
    ])
    profile = cq.Wire.makeCircle(WIRE_DIAMETER / 2, start, cq.Vector(0, 0, 1))
    return cq.Solid.sweep(profile, [], path)


def check_lid(lid, stock):
    assert lid.isValid() and len(lid.Solids()) == 1, "lid must be one valid solid"
    extent = bounds(lid)
    for actual, expected in zip(extent, (-21, -21, PCB_TOP, HOOD_X[1], 21, TOP)):
        assert abs(actual - expected) < TOL, extent
    # Inspect the hood beyond the base outline so the lid itself cannot
    # satisfy the flush-height check.
    hood_tip = lid.intersect(box(22.5, HOOD_Y[0] - .1, PCB_TOP - .1,
                                HOOD_X[1] + .1, HOOD_Y[1] + .1, TOP + .1))
    hood_bounds = bounds(hood_tip)
    assert abs(hood_bounds[2] - PCB_TOP) < TOL and abs(hood_bounds[5] - TOP) < TOL

    # Check the socket openings above the new bottom edge round.
    usb_region = box(-13, 19.42, PCB_TOP + BOTTOM_EDGE_RADIUS, 13, 22, 9.55)
    original_usb, new_usb = stock.intersect(usb_region), lid.intersect(usb_region)
    assert original_usb.cut(new_usb).Volume() + new_usb.cut(original_usb).Volume() < TOL
    # The wire and mated plug are bounded by one clear vertical corridor.
    # The roof moves away from them as the lid is lifted.
    wire_outer_x = WIRE_TURN_DOWN_X + BEND_RADIUS + WIRE_DIAMETER / 2
    corridor = box(15.77, -8.76, WIRE_EXIT_Z, wire_outer_x + 0.01, -0.54, CEILING)
    assert lid.intersect(corridor).Volume() < TOL
    # Confirm that the end wall shields the full wire run across the bend
    # height, while the open underside remains in the assembly corridor.
    shield = box(HOOD_INNER_END + 0.3, OPENING_Y[0] + 0.2, WIRE_LAUNCH_Z,
                 HOOD_X[1] - 0.25, OPENING_Y[1] - 0.2, WIRE_LAUNCH_Z + BEND_RADIUS)
    assert abs(lid.intersect(shield).Volume() - shield.Volume()) < TOL
    for x, y in MOUNT_CENTERS:
        shank = cq.Solid.makeCylinder(1.799, TOP + 0.1, cq.Vector(x, y, PCB_TOP))
        well = cq.Solid.makeCylinder(3.299, TOP - SCREW_SEAT, cq.Vector(x, y, SCREW_SEAT))
        assert lid.intersect(shank).Volume() < TOL, (x, y, "shank obstruction")
        assert lid.intersect(well).Volume() < TOL, (x, y, "head/tool obstruction")
        seat = cq.Solid.makeCylinder(2.7, 0.2, cq.Vector(x, y, SCREW_SEAT - 0.2))
        seat_ring = seat.cut(cq.Solid.makeCylinder(1.8, 0.2, cq.Vector(x, y, SCREW_SEAT - 0.2)))
        assert abs(lid.intersect(seat_ring).Volume() - seat_ring.Volume()) < TOL, (x, y, "screw seat")

    plug = box(15.78, -8.75, MATED_BOTTOM, 19.38, -0.55, MATED_TOP)
    plug_gap = plug.distance(lid)
    assert plug_gap >= 0.9 and plug.intersect(lid).Volume() < TOL
    gaps = []
    for y in WIRE_Y:
        wire = wire_envelope(y)
        assert wire.isValid() and len(wire.Solids()) == 1
        assert wire.intersect(lid).Volume() < TOL
        gaps.append(wire.distance(lid))
    conservative_headroom = CEILING - (WIRE_LAUNCH_Z + BEND_RADIUS + WIRE_DIAMETER / 2)
    end_gap = HOOD_INNER_END - wire_outer_x
    assert min(gaps) >= min(conservative_headroom, end_gap) - TOL, gaps
    return gaps, plug_gap, conservative_headroom


def find_component_intersections(lid, base, model):
    intersections = []
    cases = [("lid", lid, PCB_TOP, TOP), ("base", base, 0, 3.4)]
    for name, xmin, ymin, zmin, xmax, ymax, zmax in model["component_bounds"]:
        if min(xmax - xmin, ymax - ymin, zmax - zmin) <= TOL:
            continue
        part = box(xmin, ymin, zmin, xmax, ymax, zmax)
        for case_name, case, lower, upper in cases:
            if zmax <= lower or zmin >= upper:
                continue
            overlap = case.intersect(part).Volume()
            if overlap > TOL:
                intersections.append({"part": name, "case": case_name,
                                      "aabb_overlap_mm3": round(overlap, 6)})
    return intersections


def export_stl(lid, path):
    cq.exporters.export(lid, str(path), tolerance=0.045, angularTolerance=0.15)
    data = path.read_bytes()
    count, = struct.unpack_from("<I", data, 80)
    assert len(data) == 84 + 50 * count
    faces = []
    for index in range(count):
        offset = 84 + 50 * index
        coordinates = struct.unpack_from("<9f", data, offset + 12)
        vertices = {coordinates[i:i+3] for i in (0, 3, 6)}
        # Meshing a fillet junction can emit a collapsed, zero-area facet.
        if len(vertices) == 3:
            faces.append(data[offset:offset+50])
    if len(faces) != count:
        path.write_bytes(data[:80] + struct.pack("<I", len(faces)) + b"".join(faces))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    model = json.loads((HERE / "component-envelopes.json").read_text())
    stock = cq.importers.importStep(str(RELEASED_PARTS / "tscircuit-nema17-top-laser-v4.step")).val()
    base = cq.importers.importStep(str(RELEASED_PARTS / "tscircuit-nema17-bottom-v4.step")).val()
    lid = build_lid(stock)
    gaps, plug_gap, headroom = check_lid(lid, stock)
    highest_neighbor = max(row[-1] for row in model["component_bounds"] if row[0] != "J1")
    assert highest_neighbor < MATED_BOTTOM, "Plug envelope and adjacent components overlap in Z"
    intersections = find_component_intersections(lid, base, model)
    assert not intersections, ("component bounds overlap", intersections)
    report = {
        "status": "Draft; physical fit and motor mounting pending",
        "board_version": model["board_version"],
        "base_footprint_mm": [42, 42],
        "lid_footprint_mm": [HOOD_X[1] + 21, 42],
        "case_height_mm": TOP,
        "hood_projection_mm": round(HOOD_X[1] - 21, 3),
        "hood_outer_width_mm": round(HOOD_Y[1] - HOOD_Y[0], 3),
        "hood_height_mm": round(TOP - PCB_TOP, 3),
        "hood_outlet_direction": "downward through open underside",
        "roof_thickness_mm": 1.4,
        "outer_corner_radius_mm": CORNER_RADIUS,
        "roof_edge_radius_mm": ROOF_EDGE_RADIUS,
        "bottom_edge_radius_mm": BOTTOM_EDGE_RADIUS,
        "notch_edge_radius_mm": NOTCH_EDGE_RADIUS,
        "vertical_assembly_corridor_clear": True,
        "side_relief_width_mm": round(OPENING_Y[1] - OPENING_Y[0], 3),
        "side_relief_top_above_pcb_mm": round(CEILING - PCB_TOP, 3),
        "assumed_wire_outer_diameter_mm": WIRE_DIAMETER,
        "assumed_minimum_bend_radius_mm": BEND_RADIUS,
        "assumed_wire_launch_x_mm": WIRE_X,
        "assumed_mated_connector_height_mm": round(MATED_TOP - PCB_TOP, 3),
        "conservative_roof_headroom_mm": round(headroom, 3),
        "modeled_wire_to_lid_distances_mm": [round(gap, 3) for gap in gaps],
        "modeled_mated_plug_to_lid_distance_mm": round(plug_gap, 3),
        "mated_plug_vertical_gap_above_other_components_mm": round(MATED_BOTTOM - highest_neighbor, 3),
        "component_bounds_overlaps": intersections,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    stem = args.output / "tscircuit-nema17-top-jst-v1.0.45-draft"
    cq.exporters.export(lid, f"{stem}.step")
    export_stl(lid, stem.parent / (stem.name + ".stl"))
    exported = cq.importers.importStep(f"{stem}.step").val()
    check_lid(exported, stock)
    (args.output / "fit-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
