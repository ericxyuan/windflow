# Calibration and commissioning

Follow this with the final wiring and mechanical assembly drawings. The default firmware is uncommissioned and intentionally does not start loads. Calibration values are specific to the actual fan, servo, linkage, divider circuit, pressure taps and sensors. Keep a written measurement log with component serial/lot identifiers, panel angles, pulse widths, ADC values, RPM, pressure, rail voltages and temperatures. The software records evidence of stable measurements; it cannot determine whether an angle was physically measured correctly.

## Before applying power

Check regulator outputs and connector polarity with the loads disconnected. Confirm that PD requests **15 V / 2 A**, that no 15 V net reaches the Pico or fan directly, and that load-switch enables default low. Use the revised ADC-isolation circuit and switched-rail servo buffer specified in the wiring document. Check rail rise times with the selected 100 nF slew capacitors and bulk capacitors. The firmware waits 50 ms before sending LED data.

Fit both temperature sensors at their intended locations; confirm addresses 0x18/0x19. Fit SDP810-125Pa at 0x25 with pressure tubing clear of moving parts. Verify the intended pressure polarity using a small known pressure source within sensor range. Fit the guard switch and guards. Keep the servo horn/linkage **disconnected for its first electrical centering operation**: an uncommissioned servo starts service jogging from 1500 us, which is not a known safe assembled-linkage position.

Initially inspect the mechanism by hand with power disconnected. Establish the fully open position, useful closure limit, hard stops, clearances and horn indexing without forcing the servo. Reconnect the linkage only when its pulse range and indexing are known. Hardware protection, a current-limited bench supply for initial isolated rail tests, and an accessible power disconnect are needed for commissioning; software feedback is not a substitute for these checks.

## Enter service mode

1. With power disconnected, fit the recessed service jumper from GP17 to ground.
2. Hold the encoder push switch while connecting the final PD supply. Continue holding for **4 seconds**. The jumper and button must already be present during the first 150 ms of startup.
3. Open the Pico's USB CDC serial port at 115200 baud. Use a verified USB data path described in the wiring document; avoid connecting two USB hosts. A data-only host connection does not satisfy the PD power requirement for actuator tests.
4. Send `status` and `help`. `state=6` means Service. If there is a latched fault, inspect the indicated condition before `ack`; acknowledgment returns to normal boot with the fan off, so re-enter service by the deliberate boot procedure if needed.

Remove the jumper after commissioning. Holding the encoder during ordinary operation only toggles night mode. A watchdog-reset fault cannot be bypassed by the service boot gesture.

## Commands

Commands are case sensitive, space separated and terminated with a newline. `status`, `help` and `ack` are available outside service. Tests expire automatically; the console must not be used to repeatedly force an obstructed mechanism.

| Command | Meaning |
|---|---|
| `status` | State/fault number, setting, PWM, closure, RPM, pressure, temperatures, measured rails, commanded pulse, ADC feedback, sensor/guard/PD validity, commissioned/filesystem flags |
| `evidence` | Five-point capture bitmask and pressure-zero/minimum-RPM/maximum-RPM evidence flags; complete captures are `0x1f` |
| `set KEY VALUE` | Change a validated setting; clears commissioning and all measurement evidence, so do configuration before collecting measurements |
| `jog -10` through `jog 10` | Adjust servo command by at most 10 us; power it for 0.8 seconds; `jog 0` briefly holds the present command |
| `capture 0` through `capture 4` | Record commanded pulse and stable ADC feedback for the physically measured panel angle |
| `fan 0` | Stop fan and servo test power immediately on the next control tick |
| `fan 20` / `fan 100` | Test the stated percentage duty for up to 10 seconds, bounded by configured maximum PWM; requires captured open position and current feedback near it |
| `measure fan-min` | Accept stable tach observations at the configured minimum duty |
| `measure fan-max` | Accept stable tach observations at configured maximum duty and record measured `rpmAtMax` |
| `zero` | Record mean pressure after at least 1 second of stable zero-flow readings |
| `led INDEX R G B` | Test one physical pixel for 2 seconds: indices 0–15 main, 16–23 ambient, RGB values 0–80 |
| `format ERASE` | Explicitly format the settings filesystem with both actuators off; needed on a new unformatted board, never a routine troubleshooting step |
| `commit MEASURED` | Validate and save commissioning after all required evidence and healthy sensor/power checks |
| `exit` | Leave service and return to startup qualification; uncommitted settings remain uncommissioned |

Fault codes: 0 none, 1 power, 2 temperature sensor, 3 overtemperature, 4 stall/abnormal RPM, 5 servo, 6 pressure, 7 guard, 8 watchdog. State codes: 0 waiting power, 1 uncommissioned, 2 homing, 3 ramp up, 4 ramp down, 5 live, 6 service, 7 fault.

## Configure before collecting evidence

Set any needed fields first. Available keys are `boostThreshold`, `minAreaRatio`, `minPwm`, `maxPwm`, `rpmAtMax`, `pressureSoft`, `pressureHard`, `warnC`, `tripC`, `busScale`, `logicScale`, `encoderReverse`, `mainCount`, `ambientCount`, `mainBrightness`, `ambientBrightness`, `nightMain`, and `nightAmbient`. Fractions use 0–1; brightness uses 0–255 but is safety limited; booleans use 0 or 1.

Default voltage scales are **11.1 bus** and **2.1 logic**, including the ADC-side 1 megohm pulldowns. Compare `status` rail readings with a calibrated meter. A correction is `newScale = oldScale * meterVoltage / displayedVoltage`; validate it at more than one voltage within the supported operating range. Bus scale is restricted to 10–12.2; logic scale to 1.9–2.3. Values outside those ranges indicate a circuit or measurement problem rather than a value to force into the firmware.

The initial normal/boost boundary is 0.75, allowed 0.60–0.90. Initial minimum area is 0.75, allowed 0.75–0.95. Use a larger area ratio to reduce constriction; never tune below 0.75 using the service console. Minimum PWM is allowed 0.20–0.40 and maximum 0.60–1.00. Default thermal warning/trip are 55/65 C; warning must be 40–58 C and trip at least 5 C above warning, no higher than 70 C. Pressure soft/hard start at 18/24 Pa, require at least 3 Pa separation, and cannot exceed 26 Pa hard.

Each `set` clears the session evidence, including cosmetic settings. If a measurement leads to a changed setting, repeat the evidence collection after the last change. This intentionally makes calibration repeatable. A schema change, different servo/divider/linkage, altered area limit, or changed fan requires recalibration.

## Measure the five servo points

The table corresponds to **equal fractions of maximum panel angle**, not equal servo angles, outlet area increments or pulse increments. For the default 94 mm outlet height, 55 mm panels and minimum area ratio 0.75, measure:

| Capture index | Panel angle inward from open |
|---|---:|
| 0 | 0 degrees |
| 1 | 3.0839 degrees |
| 2 | 6.1678 degrees |
| 3 | 9.2517 degrees |
| 4 | 12.3355 degrees |

If `minAreaRatio` changes, calculate `maximumAngle = asin(94*(1-minAreaRatio)/110)` in degrees and use 0%, 25%, 50%, 75%, 100% of that angle. Both opposing panels must reach the same angle without racking. Make a gauge/test jig and measure both sides. Do not use the manufacturer's servo travel range as a proxy for panel angle.

Approach each point in small jogs with the fan off. Establish that the servo is not pulling against a hard stop. At the measured position, send `jog 0`, allow about **0.3–0.5 seconds** for steady feedback, then issue the relevant `capture` before the 0.8-second test timeout. Capture requires at least 250 ms of stable command/feedback, ADC spread at most 12 counts and healthy sensors/PG. Repeat the hold/capture if necessary; never automate continuous retries into a stop.

All five pulse values and all five ADC values must each be strictly monotonic; either increasing or decreasing direction is accepted independently. Pulses must be 900–2100 us with an overall span 80–800 us; feedback must be 50–3200 counts with at least 120 counts total span. A feedback value near a supply rail, abrupt jumps, a reversed point or excessive friction needs correction. Record pulse/ADC values from `status` with the measured panel angle in the test log.

## Zero pressure and measure fan operation

Stop both test loads with `fan 0`; let the rotor coast completely to rest. With ports at the intended zero differential, wait at least one second and send `zero`. Readings must be within +/-2 Pa, span no more than 0.5 Pa, and tach must be below 60 RPM. This captures the mean, rather than one instantaneous sample. If a draft or plumbing error prevents stable zero, fix that first.

**Secure the panels fully open for fan-only tests.** Service fan testing switches the servo supply off, so the mechanism must not depend on powered holding torque during this test. Keep guards fitted and use an open-position fixture outside the airflow path. Briefly use `jog 0` at the captured open command, then issue the fan test while feedback still confirms the open position. Do not bypass the guard input to reach the mechanism with the rotor running.

At default settings, run `fan 20`, wait **5–7 seconds**, then `measure fan-min` before the 10-second timeout. The measured RPM must be at least 250 and stable: peak-to-peak spread no greater than the larger of 80 RPM and 20% of mean. The first two seconds are excluded from the measurement. Repeat cold/warm starts on the bench; a single running sample does not prove reliable starting. If the fan stalls or is unstable, increase `minPwm` within range and repeat the calibration evidence after that `set`.

Return to fully open and test `fan 100` (or the configured maximum percentage); after 5–7 seconds send `measure fan-max`. It requires the same stability checks and an average in 1000–2100 RPM. That measured average becomes `rpmAtMax`. Then `fan 0`. Compare tach against an independent tachometer and confirm the selected fan really outputs two pulses per revolution.

A service test exceeding the soft pressure limit or thermal warning stops test loads. All normal hard safety inputs remain effective. Service does not provide an unrestricted high-pressure sweep. Subsequent live boost testing must use an assembled guarded mechanism with calibrated feedback and pressure protection active.

## LEDs, direction, sensors and commit

Verify wheel direction, detents and press feel mechanically; set `encoderReverse` before the final evidence run if needed. Test each LED with a low value, for example `led 0 8 0 0`, and repeat green/blue to establish color order and pixel addressing. Confirm the physical main/ambient counts and diffuser brightness. Check both temperature channels against a reference at room temperature and a controlled elevated temperature; do not use a flame or deliberately overheat a regulator. Sensor positions must reflect the components being protected without creating nuisance trips from unrelated hot air.

With both actuators off, send `evidence`. It must report captures `0x1f`, zero `1`, fanMin `1`, fanMax `1`. Send `commit MEASURED` only after the recorded physical angles and measurements are correct. Commit also requires valid settings, fitted guard, both regulator PGs, good sensors, a bus of 14.5–16 V, logic rail 4.65–5.35 V and both temperatures at least 5 C below warning. If the new board has no filesystem, use `format ERASE` before the evidence sequence; formatting clears evidence.

Successful commit means the record was written, read back and verified. It does not prove airflow, torque or physical safety. Send `exit`, remove the service jumper with power disconnected and verify normal startup. With the default saved setting, this will run the startup full-power ramp before returning to normal control. Clear the bench and fit guards first.

## Physical acceptance and tuning log

Check normal mode at multiple duties, then increase boost gradually. Log outlet velocity profiles, useful flow/throw, pressure, RPM, noise at a fixed distance, servo current, regulator/air temperatures and any vibration. Evaluate 75%, 80%, 85%, 90%, 95% and 100% encoder settings and reverse the sweep to detect hysteresis. A smaller outlet does not guarantee a faster useful jet: choose a less-constricted endpoint if measured velocity, noise or stability worsens.

Verify safe reactions using controlled tests: remove the guard with power managed; interrupt tach or position feedback electrically; apply simulated temperature inputs in a dedicated test build/fixture; disconnect the pressure sensor; and reduce input voltage with a suitable bench fixture. Do not put fingers or tools into a spinning fan. Confirm loss of servo position stops the fan, rather than assuming the panels can open after a servo power failure.

Test saved-setting persistence after more than 8 seconds of inactivity and 60 seconds since the preceding save, then disconnect/reconnect power. Repeat controlled power cuts around writes and check fallback to a valid older record. Confirm short press, 1.2-second night press, saved off/zero startup, night restart, startup cancellation, fault acknowledgment, service timeout and calibration-entry resistance to accidental gestures. Flash-write and input responsiveness tests must use the actual board, not only the host simulation.

Record pass/fail and measurements for every hardware check. Until these tests are completed, the pressure/thermal thresholds, minimum PWM, servo LUT, maximum closure, vibration mounts, grille retention and airflow claims remain prototype tuning values.
