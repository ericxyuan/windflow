# Progressive nozzle mechanism study

The local fixture now contains two converging panels, a common sliding yoke, a connecting rod, an adjustable servo bracket, rigid bearing supports and guide-end stops. `build_prototypes.py` produces the STEP assembly, individual parts, STL coupons, a measured BRep report and `prototypes/overview.png`. It is a mechanism study for integration into the main enclosure, **not a released, removable product nozzle**.

## Datums and integration

All dimensions are millimetres. Air travels in **+Y**, width is X and height is Z. Panel axes are `(Y=0, Z=+47)` and `(Y=0, Z=-47)`, parallel to X. Translate the study by `(0,90,10)` to match the product layout. The 10 mm head height offset is stored in `parameters.json`. Head part exports retain local Z=0; the assembly applies that offset. The script-local `OUTBOARD=17` moves the linkage outside the head's maximum right wall at X=66 without changing the 104 × 94 clear section.

| Item | Installed datum or occupied range |
|---|---|
| Panels, open | Air-facing planes Z=±47, Y=0…55, X=±51.65 |
| Driven cranks | X=73…77, nominal pin radius 24 |
| Yoke | X=77.5…81.5, Z=−77…77; centre Y=0…5.1273 |
| Connecting rod | X=72.5…76.5; 35 mm centre distance; 4 mm thick |
| Approximate servo axis | X=72, Y=−35, Z=−10; axis parallel to X |
| Approximate servo body and flange | X=77.3…99.3; Y=−56.7…−24.1; Z=−16.25…−3.75 |
| Servo mount plate | X=85.3…88.3; two M2 slots on 27 mm nominal pitch |
| Mount-to-frame screws | Axes parallel to X, Y=−11.5, Z=−22 and −32 |
| Rod clearance to X=66 parent wall | 6.5 mm before tolerance or wiring |

The servo envelope is **not exact purchased-component CAD**. The FS90-FB body dimensions are 23.2 × 12.5 × 22. The related FS90-C drawing gives 32.6 mm overall lug span and 27 mm centres, but does not establish the selected feedback variant's complete shaft-to-flange datum. The study uses a provisional 5.4 mm shaft offset from the body centre and 10.9 mm output-to-mount offset. The bracket has 5.8 × 2.6 mm slots, a body window with 0.5 mm clearance per side, and removable M3 attachment. Measure the actual feedback servo before accepting this bracket. Sources: [selected servo](https://www.pololu.com/product/3436/specs), [supplier resources and family drawing](https://www.pololu.com/product/3436/resources).

Files beginning `REF-` are envelopes for purchased items and deliberately have no STL. Use the supplied servo horn and its original spline/centre screw; the approximate horn shape has no usable spline. Verify that the supplied horn can provide a 10 mm pin radius with adequate material around an M2 joint before drilling it.

`boost-panel-upper-test.step` and the lower equivalent are part-local: the hinge is at the origin. The `installed-*-max-boost.step` files preserve the complete study's installed coordinates at maximum nominal boost. `nozzle-test-frame.step` and `servo-slotted-bracket.step` already use installed coordinates. The assembly `nozzle-mechanism-study.step` contains labelled solids and simplified metal shaft/sleeve envelopes.

## Kinematics and hard stops

At panel angle θ, gross exit height is `H − 2 L sin θ`. With `H=94`, `L=55` and minimum area ratio 0.75, maximum nominal angle is **12.3355°**, exit height is **70.5** and exit gross area is **7332 mm²**. The normal gross area is 9776 mm². Side gaps, grille blockage and boundary layers are excluded from these gross areas.

The common yoke travels `s = 24 sin θ`. At maximum nominal closure, `s=5.1273`. Vertical slots accommodate the crank pins' 0.5541 mm vertical movement, imposing equal and opposite panel rotation through one yoke. The servo-to-yoke connecting rod has an exact slider-crank relationship:

```
s = -35 + 10 sin φ + sqrt(35² - [10(cos φ - 1)]²)
```

The required servo swing is **31.0415°**. Rod angle changes only from 0 to **2.3450°**. The mechanism stays far from its toggle position over the commanded range. Firmware must use measured pulse/feedback calibration, since horn spline indexing and real linkage tolerances determine pulse endpoints.

The guide tunnels leave 0.3 mm axial clearance beyond each nominal endpoint. Their closed end walls form secondary mechanical limits. The constricted stop is at **13.0697°**, approximately **73.54% gross area**; it occurs before the shared 15° absolute ceiling. These stops protect against a control error and are not normal operating surfaces. Centre the open endpoint with the panel face flush, not with the servo pressing against a stop. Confirm enough clearance throughout the measured pulse range and ensure servo power is removed on tracking fault.

## Nominal clearance and torque assessment

The report checks 61 equally spaced panel angles, a 0.2056° step, against the frame, servo bracket and approximate servo body. All non-mating moving pairs are checked. The sole excluded pair is the horn's intentional connection to the approximate servo output. The latest `validation.json` records every pair's maximum overlap. This verifies sampled nominal rigid solids, not tolerance extremes, cable sweep, flexible deflection or the final parent enclosure.

Starting allowances are 0.35 mm panel clearance on each side, 0.3 mm diametral clearance on 3 mm hinge rods, 0.4 mm slot clearance over a 3 mm smooth sleeve, 0.3 mm guide clearance per X side, 1 mm axial rod-to-yoke clearance and 0.8 mm axial rod-to-servo-body clearance. Print coupons before adjusting them. Ream bearing bores with an appropriate hand tool rather than forcing a shaft through an undersized print.

At uniform 24 Pa pressure, each panel carries approximately 0.136 N and 0.00375 N·m about its hinge. The combined yoke force is approximately 0.320 N and the calculated servo load at maximum closure is only **0.00267 N·m**. This excludes friction, gravity, acceleration and obstruction; those can dominate such a lightly loaded nozzle. The selected servo's 4.8 V stall torque is 0.1275 N·m, which is not a continuous working rating. Demonstrate free motion manually first, then measure powered operating current and tracking error. A loaded printed guide or trapped cable must not be overcome by increasing endpoint travel.

## Fasteners, smooth bearings and access

- Use two straight 3 mm steel hinge shafts. The assembly shows 155 mm shafts from X=−60.5 to 94.5, retained by four Mädler 62300300 collars (3 mm bore, 7 mm OD, 5 mm width). Cut and retain the final shafts after checking actual frame width and collar/clip placement. They must withdraw axially for service; keep covers removable and do not permanently pot the ends.
- The three main moving joints use a **3 mm OD / 2 mm ID smooth metal sleeve**, M2 screw, washers and a locknut. The sleeve, not the printed eye, takes the clamp load. The current stacks use two 9.1 mm crank/yoke sleeves, one 9.6 mm rod/yoke sleeve and one 8.6 mm horn/rod sleeve, all 3 mm OD / 2.1 mm ID. Use the selected M2 x 14 screws, at most 0.35 mm washers and at most 2.8 mm nut thickness; the geometry reserves at least 0.4 mm thread protrusion. Verify free axial motion after tightening. Use the supplied horn's measured thickness to establish its separate sleeve/washer stack. Do not put screw threads directly against a printed slot.
- Servo lugs use two M2 screws and broad washers over the adjustment slots. Do not crush the plastic servo tabs. Use locknuts after setting the shaft datum.
- Two M3 screws attach the removable servo bracket from the outside to heat-set inserts in the frame. The 4 mm pilot/6.8 mm insertion allowance is a coupon starting point for RX-M3x5.7, not a guaranteed printed fit. Protect nearby guide surfaces from insert-installation heat.
- Retain at least 10 mm tool clearance outside the bracket screw heads and access to the horn's centre screw. The right-side linkage cover must be separately accessible and must contain no wires in the yoke or crank sweep.

The small shaft, sleeve and washer solids in the assembly are dimensional placeholders, not a complete fastener procurement BOM. Final screw lengths depend on measured washers, horn and bearing hardware and must be reconciled with the main BOM.

## Assembly requirement that affects the final enclosure

The final head is split into left and right structural halves with an integral outlet. The cranks are separate double-flat keyed parts with M2 x 16 split clamps. The yoke enters its guides before the crank pins; upper and lower cranks enter vertically from opposite directions. Panels enter through the left split, and the left shell follows. Both 155 mm hinge shafts enter from the left after closing the shell; collars approach axially. The current sampled insertion report contains 13 paths at a maximum 1 mm translational step. It excludes hardware and wiring installed later, tool sweeps and tolerance extremes.

The cover has four integral M3 mounting locations and an open inward face. It withdraws along +X after its screws and cable restraint are released. Whole-assembly checks sample its removal at open, intermediate and maximum boost positions. Keep wiring clear of this path. A slit TPU grommet protects the servo-cable exit; it is not by itself strain relief.

Assembly order: install inserts and captive nuts; insert yoke and retaining spacers; insert separate cranks and panels; place stator/shim/fixed guard; close the left shell; slide in shafts from the left; fit collars and crank clamps; fit sleeved pin stacks, rod and centred supplied horn; align and secure the actual servo; manually check both endpoints; connect feedback and power; calibrate with limited current and safe movement bounds; finally fit the cover. See the product assembly instructions and current reports for the exact boundaries of the checks.

## Printing and coupons

Use dimensionally stable PETG or another characterised engineering filament for the mechanism, and TPU only for the intended isolation coupons. Keep the inside panel surfaces smooth. The 1.6 mm panels require an actual four-perimeter result with a 0.4 mm nozzle or a verified equivalent; do not let a slicer leave sparse, unsupported internal regions. Expect some local support or a deliberate orientation test for the hinge tube; the crank is a separate print. The moving parts are not ready for blind mass printing.

| Small print | What it establishes |
|---|---|
| `horizontal-hinge-bore-coupon` | 3.15 / 3.30 / 3.45 mm horizontal bores, ordered along Y=−15 / 0 / +15; checks bridge sag and 3 mm shaft fit |
| `yoke-slot-width-coupon` | 3.2 / 3.4 / 3.6 mm slots along Z=−12 / 0 / +12; checks the selected 3 mm sleeve |
| `sliding-yoke-coupon` and `servo-connecting-rod` | Print on a broad X face, preserving hole axes normal to the bed; verify smooth edges and no elephant-foot binding |
| `yoke-crank-coupon` | Checks sleeve/washer stack and printed hole strength before making a complete panel |
| `servo-slotted-bracket` | Confirms the actual servo body, lug pitch, shaft datum and connector access |
| `encoder-mount-coupon` and three wheels | M7 bushing fit, 0.05 / 0.15 / 0.25 mm shaft allowance and tactile grip; verify axial press travel after mounting horizontally |
| `magnet-pocket-coupon` | 6.45 / 6.55 / 6.65 mm pockets along X=−15 / 0 / +15; tests pocket fit and the separate keeper before release |
| `led-channel-coupon` and 0.6 / 0.8 / 1.0 diffusers | Board fit, diffusion, hot spots and the real chosen translucent filament |
| `m3-insert-coupon` | 3.8 / 4.0 / 4.2 mm pilots; check straight insertion, pull-out and wall splitting |
| TPU pad and bushing | Existing M4-clearance options only; the final M3/sleeve mount is established by the parent head |

The present magnetic coupon uses a 1.6 mm floor plus a separate keeper. It tests fit and retention construction, not the final grille's 0.4 mm skin holding force. The final grille test must reproduce its exact magnet-to-magnet gap, polarity, support and removal direction.

For the large frame, final shell orientation depends on the assembly split. Avoid inaccessible supports in the airflow path. For the panels, first print a short hinge/crank section using the planned orientation; use a brim if printing the plate on an edge. Inspect layer adhesion at the outboard crank root. A layer crack or tight hinge is a reason to change geometry/orientation, not to increase servo torque.

Physical tuning still required: measured servo datum and pulse range; guide friction and wear; shaft and sleeve fit; fastener length/retention; assembly split and insertion path; linkage cover/wiring clearance; maximum useful constriction, pressure limit, sound and throw; actual magnet retention and LED diffusion. The CAD and low-pressure torque estimate cannot establish those measurements.
