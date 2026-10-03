"""Sample explicit assembly paths against the generated parent housing.

This is a rigid nominal insertion check, not a claim about tool/hand clearance.
Run after prototype and head generation. All positions are head-local millimetres.
"""
from pathlib import Path
import cadquery as cq
import json, hashlib, math, os, sys
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parent
loaded={}
def read(name,path,shift=(0,0,0)):
    loaded[str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
    s=cq.importers.importStep(str(path)).val().translate(shift)
    assert s.isValid(), name
    return s
def overlap(a,b):
    aa,bb=a.BoundingBox(),b.BoundingBox()
    if any(getattr(aa,k+'max')<=getattr(bb,k+'min')+1e-6 or getattr(bb,k+'max')<=getattr(aa,k+'min')+1e-6 for k in 'xyz'):return 0.
    return max(0.,a.intersect(b).Volume())
def moving(n):return read(n,ROOT/'prototypes'/('installed-'+n+'-open.step'),(0,90,0))
def fixed(n):return read(n,ROOT/'prototypes'/('installed-'+n+'.step'),(0,90,0))

assembled={'right_head':read('right_head',ROOT/'rev_b/head-right-integral-outlet.step')}
steps=[];issues=[]
def insert(name,shape,waypoints):
    record={'part':name,'waypoints_translation_mm':waypoints,'samples':0,'max_overlap_mm3':0.,'collisions':[]}
    for start,end in zip(waypoints,waypoints[1:]):
        length=math.dist(start,end); count=max(1,math.ceil(length))
        for i in range(count+1):
            offset=tuple(a+(b-a)*i/count for a,b in zip(start,end))
            s=shape.translate(offset);record['samples']+=1
            for other,t in assembled.items():
                v=overlap(s,t);record['max_overlap_mm3']=max(record['max_overlap_mm3'],v)
                if v>.01:
                    failure={'against':other,'translation_mm':offset,'overlap_mm3':v}
                    record['collisions'].append(failure)
                    issues.append({'part':name,**failure})
                    # First obstruction invalidates this path; stop wasting work
                    # but record later intended final positions for diagnosis.
                    steps.append(record); assembled[name]=shape
                    print('BLOCKED '+name+' / '+other,flush=True)
                    return
    steps.append(record);assembled[name]=shape
    print('INSERTION CLEAR '+name,flush=True)

insert('yoke',moving('yoke'),[(0,0,180),(0,0,0)])
for tag in ('upper','lower'):
    # Bring the spacer into the open outboard volume first, then slide axially
    # through the yoke notch; it cannot pass through the fixed bearing from right.
    insert(tag+'_retaining_spacer',fixed(tag+'_retaining_spacer'),[(-15.2,100,0),(-15.2,0,0),(0,0,0)])
    # The cover supports obstruct the front approach. The cranks enter
    # vertically at their hinge station before their matching panels are fitted.
    insert(tag+'_crank',moving(tag+'_crank'),[(0,0,100 if tag=='upper' else -100),(0,0,0)])
    insert(tag+'_panel',moving(tag+'_panel'),[(-140,0,0),(0,0,0)])
left=read('left_head',ROOT/'rev_b/head-left-integral-outlet.step')
insert('left_head',left,[(-140,0,0),(0,0,0)])
for tag in ('upper','lower'):
    insert(tag+'_shaft',fixed(tag+'_shaft'),[(-160,0,0),(0,0,0)])
    insert(tag+'_left_collar',fixed(tag+'_left_collar'),[(-30,0,0),(0,0,0)])
    insert(tag+'_right_collar',fixed(tag+'_right_collar'),[(30,0,0),(0,0,0)])

report={'completed_utc':datetime.now(timezone.utc).isoformat(),'status':'passed sampled paths' if not issues else 'blocked insertion paths',
        'coordinate_system':'head local, airflow +Y, Z centre 0; product height from parameters.json',
        'maximum_translation_step_mm':1,'steps':steps,'issues':issues,
        'input_sha256':loaded,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'limitations':['Nominal rigid solids at sampled points, not a continuous collision proof or tolerance study.',
        'Servo, rod, pins, clamp hardware, guards, screw tools and wiring are installed later; their insertion remains to check.',
        'No physical assembly, friction or printed-fit test has been performed.']}
(ROOT/'prototypes/insertion-validation.json').write_text(json.dumps(report,indent=2))
print(report['status'],flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(1 if issues else 0)
