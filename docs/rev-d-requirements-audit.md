# Current requirements audit — Rev D, 10 October 2026

This audit covers all 24 original sections and subsequent instructions. The current candidate follows the complete `rotor_selection` study: a 150 mm five-blade rotor in a flowing 195 mm intended-height product, driven by the requested P2406 Juicy 2060KV and one telemetry ESC. The screen/full-turn control changes supersede the original front light bars and threshold-only boost entry. Earlier Rev B/C geometry and reports are preserved as history.

An implemented design is an inspectable artifact. It does not establish physical cooling, acoustics, structural safety or daily reliability. Unfinished PCB, wiring, pressure plumbing and mounting design remain engineering work, even when their reserves fit.

| Original requirement | Current evidence | Unfinished design or physical acceptance |
|---|---|---|
| 1. Airflow system | Actual 150 mm rotor, 152 mm throat, R12 inlet, carrier, seven curved trial stator vanes, 85 mm contraction, 104 × 94 mm outlet and fixed guards | Fan curve, volume/velocity/throw, guard losses, noise and stator A/B require measurement. The 5 m/s rotor twist input is not predicted output. |
| 2. Progressive boost | Two 55 mm panels, one feedback servo and matched symmetric linkage; 61 poses and moving-pair checks pass | 75% minimum gross aperture gives a 12.3355° endpoint. Measured torque, friction, net outlet area, motor stability and useful boost remain unqualified. |
| 3. Parametric aerodynamics | Local JSON/CadQuery detailed geometry; native Onshape seven-part, 17-input airpath and separate native rotor | Detailed interface geometry is not all contained in the native study. Assembly mates and final detailed native integration remain open. |
| 4. Fan and RPM | Original packaged-fan choice superseded by requested motor/ESC; bounded CRC UART parsing and seven pole-pair conversion | Exact shaft seat/thread/hand/depth and ESC V2.3c connector envelope require supplier or measured evidence. Compare FOC observer RPM to an independent tachometer. |
| 5. Rotary encoder | Wheel beside screen, shaft normal to screen, spin plane parallel; 96 nominal rotation/press poses pass | Confirm direction, detents, switch travel/force, thumb comfort, and desk sliding/tipping on a physical fascia sample. |
| 6. Main speed bar | Superseded by Adafruit 4311 IPS, top 64-row status band, mode/value, relative wheel phase and entry countdown | Actual readability, glare, brightness and perceived response need hardware tests. |
| 7. Ambient strip | Eight downward addressable pixels, recessed diffuser and low plinth | Complete installed retention/loom/strain relief, then test desk hot spots, temperature and night brightness. |
| 8. Startup | Nonblocking open/verify, synchronized 1.8 s ramp within a commissioned ceiling, 0.9 s return and saved settings | Distributed firmware inhibits motor motion. Hardware ramp, power interruption and flash-write timing remain untested. Saved boost returns to open normal maximum and requires fresh entry. |
| 9. Temperature | Two MCP9808 boards and ESC telemetry, configurable protection | Both current boards sit in electronics shoulders; neither measures winding temperature. Qualify locations, coupling, lag and thresholds. |
| 10. Night mode | Long press, configurable screen/ambient darkness and essential fault indication | Actual dark-room brightness and fault visibility remain physical checks. |
| 11. Magnetic grille | Four paired D42 locations, covered pockets, alignment pilots and pull tab; permanent inner finger guard | Re-integrate the hardwired grille switch and its loom. Magnet polarity/retention, anti-rattle behavior and coasting access remain physical checks. |
| 12. TPU isolation | Separate carrier isolation ring and four replaceable feet; rigid motor carrier maintains alignment | Radial/axial fit, creep, runout and vibration transmission need printed coupons and loaded tests. |
| 13. USB-C | Battery-free 15 V / 3 A PD baseline, protected input/default-off ESC and two 5 V rails; selected modules present | Main-board routing/thermal review, external USB port retention/plug access and installed power wiring remain design work. Ordinary 5 V is unsupported. |
| 14. Power/status bar | Replaced by the reserved IPS status band; no battery added | Unsupported-source, brownout and fault indication need electrical tests. |
| 15. Exact hardware | Selected-component and captured-circuit BOM retained from Rev C; current mechanical decisions recorded separately | Reconcile new mounting stacks, quantities, loom lengths, supplied connectors and unmeasured motor clamp. BOM is not yet a final order list. |
| 16. Purchased CAD | Nine inherited vendor placements reproduced from source manifests; included in detailed stage | Motor/servo/encoder/ESC use explicitly labelled drawing envelopes. Historical ESC V2.2 CAD is not exact V2.3c fit evidence. |
| 17. Calibration | Recessed service shunt plus held encoder at boot; bounded serial motor/servo/display/sensor/settings commands | Schema 5 binds the exact 150 mm P2 STEP article; old/other-article calibration is rejected. Actual feedback, speed/pressure/thermal limits require commissioning. |
| 18. Firmware | Modular current source in historical `firmware/WindflowRevC`; 4,187 main assertions, 60 shipping service assertions, 73 qualified host-simulation assertions and Pico build pass | No device flashed or operated. Default motion inhibition and no approved rotor RPM remain explicit. |
| 19. FDM | Separate printed structure/TPU, split head, integral outlet, service tray; all 28 stage STL topology checks pass | Current approximately 275 × 185 mm head halves need a 300 mm class bed. A rear split for smaller beds, slicer/support review and final assembly access remain open. |
| 20. Test pieces, fixed nozzle | New M5 bore/clamp and stationary root/edge coupons; previous control/magnet/TPU/hinge/diffuser coupons retained as history | Adapt historical coupons to changed interfaces before claiming current fit. Final nozzle stays integral. |
| 21. Safety | Default-off motor rail, guard AND circuit, UART/temperature/current/voltage/pressure/RPM/servo logic; shipping inhibit tested | Current grille-switch geometry, populated PCB/harness and pressure taps/hoses are unfinished. Printed guards are not qualified rotor-fragment containment. |
| 22. Full CAD integration | Detailed 61-group stage has 1,830 nominal pairs with no unintended overlap; native rotor and seven-part airpath exist online | Complete main-board population/retention, looms/hoses/interlock/fasteners/tool approaches and native motion mates. A major-profile native study is not the detailed fit article. |
| 23. Critical validation | Current full motion report passes 22,570 mechanism/fixed, 1,281 moving-pair, 5,664 wheel, 2,958 screen-service and 60 rotor-envelope checks; exact 195 mm height passes | Nominal sampled geometry only. Tolerance extremes, connected service access, spin/balance, cooling/noise/thermal/torque/endurance require additional work. |
| 24. Deliverables | Current CAD sources, inhibited firmware, selected BOM, circuit/wiring/pins/power and engineering documents are indexed | Overall project remains in progress. The queue below distinguishes unfinished design from physical testing. |

## Later instructions checked

- **Rotor study first:** complete archived analysis and source snapshots reviewed before the 150 mm design. Five blades are the baseline; seven at equal solidity is a comparator, mixed flow a fallback. The complete-product 200 mm limit governs packaging.
- **Exterior and controls:** flowing hollow shoulders hide the linkage; low plinth replaces the tall electronics box. Wheel and screen share the lower front. The final outlet is integral.
- **Full-circle boost:** normal output uses 24 detents; another fresh 24 at maximum normal output arms boost with panels open, then 24 progressively adjust closure. Every exit, off, fault, service or reboot clears entry progress. Screen text and countdown make the transition visible.
- **Maintenance:** a failed backward/downward display-and-cradle path was found and preserved at `b70a79d`. The corrected display-only forward path passes; cradle replacement still needs shell opening. Loom and driver access remain separate unfinished checks.
- **GitHub identity:** canonical repository is ericxyuan/windflow. Automated commits use ericxyuan / eric.x.yuan@icloud.com for both author and committer, without changing manual defaults. Completed work is committed and remote verification uses the actual remote tip.
- **No competing work:** browser interaction and CAD mutation stay in this task. Local independent studies do not overwrite geometry under an active verification run.
- **Usage reset authorization:** maximum two existing resets across the project, only with a live five-hour reading of zero remaining and the authorized reset tool. No reset was redeemed in this run; missing readings/tooling do not qualify.

## Authorized unfinished design queue

1. Preserve a source-matched complete exchange and Onshape checkpoint of the checked 150 mm assembly, with explicit STEP/mates limitations.
2. Integrate the external side-facing USB port with board retention, plug/cable clearance and fit coupon; regenerate dependent stage/mesh/motion/export evidence.
3. Re-integrate grille interlock, pressure taps/hoses and installed wiring with service slack and strain relief.
4. Finish and review main PCB routing/thermal paths, keyed Pico transition and pressure daughterboard; integrate their populated geometry and retention.
5. Resolve every fastener stack, insertion/removal and driver approach; refine printer-specific splits and aiming/stability without making the final nozzle detachable.
6. Reconcile the final BOM, assembly sequence and current Onshape geometry against all changes.

Physical tests remain separate: shaft/root coupons, FDM material/process strength, guarded rotor qualification/balance/retention/tip deflection, low-speed motor/ESC compatibility and true RPM, pressure/swirl/stator comparison, normal/boost cooling/throw/noise, servo load/jam/endpoints, voltage/inrush/thermal/fault behavior, grille retention, screen/encoder feel/night mode, stability and endurance. None has been substituted with a render or software assertion.

[Deliverable register](deliverable-status.md), [current CAD and assembly development](rev-d-150mm-cad.md), [neutral daily-use review](rev-d-daily-use-review.md).
