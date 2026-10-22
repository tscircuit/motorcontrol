"""Verify archived experiment data offline. Does not extract files or access hardware."""
import csv
import hashlib
import io
import json
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parent


def require(condition, message):
    if not condition:
        raise SystemExit(message)


def read_archive(name):
    records = {}
    with tarfile.open(ROOT / "data" / name, "r:gz") as archive:
        for member in archive.getmembers():
            require(member.isfile(), f"Unexpected archive entry: {member.name}")
            require(member.name not in records, f"Duplicate archive entry: {member.name}")
            with archive.extractfile(member) as file:
                records[member.name] = file.read()
    return records


def check_trace(data, name):
    require(data["failure"] is None, f"Failed trial: {name}")
    require("User confirmed" in data["label_status"], f"Unconfirmed labels: {name}")
    require(not data.get("exclude_from_training"), f"Excluded trial: {name}")
    require(data["sample_hz"] == 1000, f"Unexpected feature frequency: {name}")
    bins = data["bins"]
    require(len(bins) == 4096, f"Incomplete feature trace: {name}")
    require(all(len(row) == 5 for row in bins), f"Unexpected row shape: {name}")
    require(all(b[0] - a[0] == 1000 for a, b in zip(bins, bins[1:])),
            f"Discontinuous feature trace: {name}")
    require(data["after"]["current_stall_samples_dropped"] == 0, f"Dropped pairs: {name}")


def main():
    checksums = json.loads((ROOT / "checksums.json").read_text())
    require(checksums["algorithm"] == "sha256", "Unsupported checksum algorithm")
    for name, expected in checksums["files"].items():
        require(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected,
                f"Checksum mismatch: {name}")

    records = read_archive("nema17-training-20261016.tar.gz")
    trials = {name: raw for name, raw in records.items() if Path(name).name.startswith("trial-")}
    require(len(trials) == 24, "Expected 24 training recordings")
    digest = hashlib.sha256(b"".join(trials[name] for name in sorted(trials))).hexdigest()
    model = json.loads((ROOT.parent / "firmware-c/calibration/nema17-stall-20261016.json").read_text())
    require(digest == model["dataset_sha256"], "Dataset does not match calibration digest")
    require(model["recording_count"] == len(trials), "Calibration trial count mismatch")
    index = {row["file"]: row for row in csv.DictReader(io.StringIO((ROOT / "data/trials.csv").read_text()))}
    require(len(index) == 24, "Expected 24 CSV index rows")
    for name, raw in trials.items():
        data = json.loads(raw)
        check_trace(data, name)
        row = index[Path(name).name]
        require(row["sha256"] == hashlib.sha256(raw).hexdigest(), f"Index digest mismatch: {name}")
        require(float(row["speed_full_steps_s"]) == data["config"]["speed"], f"Index speed mismatch: {name}")
        require(row["initial_state"] == data["config"]["initial"], f"Index label mismatch: {name}")

    fresh = read_archive("nema17-fresh-validation-20261016.tar.gz")
    require(len(fresh) == 2, "Expected two fresh validation recordings")
    for name, raw in fresh.items():
        check_trace(json.loads(raw), name)
    excluded = json.loads((ROOT / "results/excluded-batch-manifest.json").read_text())
    require(excluded["exclude_from_training"] is True, "Missing invalid-batch exclusion")
    print(f"PASS: {len(checksums['files'])} file hashes; 24 training + 2 fresh traces; "
          f"4,096 continuous bins each; model dataset SHA-256 {digest}")


if __name__ == "__main__":
    main()
