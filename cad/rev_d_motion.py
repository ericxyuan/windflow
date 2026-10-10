"""Independent rigid-motion checks of the 150 mm development assembly.

These are sampled nominal checks, not a rotor spin or tolerance qualification.
The rotor swept annulus is a conservative continuous clearance envelope.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, math, os, tempfile
import cadquery as cq
import time
if __package__:
    from .rev_d_front_service import SCREEN, REMOVED, positions
else:
    from rev_d_front_service import SCREEN, REMOVED, positions

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'cad/rev_d'

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

_bounds_cache={}
def bounds(shape):
    # Transforms and Boolean results create new shapes. Keep strong references
    # alongside cached bounds so Python cannot recycle an object's id.
    key=id(shape)
    if key not in _bounds_cache:_bounds_cache[key]=(shape,shape.BoundingBox())
    return _bounds_cache[key][1]

def overlap(a,b):
    aa,bb=bounds(a),bounds(b)
    if any(getattr(aa,k+'max')<=getattr(bb,k+'min')+1e-6 or
           getattr(bb,k+'max')<=getattr(aa,k+'min')+1e-6 for k in 'xyz'): return 0.
    return max(0.,a.intersect(b).Volume())

def run():
    _bounds_cache.clear()
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
    sources=[Path(__file__),Path(__file__).with_name('rev_d_front_service.py'),OUT/'stage-validation.json',OUT/'head-parameters.json',
             OUT/'rotor-validation.json',OUT/'rotor-parameters.json']
    input_hashes={str(q.relative_to(ROOT)):digest(q) for q in sources}
    geometry_hashes={str((OUT/(n+'.step')).relative_to(ROOT)):digest(OUT/(n+'.step')) for n in shapes}
    signature=hashlib.sha256(json.dumps({'source':input_hashes,'geometry':geometry_hashes},sort_keys=True).encode()).hexdigest()
    # Progress is disposable. Keep its frequently replaced file outside the
    # iCloud checkout so a sync-provider lock cannot stop geometry validation.
    workspace_key=hashlib.sha256(str(ROOT).casefold().encode()).hexdigest()[:12]
    local_base=Path(os.environ.get('LOCALAPPDATA') or tempfile.gettempdir())
    cache_path=local_base/'Windflow/cad-check-cache'/workspace_key/'motion-check-progress.json'
    cache_path.parent.mkdir(parents=True,exist_ok=True)
    done={k:set() for k in ('boost','wheel','screen','rotor')}
    reused={k:0 for k in done}
    if cache_path.exists():
        try:cache=json.loads(cache_path.read_text())
        except (OSError,ValueError):cache={}
        if cache.get('signature')==signature:
            done={k:set(cache['done'][k]) for k in done}
            reused={k:len(v) for k,v in done.items()}
            issues=cache['issues'];counts=cache['counts'];maxima=cache['maxima'];coupling=cache['coupling']
            print('RESUME source-matched completed samples',reused,flush=True)
    def checkpoint(kind,index):
        done[kind].add(index)
        cache={'signature':signature,'done':{k:sorted(v) for k,v in done.items()},
               'issues':issues,'counts':counts,'maxima':maxima,'coupling':coupling,
               'updated_utc':datetime.now(timezone.utc).isoformat()}
        temporary=cache_path.with_suffix('.tmp')
        try:
            temporary.write_text(json.dumps(cache,indent=2)+'\n');temporary.replace(cache_path)
        except OSError as error:
            # Never turn an optional checkpoint failure into a geometry pass
            # or stop the checks. The final report still requires all samples.
            print('PROGRESS CACHE UNAVAILABLE; checks continue:',type(error).__name__,flush=True)
    local_fixed={}
    envelopes={}
    def check(kind,label,a,n,b,pose):
        candidate=b
        if kind=='mechanism_fixed' and n.startswith('P2-flowing-head-'):
            key=(label,n)
            if key not in local_fixed:
                limits=envelopes[label]
                clip=cq.Solid.makeBox(limits[1]-limits[0]+.2,limits[3]-limits[2]+.2,
                                     limits[5]-limits[4]+.2,
                                     cq.Vector(limits[0]-.1,limits[2]-.1,limits[4]-.1))
                piece=b.intersect(clip)
                assert piece.isValid(),('Invalid spatial subset',label,n)
                local_fixed[key]=piece if piece.Volume()>1e-8 else None
            candidate=local_fixed[key]
        v=0. if candidate is None else overlap(a,candidate)
        counts[kind]+=1
        key=label+' / '+n
        maxima[key]=max(maxima.get(key,0.),v)
        if v>1e-4: issues.append({'kind':kind,'moving':label,'fixed':n,'pose':pose,'overlap_mm3':v})
    poses=[]
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
        poses.append((i,a,moving))
        for n,sample in moving.items():
            b=sample.BoundingBox()
            bounds=[b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax]
            if n not in envelopes:envelopes[n]=bounds
            else:
                for j in range(6):envelopes[n][j]=(min if j%2==0 else max)(envelopes[n][j],bounds[j])
    # Every sampled moving shape is enclosed by its union AABB. Restricting
    # only the fixed head to that box plus 0.1 mm preserves every intersection
    # in the sampled checks; it avoids repeatedly processing remote surfaces.
    for i,a,moving in poses:
        if i in done['boost']:continue
        started=time.perf_counter()
        print('BOOST CHECK',i,'/60',flush=True)
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
        checkpoint('boost',i)
        print('BOOST COMPLETE',i,'seconds',round(time.perf_counter()-started,2),flush=True)
    x,z=p['encoder_center_x_mm'],p['encoder_center_z_mm']
    b=shapes[wheel_name].BoundingBox();bezel=shapes['display-front-bezel-development'].BoundingBox()
    gap=bezel.xmin-b.xmax;assert gap>=5, ('Control finger gap',gap)
    wheel_fixed={n:s for n,s in shapes.items() if n not in (wheel_name,'REF-Bourns-PEC11H-drawing-envelope')}
    for angle in range(0,360,15):
        spun=shapes[wheel_name].rotate((x,0,z),(x,1,z),angle)
        for j,press in enumerate((0,.4,.8,1.5)):
            index=(angle//15)*4+j
            if index in done['wheel']:continue
            sample=spun.translate((0,-press,0))
            for n,fixed in wheel_fixed.items():check('wheel_press',wheel_name,sample,n,fixed,{'angle_deg':angle,'press_mm':press})
            checkpoint('wheel',index)
            print('WHEEL COMPLETE',index,'/95',flush=True)
    print('WHEEL CHECKED',counts['wheel_press'],flush=True)
    # Unplug through bottom service access, then remove bezel/lens and the
    # two PCB screws. Pull the display alone forward; its cradle stays inside.
    # Keeping tray/diffuser in the collision test is conservative. No wire or
    # screwdriver clearance is claimed by this rigid-body path check.
    for i,sample,pose in positions(shapes[SCREEN]):
        if i in done['screen']:continue
        for n,fixed in shapes.items():
            if n not in REMOVED:check('screen_service','screen module',sample,n,fixed,pose)
        checkpoint('screen',i)
        print('SCREEN SERVICE COMPLETE',i,'/50',flush=True)
    print('SCREEN SERVICE CHECKED',counts['screen_service'],flush=True)
    seat=p['motor_prop_seat_y_assumed_mm']
    rotor_report=json.loads((OUT/'rotor-validation.json').read_text())
    hub_length=json.loads((OUT/'rotor-parameters.json').read_text())['hub_length_mm']
    swept=cq.Solid.makeCylinder(p['rotor_diameter_mm']/2,hub_length,cq.Vector(0,seat-hub_length,0),cq.Vector(0,1,0)).cut(
        cq.Solid.makeCylinder(2.6,hub_length+.2,cq.Vector(0,seat-hub_length-.1,0),cq.Vector(0,1,0)))
    rotor_name='P2-150mm-rotor-installed-TEST-ONLY'
    assert shapes[rotor_name].cut(swept).Volume()<1e-5, 'Rotor must fit its continuous swept envelope'
    for i,(n,fixed) in enumerate(shapes.items()):
        if n==rotor_name or i in done['rotor']:continue
        check('rotor_swept_envelope',rotor_name,swept,n,fixed,{'continuous_annulus':True})
        checkpoint('rotor',i)
    result={'result':'PASS' if not issues else 'FAIL','physical_qualification':False,
            'generated_utc':datetime.now(timezone.utc).isoformat(),'counts':counts,'issues':issues,
            'panel_samples':61,'maximum_panel_deg':math.degrees(maxa),'servo_horn_deg':math.degrees(phi),
            'minimum_gross_outlet_ratio':p['minimum_gross_outlet_ratio'],'bezel_to_wheel_gap_mm':gap,
            'exact_height_envelope_mm':p['target_product_height_mm'],'outside_height_volume_mm3':outside_height,
            'wheel_rotation_plane':'XZ, parallel to screen','rotor_nominal_radial_gap_mm':(p['throat_diameter_mm']-p['rotor_diameter_mm'])/2,
            'screen_service_protocol':'Display alone forward +Y 50 mm after unplugging and removing bezel/lens and two PCB screws; cradle retained.',
            'bounds_cache':'Computed once per immutable shape; strong references prevent identity reuse.',
            'maxima_mm3':maxima,'intentional_supplier_horn_interface':coupling,
            'sampled_motion_envelopes_xyz_mm':envelopes,
            'input_sha256':input_hashes,'geometry_sha256':geometry_hashes,
            'source_matched_resume':{'signature':signature,'reused_samples':reused},
            'progress_cache_policy':'Disposable progress outside the synced checkout; failed cache writes do not skip validation.',
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
