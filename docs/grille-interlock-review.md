# Grille interlock design study

This study supplies real printable geometry for the removable front grille interlock. It is an isolated nominal design, ready for integration and whole-assembly checking; it is not a certified safety device or a manufacturing release. It modifies the left head, the grille and the head magnet-retaining rim. The integral airflow nozzle remains part of the enclosure.

The selected switch is **Omron D2F-01L**, with gold-alloy contacts, a hinge lever and straight PCB terminals. Case, hole and terminal dimensions follow [Omron's D2F drawing](https://omronfs.omron.com/en_US/ecb/products/pdf/en-d2f.pdf), pages 2–5. The manufacturer CAD route required a member login, so the switch STEP files explicitly describe drawing envelopes. They omit molded recesses, the plunger and the real elastic lever geometry. Their dimensions should not be mistaken for a downloaded manufacturer model.

## Geometry and datums

The study uses assembled coordinates: airflow is +Y, and head-local Z is translated by the project head-centre height, currently 10 mm. The switch sits outside the left side of the air passage. The unmodified right head, grille front keeper and captured inner guard remain in the study to check nearby structure.

| Feature | Trial geometry or specification |
|---|---|
| Switch case | X thickness 5.8 mm, Y height 6.5 mm, Z length 12.8 mm |
| Case placement | X −63.1…−57.3; head-local Z 12…24.8 mm |
| Switch hole pattern | Two nominal Ø2 mm holes, 6.5 mm apart; first hole 3.15 mm from the case end |
| Sliding bracket | X −65.5…−63.1 mm, two Ø2.4 mm capsule slots; conservative Y adjustment ±2 mm |
| Bracket head mounts | Y=136.7; head-local Z=8 and 29 mm |
| Raceway head mounts | Y=133; head-local Z=−14 and −52 mm |
| Actuator face | Y=143.25; X centre −60.2; lever-contact height inferred at head-local Z=25.4 mm |
| Tongue nose | Integral grille tongue; 0.3 mm rounding retains a flat contact face |
| Fixed signal raceway | X centre −60.2, Y=125.5, head-local Z −65…0 mm |
| Trial signal wires | Two Ø1.2 mm envelopes, centres X=−60.85/−59.55; tangent R4 bends |
| Fixed strain clamp | Head-local Z −10…−4 mm; it does not move with the switch bracket |
| TPU liner | Free Ø4.15 × 6.2 mm, installed envelope Ø4 × 6 mm; two trial Ø1.1 mm wire holes |
| Front seating land | Head rim face Y=150.8; grille rear face Y=151.0; nominal additional inward travel 0.20 mm |

The protective cover's upper cavity clears the mounting boss. A capsule opening at its bottom allows the fixed wires to pass when the bracket shifts through its calibration range. Moving the raceway 2 mm rearward gives 3.8 mm nominal straight solder tails before the R4 elbows, with 2.3 mm at the worst operating-position extreme.

The rigid clamp alone would leave clearance around the two-wire bundle. The separate TPU liner provides trial interference, while the rigid mating faces limit screw travel. The liner's holding force and effect on insulation must be tested; neither the CAD nor a zero-clash result proves strain retention. Alternative Ø1.0 and Ø1.2 mm hole coupons allow adjustment to the received wire and printer.

## Mechanical operating range and calibration

The switch's operating position is **6.8 ±1.5 mm** from the mounting-hole datum. Its guaranteed minimum overtravel is **0.55 mm**; movement differential is up to **0.5 mm**. A single fixed, uncalibrated tongue cannot reliably accommodate that operating-position tolerance. The ±2 mm slotted mounting range is intentional.

Calibrate each received switch using a multimeter, with device power disconnected. Seat the grille on its normal datums. Start with the bracket toward −Y, then slide it toward +Y until COM–NO first closes. Move the bracket a further **0.25 mm toward +Y**, measured from a repeatable bracket datum, and secure its two outboard screws. Check that removal opens the contact, and that reinstalling the grille closes it consistently. Recheck after tightening.

The nominal grille seating gap permits another 0.20 mm inward motion before the nearby rim land stops it. This produces **0.45 mm** nominal post-trip travel at the stop, leaving only **0.10 mm** relative to the guaranteed minimum overtravel. That margin is small. Measure the actual additional inward travel and lever depression with the printed coupon; reject or adjust a combination exceeding 0.20 mm additional motion or 0.50 mm total measured post-trip travel. Printed tolerance, grille flex and lever deformation cannot be inferred from the rigid stop check. Do not resolve a poor fit by pressing the grille harder.

For the specified operating-position endpoints, the calibrated bracket translations from nominal are +1.5, 0 and −1.5 mm. The study evaluates all three positions, including the fixed wiring. The lever shapes are approximate envelopes; the final received switch must still be checked for contact location, released position and deflection.

## Fasteners and assembly

The incremental hardware is one D2F-01L switch, **two ISO 4762 M2×16 screws**, **six ISO 4762 M2×10 screws**, **eight ISO 7089 M2 washers** and **eight DIN 934 M2 nuts**. The M2×10 groups hold the switch, wire clamp and raceway. Smooth reference solids represent the nominal fastener envelope; they omit thread profiles. Omron specifies 0.08–0.10 N·m for the switch mounting screws with washers. The printed bracket and other joints still require torque and retention qualification.

Print the bracket, cover, clamp, raceway and lid on their broad X faces. Print the TPU liner along its Z axis with a brim if necessary. These are proposed orientations: check the slicer, nut pockets, bore fidelity and bridges before printing. The modified head and grille retain their main project orientations. Use the small head-corner, tongue, clamp and liner test pieces before committing to a full head print.

1. Fit the switch to the bracket on the bench. Its screw heads face +X; the nuts load from the outboard side. Insulate the unused NC terminal. Attach COM and NO leads while keeping solder and heat away from the case as specified by Omron.
2. Dress the two leads through the fixed raceway and TPU liner. Install the clamp on the bench, checking grip without crushing or cutting the insulation. Leave the upper straight tails and R4 bends free to accommodate the bracket's calibration movement.
3. Load the four head mounting nuts through their channels, install the bracket/cover and raceway/lid, and secure the four outboard head screws. The nut loading channels open toward +Y; retain loose nuts during assembly.
4. Route the continuation to J12, outside the fan and linkage sweeps. The study ends at head-local Z=−65 mm; the final base feed-through and connector access belong to whole-assembly integration.
5. Calibrate the bracket with the grille seated, then verify the electrical guard state using the project's loads-off service procedure before powered fan testing.

The grille pulls forward without a screw or a loose actuator. The interlock cannot stop a spinning rotor instantly. Turn the fan off and wait for the rotor to stop before cleaning; the captured fixed inner guard remains necessary.

The inboard switch/clamp screw approaches are not service paths through the assembled nozzle wall. For replacement, remove the grille, unplug J12 and free its base continuation, remove the four outboard head retaining screws, and withdraw the **whole wired switch/raceway unit toward −X**. The soldered leads remain attached. Switch and clamp screws are accessible on the bench. Raceway-lid removal is checked separately. Do not pull a still-connected harness out of the base.

## Electrical integration

From the case end at head-local Z=12 mm, the terminal order is **COM, NO, NC** at Z=13.32, 18.4 and 23.48 mm. COM goes to ground; NO goes to the raw guard input on J12; NC remains insulated and unused. The seated grille closes NO to COM. A broken or unplugged wire therefore reports an absent grille; a shorted guard line can still defeat this indication.

Omron lists a 1 mA at 5 V minimum applicable load as a reference value for its gold-contact models. The previous 4.7 kΩ pull-up at 3.3 V was below that reference. The parent E3 electrical revision uses **R5=3.9 kΩ to the 5 V logic rail**, followed by a **5 V tolerant, 3.3 V powered TI SN74LVC1G17DBVR Schmitt buffer** to GP15. This gives approximately 1.28 mA at nominal 5 V and protects the microcontroller from the raw 5 V node. Use the current [wiring specification](../hardware/wiring.md) for BUF4, R60 and C31/C32, and verify actual rail voltage, startup, contact wetting and fault states on the bench. This study does not capture or route that circuit.

## Reproduction and adoption

Run from the project folder in PowerShell:

```powershell
.tools/venv/Scripts/python.exe cad/grille_interlock_study.py
```

The study loads byte-frozen input STEP files and parameter/source records from `cad/grille_interlock_study/baseline/`; `baseline/provenance.json` records their original project paths and SHA-256 hashes. Those script copies are provenance, not a second main design to edit or rebuild. Later main-head regeneration does not change the study baseline. The datasheet is cached under ignored `build/datasheets/grille-interlock/`, with the existing ignored `hardware/datasheets/D2F.pdf` download as a fallback. Vendor PDFs are not project deliverables.

`build_geometry(left, grille, keeper, head_z)` and `integrate_head_parts(...)` accept the caller's B-reps in its existing Z datum. The integration function returns the three modified main parts, the five separate rigid interlock prints and the free TPU liner. Save the free liner as a print artifact; use the installed liner reference in the assembly. `installed_reference_parts(head_z)` reads only hash-checked installed component/fastener/wire/liner STEP exports from the successful report. The drawing-based case/lever must retain their reference labels.

Integration must replace the corresponding main head, grille and rim, add the printed interlock parts and installed references, regenerate the main reports, check the base harness continuation, and perform whole-assembly collision/tool/motion checks. Expected wire-to-terminal solder contact and TPU-to-insulation compression are explicit study contacts. The rest of the assembly must not use a blanket collision exclusion for this module. The study alone does not update Onshape.

The validation report records valid single-solid exports, panel motion samples, bracket calibration extremes, grille withdrawal, separate module/raceway-lid withdrawal, whole wired-unit service, outboard and bench drivers, and the actuator-to-lever contact distance. Its continuous X-boundary check keeps the added hardware outside the air-passage prism, independently of the sampled panel poses. Consult `validation.json` and `check-diagnostics.json` for the current source-matched counts and exact contact volumes.

Physical qualification remains required for switch contact repeatability/life, actual overtravel and grille flex, magnet seating, print tolerances, nut retention, screw torque, TPU wire grip/insulation damage, received wire bend radius, electrical guard behavior, and the final base feed-through/service loop. These are release gates, not benefits established by this study.
