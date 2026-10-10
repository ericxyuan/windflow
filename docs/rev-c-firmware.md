# Motor / ESC firmware — 150 mm Rev D profile, 10 October 2026

`firmware/WindflowRevC` is the separate Raspberry Pi Pico sketch for the T-Motor Pacer V4 P2406 Juicy 2060KV motor and one TeamTriforceUK A50S V2.3c-12-10 VESC-compatible ESC. The proven `firmware/Windflow` Rev B sketch is preserved. Rev C uses closed-loop mechanical speed requests over UART; GPIO6 no longer emits the old 25 kHz four-wire fan signal.

The sketch folder retains its historical `WindflowRevC` name; its active rotor profile now identifies the **150 mm P2 fit article** by the SHA-256 string in `Config.h` and a saved article tag. Schema 5 rejects prior schema-4 records, and settings with a mismatched article tag are rejected even with a correct CRC. The change requires fresh calibration rather than carrying approval from the smaller rotor.

**The distributed build cannot spin the rotor.** `WF_MOTION_BUILD_QUALIFIED` defaults to zero. Normal operation requires that build flag, the schema-5 `rotorQualified` acknowledgement and a measured `commissioned` profile. The physical rotor, enclosure containment, ESC limits and sensorless minimum speed have not been qualified. **The 150 mm rotor has no approved operating RPM.** The unchanged 3000 RPM settings placeholder and 5000 RPM commissioning-input sanity cap are not permission to run this larger rotor. Setting a flag or passing a host test cannot establish printed-rotor strength.

## Hardware and pins

Use a verified 15 V / at least 3 A USB-C PD contract. HUSB238 `PD_STATUS0` voltage code 4 and current code at least `0xA`, plus `PD_STATUS1` attached bit 6, are required; measured bus voltage must also remain 14–16 V. The former 15 V / 2 A configuration is rejected. A50S receives the protected 15 V branch through the new TPS26630 eFuse. Its 5 V BEC and 3.3 V power pins are **not connected to Pico power**. The existing separate 5 V logic and servo regulators remain part of the coordinated Rev C power proposal.

| Pico GPIO | Rev C assignment | Interface |
|---|---|---|
| 0 / 1 | Encoder A / B | Detented quadrature, external pullups and interrupt capture |
| 2 | Encoder press | Debounced short / long press |
| 3 | Reserved optical RPM input | Unfitted; not used as a safety measurement |
| 4 / 5 | I2C SDA / SCL | HUSB238 0x08, MCP9808 0x18/0x19, SDP810-125Pa 0x25 |
| 6 | ESC branch enable | TPS26630 SHDN, active high; default pulldown plus independent grille / logic interlock |
| 7 | Screen reset | Existing buffered screen circuit |
| 8 | Nozzle servo signal | 50 Hz, FS90-FB feedback servo |
| 9 | Servo rail enable | Moved from GPIO13 |
| 10 | Screen D/C | ST7789 control |
| 11 | Ambient strip data | Existing switched 5 V buffer / NeoPixel strip |
| 12 | UART0 TX | Pico TX to A50S RX, 3.3 V maximum signal |
| 13 | UART0 RX | A50S TX to Pico RX, common GND |
| 14 | Ambient rail enable | Existing switched LED supply |
| 15 | Grille interlock status | Buffered active-low closed indication |
| 16 | Screen backlight | 2 kHz PWM |
| 17 | Recessed service jumper | Fit before power-up; encoder held continuously for 4 s |
| 18 / 19 / 20 | Screen SCK / MOSI / CS | SPI0, 24 MHz; no SPI RX pin |
| 21 | Servo power-good | Existing protected input |
| 22 | ESC branch power-good | New branch PG interface, never connect a 15 V signal directly |
| 26 / 27 / 28 | Bus voltage / servo feedback / logic voltage | Scaled ADC inputs, 12-bit readings |

These assignments correspond to the captured Rev C schematic and [physical pin/connector tables](../hardware/rev_c/wiring.md). The Rev B carrier cannot be substituted. The main PCB and installed loom still require completion; changing only the sketch is insufficient.

## ESC transport and speed control

The UART runs at 115200 baud. `VescProtocol.h` implements the documented short and long packet framing with a fixed 128-byte maximum payload, CRC16 CCITT/XMODEM (polynomial `0x1021`, initial zero), checked footer and a 20 ms inter-byte gap timeout. Only a valid `COMM_GET_VALUES` payload of at least 54 bytes updates telemetry. A damaged frame, wrong command, truncated prefix, impossible numeric range or arbitrary incoming byte stream cannot refresh the last valid measurement. RX processing is limited to 64 bytes per loop; USB service RX separately limits work to 24 bytes per loop.

The established GET_VALUES prefix contains FET temperature, signed motor/input current, duty, electrical RPM, input voltage and the ESC fault byte. Extra bounded trailing fields are ignored. A50S firmware must be checked against that layout on the actual controller. The conversion is `mechanical RPM = electrical RPM / 7` for the selected 14-pole motor. Confirm it with an independent optical tachometer during commissioning; the FOC estimator is not an independent physical tachometer.

Every 50 ms the firmware sends `COMM_SET_RPM` for a positive, bounded target. The target equals `speedFraction × rpmAtMax`, at most the configured qualified ceiling and never above the 5000 RPM analysis ceiling. Every 100 ms it requests GET_VALUES. Stop requests use `COMM_SET_CURRENT` with exactly zero to release torque/coast. The firmware emits no raw duty command, reverse command, braking current, motor detection command, ESC configuration write or ESC flash write.

The ESC is powered at rest for telemetry only when the contract, bus, logic, temperature inputs and grille allow it. This separates safe stopped telemetry acquisition from a motion request. A live motion request additionally requires fresh telemetry, the build and rotor qualification gates, valid settings, and no ESC safety fault. All controller faults clear both motion and ESC branch enable. Hardware gating must independently remove branch enable on grille removal, logic loss or reset; software is not a substitute for that circuit.

## User controls and display

The front wheel is beside the IPS screen, with its rotation plane parallel to the screen face and horizontal shaft along +Y. It retains24detents per revolution and the downward ambient strip. One turn spans normal zero to maximum. Commission the direction so clockwise, or upward rolling on the rim nearest the screen, increases output; reversing it decreases output. Once the motor has reached the configured maximum, fresh telemetry confirms it within ±5%, and the nozzle is physically open according to servo feedback, another complete increasing turn arms boost control. That turn holds maximum normal speed with the panels open. The next 24 detents progressively request nozzle closure.

Returning boost to zero leaves boost control and requires a fresh complete entry turn. A partial entry turn can be unwound by turning downward, after which normal output decreases. Extra turns at a limit do not accumulate. Saved boost is restored as maximum **normal** output with an open nozzle after restart; it never restores boost authorization. Off, fault, service entry and reboot clear the volatile gesture.

The screen's top 64 rows replace the previous speed/boost and system light bars. The lower area shows relative wheel phase, requested normal/boost level and degrees remaining before boost control. Wheel phase is relative to boot, because this incremental encoder has no absolute-angle sensor. The former `PWM` label is now `SPEED`. Short press changes on/off, long press changes night mode. Night brightness is configurable, essential faults remain visible, and night startup omits the full-speed cosmetic ramp.

The nominal nozzle inputs remain 104 × 94 mm, 55 mm panel length, at least 75% gross open area and a 15° absolute angle limit. They match the current Rev D nominal proposal; the 75% area input requests approximately 12.3355° maximum closure. The final linkage, real minimum area, opening force and pressure limits remain physical/mechanical qualification work. Firmware pressure and RPM evidence cannot certify the linkage geometry.

## Startup, settings and protection

Startup waits for a stable power contract, valid commissioned settings and stopped ESC telemetry. It opens the nozzle, verifies open feedback and waits for a complete initial display frame. The normal startup then ramps smoothly over 1.8 s to **100% of the configured speed ceiling**, fills the screen bar in sync and returns to the saved normal setting over 0.9 s. It uses no full-throttle interpretation of the motor's KV rating. Off, night, thermal and unhealthy-pressure conditions skip or limit the cosmetic ramp. The user still needs a fresh full turn to enter boost.

Schema 5 deliberately rejects Rev B and earlier 112 mm Rev C records. Dual LittleFS records retain sequence numbers, CRC32, full validation and read-back verification. Setting changes wait at least 8 s before saving and saves are separated by at least 60 s; volatile wheel phase and boost entry progress do not trigger writes. Service commit is explicit. Measure worst-case flash-write pause against the independent 250 ms ESC watchdog during hardware qualification; the firmware cannot prove that timing through a host test. A lost keepalive must coast the ESC.

| Condition | Current Rev C software response |
|---|---|
| ESC telemetry missing or older than 300 ms during homing/live/motor test | Latch ESC link fault; motion and ESC branch off. Initial power qualification waits at rest for the first valid measurement. |
| Any nonzero ESC fault code | Latch controller fault; loads off |
| RPM above the lower of `1.10 × rpmAtMax` and 5000 | Latch overspeed fault; ESC branch off |
| RPM below −50, duty below −0.02, or input current below −0.10 A | Latch direction/regeneration fault |
| Input current above 1.4 A, motor current magnitude above 3 A, or input power above 18 W | Latch motor load fault; configurable only downward within these bounds |
| ESC voltage outside 14–16 V or disagrees with bus ADC by more than 1 V | Latch power fault |
| FET/external power/motor sensor temperature reaches 65 °C | Latch overtemperature fault |
| Temperature warning at 55 °C | Open/disable boost, cap speed fraction, turn ambient off; 5 °C recovery hysteresis |
| Missing temperature input / bad power / grille open | Latch corresponding fault |
| Requested speed high but measured RPM stays too low after startup grace | Latch stall fault |
| Excess pressure or sustained abnormal maximum RPM | Open boost, reduce requested speed as needed, latch a fault if sustained |
| Nozzle position deviates or servo rail fails while operating | Latch servo/power fault |
| Pico watchdog reboot | Start in fault with motion off |

Current thresholds use averaged ESC telemetry; independent ESC current, ERPM, voltage, temperature and timeout limits are required for faster protection. The phase/input limits, 55/65 °C and 18/24 Pa pressure thresholds are trial values requiring bench characterization. Software does not silently re-arm after a fault: acknowledgement requires safe temperature/power/grille state and a finite reported speed within ±60 RPM, sets the saved on-state to off, and clears boost entry progress. The ESC branch shuts down during a fault, so stale feedback is not independent proof of rotor rest. The operator must verify rest before acknowledgement or access, retain fixed guards through coast-down, and use fresh ESC telemetry and an independent optical RPM observation during qualification. Service motion and calibration commits require fresh telemetry.

The magnetic grille interlock stops electrical drive, but the rotor coasts. A fixed secondary guard and suitable containment must prevent contact throughout coast-down. Power removal and a plausible estimated zero RPM do not make a printed rotor safe to touch.

## Commissioning and service

Before any spinning test, use the contained physical rotor qualification procedure and record material, layer orientation, print quality, balance, shaft attachment, optical RPM, vibration, current, temperature and containment outcome. Configure the ESC in VESC Tool with the real motor detection results, UART mode/baud, one allowed direction, conservative phase/input/watt/ERPM limits, no regenerative braking and a 250 ms coast timeout. Check timeout and hard interlock action independently with the Pico disconnected or held in reset. Do not perform motor detection with an unqualified attached printed rotor.

Only after those tests pass should an explicitly qualified build be produced by setting `WF_MOTION_BUILD_QUALIFIED=1`. The checked-in build tool intentionally supplies no such flag. Even that build starts uncommissioned; a console acknowledgement refers to the external physical test record and is not a strength test.

1. Fit the recessed service jumper before power-up and hold the encoder continuously for 4 s. Read `status` and `esc`. Check bus, logic, two temperature sensors, pressure, grille and ESC PG/telemetry. Verify sensor placement and lag physically.
2. Set the qualified ceiling and lower electrical limits as appropriate, for example `set rpmAtMax 2500`. Changes to RPM/current/power qualification fields clear both commissioning and rotor qualification. Geometry, sensor, direction and LED-count changes also clear commissioning; brightness-only changes preserve it.
3. With both loads off and the rotor at rest, send `rotor CONTAINED_QUALIFIED`. It is refused by the distributed build and requires healthy stopped ESC telemetry. Preserve the independent physical test record alongside the assembly record.
4. Use bounded `jog -10..10` commands or the wheel to move the servo. Measure real panel angle and capture `0..4` while feedback is stable. Jog power expires after 0.8 s. The angle cannot be inferred from the ADC alone. Check all five points against the linkage and hard stops.
5. Stop both loads, wait for settled pressure and send `zero`. The sensor must remain within 2 Pa, with no more than 0.5 Pa spread, for at least 1 s.
6. Return to captured fully-open position. Send `motor 30` for the default minimum fraction, then after at least 5 s of stable tracking use `measure motor-min`. Motor tests expire after 10 s. Test the actual configured minimum, not an assumed fraction. The servo holds the calibrated open position while spinning and through coast-down; loss of open feedback stops the test.
7. Test the configured maximum fraction with the same procedure and `measure motor-max`. The measured RPM must track the command within 10% and remain stable. This verifies the ceiling without raising it. Send `motor 0` and wait for rest. Soft protection cancels the active test; it does not automatically retry it.
8. Test individual ambient pixels using `led INDEX R G B`, screen patterns using `screen 1..5`, brightness/count limits and encoder direction. Record noise, flow, maximum safe constriction and temperature margins using hardware measurements. A complete session requires all five servo captures, pressure zero, minimum and maximum speed evidence.
9. With loads off, rotor stopped and sensors healthy, send `commit MEASURED`. Settings are saved and read back. `exit` is refused until the rotor is stopped and both loads are off. Remove the service jumper before normal operation.

## Verification and limits of evidence

Run `tools/test_rev_c_firmware.ps1` for the real production parser/control/service code. One test compilation explicitly enables the motion gate **only in a host simulation**; a second tests the shipping gate and two service variants verify both behaviors. Run `tools/build_rev_c_firmware.ps1` for the default inhibited RP2040 build. `firmware/WindflowRevC/validation.json` records clean process exit codes, test counts, source hashes and the resulting UF2 hash. It does not certify the physical assembly.

Remaining hardware checks include ESC firmware/pinout/timeout behavior, verified 7-pair RPM conversion, sensorless starting/minimum-speed stability, correct phase direction, no regeneration into USB-C, rotor strength/balance/containment, servo hold force and open feedback under airflow, pressure-zero routing and limits, hard interlock/PG/ADC circuits, worst-case flash/SPI/UART latency, thermal lag, noise and flow. No MCU or ESC has been flashed or commissioned in this work.

Primary protocol references: [VESC command implementation](https://github.com/vedderb/bldc/blob/master/comm/commands.c), [packet transport](https://github.com/vedderb/bldc/blob/master/comm/packet.c), [command IDs and controller configuration types](https://github.com/vedderb/bldc/blob/master/datatypes.h). The PD current code follows the [Adafruit HUSB238 register interface](https://github.com/adafruit/Adafruit_HUSB238/blob/main/Adafruit_HUSB238.h). Exact ESC/power selection and supplier links are recorded in the coordinated Rev C hardware documents.
