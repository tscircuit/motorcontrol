# NEMA17 DRV8825 with PD sensing

Build with `-DMOTOR_BOARD=drv8825_pd`. Firmware 1.0.22 targets PCB 1.0.48
(and 1.0.47 with the same populated sensing circuits). Board ID is
`rp2040_drv8825_pd`. The existing `drv8825` target supports PCB 1.0.42.

GPIO7 reads active-high POWER_GOOD with internal pulls disabled. INA226 at
I²C1 address 0x40 measures raw PWR USB VBUS. GPIO26/27 also serve TMP102.
INA226 register 0x02 uses 1.25 mV per count. Its configuration is 0x4526,
continuous bus-voltage-only conversion with 16 averages and 1.1 ms conversion
time. Winding ADC capture continues on GPIO28/29.

Telemetry includes `pd_power_good`, `pd_voltage_measured` (null on sensor
failure), and `pd_voltage_valid`. The dashboard, single-motor and gantry pages
show POWER_GOOD and measured voltage. Firmware and board capabilities identify
the revision and sensing source.

Voltage changes reset qualification. After the existing two-second settling
interval, motion requires three consecutive 100 ms samples within ±5% of the
requested voltage, POWER_GOOD high, and fresh sensor data. Missing or invalid
measurements and out-of-range voltage reset qualification. POWER_GOOD loss is
checked each protection loop; voltage loss is checked each 100 ms sample.
Motion stops and requires an explicit new motion command after recovery.
Startup requests 5 V and holds the motor disabled.

If a request of 9 V or higher is still unready 500 ms after the settling
interval, the buzzer plays an error pattern twice, two seconds apart.
A valid measurement below 1 V with POWER_GOOD low selects the three-note
“buh buh duh” disconnected pattern (220 / 220 / 330 Hz). Other power faults
select the descending “ehh arr” negotiation pattern (440 / 294 Hz).
Both use a four-second notification window, then remain silent until the
requested voltage changes. Reissuing the same voltage or reconnecting power
does not restart the notification window. Recovery silences any active tone.
Temperature alarms have priority. `pd_alarm_active` reports the notification
window and `pd_fault_kind` reports `none`, `disconnected`, or `negotiation`.
At the default 5 V setting the PD alarms remain silent.

Circuit references:
- https://imrishabh18--rp2040-motor-controller-v1-0-48.tscircuit.app/engineering/pd-power-good.md
- https://imrishabh18--rp2040-motor-controller-v1-0-48.tscircuit.app/engineering/pd-voltage-monitor.md
