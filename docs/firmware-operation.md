# Firmware operation and validation

The firmware targets the **Raspberry Pi Pico SC0915 / RP2040**, Arduino-Pico core **6.1.0**, and Adafruit NeoPixel **1.15.2**, Adafruit **ST7735 and ST7789 Library 1.11.0**, **GFX 1.12.6** and **BusIO 1.17.4** for the SPI IPS screen. The E3 source and current UF2 have passed host checks and the Pico build described below; this remains software verification without an attached physical device. It is a commissioned-prototype controller, not a claim of tested physical hardware. Initial settings are deliberately uncommissioned: the fan and servo stay disabled until calibration is completed and saved. Build scripts do not flash a board automatically.

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
| `Input.h`, rotary-control state | Quadrature decoding, debounce, button gestures, relative angle and deliberate 360 degree boost-entry turn |
| `Lighting.*` | Downward ambient chain and bounded service pixel tests |
| `Display.*`, `DisplayView.*`, `DisplayLayout.*` |320 x240 landscape display, reserved top status/speed area, relative encoder dial and boost-entry countdown |
| `Service.*`, `Calibration.h` | Bounded USB command parser and session calibration evidence |
| `Storage.*`, `SettingsRecord.h` | Two alternating filesystem records, CRC and validation |
| `Windflow.ino` | Boot/service gate, cooperative scheduling, delayed saves and watchdog |

The control tick is 10 ms; ambient LEDs refresh approximately every 33 ms. The screen renders into one 320 x16 RGB565 buffer (10,240 bytes), rather than allocating a full screen framebuffer. Each strip has 3.41 ms raw wire time at 24 MHz; the 15 strips use at least 6 ms between transfers, with control/sensor polling between strips and approximately 10 Hz page updates. The reserved header remains 64 pixels high. Drawing overhead and actual maximum control-loop delay still need measurement; raw wire-time arithmetic does not prove real-time timing. I2C runs at 100 kHz with 2 ms transaction timeouts. Voltage/position inputs update every 10 ms, pressure every 20 ms, PD status every 100 ms, and both temperature sensors every 150 ms. Each loop processes at most 24 incoming USB characters. No startup animation uses a blocking delay. The one-second watchdog resets the MCU if the loop stops progressing; a watchdog reset latches a fault on the following boot.

GP6 generates **25 kHz** fan PWM through an inverting open-drain transistor. GP8 uses a different RP2040 PWM slice for **50 Hz** servo pulses. Signal levels are set before loads are enabled. Hardware enable pulldowns keep all switched loads off during reset. The cosmetic LED rail has a **50 ms** settling interval before data is sent, matching the specified 100 nF load-switch slew capacitor.

## User controls and deliberate boost entry

The encoder is a 24-detent Bourns PEC11H. Set `encoderReverse` so moving the exposed wheel upward increases output. A short release toggles on/off. Holding **1.2 seconds** toggles night mode without generating a short press; push debounce is 25 ms. The mechanical encoder rotates continuously, so the screen shows a **relative angular position since boot**, with 15 degrees per detent and wrap at 360 degrees. It is not an absolute shaft-angle sensor.

The normal and boost controls now have a deliberate separation requested by the user:

1. In normal control, rotation raises fan power from 0 to 100% while keeping both nozzle panels fully open. **24 physical detents, one revolution, cover the entire normal range**, independent of the configured internal endpoint. The default stored normal segment is 0–750; the controller maps 25 positions to rounded values on that segment. Normal power changes by approximately 4.17 percentage points per detent. An arbitrary saved/service value stays unchanged until rotation, then moves to the strictly adjacent grid point in the chosen direction. At stored 400, for example, upward rotation selects 406 and downward selects 375.
2. At normal 100%, continue upward for **one complete revolution: 24 detents /360 degrees**. This is the boost-entry turn. The fan remains at its maximum allowed PWM and the panels stay fully open. The screen counts down the remaining degrees/detents. The detent that completes this entry turn does **not** close the panels.
3. Subsequent upward rotation controls progressive boost over a further 24 detents. The fan remains at maximum allowed PWM; the outlet area decreases smoothly from 100% to the calibrated minimum, initially 75%. The screen switches to a distinct purple boost indication and shows commanded boost percentage.
4. Rotate downward to reduce boost. Reaching zero closure leaves boost control at normal 100%, fully open, and clears the entry counter. A fresh 24-detent /360 degree entry turn is required before every later boost session. Downward rotation during a partly completed entry turn first unwinds that progress; further downward rotation reduces normal power.

Entry is accepted only in Live operation with the fan on, at normal maximum, the nozzle open, and no thermal/boost limitation. Startup, off, service and fault states cannot queue an entry turn. Turning off cancels boost and entry progress. A saved boost setting is restored as **normal maximum with the nozzle open**, requiring the deliberate entry turn again after power-up. Safety opening takes priority over the displayed command; a limited boost condition is clearly indicated.

Internally, `boostThreshold` retains the stored-setting split for compatibility with geometry and calibration; it no longer causes entry merely by crossing a normal percentage. With normal fraction `n`, requested boost fraction `b`, minimum stable PWM `pmin=0.20`, maximum permitted PWM `pmax=1.00`, and minimum area ratio `rmin=0.75`:

| Control state | Fan target | Nozzle target |
|---|---|---|
| Off or normal zero | Supply disabled | Opens while servo supply is healthy |
| Normal 0–100% | `pmin + (pmax-pmin)*n` for nonzero settings | Fully open |
| Boost-entry turn | `pmax` | Fully open |
| Boost control 0–100% | `pmax` | Area ratio `1-b*(1-rmin)` |

Panel angle is `asin(H*(1-areaRatio)/(2*L))`, with `H=94 mm`, `L=55 mm`. At the initial endpoint each panel rotates **12.3355 degrees** and retains 75% gross outlet area. Five measured servo pulse/feedback pairs interpolate equal panel-angle fractions. This is not a direct linear servo sweep. Closure remains bounded by a 15-degree geometric ceiling, the allowed area ratio is at least 0.75, and pulses must remain 900–2100 microseconds.

Closure advances at no more than 0.35 calibrated travel per second and opens at up to 1.2 per second. Live fan increases are slew limited to full duty per second; reductions are twice as fast. Off/zero disables the fan immediately. Pressure, thermal, servo and power protection override all user targets.

## Screen layout and night mode

The selected **Adafruit 4311 2 inch IPS screen** uses 320 x240 landscape pixels. The **top 64 rows are reserved** for the bars it replaces: normal power in blue/cyan, boost in purple, plus USB power, system/fault and night indicators. Text accompanies color so the operating mode is unambiguous. The lower 176 rows prioritize a large power percentage during normal use, the remaining angle during entry, and a large boost percentage in boost. They also show relative wheel position, measured RPM, worst monitored temperature, pressure and commanded outlet area. The outlet percentage is computed from the commanded panel position; it is not an independent measurement of open area. Below normal maximum the countdown includes the detents needed to reach maximum plus the complete entry turn; it identifies those two parts explicitly. At zero it shows 720 degrees, at stored 400 it shows 540, and at normal maximum it starts at 360; it reaches 0 only after the full entry turn. If entry is temporarily unavailable, the screen distinguishes opening the outlet, reaching full power and a safety restriction. Rejected turns are not queued for later entry.

The separate downward 8-pixel strip remains warm-white ambient lighting. Its default brightness is 12/255; default night ambient brightness is zero. Screen backlight uses the retained service key `mainBrightness` (default 60/255, maximum 80); night backlight uses `nightMain` (default 0, maximum 4). Their legacy names do not refer to physical main LEDs. `mainCount` is a reserved stored field fixed at 16 for compatibility and is not a service key; only the ambient strip has addressable pixels. Screen backlight uses 2 kHz PWM on GP16. Night mode suppresses unnecessary animation and greatly dims/disables the screen while leaving fan control active. An essential fault overrides night dimming with 36/255 backlight and remains visible while the 5 V logic rail is healthy. Service mode also uses at least 36/255 for calibration legibility; a thermal warning enforces at least 16/255 while ambient lighting is disabled. The screen is powered from REG2 and is independent of the switched ambient rail.

The selected pins are SPI0 MOSI=GP19, SCK=GP18, CS=GP20, D/C=GP10, RST=GP7, BL PWM=GP16. Backlight uses PWM slice 0, separate from fan slice 3 and servo slice 4. GPIO supplies control signals only; the screen/backlight is powered by the 5 V rail. BUF2 channels 1/2 buffer CS/reset; channel 3 buffers BL with the same active-high 2 kHz PWM. Its GP16-side R59=100k pulldown, R55=330 ohm output series and display-side R56=1k pulldown must be fitted. This external circuit correction needs no inversion or firmware pin change. Host tests do not establish physical darkness at night brightness zero or absence of a power/reset flash.

## Startup and saved settings

1. Initialize output signals with load supplies disabled, read settings, start sensors and the watchdog.
2. Require a stable **15 V / at least 2 A** PD contract, measured bus 14–16 V and logic rail 4.65–5.35 V for 500 ms.
3. Refuse automatic operation if settings are absent, invalid or uncommissioned.
4. Command fully open panels, keep the fan and decorative LEDs off, and check position feedback. Home requires 400 ms elapsed, feedback within 60 ADC counts of the open calibration, and good servo-regulator PG. Failure to reach home by 1.5 seconds latches a servo fault.
5. Enable the screen live/startup display and ambient lighting. Ramp fan duty from zero to configured `maxPwm` over **1.8 seconds** using a smoothstep curve. The speed indication in the reserved screen header fills in sync, with panels open.
6. Return smoothly toward the saved setting over **0.9 seconds**, still with panels open. A saved boost setting is clamped to normal maximum/open; closure needs a new deliberate 360 degree entry turn.

Night mode, a saved off/zero setting, thermal warning, or invalid pressure skips the full-speed animation. Pressure/thermal limits remain active during both ramps. An off/zero command cancels a ramp. This prevents a deliberately stopped fan from briefly starting at full power after reconnection.

Settings schema **3** adds the screen/input revision and rejects the earlier light-bar settings. The retained ADC isolation circuit uses default bus scale **11.1** and logic scale **2.1**. Schema-1 and schema-2 records are rejected and require recalibration. The analog feedback LUT must also be measured with the final divider circuit.

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

Boost limits remain latched until the control is returned to the normal segment; reopening alone does not automatically reapply constriction. The screen header explicitly identifies waiting, service, uncommissioned, limited boost and faults. Fault indication overrides night mode and cosmetic animation. Leaving boost requires a fresh 360 degree entry turn before another boost session.

Faults require `ack` over USB or a short encoder press. Acknowledgment requires good PD, correct measured rails, valid cool temperatures and the guard fitted; it restarts with the fan **off**. If the original problem persists, the next operating checks can latch the fault again. There is no automatic repeated restart into a stall.

RPM does **not** measure airflow on the selected speed-regulated Noctua fan; a restriction can preserve RPM. The differential-pressure sensor provides an independent restriction signal, but blocked/disconnected tubing that produces plausible readings is not fully diagnosable. Pressure tap placement and thresholds require measurement. The servo does not spring open when unpowered; a severe fault disconnects the fan rather than assuming an open nozzle. No current sensor is fitted: branch fuses, voltage supervision, position feedback and time limits complement one another but do not measure winding current.

## Validation evidence and remaining physical checks

The current E3 host suite passes **7,112 control assertions** and **163 display-view assertions**, with exit 0 for both programs. It compiles the production control logic, calibration evidence, settings records and sensor decoders, and checks the deliberate 24-detent entry turn, progressive boost, reversal/re-entry, cancellation, saved-boost restart, screen data and safety priorities. The exact production Adafruit_GFX layout also passes **384,000 pixel comparisons**, with exit 0. That comparison verifies that the 16-pixel strip renderer reproduces the complete 320 x240 scenes; it is not a test of the physical TFT, its wiring or SPI timing.

The final Pico compilation passes with exit 0: **120,852 bytes of program storage and 11,112 bytes of static RAM**. The canvas additionally allocates **10,240 bytes from the heap**; the static-RAM figure does not include that allocation or all runtime stack/heap use. The current build uses the pinned libraries listed above. No UF2 has been flashed and no physical fan, servo, sensor or screen has been commissioned.

Host/build checks do not exercise I2C/SPI wiring, real USB framing, flash power loss, analog noise, actual PWM/rail timing or actuator behavior. Hardware release still requires scope checks of PWM and rail sequencing, measured voltage scaling, tach comparison with an independent tachometer, temperature-sensor reference checks, safe obstruction/pressure tests, servo jam/current/torque tests, screen/ambient/input checks, repeated power-cut storage tests and the airflow/noise/temperature procedure in [calibration.md](calibration.md). Measure maximum control-loop gaps during screen refresh and confirm full-turn entry/reversal/re-entry on the actual encoder. Rendered previews and raw SPI wire-time calculations do not prove readable brightness, absence of reset flashes or real-time responsiveness.
