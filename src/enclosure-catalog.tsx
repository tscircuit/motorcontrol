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
      title: "Stepped top cover",
      stl: "tscircuit-nema14-contour-top-v1.stl",
      step: "tscircuit-nema14-contour-top-v1.step",
      notes: "90° corners, a raised WAGO hood, and recessed USB-C power and data openings.",
      height_mm: 16.68,
    },
    {
      id: "bottom",
      title: "Square flat bottom spacer",
      stl: "tscircuit-nema14-contour-bottom-v1.stl",
      step: "tscircuit-nema14-contour-bottom-v1.step",
      notes: "Ø22.6 mm center opening and four straight Ø6.2 mm bolt holes.",
      height_mm: 3.3,
    },
  ],
  sha256: {
    "tscircuit-nema14-contour-top-v1.stl":
      "50ab2938727d3bc88c7576d6b18fbae4140ef179a238a6d61e5138edd102b89a",
    "tscircuit-nema14-contour-top-v1.step":
      "b4e12884c2c94e5369203ac32dd02f2f14ed9696c95182daf2e0d2a8f80e7ad2",
    "tscircuit-nema14-contour-bottom-v1.stl":
      "6f0c8c811b52059bb8153ec9a20ad9dcb79378a45e080a14cc90bc550607a2dc",
    "tscircuit-nema14-contour-bottom-v1.step":
      "76afd4c9914b48fd83c19f02d1deddaa3c75f58fc3e85101e45ebfdcf963cef7",
  },
};

export const enclosureCatalogs = {
  "nema17-enclosure": enclosureCatalog,
  "nema14-enclosure": nema14EnclosureCatalog,
};
