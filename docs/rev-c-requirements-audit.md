# Full requirements audit — active Rev C, 8 October 2026

This audit covers the original 24 sections and later changes. The latest instructions take precedence: one P2406 Juicy 2060KV motor and one ESC replace the packaged fan; the clear IPS screen replaces the front light bars; boost requires a fresh full encoder turn after maximum normal output and after each exit. A flowing exterior remains a design requirement. The canonical repository is ericxyuan/windflow.

“Implemented” means an inspectable source/design exists. A local build or nominal collision check is not physical qualification. Unfinished board, harness, mounting-stack and hose design is identified as design work. No assembled product, airflow/noise result or rotor operating approval is claimed.

| Requirement | Current implementation | Remaining work / acceptance |
|---|---|---|
| 1. Complete airflow system | 114 mm throat, R14 inlet, custom112 mm impeller, carrier, trial stator, smooth transition and integrated104×94 mm outlet | Measure fan curve, losses, swirl, throw and sound; compare stator with open spacer. Resolve guard masking and surface finish from tests. |
| 2. Progressive boost | Two55 mm converging panels, matched cranks/yoke and one feedback servo; 75% minimum gross area and12.3355° endpoint | Reopened STEP and native clearance verification; final sleeved pivot fasteners/tool paths; measured friction, torque and useful boost endpoint. |
| 3. Parametric airflow | Native FeatureScript architecture plus local JSON/CadQuery; inlet/throat/stations/wall/outlet/panel/stator/clearance parameters | Detailed physical interfaces are in local source, not all in one native Onshape feature. Future full native feature integration/mates remains design work. |
| 4. Fan and RPM | Superseded by explicit motor change. Exact P2406 and A50S selected; UART speed/health, CRC and7 pole-pair conversion | Exact prop seat/thread/depth and V2.3c envelope; sensorless low-RPM commissioning and independent true-RPM qualification. |
| 5. Encoder | PEC11H horizontal axis, supported PCB/nut/thumbwheel; short on/off and long night press | Real6 N push force, thumbwheel travel, direction, desk sliding/tipping and ergonomics. |
| 6. Main speed/boost bar | Superseded by IPS screen: top64rows status band, distinct text/color and live normal/boost range | Actual screen brightness, viewing-distance/glare and protected-window readability. |
| 7. Downward ambient strip | Eight addressable pixels, recessed channel, replaceable diffuser/keeper and desk clearance | Finish installed cable/strain relief; test hot spots, desk reflection and temperature. |
| 8. Startup and storage | Nonblocking open/verify,1.8s ramp and0.9s return within commissioned ceiling; animation, debounced dual records | Power-loss/write-pause/ESC watchdog bench tests. Off/night/fault limits override ramp; reboot requires fresh boost entry. |
| 9. Temperature | Two MCP9808 boards and ESC temperature telemetry; configurable warning/trip | Sensor1 near power board, sensor2 base air, not winding temperature. Qualify thermal coupling/lag and avoid nuisance trips. |
| 10. Night mode | Long press, configurable screen/ambient darkness, essential faults retained | Physical dark-room readability/fault indication. |
| 11. Magnetic grille | EightD42 magnets, blind pockets, mechanical keeper rings, peel recess; independent fixed guard and grille switch | Actual polarity/holding force, rattling, switch trip/overtravel and magnet retention under operation. |
| 12. TPU isolation | Separately printed0.8 mm radial sleeve/0.4 mm lips, rigid carrier, four0.3 mm stops, desk feet | Print fit, creep/compression/runout and vibration/acoustic results. |
| 13. USB-C | Battery-free15V3A PD, protected input and gated ESC, independent5V rails, fuses/TVS/buffers | Main PCB placement/routes/thermal and installed cable design; rail/inrush/backfeed/load measurements. Ordinary5V is unsupported. |
| 14. Power/charging status | Screen top band shows system/power/fault status; no unnecessary battery | Physical fault/power-source-loss behavior and clear unsupported-supply indication. |
| 15. Exact hardware | Consolidated selected-component/passive/fastener/cable BOM, with unresolved motor clamp explicitly marked | Reconcile every fastener stack and actual supplied connectors; final quantities after PCB/loom completion. |
| 16. Purchased CAD | Vendor screen/Pico/PD/regulators/temp/ambient/pressure models integrated; primary motor drawing and labelled motor/servo/encoder/ESC envelopes | Exact motor and V2.3c STEP unavailable in bounded search. Historical V2.2 downloaded, not substituted as a verified fit. Measure uncertain datums. |
| 17. Calibration | Service shunt plus4s held encoder at boot; bounded serial motor/servo/LED/sensor/direction/settings commands | Hardware commissioning and actual feedback table. Shipping build prohibits rotor motion. |
| 18. Modular firmware | Separate Rev C sketch, control/ESC transport/input/display/lighting/safety/storage/service modules; compiled Pico binary | Hardware timing/electrical/ESC protocol and fault injection. Host results are not runtime qualification. |
| 19. FDM and access | Split head, open-bottom service base, removable tray/cover/cradle, inserts/nuts, separate TPU | Slicer review, final fasteners and tools, connector insertion, physical assembly and supports. No print release yet. |
| 20. Test pieces, fixed nozzle | Thirteen new fit/diffuser/magnet/TPU/hinge/aiming coupons; separate rotor shaft coupons; outlet integral | Print with actual machine/material, adjust parameter fits and repeat before full prints. |
| 21. Safety | Hardwired guard AND, default-off motor rail, UART timeout, thermal/current/voltage/pressure/RPM/servo protections | Bench fault timing, ESC configuration, rotor retention/containment. No repeated stall restart or braking. |
| 22. Final CAD integration | Native10-part adjustable architecture and71-group purchased/mechanical assembly in Onshape | Update exchanged geometry after native findings; complete PCB/harness/hoses/fasteners, tool checks and motion mates. |
| 23. Critical validation | Source hashes, nominal geometry/motion/service checks, schematic/netlist/ERC and firmware assertions/build | Independent exchange checks found a stator-seat error and triggered a fix. Measured cooling/noise/torque/thermal/endurance are still required. |
| 24. Deliverables | Current CAD, firmware, BOM, schematic, pins, power calculations and engineering/printing/service documents exist | Overall task remains in progress while the design items below remain. Do not treat documentation as completion of their geometry/layout. |

## Later instructions checked explicitly

- **Identity:** origin and active links use ericxyuan. Per-command automated commits use ericxyuan / eric.x.yuan@icloud.com under current host instructions; user defaults are preserved.
- **Screen:** front speed/power bars removed from active CAD/electronics. A clear protective window is used over the240×320 IPS display. The top64rows are reserved; normal/boost text, relative wheel phase and remaining entry degrees are visible.
- **Full-turn control:** at maximum normal output, open-panel feedback and confirmed motor readiness are prerequisites. Fresh24detents arm boost while holding the panels open; subsequent24detents progressively close. Leaving boost, off, fault, service or reboot clears authorization. Saved boost restarts at open maximum normal, requiring a new entry turn.
- **Motor/exterior:** one P2406 Juicy2060KV motor, a custom five-blade impeller and one A50S ESC are the active architecture. Rounded shoulders, lofted head and curved base/fairing replace the box fan bay.
- **Onshape:** browser and MCP access were restored on8October. The uploaded integration is inspected in the user's existing document. Original and historical designs remain preserved.
- **Autonomy/resets:** no new competing tasks are created. No usage-reset credit has been redeemed in this run. A reset requires a live five-hour zero-remaining reading and the authorized reset tool; unavailable readings/tooling do not qualify.

## Authorized unfinished design queue

1. Resolve the independent exchanged-geometry/native interference findings and preserve a matching Onshape checkpoint.
2. Place and route the captured protected main board, including real connector lands/thermal return paths; verify schematic parity/DRC and integrate its populated model.
3. Complete the Pico-side keyed transition, pressure daughterboard, pressure taps/hoses and installed looms/strain relief/service slack.
4. Finish all fastener stacks and actual driver approaches; verify insertion/removal and update the source-matched assembly/native checkpoint.
5. Refine exterior seams/aiming/control access using concrete geometry and test pieces. Regenerate dependent reports after changes.

The motor shaft/seat/thread-hand discrepancy, exact supplied ESC connectors and physical speed/noise/thermal limits require supplier or hardware evidence. They must not be filled with fabricated dimensions. [Deliverable index](deliverable-status.md), [airflow and mechanism](rev-c-airflow-and-mechanism.md), [daily-use assessment](rev-c-daily-use-review.md).
