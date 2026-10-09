# Rev C wiring and pin assignments — 8 October2026

The source of these tables is the checked [native circuit population](../pcb/rev_c/circuit-population.json). Use the [complete10-sheet schematic](../pcb/rev_c/windflow-rev-c-schematic.pdf) for component pins and protection. This describes the electrical connections; the main PCB and complete installed loom are still under development. Rev B25kHz fan control and its keyed Pico cable are incompatible with Rev C.

## Power path

USB-C15V3A contract → Adafruit5807 → J1/F1 → reverse-blocking CSD19537Q3/TPS26630 EF1 → protected15V bus. The ESC path adds F2 and default-off EF2, then J20 → suppliedXT30 → A50S. The three motor phases use the suppliedMR30 pair. Two D24V22F5 modules supply independent5V logic and servo rails. The servo and ambient rails have their own controlled switches. All returns join system ground. No load current runs through Pico GPIO or the Pico ribbon. The ESC BEC and3.3V outputs are insulated and unconnected.

Use22AWG for the protected power/5V branches and26AWG for signals. Keep phase leads apart from UART, I2C and ADC wiring. Use the included ESC loom for its20-cavity interface; only vendor-labelledGND,TX,RX are connected. Cavity numbers are not inferred from an unnumbered drawing. UART TX/RX cross, with a nearby ground return and a maximum150mm signal route. C38/C39/D3/R80 are at the ESC end behind the gate; C30/R56 are at the screen end.

## Removable cable connectors

Pin numbers below are the PCB footprint numbers. Determine the actual latch/pin1 view from the manufacturer drawing before crimping; do not copy a mirror image seen from the wire entry. All unused contacts remain unconnected.

| Board connector | Selected board part | Pin-to-net assignment |
|---|---|---|
| J1 | JST B2B-XH-A(LF)(SN) | 1 PD_RAW, 2 GND |
| J18 | Molex 43045-0412 | 1 GND, 2 BUS_PROTECTED, 3 REG5_LOGIC, 4 NC |
| J19 | Molex 43045-0812 | 1 GND, 2 BUS_PROTECTED, 3 REG5_SERVO, 4 PG_SERVO, 5 NC, 6 NC, 7 NC, 8 NC |
| J4 | Samtec TSW-103-07-G-S | 1 GND, 2 SERVO5_SWITCHED, 3 SERVO_SIGNAL |
| J5 | Samtec TSW-101-07-G-S | 1 SERVO_FEEDBACK_RAW |
| J7 | JST B3B-XH-A(LF)(SN) | 1 GND, 2 AMBIENT5_SWITCHED, 3 AMBIENT_DATA |
| J2 | JST B3B-XH-A(LF)(SN) | 1 GND, 2 I2C_SDA, 3 I2C_SCL |
| J8 | JST B4B-XH-A(LF)(SN) | 1 GND, 2 ENC_A, 3 ENC_B, 4 ENC_PUSH |
| J9 | JST B4B-XH-A(LF)(SN) | 1 GND, 2 +3V3, 3 I2C_SDA, 4 I2C_SCL |
| J10 | JST B4B-XH-A(LF)(SN) | 1 GND, 2 +3V3, 3 I2C_SDA, 4 I2C_SCL |
| J11 | JST B4B-XH-A(LF)(SN) | 1 GND, 2 +3V3, 3 I2C_SDA, 4 I2C_SCL |
| J12 | JST B2B-XH-A(LF)(SN) | 1 GND, 2 GUARD_CONTACT_5V |
| J14 | Samtec TSW-102-07-G-S | 1 GND, 2 SERVICE_JUMPER |
| J6 | JST B8B-XH-A(LF)(SN) | 1 REG5_LOGIC, 2 GND, 3 TFT_MOSI, 4 TFT_SCK, 5 TFT_CS, 6 TFT_DC, 7 TFT_RST, 8 TFT_BL |
| J20 | Molex 43045-0212 | 1 GND, 2 ESC_15V |
| J22 | JST B3B-XH-A(LF)(SN) | 1 GND, 2 UART_TO_ESC_RX, 3 UART_FROM_ESC_TX |
| J21 (DNP) | JST B3B-XH-A(LF)(SN) | 1 GND, 2 +3V3, 3 OPTICAL_RPM |

J8 mates the encoder daughterboard J1, pin1GND/pin2A/pin3B/pin4PUSH. J9/J10 go to the MCP9808 breakouts at0x18 and0x19; J11 goes to the SDP810 daughterboard at0x25. J2 carries GND/SDA/SCL to the already powered HUSB238 board. J12 goes to Omron COM/NO; insulate NC. Its raw contact is5V, translated before GP15. The FEETECH supplied servo plug goes to J4; the separate feedback wire goes to J5. Confirm real lead colors/positions against the supplied servo.

## Pico physical pins and ribbon mapping

J15/J16 are keyed2×10 headers with all20 contacts. Connector pin n maps to Pico physical n for J15 and n+20 for J16. These mappings require a purpose-built Pico-side transition and strain relief; they are not a direct mechanical plug into the Pico1×20 rows. That transition is unfinished design work. Label the two looms separately and continuity-test all40 contacts before applying power.

| Pico physical pin | Pico function | Carrier connector | Net / use |
|---:|---|---|---|
| 1 | GP0 | J15.1 | ENC_A — Encoder A |
| 2 | GP1 | J15.2 | ENC_B — Encoder B |
| 3 | GND | J15.3 | GND |
| 4 | GP2 | J15.4 | ENC_PUSH — Encoder push |
| 5 | GP3 | J15.5 | OPTICAL_RPM — Optional optical RPM; unpopulated/untrusted |
| 6 | GP4 | J15.6 | I2C_SDA — I2C SDA |
| 7 | GP5 | J15.7 | I2C_SCL — I2C SCL |
| 8 | GND | J15.8 | GND |
| 9 | GP6 | J15.9 | ESC_POWER_REQUEST — ESC power request to hardwired guard AND |
| 10 | GP7 | J15.10 | TFT_RST_GPIO — Screen reset |
| 11 | GP8 | J15.11 | SERVO_PWM_GPIO — Servo50Hz PWM |
| 12 | GP9 | J15.12 | EN_SERVO — Servo supply enable |
| 13 | GND | J15.13 | GND |
| 14 | GP10 | J15.14 | TFT_DC_GPIO — Screen DC |
| 15 | GP11 | J15.15 | AMBIENT_DATA_GPIO — Ambient addressable data |
| 16 | GP12 | J15.16 | UART_TX_GPIO — UART0TX to ESC RX via BUF5 |
| 17 | GP13 | J15.17 | UART_RX_GPIO — UART0RX from ESC TX via BUF5 |
| 18 | GND | J15.18 | GND |
| 19 | GP14 | J15.19 | EN_AMBIENT — Ambient supply enable |
| 20 | GP15 | J15.20 | GUARD_LOGIC_3V3 — Grille contact; LOW means present |
| 21 | GP16 | J16.1 | TFT_BL_GPIO — Screen backlight |
| 22 | GP17 | J16.2 | SERVICE_JUMPER — Service shunt |
| 23 | GND | J16.3 | GND |
| 24 | GP18 | J16.4 | TFT_SCK_GPIO — Screen SPI SCK |
| 25 | GP19 | J16.5 | TFT_MOSI_GPIO — Screen SPI MOSI |
| 26 | GP20 | J16.6 | TFT_CS_GPIO — Screen CS |
| 27 | GP21 | J16.7 | PG_SERVO — Servo branch PGOOD |
| 28 | GND | J16.8 | GND |
| 29 | GP22 | J16.9 | PG_ESC — ESC branch PGOOD |
| 30 | RUN | J16.10 | NC |
| 31 | GP26/ADC0 | J16.11 | ADC_BUS — Protected bus ADC; divider11.1 |
| 32 | GP27/ADC1 | J16.12 | ADC_SERVO_FEEDBACK — Servo feedback ADC; divider2.1 |
| 33 | AGND | J16.13 | GND |
| 34 | GP28/ADC2 | J16.14 | ADC_LOGIC — Logic5V ADC; divider2.1 |
| 35 | ADC_VREF | J16.15 | NC |
| 36 | 3V3_OUT | J16.16 | +3V3 |
| 37 | 3V3_EN | J16.17 | NC |
| 38 | GND | J16.18 | GND |
| 39 | VSYS | J16.19 | PICO_VSYS |
| 40 | VBUS | J16.20 | NC |

RUN,ADC_VREF,3V3_EN andVBUS stay unconnected at this carrier. Pico VSYS is diode-fed from the logic regulator; 3V3_OUT powers3.3V buffers/sensors. Powered USB programming must be checked for backfeed through the finished circuit.

## Commissioning sequence

1. Leave the motor/impeller disconnected. Check every cable contact against these tables, including no shorts to adjacent pins and all NC insulation.
2. Verify unsupported5V USB leaves motor permission off. Confirm the selected source negotiates15V3A and the measured bus is within limits.
3. Check protected bus, both5V rails, Pico3V3, ADC scale and I2C addresses before enabling loads.
4. Remove/reseat the grille: verify the contact, GP15 and EF2SHDN independently. Reset/boot must leave the motor branch off.
5. Check servo feedback/open position and its bounded jam cutoff with rotor absent. Check display, wheel/countdown, night mode and ambient dimming.
6. Verify UART levels, both power sequences, stale telemetry and ESC timeout. Follow the guarded motor/impeller qualification procedure before any motion build.

Cable lengths, clips, bend envelopes, shield/return routing and populated-tray service slack need source-matched physical CAD integration. Nominal unplugged screen removal is not a connected-loom removal qualification.
