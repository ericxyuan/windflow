# Printing and assembly — development build

This procedure describes the Rev B straight-through, single-fan design. It is a build sequence for the developing geometry, not authorization to print a finished product. The final outlet is part of the two structural head halves. The removable pieces are the front cleaning grille, internal comparison straightener, service covers and purchased components; do not substitute the separate nozzle study fixture for the product head.

Use this document with the [BOM](../hardware/BOM.md), [electronics assembly procedure](electronics-assembly.md), [calibration procedure](calibration.md) and [physical validation plan](physical-validation.md). The live [deliverable register](deliverable-status.md) records what has actually been completed. The carrier PCB, grille interlock mounting, linkage protection and some component restraints remain design/release dependencies until the corresponding artifacts are present and checked. Onshape integration is a separate deliverable; local STEP exports do not establish that it is complete.

## Choose the right files

`cad/parameters.json` defines the shared mechanical starting dimensions. `cad/build_prototypes.py`, `cad/build_head.py` and `cad/build_base.py` generate the geometry. The head uses millimetres, airflow along +Y, width along X and height along Z. The integrated assembly raises the head centre by the `head_center_height` parameter; do not manually apply that offset to individual printable parts.

| Artifact | Use |
|---|---|
| `cad/prototypes/validation.json` | Generated coupon/part list, mechanism motion checks and their stated limits. Read the report produced by the current source revision. |
| `cad/rev_b/validation.json` | Generated head parts and dimensional checks. |
| `cad/rev_b/base-validation.json` | Generated base parts, vendor placements, fastener locations and sampled service-tray/USB access checks. |
| `cad/rev_b/assembly-interference.json` | Whole-assembly findings for the stated pose and generated files. Resolve every unintended intersection before treating a build as released. |
| Individual `.stl` files named in current manifests | Custom printable parts. Orient each part in the slicer; installed coordinates are not print orientations. |
| `REF-*`, `*-vendor.step`, compression-limiter references and full STEP assemblies | Purchased-item geometry, simplified envelopes or inspection assemblies. Do not print them as replacements for real fans, motors, electronics, metal shafts or fasteners. |
| `nozzle-test-frame` | Independent fit/motion test fixture. Its existence does not make the final nozzle detachable. |

Old exports may remain in a development folder after a geometry change. Select parts from the fresh manifest, not every STL found in the directory. Final quantities, screw lengths and shaft cut lengths must be reconciled against the frozen assembly and BOM. A changed panel key, collar, fan pad or printed skin can invalidate a previously accepted fit coupon.

## Print coupons before large parts

Use the intended printer, dried material, nozzle, layer height and orientation. Label each coupon with its actual size and slicer profile. Measure the finished part after cooling, then test it with the actual purchased item. A nominal CAD diameter is not a measured printed bore.

| Coupon / part | Starting options and acceptance |
|---|---|
| `m3-insert-coupon` | 3.8 / 4.0 / 4.2 mm pilots for the selected RX-M3x5.7 inserts. Choose a fit that installs straight without splitting or bulging the wall and resists the intended screw clamp load. Record insertion temperature and depth. |
| `horizontal-hinge-bore-coupon` | 3.15 / 3.30 / 3.45 mm bores for a 3 mm metal shaft. Check horizontal bridge sag, free rotation and remaining wall strength. The shaft must slide through by hand after normal finishing. |
| `yoke-slot-width-coupon` | 3.2 / 3.4 / 3.6 mm slots for the smooth 3 mm sleeve. Check both travel directions with the real washer stack tightened. |
| `panel-key-clamp-coupon` with `boost-panel-keyed-crank` | Fit the shaft before gently clamping the split hub. Require no cracked key, no shaft binding and no detectable lost panel motion under the measured operating load. Recheck after cycling. |
| `sliding-yoke-coupon`, rod and crank | Check straightness, guide sliding, screw access and clamp-free pivots before assembling a full nozzle. |
| `servo-slotted-bracket` | Measure the actual FS90-FB shaft datum, lug spacing, body, cable exit and supplied horn. The present family-derived envelope is provisional. |
| `encoder-mount-coupon` and wheel variants | Check M7 bushing support and 0.05 / 0.15 / 0.25 mm D-shaft allowances. The 30 mm wheel must rotate without shroud contact and still transmit the encoder's axial push travel. |
| `magnet-pocket-coupon` and keeper | 6.45 / 6.55 / 6.65 mm pockets for 6.35 mm magnets. Test fit, adhesive space and keeper fastening. This coupon's floor is not the final grille magnet gap. |
| `led-channel-coupon` with 0.6 / 0.8 / 1.0 mm diffusers | Use the actual NeoPixel board revision and translucent filament. Check solder-joint clearance, hot spots, viewing angle and light leakage at configured brightness. |
| TPU fan pad/bushing and final `tpu-fan-pad-m3` | Older coupons include M4 options. Use the final M3 mount stack for qualification; check compression, alignment and creep with the metal limiter fitted. |

Also make slicer-cut samples from the current large geometry for the USB receptacle opening and tray fascia, grille magnet pair with both skins, one rear-guard mounting post, one head seam/insert joint and a short panel/hinge section. Preserve the original wall thickness and print orientation in these samples. These are additional test pieces to derive from the frozen model, not claims that individually named exports already exist.

## Material, slicing and finishing

Use characterised PETG for structural parts and TPU 95A for the designated pads, shim and feet. Use translucent PETG for diffusers. Follow the chosen filament's temperature and drying instructions and verify dimensional results on coupons. The enclosure's thermal test determines whether the selected material remains suitable; the firmware's sensor temperature is not a rating for every printed surface.

A useful first profile is a 0.4 mm nozzle with 0.20 mm layers, reduced to 0.12–0.16 mm where curved inlet finish or horizontal holes benefit. Start with four perimeters and five top/bottom layers on structural pieces, with moderate infill in thick bosses. Thin aerodynamic parts require explicit slicer inspection: a 0.8 mm vane should resolve as two continuous extrusion lines, and a 1.6 mm panel as a fully joined wall. Adjust extrusion width/perimeter strategy to the actual geometry instead of assuming a perimeter count guarantees the intended solid section. Keep seams and support scars off the inner inlet, panel faces and guide surfaces.

| Part family | Initial orientation and inspection |
|---|---|
| Head halves | Put the broad split face toward the bed, with each duct half open for support removal. Inspect bearing-arm and guide-tunnel layers individually; use only accessible local supports. Check the seam lies flat after cooling and that support removal does not gouge the air path. |
| Bell-mouth inlet | Start with the flat throat mounting face down and mouth up. The outer lip approaches a horizontal overhang; test a section and use accessible support on the exterior if the profile needs it. Do not fill the curved internal air surface with inaccessible support. |
| Radial straightener | Put a circular end face down, with the airflow axis vertical. Confirm the ring, hub and every vane grow continuously together. Reject missing lines, loose strings or a detached vane. |
| Fixed inner and rear guards | Put the flat grille face down. Rear mounting posts then grow away from the bed. Check rib adhesion, open slots and post strength; a slicer preview is not a finger-access test. |
| Front grille and magnet keeper rims | Print broad faces flat. Confirm the magnet skins and thin keepers are continuous, with no pinholes or lifted corners. Keep mating surfaces flat enough to prevent rattle. |
| Boost panels | Trial the broad outside face down, retaining a smooth air face. Horizontal hinge bores may need local support and finishing. Print a short section first; use an alternate edge orientation only after checking warping and layer strength at the keyed hinge end. |
| Yoke, rod, separate cranks and spacers | Prefer a broad face on the bed with pivot-hole axes vertical where the shape permits. Keep elephant foot out of sliding slots and key sockets. A separate crank avoids making the panel's print orientation serve the entire linkage. |
| Base shell | Start roof down with the service opening upward. Check the USB opening, encoder shroud, light wells and screw bosses for accessible support. Verify the flat roof and head supports remain true. |
| Service tray | Start its flat underside toward the bed, with board supports upward. Check underside nut pockets, the USB fascia and light recesses in layer preview before choosing support. |
| Diffusers | Print flat with consistent layer direction and a repeatable surface finish. Compare transmitted light before selecting thickness; opaque paint or foil must not contact electronics. |
| TPU pieces | Print on a broad flat face using the material's supported profile. Keep each pad/foot separately replaceable. Confirm fill pattern does not leave unsupported compression surfaces. |

Remove burrs and strings, deburr shaft ends and clear designed passages. Hand-ream a selected bore only as needed; do not enlarge all bearing holes blindly. Lightly smooth inlet and nozzle surfaces without changing the measured throat or removing thin vane/panel walls. Clean all debris before installing the fan. Keep adhesive, lubricant and heat-set tooling away from rotor bearings, electronics, pressure bores and sliding guide surfaces.

Install heat-set inserts before purchased electronics and TPU. Use a depth stop and a matching screw to check alignment after cooling. Screws must not bottom in blind inserts. Metal compression sleeves set rigid fan alignment; washers and the selected TPU compression provide compliance without bending the fan frame. Record the final sleeve length and stack instead of relying on a reference cylinder as a cut drawing.

## Mechanical assembly sequence

This is the intended sequence for the current split head and separate keyed cranks. Complete the source-matched insertion checks and tool-access review before a full print. Checks at sampled positions establish nominal rigid clearance only; they do not establish hand access, wiring clearance or tolerance extremes.

1. Inspect all printed parts and complete the coupon decisions. Dry-fit head halves, rear inlet and base without purchased loads. Inspect the integral outlet surfaces and remove every loose particle. Install the required inserts and captive nuts while their pockets are accessible.
2. Prepare the right head half on a support fixture with its split face accessible. Feed the yoke into the outboard guides before connecting either crank. Place the crank-retaining spacers and separate keyed cranks in their outboard locations. The generated insertion study approaches the upper crank from above and the lower crank from below; keep those paths clear.
3. Slide the upper and lower panels into the open split from the left, engaging each double-flat hinge end with its matching crank socket. Keep both panels fully open and parallel. After closing the left shell in step 5, insert the metal hinge shafts from the left through the bearings, spacers and panel bores. Do not force a misaligned key or use a screw to pull the panel into position.
4. Fit the radial straightener, TPU axial shim and fixed inner guard into their respective seats before closing the head. The straightener ring is located between its rear stop and shim/guard stack; verify gentle axial capture without deforming the guard. For an approved comparison run without vanes, maintain guard location and capture with a suitable ring/spacer; do not leave a loose stack.
5. Close the left head half over the aligned assembly. Start all seam screws before tightening evenly. Fit the specified shaft collars outside the bearings, set the measured axial clearance and secure their set screws. Fit crank clamp fasteners with the shaft present, using only enough preload to remove backlash. Check free panel motion again.
6. Fit smooth sleeve/washer stacks through the crank-yoke and rod joints. Tighten onto the metal sleeves so the printed eyes and slots remain free. Fit the removable servo bracket loosely, then the actual servo. Keep its horn disconnected until electrical centring has established a safe pulse. Retain access to the supplied horn's centre screw, bracket screws, collar set screws and crank clamps.
7. Install the fan with airflow toward +Y, its purchased pads and final TPU/metal limiter stack. Route the original cable outside the rotor aperture. Tighten corner mounts evenly to their established stop; verify the rotor remains clear of rigid and soft parts. Fit the bell-mouth and rear guard with the specified rear screw stack. Guard support loads must not distort the inlet.
8. Assemble the four magnet pairs on the bench and mark the attracting faces before adhesive is introduced. Load each head and grille pocket from its designed accessible side, keep magnets seated, then fit the screw-retained rims. The adhesive removes rattle; the retainers prevent a released magnet entering the airflow. Confirm all four pairs attract in the final orientation and the grille can be intentionally peeled away without pulling a keeper off.
9. Fit and adjust the grille-present switch only after its actual mount and contact travel are resolved. Use COM/NO as specified in the wiring document. Verify the removable grille closes the switch reliably without forcing its lever to its hard end. Keep the fixed guard fitted independently. Finish the linkage cover and check its full motion clearance before powered operation.
10. Attach the head to the base using its four support locations while the underside is open for screw access. Confirm no fastener intrudes into the air path and that the head is square to the base. Fit the horizontal encoder in its bushing-supported mount, then the wheel. Verify the exposed rim rolls up/down, pressing acts along the horizontal shaft, and the base does not slide or tip during a press.

Do not improvise an enclosure closure around an unresolved insertion trap. Change the relevant retainer or split and repeat the path check. The head halves must continue to carry the final nozzle; a detachable outlet module is not the remedy for an assembly-order problem.

## Electronics, lighting and service closure

Complete the independent electrical checks in [electronics-assembly.md](electronics-assembly.md) before installing boards in the base. The 90 × 65 × 22 mm carrier reserve is an allowance, not a fabricated board. Its final connectors, mounting holes, component heights and tool access must agree with the carrier design before release. The Adafruit 1782 temperature-board model matches the manufacturer’s current non-STEMMA revision; the 2023 change was silkscreen only. Compare the approximate encoder and servo envelopes with the supplied parts.

Install the tray-mounted Pico, regulator and PD modules with their insulating supports and specified fasteners. Use the current generated fastener table; confirm screws and nuts do not touch traces or underside components. Direct-solder the pressure sensor’s four 2 mm-pitch pins to its dedicated daughterboard. Use the two M2 x 20 housing fasteners, two M2 x 6 daughterboard fasteners and four M2 x 14 temperature-board fasteners with the captive nuts in the tray. The daughterboard is an outline and hole pattern; it still needs routing and fabrication data. Support the USB board at its mounting holes; do not transfer plug insertion loads through soldered signal wires. The USB fascia travels with the service tray so the connector can withdraw through the shell's bottom opening.

Fit the main two-stick LED chain in the front channel, observing DIN/DOUT direction. Put the diffuser in its seat and fasten the retaining frame. Independently retain the status diffuser and lamp after checking its final retainer geometry. Mount the ambient stick facing the desk, connect its separate data chain and install its diffuser and screw-retained keeper. Verify no bare copper or solder joint touches a screw, insert or diffuser. Keep optical cavities clear of wiring that would make visible shadows.

Label every harness at both ends using the connector names in [wiring.md](../hardware/wiring.md). Similar keyed housings still need labels. Route power with its return; keep sensitive analog and pressure wiring away from regulator switching nodes and servo current loops. Secure looms to the final cable-management features, leaving sufficient slack for the defined tray service position and connector removal. Keep the pressure tubing outside hinge, yoke and fan sweeps, without tight bends or tension on sensor nipples. The positive tap must be flush and clear; the ambient reference must be sheltered from the inlet and outlet jet.

With power disconnected, move the panels through the entire range while observing all wires, tubes and cover clearances. Withdraw the service tray along its defined path and check that no plug, nut, USB overmould or loom becomes trapped. Support the tray during service rather than letting it hang by its harness. Connect the servo horn only at the measured open position, then follow the complete five-point calibration procedure. Close the base and fit its TPU feet only after electrical, input, light and guarded mechanism checks pass. Repeat the enclosed thermal and power tests; an open-bench pass does not qualify the closed enclosure.

## Cleaning and replaceability

Unplug USB-C and wait for the rotor to stop before removing the magnetic front grille. The switch cannot stop rotor coast instantly. Wipe or brush printed surfaces without forcing debris into bearings or pressure taps. Do not soak the installed motor, magnets or electronics. Removing the cosmetic grille does not authorize operating with the fixed inner guard removed.

The tray provides access to electronics, internal Pico service USB and the calibration jumper. The linkage cover provides access to the servo, horn and pivots. Shaft collars permit later panel removal using the reverse of the verified insertion sequence. Replace TPU pieces that develop permanent set or cracks, and recheck alignment after retightening. Any replacement servo, changed linkage fit, sensor circuit revision or altered airflow limit requires recalibration and the affected validation tests.

Before calling a print set released, attach its CAD/source revision, generated manifests, zero-unintended-interference evidence, insertion/tool-access review, slicer profiles, final hardware quantities and coupon results. Physical qualification records belong in the companion validation log; none are inferred from the existence of an STL.
