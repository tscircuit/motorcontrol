# Stall testing record

Recorded here on 2026-10-21 from the 2026-10-16 experiment files and operator conversation. This is an archive of prior tests, not a new hardware test. No motors were commanded while preparing this directory.

**Mounted XY homing is not yet verified. Neither axis completed homing and no travel bounds were saved.** The shared NEMA17 model is an experimental current-pattern classifier trained on one motor, not a universal stall sensor. Increasing sensitivity to 90/100 caused a physically confirmed false trigger.

## Contents

| Location | Contents |
| --- | --- |
| [PROCESS.md](PROCESS.md) | Acquisition procedure, label corrections, firmware integration and next validation steps |
| [HOMING.md](HOMING.md) | Three mounted-gantry attempts, physical observations and unresolved outcome |
| `data/nema17-training-20261016.tar.gz` | Original bytes of all 24 accepted trial JSON files and their batch manifest |
| `data/nema17-fresh-validation-20261016.tar.gz` | Two later, operator-confirmed recordings, separate from training |
| [data/trials.csv](data/trials.csv) | Training trial settings, labels, counts, firmware versions and individual hashes |
| `results/` | Model validation summary, fresh-run summary, excluded-batch manifest and post-flash controller reports |
| `evidence/` | Original screenshots of the accepted batch, fresh validation and stopped homing attempts |
| [checksums.json](checksums.json) | SHA-256 of every archived data, result and evidence file |
| [verify.py](verify.py) | Offline integrity, dataset-digest, labels and feature-bin checks; no serial access |

The archives contain controller identifiers, telemetry, fixture cue timestamps, current feature bins and before/after state. They contain **1 kHz aggregated features, not every 100 kHz raw ADC sample**. Original files have not been relabelled or reformatted. A separate excluded-batch manifest preserves the invalid-label decision without mixing those recordings into training.

## Hardware and firmware provenance

| Controller | Device ID | Role |
| --- | --- | --- |
| Gantry XX | `e66568714f117e21` | DRV8825 NEMA17 training motor; mounted gantry X during homing attempts |
| Gantry YY | `e66568714f538921` | Compatible DRV8825 controller using the shared default; mounted gantry Y |

Training records report firmware 1.0.12; later validation uses the fitted firmware model. Both controllers were subsequently read back on **1.0.17**, build `30c1b02e14fd6ffa`, model `nema17-20261016-v2`, scope `shared-default`. The update reports are evidence of installation/settings, not successful motion or homing. These are historical states, not a claim about what is connected today.

Relevant changes: [shared default model, PR #37](https://github.com/tscircuit/motorcontrol/pull/37), [sensitivity and homing, PR #36](https://github.com/tscircuit/motorcontrol/pull/36). The tested shared-model main commit was `b2e818b`.

The source of truth for coefficients is [the calibration JSON](../firmware-c/calibration/nema17-stall-20261016.json); the deployed coefficients are [stall_model.h](../firmware-c/stall_model.h). Do not maintain a second hand-edited model here.

## Offline reproduction

From the repository root:

```sh
python3 stall-testing/verify.py
mkdir -p /tmp/motorcontrol-stall-study
tar -xzf stall-testing/data/nema17-training-20261016.tar.gz -C /tmp/motorcontrol-stall-study
python3 -m venv /tmp/motorcontrol-stall-study/venv
/tmp/motorcontrol-stall-study/venv/bin/pip install numpy
/tmp/motorcontrol-stall-study/venv/bin/python tools/train_stall_model.py \
  /tmp/motorcontrol-stall-study/batch-20261016-144921-3968 \
  /tmp/motorcontrol-stall-study/model.json
```

Training explores nested whole-trial folds and can take several minutes. Historical NumPy/package versions were not recorded, so bit-for-bit numerical reproducibility across library versions is not asserted. The original JSON bytes and dataset digest are reproducible.

To regenerate the checked-in model from its stored fit:

```sh
/tmp/motorcontrol-stall-study/venv/bin/python tools/export_stall_model.py \
  firmware-c/calibration/nema17-stall-20261016.json \
  /tmp/motorcontrol-stall-study/batch-20261016-144921-3968
git diff -- firmware-c/stall_model.h firmware-c/calibration/nema17-stall-20261016.json
sh scripts/test_native.sh
node tests/test_current_stall.cjs
node tests/test_stall_controls.cjs
node tests/test_homing.cjs
```

The exporter writes those two model files; run it in a clean checkout and inspect the diff. Offline tests establish software behavior and waveform replay, not physical end-stop detection.

Archive checks on 2026-10-21 passed for all file hashes, 24 training traces and two fresh traces, including 4,096 consecutive bins per trace. Exporting the stored fit using the archived training data reproduced `stall_model.h` byte-for-byte with NumPy 2.5.4. The full model-selection search was not rerun for this documentation update.
