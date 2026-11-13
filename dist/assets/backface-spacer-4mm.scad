// Dimensions in mm. Defaults reproduce the 4 mm NEMA 17 spacer.
// Set total_height = 10 for the 10 mm NEMA 17 variant (1 mm base + 9 mm sleeves).
// Use scripts/build_spacer_assets.py to export all frame sizes.
$fn = 160;
face = 42;
pitch = 31;
base_height = 1;
total_height = 4;
sleeve_height = total_height - base_height;
sleeve_od = 10;
screw_clearance = 3.4;
rotor_clearance = 22.6;
corner_clip = 5;

half = face / 2;
corner = half - corner_clip;

module outline() {
    polygon([
        [-corner, -half], [corner, -half], [half, -corner], [half, corner],
        [corner, half], [-corner, half], [-half, corner], [-half, -corner]
    ]);
}

module bolt_pattern() {
    for (x = [-pitch / 2, pitch / 2], y = [-pitch / 2, pitch / 2])
        translate([x, y]) children();
}

module bolt_holes() {
    bolt_pattern() circle(d = screw_clearance);
}

module base_profile() {
    difference() {
        outline();
        bolt_holes();
        circle(d = rotor_clearance);
    }
}

module sleeve_profile() {
    intersection() {
        outline();
        difference() {
            bolt_pattern() circle(d = sleeve_od);
            bolt_holes();
        }
    }
}

union() {
    linear_extrude(base_height) base_profile();
    translate([0, 0, base_height])
        linear_extrude(sleeve_height) sleeve_profile();
}
