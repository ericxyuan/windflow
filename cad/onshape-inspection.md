# Onshape inspection — 8 September 2026

Document: [Windflow](https://cad.onshape.com/documents/5ca1b5b26cd9a4a93dde4737/w/6d3d38529391b53ad011b362/e/4ed72084c2e4978faf960789), Main workspace. Inspection used authenticated Chrome computer control. The user signed in; no credentials were extracted.

| Studio | Element ID | Observed contents |
|---|---|---|
| Base | 4ed72084c2e4978faf960789 | 28 features, 1 part, 240 x 150 x 120 mm starting solid, R7.5 plan corners; intake, fan slots/mounts/vents, magnets, central splitter |
| Duct | 701531be8283496518094244 | 21 features, 1 part; curved turning region, lofted rectangular contraction, inner/outer sketches and exit fillet |
| Full Fan Assembly | 70ec7dcf7d4e8e53233e7e35 | 12 instances: Base, Duct, 2 P12 Pro fans, 8 magnets named 8 x 3 Circular Magnet; 16 mate features |
| Iris Nozzle | dc005eb6daeebf72d56af4a1 | Separate 30-instance assembly with six-sector planar closing blades, slotted top/bottom plates; 11 mate features visible in tree |

Read dimensions directly from Base Profile and Base extrude dialogs, then cancelled each dialog. Duct Outer End Profile reports not fully defined; R7.5 is visible. Inner profile shows 10 mm offset constraints and R5. No reliable overall outlet width/height was captured, so none is inferred from screen pixels. Original fan orientation is visibly tilted; no exact angle was measured.

Engineering concerns: merging streams and a substantial turn upstream of an already contracted exit; large base footprint; planar iris behaves as an orifice, cannot by itself form the requested gradual converging nozzle; original magnetic joint removes the whole duct, whereas the revised final outlet must be integrated with the enclosure. No thermal, pressure, servo or electronic integration is present in the inspected full assembly. This is a visual/feature inspection, not CFD or a physical airflow test.

The implementation plan was revised before any major geometry change. Baseline version requested through Onshape's Create version dialog: **Baseline - original dual fan and iris - 2026-09-08**.

## Verified Rev B work — 3 October 2026

Authenticated Chrome access and file upload work. All edits below used supported browser computer control.

| Element / version | ID | Observed result |
|---|---|---|
| Rev B — Native parametric airflow | `4ecc138b99d5ee5b9bc3d4d8` | Seven features including defaults, five parts: bell-mouth, trial radial straightener, nozzle frame and two panels. |
| Feature Studio 1 | `f1f1c6bace056a2c14a10a1d` | `WindflowAirpath.fs` committed; three custom features available. |
| Rev B parametric progressive nozzle - 2026-10-03 | `9670ba1935877d1f8be26cff` | Version used by the native progressive-nozzle feature. |
| First development assembly import | `e20438303bd050e5c8c1d3db` | 72 instances with purchased models; both housing halves initially imported as faulty. Needs refresh and new-instance reconciliation. |
| full-development-assembly parts | `8ebacee9e57babec21768854` | Combined imported parts studio; vendor sub-bodies increase its B-rep count beyond assembly instances. |
| Repaired right housing | `c5c2dc49cb3574b3ca84781e` | One part with Allow faulty parts unchecked; accepted and saved. |
| Repaired left housing | `f291a032dfe27397b288cbaf` | One part with Allow faulty parts unchecked; accepted and saved. |

The housing repair uses an exact circle split into eight arcs at the throat. It removes tiny straight segments from the previous almost-circular rounded rectangle. Separate import checks establish Onshape solid acceptance; they do not automatically update the old assembly.

The native nozzle was checked at boost fractions 0, 0.5 and 1. All produced five parts with the existing inlet and stator. Setting minimum area ratio to 0.5 produces a feature error because the required angle exceeds 15 degrees. The saved value is restored to 0.75, boost 0. The native nozzle is an aerodynamic parametric study; hinges, keyed cranks, fasteners and structural details remain in the integrated development model.

Proof images are in `evidence/`: native-airflow-five-parts, open/half/max nozzle, angle-rejection and left/right valid-housing images dated 2026-10-03. No Onshape collision analysis or physical performance is inferred from screenshots.

### Complete assembly refresh and native collision review

The source-matched local model subsequently passed with exit 0: 81 components, 6,121 checked pairs, 183 +X cover-removal samples and zero unintended intersections. A fresh STEP import completed without an error notification and shows **Instances (81)**. It is named **Rev B — Integrated development assembly — 2026-10-03**, element `3c99f91ec444444536245cd7`. The previous 72-instance import is retained as **Superseded — Rev B initial import — 72 instances**.

Onshape's native **Check interference** command was run on the complete new assembly with standard content and top-level filtering unchecked. It reported seven entries: six between sub-bodies of Adafruit's supplied HUSB238 board model, and one between the encoder shaft envelope and thumbwheel. The latter is the intended D-shaft engagement; the six vendor entries are internal to one purchased module. No additional enclosure or mechanism intersections were reported. This native check is the imported maximum-boost pose; the separate local report covers open and intermediate poses and sampled cover removal.

Proof: `evidence/onshape-integrated-81-instances-2026-10-03.jpg`, `evidence/onshape-integrated-native-interference-2026-10-03.jpg` and `evidence/onshape-integrated-outlet-2026-10-03.jpg`. Motion mates, full fasteners, wiring/tube sweeps and tolerance qualification remain open.

### E3 screen assembly refresh — 3 October 2026

The latest user revision replaces front main/status bars with the Adafruit 4311 IPS screen and requires a fresh full encoder turn before each boost session. The source-matched local E3 model passed with exit 0: **76 components, 5,536 pair checks, 183 cover-removal samples and zero unintended intersections**, across open, halfway and maximum boost. The 174-sample display service-path report and twelve nominal display fastener checks supplement that whole-assembly result. They exclude complete harness, tool, tolerance and physical fit qualification.

The checked `full-development-assembly.step` is 69,837,546 bytes with SHA-256 `9e377ef335463d43efa9764526675d6dbd54f98391e9d279571e6ecb914d7159`. Browser file upload and translation completed. The [current assembly](https://cad.onshape.com/documents/5ca1b5b26cd9a4a93dde4737/w/6d3d38529391b53ad011b362/e/9ee256003ae02b710e21a9ec) is named **Rev B — IPS screen and full-turn boost — 2026-10-03** and visibly shows **Instances (76)**. Its combined Part Studio, element `204ab75d338147c6452e9495`, contains 203 bodies, reflecting separate solids within purchased modules. The earlier 81-instance import is renamed **Superseded — Rev B LED controls — 81 instances**.

Onshape's native **Check interference** was run for the complete 76-instance assembly with standard content and top-level filtering unchecked. It reports seven entries: six within the supplied HUSB238 module and one intended encoder/wheel engagement. No additional enclosure, linkage or screen intersections were reported. This checks the imported maximum-boost pose; the local report covers the other poses and sampled cover removal.

The clear acrylic window's Part Studio appearance is saved with color `DCEEF7` and alpha 0.15; the returned assembly view shows the display behind it. CAD appearance does not establish optical performance. The manufacturer's generic screen surface has no firmware UI texture; the separate production-rendered previews in `docs/images/` demonstrate the actual software layout.

Proof: `evidence/onshape-screen-native-interference-2026-10-03.jpg` and `evidence/onshape-screen-outlet-2026-10-03.jpg`. The assembly remains an imported development model; native airflow parameters do not automatically modify its detailed shell or mechanism. Motion mates, full harness/tubing, carrier PCB, interlock interface and complete tool/fastener access remain unfinished design work.
