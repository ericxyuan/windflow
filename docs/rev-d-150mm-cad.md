# Rev D — 150 mm rotor and flowing enclosure

Development candidate, 9 October 2026. **No operating RPM is approved for this rotor.** This revision implements the recommendation in `rotor_selection`; it preserves the 112 mm Rev C sources and the user's earlier Onshape elements. Valid CAD and a watertight STL do not qualify a printed rotor for spinning.

## Study reviewed and implementation plan

The complete archived report, calculations, source snapshots and recorded layout decision were reviewed. The selected starting point is a **150 mm, five-blade ducted axial rotor** with moderate forward sweep, camber and spanwise twist. Seven blades are a comparator at equal total solidity, not an automatic improvement. Mixed flow is the fallback if the axial stage loses too much flow through the outlet. The archived analysis allowed rearranging the complete product within **200 mm total height**, retaining the display and controls.

The mechanical plan is a 152 mm rotor throat, R12 inlet, rigid 16 mm PCD motor carrier with separate TPU isolation, an interchangeable curved-stator/open-spacer trial, an 85 mm smooth contraction and the existing matched single-servo two-panel linkage. The enclosure has a flowing hollow outer skin, an integral outlet and electronics in its lower shoulders. A low plinth replaces the tall separate electronics base. A fixed inner finger guard remains when the magnetic cleaning grille is removed.

The electrical baseline remains the **T-Motor Pacer V4 P2406 Juicy 2060 KV**, single **Team Triforce A50S V2.3c** ESC, Pico, Adafruit 4311 IPS screen and horizontal Bourns encoder. The existing 15 V / 3 A USB PD architecture, 18 W motor/ESC input ceiling and initial 3 A phase-current ceiling remain the development baseline. A drone's one-second peak rating is not the desktop continuous rating. Actual motor shoulder, shaft projection, thread pitch, mounting screw depth, exact servo and ESC dimensions still require measured confirmation.

The active firmware in the historical `firmware/WindflowRevC` folder now identifies the exact 150 mm P2 STEP article with its SHA-256 and a saved article tag. Schema 5 rejects earlier 112 mm calibration records; a CRC-correct record with another article tag is rejected too. Verification on 10 October passed 4,187 parser/safety/control/display assertions, 60 default service assertions, 73 qualified **host simulation** service assertions, the motion-inhibited shipping test and a Pico build. Those results do not grant any operating RPM to the larger rotor.

Firmware remains **motion inhibited**. No new speed, higher current or boost speed reserve has been enabled. The study's proposed 15–20% speed reserve and 20–30% boost airspeed improvement are future experimental objectives. The existing normal/full-turn-arm/boost interaction, screen status band, wheel phase, entry countdown, night mode and safety logic are preserved. Each exit from boost still requires a fresh complete arm turn at maximum normal output; no new hardware control has been introduced.

## Actual geometry

| Feature | Current CAD input | Purpose / physical tuning |
|---|---:|---|
| Rotor / throat | 150 / 152 mm | Nominal 1 mm radial gap; dynamic and print errors unqualified |
| Blade count | 5 | Compare 7 only with comparable total solidity |
| Hub | 40 mm diameter × 40 mm long | Root support and M5 clamp access; adds inertia |
| Bore / clamp web / nut access | 5.2 / 2.5 / 14.5 mm | Fit coupons first; actual shaft shoulder and nut clearance unmeasured |
| Root blend / hub round | 3 / 1.5 mm | The independently checked P2 STEP includes the dense root blend |
| Blade radii | 16, 20, 23, 30, 42, 55, 66, 75 mm | Editable section stations |
| Section chords | 28, 30, 31, 33, 34, 31, 26, 20 mm | Broad midspan, reduced tip loading hypothesis |
| Section thicknesses | 6.5, 6.5, 5.6, 4.8, 4.2, 3.5, 2.8, 2.4 mm | Finite FDM edges and structural trial |
| Tip leading / trailing radius | 0.8 / 0.4 mm | Avoid a fragile mathematical knife edge |
| Forward sweep | 0 to 8° | Adjustable modest sweep; acoustic benefit unmeasured |
| Pitch geometry inputs | 2,200 rpm; 5 m/s; 5° incidence | **Design inputs, neither predicted performance nor permitted operation** |
| Bell mouth | R12 mm | Quarter-round entry; radius/throat parametric |
| Curved trial stator | 7 × 1.2 mm vanes, 24 mm axial length | Nominal inlet slope 20°, exit axial; measure rotor swirl first |
| Contraction | 85 mm | Six smooth rounded stations from circular throat to outlet |
| Outlet | 104 × 94 mm, R3 corners | Gross rectangular area 9,776 mm²; real free area lower |
| Boost panels | 55 mm; maximum 12.3355° | 75% minimum gross aperture trial, below 15° hard geometric ceiling |
| Fixed guard | 4.8 mm nominal slots / 1.2 mm bars | Finger-access trial; **not qualified fragment containment** |
| Magnetic grille | 120 × 100 mm outer frame | Side-rail D42 pockets, pilot pins, separate glued retaining covers |
| Head / plinth / feet | 185 / 6 / 4 mm | Intended complete 195 mm geometric stack, checked against 200 mm limit |
| Screen / wheel centers (X,Z) | (10,−70.5) / (−56,−70.5) mm | Wheel beside screen; axis +Y and spin plane XZ parallel to screen |

The annular rotor area with a 40 mm hub is approximately 16,415 mm². The open outlet's gross rectangular area is about 59.6% of that, falling to 44.7% at maximum geometric closure. Corners, hub wake, vanes, grilles and boundary layers reduce actual free area. The 75% closure setting alone cannot establish a faster jet. A 20% mean velocity increase at that area needs roughly 90% of normal volumetric flow to remain; compare measured flow, power and noise before increasing closure.

The solid-PETG mass estimate is **91.87 g** at 1,270 kg/m³. Printed mass, balance and strength are unknown. The study's motor torque limitation therefore remains material to startup, sustained operation and braking. The rotor must not inherit the smaller rotor's previous trial limit.

## Onshape and authoritative articles

The existing assembly was inspected before new geometry. A separate **Rev D — 150mm parametric rotor — DEVELOPMENT** Part Studio has been created in the same document. Its native custom feature exposes diameter, blade count, chord multiplier, forward-sweep multiplier and twist-design inputs.

- Native Part Studio: https://cad.onshape.com/documents/5ca1b5b26cd9a4a93dde4737/w/6d3d38529391b53ad011b362/e/ac831cfb3e2f99f349f8306c
- Native source Feature Studio: `7adab6e2c2df5d71438ba1ef`, local `cad/WindflowRevDRotor.fs`, library 3083.
- Default feature evaluation returned **no notices** and produced one part in the user document.
- Native proof: `cad/evidence/onshape-rev-d-native-rotor-2026-10-09.png`.
- Prototype fit article: `cad/rev_d/impeller-P2-150mm-GUARDED-TEST-ONLY.step` and `.stl`.

**The native feature is a profile study, not the identical P2 fit article.** Its smooth raw sections omit the P2 article's denser ruled root-flare stations and rounded hub. The independent mesh/STEP report applies only to the named P2 artifacts and their hashes. Parameter bounds in the native feature are editing ranges; only the default has been evaluated so far. For an equal-solidity seven-blade comparison, start with approximately 5/7 of the five-blade chord multiplier and revalidate the resulting geometry and flow.

The new [Rev D parametric airflow/exterior Feature Studio](https://cad.onshape.com/documents/5ca1b5b26cd9a4a93dde4737/w/6d3d38529391b53ad011b362/e/fcaf5b7ea81e608e05d9abb6) contains the checked `cad/WindflowRevDHead.fs` source. Its 17 inputs cover throat diameter, bell radius, wall and head dimensions, outlet width/height/corners, contraction length, stator thickness/length/count/inlet angle, insert clearance, panel length, minimum gross aperture, angle ceiling and boost fraction. Default-open and maximum-closure evaluations passed in Onshape with no notices, including the seven-solid-body assertion. Exact source readback matches the local file; `cad/rev_d/native-airpath-validation.json` records both evaluations.

This native airpath is a major-profile study with a hollow flowing exterior, rounded inlet, rigid carrier, TPU isolation, curved stator and two progressive panels. Its contraction begins with a true circle and has axial tangent constraints at both ends. The outlet cut includes 0.02 mm radial numerical relief. It omits the detailed assembly's bearings, linkage, split seam, guards, purchased electronics and plinth; those fit and mesh checks do not transfer to it. The [native airpath Part Studio](https://cad.onshape.com/documents/5ca1b5b26cd9a4a93dde4737/w/6d3d38529391b53ad011b362/e/399cdd4584e017c0a30623b4) now visibly contains seven parts with the default open panels. It was inserted through **Custom features in this workspace** after committing the checked source. The proof screenshot is `cad/evidence/onshape-rev-d-native-airpath-2026-10-10.png`.

## Validation records

- `cad/rev_d/rotor-validation.json`: independent STEP round-trip, one valid solid, 436,470 STL triangles, one connected component, zero boundary/nonmanifold edges, zero inconsistent winding edges. The bore-fit and root/edge coupons also passed geometry/mesh checks.
- `cad/rev_d/stage-validation.json`: regenerated nominal placements, STEP reimports, complete-product bounds and pair intersections. A result supports only the source hashes and geometry recorded in that file.
- `cad/rev_d/mesh-validation.json`: **28 stage STL files passed** shared-edge, winding, connectivity and positive component-volume checks. The four TPU feet are correctly treated as four separate bodies. The initial bell-mouth and both enclosure-half meshes had open edges even though their STEP solids were valid; `cad/rev_d/stl-refinements.json` records their accepted fresh tessellations from the unchanged STEP geometry. No vertex welding is used. The left half needs a 0.001 mm absolute tessellation tolerance and is about 95 MiB; this is an export workaround, not a proposed printing tolerance.
- `cad/rev_d/motion-validation.json`: sampled boost motion, moving-part pairs, encoder rotation/press, unplugged display removal and conservative rotor swept-envelope checks.
- `cad/rev_d/integration-export-validation.json`: only generated after source-matched PASS records, with named assembly STEP round-trip validation.

No test report establishes measured airflow, throw, acoustic noise, rotor burst strength, actual motor torque, electronics temperature, magnet retention or hardware operation. The Onshape imported hierarchy will not by itself supply native kinematic mates. Latest online integration is recorded separately in `cad/onshape-rev-d-checkpoint.json`; an earlier online checkpoint never proves later source changes.

## Printing and assembly development

Start with the **M5 bore/clamp coupon** and **root/edge stationary coupon**. These establish fit and surface quality without printing the full rotor. Use dry PETG, 0.4 mm nozzle, 0.16 mm layers, at least six perimeters and solid infill as initial stationary-fit settings. Rotate the rotor's +Y axis to the build Z axis; inspect the slicer for isolated blade islands and support the underside where needed. Support scars, moisture and poor bonding must be evaluated before any contained spin trial. Settings are an initial prototype process, not a qualified rotor production process.

The current full-length head halves need a build envelope accommodating roughly **275 mm length × 185 mm other extent** in the chosen orientation, plus brim/support allowance. A 300 mm class plate is the straightforward starting point. They are not yet qualified for a 256 mm printer. Splitting the rear inlet/carrier section at a bolted joint while retaining the complete final nozzle in the front shell is an open printability refinement. The nozzle is integral to the enclosure; no detachable final nozzle is introduced.

Fit the real motor to the rigid carrier with measured-length M3 screws before closing the shell. Fit the separately printed TPU ring without allowing the motor to shift radially. Assemble the stator or open comparison spacer, servo bracket and accessible linkage before joining the head halves. The shaft, bearing and motor interfaces are drawing-based pending fit checks. Install electronics before the bottom tray. The screen/cradle removal sequence removes bezel/lens and tray, unplugs wires, shifts rearward 4 mm and then down; only a passing motion report supports this path.

The two modeled temperature boards sit in the lower electronics shoulders. The second board is **not a winding-temperature measurement** at its current placement. Its usefulness as a motor-temperature proxy needs a measured thermal relationship, or relocation with an appropriate probe. ESC telemetry and direct commissioning measurements remain necessary before permitting motor operation.

The cleaning grille uses eight D42 magnets (four paired locations), 0.2 mm radial pocket clearance, adhesive allowance, retaining covers and alignment pins. Mark polarity before bonding. The fixed seat frame uses four M2 mounting locations in the side rails. Complete screw lengths, insert retention, anti-rattle treatment, repeated removal and maximum-flow pull tests remain to be validated. Adhesive covers are not an assurance of retention under printed-rotor failure.

## Remaining design and physical tests

**Design still to complete:** exact purchased hardware datum confirmation; main PCB population/retention, connected harness and pressure plumbing; re-integrated grille interlock; complete fasteners and tool approaches; connector/plug/strain-relief access; shell print split or printer-specific orientation; tolerance extremes, native assembly mates and final assembly order. The independent open spacer is an A/B trial, not an extra part to install with the stator.

**Physical qualification:** printed shaft/root/edge coupons; filament/process strength and guarded overspeed procedure; dynamic balance and rotor retention; minimum tip clearance under heat/deflection; motor/ESC phase-current and input-power curves; gradual startup and braking; normal and boost velocity traverse/flow/throw measurements; pressure/swirl survey and stator A/B; measured acoustic comparison at equal cooling; servo travel/torque/jam recovery; thermal and power-fault tests; encoder direction/feel, screen readability/night use; grille retention and anti-rattle tests; foot stability and vibration transmission.

No favorable daily-use rating is justified by a rotor shape alone. Cooling and noise remain unmeasured. This revision improves the control location, removes exposed linkage housings and reduces the height; mass, footprint, service access and actual acoustic performance remain important review items.

## Reproduction

Use Python 3.12 and the existing pinned **CadQuery 2.6.1** environment at `.tools/rev-c-cad-venv`, with `cad/rev_d/requirements.txt`. The study archive is retained unchanged. Vendor dependencies are local references described by the checked-in download manifest. `tools/prepare_rev_d_vendor_inputs.py` validates the nine inherited purchased-component placements or reconstructs missing ones from their original manufacturer files, using `cad/rev_d/vendor-model-inputs.json`. Checks include the downloaded source hash, orientation, minimum bounds, dimensions, body count, and matched per-body volume/centroid. This is not a Boolean equality proof or a check of an unmeasured physical component. Existing placed references are preserved.

Run `tools/build_rev_d_cad.ps1 -RebuildRotor` to prepare vendor inputs and rebuild the rotor, stage, checked STL tessellations, motion checks and exchange assembly. Omit `-RebuildRotor` only when the rotor report hashes still match. Any failing stage, mesh or motion check stops export. The exchange exporter also checks report freshness and the individual accepted STL hashes. It verifies the firmware source/image hashes, matching 150 mm article SHA, schema 5, default motion inhibition and absence of an approved operating RPM before exporting. Large vendor STEP references and the complete imported assembly are local reproducible outputs, not substitute manufacturing releases.
