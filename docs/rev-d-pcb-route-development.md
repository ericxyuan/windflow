# Main PCB routing development

The captured 80 × 55 mm, four-layer circuit has a reproducible **connected routing candidate**. KiCad 10.0.6 reports zero clearance/fabrication violations, zero unconnected items and zero schematic-parity findings for this candidate, with `--severity-all --schematic-parity --exit-code-violations` and exit code 0. The authoritative placed board is still unrouted. Neither board is approved for manufacture.

The initial routing session, [session manifest](../hardware/pcb/rev_c/route-study/session-manifest.json) and [current candidate report](../hardware/pcb/rev_c/route-study/minimum-route-validation.json) preserve the design input and exact verification snapshot. [The reproducible candidate builder](../tools/build_rev_c_route_candidate.py) imports this checked session into an isolated working directory, verifies current footprint placement and pad nets, enforces the existing 0.2 mm minimum track width and moves five crowded bends. It changes 226 track widths and 22 incident endpoints, including the connected via at the UART bend. The fabrication rules, circuit and pads are unchanged.

Run the builder with the pinned KiCad Python at `.tools/kicad-10.0.6/bin/python.exe`. It writes the candidate under `build/rev-c-board/minimum-route-candidate`, then runs the pinned native KiCad checker. It does not write Gerbers or replace the authoritative board. Generated KiCad identifiers can differ on regeneration; always use the fresh report for the regenerated artifact.

## Why this is not the power-board release

Several power nets, including the protected 15 V bus, ESC feed, servo rail and logic supply, contain long 0.2 mm tracks. The current requirement includes a 3 A input and larger servo transients. Connectivity and clearance do not demonstrate that these tracks can carry those currents with acceptable drop and temperature. Treating the native routing pass as power qualification would be incorrect.

A separate initial route with wider power classes had 123 unconnected findings. Its missing connections include ground-plane access and the fine-pitch power-device pad escapes. It has not been adopted. Wide tracks cannot simply start at every fine-pitch pad; short reviewed necks, parallel copper and appropriate vias must connect those devices to adequately sized power and return copper.

## Wider-power return development — 12 October 2026

[The preserved wider-class session](../hardware/pcb/rev_c/route-study/power-session-manifest.json) and [reproducible return builder](../tools/build_rev_c_ground_return_candidate.py) now produce a separate candidate with a dedicated In1.Cu ground plane, 46 direct ground escape vias, six short bent escapes and 24 shared/previously overlapping ground links. The exact counts and all input/output hashes are in [the development record](../hardware/pcb/rev_c/route-study/ground-return-development.json). The plane contains no routed signal tracks; existing eFuse exposed-pad thermal lands reach this return layer.

The native checker reports **zero clearance/fabrication violations, zero schematic-parity findings, and 51 missing connections**. It returns **exit code 5**, and the record is labelled **INCOMPLETE**. This is not a full DRC pass. Seven ground pads remain disconnected, with other missing connections on the protected power branches and two screen-select findings. The independently connected minimum-width study still has its own zero-missing-connection result; these two studies must not be conflated.

The escape geometry avoids new vias in SMD solder lands, respects the current 0.6 mm via / 0.3 mm drill and 0.2 mm track rules, and leaves component positions and pad nets unchanged. Return branches use 0.2–0.5 mm tracks; their geometry does not allocate all power current or qualify pulse impedance. Native hole/clearance checks include the added vias. No fabrication outputs are produced.

The [TPS2663 manufacturer layout guidance, section 9.6](https://www.ti.com/lit/ds/symlink/tps2663.pdf) calls for a short plane connection from the external FET drain to the device inputs, close bypass/support components, short power paths sized for twice the full load, and ground-plane heat spreading beneath the exposed pad. The current placement and partial routes still need review against those requirements; a connectivity result alone would not meet them.

The next PCB work is to redesign the power routes and returns, check regulator/eFuse/FET decoupling loops and heat spreading, finish the remaining connections, and rerun native checks at all severities. Record any deliberate short pad necks, their current allocation and their surrounding copper. Then review actual voltage drop, dissipation, stackup and component thermal limits before adopting the routed board and populated CAD. Physical voltage/inrush/load/thermal/EMC tests remain necessary after this design review.

The encoder daughterboard's separate native route checks remain distinct from this main-board candidate. This milestone does not change firmware motion inhibition or qualify the printed rotor.
