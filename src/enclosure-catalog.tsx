export type EnclosurePart = {
  id: "plain" | "sticker" | "top" | "bottom";
  title: string;
  stl: string;
  step: string;
  notes: string;
  height_mm: number;
  footprint_mm?: readonly [number, number];
};
export type EnclosureCatalog<Pitch extends number | readonly [number, number] = number> = {
  revision: string;
  status: string;
  board_revision: string;
  footprint_mm: readonly [number, number];
  mounting_pitch_mm: Pitch;
  print_plate?: string;
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
  revision: "r5",
  status: "Fit-test draft. Physical fit unverified.",
  board_revision: "2.0.0-dev.11",
  footprint_mm: [35.2, 35.2],
  mounting_pitch_mm: 26,
  parts: [
    {
      id: "top",
      title: "Flat top cover with USB-C braces and WAGO access",
      stl: "tscircuit-nema14-wago-top-r5.stl",
      step: "tscircuit-nema14-wago-top-r5.step",
      notes: "Two flush USB-C plug collars, an open WAGO service bay, and four equal-depth Ø6.4 mm screw pockets.",
      footprint_mm: [38.25, 38.25],
      height_mm: 13.55,
    },
    {
      id: "bottom",
      title: "Bottom housing with WAGO pin relief",
      stl: "tscircuit-nema14-wago-bottom-r2.stl",
      step: "tscircuit-nema14-wago-bottom-r2.step",
      notes: "3.5 mm deep WAGO pin pocket, Ø22.6 mm center opening and four Ø6.2 mm bolt holes.",
      height_mm: 5.8,
    },
  ],
  sha256: {
    "tscircuit-nema14-wago-top-r5.stl":
      "3950c5d4227e44804184e94f950704d8606c70066107f683888878314438802e",
    "tscircuit-nema14-wago-top-r5.step":
      "03d5baff10a21c012a499a93d5640c7e734364ec5212f56bac673b013d8d7d62",
    "tscircuit-nema14-wago-bottom-r2.stl":
      "a61e4fd7f3ef5ec6872272e5f3ea574f24e3ee1ea56e8f4b2e931b54b140b04e",
    "tscircuit-nema14-wago-bottom-r2.step":
      "b614225fbcb16744b877e7127d93c58fa728f5d8ecd4a517f19d880e5160751f",
  },
};

// Exports from mechanical/nema17-flat-top-enclosure/build-cad.py (CadQuery).
export const nema17FlatTopEnclosureCatalog: EnclosureCatalog = {
  revision: "r2",
  status: "Fit-test draft. Physical fit unverified.",
  board_revision: "1.0.58",
  footprint_mm: [45.3, 45.32],
  mounting_pitch_mm: 31,
  parts: [
    {
      id: "top",
      title: "Flat-top cover with LED openings",
      stl: "tscircuit-nema17-flat-top-cover-r2.stl",
      step: "tscircuit-nema17-flat-top-cover-r2.step",
      notes:
        "One flat top face with four recessed M3 pockets. Each LED has a Ø1.5 mm hole above it and a 4 × 2.4 mm notch in the side wall beside it. USB-C and JST openings are in the other side walls.",
      height_mm: 7.3,
    },
    {
      id: "bottom",
      title: "Spacer tray",
      stl: "tscircuit-nema17-flat-top-spacer-r1.stl",
      step: "tscircuit-nema17-flat-top-spacer-r1.step",
      notes:
        "Holds the PCB 3.4 mm off the motor and walls in its back face and edges. Ø22.6 mm center opening.",
      height_mm: 4.9,
    },
  ],
  sha256: {
    "tscircuit-nema17-flat-top-cover-r2.stl":
      "9b7d5012a736aa4b6d6d018c97d63d4549ba569ddbc59a35b37cc2ddc9bfee86",
    "tscircuit-nema17-flat-top-cover-r2.step":
      "ec438c59fa6292044c7be91bae073b6af48580417b1af482bec8c72502333af2",
    "tscircuit-nema17-flat-top-spacer-r1.stl":
      "4f6b705398dc0cf50fad03dd77048b52820633001bafeeec190b53974fb1e0ee",
    "tscircuit-nema17-flat-top-spacer-r1.step":
      "a5e3282ee78432dd11913d1e70bc326a7a67d122f5e8eb3542345a1a75fc5cae",
  },
};

export const nema23EnclosureCatalog: EnclosureCatalog<readonly [number, number]> = {
  revision: "r1",
  status: "Fit-test draft. Physical fit unverified.",
  board_revision: "1.4.27",
  footprint_mm: [60.2, 60.2],
  mounting_pitch_mm: [50, 32],
  print_plate: "tscircuit-nema23-wago-print-plate-r1.3mf",
  parts: [
    {
      id: "top",
      title: "Vented cover",
      stl: "tscircuit-nema23-wago-cover-r1.stl",
      step: "tscircuit-nema23-wago-cover-r1.step",
      notes: "Open spring-clamp bay, two USB-C openings and recessed M3 screw seats. Print with the flat outer face down.",
      height_mm: 17.3,
    },
    {
      id: "bottom",
      title: "Motor-side tray",
      stl: "tscircuit-nema23-wago-tray-r1.stl",
      step: "tscircuit-nema23-wago-tray-r1.step",
      notes: "Supports the PCB 8 mm above the motor, with space for solder tails and a Ø24 mm center opening. Print with the motor face down.",
      height_mm: 9.5,
    },
  ],
  sha256: {
    "tscircuit-nema23-wago-cover-r1.stl":
      "263a36ba9f4665ded4f2bb056e170c5ed1dd828034c6ccfadd101c7f67e2b128",
    "tscircuit-nema23-wago-cover-r1.step":
      "e23d50e75aeb038bba6ffb114004dac9effcffe222ef35cce330d1b0e8e69ba6",
    "tscircuit-nema23-wago-tray-r1.stl":
      "d94f34e833e2bd064a55481f3df7c094bc84efc194300ac4f0d1670a957ef087",
    "tscircuit-nema23-wago-tray-r1.step":
      "61406320e76bb4ec8840bb4f8c7c78f5d2a8ddcfef2df2f264091a26ee5e9fa5",
    "tscircuit-nema23-wago-print-plate-r1.3mf":
      "841ad99a42b3090dacf6bae1d56f49e5214c319f6fd858d4b8be787668550e4d",
  },
};

export const enclosureCatalogs = {
  "nema17-enclosure": enclosureCatalog,
  "nema17-flat-top-enclosure": nema17FlatTopEnclosureCatalog,
  "nema14-enclosure": nema14EnclosureCatalog,
  "nema23-enclosure": nema23EnclosureCatalog,
};
