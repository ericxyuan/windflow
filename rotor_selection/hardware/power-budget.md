# USB-C power architecture and budget

**Rev B historical budget.** The active [Rev C calculation](../docs/rev-c-motor-power.md) requires 15 V / 3 A USB PD (45 W), revised protection and a capped ESC branch. The 2 A request and 12 V fan rail below are not the current motor architecture.

Electrical revision E3, 2026-10-03. Selected contract: **USB PD 15 V / 2 A (30 W)**, supplied by the Raspberry Pi 45W USB-C Power Supply, UK Type G, white, with captive cable. Its 15 V / 3 A PDO supports this request. No rechargeable battery is needed for the stated desk use. The reserved top section of the IPS screen indicates system power/service/fault status. [Supply specifications](https://www.raspberrypi.com/products/45w-power-supply/).

| Load | Rail | Continuous design scenario | Electrical upper allowance |
|---|---:|---:|---:|
| Noctua NF-A12x25 G2 | 12 V | 0.15 A / 1.80 W at full PWM | 0.15 A / 1.80 W manufacturer maximum; validate startup pulse |
| Servo | 5 V dedicated | 0.25 A / 1.25 W moving/holding allowance | **1.00 A / 5.00 W** transient/jam allowance; above 0.6 A supplier measurement and 0.8 A family drawing |
| Adafruit 4311 IPS screen | 5 V logic | **0.100 A / 0.500 W** reserved even with dimmed backlight | **0.100 A / 0.500 W engineering allowance**, not a manufacturer maximum; measure the actual board |
| 8 ambient pixels | 5 V logic/LED | At 12/255 brightness, worst white 0.0226 A /0.113 W |0.480 A /2.400 W at unbounded full white |
| Pico, sensors and buffers | 5 V logic allocation |0.150 A /0.750 W |0.150 A /0.750 W conservative allocation; verify real firmware board current |
| **Total delivered to loads** | | **4.413 W** | **10.450 W** |
| Conversion, assuming only 85% aggregate efficiency | | **5.192 W input** | **12.294 W input** |
| PD/control/quiescent reserve | |0.20 W |0.20 W |
| Input eFuse, fuse and wiring reserve | |0.50 W |0.50 W |
| **Total input estimate** |15 V | **5.892 W /0.393 A** | **12.994 W /0.866 A** |

The E3 screen replaces the 16 main pixels and discrete RGB status lamp; the 8 downward ambient pixels remain. The upper allowance includes full-white ambient pixels and servo jam concurrently with full fan and screen. The 30 W contract leaves about **17.01 W /56.7% headroom**. EF1's approximately 1.49 A current limit remains a lower hardware ceiling; the 0.866 A estimate leaves about 0.54 A against a conservative 1.41 A low limit including resistor/tolerance allowance. These are engineering budgets, not measured efficiency or temperature results. A screen drawing more than its 100 mA allowance requires revising the budget before release.

REG2 carries worst 0.48 A ambient +0.10 A screen +0.15 A housekeeping = **0.73 A**, below the nominal 2.5 A family capability. The ambient TPS22810 carries only 0.48 A steady pixels. REG3 and its switch see 1.0 A allowance. REG1 sees 0.15 A. The screen and its CS/reset/backlight buffer are powered directly from REG2, allowing fault indication while SW3 shuts down decorative lighting. The new BUF2 backlight channel supplies about **3.79 mA /19.0 mW** with HIGH continuously asserted into R55=330 ohm, R56=1k and the onboard 10k pullup. That conservative DC load is included within the existing 150 mA /0.75 W Pico/sensor/buffer allocation, so it is not added again to the screen allowance. At the maximum allowed 80/255 PWM duty its HIGH-path average is about 6 mW before buffer switching/quiescent current, which also remains in that allocation. No display or LED power flows through GPIO. Use enough copper area and ventilation to maintain ratings in the closed base; Pololu's continuous rating is thermally dependent. [Regulator details](https://www.pololu.com/product/2858), [switch limits](https://www.ti.com/lit/ds/symlink/tps22810.pdf), [screen power and backlight interface](https://learn.adafruit.com/2-0-inch-320-x-240-color-ips-tft-display/pinouts).

At 85% efficiency, simultaneous upper loads imply approximately **1.84 W conversion heat**, plus the 0.5 W input-path allowance and smaller load-switch losses. Put TEMP1 near the REG2/REG3 hot region, thermally coupled to the board rather than measuring cold intake air. Vent the electronics base independently; the main fan cannot be assumed to cool the base after a stall. Screen backlight dimming reduces actual draw, but this budget conservatively reserves 100 mA in both columns.

## Commissioning measurements

The5 October guard correction adds a nominal1.282 mA closed-contact path from unswitched5 V (6.41 mW), plus BUF4's at-most10 uA quiescent current and the33 uA GP15 pullup when LOW. These remain within the150 mA housekeeping allowance and are not added twice to the totals. Verify the contact load and buffer sequencing on the captured circuit before hardware operation; this analytical allowance is not a bench result.

Record input current at cold connection, open-nozzle full speed, fastest servo motion, jam cutoff, full-white ambient test, screen at maximum allowed backlight, and hot steady state. Use an oscilloscope at Pico VSYS, the servo connector and fan connector while exercising the linkage. Acceptance: no MCU brownout, no unexplained USB renegotiation, regulated fan voltage within 12 V nominal and below 13.2 V fan operating maximum, servo supply near 5 V, and PD input within 14–16 V during enabled operation. Verify fuse inrush coordination instead of raising fuse values after nuisance trips.

The firmware does not measure current directly. EF1 provides input current limiting and controlled startup; its IMON output is unused. Fuses, branch voltage monitoring, temperature and servo feedback provide further protection. EF1 in current-limit/latch mode can limit current before thermal shutdown; it is not an instantaneous disconnect at 1.49 A. Any regulator or switch that reaches its thermal shutdown during normal operation fails the enclosure thermal test.

## Capacitor inrush and sequencing

Each 470 uF output reservoir with TPS22810 CT=100 nF has estimated charging current `Cload × 46.62/Ct = 0.219 A`, using Ct in pF and consistent time units. The previous 10 nF value gave about 2.19 A before adding load current. The calculated full 5 V ramp is about 10.7 ms; firmware now waits 50 ms before pixel data. The theoretical ambient branch demand during charging plus a full-white load is about 0.70 A; use an oscilloscope to verify because load startup and CT tolerance are not ideal capacitors. [Switch slew model](https://www.ti.com/lit/ds/symlink/tps22810.pdf).

EF1 C29=100 nF gives approximately 12 ms initial 15 V ramp from TI's relation `t=8000×Vin×C`. Only C1=100 nF is added on the raw side; C2 and the regulator input capacitance are behind EF1. Sum actual module input capacitance and measure USB connection current rather than claiming USB compliance from this estimate. R39–41=330 ohm QOD resistors limit discharge heating; the output may take hundreds of milliseconds to discharge, so magnetic grille release still needs a fixed inner guard. [Input eFuse data](https://www.ti.com/lit/ds/symlink/tps2660.pdf).
