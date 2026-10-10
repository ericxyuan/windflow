# Main PCB routing development

The captured 80 × 55 mm, four-layer circuit has a reproducible **connected routing candidate**. KiCad 10.0.6 reports zero clearance/fabrication violations, zero unconnected items and zero schematic-parity findings for this candidate, with `--severity-all --schematic-parity --exit-code-violations` and exit code 0. The authoritative placed board is still unrouted. Neither board is approved for manufacture.

The initial routing session, [session manifest](../hardware/pcb/rev_c/route-study/session-manifest.json) and [current candidate report](../hardware/pcb/rev_c/route-study/minimum-route-validation.json) preserve the design input and exact verification snapshot. [The reproducible candidate builder](../tools/build_rev_c_route_candidate.py) imports this checked session into an isolated working directory, verifies current footprint placement and pad nets, enforces the existing 0.2 mm minimum track width and moves five crowded bends. It changes 226 track widths and 22 incident endpoints, including the connected via at the UART bend. The fabrication rules, circuit and pads are unchanged.

Run the builder with the pinned KiCad Python at `.tools/kicad-10.0.6/bin/python.exe`. It writes the candidate under `build/rev-c-board/minimum-route-candidate`, then runs the pinned native KiCad checker. It does not write Gerbers or replace the authoritative board. Generated KiCad identifiers can differ on regeneration; always use the fresh report for the regenerated artifact.

## Why this is not the power-board release

Several power nets, including the protected 15 V bus, ESC feed, servo rail and logic supply, contain long 0.2 mm tracks. The current requirement includes a 3 A input and larger servo transients. Connectivity and clearance do not demonstrate that these tracks can carry those currents with acceptable drop and temperature. Treating the native routing pass as power qualification would be incorrect.

A separate initial route with wider power classes avoids geometric violations but still has 123 unconnected findings. Its missing connections include ground-plane access and the fine-pitch power-device pad escapes. It has not been adopted. Wide tracks cannot simply start at every fine-pitch pad; short reviewed necks, parallel copper and appropriate vias must connect those devices to adequately sized power and return copper.

The next PCB work is to redesign the power routes and returns, check regulator/eFuse/FET decoupling loops and heat spreading, finish the remaining connections, and rerun native checks at all severities. Record any deliberate short pad necks, their current allocation and their surrounding copper. Then review actual voltage drop, dissipation, stackup and component thermal limits before adopting the routed board and populated CAD. Physical voltage/inrush/load/thermal/EMC tests remain necessary after this design review.

The encoder daughterboard's separate native route checks remain distinct from this main-board candidate. This milestone does not change firmware motion inhibition or qualify the printed rotor.
