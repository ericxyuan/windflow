"""Sample actual Rev C mechanism and unplugged service paths against fixed parts."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,math
import cadquery as cq

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'rev_c'
P=json.loads((OUT/'head-parameters.json').read_text())
REPORT=json.loads((OUT/'head-validation.json').read_text())
assert json.loads((OUT/'build-state.json').read_text())['status']=='PASS','Head build must finish successfully'
for name,digest in REPORT['input_sha256'].items():
    assert hashlib.sha256((ROOT.parent/name).read_bytes()).hexdigest()==digest,('Stale head input',name)
for name,digest in REPORT['artifact_sha256'].items():
    assert hashlib.sha256((ROOT.parent/name).read_bytes()).hexdigest()==digest,('Stale head artifact',name)
assert not REPORT['unintended_issues'],'Resolve nominal intersections first'
SHAPES={}
def get(n):
    if n not in SHAPES:SHAPES[n]=cq.importers.importStep(str(OUT/(n+'.step'))).val()
    return SHAPES[n]
def overlap(a,b):
    aa,bb=a.BoundingBox(),b.BoundingBox()
    if any(getattr(aa,k+'max')<=getattr(bb,k+'min')+1e-6 or getattr(bb,k+'max')<=getattr(aa,k+'min')+1e-6 for k in 'xyz'):return 0.
    return max(0.,a.intersect(b).Volume())
hy=P['panel_hinge_y'];h=P['outlet_height'];l=P['panel_length']
maxa=math.asin(h*(1-P['minimum_gross_outlet_ratio'])/(2*l))
def moving(f):
    a=maxa*f;s=24*math.sin(a);lo,hi=0,math.pi/3
    for _ in range(52):
        phi=(lo+hi)/2
        v=-35+10*math.sin(phi)+math.sqrt(35**2-(10*(math.cos(phi)-1))**2)
        if v<s:lo=phi
        else:hi=phi
    phi=(lo+hi)/2;ey=hy-35+10*math.sin(phi);ez=-10+10*math.cos(phi)
    rod_a=math.atan2(-ez,hy+s-ey)
    result={}
    for tag,sgn in (('upper',1),('lower',-1)):
        for typ in ('panel','crank'):
            n='REF-mechanism-'+tag+'_'+typ+'-open'
            result[n]=get(n).rotate((0,hy,sgn*h/2),(1,hy,sgn*h/2),-sgn*math.degrees(a))
    result['REF-mechanism-yoke-open']=get('REF-mechanism-yoke-open').translate((0,s,0))
    result['REF-mechanism-rod-open']=get('REF-mechanism-rod-open').rotate((0,hy-35,0),(1,hy-35,0),math.degrees(rod_a)).translate((0,ey-(hy-35),ez))
    result['REF-mechanism-horn-open']=get('REF-mechanism-horn-open').rotate((0,hy-35,-10),(1,hy-35,-10),-math.degrees(phi))
    return result

fixed=['head-left-integral-outlet','head-right-integral-outlet','flowing-base-open-bottom',
       'curved-linkage-fairing-development','rigid-motor-carrier-PCD16',
       'seven-vane-straightener-development','fixed-front-finger-guard-development',
       'magnetic-front-cleaning-grille-development','head-magnet-retaining-ring-development',
       'servo-slotted-bracket-development','REF-FS90-FB-family-envelope-UNVERIFIED']
maximum={};issues=[];count=0
for i in range(61):
    for n,s in moving(i/60).items():
        for fn in fixed:
            # Supplier horn spline intentionally seats on the approximate servo.
            # This specific pair is not a free-volume clearance qualification.
            if n.endswith('horn-open') and fn=='REF-FS90-FB-family-envelope-UNVERIFIED':continue
            v=overlap(s,get(fn));count+=1;k=n+' / '+fn
            maximum[k]=max(maximum.get(k,0),v)
            if v>1e-4:issues.append({'sample':i,'panel_deg':math.degrees(maxa*i/60),'moving':n,'fixed':fn,'overlap_mm3':v})
    if i%10==0:print('SWEEP',i,'/60',flush=True)

# The screen and cradle remain bolted together; the bezel, lens and tray are
# removed first. Wires are unplugged, so these checks do not pretend to validate
# a flexible connected harness or a screwdriver's approach.
service=[];service_count=0
screen=cq.Compound.makeCompound([get('REF-Adafruit-4311-IPS-vendor'),get('display-removable-cradle-development')])
service_fixed=['flowing-base-open-bottom','head-left-integral-outlet','head-right-integral-outlet',
               'horizontal-encoder-mount-development','horizontal-encoder-thumbwheel-development',
               'encoder-daughterboard-P1-FR4','REF-Bourns-PEC11H-drawing-envelope',
               'Raspberry-Pi-Pico-SC0915-vendor',
               'Sensirion-SDP810-125Pa-vendor','REF-A50S-V2p3c-envelope-UNVERIFIED']
for sample,(yshift,zshift) in enumerate([(-i*.5,0) for i in range(9)]+[(-4,-i) for i in range(1,71)]):
    s=screen.translate((0,yshift,zshift))
    for n in service_fixed:
        v=overlap(s,get(n));service_count+=1
        if v>1e-4:service.append({'part':'screen+cradle','yshift':yshift,'zshift':zshift,'fixed':n,'overlap_mm3':v})
    if sample%20==0:print('SCREEN SERVICE',sample,'/78',flush=True)
report={'result':'PASS' if not issues and not service else 'FAIL','physical_qualification':False,
        'timestamp_utc':datetime.now(timezone.utc).isoformat(),'panel_samples':61,
        'mechanism_pair_checks':count,'maximum_overlap_by_pair_mm3':maximum,
        'mechanism_issues':issues,'screen_service_pair_checks':service_count,
        'screen_service_issues':service,'input_sha256':{
            str(p.relative_to(ROOT.parent)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [Path(__file__),OUT/'head-parameters.json',OUT/'head-validation.json']},
        'screen_service_rearward_clearance_mm':4,
        'geometry_sha256':{str((OUT/(n+'.step')).relative_to(ROOT.parent)):
                            hashlib.sha256((OUT/(n+'.step')).read_bytes()).hexdigest() for n in SHAPES},
        'limits':['Sampled nominal rigid geometry, not continuous or tolerance-extreme proof.',
                  'No wires, pressure hoses, flexible deformation or tool sweeps in this report.',
                  'Approximate FS90-FB family datum and exact A50S case require measured verification.',
                  'Original mechanism hardware sleeve/fastener study remains separately documented.']}
(OUT/'motion-validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(report['result'],count,'mechanism pairs;',service_count,'screen removal pairs;',len(issues)+len(service),'issues')
if issues or service:raise SystemExit(1)
