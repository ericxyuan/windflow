"""Editable Rev C circuit capture for the P2406/A50S architecture.

Reuses the reviewed E3 symbol/export helpers while replacing the retired fan
and 12 V circuitry. This is a circuit/netlist milestone, not a routed PCB.
"""
from pathlib import Path
from datetime import datetime, timezone
import collections
import csv
import json
import uuid
import xml.etree.ElementTree as ET
import build_carrier_circuit as b

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'hardware/pcb/rev_c'


def configure():
    b.OUT = OUT
    b.LIB = OUT / 'WindflowCarrier.pretty'
    b.NAME = 'windflow-rev-c'
    b.NS = uuid.UUID('7536a1c0-1fb3-5315-b196-8e07db8b3476')
    b.ROOT_UUID = b.uid('root')
    b.SCHEMATIC_REVISION = 'Rev C / P2406 and A50S'
    b.CAPTURE_DATE = '2026-10-07'
    b.BOARD_SCOPE = '80x55mm board reserve. Circuit capture only; placement, routing and thermal qualification remain.'
    b.SHEET_COLUMNS = 3
    b.SHEET_WIDTH = 105
    b.SHEET_X_STEP = 127
    b.FLAG_NETS = ['RAW_FUSED', 'EF1_IN', 'ESC_FUSED', 'REG5_LOGIC', 'REG5_SERVO',
                   'SERVO_FUSED', '+3V3', 'GND']
    b.GROUP_TITLES = {
        'power': '15V input and reverse blocking', 'rails': 'Protected bus and 5V rails',
        'esc': 'Default-off ESC branch', 'uart': 'Guard interlock and UART isolation',
        'servo': 'Servo supply and feedback', 'ambient': 'Downward ambient strip',
        'inputs': 'Encoder, I2C and Pico', 'adc': 'ADC isolation and filters',
        'screen': 'IPS screen interfaces'}
    b.NOTES = {
        'power': ['TPS26630 RGE has system GND on pin8 AND pad25; no isolated EF_RTN island.',
                  'QRC1 source=RAW_FUSED; drain=EF1_IN. QDRV1 gate=DRV, drain=BGATE, source=RAW_FUSED.',
                  'EF1 SHDN is intentionally open: specified open-circuit voltage2.48..3.3V. MODE open=latchoff.'],
        'rails': ['15V3A PD contract required. No battery, no12V converter, no ESC BEC connection.',
                  'Remote D24V22F5 modules: input from protected bus, separate logic/servo5V outputs.',
                  'Regulator EN stays NC. PG_SERVO pullup is3.3V; modules must be qualified under load.'],
        'esc': ['EF2 SHDN has10k pulldown. Guard AND MCU request enables it; reset/removal cuts motor power.',
                'IN_SYS=IN=BUS_PROTECTED; B_GATE and DRV intentionally NC for this branch.',
                '470uF35V, ceramic, TVS and3.3k bleed fit at ESC. No braking or regenerative energy sink.'],
        'uart': ['BUF5 VCC=3.3V. Both /OE follow inverted ESC PGOOD;10k pullup defaults disabled.',
                 'UART RX/TX are directionally buffered; max3.3V. ESC5V BEC remains physically insulated NC.',
                 'QRC1 symbol pad5 represents common drain terminals5..8+exposed drain, per actual drawing.'],
        'servo': ['GPIO8 is50Hz servo PWM; GPIO9 is supply enable. BUF3 follows switched5V.',
                  'Timed movement and feedback checks bound jam energy; F3 does not replace jam cutoff.',
                  'Use real supplied20T servo horn; measured feedback table and end stops required.'],
        'ambient': ['Eight ambient pixels only. Screen replaces the front speed/power light bars.',
                    'BUF1 powered from switched ambient5V; its unused channels disabled and grounded.'],
        'inputs': ['Guard COM/NO pulls rawguard LOW when grille is present; BUF4 translates it to GP15.',
                   'J15/J16 are keyed2x10 IDC headers, all20 contacts retained. OLD E3 keyed cable is incompatible.',
                   'J15 pin n maps Pico physical n; J16 pin n maps physical n+20. Verify ribbon pin1 continuity.',
                   'R6/R7 DNP until aggregate breakout I2C pullups are measured. J21 optical RPM is DNP.'],
        'adc': ['Filters precede TMUX1511. ADC-side1M pulldowns remain after isolation.',
                'SUP1 enables ADC only after3.3V is healthy. Bus/logic scales11.1 and2.1 require calibration.'],
        'screen': ['BUF2 uses unswitched5V. CS/RST pullups never connect5V directly to Pico.',
                   'C30/R56 fit at screen end. Top64rows reserve status band; wheel phase/countdown remain visible.']}


def population():
    b.population()
    retired = {'EF1', 'C3', 'C6', 'C29', 'J17', 'F2', 'SW1', 'C11', 'C14',
               'R39', 'R10', 'Q1', 'R13', 'R14', 'J3', 'R4', 'R9',
               *('R'+str(i) for i in range(42,48))}
    b.COMPONENTS[:] = [c for c in b.COMPONENTS if c['ref'] not in retired]
    for c in b.COMPONENTS:
        if c['group'] == 'power': c['group'] = 'rails'
        if c['group'] == 'fan_servo': c['group'] = 'servo'
        if c['ref'] in {'J1', 'F1', 'D1', 'C1'}: c['group'] = 'power'
        if c['ref'] == 'F1': c.update(value='3A',mpn='Littelfuse 0451003.MRL')
        if c['ref'] == 'J15':
            replacements = {5:'OPTICAL_RPM',9:'ESC_POWER_REQUEST',12:'EN_SERVO',16:'UART_TX_GPIO',17:'UART_RX_GPIO'}
            for p in c['pins']:
                if int(p['number']) in replacements: p['net'] = replacements[int(p['number'])]
        if c['ref'] == 'J16':
            for p in c['pins']:
                if p['number'] == '9': p['net'] = 'PG_ESC'
        if c['ref'] in {'J15','J16'}:
            c.update(value='Keyed IDC20',mpn='Wurth Elektronik 61202021621',
                footprint_source='Connector_IDC:IDC-Header_2x10_P2.54mm_Vertical',
                datasheet='https://www.we-online.com/katalog/datasheet/61202021621.pdf',
                note='All20 contacts retained. New keyed2x10 loom with61202023021 sockets; no E3 contact-removal key.')

    def r(ref,value,a,d,g,part=None,location='carrier'):
        b.resistor(ref,value,a,d,g,part,location=location)
    def c(ref,value,a,d,g,location='carrier'):
        b.capacitor(ref,value,a,d,g,location=location)

    def ef(ref,vin,vout,g,blocked=False):
        nets = {1:'EF1_IN' if blocked else vin,2:'EF1_IN' if blocked else vin,
                3:'EF_BGATE' if blocked else None,4:'EF_DRV' if blocked else None,
                5:vin,6:ref+'_UVLO',7:ref+'_OVP',8:'GND',9:ref+'_DVDT',
                10:ref+'_ILIM',11:None,12:None if blocked else 'ESC_ENABLE_HW',
                13:None,14:None,15:ref+'_PGTH',16:'PG_INPUT' if blocked else 'PG_ESC',
                17:vout,18:vout,25:'GND'}
        names = {1:'IN',2:'IN',3:'B_GATE',4:'DRV',5:'IN_SYS',6:'UVLO',7:'OVP',
                 8:'GND',9:'DVDT',10:'ILIM',11:'MODE',12:'SHDN',13:'IMON',14:'FLT',
                 15:'PGTH',16:'PGOOD',17:'OUT',18:'OUT',25:'EP_GND'}
        pins = []
        for n in range(1,26):
            net = nets.get(n)
            kind = 'passive'
            if n in (1,5,8,25): kind = 'power_in'
            if n == 17: kind = 'power_out'
            if n in (6,7,12,15): kind = 'input'
            if n in (14,16): kind = 'open_collector'
            if n >= 19 and n <= 24: kind = 'no_connect'
            pins.append(b.pin(n,names.get(n,'NC'),net,kind))
        b.add(ref,'TPS26630RGER','Texas Instruments TPS26630RGER',g,pins,
              'Package_DFN_QFN:Texas_RGE0024H_VQFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm_ThermalVias',
              'https://www.ti.com/lit/ds/symlink/tps2663.pdf')

    ef('EF1','RAW_FUSED','BUS_PROTECTED','power',True)
    ef('EF2','BUS_PROTECTED','ESC_15V','esc')
    for ref,g,vin,vout,rref,ilim in [('EF1','power','RAW_FUSED','BUS_PROTECTED',61,'7.15k'),
                                    ('EF2','esc','BUS_PROTECTED','ESC_15V',66,'10k')]:
        r('R'+str(rref),ilim,ref+'_ILIM','GND',g,'RC0603FR-077K15L' if ilim=='7.15k' else None)
        for offset,value,a,d,mpn in [(1,'100k',vin,ref+'_UVLO',None),(2,'10k',ref+'_UVLO','GND',None),
                                    (3,'132k',vin,ref+'_OVP','RC0603FR-07132KL'),(4,'10k',ref+'_OVP','GND',None)]:
            r('R'+str(rref+offset),value,a,d,g,mpn)
        r('R'+str(rref+10),'100k',vout,ref+'_PGTH',g)
        r('R'+str(rref+11),'10k',ref+'_PGTH','GND',g)
        c('C34' if ref=='EF1' else 'C35','100nF',ref+'_DVDT','GND',g)
        c('C36' if ref=='EF1' else 'C37','1uF',vin,'GND',g)
    b.add('QRC1','CSD19537Q3','Texas Instruments CSD19537Q3','power',
          [b.pin(1,'S1','RAW_FUSED'),b.pin(2,'S2','RAW_FUSED'),b.pin(3,'S3','RAW_FUSED'),
           b.pin(4,'G','EF_BGATE'),b.pin(5,'D5..8+EP','EF1_IN')],
          'Package_SON:VSON-8_3.3x3.3mm_P0.65mm_NexFET',
          'https://www.ti.com/lit/ds/symlink/csd19537q3.pdf',
          note='Actual drawing: source1..3, gate4, drain5..8+EP. Shared drain land represented by common pad5.')
    b.add('QDRV1','BSS138-7-F','Diodes Incorporated BSS138-7-F','power',
          [b.pin(1,'G','EF_DRV'),b.pin(2,'S','RAW_FUSED'),b.pin(3,'D','EF_BGATE')],
          'Package_TO_SOT_SMD:SOT-23','https://www.diodes.com/assets/Datasheets/BSS138.pdf')
    # Branch fuse is upstream of the controlled-inrush eFuse and its local bulk.
    b.add('F2','2A','Littelfuse 0451002.MRL','rails',
          [b.pin(1,'1','BUS_PROTECTED'),b.pin(2,'2','ESC_FUSED')],'Fuse:Fuse_2410_6125Metric')
    ef2 = next(c for c in b.COMPONENTS if c['ref']=='EF2')
    for p in ef2['pins']:
        if p['net']=='BUS_PROTECTED': p['net']='ESC_FUSED'
    for x in b.COMPONENTS:
        if x['group']=='esc':
            for p in x['pins']:
                if p['net']=='BUS_PROTECTED': p['net']='ESC_FUSED'
    b.add('J20','ESC power','Molex 43045-0212','esc',
          [b.pin(1,'GND','GND'),b.pin(2,'15V','ESC_15V')],
          'Connector_Molex:Molex_Micro-Fit_3.0_43045-0212_2x01_P3.00mm_Vertical',
          note='Adapter loom to suppliedXT30; no3A motor power through Pico/ribbon.')
    b.xh('J22',3,['GND','UART_TO_ESC_RX','UART_FROM_ESC_TX'],'uart',
         'Adapter to vendor-labelled GND/RX/TX wires. Verify A50S20-cavity loom; BEC insulated NC.')
    b.add('C38','470uF/35V','Panasonic EEU-FR1V471','esc',
          [b.pin(1,'+','ESC_15V'),b.pin(2,'-','GND')],
          'Capacitor_THT:CP_Radial_D8.0mm_P3.50mm',location='esc_harness')
    c('C39','1uF','ESC_15V','GND','esc',location='esc_harness')
    b.add('D3','SMBJ18A','Littelfuse SMBJ18A','esc',
          [b.pin(1,'K','ESC_15V'),b.pin(2,'A','GND')],'Diode_SMD:D_SMB',location='esc_harness')
    r('R80','3.3k','ESC_15V','GND','esc','RC1206FR-073K3L',location='esc_harness')
    r('R81','10k','ESC_ENABLE_HW','GND','uart')
    r('R82','10k','+3V3','PG_ESC','uart')
    r('R83','10k','+3V3','PG_INPUT','power')

    def gate(ref,part,pins):
        b.add(ref,part,'Texas Instruments '+part,'uart',pins,
              'Package_TO_SOT_SMD:SOT-23-5','https://www.ti.com/lit/ds/symlink/'+part.split('DB')[0].lower()+'.pdf')
    for ref,source,dest in [('U1','GUARD_LOGIC_3V3','GUARD_PRESENT'),('U2','PG_ESC','UART_DISABLE')]:
        gate(ref,'SN74LVC1G04DBVR',[b.pin(1,'NC',None,'no_connect'),b.pin(2,'A',source,'input'),
             b.pin(3,'GND','GND','power_in'),b.pin(4,'Y',dest,'output'),b.pin(5,'VCC','+3V3','power_in')])
    gate('U3','SN74LVC1G08DBVR',[b.pin(1,'A','GUARD_PRESENT','input'),b.pin(2,'B','ESC_POWER_REQUEST','input'),
         b.pin(3,'GND','GND','power_in'),b.pin(4,'Y','ESC_ENABLE_HW','output'),b.pin(5,'VCC','+3V3','power_in')])
    b.add('BUF5','74LVC2G125DP-Q100H','Nexperia 74LVC2G125DP-Q100H','uart',
          [b.pin(1,'1OE','UART_DISABLE','input'),b.pin(2,'1A','UART_TX_GPIO','input'),
           b.pin(3,'2Y','UART_RX_BUF','output'),b.pin(4,'GND','GND','power_in'),
           b.pin(5,'2A','UART_FROM_ESC_TX','input'),b.pin(6,'1Y','UART_TX_BUF','output'),
           b.pin(7,'2OE','UART_DISABLE','input'),b.pin(8,'VCC','+3V3','power_in')],
          'Package_SO:TSSOP-8_3x3mm_P0.65mm','https://assets.nexperia.com/documents/data-sheet/74LVC2G125_Q100.pdf')
    r('R84','10k','UART_DISABLE','+3V3','uart')
    r('R85','10k','ESC_POWER_REQUEST','GND','uart')
    r('R86','33','UART_TX_BUF','UART_TO_ESC_RX','uart')
    r('R87','33','UART_RX_BUF','UART_RX_GPIO','uart')
    for i,ref in enumerate(('U1','U2','U3','BUF5'),40): c('C'+str(i),'100nF','+3V3','GND','uart')
    b.xh('J21',3,['GND','+3V3','OPTICAL_RPM'],'inputs','DNP optical RPM service header; no unqualified sensor trusted')
    next(c for c in b.COMPONENTS if c['ref']=='J21')['dnp']=True
    assert not any(p['net'] and ('FAN' in p['net'] or p['net'] in ('REG12V','EF_RTN')) for c in b.COMPONENTS for p in c['pins'])


def validate():
    tree=ET.parse(OUT/(b.NAME+'.net.xml')).getroot()
    actual={};nodes={}
    for net in tree.findall('nets/net'):
        nn=net.attrib['name'];nodes[nn]=[]
        for n in net.findall('node'):
            k=(n.attrib['ref'],n.attrib['pin']);assert k not in actual
            actual[k]=nn;nodes[nn].append(k)
    count=0
    for c in b.COMPONENTS:
        for p in c['pins']:
            k=(c['ref'],p['number']);assert k in actual,k
            if p['net'] is None:
                assert actual[k].startswith('unconnected-') and nodes[actual[k]]==[k],k
            else: assert actual[k]==p['net'],(k,actual[k],p['net'])
            count+=1
    # Independent datasheet and hardware/firmware invariants, beyond export parity.
    expected={('EF1','8'):'GND',('EF1','25'):'GND',('EF2','8'):'GND',('EF2','25'):'GND',
        ('EF1','5'):'RAW_FUSED',('EF1','1'):'EF1_IN',('EF1','2'):'EF1_IN',
        ('QRC1','1'):'RAW_FUSED',('QRC1','4'):'EF_BGATE',('QRC1','5'):'EF1_IN',
        ('QDRV1','1'):'EF_DRV',('QDRV1','2'):'RAW_FUSED',('QDRV1','3'):'EF_BGATE',
        ('EF2','1'):'ESC_FUSED',('EF2','2'):'ESC_FUSED',('EF2','5'):'ESC_FUSED',
        ('EF2','12'):'ESC_ENABLE_HW',('U3','1'):'GUARD_PRESENT',('U3','2'):'ESC_POWER_REQUEST',
        ('U1','2'):'GUARD_LOGIC_3V3',('U2','2'):'PG_ESC',('BUF5','1'):'UART_DISABLE',
        ('BUF5','7'):'UART_DISABLE',('BUF5','8'):'+3V3',('BUF5','2'):'UART_TX_GPIO',
        ('BUF5','5'):'UART_FROM_ESC_TX',('J15','12'):'EN_SERVO',('J15','16'):'UART_TX_GPIO',
        ('J15','17'):'UART_RX_GPIO',('J15','9'):'ESC_POWER_REQUEST',('J16','9'):'PG_ESC',
        ('SW2','6'):'SERVO5_SWITCHED',('BUF3','5'):'SERVO5_SWITCHED',('BUF1','14'):'AMBIENT5_SWITCHED',
        ('BUF2','14'):'REG5_LOGIC',('ISO1','3'):'ADC_BUS',('D2','1'):'PICO_VSYS'}
    for k,n in expected.items(): assert actual[k]==n,(k,n,actual[k])
    for k in [('EF1','11'),('EF1','12'),('EF2','11'),('EF2','3'),('EF2','4')]:
        assert actual[k].startswith('unconnected-'),k
    assert not any(n in nodes for n in ('EF_RTN','REG12V','FAN_FUSED','FAN_TACH','FAN_PWM_GPIO'))
    b.write(OUT/'netlist-validation.json',json.dumps({'result':'PASS','physical_qualification':False,
        'native_netlist_sha256':b.digest(OUT/(b.NAME+'.net.xml')),'component_count':len(b.COMPONENTS),
        'pin_net_assertions':count,'independent_invariant_count':len(expected)+6,
        'nets':{n:sorted(v) for n,v in sorted(nodes.items())}},indent=2)+'\n')
    print('PASS Rev C native netlist:',len(b.COMPONENTS),'components;',count,'pins',flush=True)


def main():
    configure();OUT.mkdir(parents=True,exist_ok=True)
    population();b.footprint_libraries();b.schematics()
    b.write(OUT/(b.NAME+'.kicad_pro'),json.dumps({'meta':{'filename':b.NAME+'.kicad_pro','version':1}},indent=2)+'\n')
    b.write(OUT/'circuit-population.json',json.dumps({'scope':'Rev C native circuit capture; PCB unrouted',
        'components':b.COMPONENTS,'footprint_sources':b.FP_SOURCES},indent=2)+'\n')
    with (OUT/'circuit-BOM.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.writer(f);w.writerow(['Ref','Qty','Value','Exact MPN','Location','DNP','Footprint','Notes'])
        for c in b.COMPONENTS:w.writerow([c['ref'],1,c['value'],c['mpn'],c['location'],c['dnp'],c['footprint'],c['note']])
    sch=OUT/(b.NAME+'.kicad_sch')
    b.call('sch','export','netlist','--format','kicadxml','-o',OUT/(b.NAME+'.net.xml'),sch)
    validate()
    b.call('sch','erc','--format','json','--severity-all','--exit-code-violations','-o',OUT/'erc.json',sch)
    b.call('sch','export','svg','--exclude-drawing-sheet','-o',OUT/'schematic-svg',sch)
    b.call('sch','export','pdf','--exclude-drawing-sheet','-o',OUT/(b.NAME+'-schematic.pdf'),sch)
    b.write(OUT/'provenance.json',json.dumps({'result':'PASS: circuit capture and ERC',
        'timestamp_utc':datetime.now(timezone.utc).isoformat(),'physical_qualification':False,
        'generator_sha256':b.digest(__file__),'helper_sha256':b.digest(ROOT/'tools/build_carrier_circuit.py'),
        'kicad_version':'10.0.6','board_reserve_mm':[80,55],'PCB_routed':False,
        'files':{str(p.relative_to(OUT)).replace('\\','/'):b.digest(p) for p in sorted(OUT.rglob('*'))
                 if p.is_file() and p.name!='provenance.json' and p.suffix!='.kicad_prl'}},indent=2)+'\n')
    print('PASS Rev C editable schematic/netlist/ERC; board remains unrouted',flush=True)


if __name__=='__main__':main()
