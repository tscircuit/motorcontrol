"""Motor-mounted enclosure for imrishabh18/nema-23-stepper-controller v1.4.27.

Millimeters in assembly coordinates. Z=0 is the motor rear face. USB faces +Y.
Run this file to check the fit and write the parts and print plate to models/.
"""

import json
from math import pi, sqrt
from pathlib import Path

import cadquery as cq
import trimesh

HERE = Path(__file__).resolve().parent
BOARD = json.loads((HERE / "board-v1.4.27.json").read_text())
BOUNDS = BOARD["bounds_from_pcb_top_mm"]
HOLES = [(x, y) for x, y, diameter in BOARD["rear_holes_mm"]]
PCB_BOTTOM = 8.0  # published board-to-motor gap
PCB_TOP = PCB_BOTTOM + BOARD["pcb_size_mm"][2]
FLOOR = 1.6
EDGE_GAP, WALL = 0.45, 1.65
OUTER = EDGE_GAP + WALL
SEAM = 0.20
CEILING = PCB_TOP + BOUNDS["C_BULK"][5] + 3.0
TOP = CEILING + 1.8
BORE_D, HEAD_D, SEAT = 3.7, 6.8, 15.0  # M3 screw, seat measured from motor
USB_PORTS = ("J_USB", "J_USB_POWER")
INDICATORS = ("D_PWR", "D_STATUS")
BUTTONS = ("SW_BOOT", "SW_RUN")


def box(x0, y0, z0, x1, y1, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, cq.Vector(x0, y0, z0))


def cylinder(x, y, z0, z1, diameter):
    return cq.Solid.makeCylinder(diameter / 2, z1 - z0, cq.Vector(x, y, z0))


def profile(offset, z0, z1):
    """The three tangent arcs in each quadrant of the release's rear-outline.ts."""
    path = cq.Workplane("XY", origin=(0, 0, z0)).moveTo(-16.5, 28 + offset)
    outer_radius, inner_radius = 2.5 + offset, 5.0 - offset
    dr, di = outer_radius / sqrt(2), inner_radius / sqrt(2)
    for side in range(4):

        def xy(x, y, quadrant=side):
            return ((x, y), (y, -x), (-x, -y), (-y, x))[quadrant]

        path = (
            path.lineTo(*xy(16.5, 28 + offset))
            .threePointArc(xy(16.5 + dr, 25.5 + dr), xy(19 + offset, 25.5))
            .lineTo(*xy(19 + offset, 24))
            .threePointArc(xy(24 - di, 24 - di), xy(24, 19 + offset))
            .lineTo(*xy(25.5, 19 + offset))
            .threePointArc(xy(25.5 + dr, 16.5 + dr), xy(28 + offset, 16.5))
        )
    return path.close().extrude(z1 - z0)


def center(name):
    x0, y0, _, x1, y1, _ = BOUNDS[name]
    return (x0 + x1) / 2, (y0 + y1) / 2


def usb_opening(name):
    x, _ = center(name)
    z = PCB_TOP + 1.6
    return (
        cq.Workplane("XZ", origin=(x, 34, z))
        .rect(14.2, 9.2)
        .extrude(6.5)
        .edges("|Y")
        .fillet(1.0)
        .val()
    )


def terminal_bay():
    x0, y0, _, x1, y1, _ = BOUNDS["J_MOTOR"]
    # Open through the rim and roof. The inboard corners are rounded for printing.
    bay = box(x0 - 2.4, y0 - 10, PCB_TOP - 3.7, x1 + 2.4, y1 + 1.7, TOP + 1)
    return cq.Workplane(obj=bay).edges("|Z").fillet(1.2).val()


def connector_cuts(part):
    for name in USB_PORTS:
        part = part.cut(usb_opening(name))
    return part.cut(terminal_bay())


def build_tray():
    rim_z = PCB_TOP - SEAM / 2
    tray = profile(OUTER, 0, rim_z).faces("<Z").edges().chamfer(0.35).val()
    tray = tray.cut(profile(EDGE_GAP, FLOOR, rim_z + 1).val())
    tray = tray.cut(cylinder(0, 0, -1, rim_z + 1, 24))
    for x, y in HOLES:
        tray = tray.fuse(cylinder(x, y, FLOOR - 0.1, PCB_BOTTOM, 8.7))
        tray = tray.cut(cylinder(x, y, -1, rim_z + 1, BORE_D))
        # Lets the tray register over the original heads for an unfastened dry fit.
        tray = tray.cut(cylinder(x, y, -1, 3.5, 6.6))
    return connector_cuts(tray).clean()


def build_cover():
    rim_z = PCB_TOP + SEAM / 2
    cover = profile(OUTER, rim_z, TOP).faces(">Z").edges().chamfer(0.5).val()
    cover = cover.cut(profile(EDGE_GAP, rim_z - 1, CEILING).val())
    for x, y in HOLES:
        # Small annular feet clamp the PCB around its holes. The wider tubes
        # join the side wall above nearby SMD components.
        cover = cover.fuse(cylinder(x, y, PCB_TOP, PCB_TOP + 2.1, 6.2))
        cover = cover.fuse(cq.Solid.makeCone(3.1, 4.3, 1.2, cq.Vector(x, y, PCB_TOP + 2.0)))
        cover = cover.fuse(cylinder(x, y, PCB_TOP + 3.2, CEILING + 0.1, 8.6))
        cover = cover.cut(cylinder(x, y, PCB_TOP - 1, TOP + 1, BORE_D))
        cover = cover.cut(cylinder(x, y, SEAT, TOP + 1, HEAD_D))
    cover = connector_cuts(cover)
    for name in INDICATORS + BUTTONS:
        cover = cover.cut(
            cylinder(*center(name), CEILING - 1, TOP + 1, 2.6 if name in INDICATORS else 3.6)
        )
    # Air slots above the driver and buzzer. Both groups print flat on the bed.
    for name, length, count in (("DRIVER", 15.0, 3), ("BZ1", 7.0, 2)):
        x, y = center(name)
        for row in range(count):
            cy = y + (row - (count - 1) / 2) * 3.8
            slot = (
                cq.Workplane("XY", origin=(x, cy, CEILING - 1))
                .slot2D(length, 1.7)
                .extrude(TOP - CEILING + 2)
                .val()
            )
            cover = cover.cut(slot)
    return cover.clean()


def component(name):
    x0, y0, z0, x1, y1, z1 = BOUNDS[name]
    if name == "C_BULK":  # round aluminum can in index.circuit.tsx
        return cylinder(*center(name), PCB_TOP + z0, PCB_TOP + z1, x1 - x0)
    return box(x0, y0, PCB_TOP + z0, x1, y1, PCB_TOP + z1)


def check(tray, cover):
    def no_overlap(a, b, description):
        volume = a.intersect(b).Volume()
        if volume > 1e-5:
            raise ValueError(f"{description}: {volume:.4f} mm³ overlap")

    for part in (tray, cover):
        assert part.isValid() and len(part.Solids()) == 1
        no_overlap(part, profile(0, PCB_BOTTOM, PCB_TOP).val(), "PCB laminate")
    no_overlap(tray, cover, "part seam")
    case = cq.Compound.makeCompound([tray, cover])
    clearances = {name: case.distance(component(name)) for name in BOUNDS}
    closest = min(clearances, key=clearances.get)
    if clearances[closest] < 0.4:
        raise ValueError(f"Only {clearances[closest]:.3f} mm to {closest}")
    for name, x, y in BOARD["through_hole_pins_mm"]:
        no_overlap(tray, cylinder(x, y, PCB_BOTTOM - 3.5, PCB_BOTTOM, 2.4), name + " solder tail")
    for x, y in HOLES:
        no_overlap(case, cylinder(x, y, -1, TOP + 1, BORE_D - 0.02), "screw shank")
        no_overlap(cover, cylinder(x, y, SEAT, TOP + 1, HEAD_D - 0.02), "head and tool")
        no_overlap(tray, cylinder(x, y, -1, 3.0, 5.5), "reference motor screw head")
    for name in USB_PORTS:
        x, _ = center(name)
        y = BOUNDS[name][4]
        z = PCB_TOP + 1.6
        no_overlap(case, box(x - 6.35, y, z - 3.9, x + 6.35, y + 20, z + 3.9), name + " plug")
    x0, y0, _, x1, y1, height = BOUNDS["J_MOTOR"]
    no_overlap(case, box(x0, y0, PCB_TOP + height, x1, y1, TOP + 15), "terminal push tabs")
    no_overlap(case, box(x0, y0 - 20, PCB_TOP + 1, x1, y1, PCB_TOP + height), "wire access")
    for name in INDICATORS + BUTTONS:
        no_overlap(
            cover, cylinder(*center(name), PCB_TOP + BOUNDS[name][5], TOP + 1, 2), name + " access"
        )
    print(f"{len(BOUNDS)} component envelopes, closest {closest}: {clearances[closest]:.2f} mm")
    print(
        f"Motor face to roof {TOP:.1f} mm; clearance over C_BULK {CEILING - PCB_TOP - BOUNDS['C_BULK'][5]:.1f} mm"
    )


def export_print_plate(out):
    plate = trimesh.Scene()
    for name, x in (("tray", 50), ("cover", 120)):
        mesh = trimesh.load_mesh(out / f"tscircuit-nema23-wago-{name}-r1.stl")
        assert mesh.is_volume and mesh.body_count == 1, name
        if name == "cover":
            mesh.apply_transform(trimesh.transformations.rotation_matrix(pi, [1, 0, 0]))
        mesh.apply_translation([x, 85, -mesh.bounds[0, 2]])
        mesh.units = "mm"
        plate.add_geometry(mesh, node_name=name, geom_name=name)
    plate.export(out / "tscircuit-nema23-wago-print-plate-r1.3mf")


if __name__ == "__main__":
    tray, cover = build_tray(), build_cover()
    check(tray, cover)
    out = HERE / "models"
    out.mkdir(exist_ok=True)
    for name, solid in (("tray", tray), ("cover", cover)):
        for ext in ("step", "stl"):
            path = out / f"tscircuit-nema23-wago-{name}-r1.{ext}"
            cq.exporters.export(solid, str(path), tolerance=0.025, angularTolerance=0.12)
    export_print_plate(out)
