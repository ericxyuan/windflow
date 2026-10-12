"""Build the direct-solder SDP810 P1 daughterboard; do not adopt it as fan CAD."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import uuid
import math
import subprocess
import shutil
import xml.etree.ElementTree as ET
import pcbnew as p
from build_encoder_board import property_text

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'hardware/pcb/pressure'
LIB=OUT/'WindflowPressure.pretty'
RUNTIME=ROOT/'.tools/kicad-10.0.6'
CLI=RUNTIME/'bin/kicad-cli.exe'
NAME='windflow-pressure'
NS=uuid.UUID('7cf354ac-b457-4f23-adf1-bad464088743')
ROOT_ID=str(uuid.uuid5(NS,'root'))
URL='https://sensirion.com/media/documents/90500156/6167E43B/Sensirion_Differential_Pressure_Datasheet_SDP8xx_Digital.pdf'
DP={'1':'I2C_SCL','2':'+3V3','3':'GND','4':'I2C_SDA'}
PIGTAIL={'1':'GND','2':'+3V3','3':'I2C_SDA','4':'I2C_SCL'}
COMMANDS=[]


def uid(name):return str(uuid.uuid5(NS,name))
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,content):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(content,encoding='utf-8',newline='\n')
def vec(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))


def checked(*args):
    run=subprocess.run([str(CLI),*map(str,args)],cwd=OUT,capture_output=True,text=True)
    COMMANDS.append({'arguments':list(map(str,args)),'exit_code':run.returncode,'stdout':run.stdout.strip(),'stderr':run.stderr.strip()})
    write(OUT/'verification-commands.json',json.dumps(COMMANDS,indent=2)+'\n')
    assert run.returncode==0,(args,run.returncode,run.stdout,run.stderr)


def schematic():
    definitions={};instances=[]
    specifications=[('DP1','SDP810_125Pa','SDP810-125Pa / 1-101597-01','SDP810_DirectPins',DP,URL,(55.88,50.8)),
                    ('J1','Pigtail4','26AWG direct-solder pigtail','Pigtail4',PIGTAIL,'',(116.84,50.8)),
                    ('C33','C0603','100nF / GRM188R71H104KA93D','C_0603_1608Metric',{'1':'+3V3','2':'GND'},'',(55.88,88.9)),
                    ('H1','M2Mount','M2 NPTH 2.4mm','M2Mount',{},'',(116.84,88.9)),
                    ('H2','M2Mount','M2 NPTH 2.4mm','M2Mount',{},'',(147.32,88.9))]
    for ref,sym,value,footprint,mapping,datasheet,(x,y) in specifications:
        pins=[(pin,net,7.62-i*2.54) for i,(pin,net) in enumerate(mapping.items())]
        props=property_text('Reference',ref,0,11.43)+property_text('Value',value,0,-11.43)
        props+=property_text('Footprint','WindflowPressure:'+footprint,hide=True)+property_text('Datasheet',datasheet,hide=True)
        body='(rectangle (start -7.62 10.16) (end 7.62 -10.16) (stroke (width .254) (type default)) (fill (type background)))'
        # J1 supply pins explicitly represent the external 3.3V/GND source.
        pintext=''
        for pin,net,yy in pins:
            kind=('power_out' if ref=='J1' else 'power_in') if net in ['+3V3','GND'] and ref in ['DP1','J1'] else 'input' if ref=='DP1' and pin=='1' else 'bidirectional' if ref=='DP1' else 'passive'
            pintext+=f'(pin {kind} line (at -10.16 {yy} 0) (length 2.54) (name "{net}" (effects (font (size 1 1)))) (number "{pin}" (effects (font (size 1 1)))))'
        definition=f'(symbol "{sym}" (pin_names (offset .5)) (exclude_from_sim no) (in_bom yes) (on_board yes) {props} (symbol "{sym}_0_1" {body}) (symbol "{sym}_1_1" {pintext}))'
        definitions[sym]=definition
        props=property_text('Reference',ref,x,y-12.7)+property_text('Value',value,x,y+12.7)
        props+=property_text('Footprint','WindflowPressure:'+footprint,x,y,hide=True)+property_text('Datasheet',datasheet,x,y,hide=True)
        instances.append(f'(symbol (lib_id "WindflowPressure:{sym}") (at {x} {y} 0) (unit 1) (in_bom {"no" if ref.startswith("H") else "yes"}) (on_board yes) (dnp no) (uuid "{uid(ref)}") {props} '+
                         ' '.join(f'(pin "{pin}" (uuid "{uid(ref+pin)}"))' for pin,_,_ in pins)+
                         f' (instances (project "{NAME}" (path "/{ROOT_ID}" (reference "{ref}") (unit 1)))))')
        for pin,net,py in pins:
            yy=round(y-py,5);left=round(x-15.24,5);right=round(x-10.16,5)
            instances.append(f'(wire (pts (xy {left} {yy}) (xy {right} {yy})) (stroke (width 0) (type default)) (uuid "{uid(ref+pin+"wire")}"))')
            instances.append(f'(label "{net}" (at {left} {yy} 0) (effects (font (size 1 1)) (justify left bottom)) (uuid "{uid(ref+pin+"label")}"))')
    notes=['SDP810-125Pa P1: sensor-side footprint SCL / VDD / GND / SDA, 2mm pitch.',
           'J1 is solder pads: 1 GND, 2 +3V3, 3 SDA, 4 SCL; cable mates main J11.',
           'C33 100nF sits on the opposite face from the sensor. No duplicated I2C pullups.',
           '18x12x1.6mm prototype; installed sensor/retainer/loom clearances still require CAD adoption.']
    for i,text in enumerate(notes):instances.append(f'(text "{text}" (at 35.56 {125+i*5.08} 0) (effects (font (size 1.1 1.1)) (justify left)) (uuid "{uid("note"+str(i))}"))')
    write(OUT/'WindflowPressure.kicad_sym','(kicad_symbol_lib (version 20250114) (generator "kicad_symbol_editor")\n'+'\n'.join(definitions.values())+'\n)\n')
    embedded=' '.join(data.replace('(symbol "'+sym+'"','(symbol "WindflowPressure:'+sym+'"',1) for sym,data in definitions.items())
    write(OUT/(NAME+'.kicad_sch'),f'(kicad_sch (version 20250114) (generator "eeschema") (uuid "{ROOT_ID}") (paper "A4") (title_block (title "Windflow SDP810 pressure daughterboard") (rev "P1 development")) (lib_symbols {embedded}) '+' '.join(instances)+' (sheet_instances (path "/" (page "1"))))\n')
    write(OUT/'sym-lib-table','(sym_lib_table (version 7) (lib (name "WindflowPressure") (type "KiCad") (uri "${KIPRJMOD}/WindflowPressure.kicad_sym") (options "") (descr "SDP810 explicit pin mapping")))\n')


def footprints():
    LIB.mkdir(exist_ok=True)
    def generated(name,body):
        write(LIB/(name+'.kicad_mod'),f'(footprint "{name}" (version 20250108) (generator "pcbnew") (layer "F.Cu") (attr through_hole) '+
              '(property "Reference" "REF**" (at 0 0 0) (layer "F.Fab") (hide yes) (effects (font (size .8 .8)))) '+
              f'(property "Value" "{name}" (at 0 0 0) (layer "F.Fab") (hide yes) (effects (font (size .8 .8)))) '+body+')\n')
    pins=''.join(f'(pad "{i}" thru_hole {"rect" if i==1 else "circle"} (at {-5+2*i} 3) (size 1.4 1.4) (drill .8) (layers "*.Cu" "*.Mask"))' for i in range(1,5))
    generated('SDP810_DirectPins','(descr "Sensirion SDP8xx digital v1.1 Figure3, sensor side: SCL VDD GND SDA; body overhang needs 3D verification") '+pins+
              '(fp_rect (start -14.5 -9) (end 14.5 9) (stroke (width .1) (type default)) (fill none) (layer "F.Fab")) '+
              '(fp_rect (start -3.95 2.05) (end 3.95 3.95) (stroke (width .05) (type default)) (fill none) (layer "F.CrtYd"))')
    generated('Pigtail4',''.join(f'(pad "{i}" thru_hole {"rect" if i==1 else "circle"} (at {-10+4*i} 0) (size 1.6 1.6) (drill .8) (layers "*.Cu" "*.Mask"))' for i in range(1,5))+
              '(fp_rect (start -7.05 -1.05) (end 7.05 1.05) (stroke (width .05) (type default)) (fill none) (layer "F.CrtYd"))')
    generated('M2Mount','(pad "" np_thru_hole circle (at 0 0) (size 2.4 2.4) (drill 2.4) (layers "*.Cu" "*.Mask"))')
    shutil.copyfile(RUNTIME/'share/kicad/footprints/Capacitor_SMD.pretty/C_0603_1608Metric.kicad_mod',LIB/'C_0603_1608Metric.kicad_mod')
    write(OUT/'fp-lib-table','(fp_lib_table (version 7) (lib (name "WindflowPressure") (type "KiCad") (uri "${KIPRJMOD}/WindflowPressure.pretty") (options "") (descr "SDP810 manufacturer pattern and direct solder pads")))\n')


def board():
    b=p.BOARD();b.SetCopperLayerCount(2)
    s=b.GetDesignSettings();s.SetBoardThickness(p.FromMM(1.6));s.m_MinClearance=p.FromMM(.25);s.m_TrackMinWidth=p.FromMM(.25)
    s.m_ViasMinSize=p.FromMM(.6);s.m_MinThroughDrill=p.FromMM(.3)
    nets={}
    for name in dict.fromkeys(DP.values()):net=p.NETINFO_ITEM(b,'/'+name);b.Add(net);nets[name]=net
    fps={}
    for ref,fp,value,xy,mapping,back,angle in [('DP1','SDP810_DirectPins','SDP810-125Pa / 1-101597-01',(9,6),DP,False,0),
          ('J1','Pigtail4','26AWG direct-solder pigtail',(9,5.5),PIGTAIL,False,0),
          ('C33','C_0603_1608Metric','100nF / GRM188R71H104KA93D',(9,7),{'1':'+3V3','2':'GND'},True,0),
          ('H1','M2Mount','M2 NPTH 2.4mm',(2,2),{},False,0),('H2','M2Mount','M2 NPTH 2.4mm',(16,2),{},False,0)]:
        f=p.FootprintLoad(str(LIB),fp);assert f;b.Add(f);f.SetReference(ref);f.SetValue(value);f.SetFPIDAsString('WindflowPressure:'+fp)
        f.SetPosition(vec(*xy))
        if back:f.Flip(f.GetPosition(),False)
        f.SetOrientationDegrees(angle);f.SetPath(p.KIID_PATH('/'+ROOT_ID+'/'+uid(ref)))
        if ref=='DP1':f.GetField(p.FIELD_T_DATASHEET).SetText(URL)
        if ref.startswith('H'):f.SetAttributes(f.GetAttributes()|p.FP_EXCLUDE_FROM_BOM|p.FP_EXCLUDE_FROM_POS_FILES)
        f.Reference().SetVisible(False);f.Value().SetVisible(False)
        for pad in f.Pads():
            if pad.GetNumber() in mapping:pad.SetNet(nets[mapping[pad.GetNumber()]])
        fps[ref]=f
    c33={q.GetNumber():[p.ToMM(q.GetPosition().x),p.ToMM(q.GetPosition().y)] for q in fps['C33'].Pads()}
    assert c33=={'1':[8.225,7.0],'2':[9.775,7.0]},c33
    def route(net,points,layer):
        for a,c in zip(points,points[1:]):
            t=p.PCB_TRACK(b);t.SetStart(vec(*a));t.SetEnd(vec(*c));t.SetWidth(p.FromMM(.35));t.SetLayer(layer);t.SetNet(nets[net]);b.Add(t)
    route('+3V3',[(8,9),(8.225,7),(7,5.5)],p.B_Cu)
    route('GND',[(9.775,7),(10,9)],p.B_Cu)
    route('I2C_SCL',[(6,9),(6,10.8),(14,10.8),(14,6.5),(15,5.5)],p.F_Cu)
    route('I2C_SDA',[(12,9),(12,6.5),(11,5.5)],p.B_Cu)
    for x,y in [(2,2),(16,2)]:
        z=p.ZONE(b);z.SetIsRuleArea(True);z.SetLayerSet(p.LSET.AllCuMask(2));z.SetZoneName('M2 washer exclusion')
        z.SetDoNotAllowTracks(True);z.SetDoNotAllowVias(True);z.SetDoNotAllowZoneFills(True);z.SetDoNotAllowPads(False)
        z.SetDoNotAllowFootprints(False);poly=z.Outline();poly.NewOutline()
        for i in range(48):poly.Append(vec(x+2.6*math.cos(i*math.pi/24),y+2.6*math.sin(i*math.pi/24)))
        b.Add(z)
    z=p.ZONE(b);z.SetLayer(p.B_Cu);z.SetNet(nets['GND']);z.SetLocalClearance(p.FromMM(.25));z.SetMinThickness(p.FromMM(.25))
    z.SetPadConnection(p.ZONE_CONNECTION_FULL);poly=z.Outline();poly.NewOutline()
    for xy in [(.4,.4),(17.6,.4),(17.6,11.6),(.4,11.6)]:poly.Append(vec(*xy))
    b.Add(z)
    for a,c in [((0,0),(18,0)),((18,0),(18,12)),((18,12),(0,12)),((0,12),(0,0))]:
        line=p.PCB_SHAPE(b);line.SetShape(p.SHAPE_T_SEGMENT);line.SetLayer(p.Edge_Cuts);line.SetWidth(p.FromMM(.05));line.SetStart(vec(*a));line.SetEnd(vec(*c));b.Add(line)
    b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones());p.SaveBoard(str(OUT/(NAME+'.kicad_pcb')),b)
    return {'outline_mm':[18,12],'total_thickness_mm':1.6,'sensor_face':'F.Cu','capacitor_face':'B.Cu','mount_holes_xy_mm':[[2,2],[16,2]],
            'sensor_pin_xy_mm':{q.GetNumber():[p.ToMM(q.GetPosition().x),p.ToMM(q.GetPosition().y)] for q in fps['DP1'].Pads()},
            'pad_drills_mm':{'DP1':.8,'J1':.8,'H1':2.4,'H2':2.4},'c33_pad_xy_mm':c33,
            'pigtail_pad_xy_mm':{q.GetNumber():[p.ToMM(q.GetPosition().x),p.ToMM(q.GetPosition().y)] for q in fps['J1'].Pads()}}


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    source=ROOT/'hardware/datasheets/SDP800.pdf'
    assert digest(source)=='dbcbad9c96a414903676b160715a082126f0a5f6fe37441114965aebebbf9835'
    captured=json.loads((ROOT/'hardware/pcb/rev_c/circuit-population.json').read_text())['components']
    # The purchased sensor is external to the captured carrier circuit. Its
    # pin order comes from the manufacturer; the carrier defines the loom.
    cable=next(c for c in captured if c['ref']=='J11');capacitor=next(c for c in captured if c['ref']=='C33')
    assert {q['number']:q['net'] for q in cable['pins']}==PIGTAIL
    assert capacitor['mpn']=='Murata GRM188R71H104KA93D'
    assert capacitor['location']=='pressure_daughterboard'
    assert {q['number']:q['net'] for q in capacitor['pins']}=={'1':'+3V3','2':'GND'}
    footprints();schematic()
    write(OUT/(NAME+'.kicad_pro'),json.dumps({'meta':{'filename':NAME+'.kicad_pro','version':1},'net_settings':{'classes':[{'name':'Default','clearance':.25,'track_width':.35,'via_diameter':.6,'via_drill':.3}],'meta':{'version':4}}},indent=2)+'\n')
    write(OUT/(NAME+'.kicad_dru'),'(version 1)\n(rule "Prototype clearance" (constraint clearance (min 0.25mm)))\n(rule "Trace minimum" (constraint track_width (min 0.25mm)))\n(rule "Board edge" (constraint edge_clearance (min 0.25mm)))\n')
    interface=board();write(OUT/'mechanical-interface.json',json.dumps(interface,indent=2)+'\n')
    sch=OUT/(NAME+'.kicad_sch');pcb=OUT/(NAME+'.kicad_pcb')
    checked('sch','export','netlist','--format','kicadxml','-o',OUT/(NAME+'.net.xml'),sch)
    tree=ET.parse(OUT/(NAME+'.net.xml')).getroot()
    actual={n.get('name'):{(v.get('ref'),v.get('pin')) for v in n.findall('node')} for n in tree.findall('nets/net')}
    expected={'/'+net:set() for net in DP.values()}
    for ref,mapping in [('DP1',DP),('J1',PIGTAIL),('C33',{'1':'+3V3','2':'GND'})]:
        for pin,net in mapping.items():expected['/'+net].add((ref,pin))
    assert actual==expected,(actual,expected)
    checked('sch','erc','--format','json','--severity-all','--exit-code-violations','-o',OUT/'erc.json',sch)
    checked('pcb','drc','--format','json','--all-track-errors','--schematic-parity','--severity-all','--exit-code-violations','-o',OUT/'drc.json',pcb)
    checked('pcb','export','step','--board-only','--force','-o',OUT/(NAME+'-board-only.step'),pcb)
    checked('pcb','export','svg','--mode-single','--fit-page-to-board','--exclude-drawing-sheet','-l','F.Cu,Edge.Cuts','-o',OUT/'front.svg',pcb)
    checked('pcb','export','svg','--mode-single','--fit-page-to-board','--exclude-drawing-sheet','--mirror','-l','B.Cu,Edge.Cuts','-o',OUT/'back.svg',pcb)
    checked('sch','export','svg','--exclude-drawing-sheet','-o',OUT/'schematic-svg',sch)
    for svg in OUT.rglob('*.svg'):
        write(svg,'\n'.join(line.rstrip() for line in svg.read_text(encoding='utf-8').splitlines())+'\n')
    assert not any(json.loads((OUT/'drc.json').read_text())[k] for k in ['violations','unconnected_items','schematic_parity'])
    record={'result':'PASS native circuit/netlist/ERC/DRC','generated_utc':datetime.now(timezone.utc).isoformat(),
            'kicad_version':'10.0.6','manufacturer_reference':{'url':URL,'sha256':digest(source),'pages':[4,11,12]},
            'functional_nets':{n:sorted(v) for n,v in actual.items()},'native_exit_codes':[c['exit_code'] for c in COMMANDS],
            'physical_qualification':False,'adopted_into_fan_CAD':False,'fabrication_release':False,
            'input_sha256':{str(q.relative_to(ROOT)):digest(q) for q in [Path(__file__),ROOT/'tools/build_encoder_board.py',
                             source,ROOT/'hardware/pcb/rev_c/circuit-population.json']},
            'artifact_sha256':{str(q.relative_to(ROOT)):digest(q) for q in OUT.rglob('*') if q.is_file() and q.name!='provenance.json' and q.suffix!='.kicad_prl'},
            'limits':['Independent electrical prototype candidate; installed sensor/retainer/loom CAD remains required.',
                      'Pin order is viewed from sensor side; do not mirror it using a solder-side image.',
                      'Total 1.6mm mechanical datum must be checked separately from the native dielectric-only STEP.',
                      'No fabrication outputs or physical solder, I2C, mounting or pressure-system qualification.']}
    write(OUT/'provenance.json',json.dumps(record,indent=2)+'\n')
    print('PASS pressure daughterboard: exact captured nets, all-severity native ERC/DRC, EXIT 0',flush=True)


if __name__=='__main__':main()
