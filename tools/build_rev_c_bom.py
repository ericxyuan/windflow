"""Consolidate selected bought parts and the captured Rev C circuit population."""
from pathlib import Path
from datetime import datetime,timezone
import csv,json,hashlib

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'hardware/rev_c'

def main():
    rows=[]
    def add(ref,qty,maker,part,function,status='Selected; physical qualification required',location='assembly'):
        rows.append({'Reference':ref,'Quantity':qty,'Manufacturer':maker,'Exact part/specification':part,
            'Function':function,'Location':location,'Status':status})
    for args in [
        ('MOTOR1',1,'T-Motor','Pacer V4 P2406 Juicy2060KV','Single axial-impeller drive'),
        ('ESC1',1,'TeamTriforceUK','A50SV2.3c-12-10, A50S V2.3c12S','Single FOC ESC; UART speed/current/temperature'),
        ('PD1',1,'Adafruit','5807 HUSB238','15V3A PD sink; exact15V contract required'),
        ('PSU1',1,'Raspberry Pi','45W USB-C Power Supply UK TypeG white','15V3A USB PD source, integral cable'),
        ('MCU1',1,'Raspberry Pi','Pico SC0915','RP2040 controller; use Rev C firmware only'),
        ('SERVO1',1,'FEETECH / Pololu','FS90-FB / Pololu3436','Feedback servo; supplied20T horn and retaining screw'),
        ('ENC1',1,'Bourns','PEC11H-4215F-S0024','24-detent horizontal push thumbwheel'),
        ('TFT1',1,'Adafruit','4311,2-inch ST7789 IPS240x320','Clear landscape display; top status band and wheel/countdown'),
        ('LED1',1,'Adafruit','1426,8-pixel NeoPixel stick','Recessed downward ambient lighting'),
        ('TEMP1,TEMP2',2,'Adafruit','1782 MCP9808','Power-board-adjacent and base-air temperature; addresses0x18/0x19'),
        ('DP1',1,'Sensirion','SDP810-125Pa,1-101597-01','Restriction sensing; direct-solder2mm-pitch daughterboard required'),
        ('REG1,REG2',2,'Pololu','2858 D24V22F5','Separate5V logic and servo rails'),
        ('SW-GRILLE',1,'Omron','D2F-01L','COM/NO magnetic-grille-present interlock'),
        ('MAG1..8',8,'K&J Magnetics','D42,N42 axial,6.35x3.175mm','Four captive opposing pairs; face gap1.925mm nominal'),
        ('HINGE1,2',2,'Metal stock supplier','Ground stainless steel rod3mm,cut172mm','Two panel hinge shafts, deburred'),
        ('COLLAR1..4',4,'Maedler','62300300,DIN705A,3mm bore','Four shaft collars with suppliedM2x3 set screws'),
        ('HINGE-SPACER1,2',2,'Metal stock supplier','Stainless tube7mmOD/3.3mmID,cut7.6mm','Right-side shaft spacers'),
        ('PIVOT-SLEEVE1..4',4,'Metal stock supplier','Stainless tube3mmOD/2.1mmID;cuts9.1,9.1,9.6,8.6mm','Smooth sleeve bearings for4M2 pivot stacks'),
        ('PIVOT-SCREW1..4',4,'Accu','SSC-M2-14-A2 + HNN-M2-A2 + HPW-M2-A2','Four metal-clamped linkage pivots'),
        ('CLAMP1,2',2,'ISO hardware supplier','ISO4762A2-70M2x16 / ISO10511M2 / ISO7089M2','Keyed crank clamp sets'),
        ('LOOM-PICO-SOCKET',2,'Wurth Elektronik','61202023021,20pin IDC with strain relief','Mating J15/J16 sockets; new keyed loom, not E3 cable'),
        ('LOOM-PICO-WIRE',2,'Cable supplier','28AWG20way ribbon,1.27mm pitch,maximum150mm','Pico-side transition/strain relief still requires physical layout'),
        ('MOTOR-CONNECTOR',1,'Amass','MR30 pair supplied with ESC','Three-phase loom; verify supplied connector sex'),
        ('ESC-POWER-CONNECTOR',1,'Amass','XT30 pair supplied with ESC','Power loom from J20; verify supplied connector sex'),
        ('ESC-IO-LOOM',1,'Molex / ESC supplier','5011892010 interface,ESC-supplied mating shell and precrimped wires','Use vendor-labelled3.3V UART/GND; insulate BEC'),
        ('TUBE-DP',1,'Saint-Gobain','TygonE-3603ACF00010,ID3.96875/OD7.14375mm','Cut matched hoses after Rev C route; minimum bend radius12.7mm'),
        ('WIRE-POWER',1,'Alpha Wire','3051,22AWG','Power branches; lengths from finished loom'),
        ('WIRE-SIGNAL',1,'Alpha Wire','5853,26AWG','Signal/feedback/I2C; twisted ground/UART where practical'),
        ('WINDOW',1,'Acrylic supplier','Clear45x34.4x1mm cut sheet','Screen protective window; no diffuser over TFT'),
        ('WINDOW-ADHESIVE',1,'3M','467MP,0.05mm','Window perimeter only'),
        ('MAGNET-ADHESIVE',1,'3M','Scotch-WeldDP100PlusClear','Allowed pocket glue, retained mechanically'),
        ('SERVICE-SHUNT',1,'Samtec','SNT-100-BK-G','Calibration entry shunt for service header'),
        ('ESC-STRAP',1,'Cable tie supplier','Nonconducting3mm-wide removable tie','ESC case restraint; qualify actual connector access'),
    ]:add(*args)
    circuit=ROOT/'hardware/pcb/rev_c/circuit-population.json'
    population=json.loads(circuit.read_text())['components']
    for c in population:
        add(c['ref'],0 if c['dnp'] else 1,'See exact MPN',c['mpn'],c['value']+('; '+c['note'] if c['note'] else ''),
            'DNP' if c['dnp'] else 'Captured/checked circuit; board unrouted',c['location'])
    # Include both ends of each removable cable. Board headers alone are not a
    # complete assembly BOM. XH crimp choice covers the selected22..26AWG wire.
    shells={};xh_contacts=0
    for c in population:
        if c['mpn'].startswith('JST B') and '-XH-' in c['mpn'] and not c['dnp']:
            count=len(c['pins']);shells[count]=shells.get(count,0)+1;xh_contacts+=count
    # The encoder daughterboard has its own second XH4 cable termination.
    shells[4]=shells.get(4,0)+1;xh_contacts+=4
    for count,qty in sorted(shells.items()):
        add('LOOM-XH-'+str(count),qty,'JST','XHP-'+str(count),'Mating shell for selected XH'+str(count)+' headers')
    add('LOOM-XH-CONTACT',xh_contacts,'JST','SXH-001T-P0.6N','XH crimp contacts for22..26AWG; no bare push-on wires')
    for suffix,contacts in (('0210',2),('0410',4),('0810',8)):
        add('LOOM-MICROFIT-'+suffix,1,'Molex','43025-'+suffix,'Mating dual-row housing for protected power/module connector')
        add('LOOM-MICROFIT-CRIMP-'+suffix,contacts,'Molex','43030-0007','Tin female contacts for selected22AWG power loom')
    add('ENC-NUT',1,'Bourns / ISO hardware','M7x0.75 panel nut and washer supplied/verified withPEC11H','Encoder mount, separate from wheel support')
    add('LOOM-SERVO',1,'FEETECH','FS90-FB supplied3-contact plug plus feedback lead','No guessed replacement servo pin order')
    add('LOOM-DISPLAY',1,'Adafruit','4311 supplied solder-pad interface; eight26AWG leads','J6-to-VIN/GND/MOSI/SCK/CS/DC/RST/LITE; verify current board labels')
    add('THREADLOCK',1,'Henkel','LOCTITE243','Metal-to-metal linkage fasteners only; keep off TPU/plastic and motor bearings')
    # This covers populated circuit elements, but custom PCB manufacture is
    # explicitly pending. Do not issue Gerbers from a mechanical blank.
    add('PCB-MAIN',1,'PCB fabricator','Rev C80x55mm,1.6mmFR4','Protected power/control carrier','UNROUTED; not orderable')
    add('PCB-ENCODER',1,'PCB fabricator','Windflow encoder P1 native KiCad design','Supported encoder daughterboard','Routed/checked prototype; assembly qualification pending')
    add('PCB-PRESSURE',1,'PCB fabricator','SDP810 direct-solder2mm-pitch daughterboard','Independent sensor housing support','UNFINISHED; not orderable')
    # Nominal assembly allowance derived from current CAD interfaces. The motor
    # and rotor clamp are deliberately not guessed from conflicting shaft data.
    for part,qty,use in [
        ('ISO4762A2-70M1.6x12 + DIN934M1.6',4,'Pico mounting'),
        ('ISO4762A2-70M1.6x8 + DIN934M1.6',2,'Ambient PCB'),
        ('ISO4762A2-70M2x14 + ISO4032M2',6,'Two regulators and PD sink'),
        ('ISO4762A2-70M2x12 + ISO4032M2',8,'Two MCP9808 and main PCB'),
        ('ISO4762A2-70M2x20 + ISO4032M2',2,'SDP810 housing allowance'),
        ('ISO4762A2-70M3x8',10,'Four screen cradle, four fairing, two encoder'),
        ('ISO4762A2-70M3x12',10,'Six head seams and four tray/feet'),
        ('ISO4762A2-70M3x10',4,'Head-to-base feet from interior'),
        ('ISO4762A2-70M2x6',16,'Four bezel, eight magnet keepers, two inner guard, two ESC cradle'),
        ('ISO4762A2-70M2x10 + ISO4032M2',14,'Four rear guard, eight interlock switch/clamp/raceway and two encoder PCB screws'),
        ('ISO4762A2-70M2x20 + ISO10511M2 + ISO7089M2',2,'Interlock bracket with new continuous backplate'),
        ('ruthexRX-M3x5.7',24,'Head seams, head/base, tray, screen, encoder and fairing'),
        ('ruthexRX-M2x4 / GE-M2x04-001',18,'Bezel, magnet/guard/ESC/diffuser mounts'),
    ]:add('FIX-'+str(len(rows)),qty,'ISO / ruthex',part,use,'Nominal CAD allowance; measure stacks and reconcile complete fastener models')
    add('MOTOR-M3',4,'ISO hardware supplier','M3 cap screw; LENGTH NOT FROZEN','Motor mounting on6mmcarrier','Supplier insertion limit/actual base depth required')
    add('ROTOR-CLAMP',1,'Motor/fastener supplier','M5 clamping stack; THREAD/HAND/HEIGHT NOT FROZEN','Retain printed hub','Actual8/10mmthread discrepancy must be resolved; no improvised clamp')
    path=OUT/'BOM.csv'
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    report={'timestamp_utc':datetime.now(timezone.utc).isoformat(),'bom_rows':len(rows),
        'circuit_components':len(population),'printed_parts_included':False,'order_release':False,
        'input_sha256':{'tools/build_rev_c_bom.py':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                        'hardware/pcb/rev_c/circuit-population.json':hashlib.sha256(circuit.read_bytes()).hexdigest()},
        'limits':['Fastener quantities are CAD-based allowances until every stack is modelled and measured.',
                  'Pressure board, main PCB routes and Pico ribbon transition remain design work.',
                  'Current supplier stock and motor clamp dimensions are not assumed.']}
    (OUT/'BOM-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('BUILT',len(rows),'selected bought-part/circuit rows; purchasing release withheld for unresolved designs')

if __name__=='__main__':main()
