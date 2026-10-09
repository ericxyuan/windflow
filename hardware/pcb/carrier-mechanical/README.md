# E3 carrier mechanical blank

This is a native KiCad 10 mechanical design, **not a routed electrical board or fabrication release**. It establishes the board datum, mounting holes and enforced mounting keepouts before component placement. Do not order it as a complete controller.

| Property | Value |
|---|---|
| Outline / nominal thickness | 90 × 65 × 1.6 mm |
| Mount holes | Four Ø2.4 mm NPTH, at (3,3), (3,62), (87,3), (87,62) mm |
| Mount keepout | Minimum radius 3.5 mm, all provisional copper layers; no tracks, vias, pours, electrical pads or other footprints |
| Assembly lower corner | (5,55,−106) mm |
| Global hole centres | (8,58), (8,117), (92,58), (92,117) mm |
| Populated height reserve | 22 mm from underside, leaving 20.4 mm above the nominal PCB top |
| Electrical content | No electrical nets, parts, tracks, vias or captured schematic |

Open `carrier-mechanical.kicad_pro` in KiCad. The project-local `WindflowMechanical.pretty` library and `fp-lib-table` keep the mounting footprint reproducible. Four provisional copper layers only let the mounting rules cover a possible future stackup; layer count and thickness distribution must be chosen during electrical layout.

From **PowerShell in the Windflow project folder**, regenerate with:

```powershell
& .tools/venv/Scripts/python.exe tools/build_carrier_mechanical.py
```

The runtime comes from the checked-in `tools/setup_kicad.ps1` and `tools/kicad-runtime.json`. Downloaded tools remain local. The generator reloads the board with native `pcbnew`, checks 23 mechanical properties, runs CLI DRC, exports SVG and STEP, and deliberately inserts separate copper, footprint and electrical-pad violations to prove the stored keepouts reject them. Probe boards are disposable intermediates under ignored `build/carrier-mechanical-validation/`; their reports are preserved under `negative-probes/`. The baseline DRC exits 0 with zero violations; each negative probe exits 5 with the expected keepout violation. `validation.json` records source and output hashes.

`carrier-mechanical-kicad.step` is the untouched board-only KiCad export. For an unpopulated board, this KiCad version omits outer copper/mask and exports a 1.51 mm substrate. `carrier-mechanical-cad-datum.step` separately extrudes the same validated drilled outline to the full 1.6 mm mechanical thickness and places it in the existing assembly datum. It has one valid solid, the expected 9,331.047 mm³ volume and four clear hole-axis probes. This is not a fabricated stackup model.

The [Onshape mechanical datum studio](https://cad.onshape.com/documents/5ca1b5b26cd9a4a93dde4737/w/6d3d38529391b53ad011b362/e/9b11b7d7a7402bf192647aba) visibly contains one imported part and is named **Rev B — Carrier PCB mechanical datum — UNROUTED**. It is an independent datum study; the existing 76-instance product assembly still contains its electronics reserve. Import provenance is recorded in `../../../cad/onshape-inspection.md`. Regeneration can change STEP serialization and timestamps, so the recorded import hash and later local export hash are distinguished.

Next work is schematic capture and review, final connectors and harness restraints, actual component placement, routing, ERC/DRC with schematic parity, thermal/current review, fabrication outputs and a populated-assembly check. Empty-board DRC and nominal hole alignment do not establish any of those outcomes. The remote Pico candidate is explained in [carrier-interface-study.md](../../carrier-interface-study.md).
