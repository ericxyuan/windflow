# Implementation plan — provisional until existing CAD is inspected

## Inspection gate

Obtain the existing Onshape document in an accessible authenticated browser. Record document/workspace/element URLs, existing features and variables, part and assembly structure, dimensions, fan envelope, air path, print splits, and current mechanism. Create an Onshape version before major changes. Revise this plan from those observations before changing geometry. Do not treat the architecture below as a review of the unseen model.

## Mechanical architecture

Prototype around a Noctua NF-A12x25 G2 PWM, 120 x 120 x 25 mm bare frame, 105 mm square mounting centres. Provide rigid alignment sleeves with replaceable TPU isolation at four corners. Develop a horizontal airflow head over a serviceable electronics base; final envelope depends on the inspected CAD and component stack. The outlet is integral with the structural enclosure, with an independently removable magnetic grille. Include a fixed inner finger guard and a rear inlet guard, so removing the cosmetic front grille does not expose moving blades or nozzle linkages.

## Airflow

Use a rounded inlet and a gradual circle-to-rounded-rectangle transition without reducing area unnecessarily. Initial throat diameter 114 mm and bell-mouth radius 14 mm are tuning values, subject to the actual fan aperture. Keep at least 15 mm rotor/stator separation as a starting point. Compare an unobstructed duct with a removable internal radial-vane test insert; start with 7 vanes, 0.8 mm thickness and 18 mm axial length. Avoid a long honeycomb unless swirl/velocity measurements justify its pressure loss. The final nozzle is not removable.

## Progressive nozzle

Investigate two opposing broad panels forming a rectangular converging jet, driven by one feedback servo via equal opposite crank motions and a cross-shaft outside the air path. A linked pair is easier to align and seal than four overlapping petals. Initial clear outlet 104 x 94 mm, panel length 55 mm, minimum area ratio 0.75, giving approximately 12.3 degrees maximum inward rotation of each panel. Verify geometry and safe operating point before enabling boost. Use overlaps along sidewalls, supported metal hinge pins, accessible linkage cover and hard stops. The linkage must remain backdrivable enough for a tested opening spring; do not assume an unpowered hobby servo springs open.

## Electronics and power

Use a Raspberry Pi Pico, a Bourns PEC11H encoder with horizontal shaft and edge-operated thumbwheel, addressable speed/ambient LEDs, separate power/fault indication, two temperature sensors, fan tach and differential-pressure sensor. Use a FEETECH FS90-FB position-feedback servo; measure linkage friction and required torque before committing the mount. USB-C PD requests 15 V; convert to regulated 12 V for the fan, 5 V for servo/lighting and a separate housekeeping rail. No battery. Size rails for unthrottled LED current and servo stall current. Load enables default off, with voltage/temperature/current supervision and a watchdog.

## Firmware

Implement timed state machines for power qualification, opening/home verification, smooth startup ramp, saved-setting restore, live control, service mode and latched faults. Map 0–75% of the control range to fan PWM and the last 25% to progressive area reduction with maximum fan PWM. Panel angle follows inverse nozzle geometry, not an arbitrary servo sweep. Boost requires calibrated feedback and pressure sensing. RPM is diagnostic, not a direct flow measurement. Use delayed, validated non-volatile records; input and safety remain responsive during animations. Enter service with a recessed jumper plus a deliberate boot hold and a USB service console.

## Physical integration and validation

Download manufacturer models, log provenance and dimensions, and distinguish exact models from simplified envelopes. Add connector and tool-access volumes. Build small coupons for encoder, diffuser, magnets, TPU mounts and linkage/hinges first. In Onshape, mate and sweep the complete mechanism, run interference at open/intermediate/closed positions, and demonstrate the assembly order. Compile the selected firmware, test the control/safety state machines, then follow a hardware commissioning procedure before releasing printable enclosure files.
