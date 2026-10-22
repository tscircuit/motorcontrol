# Mounted XY homing attempts — 2026-10-16

Recorded retrospectively on 2026-10-21 from the conversation and browser observations. The mounted-gantry attempts have screenshots and observed status excerpts, **not continuous raw current traces**. Positions below are controller-commanded coordinates, not measured carriage displacement. No mm/step or gantry dimensions were recorded.

Both controllers reported firmware 1.0.17 / build `30c1b02e14fd6ffa`, shared model `nema17-20261016-v2`. Supply request was 9 V; no independent PD measurement was captured for these runs. General stall auto-stop was off, warning beeping on. Homing was launched from the gantry page, which sequences X before Y and stops the sequence on failure/cancellation.

| Attempt | Sensitivity / score threshold | Speed | Search per end | Backoff | Outcome |
| --- | --- | --- | --- | --- | --- |
| 1 | 90 / 10 | 60 full steps/sec | 1,000 full steps | 100 full steps | X reversed early, then `Stall did not clear during backoff`. Operator confirmed it reversed **before** the physical stop. False positive; no bounds saved. |
| 2 | 35 / 65 | 60 full steps/sec | 1,000 full steps | 100 full steps | X reached commanded -1,000; `No end stop detected within maximum travel`. Operator said it “literally was about to hit the stop.” This is a too-short search, not a confirmed missed contact. |
| 3 | 35 / 65 | 60 full steps/sec | 3,000 full steps | 100 full steps | X sought minimum from approximately -1,000. A sampled display showed ~57/100 at commanded -1,488.4375. Later both axes were stopped, X at -1,600.8125, page reported `Stopped. Press a fresh arrow key to jog again.` Cause of stopping/contact state was not established. No homing completion or bounds. |

Before attempt 2 the operator explicitly confirmed both axes had physical stops suitable for brief contact, clear travel, and approved the retry. Attempt 3 extended the finite search after the operator reported attempt 2 stopped just before contact.

During attempt 1, a sampled display showed a 56/100 stall-like score during backoff at sensitivity 90. During attempt 2 it showed approximately 56/100 with a free-running-like classification while seeking minimum. These sparse samples cannot establish the full free-travel envelope or a reliable replacement threshold. At maximum sensitivity (100), the threshold becomes zero: every otherwise eligible nonnegative score can qualify. “More sensitive” cannot substitute for separating loaded free travel from true stop contact.

## Firmware procedure being exercised

At tested commit `b2e818b`, firmware homing:

1. Checks stopped state, live connection, power readiness, temperature and driver health; NEMA17 requires a 9 V request and 25, 60 or 100 full steps/sec.
2. Seeks minimum with finite travel/time bounds. A fresh eligible score above the sensitivity threshold must persist for 100 ms before triggering.
3. Stops, backs off and requires at least one eligible clear reading before proceeding.
4. Seeks maximum, removes backoff and a detector-response guard from usable travel, then backs off and again requires clearance.
5. Returns to zero and saves bounds only after completion. Bounds constrain commanded steps and cannot confirm actual position or belt/coupling integrity. A restart requires rehoming.

See [firmware](../firmware-c/main.c), [pulse/travel-limit tests](../tests/native/test_homing.c) and [XY page runner](../dist/homing-controls.js). Software tests passed for the implementation; they do not convert the failed/incomplete physical attempts into successful homing.

## Last recorded state and unresolved observation

Both axes stopped; both set to sensitivity 35; neither homed; no travel bounds saved. Y's physical homing was not reached in these sequences. This is the final state observed on 2026-10-16, not a fresh controller readback on the documentation date.

The outstanding operator question is: **Did X reach the physical stop before attempt 3 stopped, or was it still traveling?** The conversation contains no answer. Do not label that run a detected stall, a missed stall, operator cancellation, or successful homing without additional evidence.

Evidence: [first-attempt page](evidence/xy-homing-first-attempt.png), [final stopped page](evidence/xy-homing-stopped.png). Screenshots reflect capture time and may postdate the event discussed; the first screenshot was captured after the initial failed attempt, not a continuous recording of it.
