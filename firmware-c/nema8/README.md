# NEMA8 dual-USB-C bench firmware

Native C for the [NEMA8 controller PCB v1.0.48](https://tscircuit.com/ShiboSoftwareDev/nema8-20mm-dual-usbc-stepper-controller#files). The DATA connector supplies logic power and carries USB CDC serial. The separate PWR/PD connector supplies the TMC2209 motor rail at the USB source's default 5 V. This firmware leaves USB PD negotiation disabled.

## Build and flash

From the repository root, with a bare-metal RISC-V GCC toolchain, newlib headers, and GNU make installed:

```sh
git submodule update --init firmware-c/nema8/vendor/ch32fun
cd firmware-c/nema8
make
```

The build produces `nema8.bin`. On systems that install newlib headers outside the compiler search path, pass `NEWLIB=/path/to/newlib/include` to make.

1. Disconnect both USB ports. Hold BOOT while connecting DATA to the host, then release it.
2. Run `wchisp info` and confirm the chip is a CH32X035F8U6. Run `wchisp flash nema8.bin`. The tool verifies the flash contents and resets the chip.
3. Open the new USB serial port in a terminal with line endings enabled. Send `status` and expect `nema8 idle`.

## Jog the motor

Connect the motor with both supplies off. J_MOTOR pins 1–2 are one winding and pins 3–4 the other. Reconnect DATA normally, then attach a 5 V source to PWR/PD.

| Command | Behavior |
| --- | --- |
| `status` | Reports idle or moving |
| `forward`, `reverse` | Send 400 STEP pulses at 400 pulses/s, then disable the bridge |
| `stop` | Cancel the jog and disable the bridge immediately upon processing |

Commands end with CR or LF. Motion starts only on an explicit jog. Each jog checks that the driver's UART write counter advances after setting IRUN to 9 and IHOLD to 2. With 0.33 Ω sense resistors and the board's analog reference divider, the nominal run current is approximately 0.19 A RMS per phase. “driver unavailable” means the UART exchange failed. Check PWR/PD and the PA3 single-wire connection. A successful jog command confirms driver communication. Observe the shaft to confirm rotation.

| Signal | MCU pin |
| --- | --- |
| TMC2209 STEP, DIR | PB11, PA1 |
| TMC2209 ENN, STDBY | PB12, PA4 |
| TMC2209 PDN_UART (address 0) | PA3 |
| USB D−, D+ | PC16, PC17 |
