"""Import only reviewed signal nets; preserve power copper and incomplete status."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil
import collections
import subprocess
import math
import heapq
import pcbnew as p
from import_rev_c_routing import sexpr, item
from repair_rev_c_route_widths import placement

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT/'hardware/pcb/rev_c/route-study'
PARENT = ROOT/'build/rev-c-board/input-copper-candidate'
OUT = ROOT/'build/rev-c-board/signal-recovery-candidate'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signature(track):
    if isinstance(track,p.PCB_VIA):
        at = track.GetPosition()
        return ('via',track.GetNetname(),at.x,at.y,track.GetWidth(p.F_Cu),track.GetDrillValue())
    a,b = track.GetStart(),track.GetEnd()
    return ('track',track.GetNetname(),track.GetLayer(),a.x,a.y,b.x,b.y,track.GetWidth())


def main():
    parent_path = EVIDENCE/'input-copper-development.json'
    parent = json.loads(parent_path.read_text())
    for key in ['input_sha256','artifact_sha256']:
        for name,sha in parent[key].items():
            assert digest(ROOT/name) == sha,('Stale source copper',name)
    manifest_path = EVIDENCE/'signal-recovery-session-manifest.json'
    manifest = json.loads(manifest_path.read_text())
    session = ROOT/manifest['path']
    assert digest(session) == manifest['sha256']
    assert digest(PARENT/'windflow-rev-c.kicad_pcb') == manifest['source_board_sha256']
    data = sexpr(session.read_text())
    assert item(data,'base_design')[1] == 'signal-recovery'
    board = p.LoadBoard(str(PARENT/'windflow-rev-c.kicad_pcb'))
    baseline = p.LoadBoard(str(ROOT/'hardware/pcb/rev_c/windflow-rev-c.kicad_pcb'))
    assert placement(board) == placement(baseline)
    before = collections.Counter(signature(t) for t in board.GetTracks())
    selected = set(manifest['signal_nets_to_import'])
    assert selected == set(parent['signal_tracks_and_vias_removed_for_rerouting'])
    assert not any(t.GetNetname() in selected for t in board.GetTracks())
    fps = {f.GetReference():f for f in board.GetFootprints()}
    placements = item(data,'placement')
    assert item(placements,'resolution')[1:] == ['um','10']
    refs = []
    for component in placements[1:]:
        if not isinstance(component,list) or component[0]=='resolution':
            continue
        assert component[0] == 'component'
        for place in component[2:]:
            assert place[0] == 'place'
            ref,x,y,side,angle = place[1:6]
            fp = fps[ref]
            assert abs(p.ToMM(fp.GetPosition().x)-float(x)/10000)<.00011
            assert abs(p.ToMM(fp.GetPosition().y)+float(y)/10000)<.00011
            assert (side=='front') == (fp.GetLayer()==p.F_Cu)
            expected = fp.GetOrientationDegrees()+(0 if side=='front' else 180)
            assert abs((float(angle)-expected+180)%360-180)<.0001
            refs.append(ref)
    absent = set(fps)-set(refs)
    assert absent <= {'H1','H2','H3','H4'},('Incomplete electrical placement snapshot',sorted(absent))
    assert all(fps[ref].GetAttributes() & p.FP_BOARD_ONLY for ref in absent)
    routes = item(data,'routes')
    assert item(routes,'resolution')[1:] == ['um','10']
    nets = {n.GetNetname():n for n in board.GetNetInfo().NetsByNetcode().values()}
    layers = {'F.Cu':p.F_Cu,'In2.Cu':p.In2_Cu,'B.Cu':p.B_Cu}
    added = collections.Counter()
    widened = collections.Counter()
    for net in item(routes,'network_out')[1:]:
        assert net[0] == 'net'
        if net[1] not in selected:
            continue
        for element in net[2:]:
            if element[0]=='wire':
                assert len(element)==2 and element[1][0]=='path'
                path = element[1]
                assert path[1] in layers,'Dedicated In1 return plane must not carry signal tracks'
                width = float(path[2])/10000
                assert len(path[3:])%2==0 and .1<=width<=.200001,(net[1],path[:3])
                points = [p.VECTOR2I(p.FromMM(float(path[i])/10000),p.FromMM(-float(path[i+1])/10000))
                          for i in range(3,len(path),2)]
                for a,b in zip(points,points[1:]):
                    assert a != b
                    track = p.PCB_TRACK(board)
                    track.SetStart(a);track.SetEnd(b);track.SetWidth(p.FromMM(.2))
                    track.SetLayer(layers[path[1]]);track.SetNet(nets[net[1]]);board.Add(track)
                    added[net[1]] += 1
                    if width<.2:
                        widened[net[1]] += 1
            elif element[0]=='via':
                assert len(element)==4 and element[1]=='Via[0-3]_600:300_um'
                via = p.PCB_VIA(board)
                via.SetPosition(p.VECTOR2I(p.FromMM(float(element[2])/10000),p.FromMM(-float(element[3])/10000)))
                via.SetWidth(p.FromMM(.6));via.SetDrill(p.FromMM(.3));via.SetViaType(p.VIATYPE_THROUGH)
                via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(nets[net[1]]);board.Add(via)
                added[net[1]] += 1
            else:
                raise AssertionError(('Unsupported selected route element',element[0]))
    assert set(added) == selected
    correction_path = EVIDENCE/'signal-recovery-corrections.json'
    corrections = json.loads(correction_path.read_text())
    corner = corrections['corner']
    old = [p.VECTOR2I(p.FromMM(x),p.FromMM(y)) for x,y in corner['from_xy_mm']]
    delta = p.VECTOR2I(*[p.FromMM(x) for x in corner['shift_xy_mm']])
    moved = 0
    for track in board.GetTracks():
        if isinstance(track,p.PCB_VIA) or track.GetNetname()!=corner['net']:
            continue
        for get,setter in [(track.GetStart,track.SetStart),(track.GetEnd,track.SetEnd)]:
            if get() in old:
                setter(get()+delta);moved += 1
    assert moved>0,'Reviewed ENC_A corner no longer matches this routing session'
    escaped = []
    for request in corrections['missing_smd_escapes']:
        pad = next(q for q in fps[request['ref']].Pads() if q.GetNumber()==request['pin'])
        assert pad.GetNetname()==request['net']
        layer = {'F.Cu':p.F_Cu,'B.Cu':p.B_Cu}[request['layer']]
        assert pad.GetLayerSet().Contains(layer)
        start = pad.GetPosition()
        end = p.VECTOR2I(*[p.FromMM(x) for x in request['via_xy_mm']])
        assert any(isinstance(t,p.PCB_VIA) and t.GetPosition()==end and t.GetNetname()==request['net'] for t in board.GetTracks())
        obstacles = [(q.GetNetname(),q.GetEffectiveShape(layer)) for f in board.GetFootprints() for q in f.Pads() if q.GetLayerSet().Contains(layer)]
        obstacles.extend((t.GetNetname(),t.GetEffectiveShape(layer)) for t in board.GetTracks() if t.GetLayerSet().Contains(layer))
        indexed = []
        for net,shape in obstacles:
            if net==request['net']:continue
            bb=shape.BBox(0)
            clearance=p.FromMM(corrections['clearance_margin_mm'])
            indexed.append((net,shape,bb.GetX()-clearance,bb.GetY()-clearance,bb.GetRight()+clearance,bb.GetBottom()+clearance))
        def free(a,b):
            shape = p.SHAPE_SEGMENT(a,b,p.FromMM(corrections['track_width_mm']))
            if any(p.SHAPE.Collide(shape,p.SHAPE_CIRCLE(p.VECTOR2I(p.FromMM(x),p.FromMM(y)),p.FromMM(2.8)),0)
                   for x,y in [(3,3),(77,3),(3,52),(77,52)]):return False
            radius=p.FromMM(corrections['track_width_mm']/2)
            left,right=min(a.x,b.x)-radius,max(a.x,b.x)+radius
            top,bottom=min(a.y,b.y)-radius,max(a.y,b.y)+radius
            return not any(p.SHAPE.Collide(shape,other,p.FromMM(corrections['clearance_margin_mm']))
                           for net,other,x0,y0,x1,y1 in indexed if not(right<x0 or left>x1 or bottom<y0 or top>y1))
        reduced = [p.VECTOR2I(p.FromMM(x),p.FromMM(y)) for x,y in request['path_xy_mm']]
        assert reduced[0]==start and reduced[-1]==end
        blocked = [(i,request['path_xy_mm'][i:i+2]) for i,(a,b) in enumerate(zip(reduced,reduced[1:])) if not free(a,b)]
        if blocked:
            step=p.FromMM(corrections['route_grid_mm']);maximum=p.FromMM(corrections['maximum_route_length_mm'])
            margin=p.FromMM(corrections['search_margin_mm'])
            bounds=(min(start.x,end.x)-margin,max(start.x,end.x)+margin,min(start.y,end.y)-margin,max(start.y,end.y)+margin)
            queue=[(math.hypot(end.x-start.x,end.y-start.y),0.,0,0)];costs={(0,0):0.};parents={};goal=None
            while queue:
                score,cost,ix,iy=heapq.heappop(queue)
                if cost!=costs[ix,iy]:continue
                at=start+p.VECTOR2I(ix*step,iy*step)
                distance=math.hypot(end.x-at.x,end.y-at.y)
                if distance<=step*1.5 and cost+distance<=maximum and free(at,end):
                    goal=(ix,iy);break
                for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]:
                    neighbour=(ix+dx,iy+dy);new=cost+step*math.hypot(dx,dy)
                    if new>maximum or new>=costs.get(neighbour,float('inf')):continue
                    target=start+p.VECTOR2I(neighbour[0]*step,neighbour[1]*step)
                    if not (bounds[0]<=target.x<=bounds[1] and bounds[2]<=target.y<=bounds[3]):continue
                    if not free(at,target):continue
                    costs[neighbour]=new;parents[neighbour]=(ix,iy)
                    heapq.heappush(queue,(new+math.hypot(end.x-target.x,end.y-target.y),new,*neighbour))
            assert goal is not None,('Signal route requires another layer or placement redesign',request['net'])
            path=[goal]
            while path[-1]!=(0,0):path.append(parents[path[-1]])
            path.reverse();points=[start+p.VECTOR2I(ix*step,iy*step) for ix,iy in path]+[end]
            reduced=[points[0]]
            for i in range(1,len(points)-1):
                a,b,c=points[i-1:i+2]
                if (b.x-a.x)*(c.y-b.y)!=(b.y-a.y)*(c.x-b.x):reduced.append(b)
            reduced.append(end)
        for a,b in zip(reduced,reduced[1:]):
            if a==b:continue
            track=p.PCB_TRACK(board);track.SetStart(a);track.SetEnd(b);track.SetWidth(p.FromMM(.2))
            track.SetLayer(layer);track.SetNet(pad.GetNet());board.Add(track);added[request['net']]+=1
        if request.get('remove_unnecessary_terminal_via'):
            unused = next(t for t in board.GetTracks() if isinstance(t,p.PCB_VIA) and t.GetPosition()==end and t.GetNetname()==request['net'])
            board.Delete(unused)
        escaped.append({**request,'length_mm':sum(p.ToMM(math.hypot(b.x-a.x,b.y-a.y)) for a,b in zip(reduced,reduced[1:])),
                        'path_xy_mm':[[p.ToMM(at.x),p.ToMM(at.y)] for at in reduced]})
    assert collections.Counter(signature(t) for t in board.GetTracks() if t.GetNetname() not in selected)==before
    assert placement(board) == placement(baseline)
    for file in PARENT.iterdir():
        if file.suffix in ['.kicad_sch','.kicad_pro','.kicad_dru','.kicad_sym'] or file.name in ['fp-lib-table','sym-lib-table']:
            shutil.copyfile(file,OUT/file.name)
        elif file.is_dir() and file.suffix=='.pretty':
            shutil.copytree(file,OUT/file.name,dirs_exist_ok=True)
    board.BuildConnectivity();p.ZONE_FILLER(board).Fill(board.Zones())
    output = OUT/'windflow-rev-c.kicad_pcb';p.SaveBoard(str(output),board)
    native_path = OUT/'drc.json'
    checked = subprocess.run([str(ROOT/'.tools/kicad-10.0.6/bin/kicad-cli.exe'),'pcb','drc',str(output),'--format','json',
                              '--schematic-parity','--severity-all','--exit-code-violations','--output',str(native_path)],capture_output=True,text=True)
    native = json.loads(native_path.read_text())
    counts = {k:len(native[k]) for k in ['violations','unconnected_items','schematic_parity']}
    assert not counts['violations'] and not counts['schematic_parity'],(checked.returncode,counts,native['violations'][:12])
    missing = collections.Counter(i['items'][0]['description'].split('[')[1].split(']')[0] for i in native['unconnected_items'])
    assert all(missing[n]==0 for n in selected|{'PD_RAW'}),dict(missing)
    assert checked.returncode==5 and 0<counts['unconnected_items']<parent['native_counts']['unconnected_items']
    record = {'result':'INCOMPLETE','scope':'Displaced signals rerouted around retained wide USB input copper',
              'generated_utc':datetime.now(timezone.utc).isoformat(),'native_exit_code':checked.returncode,'native_counts':counts,
              'missing_by_net':dict(missing),'selected_signal_tracks_and_vias_added':dict(added),
              'signal_segments_raised_to_0p2mm_rule':dict(widened),
              'corner_incident_endpoints_moved':moved,'completed_signal_links':escaped,
              'PD_RAW_and_selected_signals_missing_connections':0,'parent_copper_geometry_unchanged':True,
              'router_omitted_board_only_mounting_refs':sorted(absent),
              'placement_and_pad_nets_unchanged':True,'physical_qualification':False,'adopted_as_main_board':False,'power_layout_approved':False,
              'input_sha256':{str(q.relative_to(ROOT)):digest(q) for q in [Path(__file__),ROOT/'tools/import_rev_c_routing.py',
                              ROOT/'tools/repair_rev_c_route_widths.py',parent_path,manifest_path,session,correction_path,PARENT/'windflow-rev-c.kicad_pcb']},
              'artifact_sha256':{str(q.relative_to(ROOT)):digest(q) for q in [output,native_path]},
              'limits':['Missing power/return connections still prevent manufacture; native exit 5 is recorded.',
                        'Existing copper, placement, circuit and fabrication rules are unchanged.',
                        'No current capacity, thermal, EMC or physical qualification.']}
    (EVIDENCE/'signal-recovery-development.json').write_text(json.dumps(record,indent=2)+'\n')
    print('Six signal nets recovered; incomplete board',counts,'EXIT',checked.returncode,flush=True)


if __name__ == '__main__':
    main()
