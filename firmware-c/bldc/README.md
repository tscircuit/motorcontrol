# Single BLDC — RP2040 / MCT8329A

The native `motorcontrol_bldc.uf2` target powers the dedicated [Single BLDC dashboard](https://motorcontrol.tscircuit.com/bldc.html). It is separate from all stepper targets. Its pin map is for [MustafaMulla29/rp2040-bldc-motor-controller-new v0.3.100](https://tscircuit.com/MustafaMulla29/rp2040-bldc-motor-controller-new), not a generic Pico wiring example.

## Install and use

1. Secure the D4215-650KV motor with no propeller. Set SW4 OFF for firmware changes. Connect the computer to J1 DATA; J19 is the separate PD power input. Connect motor leads to J10/J11/J12 only with motor power removed.
2. Hold BOOTSEL while connecting J1, then copy the [BLDC UF2](https://motorcontrol.tscircuit.com/firmware/motorcontrol-bldc.uf2) onto RPI-RP2.
3. Open the BLDC page in desktop Chrome or Edge and choose **Connect motor**. Only this page understands the `bldc-1` protocol; the stepper pages do not control this firmware.
4. Select **5, 9, 15 or 20 V** and choose **Apply**. Changing the selection pauses drive and re-arms after the selected rail is ready. The connected charger must support the selected voltage at 2 A.
5. Choose **Arm motor**, then **Start timed run** within 30 seconds. The slider supports0–100%. Continuous mode runs until Stop; timed modes stop at their deadline. Arrow control performs its own fresh arming for each hold. Stop disarms immediately; hiding the page, losing focus, disconnecting USB, or missing heartbeats also stops the motor.

No PD NVM or MCT EEPROM writes occur. The PD chip's original settings return after removing all PD power, so select the desired voltage after reconnecting it. No automatic motor start, power negotiation, or arming occurs on connection or reboot.

## Electrical scope

The D4215 completed a short unloaded 9 V test using this RAM configuration before web integration: driver RUN state near 49 electrical Hz, 131 FG edges and physical rotation confirmed by the operator. This does not establish loaded/thermal performance or a phase-current certification.

The configuration uses the authored 0.01-ohm shunt, bidirectional current-sense gain 40, and a 0.4 V threshold for nominal 1 A alignment, open-loop and run current limiting. It retains the short tested startup settings, caps initial duty, and disables startup braking/resynchronization. The MCU additionally checks nominal feed-current increase above 0.9 A, supply bounds, PD_OK2 and nFAULT. ADC scaling remains uncalibrated. A 250 ms watchdog resets to disabled outputs if the MCU stalls. DRVOFF must clear with zero digital command before any speed command is issued.

There is no motor/MOSFET temperature probe, phase-current telemetry, calibrated RPM, position control, or sustained-operation qualification. Electrical Hz is read from the driver; it is not mechanical RPM. The speed slider is a digital reference, not a closed-loop RPM target.

## Hold-to-run arrows (v1.2.0)

Hold Up/Right for forward or Down/Left for reverse. A fresh key/pointer press arms and starts a run; release stops and disarms. Key repeat cannot restart a stopped run. Opposing directions cancel, and all arrows must be released before restarting. Arrow keys inside editable fields do not control motion. Direction changes through verified MCT DIR_INPUT bits before drive is enabled.

The power slider covers0–100% of the digital voltage reference; it does not request a motor power in watts. Zero stops the motor. Continuous mode runs until release/Stop, a fault, power loss, or heartbeat timeout. Timed operation remains available. The input-feed cutoff is nominally0.9A above the pre-run baseline; the phase-current threshold remains nominally1A. The artificial0.5-second reverse wait has been removed; the hardware enable/zero-command checks remain. No temperature signal is displayed or sampled.

## LED

Blue: logic power with motor rail off (also boot/negotiation). Steady amber: motor supply ready, disarmed. Flashing amber: armed and waiting for Start. Cyan: starting. Green: RUN with positive driver electrical frequency and FG activity. Red: failed test/configuration, invalid motor voltage or fault. Normal stopping returns to disarmed indication; the rotor can coast. Stop clears the software error latch.

## Build

Pico SDK with TinyUSB and Arm embedded GCC are required. Set `PICO_SDK_PATH` and optionally `PICO_TOOLCHAIN_PATH`:

```sh
cmake -S firmware-c/bldc -B build/bldc -G Ninja -DPICO_BOARD=pico
cmake --build build/bldc
```

CI builds this target alongside the retained stepper targets. The served UF2 is a checked-in release artifact; update it explicitly after building and validating changes. `firmware_build` fingerprints the C source, policy header and SDK version.

## Serial protocol

115200 baud USB CDC; newline-delimited JSON, maximum 255 bytes per incoming line. Oversized lines are discarded through the next newline. Responses use `protocol: "bldc-1"`; telemetry also includes `firmware: "native-bldc"`.

Commands with an integer `id` receive `{ "type": "ack", "protocol": "bldc-1", "id": 1, "ok": true, "error": "" }`. Heartbeats do not receive ACKs. Plain diagnostic lines may be interleaved with JSON; clients ignore them.

- `hello`: stop/disarm, open a new browser session, invalidate the old heartbeat.
- `heartbeat`: maintain that session, recommended every 300 ms; timeout 1000 ms.
- `status`: request live telemetry without altering motion.
- `set_pd_voltage`, `voltage: 5|9|15|20`: request/verify the selected RAM-only 2 A contract; automatically stops/disarms before negotiating.
- `arm`: verify/apply the RAM profile at the selected voltage with live heartbeats. It expires in 30 seconds or on power/connection loss.
- `start`, `percent: 0..100`, `duration_ms: 0 or 100..60000`, optional `direction: 1|-1`: explicit timed run; requires prior fresh arming. Duration is a whole number of milliseconds.
- `set_speed`, `percent: 0..100`: adjust the reference while running without extending its deadline.
- `stop`: stop/disarm and clear the software LED fault latch.

Telemetry includes `direction`, `direction_supported: true`, and `continuous_supported: true`. Older firmware does not enable the arrow controls.

Telemetry is sent every 250 ms and after commands: device identity/build, state/reason, armed/running/power flags, VBUS/VMOTOR, nominal feed current, feed-current delta, electrical Hz, FG edge count, reference, remaining time, LED state and cached fault words. A telemetry state of `running` requires driver RUN state, positive frequency and FG activity; `starting` only indicates drive has been enabled.

Sources: [TI MCT8329A](https://www.ti.com/lit/ds/symlink/mct8329a.pdf), board source above.

## Selectable voltage (v1.3.0)

The voltage selector requests5,9,15 or20V at2A through STUSB4500 RAM PDOs, with readback and250ms of stable contract validation. Changing voltage first disables drive and clears arming, even with SW4 ON. Unsupported chargers return an error rather than silently accepting a fallback. A MCU-only reset recovers an existing valid two-PDO configuration; no NVM is written. Power/arming thresholds follow the selected voltage; the driver supply is never accepted below4.65V. The delivered target is native C, built with the Raspberry Pi Pico SDK.

Version1.4.0 removes the SW4-off voltage-change requirement. The MCU disables ARM and sends a zero command before renegotiation. It checks the new PD contract; motor arming remains unavailable until the measured switched rail matches the selected voltage. Voltage completion automatically re-arms once the motor rail matches and live heartbeats resume. The page resumes an arrow-driven run only if the arrow is still held; releasing during the change cancels resumption.

Version1.4.1 keeps arrow intent through voltage changes, cancels it on release/Stop/disconnect, and automatically re-arms after a successful voltage change.
