export type EnclosurePart = {
  id: "plain" | "sticker" | "top" | "bottom";
  title: string;
  stl: string;
  step: string;
  notes: string;
  height_mm: number;
};
export type EnclosureCatalog = {
  revision: string;
  status: string;
  board_revision: string;
  footprint_mm: readonly [number, number];
  mounting_pitch_mm: number;
  parts: readonly EnclosurePart[];
  sha256: Record<string, string>;
};

// Reviewed v4 exports from the shared enclosure viewer. The source of the
// parametric solids remains mechanical/nema17-enclosure/build-cad.py (CadQuery).
export const enclosureCatalog: EnclosureCatalog = {
  revision: "v4",
  status: "Fit-test draft; physical fit unverified",
  board_revision: "1.0.57",
  footprint_mm: [42, 42],
  mounting_pitch_mm: 31,
  parts: [
    {
      id: "plain",
      title: "Plain top cover · no sticker recess",
      stl: "tscircuit-nema17-top-laser-v4.stl",
      step: "tscircuit-nema17-top-laser-v4.step",
      notes:
        "Flat outer face for a fit-test print or UV laser marking. Bolt counterbores remain.",
      height_mm: 6.8,
    },
    {
      id: "sticker",
      title: "Top cover · sticker pocket",
      stl: "tscircuit-nema17-top-sticker-v4.stl",
      step: "tscircuit-nema17-top-sticker-v4.step",
      notes: "38.7 × 19.65 × 0.3 mm pocket for the 38.1 × 19.05 mm label.",
      height_mm: 6.8,
    },
    {
      id: "bottom",
      title: "Bottom housing",
      stl: "tscircuit-nema17-bottom-v4.stl",
      step: "tscircuit-nema17-bottom-v4.step",
      notes: "Continuous exterior wall under the JST; replaces the old spacer.",
      height_mm: 3.4,
    },
  ],
  sha256: {
    "tscircuit-nema17-top-laser-v4.stl":
      "c6edc6291160e573b50c82c2f782bb0e6cdeae4c79ec4d9863201fb49f185fc6",
    "tscircuit-nema17-top-laser-v4.step":
      "72faa556a7152028e2167c3ed1b2e2e2f182ed211caa9ebf183653032e2435ec",
    "tscircuit-nema17-top-sticker-v4.stl":
      "651e5949a4034f23cfee416a06d09ef5fe59d66011fb385bc172d6e05c4df4c4",
    "tscircuit-nema17-top-sticker-v4.step":
      "dc9e34c2bb9834f812cebb56aa3a3bdf58ba7caddbc7daba38fdf295f672bd91",
    "tscircuit-nema17-bottom-v4.stl":
      "d17903ea9095163b85c737f05c5df93049944c757ce978f0401f665bb34e1100",
    "tscircuit-nema17-bottom-v4.step":
      "092caf0026f08dbe3ef6dc612e584d34a99421d3b1a68902f10ed790d83e1135",
  },
};

export const nema14EnclosureCatalog: EnclosureCatalog = {
  revision: "v1",
  status: "Fit-test draft. Physical fit unverified.",
  board_revision: "2.0.0-dev.11",
  footprint_mm: [35.2, 35.2],
  mounting_pitch_mm: 26,
  parts: [
    {
      id: "top",
      title: "Contour top cover",
      stl: "tscircuit-nema14-contour-top-v1.stl",
      step: "tscircuit-nema14-contour-top-v1.step",
      notes: "Recessed guards for the USB-C power and data ports.",
      height_mm: 16.68,
    },
    {
      id: "bottom",
      title: "Contour bottom spacer",
      stl: "tscircuit-nema14-contour-bottom-v1.stl",
      step: "tscircuit-nema14-contour-bottom-v1.step",
      notes: "Centered Ø11 mm through-hole for encoder and magnet clearance.",
      height_mm: 5.79,
    },
  ],
  sha256: {
    "tscircuit-nema14-contour-top-v1.stl":
      "6e8cb2196cc804aeabfcb6d4df6c13d9edc5e18698d0a479529aa006e44ddb90",
    "tscircuit-nema14-contour-top-v1.step":
      "e8c633e65f7a45d843d407d1116c604c0a0b23e3d484b15d0fa6b04c3506e217",
    "tscircuit-nema14-contour-bottom-v1.stl":
      "b3ef3d7c3722579fb501e233241f061330357be572aabfbd5733a90c42a3c534",
    "tscircuit-nema14-contour-bottom-v1.step":
      "ce18127f8dd42103578eb8374d6c06164bc8ecedf6d19ac352daa0d0359fc321",
  },
};

export const enclosureCatalogs = {
  "nema17-enclosure": enclosureCatalog,
  "nema14-enclosure": nema14EnclosureCatalog,
};
