# NEMA14 RP2040 V2 Contour enclosure

Contour v1 is a two-piece fit-test design for the
[NEMA14 RP2040 V2 PCB, release 2.0.0-dev.11](https://tscircuit.com/AnasSarkiz/NEMA14_RP2040_v2#3d).
The nominal 35.2 × 35.2 mm footprint matches the
[14HM11-0404S reference motor drawing](https://github.com/AnasSarkiz/NEMA14_RP2040_V2/blob/1bedc87e95d88da2487e9e01c44a7dc101105816/references/motor/14HM11-0404S.pdf).
The four PCB mounting points are on a 26 × 26 mm pattern. The PCB edge is
visible at the seam.

| Part | Height | Features |
| --- | --- | --- |
| Top cover | 16.68 mm | Open-sided guards for both USB-C receptacles, relief for WAGO leads, and recessed fastener seats |
| Bottom spacer | 5.79 mm | Ø11 mm through-hole on the motor axis and underside reliefs for the reference rear screw heads |

The case is 24.07 mm high in assembly, including the 1.6 mm PCB. STEP and STL
downloads are in `dist/assets/nema14-enclosure/` and on the
[Assets page](../../dist/assets.html#nema14-enclosure-heading). The CAD exports
retain their assembly coordinates. Place each part on the bed in the slicer
and inspect the roof, bosses, and connector openings for support needs.

## Encoder clearance

The optional AS5600-ASOM footprint is at the PCB origin on the underside.
The through-hole crosses the 3.20 mm spacer floor and clears the
5.40 × 7.86 mm footprint courtyard by about 0.73 mm radially at its corners.
The CAD clearance screen checked the supplier encoder model, WAGO terminals
under the PCB, reference rear screw heads and motor leads, and a
12.7 × 7.8 mm USB-C plug envelope at each port.

The release leaves the encoder unpopulated. For an encoder-equipped build,
verify the actual rear shaft or magnet carrier, alignment, and magnet-to-sensor
air gap. Check motor attachment and cable seating on the physical prototype.
The PCB and case fasteners share the four PCB holes. Check pilot sizing and
screw engagement for the chosen material and hardware.

## Native CAD

Open [contour-v1.FCStd](contour-v1.FCStd) in FreeCAD 1.0 or newer. The top
cover and spacer blank are native solids. The bottom spacer is the result of
subtracting the editable `EncoderBore` cylinder. Its radius is 5.50 mm.
Export `TopCover` and `BottomSpacer` individually as STEP and STL, and update
the hashes in `src/enclosure-catalog.tsx` when publishing a revised model.
