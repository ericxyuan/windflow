"""Independent rigid-motion checks of the 150 mm development assembly.

These are sampled nominal checks, not a rotor spin or tolerance qualification.
The rotor swept annulus is a conservative continuous clearance envelope.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, math
import cadquery as cq

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'cad/rev_d'

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def overlap(a,b):
    aa,bb=a.BoundingBox(),b.BoundingBox()
    if any(getattr(aa,k+'max')<=getattr(bb,k+'min')+1e-6 or
           getattr(bb,k+'max')<=getattr(aa,k+'min')+1e-6 for k in 'xyz'): return 0.
    return max(0.,a.intersect(b).Volume())

def run():
    report=json.loads((OUT/'stage-validation.json').read_text())
    assert report['result']=='PASS', 'Resolve nominal collisions first'
    assert json.loads((OUT/'stage-build-state.json').read_text())['status']=='PASS'
    for n,h in report['input_sha256'].items(): assert digest(ROOT/n)==h, ('Stale stage input',n)
    excluded=set(report['excluded_alternative_and_reserves'])
    shapes={}
    for r in report['parts']:
        n=r['name']
        assert digest(OUT/(n+'.step'))==r['sha256'], ('Stale part',n)
        if n not in excluded: shapes[n]=cq.importers.importStep(str(OUT/(n+'.step'))).val()
    p=json.loads((OUT/'head-parameters.json').read_text())
    height_box=cq.Solid.makeBox(1000,1000,p['target_product_height_mm'],
                               cq.Vector(-500,-500,p['foot_bottom_z_mm']))
    outside_height={}
    for n,s in shapes.items():
        b=s.BoundingBox()
        if b.zmin<p['foot_bottom_z_mm']-1e-6 or b.zmax>p['foot_bottom_z_mm']+p['target_product_height_mm']+1e-6:
            outside_height[n]=max(0.,s.cut(height_box).Volume())
            assert outside_height[n]<1e-4, ('Outside intended complete-height box',n,outside_height[n])
    hy,h,l=p['panel_hinge_y_mm'],p['outlet_height_mm'],p['panel_length_mm']
    maxa=math.asin(h*(1-p['minimum_gross_outlet_ratio'])/(2*l))
    assert math.degrees(maxa)<=p['absolute_closure_limit_deg']
    moving_names={f'REF-mechanism-{tag}_{kind}-open' for tag in ('upper','lower') for kind in ('panel','crank')}
    moving_names.update('REF-mechanism-'+n+'-open' for n in ('yoke','rod','horn'))
    wheel_name='horizontal-encoder-thumbwheel-development'
    static={n:s for n,s in shapes.items() if n not in moving_names and n!=wheel_name}
    issues=[];counts={'mechanism_fixed':0,'mechanism_moving':0,'wheel_press':0,'screen_service':0,'rotor_swept_envelope':0}
    maxima={};coupling=[]
    def check(kind,label,a,n,b,pose):
        v=overlap(a,b);counts[kind]+=1
        key=label+' / '+n
        maxima[key]=max(maxima.get(key,0.),v)
        if v>1e-4: issues.append({'kind':kind,'moving':label,'fixed':n,'pose':pose,'overlap_mm3':v})
    for i in range(61):
        a=maxa*i/60;s=24*math.sin(a);lo,hi=0,math.pi/3
        for _ in range(52):
            phi=(lo+hi)/2
            v=-35+10*math.sin(phi)+math.sqrt(35**2-(10*(math.cos(phi)-1))**2)
            if v<s: lo=phi
            else: hi=phi
        phi=(lo+hi)/2;ey=hy-35+10*math.sin(phi);ez=-10+10*math.cos(phi)
        rod_a=math.atan2(-ez,hy+s-ey)
        moving={}
        for tag,sgn in (('upper',1),('lower',-1)):
            for kind in ('panel','crank'):
                n=f'REF-mechanism-{tag}_{kind}-open'
                moving[n]=shapes[n].rotate((0,hy,sgn*h/2),(1,hy,sgn*h/2),-sgn*math.degrees(a))
        n='REF-mechanism-yoke-open';moving[n]=shapes[n].translate((0,s,0))
        n='REF-mechanism-rod-open';moving[n]=shapes[n].rotate((0,hy-35,0),(1,hy-35,0),math.degrees(rod_a)).translate((0,ey-(hy-35),ez))
        n='REF-mechanism-horn-open';moving[n]=shapes[n].rotate((0,hy-35,-10),(1,hy-35,-10),-math.degrees(phi))
        for n,sample in moving.items():
            for fn,fixed in static.items():
                if n.endswith('horn-open') and fn=='REF-FS90-FB-family-envelope-UNVERIFIED':
                    # Intentional supplier spline interface is not a free-volume
                    # qualification, and the family envelope is unmeasured.
                    coupling.append({'sample':i,'overlap_mm3':overlap(sample,fixed)})
                    continue
                check('mechanism_fixed',n,sample,fn,fixed,{'sample':i,'panel_deg':math.degrees(a)})
        items=list(moving.items())
        for j,(n,sample) in enumerate(items):
            for fn,fixed in items[j+1:]:check('mechanism_moving',n,sample,fn,fixed,{'sample':i})
        if i%10==0: print('BOOST SWEEP',i,'/60',flush=True)
    x,z=p['encoder_center_x_mm'],p['encoder_center_z_mm']
    b=shapes[wheel_name].BoundingBox();bezel=shapes['display-front-bezel-development'].BoundingBox()
    gap=bezel.xmin-b.xmax;assert gap>=5, ('Control finger gap',gap)
    wheel_fixed={n:s for n,s in shapes.items() if n not in (wheel_name,'REF-Bourns-PEC11H-drawing-envelope')}
    for angle in range(0,360,15):
        spun=shapes[wheel_name].rotate((x,0,z),(x,1,z),angle)
        for press in (0,.4,.8,1.5):
            sample=spun.translate((0,-press,0))
            for n,fixed in wheel_fixed.items():check('wheel_press',wheel_name,sample,n,fixed,{'angle_deg':angle,'press_mm':press})
    print('WHEEL CHECKED',counts['wheel_press'],flush=True)
    # Unplug and remove bezel/lens and bottom tray before sliding the screen
    # rearward 4 mm and down. No connected cable or screwdriver claim.
    screen_names={'REF-Adafruit-4311-IPS-vendor','display-removable-cradle-development'}
    service_removed=screen_names|{'REF-clear-display-lens-45x34p4','display-front-bezel-development',
                                'P2-bottom-electronics-service-tray','P2-downward-ambient-diffuser'}
    screen=cq.Compound.makeCompound([shapes[n] for n in screen_names])
    for i,(ys,zs) in enumerate([(-i*.5,0) for i in range(9)]+[(-4,-i) for i in range(1,71)]):
        sample=screen.translate((0,ys,zs))
        for n,fixed in shapes.items():
            if n not in service_removed:check('screen_service','screen+cradle',sample,n,fixed,{'sample':i,'yshift_mm':ys,'zshift_mm':zs})
    print('SCREEN SERVICE CHECKED',counts['screen_service'],flush=True)
    seat=p['motor_prop_seat_y_assumed_mm']
    rotor_report=json.loads((OUT/'rotor-validation.json').read_text())
    hub_length=json.loads((OUT/'rotor-parameters.json').read_text())['hub_length_mm']
    swept=cq.Solid.makeCylinder(p['rotor_diameter_mm']/2,hub_length,cq.Vector(0,seat-hub_length,0),cq.Vector(0,1,0)).cut(
        cq.Solid.makeCylinder(2.6,hub_length+.2,cq.Vector(0,seat-hub_length-.1,0),cq.Vector(0,1,0)))
    rotor_name='P2-150mm-rotor-installed-TEST-ONLY'
    assert shapes[rotor_name].cut(swept).Volume()<1e-5, 'Rotor must fit its continuous swept envelope'
    for n,fixed in shapes.items():
        if n!=rotor_name:check('rotor_swept_envelope',rotor_name,swept,n,fixed,{'continuous_annulus':True})
    result={'result':'PASS' if not issues else 'FAIL','physical_qualification':False,
            'generated_utc':datetime.now(timezone.utc).isoformat(),'counts':counts,'issues':issues,
            'panel_samples':61,'maximum_panel_deg':math.degrees(maxa),'servo_horn_deg':math.degrees(phi),
            'minimum_gross_outlet_ratio':p['minimum_gross_outlet_ratio'],'bezel_to_wheel_gap_mm':gap,
            'exact_height_envelope_mm':p['target_product_height_mm'],'outside_height_volume_mm3':outside_height,
            'wheel_rotation_plane':'XZ, parallel to screen','rotor_nominal_radial_gap_mm':(p['throat_diameter_mm']-p['rotor_diameter_mm'])/2,
            'maxima_mm3':maxima,'intentional_supplier_horn_interface':coupling,
            'input_sha256':{str(q.relative_to(ROOT)):digest(q) for q in [Path(__file__),OUT/'stage-validation.json',OUT/'head-parameters.json',OUT/'rotor-validation.json',OUT/'rotor-parameters.json']},
            'geometry_sha256':{str((OUT/(n+'.step')).relative_to(ROOT)):digest(OUT/(n+'.step')) for n in shapes},
            'limits':['61 sampled boost poses; nominal geometry, no continuous or tolerance-extreme guarantee for the linkage.',
                      'Servo spline/body pair is an intended supplier interface, not validated clearance.',
                      'Encoder body excluded from wheel sweep because shaft couples and translates; nominal case and nut included in stage check.',
                      '1.5 mm press sweep is conservative geometry, not permission to force a 0.5 +/- 0.3 mm encoder switch.',
                      'No wires, pressure hoses, screw/tool sweeps, elastic deformation or physical spin test.',
                      'Rotor envelope proves nominal spatial clearance only; thermal, centrifugal and FDM errors remain unqualified.']}
    (OUT/'motion-validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result['result'],counts,'issues',len(issues),flush=True)
    for issue in issues[:30]:print('COLLISION',issue,flush=True)
    if issues:raise SystemExit(1)

if __name__=='__main__':run()
