# NEMA14 RP2040 / A4988 (PCB 1.13.2)

Target: `nema14_a4988`; protocol board ID: `rp2040_a4988_nema14`; firmware version: 1.0.18.

This is the dedicated target for [AnasSarkiz/NEMA14_RP2040](https://tscircuit.com/AnasSarkiz/NEMA14_RP2040), checked against published 1.13.2 circuit JSON and the [firmware contract](https://github.com/AnasSarkiz/NEMA14_RP2040/blob/main/docs/firmware-interface.md). Do not use the DRV8825/DRV8847/DRV8452 images on this PCB.

| Function | GPIO |
| --- | --- |
| STEP / DIR | 6 / 7 |
| Active-low enable / sleep | 8 / 9 |
| CH224A active-low power good | 10 |
| TMP102 SDA / SCL (address 0x48) | 26 / 27 |
| Motor-voltage ADC / data-USB voltage ADC | 28 / 29 |
| RGB red / green / blue | 25 / 2 / 3 |
| Buzzer | 16 |

Build with Pico SDK 2.3.1 and the ARM GCC toolchain:

```sh
cmake -S firmware-c -B build/nema14 -DPICO_BOARD=pico \
  -DMOTOR_BOARD=nema14_a4988 -DMOTOR_INITIAL_NAME="NEMA14 A4988" \
  -DPICO_SDK_PATH=/path/to/pico-sdk
cmake --build build/nema14
```

The image uses generic JEDEC 03h flash reads for the GD25Q16E, avoiding a Winbond-specific quad-enable sequence. Flash `build/nema14/motorcontrol.uf2` through the DATA port's RPI-RP2 drive. The 2 MiB flash reserves its final two sectors for settings.

Connect DATA to the computer and use https://motorcontrol.tscircuit.com in a Web Serial-capable browser. Select **NEMA14 A4988** (or the saved name). Protocol 3 supports finite moves, jogging, prepared moves, ramps, RGB, buzzer, temperature and saved settings. The referenced motor has 400 full steps/revolution; MS1/MS2/MS3 are fixed high for 6400 physical pulses/revolution. Other motors require matching their step angle; commanded position is not shaft feedback.

Connect a 15 V-capable USB-PD supply to PWR for motor operation. CH224A's 56 kΩ configuration resistor requests 15 V; software cannot select a different voltage. Motor enable starts high and sleep starts low. Motion requires active-low PG plus 13.5–16.5 V measured through the 100 kΩ/10 kΩ divider. PG loss is checked every protection loop; ADC voltage is sampled every 100 ms and again before starting motion. A power failure stops and does not automatically restart motion. Readings use nominal 3.3 V ADC reference and resistor ratios; they are not calibrated. DATA voltage is measured through the 100 kΩ/100 kΩ divider.

TMP102 must be valid and below 60°C to start; 75°C, sensor failure, USB disconnect or loss of the 1.5-second heartbeat stops the driver. The 2-second watchdog remains enabled. There is no A4988 nFAULT output or winding-current telemetry. Its current is resistor-set at approximately 0.35 A peak; software cannot change it. Stall detection and stall homing are unavailable. The optional AS5600 is DNP and is not used.

`test_pulses` exercises the STEP generator and its independent PIO edge counter while keeping enable high and sleep low, even without motor power. These counts do not validate physical rotation, torque, phase current or waveforms.

Run `scripts/test_native.sh` for regression coverage, including NEMA14 disabled pin states, PG/voltage interlocks, temperature/heartbeat/USB protection, unsupported command rejection and telemetry. Physical validation evidence is recorded separately from the host tests.

## Bring-up, 2026-10-30

Built with Pico SDK 2.3.1 and flashed through the ROM USB protocol with readback verification after the macOS mass-storage copy stalled. Device `3038513237047dfe` enumerated as `NEMA14 A4988`; protocol telemetry verified version 1.0.18 and build `9df1e5bfa44d49f1`. Idle readings were approximately 25.4°C, 14.9 V motor supply and 4.9 V DATA USB, with PG asserted.

A 1,600-pulse diagnostic at 1,000 Hz completed in 1,601,289 µs, with 1,600 independently counted PIO edges, zero queue underruns, and the driver disabled. The live production single-motor page connected, recognized all five step sizes and 400 full steps/revolution, and showed current sensing as unavailable. Physical rotation, loaded accuracy, phase current, supply transients, thermal shutdown and scope waveforms were not independently validated.
