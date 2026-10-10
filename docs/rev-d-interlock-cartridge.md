# Rev D front-service interlock cartridge — development

The 150 mm grille interlock now has a checked front-removal design. This replaces the earlier independent bracket/raceway arrangement for the next main-stage integration. The current online 65-instance assembly has not yet adopted this cartridge. The fixed inner finger guard stays installed when either the cleaning grille or the cartridge is removed.

The cartridge contains the Omron D2F-01L drawing-reference switch, an adjustable switch bracket, a short covered wire raceway and a separate TPU liner/clamp. Two front-facing M2 screws secure the cartridge to heat-set inserts in the left flowing shell. The internal screws are assembled and adjusted with the cartridge outside the enclosure. Their approach directions, recessed nuts and head clearances allow the complete module to withdraw past the fixed guard.

## Checked geometry

- The standalone candidate passes **4,008 nominal part comparisons**. Two insert/shell contacts are explicitly bounded thermal-insertion interfaces; each occupies about 1.142 mm³ within its declared seat. A 2.166 mm³ contact between an ideal screw cylinder and a vendor female-thread solid is also bounded within the threaded seat. They are not waived external collisions.
- **196,561 sampled comparisons** pass for boost, encoder rotation/press, display service, grille removal, 70 mm front cartridge withdrawal, switch adjustment and declared tool approaches. No unintended overlap exceeds 0.0001 mm³ in these motion checks.
- All six separately printed cartridge meshes and the insert-seat coupon are watertight, consistently wound and single components.
- The two selected Alpha Wire 5853 signal wires have a nominal 1.1 mm envelope. Across nine switch adjustment positions from −2 to +2 mm, the smallest sampled centerline bend radius is **12.280 mm**. The selected wire's largest documented OD requires 10.922 mm at its specified 10×OD bend radius. These routes end at the cartridge exit; they do not establish a connected route to J12.

These results belong to the exact hashes in [cartridge-validation.json](../cad/rev_d/interlock-cartridge/cartridge-validation.json) and [service-motion-validation.json](../cad/rev_d/interlock-cartridge/service-motion-validation.json). The reports also identify the main-stage baseline and tool sizes. They do not establish tolerance extremes, switch trip/overtravel, conductor termination, strain-relief grip or safe rotor operation.

## Purchased parts for this module

| Item | Quantity | Geometry and function |
|---|---:|---|
| Omron D2F-01L | 1 | Primary drawing case/lever/terminal references; gold-contact COM/NO guard circuit, not a manufacturer solid or elastic model |
| ruthex RX-M2x4 | 2 | Manufacturer CAD, 3.6 mm outer diameter and 4 mm length; front cartridge seats |
| ISO 4762 M2×6, A2-70 | 2 | Adjustable bracket screws |
| ISO 4762 M2×10, A2-70 | 2 | Switch case screws |
| ISO 4762 M2×14, A2-70 | 4 | Wire clamp and raceway screws, outboard insertion direction |
| ISO 4762 M2×8, A2-70 | 2 | Front cartridge screws |
| ISO 4032 M2, A2 | 8 | Recessed captive nuts for the internal screws |
| ISO 7089 M2, A2 | 10 | Modelled 5 mm OD, 2.2 mm ID and 0.3 mm thickness; confirm the actual supplied washers |
| Alpha Wire 5853 | 2 signal conductors | About 73.7 and 79.0 mm modelled terminal-to-exit lengths at the nominal adjustment, plus termination allowance and the still-undesigned main loom |

The final project BOM must include these quantities when the cartridge is adopted. The wire tails and J12 connector length must be reconciled with the installed main board. Insulate the unused NC terminal.

The [ruthex primary product and CAD](https://www.ruthex.de/en/products/ruthex-gewindeeinsatz-m2-70-stuck-rx-m2x4-messing-gewindebuchsen) and [RX-series drawing](https://www.igo3d.com/mediafiles/Sonstiges/Ruthex/ruthex_Datenblatt_RX-Serie.pdf) specify the insert. The design uses a 3.2 mm printing bore, 5 mm blind depth and at least 1.4 mm radial plastic. The [Alpha Wire 5853 specification](https://www.alphawire.com/en/products/wire/hook-up-wire/premium/5853) governs the wire diameter and bend-radius check. Captured source files and download entries are retained in the project manifest.

## Assembly and service

1. Print the small insert-seat coupon before the whole head. Check the selected material, bore and actual insertion tool against the manufacturer insert and screw. Avoid bottoming a screw in the insert.
2. Install the two inserts from the front before fitting the cartridge. The checked insertion envelope is 5 mm diameter; confirm the actual tool fits.
3. Outside the head, fit the switch and adjustable bracket, terminate/insulate its wires, install the TPU liner, clamp and covered raceway. Confirm free lever motion before tightening the adjustment screws.
4. Insert the cartridge from the front, secure its two M2×8 screws and connect J12 through the bottom service opening. Then install the magnetic seat/keeper and cleaning grille. Perform electrical continuity and physical trip/overtravel tests before any motion qualification.
5. For cartridge service, disconnect USB power, remove the cleaning grille and magnetic seat/keeper, unplug J12 through bottom access, remove the two front screws and withdraw the entire cartridge approximately 70 mm. The permanent inner guard stays installed. Do not pull a still-connected loom.

The raceway has approximately 0.2 mm nominal clearance to the guard edge, and its clamp about 0.3 mm. These tight local fits require a cartridge/guard coupon and process compensation before the design can be released for printing. The geometric path pass is not a claim that an arbitrary FDM printer will reproduce it. The TPU mesh represents its installed shape; its free printed interference and grip must be tuned separately.

## Remaining work

Adopt the cartridge into the main-stage sources, regenerate the whole-stage static/mesh/motion/exchange reports and publish a fresh Onshape assembly/checkpoint. Then finish the connected main loom and connector restraint. Verify actual switch trip, post-trip overtravel, release on grille removal, insert pullout, fastener retention, tolerance extremes and dexterity on hardware. The existing motion-inhibited firmware and unqualified printed-rotor status remain in force.
