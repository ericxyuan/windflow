**I recommend a 150 mm, five-blade ducted axial rotor with broad, cambered, twisted and moderately swept blades**, combined with a rounded inlet, a matched downstream stator and a smooth adjustable outlet. It is the strongest first candidate for combining high useful airspeed, quiet normal operation and a noticeable boost within your **200 mm total height**.

The strongest competing shape is a **mixed-flow rotor**, which combines axial and radial flow. It could outperform the axial design if the outlet contraction demands more pressure than the axial rotor can provide efficiently. The available evidence supports this development choice; it does not yet establish a measured fastest or quietest winner.

I’ve saved the [full analysis and calculations](/C:/Users/admin/iCloudDrive/Windflow/docs/fan-shape-analysis-2026-10-09.md), including the motor matching, diameter comparisons, height budget and boost targets.

![Proposed rotor shape and complete-product layout concept](/C:/Users/admin/iCloudDrive/Windflow/docs/fan-shape-study-2026-10-09/rotor-and-layout-concept.png)

*This is a concept schematic. The blade sections and revised component placement still need detailed design.*

Your motor is the **T-Motor Pacer V4 P2406 Juicy 2060KV**. Its published **1,116 W rating is a one-second peak** under drone conditions. Your current desktop architecture supplies the motor and A50S controller through an **18 W input limit**, so the design should use its capability within that electrical and thermal envelope. Using its entire published peak would require a substantially different power system. [Motor specification](https://www.ligpower.com/product/p2406-fpv-freestyle-motor.html).

The shape comparison favours the following options. These are engineering assessments of the complete fan stage, rather than measured performance rankings. Pressure demand and flow separation are central to choosing between axial, mixed-flow and centrifugal designs. [Manufacturer’s explanation of fan architectures](https://mag.ebmpapst.com/en/insights/axial-diagonal-centrifugal_2447/).

| Fan shape | Effect on your targets | Assessment |
|---|---|---|
| Two or three narrow propeller blades | Good unrestricted flow, but harder to maintain flow through a guarded, contracted outlet at low RPM | Poor first choice for effective boost |
| **Five broad, swept and twisted axial blades** | Balances blade loading, pressure capability, drag and a direct airflow path | **Recommended starting shape** |
| Seven swept axial blades | Can distribute loading and improve pressure performance; sound depends on total blade area and blade–stator interaction | Main blade-count comparison |
| **Mixed-flow rotor** | May retain more flow as the outlet contracts, giving stronger useful airspeed | **Primary alternative** |
| Backward-curved centrifugal impeller | Strong pressure potential for a narrow jet; needs a scroll and a different airflow layout | Worth considering if concentrated jet speed dominates |
| Many-blade, high-speed EDF shape | High-speed jet emphasis, with greater potential for intrusive tones | Low priority for quiet desktop use |

**The motor’s torque limit needs attention before increasing diameter.** Your current initial limit is **3 A of motor phase current**. A rough calculation from the motor’s KV gives approximately **3.8–4.4 W of electromagnetic power at 3,000 RPM**, before friction and core losses. The range reflects different current conventions; it is not a measured torque map for your controller. [Torque-constant convention reference](https://newdocs.odriverobotics.com/v/latest/guides/odrivetool-setup.html).

That means the motor can reach its current limit well before delivering useful power comparable to the 18 W electrical budget. For perspective, producing **10 W at 2,500 RPM** would require roughly **8–10 A** under those illustrative conventions, before loss compensation. Those figures identify what needs qualification; they are not new ESC settings to apply. If 3 A must remain the permanent limit, a **125–140 mm rotor** deserves comparison because a large, slow rotor could become torque constrained.

Your larger-rotor reasoning is correct for airflow, but pressure must be included. For geometrically similar fans, enlarging a 112 mm rotor to 150 mm could match its airflow at about **1,250 RPM instead of 3,000 RPM**. However, it would retain only about **31% of the pressure capability** at that corresponding point. This is a scaling illustration, not the proposed rotor’s operating speed. [Fan scaling laws](https://beckettair.com/resources/fan-laws/).

The 150 mm design therefore needs blades that maintain flow through the outlet. Simply enlarging the current blades and lowering RPM would risk weakening boost. Equally, running the larger rotor at the same RPM increases tip speed and loading, so larger diameter alone does not establish quieter operation.

For noise reduction, I would integrate these features into the selected shape:

- **Spanwise twist and camber**, so each part of the blade works at a suitable angle instead of using one flat pitch.
- **Broad mid-span sections with gradual tip taper**, balancing pressure capability against drag.
- **Moderate sweep**, compared against an unswept version at equal useful output.
- **Smooth leading edges and consistently finished trailing edges**; the current printed tip sections have relatively blunt trailing edges.
- **A stator matched to the rotor’s swirl**, with streamlined motor supports and suitable spacing.
- **A rounded inlet, flush internal joints and a controlled tip gap**, reducing disturbances before and around the rotor.

Tip leakage and its interaction with the housing are established noise sources, but their improvement cannot be assigned a reliable dBA value for this prototype without measurement. [Blade-tip noise mechanisms](https://mag.ebmpapst.com/en/products/fans/the-formula-for-vorticity_11766/).

**Boost should use both a reserved speed range and the outlet contraction.** The current control uses the same maximum rotor speed in normal and boost modes, so its boost benefit depends entirely on how much flow survives the smaller outlet.

At the current **75% outlet-area endpoint**, continuity gives:

| Flow retained after closure, at the same RPM | Average outlet airspeed increase |
|---|---:|
| 100% | +33.3% |
| 95% | +26.7% |
| 90% | +20.0% |
| 80% | +6.7% |
| 75% | No increase |

I would reserve roughly **15–20% of the qualified maximum RPM above normal maximum**, then coordinate that reserve with the measured beneficial panel travel. Keep the fresh full encoder turn to arm boost. Set an acceptance target of **at least 20%, preferably 25–30%, higher average outlet velocity than normal maximum**, with a useful increase still apparent at 0.5 m. These are proposed targets, not predicted results.

For packaging, I propose a **195 mm total height budget**: a 185 mm head envelope including the inlet, guards and linkage, plus 10 mm of base/feet extension. A 150 mm rotor, 152 mm throat, 12 mm inlet radius and 2.4 mm wall give an inlet outer diameter of **180.8 mm**. The screen and encoder would occupy the front lower portion below the outlet, while electronics use lower and side pockets outside the air duct.

The current source-matched local assembly report reaches about **215.9 mm from feet to linkage cover**, so rearrangement is necessary even before enlarging the rotor. The proposed 195 mm layout leaves 5 mm of height reserve, but its revised 3D fit remains unverified.

The saved study includes checked calculations and two inspected diagrams. **Absolute airspeed, sound level and the final winning shape remain unmeasured**: selecting them requires comparing the complete stages at equal useful output and at their qualified maximum power. The 150 mm five-blade axial stage is my recommended first design, with mixed-flow as the serious pressure-focused comparator.

<oai-mem-citation>
<citation_entries>
MEMORY.md:247-248|note=[preserved boost interaction and checked current source evidence]
rollout_summaries/2026-09-08T20-44-35-XAFw-windflow_screen_full_turn_boost_rev_b_integration.md:9-9|note=[recovered prior screen and full-turn boost requirements]
</citation_entries>
<rollout_ids>
01a082c3-f6b3-77a2-b642-16afc9a7a406
</rollout_ids>
</oai-mem-citation>
