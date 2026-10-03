# Windflow prototype BOM — selected architecture, not an enclosure release

Updated 2026-10-03, electrical revision E2. Quantities of mounting hardware remain provisional until the final CAD fastener schedule is frozen. Manufacturer ratings and engineering allowances are distinguished below. No components have been purchased. The electrical population below is fixed for the documented prototype netlist; a **90 x 65 x 22 mm carrier allowance is not a finished PCB**. See [circuit review](circuit-review.md) and [electronics assembly](../docs/electronics-assembly.md).

## Major electrical and electromechanical components

| Ref / qty | Manufacturer / exact model | Function, interface and supply | Size / current / selection reason |
|---|---|---|---|
| FAN1 / 1 | **Noctua NF-A12x25 G2 PWM**, EAN 9010018100686 | 12 V, four-wire, 25 kHz PWM, two tach pulses/rev | 120 x 120 x 25 bare, 27 mm with pads; 105 mm mounting pitch. Max 0.15 A / 1.8 W, 1800 rpm, 107.3 m3/h free delivery, 3.14 mmH2O shutoff; these endpoints are not simultaneous. Quiet, pressure-capable, continuous duty. [Manufacturer](https://www.noctua.at/en/products/nf-a12x25-g2-pwm/specifications). |
| MCU1 / 1 | **Raspberry Pi Pico SC0915**, RP2040, unheadered | 3.3 V GPIO; VSYS from 5 V via SS14; native USB service, I2C, ADC, PWM/PIO | PCB 51 x 21; full CAD 52.3 long with USB overhang. Allocate 0.15 A at 5 V to MCU plus sensors/status, not a claimed maximum board rating. Hardware-timed fan/servo and LED output. [Documentation](https://www.raspberrypi.com/documentation/microcontrollers/pico-series.html). |
| SERVO1 / 1 | **FEETECH FS90-FB**, **Pololu 3436** | 5 V regulated; 50 Hz RC PWM plus analog position feedback fourth wire | Case 23.2 x 12.5 x 22; family drawing 32.6 overall lug span, 27 lug centres, 27.3 body-to-spline top, horn extra. 1.3 kgf-cm at 4.8 V; Pololu measured 0.6 A stalled at 6 V, related family drawing lists 0.8 A: budget **1.0 A** including uncertainty/transient. Feedback permits jam detection. Backorder shown during research; source exact FB variant before mount release. [Supplier specification](https://www.pololu.com/product/3436/specs). |
| ENC1 / 1 | **Bourns PEC11H-4215F-S0024** | Passive quadrature contacts, 24 pulses / 24 detents, momentary push | 11.8 mm body width, 6 mm D-shaft, 15 mm from mounting face, M7 x 0.75 bushing. Contact limit 10 mA / 5 V; use 3.3 V / 10k pullups. High detent force, nominal 0.0206 Nm and 100k rotations; switch force nominal about 6 N means a well-supported wheel and stable base are required. [Datasheet](https://www.bourns.com/docs/product-datasheets/pec11h.pdf). |
| LED1–3 / 3 | **Adafruit 1426 NeoPixel Stick**, 8 RGB pixels each | 5 V, 800 kHz GRB addressable; two chained for main bar, one downward ambient | Design for 51.10 x 10.22 x 3.19 each; CAD is smaller. Budget 60 mA per pixel = 0.48 A each full white; normal brightness is much lower. Current lot may be WS2812B/SK6812 compatible. [Product](https://www.adafruit.com/product/1426). |
| LED4 / 1 | **Kingbright WP154A4SUREQBFZGC** | Common-cathode RGB status lamp, three buffered on/off signals | 5 mm lens, 5.9 mm flange, 8.6 mm body length; under 7 mA total using specified resistors at 5 V. Illuminate a short 22 x 4 mm diffuser bar. Pin 2 cathode; 1 red, 3 blue, 4 green. [Datasheet](https://www.kingbrightusa.com/images/catalog/spec/WP154A4SUREQBFZGC.pdf). |
| TEMP1,2 / 2 | **Adafruit 1782 MCP9808 breakout**, Microchip MCP9808 | 3.3 V I2C, 0x18 / 0x19 (A0 high on second) | Non-STEMMA board, manufacturer rounded size 21 x 13 x 2; CAD 20.32 x 12.7 x 3.07. Two 2.5 mm holes, 15.24 mm pitch. Reserve 21.6 x 13.6 x 3.7. Manufacturer says the 2023 revision changed silkscreen only; product 5027 is the different STEMMA board. Chip roughly 0.2 mA typical active; allocate 1 mA each. Sense regulator region and base air; characterize lag. [Product and revision history](https://www.adafruit.com/product/1782). |
| DP1 / 1 | **Sensirion SDP810-125Pa**, order **1-101597-01** | 3.3 V, I2C 0x25; two pressure tubes | 29 x 18 x 27.05, maximum 5.5 mA. +/-125 Pa, low-pressure resolution suited to a 31 Pa fan. Adds meaningful restriction sensing because regulated RPM is not airflow. [Manufacturer](https://sensirion.com/products/catalog/SDP810-125Pa). |
| PD1 / 1 | **Adafruit 5807 HUSB238 USB-C PD sink** | Configure jumpers **15 V / 2 A**; I2C 0x08 reports contract | PCB/USB about 24.6 x 20.3; supplied terminal block reaches 12.1 mm overall height in CAD. Request fixed PDO; verify measured bus and negotiated current before enabling loads. [Guide](https://learn.adafruit.com/adafruit-husb238-usb-type-c-power-delivery-breakout/pinouts). |
| REG1 / 1 | **Pololu D24V22F12 #2855** | 15 V to 12 V fan rail; PG to MCU | 17.8 square, allow 9 high. Typical max 2.2 A at stated test conditions; our load is 0.15 A. Fixed voltage avoids accidental fan overvoltage. [Product](https://www.pololu.com/product/2855). |
| REG2,3 / 2 | **Pololu D24V22F5 #2858** | REG2 5 V logic/LED; REG3 separate 5 V servo | Same footprint, nominal max 2.5 A; REG2 worst 1.59 A including logic, REG3 1.0 A allowance. Check hot-enclosure derating. 5.3–36 V input for the 5 V version; output requires dropout headroom. [Product](https://www.pololu.com/product/2858). |
| SW1–3 / 3 | **Texas Instruments TPS22810DBVR** | High-side load disconnect on fan 12 V, servo 5 V, cosmetic LED 5 V | SOT23-6; 2.7–18 V operating, 2 A DBV continuous subject to thermal layout. 3.3 V enable, 100k pulldown; defaults off. Thermal shutdown is not a precision current limiter. [Datasheet](https://www.ti.com/lit/ds/symlink/tps22810.pdf). |
| BUF1,2 / 2 | **Nexperia 74AHCT125D,118** | BUF1 main/ambient data on switched LED rail; BUF2 status only on logic rail | SO14, 8.65 x 3.9 body, 6 mm lead span. TTL inputs, specified input leakage with VCC=0. Do not substitute generic HC/AHC buffers. [Datasheet](https://assets.nexperia.com/documents/data-sheet/74AHC_AHCT125.pdf). |
| BUF3 / 1 | **Nexperia 74AHCT1G125GW,125** | Noninverting GP8 servo buffer, powered from **switched servo 5 V** | TSSOP5/SOT353-1, 2 x 1.25 mm body. Removes the always-powered signal path into an unpowered servo. [Manufacturer](https://www.nexperia.com/products/analog-logic-ics/logic/buffers-inverters-transceivers/buffers/74AHCT1G125GW.html). |
| ISO1 / 1 | **Texas Instruments TMUX1511PWR** | Three ADC signal isolators; fourth channel unused | TSSOP14, 5 x 4.4 mm body; 3.3 V, up to 70 uA supply. Powered-off protection covers the divided signals. [Datasheet](https://www.ti.com/lit/ds/symlink/tmux1511.pdf). |
| SUP1 / 1 | **Texas Instruments TPS3808G33DBVR** | Holds ADC isolation off until 3.3 V is healthy | SOT23-6, 2.9 x 1.6 mm body; 3.07 V nominal threshold, CT open gives 20 ms nominal release delay. No extra GPIO. [Datasheet](https://www.ti.com/lit/ds/symlink/tps3808.pdf). |
| EF1 / 1 | **Texas Instruments TPS26600PWPR** | Input inrush control, current limiting, OVP and reverse-current blocking before the regulator bank | HTSSOP16 with thermal pad, 5 x 4.4 mm body; 4.2–60 V input, 150 milliohm typical. Netlist sets about 1.49 A limit and 16.66 V OVP. Requires a soldered thermal pad and PCB copper. [Datasheet](https://www.ti.com/lit/ds/symlink/tps2660.pdf). |
| PSU1 / 1 | **Raspberry Pi 45W USB-C Power Supply, UK Type G, white** | External supply; captive 1.5 m USB-C cable, 15 V / 3 A PDO available; device requests 2 A | Approximately 56 x 52 x 36 mm body excluding plug. Exact regional/color model is specified; confirm distributor SKU at order. The 27 W version has only 15 V / 1.8 A and is unsuitable for this configured 2 A request. [Manufacturer](https://www.raspberrypi.com/products/45w-power-supply/). |
| Q1 / 1 | **Nexperia 2N7002,215** | Open-drain inverter between fan PWM pin and ground | SOT23, 60 V VDS; PWM input only, not motor supply. Fan input sources at most 5 mA. Gate 100 ohm series and 100k pulldown. [Manufacturer](https://www.nexperia.com/product/2N7002). |
| GUARD1 / 1 | **Omron D2F-01L** | Guard-present SPDT switch; use COM/NO so installed guard closes to ground | Body approximately 12.8 x 5.8 x 6.5 plus lever and pins; mounting per drawing. Low-level gold contacts. Removable grille interruption stops loads; fixed inner guard still required. [Datasheet](https://components.omron.com/sites/default/files/datasheet_pdf/B036-E1.pdf). |

## Power protection, connectors and passives

All resistors are 1%, unless noted. Quantities are populated quantities, not reel purchase quantities. Breakout-board onboard passives are included with those products and are not counted again. Reference designators are defined in [wiring.md](wiring.md). Do not fabricate from this BOM alone; the carrier needs schematic capture, ERC, layout and DRC.

| Ref / quantity | Exact manufacturer part | Value / use |
|---|---|---|
| F1 / 1 | Littelfuse **0451002.MRL** | 2 A input fuse, before EF1 |
| F2 / 1 | Littelfuse **0451.500MRL** | 0.5 A fan branch fuse; corrected order code |
| F3 / 1 | Littelfuse **0451001.MRL** | 1 A servo branch fuse |
| D1 / 1 | Littelfuse **SMBJ18A** | Input TVS, cathode fused raw PD+, anode GND; transient suppression, not DC voltage regulation |
| D2 / 1 | Vishay **SS14-E3/61T** | REG2 anode to Pico VSYS cathode; service-USB isolation |
| C2,C6–8 / 4 | Panasonic **EEU-FR1E101** | 100 uF / 25 V: protected input bus and three regulator outputs |
| C9,C10 / 2 | Panasonic **EEU-FR1A471** | 470 uF / 10 V: switched servo and cosmetic LEDs |
| C3–5,C11–13 / 6 | Murata **GRM188R71E105KA12D** | 1 uF / 25 V X7R 0603: three regulator inputs, three load-switch inputs; check effective capacitance at DC bias |
| C1,C14–25,C29 / 14 | Murata **GRM188R71H104KA93D** | 100 nF / 50 V X7R 0603: raw input, switch CT, buffers, isolator, supervisor, pressure connector, ADC filters, EF1 slew |
| C26–28 / 3 | Murata **GRM188R71C103KA01D** | 10 nF / 16 V X7R 0603: encoder A/B/push |
| R10–12,R14,R18–24,R28,R31–32,R34–35,R38,R44 / 18 | Yageo **RC0603FR-07100KL** | 100k: pulldowns, dividers and EF1 UVLO |
| R1–3,R29,R37,R47 / 6 | Yageo **RC0603FR-0710KL** | 10k: encoder pullups, bus lower divider, supervisor pullup, EF1 OVP lower |
| R4–5,R8–9 / 4 | Yageo **RC0603FR-074K7L** | 4.7k: tach, guard, two PG pullups |
| R6–7 / 0 fitted, 2 available | Yageo **RC0603FR-074K7L** | Optional I2C pullups; populate only after measuring combined breakout pullups |
| R30,R33,R36 / 3 | Yageo **RC0603FR-071ML** | 1M: ADC-side pulldowns after ISO1 |
| R13 / 1 | Yageo **RC0603FR-07100RL** | 100 ohm: fan PWM gate |
| R15–17 / 3 | Yageo **RC0603FR-07330RL** | 330 ohm: LED data and servo PWM series |
| R25 / 1 | Yageo **RC0603FR-071K5L** | 1.5k: status red |
| R26–27 / 2 | Yageo **RC0603FR-071KL** | 1k: status green/blue |
| R39–41 / 3 | Yageo **RC1206FR-07330RL** | 330 ohm, 0.25 W, 1206: load-switch QOD resistors |
| R42 / 1 | Yageo **RC0603FR-078K06L** | 8.06k: EF1 current limit |
| R43 / 1 | Yageo **RC0603FR-07402KL** | 402k: EF1 current-limit/latch mode |
| R45 / 1 | Yageo **RC0603FR-0715KL** | 15k: EF1 UVLO lower |
| R46 / 1 | Yageo **RC0603FR-07130KL** | 130k: EF1 OVP upper |
| J1,J12 / 2 each | JST **B2B-XH-A(LF)(SN)** and **XHP-2** | PD power and guard harnesses |
| J2,J6,J7 / 3 each | JST **B3B-XH-A(LF)(SN)** and **XHP-3** | PD I2C, main LEDs, ambient LEDs |
| J8–11,J13 / 5 each | JST **B4B-XH-A(LF)(SN)** and **XHP-4** | Encoder, two temperature boards, pressure sensor and RGB status |
| 33 installed; buy 40 | JST **SXH-001T-P0.6** | One crimp per XH housing cavity above; 22–28 AWG per JST tooling/specification |
| J3 / 1 | Molex **470531000** | Keyed four-pin fan header, preserves original fan connector; [drawing](https://www.molex.com/content/dam/molex/molex-dot-com/products/automated/en-us/salesdrawingpdf/470/47053/470531000_sd.pdf) |
| J4 / 1 | Samtec **TSW-103-07-G-S** | Servo's original three-pin plug; add printed retention and polarity marking |
| J5 / 1 | Samtec **TSW-101-07-G-S** | Servo's original single feedback socket; retain alongside J4 |
| J14 / 1 each | Samtec **TSW-102-07-G-S**, **SNT-100-BK-G** | Recessed service jumper |
| 3 | Samtec **SSW-105-02-G-S** | Regulator sockets; modules include male header; label all five nets |
| 2 each | Samtec **SSW-120-02-G-S**, **TSW-120-07-G-S** | Removable Pico socket/header rows |
| 1 fabricated | SDP810 daughterboard, **18 x 12 x 1.6 mm**, four 0.8 mm plated holes at **2 mm pitch** | Sensor soldered directly; two M2 PCB holes and independent housing screws take harness/tubing loads. The earlier 2.54 mm socket was incompatible. The reviewed 2 mm sockets also needed more insertion depth than the sensor's shortest allowed pins. |
| 2 x 150 mm initial | **Tygon S3 E-3603**, 2 mm ID / 4 mm OD | Equal short pressure tubes; fit must be verified on actual nipples |
| 2 m power, 3 m signal initial | **Alpha Wire 3051** 22 AWG stranded, **3050** 24 AWG stranded | Use red/black for power, identifiable signal colors; cut list follows installed routing, keep spare service length |
| 1 fabricated set | Windflow E2 main carrier + encoder daughterboard + SDP soldered daughterboard | FR4, plated through holes; mechanical interfaces exist, **PCB design files are not yet released** |

The above is a complete electrical population for E2. It does not imply that every MPN is currently in stock. Use authorized distributors and confirm the orderable packaging suffix and board revision. The regional/color power-supply model is selected but its distributor-specific stock code remains to be recorded at purchase. Connector numbering is electrical, not a claim about an existing PCB silkscreen.

## Mechanical bought parts and printing materials

| Qty initial | Part | Use / limits |
|---|---|---|
| 8 | **K&J Magnetics D42**, N42 axial disc, 6.35 diameter x 3.175 mm | Four opposing pairs; 6.55 diameter x 3.40 mm test pockets. Vendor zero-gap pull force is not the assembled force through printed skins. [Product](https://www.kjmagnetics.com/d42-neodymium-disc-magnet). |
| 24 | **ruthex RX-M3x5.7** heat-set inserts | 5.7 long, manufacturer hole guidance plus test coupon. Initial 4.0 mm pilot / 6.8 mm depth must be confirmed with actual insert/material. [Product](https://www.ruthex.de/products/ruthex-gewindeeinsatz-m3-100-stuck-rx-m3x5-7-messing-gewindebuchsen). |
| 16 / 8 / 4 | **ISO 4762 A2-70 M3x8 / M3x12 / M3x35** socket head screws | Enclosure, carrier and fan mounts; final lengths selected after stack is measured, never bottom screws in inserts |
| 32 / 8 | **ISO 7089 A2 M3 washers / ISO 10511 A2 M3 nyloc nuts** | Mechanical joints and through-bolt mounting |
| 8 | **ISO 4762 A2-70 M2x8** + matching **ISO 4032 M2** nuts | Regulator boards and servo mounting, subject to actual lug hole verification |
| 2 | **Stainless steel ground rod, 3 mm diameter, cut to 155 mm**, deburred | Full-width boost-panel hinge shafts, installed X=-60.5..94.5 mm. Confirm sliding fit with bore coupon. |
| 4 | **Mädler 62300300**, DIN 705 A shaft collar, 3 mm bore, 7 mm OD, 5 mm width, supplied M2x3 set screw | One collar at each shaft end; accessible with linkage cover removed. |
| 2 | Stainless tube **7 mm OD / 3.3 mm ID**, cut to **7.6 mm** | Right-side hinge spacers, installed X=77.2..84.8 mm. Deburr square. |
| 4 | Stainless tube **3 mm OD / 2.1 mm ID**, cut **2 x 9.1 mm, 1 x 9.6 mm, 1 x 8.6 mm** | Crank/yoke, rod/yoke and horn/rod pivot sleeves; screws clamp the metal stacks, allowing printed parts to rotate. |
| 4 sets | **Accu SSC-M2-14-A2** cap screws, **HNN-M2-A2** nyloc nuts, **HPW-M2-A2** plain washers | Four sleeved pivots. CAD uses washer maximum **0.35 mm** and nut maximum **2.8 mm**; minimum one 0.4 mm thread pitch protrusion. Verify supplied dimensions. |
| 2 sets | **ISO 4762 A2 M2x16**, **ISO 10511 M2 nyloc nut**, M2 washers | Split keyed crank clamps; tighten with shaft installed and confirm no binding. |
| 2 / 2 sets | **ISO 4762 A2 M2x20 / M2x6**, matching **ISO 4032 M2** nuts | SDP810 housing / daughterboard mounts, plus two 0.4 mm washers on housing screws. |
| 4 sets | **ISO 4762 A2 M2x14**, **ISO 4032 M2** nuts and 0.4 mm washers | Two mounts per Adafruit 1782 temperature board. |
| 4 | Stainless spacer tube **4 mm OD / 3.2 mm ID**, cut to measured fan mount stack | Compression limiter around M3 bolts; never preload/crush the fan frame with TPU |
| 1 set | Included FEETECH 20T servo horn and retaining screw | Use real splined horn; bolt printed crank adapter to horn |
| as needed | **3M Scotch-Weld DP100 Plus Clear** epoxy | Magnet adhesive space plus mechanical cover; keep adhesive away from rotor/hinges |
| 1 spool | **Prusament PETG** (structural parts), dry before printing | 0.4 mm nozzle; avoid PLA near regulators and sustained clamp load |
| 1 spool | **BASF Ultrafuse TPU 95A** | Replaceable fan pads/bushings and desk feet; characterize compression/set |
| small amount | Natural translucent PETG | LED diffusers; print thickness coupons rather than assume transmission |

The mechanical table is an initial purchasing allowance, not an exact released assembly fastener count. Hinge-linkage bearings, gears or return spring depend on the final verified CAD and kinematics. Do not substitute a guessed spring into the assembled system; it may overload or fail to backdrive the servo.
