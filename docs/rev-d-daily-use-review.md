# Rev D daily-use review — 10 October 2026

**Development concept: provisional 5.5/10. Control workflow: provisional 8/10. Actual daily-use performance: not yet rateable.** These are subjective engineering judgments from the current geometry and host-tested firmware, not customer testing or measured product performance. There is no assembled, operating 150 mm fan to assess cooling, noise, comfort, startup reliability or endurance.

The larger rotor and revised shell resolve the study's packaging direction, but do not justify raising the overall score. A fan earns most of its value through comfortable, quiet, reliable cooling. Those properties remain unknown. The inhibited firmware is appropriate for this development state.

| Criterion | Current evidence | User consequence and assessment |
|---|---|---|
| Cooling and throw | 150 mm five-blade rotor, 152 mm throat, 104 × 94 mm outlet; no fan curve or velocity traverse | Unrated. The 5 m/s twist input is not a prediction. Smaller boost area can reduce flow enough to defeat the intended faster jet. |
| Sound | No acoustic measurements or stable-low-speed motor tests | Unrated. A larger rotor may allow a useful lower speed, but drone commutation, blade tones and guard/stator interactions could dominate. |
| Safety and reliability | Exact rotor identity, old-calibration rejection, tested motion inhibition; no printed-rotor qualification or populated main board | Unrated for daily operation. Valid solids and guards do not establish blade retention or fragment containment. |
| Control clarity | Screen status band, large mode/value, relative wheel phase, full-turn boost-entry countdown; 24 detents for normal and boost ranges | Provisional 8/10. Mode text supplements color and every boost exit resets entry progress. A deliberate extra turn costs effort, but follows the user's chosen behavior. |
| Physical interaction | Wheel beside the screen, spin plane parallel to the screen, rigid press support, separate encoder board | Positive layout evidence. The wheel is roughly 30 mm diameter and projects about 9.4 mm from the nominal front face. Actual press feel, sliding and seated reach need a sample. |
| Desk size and aiming | Conservative exchanged-model envelope about 227 × 293 × 200 mm; 194 × 248 mm plinth; 195 mm intended height envelope | Provisional 5/10 for compactness. This is a substantial desk object. A fixed low axis may miss the face; the old Rev C aiming wedges are not qualified for this plinth. |
| Exterior and maintenance | Flowing hollow shoulders, no exposed outboard linkage housing, integral outlet, magnetic cleaning grille, fixed inner guards, separately replaceable TPU | Provisional 7/10 for form and 6/10 for maintenance. The screen, grille and bottom tray are distinct service items. Harnesses, hoses, interlock and all screw/tool paths remain unfinished. |
| FDM accessibility | Source-matched rotor and printed-part mesh checks; head halves need roughly 275 × 185 mm in the chosen orientation | Provisional 4/10. A 300 mm class bed is the straightforward current option. A rear-section split is still needed for common 256 mm printers while preserving the integral final nozzle. |

The scores above are not averaged into a performance score by treating unknown criteria as zero or silently omitting them. The 5.5/10 concept score is retained as a transparent provisional judgment. Source-matched installed views are in `cad/evidence/rev-d-installed-{front,rear,internal}-2026-10-10.png`; their record explicitly distinguishes rendering from verification.

## Interaction improvements already implemented

The wheel and screen now share the lower front surface. This makes feedback visible while adjusting output and removes the side-control reach shown in the earlier layout. Normal maximum leaves the panels open. A fresh full turn at maximum arms boost control; subsequent rotation progressively closes the panels. The screen shows how much of that entry turn remains, and incremental wheel phase is identified as relative rather than an absolute shaft angle.

The flowing head hides the linkage inside its shoulders. The lower plinth reduces the complete height without creating a detachable final nozzle. The cleaning grille has a side pull feature and alignment pilots, while the fixed inner guard remains in place when the grille is removed. The night setting can fully darken the screen and ambient strip, with essential fault indication retained. The active firmware rejects the smaller rotor's saved calibration and retains a default motor-motion inhibit.

## Next improvements and acceptance criteria

1. Complete the actual USB plug route, strain relief, populated-board retention, grille interlock and connected harness/hoses. A person must be able to plug in, clean and service the product without tugging soldered wires or removing unrelated electronics.
2. Use a control/fascia coupon and weighted plinth to measure one-handed operation. The Bourns switch's approximately 6 N press must not slide or tip the fan on a clean, dusty or worn-foot desk; inspect the thumbwheel's rim, nut retention and switch travel.
3. Test the real protected IPS screen at seated distance and beside a window. The principal value, mode and boost countdown must be readable without leaning forward. Small diagnostics can remain secondary. Verify actual control-to-display response and night glare; host-rendered frames cannot establish perceived smoothness.
4. Measure aiming and comfort at the actual desk-to-user distance. Any revised aim geometry or support must stay within the height/stability constraints and be validated with the integral outlet. Do not assume the old six-degree wedges fit or remain stable.
5. Compare normal maximum with several panel settings at equal motor limits. Retain only closure that improves the useful velocity/throw without unacceptable noise, reduced cooling coverage or motor instability. At 75% gross aperture, a 20% mean-speed improvement requires about 90% of normal volumetric flow to remain.
6. Qualify cold starts, the required short startup ramp, power interruptions, sensor faults, cleaning/reassembly and overnight/night operation. At the current initial phase-current limit, the electromagnetic shaft-power allowance is much smaller than the 18 W electrical input ceiling; both must be measured before judging output.

These are specific unresolved acceptance items. They are not claims that the fan is ready for unattended use or that all remaining work can be settled in software.
