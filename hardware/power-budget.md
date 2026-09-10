# USB-C power architecture and budget

Electrical revision E2, 2026-09-09. Selected contract: **USB PD 15 V / 2 A (30 W)**, supplied by the Raspberry Pi 45W USB-C Power Supply, UK Type G, white, with captive cable. Its 15 V / 3 A PDO supports this request. No rechargeable battery is needed for the stated desk use. The small RGB bar indicates system power/service/fault status. [Supply specifications](https://www.raspberrypi.com/products/45w-power-supply/).

| Load | Rail | Continuous design scenario | Electrical upper allowance |
|---|---:|---:|---:|
| Noctua NF-A12x25 G2 | 12 V | 0.15 A / 1.80 W at full PWM | 0.15 A / 1.80 W manufacturer maximum; validate startup pulse |
| Servo | 5 V dedicated | 0.25 A / 1.25 W moving/holding allowance | **1.00 A / 5.00 W** transient/jam allowance; above 0.6 A supplier measurement and 0.8 A family drawing |
| 16 main pixels | 5 V logic/LED | At 36/255 brightness, worst white 0.136 A / 0.678 W | 0.960 A / 4.800 W at unbounded full white |
| 8 ambient pixels | 5 V logic/LED | At 12/255 brightness, worst white 0.023 A / 0.113 W | 0.480 A / 2.400 W at unbounded full white |
| Pico, sensors, buffers, status | 5 V logic allocation | 0.150 A / 0.750 W | 0.150 A / 0.750 W conservative allocation; verify real firmware board current |
| **Total delivered to loads** | | **4.59 W** | **14.75 W** |
| Conversion, assuming only 85% aggregate efficiency | | **5.40 W input** | **17.35 W input** |
| PD/control/quiescent reserve | | 0.20 W | 0.20 W |
| Input eFuse, fuse and wiring reserve | | 0.50 W | 0.50 W |
| **Total input estimate** | 15 V | **6.10 W / 0.407 A** | **18.05 W / 1.203 A** |

The worst allowance includes all pixels full white despite the firmware brightness limits, and servo stall concurrently with full fan and LEDs. The 30 W contract leaves about **11.95 W / 39.8% headroom**. EF1's approximately 1.49 A current limit is a separate lower hardware ceiling; the 1.203 A estimate leaves approximately 0.21 A against a conservative 1.41 A low limit including resistor/tolerance allowance. These are engineering budgets, not measured efficiency or temperature results.

REG2 carries worst 1.44 A LEDs plus 0.15 A housekeeping = **1.59 A**, below the nominal 2.5 A family capability. The cosmetic TPS22810 carries only the 1.44 A LEDs, below its 2 A DBV rating. REG3 and its switch see 1.0 A allowance. REG1 sees only 0.15 A. Use enough copper area and ventilation to maintain these ratings in the closed base. The Pololu continuous rating is thermally dependent, not a guarantee at any ambient temperature. [Regulator details](https://www.pololu.com/product/2858), [switch limits](https://www.ti.com/lit/ds/symlink/tps22810.pdf).

At 85% efficiency, simultaneous worst loads imply approximately **2.6 W conversion heat**, plus the 0.5 W input-path allowance and smaller load-switch losses. Put temperature sensor TEMP1 near the REG2/REG3 hot region, thermally coupled to the board rather than measuring the cold intake stream. Vent the electronics base independently; do not count on the main fan to cool the base after a stall.

The LED color combinations actually used are less demanding than full white. RGB status uses buffered 5 V with 1.5k red and 1k green/blue, approximately 2 mA per die at typical forward voltage; even a shorted die remains resistor-limited. That and sensor current fit inside the 0.15 A housekeeping allocation. Never drive these loads from GPIO supply pins.

## Commissioning measurements

Record input current at cold connection, open-nozzle full speed, fastest servo motion, jam cutoff, full-white LED test, and hot steady state. Use an oscilloscope at Pico VSYS, the servo connector and fan connector while exercising the linkage. Acceptance: no MCU brownout, no unexplained USB renegotiation, regulated fan voltage within 12 V nominal and below 13.2 V fan operating maximum, servo supply near 5 V, and PD input within 14–16 V during enabled operation. Verify fuse inrush coordination instead of raising fuse values after nuisance trips.

The firmware does not measure current directly. EF1 provides input current limiting and controlled startup; its IMON output is unused. Fuses, branch voltage monitoring, temperature and servo feedback provide further protection. EF1 in current-limit/latch mode can limit current before thermal shutdown; it is not an instantaneous disconnect at 1.49 A. Any regulator or switch that reaches its thermal shutdown during normal operation fails the enclosure thermal test.

## Capacitor inrush and sequencing

Each 470 uF output reservoir with TPS22810 CT=100 nF has estimated charging current `Cload × 46.62/Ct = 0.219 A`, using Ct in pF and consistent time units. The previous 10 nF value gave about 2.19 A before adding load current. The calculated full 5 V ramp is about 10.7 ms; firmware now waits 50 ms before pixel data. The theoretical LED branch demand during charging plus a full-white load is about 1.66 A; use an oscilloscope to verify because load startup and CT tolerance are not ideal capacitors. [Switch slew model](https://www.ti.com/lit/ds/symlink/tps22810.pdf).

EF1 C29=100 nF gives approximately 12 ms initial 15 V ramp from TI's relation `t=8000×Vin×C`. Only C1=100 nF is added on the raw side; C2 and the regulator input capacitance are behind EF1. Sum actual module input capacitance and measure USB connection current rather than claiming USB compliance from this estimate. R39–41=330 ohm QOD resistors limit discharge heating; the output may take hundreds of milliseconds to discharge, so magnetic grille release still needs a fixed inner guard. [Input eFuse data](https://www.ti.com/lit/ds/symlink/tps2660.pdf).
