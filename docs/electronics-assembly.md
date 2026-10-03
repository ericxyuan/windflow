# Electronics assembly and commissioning

Use the E2 [BOM](../hardware/BOM.md), [wiring specification](../hardware/wiring.md), [power budget](../hardware/power-budget.md) and [circuit review](../hardware/circuit-review.md) together. The firmware uses schema2 calibration and the revised divider scales. This document specifies how to build the electronics; it does not claim that the required carrier PCB already exists.

## Build prerequisites

The next fabrication artifact is a90 x65 mm maximum main carrier, with a22 mm assembled-height allowance including connectors and components. Pico, PD board and the three regulator modules are separately mounted and plugged into it. The exact carrier mounting-hole positions must be coordinated with CAD before fabrication. Also fabricate the small encoder daughterboard and pressure-sensor direct-solder daughterboard. Leave room for plugs, removal tools and wiring bends outside the bare board outline.

Create schematic symbols and footprints from the exact manufacturer package drawings listed in the circuit review, then run ERC/DRC and a schematic-to-BOM reference check. EF1 has a thermal pad: use stencil/reflow assembly and inspect the pad/thermal-via process. A general-purpose SOIC adapter or solderless breadboard does not provide the documented thermal design. Have the carrier fabricated and SMD-populated by a PCB assembly service if suitable reflow equipment and inspection are unavailable. No Gerbers or assembly service order are implied by this project state.

For the Bourns encoder, follow its solder-process limitations on the daughterboard; its data sheet discourages hand soldering. Provide mechanical bushing support so pressing the horizontal-axis wheel does not bend the PCB pins. Hold connectors and modules with screws or printed clamps so solder joints do not carry insertion or cable strain.

## Assembly order

1. Populate the carrier's SMD parts, fuses and connectors. Inspect all polarities and pin1 marks, especially the different SOT23-6 pinouts, SS14, TVS and electrolytics. Leave Pico and all loads disconnected. Confirm no low-resistance short across raw input, protected input,12 V,5 V or3.3 V.
2. Configure HUSB238: cut the default5 V and1 A links; close15 V and2 A. Check cut links are open electrically. Use its native USB-C connector and mechanically support the PCB. Do not modify or open the external mains adapter.
3. Install REG1/2/3 in their labeled sockets and secure them independently. Verify the socket pin mapping using the module silkscreen. Their EN pads remain disconnected; REG1/3 PG route only to their pullups and Pico inputs. Route each high-current return directly to the carrier/regulator ground path.
4. Test EF1 and the three unloaded regulator rails using a protected bench source. Confirm about12 V,5 V and5 V; confirm OVP turns the protected bus off before it can become an unsupported high input. Verify the intended current limit with an electronic load. Remove power and let capacitors discharge before changing connections.
5. Program the detached Pico using a USB-C-to-micro-B data cable and the built UF2. Fit the Pico to its socket, connect only the sensors/encoder/status indicator, then power through the specified PD supply. Confirm3.3 V, status and sensor diagnostics. If using USB alone with PD disconnected, disconnect J2 until the PD board's unpowered I2C behavior has been checked.
6. Connect one load at a time: fan with fixed guard, cosmetic LEDs, then servo with horn disconnected. Confirm the switched supply is off during boot/uncommissioned state. Test each output in service mode before attaching the linkage. Use the actual calibrated open pulse before installing the horn; do not assume1500 us is the correct mechanical open position.
7. Attach and secure the servo feedback plug, main/ambient power and data, guard switch and temperature boards. Label identical XH housings; a keyed connector prevents reversal but does not prevent plugging an unrelated same-size connector into the wrong socket. Use local loom labels and distinct physical routing.
8. Place TEMP1 near the regulator hot region with a repeatable thermally coupled mount, clear of bare power contacts; TEMP2 senses the fan/base air. Route equal short pressure tubes to the static taps; identify the positive and reference ports, protect against pinching and keep them out of rotor/linkage motion.
9. Enter service with the recessed jumper and deliberate boot hold, then follow [calibration](calibration.md). Record PWM/RPM, all five position points, pressure zero and voltage calibration before committing. Remove the jumper after commissioning. Test shutdown, night mode, startup, guard opening, sensor disconnection and saved-setting recovery.

## Enclosure installation

Complete the electrical checks outside the enclosure first. Install the boards so every connector is reachable from the service opening. Use insulating standoffs and leave clearance under PCB solder joints; keep metal washers and inserts clear of traces. Keep the status light visible independently of cosmetic LEDs. Secure the servo/LED loom with a relaxed service loop, then exercise the whole nozzle range while observing it before closing the base.

Do a hot enclosed run at normal full speed and the highest commissioned boost, followed by the simultaneous peak-load test. Record input current, rail minima and component/sensor temperatures. Verify the base can reject regulator heat after a fan stall. A firmware temperature reading alone does not establish the hottest component temperature.

During cleaning, unplug USB, wait for the rotor to stop and reservoirs to discharge, then remove the magnetic grille. The grille sensor stops commanded loads but cannot stop a rotor instantaneously. Avoid pulling modules by their wires or pressure tubes. The internal micro-B connector remains available for recovery; the HUSB238 data pads are not connected in E2.

## Record before calling the electronics complete

Record the carrier PCB revision/gerber hash, final populated BOM, photos of polarity-sensitive parts, continuity/ERC/DRC results, oscilloscope startup/shutdown traces, calibrated divider gains and servo tables, observed peak/continuous current, hot-case temperatures and every fault-test outcome. All of these physical results are currently pending; software simulation and analytical calculations do not replace them.
