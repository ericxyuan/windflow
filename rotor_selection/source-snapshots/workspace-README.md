# Windflow desktop fan

Rev C is the active design: one **T-Motor Pacer V4 P2406 Juicy 2060KV**, a custom printed five-blade impeller, one telemetry ESC, a flowing enclosure and an integrated progressive outlet. It is a development prototype; rotor motion is inhibited in the distributed firmware until the physical commissioning requirements are met.

The canonical repository is [ericxyuan/windflow](https://github.com/ericxyuan/windflow). Work is in the user's existing [Onshape document](https://cad.onshape.com/documents/5ca1b5b26cd9a4a93dde4737/w/6d3d38529391b53ad011b362/e/6b5211a8cb2c1370bdde64a6). It contains a native adjustable ten-part Rev C airflow/boost architecture and the named purchased/mechanical development integration. The original dual-fan design and earlier Rev B versions remain preserved. The [checkpoint record](cad/onshape-rev-c-checkpoint.json) identifies the matching exports, inspections and limitations.

The protected IPS screen replaces the front speed and status light bars. Its top 64 rows retain that status role; the main view shows normal power, relative wheel phase and the degrees remaining before boost control. A 24-detent turn covers normal output. At maximum normal output, another **fresh full turn** enters boost control while the panels remain open; subsequent rotation progressively closes them. Every exit, off/fault or reboot requires a fresh entry turn. The encoder sits beside the screen, turning parallel to its surface. Downward ambient lighting and long-press night mode remain. See [front controls](docs/rev-c-front-controls.md).

Start with these active deliverables:

- [Implementation plan](docs/rev-c-implementation-plan.md), [full requirements audit](docs/rev-c-requirements-audit.md) and [deliverable register](docs/deliverable-status.md).
- [Airflow, bell mouth and one-servo boost mechanism](docs/rev-c-airflow-and-mechanism.md), [impeller development](docs/rev-c-impeller.md), [printing and assembly](docs/rev-c-printing-and-assembly.md) and [neutral daily-use assessment](docs/rev-c-daily-use-review.md).
- [Selected bought-part BOM](hardware/rev_c/BOM.csv), [wiring and all 40 Pico pins](hardware/rev_c/wiring.md), [editable schematic](hardware/pcb/rev_c/windflow-rev-c.kicad_sch) and [schematic PDF](hardware/pcb/rev_c/windflow-rev-c-schematic.pdf).
- [15 V / 3 A USB-C PD architecture and power budget](docs/rev-c-motor-power.md). The 18 W motor/ESC cap gives a calculated 21.774 W normal-full-output scenario and 29.513 W simultaneous upper scenario; these are allowances, not measured consumption.
- [Modular firmware source](firmware/WindflowRevC), [operation and calibration](docs/rev-c-firmware.md) and [source/binary validation](firmware/WindflowRevC/validation.json). Current host checks cover 4,183 parser/control/safety/display assertions, 60 shipping service assertions and 73 qualified host-simulation service assertions, with a successful Pico build. No device has been flashed or operated.
- [CAD parameters](cad/rev_c/head-parameters.json), [exchanged-part validation](cad/rev_c/head-validation.json), [motion/service checks](cad/rev_c/motion-validation.json), [test-print pieces](cad/rev_c/testpieces) and [purchased-model register](cad/model-register.md).

Actual main-board routing, the Pico cable transition, pressure daughterboard/hoses, installed looms and full fastener/tool checks remain engineering work. Motor retention, FDM rotor strength, low-speed ESC compatibility, airflow, throw, noise, temperatures, printed fits, stability and endurance require hardware evidence. A valid model, firmware build or schematic check cannot establish those results.

The earlier Noctua fan circuit, Rev B firmware and 76-instance assembly are historical. Their reports do not qualify Rev C. See the [historical deliverable register](docs/rev-b-deliverable-status-history.md) for that checkpoint.
