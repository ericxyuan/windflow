"""Check outward removal of the display module with its cradle retained.

The abandoned backward/downward cradle path is recorded in Git at b70a79d.
Unplug the screen loom and remove bezel/lens and the two PCB screws first.
This is a rigid nominal body check; wires and screw/tool access need separate work.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json
import cadquery as cq

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'cad/rev_d'
SCREEN='REF-Adafruit-4311-IPS-vendor'
REMOVED={SCREEN,'REF-clear-display-lens-45x34p4','display-front-bezel-development'}

def positions(screen):
    for index in range(51):
        yield index,screen.translate((0,index,0)),{'sample':index,'yshift_mm':index,'zshift_mm':0}

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    stage=json.loads((OUT/'stage-validation.json').read_text())
    assert stage['result']=='PASS'
    for name,sha in stage['input_sha256'].items():assert digest(ROOT/name)==sha,('Stale stage',name)
    shapes={};geometry={}
    for part in stage['parts']:
        name=part['name']
        path=OUT/(name+'.step')
        assert digest(path)==part['sha256'],('Changed part',name)
        if name not in stage['excluded_alternative_and_reserves']:
            shapes[name]=cq.importers.importStep(str(path)).val()
            geometry[str(path.relative_to(ROOT))]=part['sha256']
    fixed={name:shape for name,shape in shapes.items() if name not in REMOVED}
    fixed_bounds={name:shape.BoundingBox() for name,shape in fixed.items()}
    assert 'display-removable-cradle-development' in fixed
    issues=[];count=0;maximum=0.
    for index,screen,pose in positions(shapes[SCREEN]):
        box=screen.BoundingBox()
        for name,shape in fixed.items():
            other=fixed_bounds[name]
            separated=any(getattr(box,k+'max')<=getattr(other,k+'min')+1e-6 or
                          getattr(other,k+'max')<=getattr(box,k+'min')+1e-6 for k in 'xyz')
            overlap=0. if separated else max(0.,screen.intersect(shape).Volume())
            count+=1;maximum=max(maximum,overlap)
            if overlap>1e-4:issues.append({'fixed':name,'pose':pose,'overlap_mm3':overlap})
        if index%10==0:print('FRONT SCREEN SAMPLE',index,'/50',flush=True)
    end=shapes[SCREEN].translate((0,50,0)).BoundingBox()
    clearance=end.ymin-max(box.ymax for box in fixed_bounds.values())
    assert clearance>2,('Display is not fully withdrawn',clearance)
    result={'result':'PASS' if not issues else 'FAIL','generated_utc':datetime.now(timezone.utc).isoformat(),
            'physical_qualification':False,'protocol':'Unplug; remove bezel/lens and two PCB screws; pull display alone forward +Y 50 mm. Cradle stays installed.',
            'cradle_retained':True,'removed_geometry':sorted(REMOVED-{SCREEN}),
            'samples':51,'pair_checks':count,'maximum_overlap_mm3':maximum,'issues':issues,
            'fully_withdrawn_clearance_mm':clearance,
            'input_sha256':{str(path.relative_to(ROOT)):digest(path) for path in [Path(__file__),OUT/'stage-validation.json']},
            'geometry_sha256':geometry,
            'limits':['Screen loom must be unplugged through the bottom service access first.',
                      'No connected cables, populated-board harness, fasteners or tool cylinders are included.',
                      'Cradle replacement still requires opening the head; routine display replacement does not.',
                      'Nominal sampled rigid removal only, not tolerance extremes or physical service qualification.']}
    (OUT/'screen-front-service-validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result['result'],count,'body checks;',len(issues),'collisions',flush=True)
    if issues:raise SystemExit(1)

if __name__=='__main__':main()
