# Implementation plan — revised after Onshape inspection, 2026-09-08

## Existing design and decision

Inspected the authenticated Windflow Main workspace in Chrome. The Base has 28 features and one part; its starting profile is 240 x 150 mm, R7.5 corners, extruded 120 mm. Two tilted P12 Pro fan instances feed a central divided plenum. The separate Duct has 21 features, a turning passage and a contracted rectangular exit; its outer-end sketch is underconstrained. The Full Fan Assembly has 12 instances, including eight 8 x 3 mm magnets, and 16 mate features. A separate 30-instance Iris Nozzle assembly uses planar overlapping blades and slotted plates. It is not a smooth converging nozzle and is not integrated in the full assembly. The visible full assembly has no encoder, power electronics or actuating servo.

Save the original as **Baseline - original dual fan and iris - 2026-09-08**. Develop the replacement in clearly named new parametric studios in the same document. Use a straight axial path instead of merging two tilted streams into a turning duct. This removes the central obstruction and bend, reduces size and motor count, and provides a practical location for progressive converging panels. One fan has a lower free-air rating than two fans combined; improved delivered airflow or noise must be measured, not assumed. Retain the original version as the comparison baseline. Replace the planar iris with opposing panels rather than refining an inherently abrupt restriction.

## Mechanical architecture

Prototype around a Noctua NF-A12x25 G2 PWM, 120 x 120 x 25 mm bare frame, 105 mm square mounting centres. Provide rigid alignment sleeves with replaceable TPU isolation at four corners. Develop a horizontal airflow head over a serviceable electronics base; final envelope depends on the inspected CAD and component stack. The outlet is integral with the structural enclosure, with an independently removable magnetic grille. Include a fixed inner finger guard and a rear inlet guard, so removing the cosmetic front grille does not expose moving blades or nozzle linkages.

## Airflow

Use a rounded inlet and a gradual circle-to-rounded-rectangle transition without reducing area unnecessarily. Initial throat diameter 114 mm and bell-mouth radius 14 mm are tuning values, subject to the actual fan aperture. Keep at least 15 mm rotor/stator separation as a starting point. Compare an unobstructed duct with a removable internal radial-vane test insert; start with 7 vanes, 0.8 mm thickness and 18 mm axial length. Avoid a long honeycomb unless swirl/velocity measurements justify its pressure loss. The final nozzle is not removable.

## Progressive nozzle

Use two opposing broad panels forming a rectangular converging jet, driven by one feedback servo through equal cranks and a translating slotted yoke outside the air path. The local mechanism fixture passes 61 nominal sampled positions; whole-product and insertion checks have separate reports. Separate keyed cranks permit assembly through the split housing, and a removable external cover protects the linkage. Initial clear outlet 104 x 94 mm, panel length 55 mm, minimum area ratio 0.75, giving 12.3355 degrees maximum inward rotation and 5.1273 mm yoke stroke with 24 mm cranks. Verify the fan operating point before enabling boost. Use sidewall overlaps, supported metal hinge pins, accessible linkage cover and hard stops. Do not assume an unpowered hobby servo springs open; loss of tracking must stop the fan.

## Electronics and power

Use a Raspberry Pi Pico, a Bourns PEC11H encoder with horizontal shaft and edge-operated thumbwheel, addressable speed/ambient LEDs, separate power/fault indication, two MCP9808 sensors, fan tach and an SDP810-125Pa differential-pressure sensor. Use a FEETECH FS90-FB position-feedback servo; measure linkage friction and required torque before committing the mount. USB-C PD requests 15 V / 2 A; convert to regulated 12 V for the fan and separate 5 V servo and logic/lighting rails. No battery. Size rails for unthrottled LED current and servo stall current. Load enables default off, with voltage/temperature/position supervision, branch fuses and a watchdog. There is no electronic current measurement in this revision.

## Firmware

Implement timed state machines for power qualification, opening/home verification, smooth startup ramp, saved-setting restore, live control, service mode and latched faults. Map 0–75% of the control range to fan PWM and the last 25% to progressive area reduction with maximum fan PWM. Panel angle follows inverse nozzle geometry, not an arbitrary servo sweep. Boost requires calibrated feedback and pressure sensing. RPM is diagnostic, not a direct flow measurement. Use delayed, validated non-volatile records; input and safety remain responsive during animations. Enter service with a recessed jumper plus a deliberate boot hold and a USB service console.

## Physical integration and validation

Download manufacturer models, log provenance and dimensions, and distinguish exact models from simplified envelopes. Add connector and tool-access volumes. Build small coupons for encoder, diffuser, magnets, TPU mounts and linkage/hinges first. In Onshape, mate and sweep the complete mechanism, run interference at open/intermediate/closed positions, and demonstrate the assembly order. Compile the selected firmware, test the control/safety state machines, then follow a hardware commissioning procedure before releasing printable enclosure files.
