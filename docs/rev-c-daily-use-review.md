# Rev C daily-use assessment — 8 October 2026

The P2406/custom-impeller architecture is provisionally **5.5/10 as a development product concept**, with **8/10 for the specified control workflow**. This is an engineering judgment from CAD and software evidence. An actual user-performance rating is currently unavailable: no assembled fan has been operated or measured. Airflow, throw, sound, comfort, startup reliability and endurance therefore remain unrated.

| Daily-use criterion | Assessment | Why it matters to a user |
|---|---|---|
| Cooling and noise | Unrated | The custom five-blade rotor has no measured fan curve or sound spectrum. The 2060KV motor may add tonal or low-speed commutation noise. A 18 W input cap does not guarantee better cooling than the former manufactured fan. |
| Control clarity | Provisional 8/10 | One normal turn gives usable adjustment. The screen shows the wheel phase and a visible fresh full-turn boost-entry countdown. Mode text supplements color. Boost remains a deliberate extra action. |
| Physical form | Provisional 7/10 | Rounded inlet/head transitions, curved shoulders, an integrated outlet and a rounded service base provide a flowing silhouette. The outboard one-servo linkage and protected switch still add width. Printed seams and finish require an actual sample. |
| Maintenance | Provisional 7/10 | Magnetic cleaning access, independent fixed guards, captured motor/inlet parts, replaceable TPU, a removable LCD cradle and an accessible electronics tray are useful. Connected harnesses and pressure plumbing remain unfinished. |
| Development readiness | Provisional 4/10 | The motor/rotor/ESC is unqualified. The exact ESC case and motor seat are unresolved. The new main board is placed but routing, looms and pressure plumbing remain unfinished. The native architecture and full development geometry are in Onshape, with detailed parametrics retained locally. The inhibited firmware correctly reflects that state. |

These scores are rounded subjective assessments rather than a weighted performance measurement. Improving the screen cannot compensate for unknown noise, blade retention or motor startup behavior.

## Changes made for ordinary use

Normal maximum keeps the outlet open. A further fresh 24 detents enters boost control, and each exit resets that authorization. Progress cannot accumulate while the outlet is reopening, during startup, or while a safety limit is active. The screen explains the wait and retains its top64 status band. A large normal percentage, entry countdown or boost percentage takes priority over secondary diagnostics. Relative encoder phase remains visible; an incremental encoder has no absolute shaft reference.

The front wheel now sits beside the screen, turns parallel to its face and presses toward the enclosure. Its mounting nut and rigid bracket carry the press load, with a separately supported encoder PCB. This brings the control and feedback into one viewing area. The new base gives access to this mount and the clear screen cradle. The downward strip sits behind a recessed replaceable diffuser; the desk feet provide real light clearance. Night mode can fully darken the screen and ambient strip while preserving essential fault indication.

The inlet and motor carrier are positively captured by the split head. The front cleaning grille has captive magnets and a peel recess. The fixed guards remain after cleaning access is opened. Service access no longer depends on holding loose magnets or pulling a PCB by soldered wires. The curved linkage cover has accessible mounting points.

## Remaining interaction improvements to qualify

- **One-handed operation:** the Bourns switch needs approximately6 N. Measure sliding/tipping on a smooth desk, including dusty/worn feet and USB cable pull. A broad base alone is not proof that pressing is comfortable.
- **Readability:** test the actual protected2-inch screen at a normal seated distance and near a bright window. Supporting1× text is small. Keep the primary value readable without leaning forward; leave advanced data in service/status output.
- **Aiming:** the fixed axis is low for face cooling. Two support rails providing a 6° upward trial are now included among the small test pieces. Measure where the jet reaches a seated user; 6° may still be insufficient for face cooling. This is an optional aiming trial, not a qualified fitted tilt joint. Any aiming option must retain stability and the integrated outlet.
- **Startup sound:** the required ramp to100% uses the qualified speed ceiling and takes1.8 seconds, then returns over0.9 seconds. Evaluate whether its sound is distracting. Off, night and unsafe conditions suppress or limit animation/ramp as documented.
- **Boost usefulness:** compare velocity and perceived comfort at normal maximum and several panel angles at the same motor limit. A narrower jet can feel harsher, and restriction may reduce both flow and noise quality. Keep only closure that gives a measured benefit.
- **Daily reliability:** qualify repeated cold starts, night operation, cleaning/reassembly, a disconnected sensor and power-source interruptions before unattended use.

Reopened STEP validation now checks 2,485 nominal pairs, and the current 61-position mechanism sweep plus screen removal has no nominal collisions. The main circuit is captured and all 132 carrier footprints are placed. The useful next product work is power/return-path routing, installed harness/hoses and fastener access, followed by guarded motor/rotor characterization. After those results, replace these provisional scores with measured daily-use feedback.

## Neutral tradeoffs

The custom motor/ESC adds cost, setup and failure modes compared with a manufactured fan. Its high drone power rating says little about useful quiet desk airflow at this project's 18 W limit. A successful design must demonstrate stable low-speed starts and a pleasant sound spectrum, not merely a high centerline velocity.

The visible extra turn makes accidental boost less likely, but it takes more rotation than a simple speed dial. The countdown and distinct mode text explain that cost; testing with a new user should establish whether entry feels deliberate or tedious. The wheel phase is relative, since this incremental encoder has no absolute shaft reference.

The rounded shell improves the silhouette, but the side linkage, guard switch and service base add bulk. The current CAD is a substantial desk object rather than a pocket-size fan. Cosmetic form is therefore provisional until a printed sample confirms seams, reach, glare and cleaning access.

Do not present the 5.5/10 concept assessment as a tested daily-use score. Airflow, sound, comfort, power use and reliability remain unknown; no unbiased evaluator can score those from CAD alone.

The front encoder relocation improves reach and makes the control easier to associate with the screen. Its face remains parallel to the screen while turning. The revised orientation may reduce sideways pushing, but a measured sliding/tipping test is still required; it does not justify raising the readiness score. See [front controls](rev-c-front-controls.md).
