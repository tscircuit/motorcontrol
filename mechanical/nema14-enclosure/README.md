# NEMA14 WAGO enclosure

This two-piece enclosure is a fit-test design for the
[NEMA14 WAGO PCB](https://tscircuit.com/AnasSarkiz/NEMA14_RP2040_v2#3d).
The 35.2 × 35.2 mm motor interface matches the
[14HM11-0404S reference motor drawing](https://github.com/AnasSarkiz/NEMA14_RP2040_V2/blob/1bedc87e95d88da2487e9e01c44a7dc101105816/references/motor/14HM11-0404S.pdf).
The four PCB mounting points are on a 26 × 26 mm pattern. The PCB edge is
visible at the seam between the cover and housing.

| Part | Height | Features |
| --- | --- | --- |
| R5 top cover | 13.55 mm | Flat top across both USB-C collars, four equal-depth screw pockets, and an open WAGO service bay |
| R2 bottom housing | 5.80 mm | 3.50 mm deep WAGO pin pocket, flat motor-facing side, Ø22.6 mm center opening, and four Ø6.2 mm through-holes on 26 mm pitch |

The two collars project 3.05 mm past the motor outline on their respective
sides. The overall envelope is 38.25 × 38.25 × 20.95 mm, including the 1.6 mm
PCB. STEP and STL
downloads are in `dist/assets/nema14-enclosure/` and on the
[Assets page](../../dist/assets.html#nema14-enclosure-heading). The CAD exports
retain their assembly coordinates.

## Plug support and WAGO access

Each collar has a nominal 13.3 × 8.4 mm pocket for a 12.7 × 7.8 mm USB-C plug
body. In CAD the seated plug envelope contacts the collar within 0.45 mm of
translation in each of the four lateral directions. Check that the real
plugs seat before testing side loads.

All four M2.5 screws seat 8.1 mm below the flat top in Ø6.4 mm pockets.
This leaves 0.85 mm radial clearance for a Ø4.7 mm screw head and room for
the driver shaft. Use heads up to 1.45 mm tall for the checked fit. The
DATA-side head has 0.51 mm of clearance beneath the nominal USB-C plug body.
Unplug the DATA cable to reach that screw from above.

The rear bay is open across the WAGO terminal so its push tabs can be reached
from above while wires enter from the rear. CAD checks covered the tool
envelope and the reference harness when lowering the cover. The
cover uses continuous walls over the LEDs. Clear or translucent material is
an option for viewing status lights through the shell.

## Spacer and encoder clearance

The optional AS5600-ASOM footprint is at the PCB origin on the underside.
The Ø22.6 mm opening matches the existing NEMA 14 backface spacer. The
four straight Ø6.2 mm bolt holes clear the reference motor screw heads.
The PCB seats directly on the housing. Two WAGO solder tails lie outside
the center opening. The relief pocket clears them and gives 1.60 mm of
additional depth below the nominal supplier-model pin tips. The CAD check
found no overlap with the WAGO supplier model, populated component envelopes, the
optional encoder model, the reference motor leads, or a 12.7 × 7.8 mm USB-C
plug envelope at either port. The roof shields the modeled electronics
outside the connector bays.

The release leaves the encoder unpopulated. For an encoder-equipped build,
verify the actual rear shaft or magnet carrier, alignment, and magnet-to-sensor
air gap. Check that the printed housing seats against the PCB and clears the
soldered WAGO pins. Check motor attachment and cable seating on the prototype.
Select the fasteners after checking the rear motor interface and the stack
with the actual hardware.

## Native CAD

Open [nema14-wago-r5.FCStd](nema14-wago-r5.FCStd) in FreeCAD 1.0 or newer. The top
cover is a native solid. The bottom housing extrudes the editable
`FlatSpacerProfile` sketch and cuts the editable `WagoRelief` pocket.
The center opening and four bolt holes are dimensioned in the sketch.
Export `TopCover` and `BottomHousing` individually as STEP and STL, and update
the hashes in `src/enclosure-catalog.tsx` when publishing a revised model.
