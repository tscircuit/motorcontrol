# Motorcontrol Desktop

The companion opens a private loopback address in your default browser and serves the dashboard files bundled from `dist/`. Bench, single stepper, two- and three-axis gantry, BLDC, songs, assets and firmware use the same pages as the website. The native process uses pySerial to open USB serial devices. Keep the companion tab visible while moving. Disconnect before changing dashboards. **Quit desktop** shuts down the companion and releases its serial handles.

[Signed downloads for Apple silicon and Windows x64](https://github.com/tscircuit/tscircuit-desktop/releases?q=motorcontrol). Open the DMG and copy the app to Applications, or run the Windows executable. On Linux, run the source with Python 3.10+ and pySerial, USB serial permissions and a desktop automounter.

## Firmware

Stop the motor, disconnect dashboards, unplug PWR and connect only the target board by DATA. Under **Firmware**, select **Identify controller**, check the device ID and proposed version, then **Install firmware**. The updater checks the bundled SHA-256, requires an acknowledged stop, sends the native bootloader command, and writes to the single newly mounted RP2040 drive. Leave other USB devices in place throughout the update. It verifies the original device ID, board profile, firmware version and build fingerprint over serial after restart. Keep PWR disconnected if verification fails. For recovery, use the Firmware page's instructions and the correct UF2 for the physical PCB.

The updater matches the running native NEMA17 firmware profile. It cannot identify a blank board, an incorrectly provisioned board, or a board running unrelated firmware. Use the documented physical PCB target and manual installation in those cases. The BLDC and gantry dashboards remain available for normal operation.

| Reported board profile | Bundled image provenance |
| --- | --- |
| rp2040_drv8825 | PCB 1.0.42, native.yml artifact 14400250000 at b561ae0 |
| rp2040_drv8847 | Older NEMA17, native.yml artifact 14399773851 at b561ae0 |
| rp2040_drv8825_pd | DRV8825 with PD sensing, 1.0.23 UF2 from [the hardware-tested firmware change](https://github.com/tscircuit/motorcontrol/pull/41) at ac88b95 |

The exact source commits, hashes and expected build IDs are in [images/manifest.json](images/manifest.json). When refreshing an image, update the manifest and run the tests. A newer running version is protected against downgrade. The application icon and wordmark come from [tscircuit/design](https://github.com/tscircuit/design/tree/4ec8d68a5a13c182842fd61ece1686e178d7ad20/ts-logo).

## Development

From the repository root, in a Python virtual environment:

```sh
python -m pip install -r desktop/requirements.txt
python -m unittest discover -s desktop -p 'test_*.py'
python desktop/motorcontrol.py
python desktop/build.py
```

The build writes to `build/desktop/`. Pull requests build and smoke-test development packages without release credentials. To publish customer downloads after merging, run **Release Motorcontrol Desktop** on the default branch in tscircuit/tscircuit-desktop. That workflow builds the current motorcontrol main commit and uses the desktop project's Apple Developer ID, notarization, and Windows Artifact Signing configuration. Motorcontrol releases use their own tag prefix and leave the desktop app's latest release in place.
