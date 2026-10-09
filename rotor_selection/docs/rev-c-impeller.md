# Rev C impeller P1 — development article

This is an actual five-blade, 112 mm diameter impeller model for the requested T-Motor Pacer V4 P2406 Juicy 2060KV motor. It is a **guarded prototype only**. The model's closed solid and mesh checks establish geometric consistency; they do not establish a safe operating speed, adequate shaft retention, strength, balance, airflow or noise.

The repeatable design is in `cad/rev_c_rotor.py`, with editable parameters in `cad/rev_c/rotor-parameters.json`. A successful run writes STEP and STL files, a stationary M5 shaft/clamping fit coupon, station dimensions and `cad/rev_c/rotor-validation.json`. Generated reports include hashes of the exact source and parameters. Do not use an old report after altering either file.

## Blade and hub geometry

The local rotation axis is +Y. Y=0 is the motor prop-seat plane. All rotor geometry lies forward of this plane so that the rotating motor bell can remain behind it. To place the rotor with the main design's motor seat at global Y=29 mm, rotate 180° around X and translate by (0,29,0): `(x,y,z) -> (x,29-y,-z)`. This points the rotor's local +Y away from the motor and upstream. The final ESC direction must be established from actual airflow in a guarded test; do not infer motor phase order from a perspective view.

Five identical blades begin inside the 36 mm hub and merge into it. The unflared radial stations use a wide 28 mm root/mid-root chord, falling to a 14 mm tip chord. The base root section thickness is 6 mm and tip section thickness is 2.6 mm; the reinforcement flare increases the innermost chord and thickness by up to 5 mm. Leading edges and trailing edges are circular caps; the unflared root trailing-edge diameter is 2.4 mm and the outer trailing-edge diameter is 1.2 mm. The reinforced inner tails are thicker. These finite thicknesses accommodate a 0.4 mm FDM nozzle. They incur more drag than a thin molded trailing edge, which must be assessed in airflow and acoustic measurements.

The root section expands into a radius-controlled flare, using a 2.5 mm quarter-circle offset sampled at eight stations. The inner blend uses ruled loft intervals for a robust solid and the outer blade uses a smooth loft. This is an approximation to a rounded root transition, with thicker material around the attachment, rather than an exact rolling-ball fillet. The report records the construction and the stations. The hub has rounded outer rims. Neither the loft nor the nominal blend radius is a substitute for layer-adhesion or fatigue testing.

The blade pitch follows a deliberately transparent initial rule:

`pitch(r) = atan(V_design / (omega_design * r)) + incidence`

Here `V_design=5 m/s`, `omega_design=2*pi*3000/60 rad/s` and incidence is 8°. This is a relative-velocity geometric starting point with modest camber, not a prediction of a uniform 5 m/s flow. Induced flow, blockage, swirl, radial variation, tip leakage, inlet/outlet loading and viscous losses change the actual flow and incidence. There is no measured fan curve or CFD result for this impeller. The five-blade rotor and seven-vane stator have different counts, reducing repeated simultaneous alignment; noise benefit remains unmeasured. The previous straightener geometry must be rechecked for the motor and rotor wake.

The nominal radial clearance in the earlier 114 mm throat is 1 mm. Printing error, radial runout, mount deflection, shaft error and thermal changes consume this allowance. It must be measured around the complete revolution and under load. The enclosure, motor mount and guards must be checked again in the complete Rev C assembly; the old Noctua assembly clearance report is superseded for motor/rotor fit.

## Shaft and clamping interface

The motor [manufacturer's drawing](https://www.ligpower.com/images/202508/Pacer-V4-Juicy-draw.png) gives an M5 threaded shaft and 8 mm dimension at the thread; the [product specifications](https://www.ligpower.com/product/p2406-fpv-freestyle-motor.html) give 10 mm. Use 8 mm conservatively until the supplied motor is measured. The drawing does not separately define the prop-seat diameter or plain shoulder length. The shaft clearance is initially 5.2 mm, and the fit coupon includes 5.1, 5.2 and 5.3 mm bores.

The hub's central clamping web is 2.5 mm thick with a 14.5 mm access recess for a metal nut and washer. The 26 mm outer hub gives the blades an extended root connection, while the thin central web preserves thread engagement. Use thin, flat metal load-spreading washers only after confirming the actual seat, thread length and nut engagement. The metal nut must turn freely through the recess, clamp the web evenly and leave useful thread engagement. Do not bury a nut directly in plastic, use a loose grub screw as primary retention or let a washer catch a shaft shoulder instead of clamping the rotor. A retaining system cannot be finalized from the incomplete shaft drawing.

The coupon is a stationary fit test. It must not be spun. Check bore fit, concentricity, web creep under clamping, nut tool access and both washer faces before a full rotor is printed. Physical shaft and prop-seat measurements may require a change to the central hub and web dimensions.

## Rotational estimates and speed control

At 3000 rpm the 112 mm tip travels approximately 17.6 m/s. At the separate 5000 rpm analytical case it travels approximately 29.3 m/s. The report estimates centrifugal load for an individual lofted blade using its CAD mass and center of mass, assuming a material density of 1270 kg/m³. It also gives a conservative upper bound on total rotor kinetic energy by putting the entire estimated mass at the tip radius: `E <= 0.5 * m * R² * omega²`. These calculations are load/energy estimates, not allowable stresses or a burst-speed calculation. The real print may have voids, weld weaknesses, moisture effects, defects, residual stresses and different density.

The 3000 rpm figure is the first guarded commissioning ceiling, pending qualification. The 5000 rpm case is **not operating permission** and must not become the default firmware maximum. No uncontained or unattended run is approved by this geometry package. Motor KV is far too high to infer a safe fan speed from a fixed throttle fraction or USB input voltage. The ESC and firmware must use measured RPM, power/current limiting, stall protection and an independent overspeed response. Boost changes the aerodynamic load, so the limits must remain active across the full panel travel.

## Printing and inspection

Print the rotor in one piece with the shaft axis vertical and the motor-side clamping face toward the bed. A rigid, dry PETG prototype is the initial material choice; a specific filament brand/lot, print process and thermal range require qualification. Use 0.16 mm layers, a 0.4 mm nozzle, at least six perimeters and 100% infill. Inspect the slicer to ensure the 1.2 mm tails resolve into connected extrusion paths and that the roots do not contain sparse infill or unbonded islands. The curved blade undersides require deliberately placed, removable support. Keep support contact off the clamping faces, leading/trailing edges and bore where possible. Do not describe this rotor as support-free.

Remove supports and finish each blade consistently. Do not remove material from one blade casually to disguise an unbalanced print. Inspect the bore, hub web, fillet surfaces, roots, tips and every layer transition for cracks, gaps, seams or damage. Recheck tip diameter after finishing. Reject distorted or defective prints. Use a proper low-friction propeller/rotor balancer with a straight metal mandrel for static balancing; a printed bearing or fit coupon does not prove balance. Dynamic imbalance at operating speed requires vibration measurement, not just a stationary balance.

The first full article must be tested behind a containment barrier with the finished front and rear guards, secure mounting, a controlled power limit, measured RPM and a working stop. Conduct staged spin, temperature, vibration and endurance tests before qualifying any desktop-use maximum. Test nut retention and clamping creep after warm operation. Inspect the rotor again after each early test. A cosmetic grille is not a certified fragment containment shield, and its removable interlock must disable torque before access while allowing for coast-down.

## Physical work still required

1. Measure the purchased motor's seat, shaft and thread; test washer/nut engagement and the stationary coupon.
2. Measure actual rotor dimensions, runout, static balance and dynamic vibration.
3. Establish a contained spin-test procedure, independent RPM shutdown and safe coast-down/access behavior.
4. Qualify printed-root fatigue, web creep, warm clamping, layer adhesion and rotor retention.
5. Recheck motor/rotor/guard/stator collisions and insertion order in the full assembly.
6. Measure airflow, pressure, useful throw, noise and power across normal speed and progressive boost. Tune the pitch, chord, stator, throat clearance and panel minimum area from those results.

All remaining physical uncertainties are material requirements for release, even if every CAD and software check passes.
