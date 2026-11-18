"""Build and check a draft lid for the pinned v1.0.45 PCB. Dimensions are mm."""

import argparse
import json
import math
from pathlib import Path

import cadquery as cq
from OCP.BRepBndLib import BRepBndLib
from OCP.Bnd import Bnd_Box


HERE = Path(__file__).resolve().parent
RELEASED_PARTS = HERE.parents[3] / "dist/assets/nema17-enclosure"
PCB_TOP = 5.0
TOP = 21.8
CEILING = TOP - 1.4
OPENING_Y = (-10.3, 1.0)
SCREW_SEAT = 8.6
WIRE_DIAMETER = 1.5
BEND_RADIUS = 4.5
WIRE_X = 17.73
WIRE_LAUNCH_Z = 14.0
WIRE_Y = (-7.65, -5.65, -3.65, -1.65)
MATED_BOTTOM = PCB_TOP + 5.65
MATED_TOP = PCB_TOP + 8.03
TOL = 1e-6
MOUNT_CENTERS = [(x, y) for x in (-15.5, 15.5) for y in (-15.5, 15.5)]


def box(xmin, ymin, zmin, xmax, ymax, zmax):
    return cq.Solid.makeBox(xmax - xmin, ymax - ymin, zmax - zmin,
                            cq.Vector(xmin, ymin, zmin))


def outline(half_width, clip, height):
    w, c = half_width, clip
    return cq.Wire.makePolygon(
        [(x, y, height) for x, y in
         [(-w + c, -w), (w - c, -w), (w, -w + c), (w, w - c),
          (w - c, w), (-w + c, w), (-w, w - c), (-w, -w + c)]],
        close=True,
    )


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


def build_lid(stock):
    # Keep the released USB cutouts, lower post reliefs and mating geometry.
    overlap_z, splice_z = 9.80, 9.96
    lower = stock.intersect(box(-22, -22, PCB_TOP - 0.1, 22, 22, splice_z))
    outer = cq.Solid.makeLoft([
        outline(21, 2.3, overlap_z), outline(21, 2.3, TOP - 0.8),
        outline(20.2, 1.84, TOP),
    ], ruled=True)
    inside = cq.Solid.makeLoft([
        outline(19.8, 1.6, overlap_z - 0.1), outline(19.8, 1.6, CEILING),
    ], ruled=True)
    upper = outer.cut(inside)
    for x, y in MOUNT_CENTERS:
        post = cq.Solid.makeCylinder(4.2, TOP - overlap_z,
                                     cq.Vector(x, y, overlap_z))
        upper = upper.fuse(outer.intersect(post))
    # Carry the existing side relief up to the new roof at its existing width.
    side_relief = box(18.5, OPENING_Y[0], overlap_z - 0.1, 23, OPENING_Y[1], CEILING)
    return cut_for_bolts(lower.fuse(upper.cut(side_relief))).clean()


def wire_envelope(y):
    start = cq.Vector(WIRE_X, y, MATED_TOP)
    rise = cq.Vector(WIRE_X, y, WIRE_LAUNCH_Z)
    angle = math.pi / 4
    midpoint = cq.Vector(WIRE_X + BEND_RADIUS * (1 - math.cos(angle)), y,
                         WIRE_LAUNCH_Z + BEND_RADIUS * math.sin(angle))
    turn_end = cq.Vector(WIRE_X + BEND_RADIUS, y, WIRE_LAUNCH_Z + BEND_RADIUS)
    exit_end = cq.Vector(27, y, turn_end.z)
    path = cq.Wire.assembleEdges([
        cq.Edge.makeLine(start, rise), cq.Edge.makeThreePointArc(rise, midpoint, turn_end),
        cq.Edge.makeLine(turn_end, exit_end),
    ])
    profile = cq.Wire.makeCircle(WIRE_DIAMETER / 2, start, cq.Vector(0, 0, 1))
    return cq.Solid.sweep(profile, [], path)


def check_lid(lid, stock):
    assert lid.isValid() and len(lid.Solids()) == 1, "lid must be one valid solid"
    extent = bounds(lid)
    for actual, expected in zip(extent, (-21, -21, PCB_TOP, 21, 21, TOP)):
        assert abs(actual - expected) < TOL, extent

    # The two sidewalls at the USB edge and the complete lower mating slice
    # must retain the released shape, including openings and counterbores.
    lower_region = box(-22, -22, PCB_TOP - 0.1, 22, 22, 9.69)
    old_lower = stock.intersect(lower_region)
    new_lower = lid.intersect(lower_region)
    lower_delta = old_lower.cut(new_lower).Volume() + new_lower.cut(old_lower).Volume()
    assert lower_delta < TOL, ("released lower geometry changed", lower_delta)
    for x, y in MOUNT_CENTERS:
        shank = cq.Solid.makeCylinder(1.799, TOP + 0.1, cq.Vector(x, y, PCB_TOP))
        well = cq.Solid.makeCylinder(3.299, TOP - SCREW_SEAT, cq.Vector(x, y, SCREW_SEAT))
        assert lid.intersect(shank).Volume() < TOL, (x, y, "shank obstruction")
        assert lid.intersect(well).Volume() < TOL, (x, y, "head/tool obstruction")
        seat = cq.Solid.makeCylinder(2.7, 0.2, cq.Vector(x, y, SCREW_SEAT - 0.2))
        seat_ring = seat.cut(cq.Solid.makeCylinder(1.8, 0.2, cq.Vector(x, y, SCREW_SEAT - 0.2)))
        assert abs(lid.intersect(seat_ring).Volume() - seat_ring.Volume()) < TOL, (x, y, "screw seat")

    plug = box(15.78, -8.75, MATED_BOTTOM, 19.38, -0.55, MATED_TOP)
    assert plug.distance(lid) >= 1.0 and plug.intersect(lid).Volume() < TOL
    gaps = []
    for y in WIRE_Y:
        wire = wire_envelope(y)
        assert wire.isValid() and len(wire.Solids()) == 1
        assert wire.intersect(lid).Volume() < TOL
        gaps.append(wire.distance(lid))
    conservative_headroom = CEILING - (WIRE_LAUNCH_Z + BEND_RADIUS + WIRE_DIAMETER / 2)
    assert min(gaps) >= conservative_headroom - TOL, gaps
    return gaps, plug.distance(lid), conservative_headroom


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
        "case_footprint_mm": [42, 42],
        "case_height_mm": TOP,
        "roof_thickness_mm": 1.4,
        "side_relief_width_mm": round(OPENING_Y[1] - OPENING_Y[0], 3),
        "side_relief_top_above_pcb_mm": round(CEILING - PCB_TOP, 3),
        "assumed_wire_outer_diameter_mm": WIRE_DIAMETER,
        "assumed_minimum_bend_radius_mm": BEND_RADIUS,
        "assumed_mated_connector_height_mm": round(MATED_TOP - PCB_TOP, 3),
        "conservative_roof_headroom_mm": round(headroom, 3),
        "modeled_wire_to_lid_distances_mm": [round(gap, 3) for gap in gaps],
        "modeled_mated_plug_to_lid_distance_mm": round(plug_gap, 3),
        "mated_plug_vertical_gap_above_other_components_mm": round(MATED_BOTTOM - highest_neighbor, 3),
        "component_bounds_overlaps": intersections,
    }
    args.output.mkdir(parents=True, exist_ok=True)
    stem = args.output / "top-v1.0.45-jst-draft"
    cq.exporters.export(lid, f"{stem}.step")
    cq.exporters.export(lid, f"{stem}.stl", tolerance=0.045, angularTolerance=0.15)
    exported = cq.importers.importStep(f"{stem}.step").val()
    check_lid(exported, stock)
    (args.output / "fit-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
