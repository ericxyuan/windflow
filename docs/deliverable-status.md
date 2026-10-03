# Deliverable status — 3 October 2026

This is a progress register, not a manufacturing release or completion certificate. Onshape access and file upload are working. The original design is preserved in its baseline version. Current engineering work has moved into concrete enclosure, mechanism and purchased-component integration.

| Required deliverable | Current artifact / status |
|---|---|
| Updated Onshape CAD | Native inlet, stator and progressive-nozzle study regenerate as five parts. Fresh 81-instance integrated assembly includes repaired structural halves and purchased models. Native interference review is recorded. Motion mates and remaining physical interfaces are still unfinished. |
| Purchased CAD integration | Manufacturer models for the fan, Pico, PD board, regulators, temperature boards, pressure sensor and LED sticks are integrated in the imported development assembly. Servo and encoder remain drawing-based envelopes. See `cad/model-register.md`. |
| Complete firmware | Modular source and compiled UF2 in `firmware/`; host assertions and board build passed. No physical device flashed or commissioned. |
| Exact BOM and nonprinted components | `hardware/BOM.md`, electrical revision E2. Current shafts, collars, sleeve stacks, pressure-sensor and temperature-board mounts are reconciled. Final carrier population and complete product fastener reconciliation remain open. |
| Wiring diagram / pin assignment | `hardware/wiring.md` contains a net-level diagram and exact Pico physical pins. It is not a captured schematic or routed carrier PCB. |
| Power budget / USB-C architecture | `hardware/power-budget.md`, `hardware/circuit-review.md`: 15 V / 2 A PD, regulated rails, no battery. Calculated allowances need measurement. |
| Airflow / bell-mouth / straightener | Parametric native and local geometry: 114 mm throat, 14 mm inlet radius, seven trial radial vanes. Performance remains unmeasured. |
| Progressive boost / mapping | One servo, symmetric panels and yoke. Nominal 75% encoder threshold, 75% minimum gross outlet area. Native aerodynamic study and integrated mechanical model have separate purposes. |
| Thermal / tach / startup logic | `docs/firmware-operation.md`: implemented and host-tested. Sensor placement/lag, tach signal and safety response require hardware qualification. |
| Calibration instructions | `docs/calibration.md`: measured commissioning evidence is required before enabling live boost. |
| Printing instructions | `docs/printing-and-assembly.md` plus fit coupons. Large-part release awaits integration, tool/harness review and slicer/coupon acceptance. |
| Assembly instructions | Split head and separate keyed cranks have an explicit insertion sequence. Sensor mounts, optical retainers and linkage cover exist. Carrier/harness/interlock integration still needs completion. |
| Physical tuning and uncertainties | `docs/physical-validation.md`, mechanism notes and calibration distinguish tuning values from measured results. No physical qualification is recorded. |

## Verified evidence and its limits

- Firmware: 6,343 host assertions with exit 0; Pico build exit 0, program 100,864 bytes and RAM 10,416 bytes. These do not prove operation of attached electronics.
- Onshape: native airflow studio shows seven features and five parts. Nozzle boost fractions 0, 0.5 and 1 regenerate; a 0.5 minimum area ratio is rejected by the 15 degree angle ceiling. Saved setting: 0 boost, 0.75 minimum area. This study does not drive the imported structural shell automatically.
- Housing import: exact eight-arc circular throat loft replaces the near-circle sliver geometry. Left and right halves each show one part with **Allow faulty parts unchecked**. Proof images are under `cad/evidence/`.
- Local mechanism fixture: 61 nominal positions, zero unintended overlap. Thirteen sampled insertion paths pass with exit 0 after changing crank approach to vertical. The insertion model excludes fasteners, servo, wiring, guards and tools installed later.
- Head and base generators pass their geometry, support and component checks. Reports record generator and parameter hashes. The full-assembly interference report must match those hashes before acceptance; stale reports are not evidence for later edits.
- The 2026-10-03 full-assembly check passes with exit 0: 81 components, 6,121 pair checks and 183 cover-removal samples across open/halfway/maximum boost. Zero unintended intersections; all recorded generator and parameter hashes match. This excludes complete fastener, harness, tool and tolerance validation.
- Nominal gross outlet area is 9,776 mm² open and 7,332 mm² at the initial limit. These dimensions establish a geometric contraction, not higher measured jet speed or throw.

## Engineering still required before physical qualification

1. Finish assembly motion/mates and the remaining physical interfaces. The complete Onshape assembly refresh and current local whole-assembly/cover-removal checks have passed.
2. Resolve the carrier-to-Pico/regulator physical interconnection. The 90 × 65 × 22 mm reserve is not a finished board, and separate tray modules cannot be assumed to mate directly to carrier sockets.
3. Capture/review the carrier schematic, route its PCB, run ERC/DRC and generate fabrication/placement files. The encoder and direct-solder pressure daughterboards also need routing.
4. Complete pressure-tap hose connection, tube path, grille-present switch mount/contact interface, wiring restraints and service slack. Resolve the fan compression-limiter/pad interface and model its actual stack.
5. Reconcile final fastener quantities and demonstrate tool access and populated-tray removal. Run final source-matched interference and insertion checks after those changes.

These are unfinished design tasks, not merely uncertainties delegated to physical testing. Airflow, noise, finger access, magnetic retention, print fit, servo friction, fault timing, thermal behavior and USB margins remain separate physical qualification work.
