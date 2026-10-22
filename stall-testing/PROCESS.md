# Acquisition and development process

## Signal and units

The NEMA17 DRV8825 has no torque-count register. Its INA240 current measurements were used to develop an experimental stall-pattern score. NEMA23 DRV8452 torque count is a different hardware signal; neither its thresholds nor its electrical-fault reports should be treated as this NEMA17 model's labels.

The firmware samples 100,000 ADC pairs/sec (100,000 samples/sec per winding), aggregates 1 ms feature bins, evaluates the classifier every 50 ms and exports lightweight telemetry at approximately 100 ms intervals. A retained trace holds the final contiguous 4,096 feature bins when deceleration begins, not the entire run. Diagnostic trace download happens while stopped. Normal stall evaluation does not depend on USB waveform streaming.

Each `bins` row is `[device_time_us, mean_a, mean_b, mean_peak_to_peak, mean_variance]`. Current means and peak-to-peak values are in amps; variance is in amps squared. Values are nominal and uncalibrated. `clock_alignment.offset_s` maps device seconds into the host monotonic clock. Cue and telemetry times are host monotonic seconds, not wall-clock dates. See the [trace protocol](../docs/current-stall-experiment.md#diagnostic-recording) and [estimator](../firmware-c/stall_estimator.c).

## Fixture recording procedure used on 2026-10-16

1. Identify XX by device ID and board family. Stop motion, disable optional current streaming and request 9 V. Requested voltage is not a measurement of the PD rail. The batch has no independent voltage measurement.
2. Verify a safe fixture and a physically observed starting state: free rotation or fully immobilized shaft. The operator confirmed they could change the fixture while running.
3. Arm diagnostic trace recording while stopped. Display a five-second motor-start countdown. Use large **LOCK FIXTURE** red text and **FREE FIXTURE** green text with a transition countdown. Verify that repeated spoken instructions, especially “LOCK FIXTURE, LOCK FIXTURE,” are clearly audible before starting a batch.
4. Run a finite 12-second move with a 400 ms ramp. At approximately 10 seconds, instruct the operator to switch fixture state. Record server cue time, browser display time and audio-start time separately.
5. Stop, download the retained trace, preserve telemetry and pre/post state, and inspect feature continuity, dropped samples, driver/sensor faults and pulse underruns. Do not treat output pulses or current as independent shaft feedback.
6. Obtain physical label confirmation from the operator. Keep unconfirmed/corrected runs out of fitting. Do not infer exact mechanical transition onset from the cue timestamp.

The accepted 24-run batch is `batch-20261016-144921-3968`: four speeds (12.5, 25, 60, 100 full steps/sec), each with free/locked starts across full, half and sixteenth logical resolutions. Direction +1 was used for full/sixteenth and -1 for half. Direction and resolution are therefore confounded, not independently swept. Hardware remained fixed at 1/16 microsteps; logical resolutions group pulses. Temperatures in the documented study ranged from 32.1875 to 42.1875 °C. Each accepted trace has 4,096 contiguous bins and reports zero dropped pairs.

## Label corrections and exclusions

- An earlier locked-to-free interpretation was withdrawn by the operator: the fixture had not actually been released as assumed. It is not evidence of a confirmed physical transition.
- Batch `batch-20261016-144621-cd72` was stopped after the operator said they had **not** been locking the fixture. Its manifest explicitly marks the entire batch invalid and excluded. It is retained under `results/excluded-batch-manifest.json`; its recordings are not in the training archive.
- After audible cues were tested, the operator confirmed all cues were followed and all shaft states were correct for the accepted 24-run batch. Those labels are still human observations, with no encoder or fixture sensor.
- Original `split: held_out` tags remain unchanged for provenance. Those runs were subsequently examined during development; they are **not** a fresh blind holdout for the final fit.

## Model selection and integration

The [trainer](../tools/train_stall_model.py) evaluates six features: radial current mean/CV, normalized peak-to-peak ripple, ripple CV, normalized raw ripple RMS and speed-normalized radial-current change. It selects windows, feature subsets and regularized linear discriminants using retrospective nested leave-one-complete-trial-out validation. Threshold selection favors rejecting the observed free-running envelope.

| Full steps/sec | Selected window | Worst outer-fold window error | Policy |
| --- | --- | --- | --- |
| 12.5 | 800 ms | 61.54% | Always uncertain |
| 25 | 400 ms | 10.00% | Classify with uncertainty checks |
| 60 | 100 ms | 0.00% | Classify with uncertainty checks |
| 100 | 100 ms | 8.57% | Classify with uncertainty checks |

These are correlated-window errors from one motor, not real-world stall detection rates. There were no loaded-but-turning controls or independent motors in training. Voltage other than a 9 V request, unfamiliar patterns, temperature excursions and interpolated speeds require the runtime's unknown/uncertain handling. A 100 ms feature window does not prove 100 ms physical detection latency.

Two fresh recordings after fitting used 60 full steps/sec free→locked and 100 full steps/sec locked→free. The operator confirmed rotation before LOCK, full restraint across the locked segments, and rotation after FREE. Cue-to-first-target-state intervals were approximately 1.164 s and 0.357 s. Mechanical onset was not measured, so these are **cue-relative intervals, not physical detection latency**. Both recordings and the summary are archived separately from training.

Firmware 1.0.17 removed the controller-serial eligibility gate for compatible DRV8825 boards and advertised `shared-default` scope. This made YY eligible without a fixture calibration; it did not independently validate transfer to YY or a mounted gantry.

Sensitivity is 0–100 and the score threshold is `100 - sensitivity`. At 90 the threshold is 10; at 35 it is 65. A valid, fresh stall-like score can drive warning beeps even when uncertain. Optional general auto-stop is off by default and requires definite detections. Homing has its own sustained-detection/backoff procedure; see [HOMING.md](HOMING.md).

## Next validation

Continue from confirmed physical positions and verify both axes have suitable stops and clear travel. Record mounted free travel under load as negative examples, actual stop contact as positive examples, both directions and clear-on-backoff. Preserve a continuous timestamped score/feature trace and independently observed contact/release times. Check repeatability and credible ranges before trusting saved bounds. Do not reuse earlier hard-stop readiness as confirmation of today's mechanical setup.

This directory records historical work only. It does not authorize or automatically launch additional motion tests.
