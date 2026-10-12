# SDP810 pressure daughterboard — P1 electrical candidate

The Sensirion **SDP810-125Pa**, order number **1-101597-01**, now has an editable, routed two-layer daughterboard. It carries the four sensor leads, the circuit's existing **C33 Murata GRM188R71H104KA93D 100 nF** capacitor, four direct-solder cable pads and two M2 non-plated mounting holes. The installed sensor, retaining bracket, complete cable and pressure hoses remain separate CAD work. This electrical candidate is not a fabrication release or a qualified assembled sensor.

Native schematic, PCB, netlist, local libraries, front/back SVGs, native board-only STEP, mechanical interface and verification records are in [pcb/pressure](pcb/pressure). Regenerate with the pinned runtime:

```powershell
& .\.tools\kicad-10.0.6\bin\python.exe tools/build_pressure_board.py
```

The builder checks the downloaded manufacturer reference hash, the captured carrier J11 pin mapping and C33 part/location/nets. It exports and compares the actual native netlist, then runs KiCad 10.0.6 ERC and DRC at all severities with schematic parity and violation exit codes enabled. The current snapshot reports **zero ERC findings, zero DRC violations, zero unconnected items and zero schematic-parity findings**, with **exit code 0** for every command. The current files and inputs are hashed in [provenance.json](pcb/pressure/provenance.json). No Gerbers are emitted.

## Sensor side and cable mapping

The [Sensirion digital SDP8xx datasheet](https://sensirion.com/media/documents/90500156/6167E43B/Sensirion_Differential_Pressure_Datasheet_SDP8xx_Digital.pdf), v1.1, page 4 defines the electrical pins. Page 12, Figure 3 explicitly shows the footprint from the **sensor side**. Its four leads are ordered **SCL, VDD, GND, SDA** from left to right at 2 mm pitch. A solder-side view reverses their appearance. Do not use the bottom CAD view to infer electrical numbering.

Board coordinates below are KiCad F-side `(u,v)`, increasing right/down. The sensor occupies the F side; C33 occupies the opposite B side. J1 is a set of solder pads, not a second purchased connector. The cable terminates at carrier **J11**, using a JST **XHP-4** housing and appropriate genuine XH contacts such as **SXH-001T-P0.6**, subject to the selected wire's conductor and insulation range.

| Sensor lead | Function | Sensor pad `(u,v)` mm | Daughterboard J1 pad | Carrier J11 pin |
| --- | --- | --- | --- | --- |
| 1 | SCL | (6,9) | 4, (15,5.5) | 4 |
| 2 | VDD, +3.3 V | (8,9) | 2, (7,5.5) | 2 |
| 3 | GND | (10,9) | 1, (3,5.5) | 1 |
| 4 | SDA | (12,9) | 3, (11,5.5) | 3 |

The sensor supports 2.7–5.5 V; this design supplies 3.3 V and uses the existing carrier I2C pullups. Its specified maximum continuous current is 5.5 mA. Do not duplicate C33 on the main board: the captured circuit already locates it on this daughterboard. The SDA/SCL traces are 0.35 mm wide; a B-side ground fill connects the cable return and sensor/C33 return. There are no signal vias.

## Mechanical interface and assembly limits

The PCB is **18 × 12 × 1.6 mm total thickness**. Sensor and cable pads have Ø0.8 mm drills. The sensor uses the manufacturer's nominal hole pattern; finished hole/lead tolerances and soldering must be qualified. Four cable pads use 4 mm pitch to leave room for individual insulated wires. The two Ø2.4 mm non-plated mounting holes are at `(2,2)` and `(16,2)`, with 2.6 mm-radius copper exclusions for M2 washers and tool clearance.

C33's actual native pads are `(8.225,7)` and `(9.775,7)` on B.Cu. The capacitor body and solder fillets need clearance on that face. The manufacturer's sensor body is wider than this small PCB; its F.Fab drawing records the 29 × 18 mm nominal body. The electrical courtyard encloses the leads only. Passing electrical courtyard checks does **not** verify that the overhanging body, clips, wires, bracket or enclosure fit.

The native board-only STEP exports dielectric geometry. It must not silently substitute for the complete 1.6 mm board thickness when installed CAD is created. Mechanical adoption must check the actual sensor leads against the drilled datum, capacitor/fillets, cable emergence, mounting stack, fastening access and service path. Verify continuity from the real sensor leads to carrier J11 before applying power. Keep solder/flux contamination out of the pneumatic ports and follow the manufacturer's handling instructions.

Remaining physical acceptance includes lead seating, solder quality, cable strain relief, address/CRC communication, pressure zero/scale and tubing leakage/lag. Installed bracket and hose design are still unfinished engineering work, not physical tests already performed.
