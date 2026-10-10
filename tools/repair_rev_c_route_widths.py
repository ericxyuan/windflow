"""Correct below-minimum route widths in an isolated, source-checked candidate.

Does not change the authoritative board or relax its design rules. KiCad's
native DRC is mandatory; passing it alone does not approve power/thermal layout.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,shutil,subprocess,collections
import pcbnew as p

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'hardware/pcb/rev_c'
INPUT=ROOT/'build/rev-c-board/converted-candidate/windflow-rev-c.kicad_pcb'
OUT=ROOT/'build/rev-c-board/width-repaired-candidate'


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def placement(board):
    return sorted((f.GetReference(),f.GetValue(),f.GetFPID().GetUniStringLibId(),f.GetLayer(),
        f.GetPosition().x,f.GetPosition().y,round(f.GetOrientationDegrees(),6),
        sorted((q.GetNumber(),q.GetNetname(),q.GetPosition().x,q.GetPosition().y,
                q.GetSize().x,q.GetSize().y,q.GetDrillSize().x,q.GetDrillSize().y)
               for q in f.Pads())) for f in board.GetFootprints())


def main():
    assert OUT.resolve().is_relative_to((ROOT/'build').resolve())
    board=p.LoadBoard(str(INPUT));original=p.LoadBoard(str(SOURCE/'windflow-rev-c.kicad_pcb'))
    assert placement(board)==placement(original),'Existing route moved/changed a current footprint or pad net'
    project=json.loads((SOURCE/'windflow-rev-c.kicad_pro').read_text())
    minimum=project['board']['design_settings']['rules']['min_track_width']
    assert minimum==.2,'Review changed fabrication minimum before repairing a route'
    OUT.mkdir(parents=True,exist_ok=True)
    for path in SOURCE.iterdir():
        if path.suffix in ('.kicad_pro','.kicad_dru','.kicad_sch','.kicad_sym') or path.name in ('fp-lib-table','sym-lib-table'):
            shutil.copyfile(path,OUT/path.name)
    shutil.copytree(SOURCE/'WindflowCarrier.pretty',OUT/'WindflowCarrier.pretty',dirs_exist_ok=True)
    changed=[];net_data=collections.defaultdict(list)
    for track in board.GetTracks():
        if isinstance(track,p.PCB_VIA): continue
        old=p.ToMM(track.GetWidth())
        if old<minimum:
            track.SetWidth(p.FromMM(minimum))
            changed.append({'net':track.GetNetname(),'layer':board.GetLayerName(track.GetLayer()),
                            'old_mm':old,'new_mm':minimum})
        net_data[track.GetNetname()].append((p.ToMM(track.GetWidth()),p.ToMM(track.GetLength()),board.GetLayerName(track.GetLayer())))
    target=OUT/'windflow-rev-c.kicad_pcb';p.SaveBoard(str(target),board)
    cli=ROOT/'.tools/kicad-10.0.6/bin/kicad-cli.exe';drc=OUT/'drc.json'
    run=subprocess.run([str(cli),'pcb','drc',str(target),'--format','json','--schematic-parity',
                        '--severity-all','--output',str(drc)],capture_output=True,text=True)
    assert run.returncode==0,(run.returncode,run.stderr)
    native=json.loads(drc.read_text(encoding='utf-8'))
    result='PASS' if not native['violations'] and not native['unconnected_items'] and not native['schematic_parity'] else 'FAIL'
    report={'result':result,'generated_utc':datetime.now(timezone.utc).isoformat(),'candidate_only':True,
            'physical_qualification':False,'changed_tracks':len(changed),'changes':changed,
            'current_placement_and_pad_nets_unchanged':True,'fabrication_rules_unchanged':True,
            'native_checks':{'violations':len(native['violations']),
                'violation_types':dict(collections.Counter(x['type'] for x in native['violations'])),
                'unconnected_items':len(native['unconnected_items']),'schematic_parity':len(native['schematic_parity'])},
            'net_widths':{n:{'minimum_mm':min(q[0] for q in data),'maximum_mm':max(q[0] for q in data),
                'total_track_length_mm':sum(q[1] for q in data),'layers':sorted(set(q[2] for q in data))}
                         for n,data in sorted(net_data.items())},
            'input_sha256':{str(x.relative_to(ROOT)):digest(x) for x in (Path(__file__),INPUT,
                SOURCE/'windflow-rev-c.kicad_pcb',SOURCE/'windflow-rev-c.kicad_pro',SOURCE/'windflow-rev-c.kicad_dru',SOURCE/'windflow-rev-c.kicad_sch')},
            'artifact_sha256':{str(x.relative_to(ROOT)):digest(x) for x in (target,drc)},
            'limits':['Candidate only. No routing adoption or fabrication release.',
                      'Power necks, return paths, regulator decoupling, heat dissipation and sensor routing still require review.',
                      'Native geometry/connectivity checks do not establish current capacity, thermal behavior or EMC.']}
    (OUT/'width-repair-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(result,report['changed_tracks'],'tracks corrected;',json.dumps(report['native_checks']),flush=True)
    for issue in native['violations'][:10]: print(issue['type'],issue['description'],flush=True)
    if result!='PASS': raise SystemExit(1)


if __name__=='__main__': main()
