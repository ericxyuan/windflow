# Carrier interfaces — design study, 5 October 2026

The carrier is mounted separately from the Pico and three regulators. The prior socket rows in the BOM do not establish a physical connection between those separate tray positions. This study defines a candidate harness and actual PCB mounting geometry; it does not replace the E3 circuit specification or qualify a fabrication release.

## Mechanical board

The main carrier outline is 90 × 65 × 1.6 mm, with four Ø2.4 mm NPTH holes at board coordinates (3,3), (3,62), (87,3), (87,62). Its lower corner in assembly coordinates is (5,55,−106), giving global hole centres (8,58), (8,117), (92,58), (92,117). The bottom face is −106 and the top face is −104.4 mm. These match the existing tray supports; the PCB is separate from the 22 mm volume reserved for populated electronics.

The mechanical KiCad files are in `pcb/carrier-mechanical/`. They have no power/control netlist or routed circuit. Mounting keepouts and a board outline are concrete design work; an empty-board DRC result cannot establish electrical safety, current handling or circuit correctness.

## Remote Pico candidate

Use four **Samtec TSW-120-07-G-S** strips: two on the Pico and two on the carrier. Replace the former carrier SSW-120 socket concept with removable cables between male headers. The selected TSW post is 5.84 mm, within the IDSS documented 5.59–6.22 mm insertion range. [TSW product](https://www.samtec.com/products/tsw-120-07-g-s), [IDSS catalogue](https://suddendocs.samtec.com/catalog_english/idss.pdf).

Two **Samtec IDSS-20-D-04.00-G** cable assemblies are the base candidate: single-row, twenty positions, sockets at both ends, 101.6 mm assembled length, gray 28 AWG ribbon, gold default contacts. Fit **PK-06** keys to both ends of the left cable at position 12 and both ends of the right cable at position 10. The same keys can be ordered through the documented P12/P10 configuration; confirm the complete multi-option order code with Samtec before purchase. Remove the corresponding male contacts on both boards. [Manufacturer series print](https://suddendocs.samtec.com/prints/idsx-xx-x-xx.xx-xxx-xxx-mkt.pdf).

| Carrier row | Cable position | Pico physical pin | Key / unused positions |
|---|---|---|---|
| J15, logical pins 1–20 | n | n | Position 12 is blocked; GP9 is unused. |
| J16, logical pins 1–20 | n | n + 20 | Position 10 is blocked; RUN, physical pin 30, is unused. |

Carrier pins corresponding to Pico physical 35 (ADC_VREF), 37 (3V3_EN) and 40 (VBUS) have no circuit connection. They must not connect to ground or a power rail. The cable still contains those conductors; keep their unused landing pads short. All eight ground/AGND positions are retained. This connects only the documented Pico low-current supply and signal nets; fan, servo and LED power never travels through the Pico or ribbon. Continuity must follow pin numbers at both ends, including the opposite numbering directions of the Pico rows. Do not infer pin order from a view of the underside or ribbon color alone.

The different blocked positions prevent a fully seated row swap or reversal when every required key and removed male contact is present. They do not guarantee resistance to forced or offset insertion. A printed retention/strain clamp and insertion review remain required. Disconnect power before attaching or removing these looms.

Candidate carrier row centres are global (13,86.5) and (22,86.5); the Pico row centres are (−53.39,86.5) and (−35.61,86.5). The separate CAD study is `../cad/interface_study/remote-pico-candidate.step`. Its ten socket/header/corridor envelopes pass 555 nominal collision checks against the revised base components and each other, with exit 0 and no intersections. The report records source/input hashes. Bends, service slack, clamp geometry and complete cable shape are absent. Restrict future components beneath the ribbon corridor to 18 mm above the carrier top; pressure tubing introduces lower keepouts on its actual route. Validate both again after component placement.

The Pico mount now uses four Accu SSCF-M1.6-10-A2 cap screws and HPN-M1.6-A4 nuts, with 1.8 mm printed holes and 3.3 mm AF nut pockets. The maximum 3 mm head leaves 0.42 mm nominal clearance to the adjacent header body. A driver no more than 3.4 mm in outside diameter leaves 0.22 mm nominal lateral clearance. Unplug both IDSS sockets before accessing the screws; no washers are fitted. These drawing-based clearances still need print and supplied-part qualification. This mount is adopted in local base geometry; the 3 October 76-instance Onshape checkpoint has not yet received it.

The full SPI route includes the Pico ribbon, carrier traces and J6 screen loom. Target their combined wire length at no more than 150 mm rather than treating each harness independently as 150 mm. The 101.6 mm Pico candidate leaves under 48.4 mm for J6 wire; geometry and service slack must establish whether that is feasible. If not, select a shorter supported Pico cable or revise the routing and SPI rate after timing/edge tests. This is a design limit, not measured signal-integrity evidence.

## Regulator connection to resolve in the schematic

Pololu explicitly permits wires soldered directly to its D24V22Fx pads for a compact installation. Use mechanically restrained, labeled pigtails from the independently screwed modules to carrier power connectors; remove the former assumption that a carrier-mounted five-pin socket directly holds each remote module. Keep each EN pad unconnected. REG1 and REG3 need VIN, GND, VOUT and PG; REG2 needs VIN, GND and VOUT only. [Manufacturer connection instructions](https://www.pololu.com/product/2858).

Choose keyed power connectors and their placement during schematic capture, accounting for 22 AWG power pairs, PG isolation, insertion access and the different output voltages. The complete ordered connectors, strain clamps, harness lengths and populated-board placement are still unfinished. The existing BOM socket rows remain provisional until that revision is reconciled; this candidate study must not be used alone to order or assemble the electronics.
