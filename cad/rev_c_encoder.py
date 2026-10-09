"""Check the front wheel's rotation, press and service envelopes independently."""
from pathlib import Path
from datetime import datetime, timezone
import math, json, hashlib
import cadquery as cq

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'cad/rev_c'

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def overlap(a,b):
    aa,bb=a.BoundingBox(),b.BoundingBox()
    if any(getattr(aa,k+'max')<=getattr(bb,k+'min')+1e-6 or getattr(bb,k+'max')<=getattr(aa,k+'min')+1e-6 for k in 'xyz'):return 0.
    return max(0.,a.intersect(b).Volume())

def main():
    head=json.loads((OUT/'head-validation.json').read_text())
    assert json.loads((OUT/'build-state.json').read_text())['status']=='PASS'
    assert not head['unintended_issues']
    for group in ('input_sha256','artifact_sha256'):
        for n,h in head[group].items():assert digest(ROOT/n)==h,('Stale head',n)
    params=json.loads((OUT/'head-parameters.json').read_text())
    x,z=params['encoder_center_x'],params['encoder_center_z']
    excluded={'head-flowing-unsplit-development','REF-ESC-connector-corridor',
              'REF-new-power-board-reserve-NOT-ROUTED',
              'horizontal-encoder-thumbwheel-development','REF-Bourns-PEC11H-drawing-envelope'}
    shapes={entry['name']:cq.importers.importStep(str(OUT/(entry['name']+'.step'))).val()
            for entry in head['parts'] if entry['name'] not in excluded}
    wheel=cq.importers.importStep(str(OUT/'horizontal-encoder-thumbwheel-development.step')).val()
    b=wheel.BoundingBox()
    assert 7.9<b.ylen<8.1 and 29.8<b.xlen<30.2 and 29.8<b.zlen<30.2
    bezel=shapes['display-front-bezel-development'].BoundingBox()
    gap=bezel.xmin-b.xmax
    assert gap>=5,('Wheel too close to bezel',gap)
    issues=[];checks=0;maxima={}
    for angle in range(0,360,15):
        spun=wheel.rotate((x,0,z),(x,1,z),angle)
        for press in (0,.4,.8,1.5):
            sample=spun.translate((0,-press,0))
            for n,fixed in shapes.items():
                v=overlap(sample,fixed);checks+=1;maxima[n]=max(maxima.get(n,0),v)
                if v>1e-4:issues.append({'angle_deg':angle,'press_mm':press,'fixed':n,'overlap_mm3':v})
    report={'result':'PASS' if not issues else 'FAIL','timestamp_utc':datetime.now(timezone.utc).isoformat(),
       'physical_qualification':False,'shaft_axis_xyz':[0,1,0],
       'wheel_rotation_plane':'XZ, parallel to LCD face',
       'wheel_center_xz_mm':[x,z],'bezel_to_rim_gap_mm':gap,
       'rotation_samples':24,'press_samples_mm':[0,.4,.8,1.5],
       'pair_checks':checks,'issues':issues,'maximum_overlap_by_fixed_part_mm3':maxima,
       'input_sha256':{str(p.relative_to(ROOT)):digest(p) for p in [Path(__file__),OUT/'head-validation.json',OUT/'head-parameters.json']},
       'geometry_sha256':{str((OUT/(n+'.step')).relative_to(ROOT)):digest(OUT/(n+'.step')) for n in [*shapes,'horizontal-encoder-thumbwheel-development']},
       'limits':['Nominal sampled rigid geometry; no tolerance-extreme or physical fit proof.',
                 'Encoder coupling excluded because the shaft rotates and presses with the wheel; case/nut clearance is checked separately by the head report.',
                 'Actual PEC11H press travel is nominal0.5+/-0.3mm;1.5mm is a conservative mechanical sweep, not allowed forced travel.',
                 'Verify D-bore grip, switch feel, clockwise/upward gesture, desk stability and screen reach on the fit pieces.',
                 'Complete connected harness and tool approaches are not included.']}
    (OUT/'encoder-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report['result'],checks,'wheel/press pairs;',round(gap,3),'mm bezel gap;',len(issues),'issues',flush=True)
    if issues:raise SystemExit(1)

if __name__=='__main__':main()
