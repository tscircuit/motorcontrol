"""Spacer tray + flat-top cover for imrishabh18/rp2040-motor-controller v1.0.58.

All dimensions mm. Assembly frame: PCB origin at the motor axis, Z=0 on the
motor's rear plane, +Z away from the motor. USB-C ports face +Y, the JST PH
motor connector faces +X.

    python mechanical/nema17-flat-top-enclosure/build-cad.py

Writes STEP and STL to the ignored models/ folder next to this file and the
design report to reports/.
"""
import json
import math
import pathlib

import cadquery as cq

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / "models"
OUT.mkdir(exist_ok=True)
REVISIONS = {"spacer": "r1", "cover": "r2"}   # r2 added the LED side notches

# ---- stack (matches the v4 NEMA17 enclosure, so the same bolts fit) ----------
BASE_HEIGHT = 3.4        # motor rear plane -> PCB underside
FLOOR = 1.0              # insulating floor between motor end cap and PCB
PCB_T = 1.6
PCB_BOTTOM = BASE_HEIGHT
PCB_TOP = PCB_BOTTOM + PCB_T
ROOF = 1.4
ROOF_GAP = 0.4           # over the tallest part (J1, 5.5 mm)
SEAT_Z = 8.6             # screw head seat above the motor rear plane (same as v4)

# ---- shell -------------------------------------------------------------------
EDGE_GAP = 0.3           # PCB edge -> inner wall
WALL = 1.2
SEAM_GAP = 0.2           # between spacer wall top and enclosure skirt
TOP_CHAMFER = 0.5
BOTTOM_CHAMFER = 0.3

# ---- fasteners (M3 socket cap, 31 mm pattern) --------------------------------
PITCH = 31.0
BORE_D = 3.6
HEAD_POCKET_D = 6.6
ENTRY_D = 7.0
POST_D = 8.4
POST_FOOT_D = 6.4        # the board keeps a 6.5 mm circle clear around each bolt
POST_FOOT_H = 1.8        # foot height, clears every small part near the bolts
ROTOR_CLEARANCE_D = 22.6

# ---- board outline: 42.30 x 42.32 octagon, R3 at every vertex -----------------
HALF_X = 21.15
HALF_Y = 21.16
CHAMFER_C = 36.81        # corner flats lie on |x| + |y| = CHAMFER_C
OUTLINE_R = 3.0

# ---- connectors ---------------------------------------------------------------
CLEAR = 0.3              # around component envelopes
USB_AXIS_Z = 1.63        # receptacle centreline above the PCB top
USB_PLUG_W, USB_PLUG_H = 13.3, 8.4   # overmold pocket per port (12.7 x 7.8 plug)
USB_RECESS_WALL = 0.8    # wall left behind the overmold recess
# The published 3D model of J1 sits 2.5 mm outboard of its own solder pads.
# The pads decide where the real part lands, so shift the envelope back.
J1_MODEL_DX = -2.5

VENTS = False            # True adds v4-style slots on the -X and -Y walls

# ---- indicator LEDs: a viewing hole through the roof over each, and a notch ---
# ---- in the nearest side wall (-X for both) so they also show from the side ---
LEDS = ("D_PWR", "D_STATUS")   # green power LED, RGB status LED
LED_HOLE_D = 1.5
LED_WINDOW_W = 4.0             # along the wall
LED_WINDOW_H = 2.4             # above the PCB top; open at the seam
LED_WINDOW_R = 1.0             # top corner radius

D_IN = EDGE_GAP
D_OUT = EDGE_GAP + WALL
HOLES = [(sx * PITCH / 2, sy * PITCH / 2) for sx in (-1, 1) for sy in (-1, 1)]


def load_envelopes():
    env = json.loads((ROOT / "component-envelopes-v1.0.58.json").read_text())
    for e in env:
        # GLB frame has the PCB mid-plane at z=0; move to the assembly frame.
        dz = PCB_BOTTOM + PCB_T / 2
        dx = J1_MODEL_DX if e["name"] == "J1" else 0.0
        e["min"] = [e["min"][0] + dx, e["min"][1], e["min"][2] + dz]
        e["max"] = [e["max"][0] + dx, e["max"][1], e["max"][2] + dz]
        # Shell stakes sit inside the board thickness (0.85 mm deep). The part
        # of each shell that overhangs the board edge starts at the PCB top.
        if e["name"] in ("J_USB", "J_MOTOR_USB"):
            e["min"][2] = PCB_TOP
    return {e["name"]: e for e in env}


ENV = load_envelopes()
TALLEST = max(e["max"][2] for e in ENV.values())
CEILING = TALLEST + ROOF_GAP
TOP = CEILING + ROOF
WALL_TOP = PCB_TOP - SEAM_GAP / 2      # spacer wall
SKIRT_BOTTOM = PCB_TOP + SEAM_GAP / 2  # enclosure wall


def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0)).val()


def cyl(d, z0, z1, x=0.0, y=0.0):
    return cq.Solid.makeCylinder(d / 2, z1 - z0, cq.Vector(x, y, z0))


def outline(d, z0, z1):
    """Board outline grown by d, extruded z0..z1."""
    hx, hy, c = HALF_X + d, HALF_Y + d, CHAMFER_C + d * math.sqrt(2)
    pts = [(c - hy, hy), (hx, c - hx), (hx, -(c - hx)), (c - hy, -hy),
           (-(c - hy), -hy), (-hx, -(c - hx)), (-hx, c - hx), (-(c - hy), hy)]
    return (cq.Workplane("XY").polyline(pts).close().extrude(z1 - z0)
            .edges("|Z").fillet(OUTLINE_R + d).translate((0, 0, z0)))


def corner_boss(x, y, z0, z1):
    """Round boss around a bolt, extended into the corner so no sliver gap is
    left between it and the wall."""
    s = 1 / math.sqrt(2)
    ux, uy = math.copysign(s, x), math.copysign(s, y)
    boss = cyl(POST_D, z0, z1, x, y).fuse(cyl(POST_D, z0, z1, x + 0.9 * ux, y + 0.9 * uy))
    return boss.intersect(outline(D_IN + 0.3, z0, z1).val())


def env_box(name, clearance):
    lo, hi = ENV[name]["min"], ENV[name]["max"]
    return box(lo[0] - clearance, hi[0] + clearance, lo[1] - clearance, hi[1] + clearance,
               lo[2] - clearance, hi[2] + clearance)


USB = [ENV["J_USB"], ENV["J_MOTOR_USB"]]
USB_MOUTH_Y = max(e["max"][1] for e in USB)
WALL_OUT_Y = HALF_Y + D_OUT
WALL_IN_Y = HALF_Y + D_IN
RECESS_FLOOR_Y = WALL_IN_Y + USB_RECESS_WALL


def usb_recess():
    """Shallow pocket in the +Y wall so plug overmolds reach the receptacles."""
    xs = [(e["min"][0] + e["max"][0]) / 2 for e in USB]
    x0, x1 = min(xs) - USB_PLUG_W / 2, max(xs) + USB_PLUG_W / 2
    zc = PCB_TOP + USB_AXIS_Z
    z0, z1 = zc - USB_PLUG_H / 2, zc + USB_PLUG_H / 2
    return (cq.Workplane("XZ").center((x0 + x1) / 2, (z0 + z1) / 2).rect(x1 - x0, z1 - z0)
            .extrude(-3).edges("|Y").fillet(1.5).translate((0, RECESS_FLOOR_Y, 0)).val())


def led_axes():
    """(x, y, top of the LED body) for each indicator LED."""
    out = []
    for name in LEDS:
        lo, hi = ENV[name]["min"], ENV[name]["max"]
        out.append(((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, hi[2]))
    return out


def led_window(y):
    """Notch in the -X wall beside an LED, open at the cover's bottom edge."""
    x0, x1 = -30.0, -HALF_X + 1
    z0, z1 = PCB_TOP - 1, PCB_TOP + LED_WINDOW_H
    return (cq.Workplane("XY").box(x1 - x0, LED_WINDOW_W, z1 - z0, centered=False)
            .translate((x0, y - LED_WINDOW_W / 2, z0))
            .edges("|X").edges(">Z").fillet(LED_WINDOW_R).val())


# ================================ spacer tray =================================
def build_spacer():
    body = outline(D_OUT, 0, WALL_TOP).faces("<Z").edges().chamfer(BOTTOM_CHAMFER).val()
    body = body.cut(outline(D_IN, FLOOR, WALL_TOP + 1).val())
    for x, y in HOLES:
        body = body.fuse(corner_boss(x, y, 0, BASE_HEIGHT))
    body = body.cut(cyl(ROTOR_CLEARANCE_D, -1, WALL_TOP + 1))
    for x, y in HOLES:
        body = body.cut(cyl(BORE_D, -1, WALL_TOP + 1, x, y))
    # USB shells overhang the board edge; keep the wall clear of their undersides.
    for e in USB:
        body = body.cut(box(e["min"][0] - 0.4, e["max"][0] + 0.4, HALF_Y, 30, PCB_TOP - 0.3, 30))
    body = body.cut(usb_recess())
    for name, e in ENV.items():          # anything hanging below the PCB
        if e["min"][2] < PCB_BOTTOM - 1e-6:
            body = body.cut(env_box(name, CLEAR))
    return body.clean()


# ================================= enclosure ==================================
def build_enclosure():
    shell = outline(D_OUT, SKIRT_BOTTOM, TOP).faces(">Z").edges().chamfer(TOP_CHAMFER).val()
    shell = shell.cut(outline(D_IN, SKIRT_BOTTOM - 1, CEILING).val())
    step = PCB_TOP + POST_FOOT_H
    flare = (POST_D - POST_FOOT_D) / 2
    for x, y in HOLES:
        shell = shell.fuse(corner_boss(x, y, step, CEILING + 0.2))
        shell = shell.fuse(cyl(POST_FOOT_D, PCB_TOP, step + 0.1, x, y))
        # 45 degree flare from the foot up to the full post
        shell = shell.fuse(cq.Solid.makeCone(POST_FOOT_D / 2, POST_D / 2, flare, cq.Vector(x, y, step - flare)))
    for x, y in HOLES:
        shell = shell.cut(cyl(BORE_D, PCB_TOP - 1, TOP + 1, x, y))
        shell = shell.cut(cyl(HEAD_POCKET_D, SEAT_Z, TOP + 1, x, y))
        shell = shell.cut(cq.Solid.makeCone(HEAD_POCKET_D / 2, ENTRY_D / 2, 0.2, cq.Vector(x, y, TOP - 0.2)))
    # USB-C: opening fitted to each shell, plus the shared overmold recess.
    for e in USB:
        shell = shell.cut(box(e["min"][0] - CLEAR, e["max"][0] + CLEAR, HALF_Y - 1, 30,
                              PCB_TOP - 1, e["max"][2] + CLEAR))
    shell = shell.cut(usb_recess())
    # JST PH: the PHR-4 plug comes in through the +X wall.
    j = ENV["J1"]
    shell = shell.cut(box(HALF_X - 1, 30, j["min"][1] - CLEAR, j["max"][1] + CLEAR, PCB_TOP - 1, CEILING))
    for x, y, z in led_axes():
        shell = shell.cut(cyl(LED_HOLE_D, z, TOP + 1, x, y))
        shell = shell.cut(led_window(y))
    if VENTS:
        for t in (-10, -5, 0, 5, 10):
            shell = shell.cut(box(-30, -HALF_X + 1, t - 0.6, t + 0.6, PCB_TOP + 1.6, PCB_TOP + 5.0))
            shell = shell.cut(box(t - 0.6, t + 0.6, -30, -HALF_Y + 1, PCB_TOP + 1.6, PCB_TOP + 5.0))
    # Local reliefs so posts and walls stay CLEAR away from every part.
    reliefs = []
    for name, e in ENV.items():
        if e["max"][2] <= PCB_TOP + 1e-6:
            continue
        tool = env_box(name, CLEAR)
        vol = shell.intersect(tool).Volume()
        if vol > 1e-6:
            shell = shell.cut(tool)
            reliefs.append({"part": name, "relief_mm3": round(vol, 3)})
    return shell.clean(), reliefs


# ================================== checks ====================================
def check(spacer, enclosure):
    pcb = outline(0, PCB_BOTTOM, PCB_TOP).val()
    problems = []
    for label, solid in (("spacer", spacer), ("enclosure", enclosure)):
        assert solid.isValid(), label
        assert len(solid.Solids()) == 1, (label, "pieces", len(solid.Solids()))
        if solid.intersect(pcb).Volume() > 1e-4:
            problems.append((label, "PCB", round(solid.intersect(pcb).Volume(), 4)))
        for name in ENV:
            v = solid.intersect(env_box(name, CLEAR - 0.05)).Volume()
            if v > 1e-4:
                problems.append((label, name, round(v, 4)))
        for x, y in HOLES:
            assert solid.intersect(cyl(BORE_D - 0.02, -5, 30, x, y)).Volume() < 1e-6, (label, "bore", x, y)
    assert spacer.intersect(enclosure).Volume() < 1e-6, "parts overlap"
    for x, y in HOLES:
        head = cyl(HEAD_POCKET_D - 0.02, SEAT_Z + 0.01, TOP + 1, x, y)
        assert enclosure.intersect(head).Volume() < 1e-6, ("head pocket", x, y)
        # the seat ring under the head must be solid plastic
        for a in range(0, 360, 30):
            px, py = x + 2.4 * math.cos(math.radians(a)), y + 2.4 * math.sin(math.radians(a))
            probe = cyl(0.1, SEAT_Z - 0.25, SEAT_Z - 0.05, px, py)
            assert abs(enclosure.intersect(probe).Volume() - probe.Volume()) < 1e-7, ("seat", x, y, a)
    assert spacer.intersect(cyl(ROTOR_CLEARANCE_D - 0.02, -1, 30)).Volume() < 1e-6
    for x, y, z in led_axes():
        # clear line of sight from the LED body straight up through the roof
        assert enclosure.intersect(cyl(LED_HOLE_D - 0.02, z, TOP + 1, x, y)).Volume() < 1e-6, ("led", x, y)
        # and plastic all the way round the hole where it leaves the top face
        for a in range(0, 360, 15):
            r = LED_HOLE_D / 2 + 0.2
            probe = cyl(0.1, TOP - 0.3, TOP - 0.1, x + r * math.cos(math.radians(a)), y + r * math.sin(math.radians(a)))
            assert abs(enclosure.intersect(probe).Volume() - probe.Volume()) < 1e-7, ("led rim", x, y, a)
        # nothing of the cover between the LED and the outside through its side notch
        half = LED_WINDOW_W / 2 - LED_WINDOW_R
        sight = box(-30, x, y - half, y + half, PCB_TOP + 0.01, PCB_TOP + LED_WINDOW_H - LED_WINDOW_R)
        assert enclosure.intersect(sight).Volume() < 1e-6, ("led window", x, y)
        # and the wall carries on above the notch
        mid = -(HALF_X + D_IN + WALL / 2)
        lintel = box(mid - 0.2, mid + 0.2, y - half, y + half, PCB_TOP + LED_WINDOW_H + 0.3, TOP - 1)
        assert abs(enclosure.intersect(lintel).Volume() - lintel.Volume()) < 1e-7, ("led lintel", x, y)
    assert not problems, problems
    # the top face is one flat plane apart from the four pockets
    top_faces = [f for f in enclosure.Faces() if abs(f.Center().z - TOP) < 1e-6 and f.geomType() == "PLANE"]
    assert len(top_faces) == 1, len(top_faces)
    return top_faces[0].Area()


def main():
    spacer = build_spacer()
    enclosure, reliefs = build_enclosure()
    top_area = check(spacer, enclosure)

    # Both parts stay in assembly coordinates, like the other enclosures here.
    for part, solid in (("spacer", spacer), ("cover", enclosure)):
        stem = str(OUT / f"tscircuit-nema17-flat-top-{part}-{REVISIONS[part]}")
        cq.exporters.export(solid, stem + ".step")
        cq.exporters.export(solid, stem + ".stl", tolerance=0.02, angularTolerance=0.1)

    report = {
        "board": "imrishabh18/rp2040-motor-controller v1.0.58",
        "revisions": REVISIONS,
        "footprint_mm": [round(2 * (HALF_X + D_OUT), 2), round(2 * (HALF_Y + D_OUT), 2)],
        "overall_height_mm": round(TOP, 2),
        "spacer": {"height_mm": round(WALL_TOP, 2), "pcb_seat_z_mm": BASE_HEIGHT, "floor_mm": FLOOR,
                   "center_opening_mm": ROTOR_CLEARANCE_D, "volume_cm3": round(spacer.Volume() / 1000, 2)},
        "cover": {"height_mm": round(TOP - PCB_TOP, 2), "roof_mm": ROOF, "ceiling_above_pcb_mm": round(CEILING - PCB_TOP, 2),
                      "tallest_part_above_pcb_mm": round(TALLEST - PCB_TOP, 2),
                      "flat_top_area_mm2": round(top_area, 1), "volume_cm3": round(enclosure.Volume() / 1000, 2)},
        "wall_mm": WALL, "pcb_edge_gap_mm": EDGE_GAP, "seam_gap_mm": SEAM_GAP, "seam_z_mm": PCB_TOP,
        "screws": {"pattern_mm": PITCH, "bore_mm": BORE_D, "head_pocket_mm": HEAD_POCKET_D,
                   "head_seat_z_mm": SEAT_Z, "pocket_depth_mm": round(TOP - SEAT_Z, 2),
                   "m3_cap_head_below_top_mm": round(TOP - SEAT_Z - 3.0, 2)},
        "usb": {"mouth_y_mm": USB_MOUTH_Y, "recess_floor_y_mm": round(RECESS_FLOOR_Y, 2),
                "outer_wall_y_mm": round(WALL_OUT_Y, 2),
                "mouth_behind_recess_floor_mm": round(RECESS_FLOOR_Y - USB_MOUTH_Y, 2)},
        "j1": {"envelope_min": ENV["J1"]["min"], "envelope_max": ENV["J1"]["max"], "model_shift_x_mm": J1_MODEL_DX},
        "led_holes": [{"led": n, "x_mm": round(x, 3), "y_mm": round(y, 3), "diameter_mm": LED_HOLE_D,
                       "led_top_below_roof_underside_mm": round(CEILING - z, 2)}
                      for n, (x, y, z) in zip(LEDS, led_axes())],
        "led_side_windows": [{"led": n, "wall": "-X", "center_y_mm": round(y, 3), "width_mm": LED_WINDOW_W,
                              "height_above_pcb_mm": LED_WINDOW_H, "corner_radius_mm": LED_WINDOW_R,
                              "led_to_inner_wall_mm": round(x + HALF_X + D_IN, 2)}
                             for n, (x, y, z) in zip(LEDS, led_axes())],
        "component_reliefs": reliefs,
        "component_clearance_mm": CLEAR,
    }
    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "reports" / "design-report.json").write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps(report, indent=1))


if __name__ == "__main__":
    main()
