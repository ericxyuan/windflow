"""Develop the USB-to-fuse copper branch, preserving incomplete-board status."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import math
import shutil
import subprocess
import collections
import pcbnew as p
from repair_rev_c_route_widths import placement

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'hardware/pcb/rev_c'
EVIDENCE = SOURCE/'route-study'
PARENT = ROOT/'build/rev-c-board/ground-return-candidate'
OUT = ROOT/'build/rev-c-board/input-copper-candidate'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def vec(x, y):
    return p.VECTOR2I(p.FromMM(x), p.FromMM(y))


def main():
    parent_report_path = EVIDENCE/'ground-return-development.json'
    parent = json.loads(parent_report_path.read_text())
    assert parent['result'] == 'INCOMPLETE' and parent['native_exit_code'] == 5
    for key in ['input_sha256', 'artifact_sha256']:
        for name, sha in parent[key].items():
            assert digest(ROOT/name) == sha, ('Stale parent route', name)
    parameter_path = EVIDENCE/'input-copper-parameters.json'
    settings = json.loads(parameter_path.read_text())
    assert settings['via_count'] == 2 and settings['via_drill_mm'] == .3
    OUT.mkdir(exist_ok=True)
    for file in PARENT.iterdir():
        if file.suffix in ['.kicad_sch','.kicad_pro','.kicad_dru','.kicad_sym'] or file.name in ['fp-lib-table','sym-lib-table']:
            shutil.copyfile(file, OUT/file.name)
        elif file.is_dir() and file.suffix == '.pretty':
            shutil.copytree(file, OUT/file.name, dirs_exist_ok=True)
    board = p.LoadBoard(str(PARENT/'windflow-rev-c.kicad_pcb'))
    baseline = p.LoadBoard(str(SOURCE/'windflow-rev-c.kicad_pcb'))
    assert placement(board) == placement(baseline)
    assert not any(t.GetNetname() == 'PD_RAW' for t in board.GetTracks())
    # The initial signal routing occupies the power-device escape region. Remove
    # only the declared signal nets; their missing connections stay explicit in
    # the native checker until they are rerouted around the reserved power path.
    removed = collections.Counter()
    for track in list(board.GetTracks()):
        if track.GetNetname() in settings['signal_nets_to_reroute']:
            removed[track.GetNetname()] += 1
            board.Delete(track)
    pads = [q for f in board.GetFootprints() for q in f.Pads()]
    layers = [p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]
    obstacles = {layer:[] for layer in layers}
    for q in pads:
        for layer in layers:
            if q.GetLayerSet().Contains(layer):
                obstacles[layer].append((q.GetNetname(),q.GetEffectiveShape(layer),q))
    for t in board.GetTracks():
        for layer in layers:
            if t.GetLayerSet().Contains(layer):
                obstacles[layer].append((t.GetNetname(),t.GetEffectiveShape(layer),t))
    drills = [(q.GetPosition(),max(q.GetDrillSize().x,q.GetDrillSize().y)/2) for q in pads
              if q.GetAttribute() in [p.PAD_ATTRIB_PTH,p.PAD_ATTRIB_NPTH]]
    drills.extend((t.GetPosition(),t.GetDrillValue()/2) for t in board.GetTracks() if isinstance(t,p.PCB_VIA))
    holes = [(3,3),(77,3),(3,52),(77,52)]

    def free(shape, layer, new_via=False):
        if any(p.SHAPE.Collide(shape,p.SHAPE_CIRCLE(vec(x,y),p.FromMM(2.8)),0) for x,y in holes):
            return False
        for net, other, item in obstacles[layer]:
            if net != 'PD_RAW' and p.SHAPE.Collide(shape,other,p.FromMM(settings['clearance_margin_mm'])):
                return False
            if new_via and isinstance(item,p.PAD) and item.GetAttribute()==p.PAD_ATTRIB_SMD:
                if p.SHAPE.Collide(shape,other,p.FromMM(settings['smd_land_to_new_via_margin_mm'])):
                    return False
        return True

    fps = {f.GetReference():f for f in board.GetFootprints()}
    connector = next(q for q in fps['J1'].Pads() if q.GetNumber()=='1')
    fuse = next(q for q in fps['F1'].Pads() if q.GetNumber()=='1')
    assert connector.GetNetname() == fuse.GetNetname() == 'PD_RAW'
    assert fuse.GetLayerSet().Contains(p.B_Cu)
    selected = None
    rejected = []
    arrays = list(settings['via_arrays_to_try_mm'])
    grid = settings['via_array_search_grid_mm']
    domain = []
    for ix in range(round(settings['via_array_search_x_mm'][0]/grid),round(settings['via_array_search_x_mm'][1]/grid)+1):
        for iy in range(round(settings['via_array_search_y_mm'][0]/grid),round(settings['via_array_search_y_mm'][1]/grid)+1):
            x,y = ix*grid,iy*grid
            distance = math.hypot(x-p.ToMM(fuse.GetPosition().x),y-p.ToMM(fuse.GetPosition().y))
            if .5 <= distance <= settings['maximum_pad_neck_length_mm']:
                domain.extend([(distance,x,y,'x'),(distance,x,y,'y')])
    arrays.extend([a[1:] for a in sorted(domain)])
    for x,y,axis in arrays:
        centre = vec(x,y)
        offset = settings['array_half_spacing_mm']
        ends = [vec(x-offset,y),vec(x+offset,y)] if axis=='x' else [vec(x,y-offset),vec(x,y+offset)]
        if any(any(math.hypot(at.x-pos.x,at.y-pos.y)<radius+p.FromMM(settings['via_drill_mm']/2+settings['hole_clearance_mm'])
                   for pos,radius in drills) for at in ends):
            rejected.append([x,y,axis,'drill separation'])
            continue
        if not all(free(p.SHAPE_CIRCLE(at,p.FromMM(settings['via_diameter_mm']/2)),layer,True) for at in ends for layer in layers):
            rejected.append([x,y,axis,'via copper or paste'])
            continue
        neck = p.SHAPE_SEGMENT(fuse.GetPosition(),centre,p.FromMM(settings['pad_neck_width_mm']))
        stem = p.SHAPE_SEGMENT(ends[0],ends[1],p.FromMM(settings['array_stem_width_mm']))
        if not free(neck,p.B_Cu) or not free(stem,p.B_Cu):
            rejected.append([x,y,axis,'neck or stem'])
            continue
        for layer_name in settings['bus_layers_to_try']:
            layer = {'F.Cu':p.F_Cu,'In2.Cu':p.In2_Cu}[layer_name]
            for jog_y in settings['bus_jog_y_to_try_mm']:
                start = connector.GetPosition()
                path = [start,vec(p.ToMM(start.x),jog_y),vec(x,jog_y),centre]
                path = [at for i,at in enumerate(path) if i==0 or at!=path[i-1]]
                if all(free(p.SHAPE_SEGMENT(a,b,p.FromMM(settings['bus_width_mm'])),layer) for a,b in zip(path,path[1:])):
                    selected = centre,ends,path,layer
                    break
            if selected:
                break
        if selected:
            break
        rejected.append([x,y,axis,'wide bus path'])
    if not selected:
        print('Reviewed array rejections',collections.Counter(row[3] for row in rejected),rejected[:12],flush=True)
    assert selected, 'No collision-free reviewed input branch; do not relax clearances'
    centre,ends,path,bus_layer = selected
    segments = []

    def add_track(a,b,width,layer,role):
        track = p.PCB_TRACK(board)
        track.SetStart(a);track.SetEnd(b);track.SetWidth(p.FromMM(width));track.SetLayer(layer);track.SetNet(fuse.GetNet())
        board.Add(track)
        segments.append({'role':role,'width_mm':width,'length_mm':p.ToMM(track.GetLength()),
                         'layer':board.GetLayerName(layer),'start_mm':[p.ToMM(a.x),p.ToMM(a.y)],'end_mm':[p.ToMM(b.x),p.ToMM(b.y)]})

    add_track(fuse.GetPosition(),centre,settings['pad_neck_width_mm'],p.B_Cu,'fuse pad neck')
    add_track(ends[0],ends[1],settings['array_stem_width_mm'],p.B_Cu,'symmetric paired-via stem')
    for a,b in zip(path,path[1:]):
        add_track(a,b,settings['bus_width_mm'],bus_layer,'wide input bus')
    for at in ends:
        via = p.PCB_VIA(board)
        via.SetPosition(at);via.SetWidth(p.FromMM(settings['via_diameter_mm']));via.SetDrill(p.FromMM(settings['via_drill_mm']))
        via.SetViaType(p.VIATYPE_THROUGH);via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(fuse.GetNet());board.Add(via)
    board.BuildConnectivity();p.ZONE_FILLER(board).Fill(board.Zones())
    assert placement(board) == placement(baseline)
    output = OUT/'windflow-rev-c.kicad_pcb';p.SaveBoard(str(output),board)
    native_path = OUT/'drc.json'
    checked = subprocess.run([str(ROOT/'.tools/kicad-10.0.6/bin/kicad-cli.exe'),'pcb','drc',str(output),'--format','json',
                              '--schematic-parity','--severity-all','--exit-code-violations','--output',str(native_path)],capture_output=True,text=True)
    native = json.loads(native_path.read_text())
    counts = {k:len(native[k]) for k in ['violations','unconnected_items','schematic_parity']}
    assert not counts['violations'] and not counts['schematic_parity'],(checked.returncode,counts,native['violations'])
    missing = collections.Counter(i['items'][0]['description'].split('[')[1].split(']')[0] for i in native['unconnected_items'])
    assert missing['PD_RAW'] == 0
    assert checked.returncode == 5 and counts['unconnected_items'] > 0
    # DC resistance only; no empirical temperature-rise or current-rating model.
    rho = settings['calculation_copper_resistivity_ohm_mm2_per_m']
    via_single_r = rho*(settings['calculation_board_thickness_mm']/1000)/(math.pi*settings['via_drill_mm']*settings['calculation_via_barrel_thickness_mm'])
    calculations = []
    for thickness in settings['calculation_copper_thicknesses_mm']:
        neck_r = rho*(segments[0]['length_mm']/1000)/(segments[0]['width_mm']*thickness)
        # Equal symmetric branch sharing makes the two half-stems parallel.
        stem_r = rho*(segments[1]['length_mm']/2/1000)/(segments[1]['width_mm']*thickness)/2
        bus_r = sum(rho*(s['length_mm']/1000)/(s['width_mm']*thickness) for s in segments[2:])
        total = neck_r+stem_r+bus_r+via_single_r/2
        for current in [settings['continuous_design_current_a'],settings['review_current_a']]:
            calculations.append({'copper_thickness_mm':thickness,'current_a':current,'resistance_ohm_at_reference_temperature':total,
                                 'drop_v':total*current,'copper_loss_w':total*current*current})
    report = {'result':'INCOMPLETE BOARD; PD_RAW branch geometry and continuity checked',
              'generated_utc':datetime.now(timezone.utc).isoformat(),'physical_qualification':False,'adopted_as_main_board':False,
              'power_layout_approved':False,'native_exit_code':checked.returncode,'native_counts':counts,'missing_by_net':dict(missing),
              'signal_tracks_and_vias_removed_for_rerouting':dict(removed),
              'PD_RAW_missing_connections':0,'segments':segments,'via_centres_mm':[[p.ToMM(at.x),p.ToMM(at.y)] for at in ends],
              'dc_calculation_assumptions':settings,'dc_resistance_estimates':calculations,
              'input_sha256':{str(q.relative_to(ROOT)):digest(q) for q in [Path(__file__),parameter_path,parent_report_path,PARENT/'windflow-rev-c.kicad_pcb']},
              'artifact_sha256':{str(q.relative_to(ROOT)):digest(q) for q in [output,native_path]},
              'limits':['Native exit 5 reflects remaining missing connections; the board is not manufacture-ready.',
                        'DC copper estimates omit fuse/connector resistance, pad spreading, thermal rise, plating variation and unequal via sharing.',
                        'No current rating, thermal/EMC or assembly qualification. The authoritative board is unchanged.']}
    (EVIDENCE/'input-copper-development.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PD_RAW continuity checked; incomplete native board',counts,'EXIT',checked.returncode,flush=True)


if __name__ == '__main__':
    main()
