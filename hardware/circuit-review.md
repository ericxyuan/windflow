# Electrical circuit review — E2

Reviewed 2026-09-09 against the selected module documentation and the Pico firmware. This is an analytical/netlist review. No carrier PCB has been routed, manufactured, populated or electrically tested. The physical assembly is therefore not yet an electronics release.

## Concrete corrections made

| Previous issue | E2 correction | Firmware consequence |
|---|---|---|
| Always-on 5 V servo buffer could drive an unpowered servo | Dedicated BUF3 on the switched servo supply; input/output pulldowns | Same GP8, noninverting |
| 10 nF switch CT with 470 uF reservoir caused about 2.19 A charging current | CT increased to 100 nF; 330 ohm external QOD resistors defined | 50 ms pixel power-up settle |
| Live divider nets and filter charge could reach an unpowered Pico | Three TMUX1511 channels enabled by a 3.3 V supervisor; filter capacitors on source side | No GPIO added |
| Servo divider unnecessarily loaded the internal feedback pot with 20k | 100k upper, 100k lower, 1M ADC-side pulldown | Recalibrate raw position LUT |
| Divider values, passive counts and firmware scales disagreed | Reference-designator netlist; bus scale11.1, logic scale2.1 | Firmware schema2 invalidates older calibration |
| Raw PD output drove bulk capacitance without controlled startup | EF1 before reservoir and regulator bank; current limit and OVP | No GPIO added; low-voltage input may leave status dark |
| Fan fuse order code was incorrect; connectors were unspecified sets | Corrected 0451.500MRL and fixed electrical harness quantities/pin order | None |

The specified Nexperia buffers characterize input leakage with supply at zero; the separate switched supplies remove an always-on buffer output from the servo and pixels. Their outputs are not universally power-off tolerant and must not be driven by another powered source. [Quad buffer](https://assets.nexperia.com/documents/data-sheet/74AHC_AHCT125.pdf), [single buffer](https://assets.nexperia.com/documents/data-sheet/74AHC_AHCT1G125.pdf).

## Voltage and current checks

| Check | Calculation / design result | Practical limit |
|---|---|---|
| Bus ADC at15 V | 15/11.1 =1.351 V | Calibrate against DMM |
| Bus ADC at18 V | 18/11.1 =1.622 V | EF1 should already have disconnected above its OVP threshold |
| Logic/servo ADC at5.25 V | 5.25/2.1 =2.50 V | Below healthy3.3 V; servo feedback cannot exceed its supply in normal operation |
| ADC disconnected, input still live | Mux source bus divider is100k/10k;15 V produces1.364 V before mux | No stored100 nF capacitor remains directly on ADC side |
| Supervisor threshold |3.07 V nominal, then20 ms release delay | Scope rapid collapse/slow ramp to verify sequencing on built board |
| EF1 OVP |1.19×(1+130/10)=16.66 V nominal | About16.08–17.47 V allowing1% resistors, reference range and100 nA leakage; verify trip on bench |
| EF1 UVLO |1.19×(1+100/15)=9.12 V rising | Firmware's14–16 V and PD check remain stricter operating qualification |
| EF1 current limit |12/8.06=1.489 A | Account for reference and resistor tolerance; not instantaneous disconnect |
| Selected input budget |18.05 W /15 V=1.203 A | At14 V approximately1.29 A before efficiency changes, still below assumed1.41 A low current limit |
| REG2 |1.44 A full-white pixels +0.15 A housekeeping =1.59 A | Nominal2.5 A is thermally dependent |
| Cosmetic load switch |1.44 A steady; approximately1.66 A including capacitor ramp | Below2 A specified DBV operating current under stated conditions; PCB copper and actual startup must be verified |
| Fan |12 V,0.15 A; fixed voltage buck | Check transient remains below13.2 V fan maximum |
| Status LEDs |About6 mA total at typical forward voltages | Even zero forward voltage is limited to13.3 mA total; use three resistors |

These calculations do not establish a single-fault-certified product. A failed regulator passing its input to a 5 V rail is outside the demonstrated protection claim. Do not infer that a TVS holds the bus to its standoff voltage, or that load-switch thermal shutdown is a current limiter. EF1 monitors input voltage; it is not a separate overvoltage detector on each regulator output.

The [TMUX1511](https://www.ti.com/lit/ds/symlink/tmux1511.pdf) accepts the divided signals while unpowered; SUP1 prevents normal connection until its [3.3 V threshold](https://www.ti.com/lit/ds/symlink/tps3808.pdf) is met. EF1 limits input current and isolates the main reservoir. OVP and slew values above are circuit calculations based on the [TPS26600](https://www.ti.com/lit/ds/symlink/tps2660.pdf), not measured trip accuracy.

## Layout requirements for the 90 x65 x22 mm allowance

The allowance is plausible for the carrier semiconductors, passives and edge connectors, with the Pico, three regulator modules and PD board mounted separately. It has **not** been verified by a PCB placement or CAD collision check. Reserve the whole volume until that verification. Put heavy reservoirs and power connectors at the board edge, and the ADC/dividers away from switch nodes and servo wiring.

Use a professionally fabricated FR4 carrier, preferably four layers with continuous system-ground reference and short high-current loops. EF1 requires an exposed-pad footprint and thermal vias into its isolated RTN copper region; follow TI's thermal layout rather than treating it as a leaded adapter. It is not suitable for a solderless breadboard. Keep all RTN-referenced control parts with EF1. Do not connect that thermal island to the general ground pour.

Required footprint families: TPS26600 PWP16/HTSSOP16 exposed pad; TPS22810 DBV/SOT23-6; TPS3808 DBV/SOT23-6 with its distinct pin mapping; TMUX1511 PW/TSSOP14; Nexperia BUF1/2 SO14; BUF3 SOT353-1/TSSOP5; 2N7002 SOT23; SMA SS14; SMB TVS; 2410 fuses;0603 signal passives;1206 QOD resistors; actual radial capacitor lead pitches; specified through-hole connectors. Verify every manufacturer's land pattern and pin1 orientation in schematic capture. Do not equate a shared package name with a shared pinout.

## Release checks still required

1. Capture the specified schematic and all reference designators, perform ERC, place/rout the carrier and complete DRC. Compare its board outline and mating plugs to the reserved CAD volume. No unreviewed auto-routing or undersized thermal adapter substitutes.
2. Inspect solder joints, measure every rail and check module PG levels before connecting the Pico or loads. Scope raw/protected PD input,3.3 V and each switched rail on connection/disconnection.
3. Verify no appreciable phantom supply voltage on servo/LED rails with them disabled and MCU running. Scope ADC pins during slow and abrupt power removal; check the supervisor actually isolates before the MCU rail falls below the signal.
4. Check source behavior with5 V-only,9 V,12 V and correct15 V PD sources. Verify negotiated current/voltage reporting, disabled loads under an unsupported contract, and recovery without repeated stalled startup.
5. Measure simultaneous full fan, quickest servo movement and full-white pixel current/temperature. Test short protection with a current-limited bench supply and isolated dummy loads before any installed harness short test.
6. Verify temperature sensor coupling and trip latency; reported55/65 C thresholds are sensor-location values, not proof that every IC junction stays below a limit. Check EF1 and SW3 temperatures separately from the regulator cluster.
7. Verify real servo feedback monotonicity, no change in settled angle when its measurement network is attached, jam timeout, opening direction and endpoint travel. Inspect grille interlock while the rotor coasts.

Every result is currently **not measured**. The fixed inner guard, fuses and hardware default-off states are part of the build, not optional substitutes for these checks.
