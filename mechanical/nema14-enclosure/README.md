# NEMA14 WAGO enclosure

This two-piece stepped enclosure is a fit-test design for the
[NEMA14 WAGO PCB](https://tscircuit.com/AnasSarkiz/NEMA14_RP2040_v2#3d).
The nominal 35.2 × 35.2 mm footprint matches the
[14HM11-0404S reference motor drawing](https://github.com/AnasSarkiz/NEMA14_RP2040_V2/blob/1bedc87e95d88da2487e9e01c44a7dc101105816/references/motor/14HM11-0404S.pdf).
The four PCB mounting points are on a 26 × 26 mm pattern. The PCB edge is
visible above the flat spacer.

| Part | Height | Features |
| --- | --- | --- |
| Top cover | 16.68 mm | 90° corners and roof step, recessed USB-C openings, WAGO lead slots, and M2.5 counterbored fastener seats |
| Flat bottom spacer | 3.30 mm | Ø22.6 mm center opening and four Ø6.2 mm through-holes on 26 mm pitch |

The modeled stack is 24.08 mm high, including the 1.6 mm PCB and
separate 2.5 mm PCB standoffs. STEP and STL
downloads are in `dist/assets/nema14-enclosure/` and on the
[Assets page](../../dist/assets.html#nema14-enclosure-heading). The CAD exports
retain their assembly coordinates.

## Spacer and encoder clearance

The optional AS5600-ASOM footprint is at the PCB origin on the underside.
The Ø22.6 mm opening matches the existing NEMA 14 backface spacer. The
four straight Ø6.2 mm bolt holes clear the reference motor screw heads.
Use separate 2.5 mm insulating standoffs over the holes, with a bearing
diameter larger than the through-holes. In this stack the two WAGO tails
outside the opening have 0.60 mm of nominal clearance above the spacer.
The CAD check found no overlap with populated component envelopes, the
optional encoder model, the reference motor leads, or a 12.7 × 7.8 mm USB-C
plug envelope at either port. The roof covers the component locations and
the vent slots sit between components.

The release leaves the encoder unpopulated. For an encoder-equipped build,
verify the actual rear shaft or magnet carrier, alignment, and magnet-to-sensor
air gap. Check motor attachment and cable seating on the physical prototype.
Select the fasteners after checking the rear motor interface and the stack
with the actual hardware.

## Native CAD

Open [contour-v1.FCStd](contour-v1.FCStd) in FreeCAD 1.0 or newer. The top
cover is a native solid. The bottom spacer extrudes the editable
`FlatSpacerProfile` sketch. Its center opening and four bolt holes are
dimensioned in the sketch.
Export `TopCover` and `BottomSpacer` individually as STEP and STL, and update
the hashes in `src/enclosure-catalog.tsx` when publishing a revised model.
