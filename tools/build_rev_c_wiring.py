"""Generate cable and Pico pin tables from the checked Rev C population."""
from pathlib import Path
import hashlib,json

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'hardware/rev_c'
source=ROOT/'hardware/pcb/rev_c/circuit-population.json'
components=json.loads(source.read_text())['components']
connectors={c['ref']:c for c in components if c['ref'].startswith('J')}
pico={1:'GP0',2:'GP1',3:'GND',4:'GP2',5:'GP3',6:'GP4',7:'GP5',8:'GND',9:'GP6',10:'GP7',
      11:'GP8',12:'GP9',13:'GND',14:'GP10',15:'GP11',16:'GP12',17:'GP13',18:'GND',19:'GP14',20:'GP15',
      21:'GP16',22:'GP17',23:'GND',24:'GP18',25:'GP19',26:'GP20',27:'GP21',28:'GND',29:'GP22',30:'RUN',
      31:'GP26/ADC0',32:'GP27/ADC1',33:'AGND',34:'GP28/ADC2',35:'ADC_VREF',36:'3V3_OUT',37:'3V3_EN',
      38:'GND',39:'VSYS',40:'VBUS'}
description={0:'Encoder A',1:'Encoder B',2:'Encoder push',3:'Optional optical RPM; unpopulated/untrusted',
 4:'I2C SDA',5:'I2C SCL',6:'ESC power request to hardwired guard AND',7:'Screen reset',8:'Servo50Hz PWM',
 9:'Servo supply enable',10:'Screen DC',11:'Ambient addressable data',12:'UART0TX to ESC RX via BUF5',
 13:'UART0RX from ESC TX via BUF5',14:'Ambient supply enable',15:'Grille contact; LOW means present',
 16:'Screen backlight',17:'Service shunt',18:'Screen SPI SCK',19:'Screen SPI MOSI',20:'Screen CS',
 21:'Servo branch PGOOD',22:'ESC branch PGOOD',26:'Protected bus ADC; divider11.1',
 27:'Servo feedback ADC; divider2.1',28:'Logic5V ADC; divider2.1'}
lines=['# Rev C wiring and pin assignments — 8 October2026','',
 'The source of these tables is the checked [native circuit population](../pcb/rev_c/circuit-population.json). '
 'Use the [complete10-sheet schematic](../pcb/rev_c/windflow-rev-c-schematic.pdf) for component pins and protection. '
 'This describes the electrical connections; the main PCB and complete installed loom are still under development. '
 'Rev B25kHz fan control and its keyed Pico cable are incompatible with Rev C.','',
 '## Power path','',
 'USB-C15V3A contract → Adafruit5807 → J1/F1 → reverse-blocking CSD19537Q3/TPS26630 EF1 → protected15V bus. '
 'The ESC path adds F2 and default-off EF2, then J20 → suppliedXT30 → A50S. '
 'The three motor phases use the suppliedMR30 pair. Two D24V22F5 modules supply independent5V logic and servo rails. '
 'The servo and ambient rails have their own controlled switches. All returns join system ground. '
 'No load current runs through Pico GPIO or the Pico ribbon. The ESC BEC and3.3V outputs are insulated and unconnected.','',
 'Use22AWG for the protected power/5V branches and26AWG for signals. Keep phase leads apart from UART, I2C and ADC wiring. '
 'Use the included ESC loom for its20-cavity interface; only vendor-labelledGND,TX,RX are connected. '
 'Cavity numbers are not inferred from an unnumbered drawing. UART TX/RX cross, with a nearby ground return and a maximum150mm signal route. '
 'C38/C39/D3/R80 are at the ESC end behind the gate; C30/R56 are at the screen end.','',
 '## Removable cable connectors','',
 'Pin numbers below are the PCB footprint numbers. Determine the actual latch/pin1 view from the manufacturer drawing before crimping; '
 'do not copy a mirror image seen from the wire entry. All unused contacts remain unconnected.','',
 '| Board connector | Selected board part | Pin-to-net assignment |','|---|---|---|']
for ref,c in connectors.items():
 if ref in ('J15','J16'):continue
 mapping=', '.join(p['number']+' '+(p['net'] or 'NC') for p in c['pins'])
 lines.append(f"| {ref}{' (DNP)' if c['dnp'] else ''} | {c['mpn']} | {mapping} |")
lines+=['','J8 mates the encoder daughterboard J1, pin1GND/pin2A/pin3B/pin4PUSH. '
 'J9/J10 go to the MCP9808 breakouts at0x18 and0x19; J11 goes to the SDP810 daughterboard at0x25. '
 'J2 carries GND/SDA/SCL to the already powered HUSB238 board. '
 'J12 goes to Omron COM/NO; insulate NC. Its raw contact is5V, translated before GP15. '
 'The FEETECH supplied servo plug goes to J4; the separate feedback wire goes to J5. Confirm real lead colors/positions against the supplied servo.','',
 '## Pico physical pins and ribbon mapping','',
 'J15/J16 are keyed2×10 headers with all20 contacts. Connector pin n maps to Pico physical n for J15 and n+20 for J16. '
 'These mappings require a purpose-built Pico-side transition and strain relief; they are not a direct mechanical plug into the Pico1×20 rows. '
 'That transition is unfinished design work. Label the two looms separately and continuity-test all40 contacts before applying power.','',
 '| Pico physical pin | Pico function | Carrier connector | Net / use |','|---:|---|---|---|']
for num in range(1,41):
 ref='J15' if num<=20 else 'J16';n=num if num<=20 else num-20
 pin=next(p for p in connectors[ref]['pins'] if int(p['number'])==n)
 key=pico[num];use=description.get(int(key.split('/')[0][2:]),'') if key.startswith('GP') else ''
 lines.append(f"| {num} | {key} | {ref}.{n} | {pin['net'] or 'NC'}{(' — '+use) if use else ''} |")
lines+=['','RUN,ADC_VREF,3V3_EN andVBUS stay unconnected at this carrier. Pico VSYS is diode-fed from the logic regulator; '
 '3V3_OUT powers3.3V buffers/sensors. Powered USB programming must be checked for backfeed through the finished circuit.','',
 '## Commissioning sequence','',
 '1. Leave the motor/impeller disconnected. Check every cable contact against these tables, including no shorts to adjacent pins and all NC insulation.',
 '2. Verify unsupported5V USB leaves motor permission off. Confirm the selected source negotiates15V3A and the measured bus is within limits.',
 '3. Check protected bus, both5V rails, Pico3V3, ADC scale and I2C addresses before enabling loads.',
 '4. Remove/reseat the grille: verify the contact, GP15 and EF2SHDN independently. Reset/boot must leave the motor branch off.',
 '5. Check servo feedback/open position and its bounded jam cutoff with rotor absent. Check display, wheel/countdown, night mode and ambient dimming.',
 '6. Verify UART levels, both power sequences, stale telemetry and ESC timeout. Follow the guarded motor/impeller qualification procedure before any motion build.',
 '', 'Cable lengths, clips, bend envelopes, shield/return routing and populated-tray service slack need source-matched physical CAD integration. '
 'Nominal unplugged screen removal is not a connected-loom removal qualification.','']
path=OUT/'wiring.md';path.write_text('\n'.join(lines),encoding='utf-8')
report={'result':'PASS:40physical Pico mappings and connector tables generated from checked population',
 'physical_qualification':False,'main_pcb_routed':False,'installed_loom_qualified':False,
 'input_sha256':{str(p.relative_to(ROOT)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest() for p in (source,Path(__file__))},
 'output_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
(OUT/'wiring-validation.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS40Pico physical pins and',len(connectors)-2,'connector tables')
