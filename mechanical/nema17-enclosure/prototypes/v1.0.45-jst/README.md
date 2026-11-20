# Rounded NEMA17 lid for PCB v1.0.45

This fit-test draft adapts the plain v4 lid for the [RP2040 motor controller
v1.0.45](https://tscircuit.com/imrishabh18/rp2040-motor-controller?version=1.0.45#3d).
The v1.0.45 board has a top-entry JST PH B4B-PH-K-S at J1. Plug the
double-ended harness into J1, then lower the one-piece lid and hood over the
wires. The cable bends downward under the hood and exits through its open
underside.

## Draft downloads

The [Motorcontrol Assets page](../../../../dist/assets.html#enclosure-rounded-jst)
lists the drafts and opens the STL in the existing 3D preview.

- [Editable STEP](../../../../dist/assets/nema17-enclosure/tscircuit-nema17-top-jst-v1.0.45-draft.step)
- [STL for a fit print](../../../../dist/assets/nema17-enclosure/tscircuit-nema17-top-jst-v1.0.45-draft.stl)
- [CAD fit report](fit-report.json)

The lid is 15.2 mm tall and the assembled case is 20.2 mm high from the
existing base datum. The released base remains 42 × 42 mm, with the two
USB-C openings and original 31 × 31 mm screw pattern. The lid extends
10.5 mm on the JST side to cover the wire bend, giving it a 52.5 × 42 mm
overall footprint. The rounded hood is 13.4 mm wide. The four body
outside corners have a 4 mm radius. The top perimeter is rounded by 0.8 mm,
and the lower perimeter and outer notch edges are rounded by 0.25 mm.
The 9.8 × 13.8 mm notch leads into the hood beneath a solid 1.4 mm roof.
The M3 head seats stay at
Z=8.6 mm, so the screw wells are deeper and require a driver that can reach them.

## Fit evidence

The builder checks the two USB-C opening profiles above the bottom edge round,
the through-bores and seats, and 111 component bounds from the pinned board
export. It checks the mated plug envelope, four swept wires and a continuous
vertical corridor for lowering the lid over the cable. It checks that the
hood end wall shields the second bend from the side. The wire model assumes
a 1.6 mm insulation diameter, an 8.03 mm mated height above the board and a
3.35 mm bend radius. Conservative roof headroom is 0.65 mm. The modeled
wire-to-lid gap is 0.65 mm through both bends.

Measure the seated lab pigtail, its insulation and bend, and both USB-C
overmolds before a fit print. Check the rounded opening and tool access in the
slicer. Motor mounting and fastener engagement still need verification on the
StepperOnline 17E1K-05.

## Rebuild

From the repository root, install
`mechanical/nema17-enclosure/requirements.txt` in a Python virtual environment
and run the builder.

```sh
python mechanical/nema17-enclosure/prototypes/v1.0.45-jst/build.py --output /tmp/nema17-jst-lid
```

`component-envelopes.json` records the Circuit JSON and GLB hashes. The GLB
comes from the pinned Circuit JSON using `circuit-json-to-gltf@0.0.166`.
The bounds are in the v4 assembly datum, with the PCB top at Z=5.0 mm.
The connector entries keep their per-primitive bounds to distinguish the
housing from features such as pins. The generated STEP is re-imported and
checked before the report is written.
