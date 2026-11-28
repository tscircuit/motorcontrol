# NEMA17 integrated motor assembly drawing

Install bun, then run `bun install` and `bun run drawing` in this directory. The SVG is emitted by the native tscircuit assembly drawing exporter. Keep the GLB next to the TSX file.

The shaft-end and controller-end isometrics include the R2 cover and R1 spacer from tscircuit/motorcontrol. The orthographic views use a dimensionable JSCAD exterior profile. The StepperOnline 17HE15-1504S is the packaging reference for the motor. The model excludes the flexible wiring, cables and label. The tapped holes are represented with nominal major-diameter outlines.

To rebuild the GLB, install cadquery 2.6.1 and trimesh 5.2.2, then run `python build-geometry.py motor-mounting.glb path/to/tscircuit-nema17-flat-top-cover-r2.stl path/to/tscircuit-nema17-flat-top-spacer-r1.stl`. The STLs are in motorcontrol at `dist/assets/nema17-flat-top-enclosure`. The source assembly uses millimetres.
