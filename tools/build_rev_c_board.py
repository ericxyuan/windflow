"""Place the captured Rev C carrier; export an offline routing input.

Use the bundled KiCad Python. Mechanical datums match the 80 x 55 mm tray
target. This generator never labels placement or autorouting a release.
"""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, math, shutil, re, subprocess, xml.etree.ElementTree as ET
import pcbnew as p

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'hardware/pcb/rev_c'
WORK=ROOT/'build/rev-c-board'
WORK.mkdir(parents=True,exist_ok=True)
POP=json.loads((OUT/'circuit-population.json').read_text())['components']
NAME='windflow-rev-c'

def vec(x,y):return p.VECTOR2I(p.FromMM(x),p.FromMM(y))
def mm(v):return p.ToMM(v)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def rect(f):
    r=f.GetBoundingBox(False,False)
    return tuple(mm(v) for v in (r.GetX(),r.GetY(),r.GetRight(),r.GetBottom()))
def collide(a,b,gap=.3):
    return not (a[2]+gap<=b[0] or b[2]+gap<=a[0] or a[3]+gap<=b[1] or b[3]+gap<=a[1])

def retain_tht_apertures(path):
    # Portable KiCad serialization drops these mask flags after a DSN working
    # conversion. Restore the actual vendor THT solder openings, while leaving
    # IC thermal vias tented. Independent native DRC checks the resulting file.
    raw=path.read_text()
    def fix(match):
        block=match.group()
        if re.search(r'\(property "Reference" "[JC][0-9]+"',block):
            block=block.replace('(layers "*.Cu")','(layers "*.Cu" "*.Mask")')
        return block
    raw=re.sub(r'\t\(footprint .*?(?=\n\t\(|\n\)\s*$)',fix,raw,flags=re.S|re.M)
    path.write_text(raw)

# Through-hole connectors have insertion access from the open-bottom service
# opening. Keyed Pico connectors are adjacent, with pin1 marked explicitly.
# The remaining SMD placement uses the underside, away from tray bosses.
FIXED={
 'J15':(11,12.4,90),'J16':(46,12.4,90),
 'J1':(8,23,0),'J18':(8,31,0),'J19':(23,31,0),
 'J20':(73,22,0),'J22':(74,41,90),
 'J2':(36,22,0),'J12':(54,21,0),
 'J7':(44,31,0),'J4':(59,27.05,90),'J5':(67.5,31,0),
 'J11':(53,41,0),'J14':(47,19.5,0),
 'J6':(9.1,49,0),'J8':(35,49,0),'J9':(49.4,49,0),'J10':(63.4,49,0),
 'C2':(20,42,0),'C7':(29,42,0),'C8':(9,42,0),
 'C9':(42,41,0),'C10':(58,33.45,0),
 'EF1':(24,24.6,0),'QRC1':(23,19.5,0),'EF2':(65,21,0),
}
GROUP_ANCHOR={'power':(22,22),'rails':(25,35),'servo':(58,29),
 'ambient':(43,31),'inputs':(36,17),'adc':(36,32),'screen':(24,17),
 'esc':(64,22),'uart':(62,37)}

def main():
    board=p.BOARD();board.SetCopperLayerCount(4)
    settings=board.GetDesignSettings()
    settings.SetBoardThickness(p.FromMM(1.6))
    settings.m_MinClearance=p.FromMM(.2)
    settings.m_TrackMinWidth=p.FromMM(.2)
    settings.m_ViasMinSize=p.FromMM(.6)
    settings.m_MinThroughDrill=p.FromMM(.2)  # 0.5/0.2 library thermal-via lands
    netlist=ET.parse(OUT/(NAME+'.net.xml')).getroot()
    metadata={c.get('ref'):c for c in netlist.find('components')}
    pad_nets={}
    nets={}
    for n in netlist.find('nets'):
        net=p.NETINFO_ITEM(board,n.get('name'));board.Add(net);nets[n.get('name')]=net
        for node in n.findall('node'):pad_nets[(node.get('ref'),node.get('pin'))]=n.get('name')
    footprints={};places=[];occupied={'F':[],'B':[]}
    # All-layer mechanical keepouts match the tray's four M2 supports.
    holes=[(3,3),(77,3),(3,52),(77,52)]
    for x,y in holes:
        r=(x-2.8,y-2.8,x+2.8,y+2.8)
        occupied['F'].append(('mount',r));occupied['B'].append(('mount',r))
    for c in POP:
        if c['location']!='carrier':continue
        f=p.FootprintLoad(str(OUT/'WindflowCarrier.pretty'),c['footprint'].split(':')[1]);assert f,c['ref']
        f.SetReference(c['ref']);f.SetValue(c['value']);f.SetFPIDAsString(c['footprint'])
        for field in metadata[c['ref']].findall('fields/field'):
            name=field.get('name');f.SetField(name,field.text or '')
            f.GetField(name).SetVisible(False)
        if c['dnp']:f.SetAttributes(f.GetAttributes()|p.FP_DNP)
        f.Reference().SetVisible(False);f.Value().SetVisible(False)
        comp=metadata[c['ref']]
        path=comp.find('sheetpath').get('tstamps')+'/'+comp.find('tstamps').text
        f.SetPath(p.KIID_PATH(path));board.Add(f)
        mapping={pin['number']:pin['net'] for pin in c['pins']}
        for pad in f.Pads():
            number=pad.GetNumber()
            if (c['ref'],number) in pad_nets:pad.SetNet(nets[pad_nets[(c['ref'],number)]])
            elif not number and pad.GetAttribute()==p.PAD_ATTRIB_PTH:
                # Library thermal vias belong to the exposed electrical land.
                thermal=mapping.get('25') or (mapping.get('5') if c['ref']=='QRC1' else None)
                assert thermal,('Unmapped thermal via',c['ref'])
                pad.SetNet(nets[thermal])
        footprints[c['ref']]=f

    def place(c,at,angle,back=False):
        f=footprints[c['ref']]
        if back and f.GetLayer()==p.F_Cu:f.Flip(f.GetPosition(),False)
        f.SetOrientationDegrees(angle);f.SetPosition(vec(*at))
        r=rect(f);layer='B' if back else 'F'
        issues=[ref for ref,ob in occupied[layer] if collide(r,ob)]
        assert not issues,(c['ref'],r,issues)
        assert r[0]>=.5 and r[1]>=.5 and r[2]<=79.5 and r[3]<=54.5,(c['ref'],'edge',r)
        occupied[layer].append((c['ref'],r))
        # Reserve the real through-hole pads on the opposite face, not a
        # nonexistent underside plastic body.
        if any(q.GetLayerSet().Contains(p.F_Cu) and q.GetLayerSet().Contains(p.B_Cu) for q in f.Pads()):
            other='F' if back else 'B'
            for q in f.Pads():
                if not (q.GetLayerSet().Contains(p.F_Cu) and q.GetLayerSet().Contains(p.B_Cu)):continue
                xx,yy=mm(q.GetPosition().x),mm(q.GetPosition().y)
                sx,sy=mm(q.GetSize().x)/2,mm(q.GetSize().y)/2
                occupied[other].append((c['ref']+' solder', (xx-sx,yy-sy,xx+sx,yy+sy)))
        places.append({'ref':c['ref'],'xy_mm':list(at),'angle_deg':angle,'side':layer,'bounds_mm':list(r),'dnp':c['dnp']})

    selected=[c for c in POP if c['location']=='carrier']
    for c in selected:
        if c['ref'] in FIXED:
            x,y,angle,*back=FIXED[c['ref']];place(c,(x,y),angle,back=bool(back and back[0]))
    remaining=[c for c in selected if c['ref'] not in FIXED]
    # Large packages first; then small decoupling/filters near their group.
    remaining.sort(key=lambda c:(-(rect(footprints[c['ref']])[2]-rect(footprints[c['ref']])[0])*(rect(footprints[c['ref']])[3]-rect(footprints[c['ref']])[1]),c['ref']))
    for c in remaining:
        f=footprints[c['ref']];f.Flip(f.GetPosition(),False)
        anchor=GROUP_ANCHOR[c['group']]
        candidates=sorted(((x*.5,y*.5) for x in range(4,157) for y in range(4,107)),key=lambda xy:(xy[0]-anchor[0])**2+(xy[1]-anchor[1])**2)
        found=None
        for at in candidates:
            for angle in (0,90):
                f.SetOrientationDegrees(angle);f.SetPosition(vec(*at));r=rect(f)
                if r[0]<.5 or r[1]<.5 or r[2]>79.5 or r[3]>54.5:continue
                if any(collide(r,ob) for _,ob in occupied['B']):continue
                found=(at,angle);break
            if found:break
        assert found,('No space for',c['ref'])
        place(c,*found,back=True)

    for i,(x,y) in enumerate(holes,1):
        f=p.FOOTPRINT(board);f.SetReference('H'+str(i));f.SetValue('M2 NPTH 2.4')
        f.SetAttributes(p.FP_BOARD_ONLY|p.FP_EXCLUDE_FROM_BOM|p.FP_EXCLUDE_FROM_POS_FILES)
        q=p.PAD(f);q.SetAttribute(p.PAD_ATTRIB_NPTH);q.SetShape(p.PAD_SHAPE_CIRCLE)
        q.SetSize(vec(2.4,2.4));q.SetDrillSize(vec(2.4,2.4))
        ls=p.LSET.AllCuMask();ls.AddLayer(p.F_Mask);ls.AddLayer(p.B_Mask);q.SetLayerSet(ls)
        f.Add(q);f.SetPosition(vec(x,y));f.Reference().SetVisible(False);f.Value().SetVisible(False);board.Add(f)
        z=p.ZONE(board);z.SetIsRuleArea(True);z.SetZoneName('M2 '+str(i)+' copper exclusion')
        z.SetLayerSet(p.LSET.AllCuMask(4));z.SetDoNotAllowTracks(True);z.SetDoNotAllowVias(True);z.SetDoNotAllowZoneFills(True)
        z.SetDoNotAllowPads(False);z.SetDoNotAllowFootprints(False)
        poly=z.Outline();poly.NewOutline()
        for j in range(32):poly.Append(vec(x+2.8*math.cos(j*math.pi/16),y+2.8*math.sin(j*math.pi/16)))
        board.Add(z)
    for a,b in [((0,0),(80,0)),((80,0),(80,55)),((80,55),(0,55)),((0,55),(0,0))]:
        line=p.PCB_SHAPE(board);line.SetShape(p.SHAPE_T_SEGMENT);line.SetLayer(p.Edge_Cuts)
        line.SetWidth(p.FromMM(.05));line.SetStart(vec(*a));line.SetEnd(vec(*b));board.Add(line)
    p.SaveBoard(str(OUT/(NAME+'.kicad_pcb')),board)
    routing_copy=WORK/(NAME+'-routing-copy.kicad_pcb')
    shutil.copyfile(OUT/(NAME+'.kicad_pcb'),routing_copy)
    routing_board=p.LoadBoard(str(routing_copy))
    assert p.ExportSpecctraDSN(routing_board,str(WORK/(NAME+'.dsn')))
    # DSN export removes mask layers from THT pads and saves its working file.
    # It is pointed at an ignored copy; authoritative footprints retain masks.
    for c in selected:
        if not c['ref'].startswith(('J','C')):continue
        for q in footprints[c['ref']].Pads():
            if q.GetAttribute()!=p.PAD_ATTRIB_PTH:continue
            ls=p.LSET.AllCuMask();ls.AddLayer(p.F_Mask);ls.AddLayer(p.B_Mask)
            q.SetLayerSet(ls)
    p.SaveBoard(str(OUT/(NAME+'.kicad_pcb')),board)
    retain_tht_apertures(OUT/(NAME+'.kicad_pcb'))
    (OUT/(NAME+'.kicad_dru')).write_text('''(version 1)
(rule "Factory NexFET land spacing only"
 (condition "A.Type == 'Pad' && B.Type == 'Pad' && A.memberOfFootprint('QRC1') && B.memberOfFootprint('QRC1')")
 (constraint clearance (min 0.12mm)))
''')
    cli=ROOT/'.tools/kicad-10.0.6/bin/kicad-cli.exe'
    drc_path=OUT/'board-placement-drc.json'
    checked=subprocess.run([str(cli),'pcb','drc',str(OUT/(NAME+'.kicad_pcb')),
        '--format','json','--schematic-parity','--severity-all','--output',str(drc_path)],
        capture_output=True,text=True,check=True)
    native=json.loads(drc_path.read_text(encoding='utf-8'))
    assert not native['violations'] and not native['schematic_parity'],checked.stdout
    subprocess.run([str(cli),'pcb','export','svg',str(OUT/(NAME+'.kicad_pcb')),
        '--layers','F.Fab,B.Fab,Edge.Cuts','--page-size-mode','2','--output',str(OUT/'board-placement.svg')],
        capture_output=True,text=True,check=True)
    report={'status':'PLACED; routing and electrical layout review pending','timestamp_utc':datetime.now(timezone.utc).isoformat(),
       'physical_qualification':False,'PCB_routed':False,'outline_mm':[80,55],'copper_layers':4,'thickness_mm':1.6,
       'placed_circuit_components':len(places),'placement':places,
       'input_sha256':{'tools/build_rev_c_board.py':digest(Path(__file__)),'hardware/pcb/rev_c/circuit-population.json':digest(OUT/'circuit-population.json')},
       'native_checks':{'copper_package_silkscreen_violations':len(native['violations']),
           'schematic_parity_issues':len(native['schematic_parity']),
           'unconnected_items':len(native['unconnected_items']),'not_routed':True},
       'artifact_sha256':{str(path.relative_to(ROOT)):digest(path) for path in [OUT/(NAME+'.kicad_pcb'),OUT/(NAME+'.kicad_dru'),drc_path,OUT/'board-placement.svg']},
       'limits':['Placement proximity is preliminary; power/thermal/decoupling routes need manual review.',
                 'Board has no routes and is not for fabrication. Through-hole leads and underside SMD clearance need assembly checks.']}
    (OUT/'board-placement.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PLACED',len(places),'circuit footprints; DSN export; not routed',flush=True)

if __name__=='__main__':main()
