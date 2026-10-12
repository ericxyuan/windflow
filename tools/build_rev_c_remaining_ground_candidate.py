"""Develop outstanding low-voltage returns; retain incomplete power-board status."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import collections
import heapq
import math
import shutil
import subprocess
import pcbnew as p
from repair_rev_c_route_widths import placement
from build_rev_c_signal_recovery_candidate import signature

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/'hardware/pcb/rev_c/route-study'
PARENT=ROOT/'build/rev-c-board/signal-recovery-candidate'
OUT=ROOT/'build/rev-c-board/remaining-ground-candidate'


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parent_path=EVIDENCE/'signal-recovery-development.json'
    parent=json.loads(parent_path.read_text())
    for key in ['input_sha256','artifact_sha256']:
        for name,sha in parent[key].items():assert digest(ROOT/name)==sha,('Stale input',name)
    board=p.LoadBoard(str(PARENT/'windflow-rev-c.kicad_pcb'))
    baseline=p.LoadBoard(str(ROOT/'hardware/pcb/rev_c/windflow-rev-c.kicad_pcb'))
    assert placement(board)==placement(baseline)
    before=collections.Counter(signature(t) for t in board.GetTracks())
    fps={f.GetReference():f for f in board.GetFootprints()}
    pending=json.loads((EVIDENCE/'ground-return-development.json').read_text())['remaining_ground_escape_pads']
    pads=[q for f in board.GetFootprints() for q in f.Pads()]
    anchors=[q.GetPosition() for q in pads if q.GetNetname()=='GND' and q.GetAttribute()==p.PAD_ATTRIB_PTH]
    anchors.extend(t.GetPosition() for t in board.GetTracks() if isinstance(t,p.PCB_VIA) and t.GetNetname()=='GND')
    records=[];failed=[]
    for ref,pin,xy in pending:
        pad=next(q for q in fps[ref].Pads() if q.GetNumber()==pin)
        assert pad.GetNetname()=='GND'
        layer=p.B_Cu if pad.GetLayerSet().Contains(p.B_Cu) else p.F_Cu
        start=pad.GetPosition()
        assert abs(p.ToMM(start.x)-xy[0])<1e-6 and abs(p.ToMM(start.y)-xy[1])<1e-6
        candidates=sorted(anchors,key=lambda at:math.hypot(at.x-start.x,at.y-start.y))[:30]
        candidates=[at for at in candidates if math.hypot(at.x-start.x,at.y-start.y)<p.FromMM(8)]
        assert candidates,('No nearby grounded return anchor',ref,pin)
        obstacles=[q.GetEffectiveShape(layer) for q in pads if q.GetNetname()!='GND' and q.GetLayerSet().Contains(layer)]
        obstacles.extend(t.GetEffectiveShape(layer) for t in board.GetTracks() if t.GetNetname()!='GND' and t.GetLayerSet().Contains(layer))
        indexed=[];clearance=p.FromMM(.21)
        for shape in obstacles:
            bb=shape.BBox(0)
            indexed.append((shape,bb.GetX()-clearance,bb.GetY()-clearance,bb.GetRight()+clearance,bb.GetBottom()+clearance))
        via_obstacles=[]
        for item in pads+list(board.GetTracks()):
            for copper_layer in [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]:
                if not item.GetLayerSet().Contains(copper_layer):continue
                smd=isinstance(item,p.PAD) and item.GetAttribute()==p.PAD_ATTRIB_SMD
                if item.GetNetname()=='GND' and not smd:continue
                gap=p.FromMM(.15) if item.GetNetname()=='GND' else clearance
                shape=item.GetEffectiveShape(copper_layer);bb=shape.BBox(0)
                via_obstacles.append((shape,gap,bb.GetX()-gap,bb.GetY()-gap,bb.GetRight()+gap,bb.GetBottom()+gap))
        drills=[(q.GetPosition(),max(q.GetDrillSize().x,q.GetDrillSize().y)/2) for q in pads if q.GetAttribute() in [p.PAD_ATTRIB_PTH,p.PAD_ATTRIB_NPTH]]
        drills.extend((t.GetPosition(),t.GetDrillValue()/2) for t in board.GetTracks() if isinstance(t,p.PCB_VIA))
        def via_ok(at):
            if any(math.hypot(at.x-pos.x,at.y-pos.y)<radius+p.FromMM(.15+.26) for pos,radius in drills):return False
            shape=p.SHAPE_CIRCLE(at,p.FromMM(.3));radius=p.FromMM(.3)
            left,right,top,bottom=at.x-radius,at.x+radius,at.y-radius,at.y+radius
            if not (p.FromMM(.7)<=left<=right<=p.FromMM(79.3) and p.FromMM(.7)<=top<=bottom<=p.FromMM(54.3)):return False
            if any(p.SHAPE.Collide(shape,p.SHAPE_CIRCLE(p.VECTOR2I(p.FromMM(x),p.FromMM(y)),p.FromMM(2.8)),0)
                   for x,y in [(3,3),(77,3),(3,52),(77,52)]):return False
            return not any(p.SHAPE.Collide(shape,other,gap) for other,gap,x0,y0,x1,y1 in via_obstacles
                           if not(right<x0 or left>x1 or bottom<y0 or top>y1))
        # These local ground escapes are not the load-return bus. Their current
        # allocation/decoupling loop still requires the power-layout review.
        width=.2
        def free(a,b):
            radius=p.FromMM(width/2);shape=p.SHAPE_SEGMENT(a,b,p.FromMM(width))
            left,right=min(a.x,b.x)-radius,max(a.x,b.x)+radius
            top,bottom=min(a.y,b.y)-radius,max(a.y,b.y)+radius
            if not (p.FromMM(.7)<=left<=right<=p.FromMM(79.3) and p.FromMM(.7)<=top<=bottom<=p.FromMM(54.3)):return False
            if any(p.SHAPE.Collide(shape,p.SHAPE_CIRCLE(p.VECTOR2I(p.FromMM(x),p.FromMM(y)),p.FromMM(2.8)),0)
                   for x,y in [(3,3),(77,3),(3,52),(77,52)]):return False
            return not any(p.SHAPE.Collide(shape,other,clearance) for other,x0,y0,x1,y1 in indexed
                           if not(right<x0 or left>x1 or bottom<y0 or top>y1))
        step=p.FromMM(.1);maximum=p.FromMM(10)
        def estimate(at):return min(math.hypot(at.x-goal.x,at.y-goal.y) for goal in candidates)
        queue=[(estimate(start),0.,0,0)];costs={(0,0):0.};parents={};goal=None;target=None;new_via=False
        while queue:
            score,cost,ix,iy=heapq.heappop(queue)
            if cost!=costs[ix,iy]:continue
            at=start+p.VECTOR2I(ix*step,iy*step)
            close=[end for end in candidates if math.hypot(at.x-end.x,at.y-end.y)<=step*1.5]
            valid=next((end for end in close if free(at,end)),None)
            if valid is not None:
                goal=(ix,iy);target=valid;break
            if cost>p.FromMM(.4) and via_ok(at):
                goal=(ix,iy);target=at;new_via=True;break
            for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]:
                neighbour=(ix+dx,iy+dy);new=cost+step*math.hypot(dx,dy)
                if new>maximum or new>=costs.get(neighbour,float('inf')):continue
                end=start+p.VECTOR2I(neighbour[0]*step,neighbour[1]*step)
                if new+estimate(end)>maximum or not free(at,end):continue
                costs[neighbour]=new;parents[neighbour]=(ix,iy);heapq.heappush(queue,(new+estimate(end),new,*neighbour))
        if goal is None:
            failed.append({'ref':ref,'pin':pin,'reachable_grid_nodes':len(costs),
                           'reason':'Existing surface routes and through-via clearances close the local escape region; placement/routing redesign remains required.'})
            print('RETURN REDESIGN NEEDED',ref,pin,flush=True)
            continue
        path=[goal]
        while path[-1]!=(0,0):path.append(parents[path[-1]])
        path.reverse();points=[start+p.VECTOR2I(ix*step,iy*step) for ix,iy in path]+[target]
        reduced=[points[0]]
        for i in range(1,len(points)-1):
            a,b,c=points[i-1:i+2]
            if (b.x-a.x)*(c.y-b.y)!=(b.y-a.y)*(c.x-b.x):reduced.append(b)
        if target!=reduced[-1]:reduced.append(target)
        length=0
        for a,b in zip(reduced,reduced[1:]):
            if a==b:continue
            track=p.PCB_TRACK(board);track.SetStart(a);track.SetEnd(b);track.SetWidth(p.FromMM(width))
            track.SetLayer(layer);track.SetNet(pad.GetNet());board.Add(track)
            length+=p.ToMM(math.hypot(b.x-a.x,b.y-a.y))
        if new_via:
            via=p.PCB_VIA(board);via.SetPosition(target);via.SetWidth(p.FromMM(.6));via.SetDrill(p.FromMM(.3))
            via.SetViaType(p.VIATYPE_THROUGH);via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(pad.GetNet());board.Add(via)
        anchors.extend(reduced)
        records.append({'ref':ref,'pin':pin,'layer':board.GetLayerName(layer),'width_mm':width,'length_mm':length,
                        'added_ground_via':new_via,
                        'path_xy_mm':[[p.ToMM(at.x),p.ToMM(at.y)] for at in reduced]})
        print('RETURN',ref,pin,width,round(length,3),flush=True)
    OUT.mkdir(exist_ok=True)
    for file in PARENT.iterdir():
        if file.suffix in ['.kicad_sch','.kicad_pro','.kicad_dru','.kicad_sym'] or file.name in ['fp-lib-table','sym-lib-table']:
            shutil.copyfile(file,OUT/file.name)
        elif file.is_dir() and file.suffix=='.pretty':shutil.copytree(file,OUT/file.name,dirs_exist_ok=True)
    assert all(collections.Counter(signature(t) for t in board.GetTracks())[key]>=count for key,count in before.items())
    assert placement(board)==placement(baseline)
    board.BuildConnectivity();p.ZONE_FILLER(board).Fill(board.Zones())
    output=OUT/'windflow-rev-c.kicad_pcb';p.SaveBoard(str(output),board)
    native_path=OUT/'drc.json'
    checked=subprocess.run([str(ROOT/'.tools/kicad-10.0.6/bin/kicad-cli.exe'),'pcb','drc',str(output),'--format','json',
                            '--schematic-parity','--severity-all','--exit-code-violations','--output',str(native_path)],capture_output=True,text=True)
    native=json.loads(native_path.read_text());counts={k:len(native[k]) for k in ['violations','unconnected_items','schematic_parity']}
    assert not counts['violations'] and not counts['schematic_parity'],(checked.returncode,counts,native['violations'][:12])
    missing=collections.Counter(i['items'][0]['description'].split('[')[1].split(']')[0] for i in native['unconnected_items'])
    assert checked.returncode==5 and 0<counts['unconnected_items']<parent['native_counts']['unconnected_items']
    inputs=[Path(__file__),ROOT/'tools/build_rev_c_signal_recovery_candidate.py',ROOT/'tools/repair_rev_c_route_widths.py',
            parent_path,EVIDENCE/'ground-return-development.json',PARENT/'windflow-rev-c.kicad_pcb']
    record={'result':'INCOMPLETE','scope':'Remaining ground escape development with explicit unfinished pads',
            'generated_utc':datetime.now(timezone.utc).isoformat(),'native_counts':counts,'native_exit_code':checked.returncode,
            'missing_by_net':dict(missing),'added_returns':records,'GND_missing_connections':missing['GND'],'unfinished_ground_pads':failed,
            'existing_copper_unchanged':True,'placement_and_pad_nets_unchanged':True,
            'adopted_as_main_board':False,'power_layout_approved':False,'physical_qualification':False,
            'input_sha256':{str(q.relative_to(ROOT)):digest(q) for q in inputs},
            'artifact_sha256':{str(q.relative_to(ROOT)):digest(q) for q in [output,native_path]},
            'limits':['Remaining power connections prevent manufacture; native exit 5 is recorded explicitly.',
                      'Return continuity does not qualify load allocation, decoupling impedance, thermal paths or EMC.',
                      'The authoritative board and prior candidates remain unchanged.']}
    (EVIDENCE/'remaining-ground-development.json').write_text(json.dumps(record,indent=2)+'\n')
    print('Ground development; incomplete native board',counts,'EXIT',checked.returncode,'unfinished pads',failed,flush=True)


if __name__=='__main__':main()
