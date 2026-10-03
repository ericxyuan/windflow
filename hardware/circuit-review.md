# Electrical circuit review — E3

Reviewed 2026-10-03 against the selected module documentation and the Pico firmware. This is an analytical/netlist review. No carrier PCB has been routed, manufactured, populated or electrically tested. The physical assembly is therefore not yet an electronics release.

## Concrete corrections made

| Previous issue | Correction retained in E3 | Firmware consequence |
|---|---|---|
| Always-on 5 V servo buffer could drive an unpowered servo | Dedicated BUF3 on the switched servo supply; input/output pulldowns | Same GP8, noninverting |
| 10 nF switch CT with 470 uF reservoir caused about 2.19 A charging current | CT increased to 100 nF; 330 ohm external QOD resistors defined | 50 ms pixel power-up settle |
| Live divider nets and filter charge could reach an unpowered Pico | Three TMUX1511 channels enabled by a 3.3 V supervisor; filter capacitors on source side | No GPIO added |
| Servo divider unnecessarily loaded the internal feedback pot with 20k | 100k upper, 100k lower, 1M ADC-side pulldown | Recalibrate raw position LUT |
| Divider values, passive counts and firmware scales disagreed | Reference-designator netlist; bus scale 11.1, logic scale 2.1 | Current screen/input schema 3 requires recommissioning; voltage scales remain11.1/2.1 |
| Raw PD output drove bulk capacitance without controlled startup | EF1 before reservoir and regulator bank; current limit and OVP | No GPIO added; low-voltage input may leave status dark |
| Fan fuse order code was incorrect; connectors were unspecified sets | Corrected 0451.500MRL and fixed electrical harness quantities/pin order | None |
| TFT BL 2.2k pulldown left 0.60 V during high-impedance reset, above some BSS138 minimum thresholds | R56=1k at the screen; spare BUF2 channel 3 drives BL, with R59=100k GPIO-side pulldown | Same GP16 and noninverting 2 kHz PWM; powered reset drives BL LOW |

The specified Nexperia buffers characterize input leakage with supply at zero; the separate switched supplies remove an always-on buffer output from the servo and pixels. Their outputs are not universally power-off tolerant and must not be driven by another powered source. [Quad buffer](https://assets.nexperia.com/documents/data-sheet/74AHC_AHCT125.pdf), [single buffer](https://assets.nexperia.com/documents/data-sheet/74AHC_AHCT1G125.pdf).

## Voltage and current checks

| Check | Calculation / design result | Practical limit |
|---|---|---|
| Bus ADC at 15 V | 15/11.1 =1.351 V | Calibrate against DMM |
| Bus ADC at 18 V | 18/11.1 =1.622 V | EF1 should already have disconnected above its OVP threshold |
| Logic/servo ADC at 5.25 V | 5.25/2.1 =2.50 V | Below healthy 3.3 V; servo feedback cannot exceed its supply in normal operation |
| ADC disconnected, input still live | Mux source bus divider is 100k/10k; 15 V produces 1.364 V before mux | No stored 100 nF capacitor remains directly on ADC side |
| Supervisor threshold |3.07 V nominal, then 20 ms release delay | Scope rapid collapse/slow ramp to verify sequencing on built board |
| EF1 OVP |1.19×(1+130/10)=16.66 V nominal | About 16.08–17.47 V allowing 1% resistors, reference range and 100 nA leakage; verify trip on bench |
| EF1 UVLO |1.19×(1+100/15)=9.12 V rising | Firmware's 14–16 V and PD check remain stricter operating qualification |
| EF1 current limit |12/8.06=1.489 A | Account for reference and resistor tolerance; not instantaneous disconnect |
| Selected input budget |12.994 W /15 V=0.866 A | At 14 V approximately 0.928 A before efficiency changes, below assumed 1.41 A low current limit |
| REG2 |0.48 A ambient +0.10 A screen +0.15 A housekeeping =0.73 A | Nominal 2.5 A is thermally dependent; screen 100 mA is an allowance |
| Ambient load switch |0.48 A steady; approximately 0.70 A including capacitor ramp | Below 2 A specified DBV operating current under stated conditions; PCB copper and actual startup must be verified |
| Fan |12 V, 0.15 A; fixed voltage buck | Check transient remains below 13.2 V fan maximum |
| Screen CS/RST |Onboard 10k pullups to 5 V VIN; BUF2 provides noninverting 5 V outputs | Never connect the module CS/RST directly to Pico GPIO during 5 V operation |
| Screen BL |Onboard 10k to 3.3 V, R56=1k to GND, BUF2 channel 3 via R55=330 ohm: nominal gate HIGH 3.748 V, ideal LOW 0.0799 V, disconnected output 0.300 V | Conservative BUF2 VOL=0.44 V gives gate about 0.403 V; verify actual off leakage/light, HIGH drive and reset sequencing |

These calculations do not establish a single-fault-certified product. A failed regulator passing its input to a 5 V rail is outside the demonstrated protection claim. Do not infer that a TVS holds the bus to its standoff voltage, or that load-switch thermal shutdown is a current limiter. EF1 monitors input voltage; it is not a separate overvoltage detector on each regulator output.

The [TMUX1511](https://www.ti.com/lit/ds/symlink/tmux1511.pdf) accepts the divided signals while unpowered; SUP1 prevents normal connection until its [3.3 V threshold](https://www.ti.com/lit/ds/symlink/tps3808.pdf) is met. EF1 limits input current and isolates the main reservoir. OVP and slew values above are circuit calculations based on the [TPS26600](https://www.ti.com/lit/ds/symlink/tps2660.pdf), not measured trip accuracy.

## Screen changes and circuit checks

E3 removes the 16-pixel main display and Kingbright status lamp, preserves the 8-pixel ambient chain, and adds an Adafruit 4311 ST7789 IPS screen. The screen is on unswitched REG2 so thermal/guard faults can disable SW3 while retaining visible fault indication when logic power remains available. BL uses GP16, on a separate PWM slice from fan GP6 and servo GP8. GP7 is digital TFT reset.

The current vendor EYESPI schematic shows 10k pullups from CS and RST to VIN. BUF2 is reused on REG2 for those two signals instead of deleting it: each Pico-side input has a 10k pullup to 3.3 V, and the 5 V outputs meet the module's input levels without exposing Pico pins to 5 V. Its third channel drives BL noninverting: A9=GP16 with R59=100k to GND, OE10=GND, Y8 through R55=330 ohm to BL. R56 is **1k**, replacing the earlier 2.2k, at the display end. Adafruit explicitly allows 3–5 V logic at BL. The onboard Q1 is specified only as generic BSS138 in the SOT23-R library device; no manufacturer/orderable-part attribute establishes which transistor is fitted. The library's NXP BSS138PW suggestion is not a fitted-part guarantee and even refers to a different package. [Current schematic](https://github.com/adafruit/Adafruit-2.0-inch-240x320-TFT-PCB/blob/master/Adafruit%20EYESPI%202.0%20Inch%20240x320%20IPS%20TFT.sch), [BL interface](https://learn.adafruit.com/2-0-inch-320-x-240-color-ips-tft-display/pinouts).

The stronger pulldown is justified by a real variant limit: Diodes' BSS138 has minimum VGS(th)=0.5 V at 250 uA, whereas the earlier disconnected gate calculation was 0.60 V. Threshold is not a guaranteed optical-darkness limit, and neither typical curves nor a generic part name prove hot off leakage. A direct 3.3 V GPIO with the new 1k pulldown would give only 2.50 V nominal HIGH and draw 2.42 mA; the spare 5 V buffer improves HIGH margin without changing PWM polarity or loading GPIO with that current. [Diodes BSS138 characteristics](https://www.diodes.com/datasheet/download/BSS138.pdf).

For an ideal buffer output `Vdrv`, the nominal network is `Vgate=(Vdrv/330 +3.3/10000)/(1/330 +1/1000 +1/10000)`. It gives 3.748 V HIGH at Vdrv=5 V, 0.0799 V LOW at Vdrv=0, and 0.300 V with its output disconnected. During normal powered reset R59 holds BUF2 LOW; the 0.300 V result describes a disconnected/high-impedance output, not normal powered reset. BUF2's conservative −40 to +85 C bounds at VCC=4.5 V and an 8 mA test load give minimum VOH=3.8 V and maximum VOL=0.44 V: using those levels yields gate HIGH 2.868 V and LOW 0.403 V with nominal resistors. Assuming 1% for all three resistors and ±2% for the module's 3.3 V, the latter rises to approximately 0.406 V; onboard tolerances must be confirmed before treating that assumption as a bound. The full −40 to +125 C VOL limit of 0.55 V instead gives 0.483 V nominal, reinforcing the need for actual thermal/optical qualification. R59's maximum 0.2 V from 2 uA specified input leakage at 125 C remains below the 0.8 V input-LOW limit. The nominal HIGH path is about 3.79 mA, comfortably below the buffer's characterized 8 mA load; reserve about 19 mW within the existing logic/buffer power allowance. Power-ramp output levels below the buffer's 4.5 V operating range are not guaranteed and require a scope/reset-flash test. [Buffer characteristics and pinout](https://assets.nexperia.com/documents/data-sheet/74AHC_AHCT125.pdf).

R50–54=33 ohm are initial series damping values, not proof of signal integrity. Keep the eight-wire display harness under 150 mm and verify SPI edges, reset, unplugging and white-screen current. The existing 3.3 V Pico regulator supplies only logic inputs, not the screen or backlight load. SDCS is unused and its onboard 10k VIN pullup keeps the unpopulated card slot deselected. The glass needs a clear protective window; no LED diffuser belongs over the visible screen. The old main optical hardware and status lamp are superseded.

## Layout requirements for the 90 x65 x22 mm allowance

The allowance is plausible for the carrier semiconductors, passives and edge connectors, with the Pico, three regulator modules and PD board mounted separately. It has **not** been verified by a PCB placement or CAD collision check. Reserve the whole volume until that verification. Put heavy reservoirs and power connectors at the board edge, and the ADC/dividers away from switch nodes and servo wiring.

Use a professionally fabricated FR4 carrier, preferably four layers with continuous system-ground reference and short high-current loops. EF1 requires an exposed-pad footprint and thermal vias into its isolated RTN copper region; follow TI's thermal layout rather than treating it as a leaded adapter. It is not suitable for a solderless breadboard. Keep all RTN-referenced control parts with EF1. Do not connect that thermal island to the general ground pour.

Required footprint families: TPS26600 PWP16/HTSSOP16 exposed pad; TPS22810 DBV/SOT23-6; TPS3808 DBV/SOT23-6 with its distinct pin mapping; TMUX1511 PW/TSSOP14; Nexperia BUF1/2 SO14 (ambient and display CS/reset/backlight); BUF3 SOT353-1/TSSOP5; 2N7002 SOT23; SMA SS14; SMB TVS; 2410 fuses; 0603 signal passives; 1206 QOD resistors; actual radial capacitor lead pitches; specified through-hole connectors. Verify every manufacturer's land pattern and pin 1 orientation in schematic capture. Do not equate a shared package name with a shared pinout.

## Release checks still required

1. Capture the specified schematic and all reference designators, perform ERC, place/rout the carrier and complete DRC. Compare its board outline and mating plugs to the reserved CAD volume. No unreviewed auto-routing or undersized thermal adapter substitutes.
2. Inspect solder joints, measure every rail and check module PG levels before connecting the Pico or loads. Scope raw/protected PD input, 3.3 V and each switched rail on connection/disconnection.
3. Verify no appreciable phantom supply voltage on servo/LED rails with them disabled and MCU running. Scope ADC pins during slow and abrupt power removal; check the supervisor actually isolates before the MCU rail falls below the signal.
4. Check source behavior with 5 V-only, 9 V, 12 V and correct 15 V PD sources. Verify negotiated current/voltage reporting, disabled loads under an unsupported contract, and recovery without repeated stalled startup.
5. Measure simultaneous full fan, quickest servo movement and full-white ambient plus maximum screen-backlight current/temperature. Test short protection with a current-limited bench supply and isolated dummy loads before any installed harness short test.
6. Verify temperature sensor coupling and trip latency; reported 55/65 C thresholds are sensor-location values, not proof that every IC junction stays below a limit. Check EF1 and SW3 temperatures separately from the regulator cluster.
7. Verify real servo feedback monotonicity, no change in settled angle when its measurement network is attached, jam timeout, opening direction and endpoint travel. Inspect grille interlock while the rotor coasts.

Screen-specific release checks also require readable text at expected desk distance, low night brightness without flicker, correct 320 x240 landscape orientation, no reset flash, and no safety-loop starvation while updating the screen. Every electrical result is currently **not measured**. The fixed inner guard, fuses and hardware default-off states are part of the build, not optional substitutes for these checks.
