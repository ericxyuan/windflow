# Firmware operation and validation

The firmware targets the **Raspberry Pi Pico SC0915 / RP2040**, Arduino-Pico core **6.1.0**, and Adafruit NeoPixel **1.15.2**. It is a commissioned-prototype controller, not a claim of tested physical hardware. Initial settings are deliberately uncommissioned: the fan and servo stay disabled until calibration is completed and saved. Build scripts do not flash a board automatically.

## Building

In PowerShell:

```powershell
cd C:\Users\admin\iCloudDrive\Windflow
.\tools\setup_arduino.ps1
.\tools\test_firmware.ps1
.\tools\build_firmware.ps1
```

The setup script installs isolated dependencies under `.tools`. The board build selects `rp2040:rp2040:rpipico:flash=2097152_262144,freq=133`. Its output is `firmware/dist/Windflow.ino.uf2`. Load it by the Pico's BOOTSEL procedure only after identifying the physical board and checking the wiring. The host tests require the project's `.tools/venv` Python environment with `ziglang`; that environment is separate from the Arduino setup script.

## Modules and timing

| Module | Responsibility |
|---|---|
| `Config.h`, `Control.*` | Validated settings, geometry mapping, timed operating states and safety priorities |
| `Hardware.*`, `SensorCodec.h` | PWM, tach capture, ADCs, I2C transactions and sensor checks |
| `Input.h` | Quadrature decoding, contact debounce and button gestures |
| `Lighting.*` | Main bar, separate ambient chain and discrete status lamp |
| `Service.*`, `Calibration.h` | Bounded USB command parser and session calibration evidence |
| `Storage.*`, `SettingsRecord.h` | Two alternating filesystem records, CRC and validation |
| `Windflow.ino` | Boot/service gate, cooperative scheduling, delayed saves and watchdog |

The control tick is 10 ms; LEDs refresh approximately every 33 ms. I2C runs at 100 kHz with 2 ms transaction timeouts. Voltage/position inputs update every 10 ms, pressure every 20 ms, PD status every 100 ms, and both temperature sensors every 150 ms. Each loop processes at most 24 incoming USB characters. No startup animation uses a blocking delay. The one-second watchdog resets the MCU if the loop stops progressing; a watchdog reset latches a fault on the following boot.

GP6 generates **25 kHz** fan PWM through an inverting open-drain transistor. GP8 uses a different RP2040 PWM slice for **50 Hz** servo pulses. Signal levels are set before loads are enabled. Hardware enable pulldowns keep all switched loads off during reset. The cosmetic LED rail has a **50 ms** settling interval before data is sent, matching the specified 100 nF load-switch slew capacitor.

## User controls and boost mapping

The 24-detent encoder advances one percentage point of the complete range per detent. `encoderReverse` is set during assembly so moving the exposed wheel upward increases output. Rotation changes the saved setting; pressing changes on/off. A short release toggles on/off. A continuous **1.2 second** hold toggles night mode and does not also generate a short press. The push input has 25 ms debounce.

For normalized encoder setting `u`, default boost threshold `T = 0.75`, minimum stable PWM `pmin = 0.20`, maximum permitted PWM `pmax = 1.00`, and minimum area ratio `rmin = 0.75`:

| Setting | Fan PWM | Nozzle |
|---|---|---|
| Off or `u = 0` | Supply disabled | Opens while servo supply is healthy |
| `0 < u <= T` | `pmin + (pmax-pmin) * u/T` | Fully open |
| `T < u <= 1` | `pmax` | Area ratio `1 - ((u-T)/(1-T)) * (1-rmin)` |

The controller computes panel angle as `asin(H * (1-areaRatio)/(2*L))`, with `H = 94 mm` and `L = 55 mm`. At the default endpoint, the opening is 75% of normal area and each panel rotates **12.3355 degrees**. It interpolates five measured servo pulse/feedback pairs at equal panel-angle intervals. This is not a direct linear servo sweep. Configurable closure never exceeds the 15-degree geometric limit, the allowed area ratio cannot be below 0.75, and endpoint pulses must be within 900–2100 microseconds.

Closure advances at no more than 0.35 of the calibrated travel per second and opens at up to 1.2 per second. Live fan increases are slew limited to full duty per second; reductions are twice as fast. Off/zero commands disable the fan immediately. Pressure, thermal, servo and power protections override user commands.

The main bar fills across the complete setting range. Normal output is cyan; crossing the threshold changes the lit section to magenta. A faint amber marker identifies the boundary before it is reached. Ambient light is a separate warm-white downward-facing chain. Default brightnesses are 36/255 main and 12/255 ambient; there are 16 and 8 pixels respectively. Night brightness defaults to zero for both. The status lamp remains available for essential fault indication.

## Startup and saved settings

1. Initialize output signals with load supplies disabled, read settings, start sensors and the watchdog.
2. Require a stable **15 V / at least 2 A** PD contract, measured bus 14–16 V and logic rail 4.65–5.35 V for 500 ms.
3. Refuse automatic operation if settings are absent, invalid or uncommissioned.
4. Command fully open panels, keep the fan and decorative LEDs off, and check position feedback. Home requires 400 ms elapsed, feedback within 60 ADC counts of the open calibration, and good servo-regulator PG. Failure to reach home by 1.5 seconds latches a servo fault.
5. Enable the main and ambient lighting. Ramp fan duty from zero to configured `maxPwm` over **1.8 seconds** using a smoothstep curve. The main bar fills in sync, with panels open.
6. Return smoothly toward the saved setting over **0.9 seconds**, still with panels open. Then allow progressive closure if the saved setting lies in boost.

Night mode, a saved off/zero setting, thermal warning, or invalid pressure skips the full-speed animation. Pressure/thermal limits remain active during both ramps. An off/zero command cancels a ramp. This prevents a deliberately stopped fan from briefly starting at full power after reconnection.

Settings schema **2** includes the revised ADC isolation circuit: default bus scale **11.1** and logic scale **2.1**. Schema-1 records are rejected and require recalibration. The analog feedback LUT must also be measured with the final divider circuit.

Settings use alternating `settings0.bin` / `settings1.bin` records with magic, schema, size, sequence and CRC32. A save writes the alternate slot, flushes it, then reads back and compares the entire record before declaring success. Loading chooses the newest valid record, including sequence rollover. The filesystem does not automatically format itself on failure.

Normal changes save only in Live state, with the servo near its feedback target, healthy PD and bus at least 14.5 V, **8 seconds after the last change** and **at least 60 seconds between attempts**. Thus a power loss immediately after adjustment can restore the previous setting. Calibration saves explicitly after validation. Two records and CRC provide corruption detection and fallback; actual brownout behavior and filesystem recovery still require power-cut tests on hardware.

## Safety behavior

| Condition | Detection and action |
|---|---|
| Fan stall | Two tach pulses per revolution; discard pulse intervals below 1.5 ms, treat feedback older than 600 ms as zero. After 2.4 seconds of fan startup grace, duty at least 30% with RPM below `max(250, 0.30 * rpmAtMax * duty)` for 800 ms latches a stall fault. |
| Abnormal full-speed RPM | In Live state near maximum duty, after 3.5 seconds of fan operation: RPM below 70% or above 125% of measured baseline for 800 ms disables boost; after 4 seconds it latches a stall fault. |
| Excessive pressure | Default pressure above 18 Pa progressively reduces the allowed closure. Above 24 Pa forces opening and caps duty at 40%; persistence over 1.2 seconds latches a pressure fault. Limits are applied to pressure after subtracting calibrated zero. |
| Pressure missing/reversed | Invalid CRC/scale, stale reading over 100 ms, non-finite data or differential pressure below -2 Pa opens the nozzle and caps duty at 50%. Stale continuous-mode measurements trigger a bounded sensor stop/start retry after about one second. |
| Servo tracking | Feedback error over 90 ADC counts or bad servo PG, after a 600 ms state settling allowance, for over 650 ms latches a servo fault. Fault disables the fan and servo so the motor is not repeatedly driven into a stop. |
| Thermal warning | Either sensor at 55 C: opens nozzle, disables cosmetic lighting and caps duty at 50%. Warning clears only below 50 C. These thresholds are configurable within validated bounds. |
| Severe heat / missing temperature | Either sensor at 65 C, invalid temperature data or readings stale over 400 ms: latch a fault and disconnect fan, servo and cosmetic lighting. |
| Power fault | Lost/insufficient PD contract, bus outside 14–16 V or logic outside 4.65–5.35 V latches a fault. Fan PG must be high after 300 ms of enable; servo PG is also checked. No high-current load is driven by a GPIO. |
| Guard removal | Open guard switch latches a fault and removes all switched loads. |
| Watchdog reset | Latches a fault at boot; automatic fan startup is suppressed. |

Boost limits remain latched until the encoder returns to or below the normal/boost threshold; reopening alone does not automatically reapply constriction. Status blue pulses indicate waiting/service/uncommissioned or limited boost. Faults pulse red; thermal warning shows red continuously. Night mode retains the essential status indication.

Faults require `ack` over USB or a short encoder press. Acknowledgment requires good PD, correct measured rails, valid cool temperatures and the guard fitted; it restarts with the fan **off**. If the original problem persists, the next operating checks can latch the fault again. There is no automatic repeated restart into a stall.

RPM does **not** measure airflow on the selected speed-regulated Noctua fan; a restriction can preserve RPM. The differential-pressure sensor provides an independent restriction signal, but blocked/disconnected tubing that produces plausible readings is not fully diagnosable. Pressure tap placement and thresholds require measurement. The servo does not spring open when unpowered; a severe fault disconnects the fan rather than assuming an open nozzle. No current sensor is fitted: branch fuses, voltage supervision, position feedback and time limits complement one another but do not measure winding current.

## Validation evidence and remaining physical checks

The host suite directly compiles the production control logic, calibration-evidence logic, settings-record codec and sensor decoders. It passes **6,343 assertions**, including all 1,001 control settings, startup/off cancellation, fault recovery grace, thermal/pressure/tach/servo faults, service expiry, five-point calibration requirements, corrupt/truncated records and sequence rollover. This establishes software behavior for the simulated inputs. It does not exercise I2C wiring, USB framing, actual flash power loss, analog noise, radio/EMC effects or a physical actuator.

The Pico board build succeeds with the pinned libraries. Adafruit NeoPixel emits a known compiler warning about its RP2040 PIO program's missing `pio_version` initializer; project compilation completes successfully. Hardware release still requires: scope checks of PWM and rail sequencing; measured voltage scaling; tach comparison with an independent tachometer; both temperature sensors checked against a reference; safe obstruction/pressure tests; servo jam/current/torque tests; input and LED checks; repeated power-cut storage tests; and the airflow/noise/temperature commissioning procedure in [calibration.md](calibration.md). No UF2 has been flashed or physical tests represented as completed.
