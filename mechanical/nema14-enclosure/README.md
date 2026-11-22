# NEMA14 WAGO enclosure

This two-piece enclosure is a fit-test design for the
[NEMA14 WAGO PCB](https://tscircuit.com/AnasSarkiz/NEMA14_RP2040_v2#3d).
The nominal 35.2 × 35.2 mm footprint matches the
[14HM11-0404S reference motor drawing](https://github.com/AnasSarkiz/NEMA14_RP2040_V2/blob/1bedc87e95d88da2487e9e01c44a7dc101105816/references/motor/14HM11-0404S.pdf).
The four PCB mounting points are on a 26 × 26 mm pattern. The PCB edge is
visible at the seam between the cover and housing.

| Part | Height | Features |
| --- | --- | --- |
| R3 top cover | 19.60 mm | Convex WAGO roof, flat exterior side opposite the USB-C data port, recessed USB-C openings, and M2.5 counterbored fastener seats |
| R2 bottom housing | 5.80 mm | 3.50 mm deep WAGO pin pocket, flat motor-facing side, Ø22.6 mm center opening, and four Ø6.2 mm through-holes on 26 mm pitch |

The roof rises 2.80 mm from its two sides to the center. The modeled stack is
27.00 mm high, including the 1.6 mm PCB. STEP and STL
downloads are in `dist/assets/nema14-enclosure/` and on the
[Assets page](../../dist/assets.html#nema14-enclosure-heading). The CAD exports
retain their assembly coordinates.

## Spacer and encoder clearance

The optional AS5600-ASOM footprint is at the PCB origin on the underside.
The Ø22.6 mm opening matches the existing NEMA 14 backface spacer. The
four straight Ø6.2 mm bolt holes clear the reference motor screw heads.
The PCB seats directly on the housing. Two WAGO solder tails lie outside
the center opening. The relief pocket clears them and gives 1.60 mm of
additional depth below the nominal supplier-model pin tips. The CAD check
found no overlap with the WAGO supplier model, populated component envelopes, the
optional encoder model, the reference motor leads, or a 12.7 × 7.8 mm USB-C
plug envelope at either port. The roof covers the component locations and
the vent slots sit between components.

The release leaves the encoder unpopulated. For an encoder-equipped build,
verify the actual rear shaft or magnet carrier, alignment, and magnet-to-sensor
air gap. Check that the printed housing seats against the PCB and clears the
soldered WAGO pins. Check motor attachment and cable seating on the prototype.
Select the fasteners after checking the rear motor interface and the stack
with the actual hardware.

## Native CAD

Open [nema14-wago-r3.FCStd](nema14-wago-r3.FCStd) in FreeCAD 1.0 or newer. The top
cover is a native solid. The bottom housing extrudes the editable
`FlatSpacerProfile` sketch and cuts the editable `WagoRelief` pocket.
The center opening and four bolt holes are dimensioned in the sketch.
Export `TopCover` and `BottomHousing` individually as STEP and STL, and update
the hashes in `src/enclosure-catalog.tsx` when publishing a revised model.
