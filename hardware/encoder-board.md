# E3 encoder daughterboard — prototype P1

The passive daughterboard for the Bourns **PEC11H-4215F-S0024** is captured as an editable KiCad 10.0.6 schematic and routed, two-layer PCB. It carries only the encoder, a **JST B4B-XH-A(LF)(SN)** four-way header and two non-plated mounting holes. The carrier's three 10 kΩ pullups and three 10 nF capacitors remain on the carrier; there are no duplicated filters or powered loads on this board. This is a fabrication candidate. Actual soldering, seating, thumbwheel force, connector service access and final assembly clearance still require qualification.

Native sources, Gerbers, routed plated-slot drill files, drill maps, ERC/DRC reports, a netlist, board/schematic SVGs and source/artifact hashes are in [pcb/encoder](pcb/encoder). Regenerate from the project root in PowerShell with:

```powershell
& .\.tools\kicad-10.0.6\bin\python.exe tools/build_encoder_board.py
```

Use the existing `tools/setup_kicad.ps1` runtime and CAD runtime. The generator requires the checked manufacturer reference `hardware/datasheets/PEC11H.pdf`; the download manifest restores that local reference. It checks the Bourns reference SHA-256 before building. The KiCad JST footprint is copied to the project library, so the saved board does not require a user's global footprint library. `.kicad_prl` is per-user UI state and is excluded from provenance.

## Wiring and placed pin coordinates

J1 mates with **JST XHP-4** and suitable genuine XH crimp contacts, for example **SXH-001T-P0.6** with the documented wire/insulation range. Read connector pin numbers from the native footprint and verify continuity. A cable viewed from its wire side can appear reversed; wire colours are not a pin-number reference.

| J1 pin | Net | Encoder terminal | Carrier endpoint |
| --- | --- | --- | --- |
| 1 | GND | C, S2 and both mounting-tab pads | J8 pin 1, GND |
| 2 | ENC_A | A | J8 pin 2, GP0 through existing carrier filter |
| 3 | ENC_B | B | J8 pin 3, GP1 through existing carrier filter |
| 4 | ENC_PUSH | S1 | J8 pin 4, GP2 through existing carrier filter |

The encoder and push switch are dry contacts. At 3.3 V with 10 kΩ pullups a closed channel carries about 0.33 mA, below the encoder's 10 mA contact rating. All three closed channels together draw about 0.99 mA through the carrier pullups. No supply rail is carried by J1. The grounded mounting pads are **not a substitute for the C terminal**. S1/S2 is a footprint convention for the two interchangeable SPST switch terminals.

The manufacturer shows the hole pattern looking toward the shaft/mounting face. The encoder is on **B.Cu**, which mirrors local X in the placed footprint. Board coordinates below are the KiCad top/F-side coordinate system: `u` increases right and `v` increases down. The generator asserts every electrical pad and both tab coordinates after the actual KiCad flip.

| Feature | Placed `(u,v)` mm | Global `(Y,Z)` mm |
| --- | --- | --- |
| Encoder shaft axis | (8.5, 12) | (3, -90) |
| A | (11, 19.5) | (5.5, -97.5) |
| C | (8.5, 19.5) | (3, -97.5) |
| B | (6, 19.5) | (0.5, -97.5) |
| S1, push signal | (11, 5) | (5.5, -83) |
| S2, push common | (6, 5) | (0.5, -83) |
| Mounting tabs | (2.1,12), (14.9,12) | (-3.4,-90), (9.4,-90) |
| J1 pins 1–4 | (21.5,8.25), (21.5,10.75), (21.5,13.25), (21.5,15.75) | (16,-86.25), (16,-88.75), (16,-91.25), (16,-93.75) |
| M2 mounting holes | (27.5,3.5), (27.5,20.5) | (22,-81.5), (22,-98.5) |

The five encoder electrical holes are Ø1.10 mm plated; its two grounded mounting tabs use **2.40 × 1.60 mm plated slots**. These are the upper ends of the Bourns mounting-hole ranges and are intentional prototype choices. The four JST holes are Ø0.95 mm plated, on 2.50 mm pitch. The two Ø2.40 mm M2 holes are non-plated. Confirm finished drill/slot tolerances with the fabricator and use the fabrication drill files, not the copper pad dimensions, as the hole specification. See the [Bourns mounting drawing and ratings](https://www.bourns.com/docs/product-datasheets/pec11h.pdf) and [JST XH header/mating drawing](https://www.jst-mfg.com/product/pdf/eng/eXH.pdf).

## CAD datums and component envelopes

The board is **29.5 × 24.0 × 1.6 mm**. Its global bounds are **X[-62.5,-60.9], Y[-5.5,24], Z[-102,-78]**. The encoder is on the X−62.5 face pointing toward −X. The connector is on the X−60.9 face pointing toward +X. Preserve the global encoder axis and M2 hole positions above; extend the earlier 24 mm board toward negative Y and move its encoder-side plane inward by 1 mm. Shorten the bracket's PCB supports so they seat on X−62.5. The main CAD owns the resulting screw engagement and shell/insertion checks.

Two exports have different purposes:

- `windflow-encoder-board-only.step` is KiCad's native export. Its actual bounds are **STEP X[0,29.5], Y[-24,0], Z[0,1.51]** because KiCad omits copper and solder mask in a board-only export. It is not the complete 1.6 mm assembly thickness.
- `windflow-encoder-mechanical-datum.step` is a re-imported, valid one-solid, **1.6 mm** drilled datum generated from the placed native pad positions and drills. Use this file for the PCB assembly envelope. It includes all 13 hole/slot locations but does not pretend to be a populated purchased-component model.

For either STEP coordinate system, the proper rigid transform is:

```text
global X = -62.5 + STEP z
global Y = -5.5 + STEP x
global Z = -78 + STEP y       (STEP y = -v)
```

Do not move the F-side component plane to X−60.99 because of the native 1.51 mm substrate. Component datums use the total board thickness. Do not apply the B-side mirror a second time after importing the board: the routed pad locations already include it.

The following envelopes are drawing reconstructions, not exact purchased CAD. Published dimensional tolerances still apply. The full assembly must model the solder-pin ends, connector withdrawal and wire bend separately.

| Item | Global X mm | Global Y mm | Global Z mm |
| --- | --- | --- | --- |
| Encoder main body, nominal 6.5 × 11.8 × 13.6 mm | -70 to -63.5 | -2.9 to 8.9 | -96.8 to -83.2 |
| Encoder rear-terminal tips, nominal | -60.5 tip | At pad positions above | At pad positions above |
| Bare JST header body, 7 mm high | -60.9 to -53.9 | 12.6 to 18.35 | -96.2 to -83.8 |
| Mated JST header/housing reserve, 9.8 mm high | -60.9 to -51.1 | 12.6 to 18.35 | -96.2 to -83.8 |
| JST solder-tail tips, nominal | -64.3 tip | 16 | At J1 pad positions above |

The connector reserve does not include wire insulation, the cable's bend radius, finger/gripper access or the axial withdrawal stroke. The nominal encoder rear body is X−63.5, leaving a **1.0 mm body-to-PCB gap**. With 3.0 mm terminals and a 1.6 mm PCB this gives about **0.4 mm protrusion** beyond the solder face. Actual terminal length, tab seating and solder fillet must be measured before ordering a final batch. The Bourns body has broad dimensional tolerances; do not assume these nominal numbers establish worst-case enclosure clearance.

## Assembly and inspection

1. Inspect finished board outline, Ø2.4 mm holes, plated round holes and plated slots. Check J1 pin 1 and footprint orientation against the tables above before fitting parts.
2. Fixture the encoder on B.Cu with its shaft toward −X and the body-to-board gap qualified from the actual part. Fit J1 on F.Cu. Preserve the gap without forcing pins or bending the encoder tabs to make an incompatible board fit.
3. Qualify soldering to the manufacturer's process: Bourns specifies wave soldering at **260 °C ±5 °C for 3 ±1 seconds** and does not recommend hand soldering. This design has not qualified a selective/wave or hobby soldering process. Inspect hole fill, fillets and insulation clearances after soldering.
4. With the cable disconnected, check J1 pin 1 to C and S2, pin 2 to A, pin 3 to B, and pin 4 to S1. Check no signal-to-signal short. Test the switch and quadrature state changes; A/B direction can subsequently be calibrated in firmware, but a wiring reversal must not be hidden by an unverified drawing.
5. Install the bracket's captive M2 nuts before placing the bracket in the shell. The panel bushing, nut and bracket carry the thumbwheel's axial press load; the PCB should be supported at both M2 holes without operating force carried through solder joints. Seat screw heads only on the mounting areas; avoid the copper exclusion zones. Final M2 screw length/engagement remains governed by the adopted main CAD.
6. Mate and strain-relieve the four-wire harness before closing the service tray. Verify it can be unplugged by gripping the housing. Route it clear of the wheel, servo linkages, tray-removal path and fan power wiring. Repeat a full turn, switch press and continuity test after enclosure installation.

## Verification scope

The generator exports and validates four functional nets against exact expected pin-node sets, 13 pads including two NPTH mounting holes, 27 route segments/vias and three rule areas. KiCad ERC and DRC run with all severities, explicit violation exit codes, all track checks and schematic/PCB parity. The final reports must have no violations, unconnected items or parity differences. The board uses 0.35 mm traces, 0.25 mm minimum clearance/edge clearance and one Ø0.60/0.30 mm via. There is no copper pour. The body-side rule area excludes foreign copper under the encoder; two mount rule areas reserve copper around screw locations.

`mechanical-validation.json` records actual native STEP bounds, all 13 transformed drills and the re-imported 1.6 mm datum's validity, solid count and analytical volume comparison. `provenance.json` records the generator, manufacturer reference and every generated artifact hash except itself and ignored `.kicad_prl` UI state. These checks establish the saved circuit/layout/datums; they do not prove enclosure assembly, solder process reliability, encoder feel or long-term use.
