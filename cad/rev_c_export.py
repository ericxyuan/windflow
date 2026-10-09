"""Export a named, coloured STEP assembly after source-matched CAD checks."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,re
import cadquery as cq

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'cad/rev_c'

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def verify(report):
    for group in ('input_sha256','artifact_sha256','geometry_sha256'):
        for name,d in report.get(group,{}).items():
            assert digest(ROOT/name)==d,('Stale validation',name)

def main():
    head=json.loads((OUT/'head-validation.json').read_text())
    motion=json.loads((OUT/'motion-validation.json').read_text())
    encoder=json.loads((OUT/'encoder-validation.json').read_text())
    assert json.loads((OUT/'build-state.json').read_text())['status']=='PASS'
    assert not head['unintended_issues'] and motion['result']=='PASS' and encoder['result']=='PASS'
    verify(head);verify(motion);verify(encoder)
    excluded={'head-flowing-unsplit-development','REF-ESC-connector-corridor',
              'REF-new-power-board-reserve-NOT-ROUTED'}
    assembly=cq.Assembly(name='Windflow-Rev-C-assembled-development')
    manifest=[]
    for entry in head['parts']:
        name=entry['name']
        if name in excluded:continue
        s=cq.importers.importStep(str(OUT/(name+'.step'))).val()
        if name.startswith('TPU') or name=='base-replaceable-feet-development':color=cq.Color(.20,.22,.24)
        elif entry['printed'] and ('panel' not in name):color=cq.Color(.83,.85,.87)
        elif 'mechanism' in name or 'carrier' in name:color=cq.Color(.35,.39,.44)
        elif 'vendor' in name:color=cq.Color(.08,.42,.25)
        elif 'magnet' in name:color=cq.Color(.6,.63,.66)
        elif 'lens' in name:color=cq.Color(.65,.82,.93,.30)
        else:color=cq.Color(.18,.22,.29)
        assembly.add(s,name=name,color=color)
        manifest.append({'name':name,'solid_count':len(s.Solids()),'source_sha256':digest(OUT/(name+'.step'))})
    target=OUT/'Windflow-Rev-C-integration-2026-10-07.step'
    assembly.export(str(target),exportType='STEP',mode='default')
    # Independent round-trip confirms geometry preservation. Product names in
    # the STEP verify that this is a hierarchy export, not a merged compound.
    restored=cq.importers.importStep(str(target)).val()
    original=assembly.toCompound()
    assert restored.isValid()
    delta=abs(restored.Volume()-original.Volume())
    assert delta<.1,(delta,restored.Volume(),original.Volume())
    raw=target.read_text(errors='replace')
    assert all(name in raw for name in ('Raspberry-Pi-Pico-SC0915-vendor','head-left-integral-outlet','REF-impeller-P1-installed-test-only'))
    report={'result':'PASS: named STEP assembly round-trip','timestamp_utc':datetime.now(timezone.utc).isoformat(),
       'physical_qualification':False,'path':str(target.relative_to(ROOT)).replace('\\','/'),
       'sha256':digest(target),'bytes':target.stat().st_size,'named_part_groups':len(manifest),
       'round_trip_solids':len(restored.Solids()),'round_trip_volume_difference_mm3':delta,
       'components':manifest,'excluded_reference_reserves':sorted(excluded),
       'input_sha256':{str(p.relative_to(ROOT)):digest(p) for p in [Path(__file__),OUT/'head-validation.json',OUT/'motion-validation.json',OUT/'encoder-validation.json']},
       'limits':['Imported hierarchy has no kinematic mates; CAD source remains in Python and separate native FeatureScript.',
                 'Purchased drawing envelopes for motor/servo/ESC are explicitly unverified; circuit-board reserve is omitted.',
                 'Wiring, pressure hoses and some assembly fasteners are not represented. No print or operation release.']}
    (OUT/'integration-export-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PASS',len(manifest),'named groups;',len(restored.Solids()),'solids;',delta,'mm3 round-trip difference',flush=True)

if __name__=='__main__':main()
