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

## USB-to-fuse copper branch — 12 October 2026

The next isolated candidate connects `PD_RAW` from J1.1 to F1.1 through 16.1 mm of 2.4 mm top copper, two 0.6/0.3 mm through-vias and a 1.55 mm-long, 1.4 mm-wide bottom pad neck. The paired vias share a symmetric 1.0 mm-wide stem and sit outside the fuse solder land. [Parameters](../hardware/pcb/rev_c/route-study/input-copper-parameters.json), [builder](../tools/build_rev_c_input_copper_candidate.py) and [native/development record](../hardware/pcb/rev_c/route-study/input-copper-development.json) preserve this geometry and its input/output hashes.

The previous display/encoder routes crossed the power-device escape region. The candidate removes six explicitly declared signal nets (`ENC_A`, `ENC_B`, `TFT_RST`, `TFT_RST_BUF`, `EF1_PGTH`, `PG_INPUT`) for rerouting. It does not move components or change the circuit or fabrication rules. Native KiCad reports **zero clearance/fabrication violations, zero schematic-parity findings, zero missing PD_RAW connections and 61 other missing connections**, with **exit code 5**. This is an incomplete board, not a full native pass or a fabrication release. The increased missing-connection count reflects the removed signal routes and must not be hidden by comparing only the completed input branch.

At reference-temperature copper resistivity, a simple DC calculation gives approximately 4.57 mΩ with 35 µm copper and 2.58 mΩ with 70 µm copper, including an assumed 25 µm-plated, 1.6 mm-long pair of barrels sharing current equally. At 3 A these correspond to about 13.7/7.7 mV drop and 41/23 mW copper loss. The 6 A review case gives about 27.4/15.5 mV and 165/93 mW. These estimates omit the fuse and connector resistance, pad spreading, unequal sharing, plating variation and temperature rise. They are not current-capacity or thermal qualification, and do not establish a permissible overload.

Run this builder only after the current ground-return candidate and its source-matched report exist. It writes under `build/rev-c-board/input-copper-candidate`; the authoritative unrouted board and the independently connected minimum-width study remain unchanged.

## Displaced signal recovery — 12 October 2026

All six displaced signal nets are now reconnected around the retained input-power copper. The [protected-input exporter](../tools/export_rev_c_signal_recovery_input.py), [preserved routing session and manifest](../hardware/pcb/rev_c/route-study/signal-recovery-session-manifest.json), [reviewed corrections](../hardware/pcb/rev_c/route-study/signal-recovery-corrections.json) and [candidate builder](../tools/build_rev_c_signal_recovery_candidate.py) reproduce this separate candidate. In1.Cu is inactive for signal routing. The importer accepts only the six declared nets and keeps every existing power/return track, via, component position and pad net unchanged; it discards all other router output.

Native review found a tight ENC_A corner after raising the router's narrow segments to the required 0.2 mm, plus two unfinished signal links. The corrected corner moves its incident endpoints by 0.02 mm. The two completed links use clearance-checked bounded paths around existing copper; an unnecessary single-layer via is removed. These corrections are included in the reproducible builder and independent native check, not waived as exceptions.

The [current recovery record](../hardware/pcb/rev_c/route-study/signal-recovery-development.json) reports **zero clearance/fabrication violations, zero schematic-parity findings, zero missing PD_RAW or selected signal connections, and 50 other missing connections**, with **exit code 5**. Power/return connections still prevent manufacture. The earlier 51- and 61-finding reports remain evidence for their own stages. Neither successful signal recovery nor the calculated input resistance completes the power/thermal design review.

The next PCB work is to redesign the power routes and returns, check regulator/eFuse/FET decoupling loops and heat spreading, finish the remaining connections, and rerun native checks at all severities. Record any deliberate short pad necks, their current allocation and their surrounding copper. Then review actual voltage drop, dissipation, stackup and component thermal limits before adopting the routed board and populated CAD. Physical voltage/inrush/load/thermal/EMC tests remain necessary after this design review.

The encoder daughterboard's separate native route checks remain distinct from this main-board candidate. This milestone does not change firmware motion inhibition or qualify the printed rotor.
