# Rev C airflow and progressive outlet design

The P2406 redesign uses a 112 mm, five-blade development impeller in a 114 mm throat. The selected motor drives it through a qualified speed request to the A50S FOC controller. The 18 W ceiling covers the motor and ESC input together. Neither the drone motor's peak rating nor a CAD rendering establishes useful airflow or quiet operation.

Air travels along +Y: rounded rear entry → impeller → rigid motor carrier → trial stator → circular-to-rounded-rectangular transition → integral outlet with two converging panels → fixed guard and magnetic cleaning grille. Electronics and the drive linkage sit outside this path. The final outlet is part of the two structural head halves; it is not a removable nozzle.

## Bell-mouth and internal transitions

The initial bell-mouth has a true 14 mm quarter-circle inner profile, a 2.4 mm wall and a 114 mm throat. Its radius/diameter ratio is 0.123. The shaped mouth reaches 142 mm diameter. A locating spigot and bead are positively captured when the head halves close. The rear fixed guard and mounting flange limit the usable clear entry to roughly 138 mm; this small masking edge is recorded for inlet testing rather than represented as a perfect unobstructed mouth.

The downstream transition spans Y80–110.02 mm, ending at a 104 × 94 mm rounded outlet. The 30 mm length, corner radii, inlet radius, throat, wall and outlet dimensions are adjustable in the local parameters and native Onshape architecture feature. Check the generated thin walls and retained seats after changing dimensions. A smaller outlet does not automatically improve the product: it also raises system resistance and can reduce useful flow.

The motor carrier's four struts support a rigid Ø16 mm pitch-circle motor mount. Its separate TPU sleeve has 0.8 mm radial thickness and 0.4 mm axial lips. Four rigid stops bound nominal carrier movement to 0.3 mm toward each stop. Nominal rotor tip clearance is 1 mm. Print error, bearing runout, balance, compression and creep still need measurement; the nominal stop geometry does not guarantee a safe operating tip gap.

## Straightener choice

Use the short seven-vane radial trial as the initial comparison article: 1.2 mm vane thickness and 18 mm length. It is separately printable and replaceable. The vane count, thickness and length are parameters. A honeycomb is omitted because a dense cellular insert adds friction, occupies axial space and could worsen a low-pressure rotor's operating point. Straight radial vanes provide a printable baseline but are not yet matched to the actual rotor's swirl angle.

The carrier and straightener rings reduce local area, and the guards have approximately 4.8 mm clear slots. Measure the combination rather than rating individual parts in isolation. Compare the trial with an open spacer at the same RPM/input limit, using outlet velocity profiles, flow, static pressure and sound. Retain the vanes only if their reduction of swirl produces a useful net result; otherwise tune incidence/count/length or use the open configuration.

## Progressive one-servo mechanism

Two 55 mm panels hinge at Y110 and Z±47 mm. The matched 24 mm cranks share a guided yoke. A 35 mm connecting rod and 10 mm servo horn move this yoke, so one FS90-FB servo moves both panels symmetrically. At the initial endpoint the yoke travels 5.127 mm and the ideal linkage uses about 31.04° of servo rotation. Smooth metal sleeves carry the pivot loads, and metal shafts, collars and spacers retain the hinges. Keep linkages accessible under the removable curved cover.

For panel angle θ, the initial gross exit-area approximation is:

`A(θ) = 104 × (94 − 2 × 55 × sin θ) mm²`.

The 75% minimum gross area gives a 12.3355° closure angle, below the 15° absolute design bound. Open and minimum gross areas are 9,776 and 7,332 mm² before grille/rib deductions. The rounded-corner correction and actual free area must be included when comparing measured flow. No panel command closes the duct completely. The panels converge smoothly; narrow edge gaps and pivot reliefs still need tolerance/friction checks.

At a fixed flow Q, average exit velocity is Q/A. A 25% area reduction increases average velocity only if boost flow remains above 75% of the open-flow value. The current geometry demonstrates contraction; it does not prove a faster jet or greater throw. Confirm benefit at several closure positions while enforcing the motor power ceiling, and reduce the endpoint if flow, noise or stability worsens.

## Conservative servo load estimate

For a uniform 24 Pa differential across a 104 × 55 mm panel, each panel's hinge moment is approximately `24 × 0.104 × 0.055 × 0.0275 = 0.003775 N·m`. Both panels together require about 0.0315 kg·cm at the servo for an ideal 10/24 leverage ratio. This excludes friction, linkage-angle changes, pressure nonuniformity and acceleration. The servo's published stall torque is not a continuous holding rating. Measure current/temperature and lever force through the complete stroke, including a worst-case jam; use the feedback and timed supply cutoff rather than repeatedly driving an endpoint.

The shipping settings start at 18 Pa soft restriction and 24 Pa hard restriction. These conservative, unqualified thresholds open the panels and reduce load; they are not a measured fan curve or proof of safe pressure. The actual rotor's sustainable range, sensor placement/zero and torque margin are commissioning gates. [Selected feedback servo](https://www.pololu.com/product/3436).

## Tuning and acceptance

- Measure open flow and noise first, then compare straightener/open-spacer configurations at equal RPM and electrical input.
- Sweep closure in small increments, recording flow, centerline/profile velocity, throw, RPM, input/phase current and sound. Keep a measured beneficial endpoint above the minimum area.
- Verify startup, normal stop, faults and grille removal with the rotor inside a containment fixture; the printed guards are not qualified fragment containment.
- Tune inlet profile/guard spacing, stator incidence/count/length, panel endpoint, gaps, servo feedback/pulses, RPM ceiling/minimum and pressure/thermal limits from those results.

The CAD source and native FeatureScript expose geometry. The measurements needed to call this a powerful, efficient and quiet desktop fan do not yet exist.
