# Windflow daily-use design review

**6 October 2026 revision:** the assessment below applies to the earlier manufactured-fan design. Rev C uses a custom printed impeller and P2406/ESC drive. Its rounded head and front-facing screen improve the intended form and access, but airflow, acoustics, rotor containment and daily-use reliability remain unmeasured. I provisionally rate this changed architecture **5.5/10 as a development concept**, with approximately **8/10 for the specified control interaction**. These are subjective engineering judgments, not an operated-product score. A high-KV drone motor brings no automatic quietness or efficiency advantage at desktop-fan speeds; balance, motor/ESC tonal noise, low-speed control and inlet/outlet losses need guarded measurement. Normal maximum remains open, the full-turn entry countdown stays visible, and each boost session requires a fresh turn. Hardware commissioning and rotor qualification are prerequisites to an actual-user performance rating.

This is an engineering review of the current design and its control workflow. It is not a review of an operated fan. No airflow, noise, comfort, display brightness, pressing force, thermal or endurance measurement exists for the assembled product. Scores below are provisional reviewer judgments on the design, not objective performance results or a certification.

The screen/control checkpoint (`8ede72d`) merits approximately **6.5/10 as a daily-use design concept**. The pushed 24-detent normal range, clearer screen hierarchy and explicit blocked-entry prompts (`422bd7b`) improve the interaction enough to support an **approximately 7/10 revised concept assessment**, with source tests, production rendering and Pico compilation passing. The project remains unfinished engineering; neither score means the present artifacts are ready to power or qualify for unattended daily use.

## Transparent assessment

| Criterion | Screen/control checkpoint | After current interaction improvements | Basis and limit |
|---|---:|---:|---|
| Airflow, useful throw and acoustics | Unrated | Unrated | A straight duct, rounded inlet and pressure-capable real fan are plausible choices. Product flow/noise and whether boost is useful remain unmeasured. |
| Size and physical appearance | 6/10 | 6/10 | The 190 × 150 mm base is plausible for a desktop; side linkage housing and the fixed head add bulk. Printed finish, cables and the view from the normal seated position are untested. |
| Interaction and information hierarchy | 6/10 | Provisional 8/10 | The original 75 normal detents and dominant countdown complicated ordinary adjustment. One normal turn, a large current-power readout, clear entry/boost states and explicit waiting prompts improve it while retaining the user's mandatory entry turn. Reading comfort and tactile behavior remain untested. |
| Safety architecture | 7/10 | 7/10 | Independent pressure, tach, position, temperature/power supervision and fixed guarding are sensible. The interlock interface and real carrier are unfinished, and controlled hardware faults have not been tested. |
| Serviceability | 7/10 | 7/10 | Removable grille, linkage cover, display cradle and bottom tray support maintenance. Full connected-harness removal, tool access and the adopted module interconnection remain open. |
| Power architecture | 7/10 | 7/10 | The selected 15 V / 2 A PD architecture has analytical margin, regulated rails and protected load switching. Real current, inrush, thermal behavior and unsupported-source recovery are unmeasured. |
| Manufacturability and reliability | 6/10 | 6/10 | Split parts, inserts and coupons are useful. Thin features, real fan-mount stack, fasteners, guides, cabling, PCB thermal layout and long-term TPU/printed-part behavior still need completion/qualification. |

The overall estimates are rounded judgments, not a precision-weighted average. In particular, the unmeasured airflow/noise criteria are not silently assigned favorable scores. The revised interaction helps the concept; it cannot compensate for an unfinished electrical or mechanical interface.

## Intended ordinary workflow

The device first needs competent assembly and measured commissioning. An uncommissioned build keeps the actuators disabled and explains the service requirement. That is appropriate for a development product, but it is not an end-user setup experience for someone who only wants a fan on their desk.

After commissioning, connect the specified USB-C PD supply. The controller qualifies power, verifies the open panels and waits for the software-rendered screen. When permitted it performs the required smooth full-power startup ramp, then returns to the saved normal setting. Night, off/zero and unsafe conditions suppress or limit that ramp. A saved boost request restarts at normal maximum with the panels open; the user's full-turn entry must be performed again.

Roll the exposed horizontal wheel upward to raise ordinary power. The revised source uses 24 detents from zero to normal maximum, approximately one physical turn. Commands remain discrete encoder increments, while fan and nozzle motion are slew limited rather than abruptly stepped. The displayed percentage is a normalized control setting; it is not measured airflow, electrical watts or a claim of linear cooling sensation.

At normal maximum, the screen emphasizes the remaining entry turn. Continue upward for 24 detents / 360°. Throughout that turn the fan stays at maximum permitted PWM and the nozzle stays open. Completing the turn enters boost control at zero closure. A further turn progressively narrows the outlet toward the qualified endpoint. Boost changes jet geometry; it does not increase fan power above the allowed maximum.

Turn downward to reduce boost. Reaching zero leaves boost control, and a fresh full entry turn is required next time. If the panels are still opening, the screen should explain the temporary wait. Upward travel during that wait is intentionally not queued for later automatic boost. Continuing down outside boost first unwinds any incomplete entry turn, then lowers ordinary power.

A short press toggles fan on/off. Holding about 1.2 seconds toggles night mode without also generating a short press. Night mode may make the screen completely dark while the fan continues; a real fault restores an essential visible indication if logic power remains healthy. Service entry uses a recessed jumper and deliberate boot hold, which reduces accidental entry during ordinary use.

## Screen and information quality

The screen satisfies the request to combine the former front light bars. Its reserved top 64 rows carry normal power, boost and power/system status. Text labels accompany blue normal, amber entry and purple boost, so color alone does not convey the mode.

The current parent revision places a large **Power percentage** in normal mode, a large **degrees-left countdown** during entry, and a large **Boost percentage** during boost. This is a better hierarchy for ordinary use than making a multi-turn countdown the most prominent normal readout. The relative wheel position remains visible separately. An incremental encoder has no absolute shaft reference, so the displayed phase is relative to boot and wraps every turn.

The Adafruit 4311's active face is only 40.8 × 30.6 mm. On this panel the standard 1× font's visible seven-pixel glyph is about 0.89 mm high; 2× is about 1.79 mm and 3× about 2.68 mm. Supporting instructions and telemetry therefore remain small at a typical seated distance. The host-generated preview establishes the production layout and strip consistency, but cannot establish readability, glare, viewing angle, brightness or night darkness.

Acceptance should use the actual protected screen at the intended desk position: normal power and mode must be readable without leaning forward; the entry turn and blocked-entry reason must be understood without a manual; fault cause and safe next action must remain readable in night mode. Test with ordinary room light, a bright window and a dark room. Use text and position as well as color. Keep secondary PWM/pressure/temperature data subordinate to the user's power and mode, and do not present a computed target opening as a separately measured outlet area.

Startup messages should explain open-position verification and setting restoration. A wrong USB-C source should identify the required 15 V / 2 A PD capability when the screen has power. If the logic rail is absent, the display cannot provide a message; a dark unit must not be described as providing a guaranteed visible power fault.

## Pressing, aiming and physical ergonomics

The wheel axis and rolling action match the specified up/down interaction. Its bushing-supported mount directs the nominal approximately 6 N press load into the shell, rather than asking solder joints to support it. The base must still resist the sideways load on real desk surfaces.

The wheel center is approximately 32 mm above the feet, so a 6 N press produces approximately 0.192 N·m lateral tipping moment. Sliding may be the stronger constraint: using an illustrative friction coefficient of 0.6, friction alone would need more than 1 kg mass to resist 6 N. The actual product mass and desk friction have not been measured; this example is not a mass requirement or proof that the base will slide. Test one-handed short and long presses, worn feet, dusty/smooth surfaces and cable pull before adding ballast or changing the control.

No adjustable aiming joint is present. The fixed horizontal head center is approximately 132 mm above the desk. This may suit hands or nearby low targets, but a user's face can be appreciably higher. Adjustable tilt was not an explicit original requirement; it is an ordinary-use improvement worth evaluating. A stable pitch wedge or a limited aiming provision is preferable to assuming throw distance alone makes the jet comfortable. Any adopted solution must retain the integral outlet, stable base and safe harness/linkage clearances.

The separate linkage cover protects the side mechanism and preserves access. Its bulk is a practical consequence of the chosen one-servo yoke. Do not remove it merely for a slimmer visual profile unless another guarded mechanism provides equivalent assembly and service access.

## Maintenance and settings burden

The magnetic front grille makes regular cleaning convenient, and the independent inner guard is valuable while the rotor coasts. Actual peel force and keeper strength need testing. Air-path cleaning should not require disturbing servo calibration, shaft collars or magnet polarity. Keep the comparison straightener and fixed guard positively captured after any cleaning/reassembly.

The removable display/cradle and bottom tray support replacement, but the verified nominal paths exclude a full installed harness and tools. A serviceable module must also be unplugged and physically removed without pulling solder joints, trapping the screen cable or forcing the pressure tubes into sharp bends. Finish and demonstrate that connected assembly sequence.

Cosmetic adjustment should be proportionate to its risk. The earlier generic service `set` command invalidated commissioning even for brightness changes, forcing a full five-position/pressure/RPM calibration again. The correction is implemented and host-tested: validated display/ambient brightness changes preserve mechanical calibration and can be saved with `commit MEASURED` in service without recollecting the five-angle/pressure/RPM evidence. Changes to servo geometry/LUT, PWM limits, sensing scale and safety thresholds still need their appropriate recommissioning safeguards. The production service-command tests cover cosmetic retention, noncosmetic invalidation, malformed/out-of-range input and unchanged save interlocks. Instructions describe explicit service commit; ordinary operating settings still use delayed storage.

## Priorities and acceptance gates

| Order | Action | Acceptance before treating it as complete |
|---|---|---|
| 1 | Accept the revised interaction and cosmetic settings behavior | Relevant control/input/display/service tests and Pico compilation pass with exit 0; production preview matches the accepted source. Full entry/re-entry and all safety overrides remain intact. |
| 2 | Correct the real fan stack and complete pressure/interlock/harness interfaces | All intended tubes, washers, screws, contacts and cable paths are modeled. No known nominal collision is delegated to physical testing. Assembly/tool/removal paths are checked. |
| 3 | Finish circuit capture and PCB layout | Adopted module interconnection, reviewed netlist, ERC, thermal/current layout, DRC and fabrication files exist for every custom board. A mechanical-only DRC result is insufficient. |
| 4 | Finish the complete product CAD and purchasing schedule | Populated electronics and connectors fit; Onshape mates/parameter behavior and final service paths are recorded; final BOM and print/fastener manifests agree. |
| 5 | Establish physical usability | At the intended desk distance the display is readable, wheel movement is intuitive, presses do not move the base, the jet can be aimed usefully, and cleaning/service paths work with real cables. |
| 6 | Establish physical performance and reliability | Measured flow/throw/noise, stator comparisons, useful boost endpoint, thermal/transient/fault/storage tests and endurance meet recorded acceptance targets with uncertainty. |

This review favors finishing the concrete interfaces and reducing ordinary-use friction before adding more features. The product has a sound direction, but its airflow quality and daily comfort will be determined by the assembled prototype and the measurements in [physical validation](physical-validation.md), not by a provisional concept score.
