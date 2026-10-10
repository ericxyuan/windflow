# Rev D side-facing USB-C access

The first independent port study passed **369 nominal interference checks with zero collisions**, including the changed shell, intact HUSB238 board, two screw/nut sets and their relationships to the rest of the 61-group assembly. It preserves the electrical 15 V / 3 A PD architecture. The completed study is a development candidate until integrated and checked in the whole-stage reports.

The native socket faces the lower left side, away from the screen and thumbwheel, at X = −110.5 mm, Y = 235 mm, Z = −70.4098 mm. A rounded 28 × 20 mm pad joins the flowing shell. Its 16.5 × 9.2 mm R2.2 aperture recesses the socket by 1.6 mm. The larger board cavity starts behind the PCB edge; a separate narrow relief accommodates the protruding socket. This leaves 2.413 mm nominal wall before the port cut, rather than thinning the complete pad to the socket's front edge.

The manufacturer CAD's **two 2.5 mm mounting holes** are used. The 1 mm header holes are not mounting holes. Transformed mount centers are X = −106.847 mm, Y = 227.253 / 242.493 mm. Integrated 7 mm diameter posts support the PCB underside. Two ISO 4762 M2×6 screws and two ISO 4032 M2 nuts retain it; nut pockets have 4.3 mm across flats and 1.9 mm height, with inward insertion slots. These are ideal fastener envelopes without threads. Check actual head/nut dimensions, thread engagement, driver access and PCB strain before freezing the stack.

The selected HUSB238 board remains intact, including its terminal block. No USB voltage or current rating is inferred from connector shape. Configure the current motor architecture's **15 V / 3 A** jumpers and use the documented 45 W supply. This study does not change the motor/ESC input or phase-current limits.

## Small print before the shell

Print `cad/rev_d/power-access-study/USB-side-port-fit-coupon.stl` to check the aperture, socket recess, board support, nut slots and screw reach. It is a single connected watertight mesh: 6,234 triangles, zero boundary/nonmanifold/winding edges and zero degenerate faces. Print in the same PETG/nozzle/layer process intended for the local shell interface. Insert nuts and board without power. Check that the supplied USB plug fully seats, can be removed by its body, and does not load the PCB excessively. Revise the opening and recess parametrically if necessary.

The **15 × 7.5 mm trial cable-boot envelope is explicitly unverified**. It is not manufacturer CAD for the Raspberry Pi supply's captive cable. Its zero overlap only checks that assumed size. Use the real supplied cable for fit; do not claim arbitrary USB-C boots fit. Cable strain relief and the board's output/I2C loom still require installed design and tests.

Reproduce with `cad/rev_d_power_access.py`, then `tools/verify_rev_d_power_access_mesh.py`, using the pinned CAD environment. `power-access-validation.json` and `coupon-mesh-validation.json` identify exact sources and exchanged geometry. The bought-board STEP remains a local reproducible reference; custom shell/coupon and ideal fastener solids are checked in. A later stage update invalidates the earlier pilot's baseline hashes until it is rechecked.
