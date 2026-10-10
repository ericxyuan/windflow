"""Source-matched mesh, removal, adjustment and driver checks of the cartridge.

Existing unchanged main-stage motion checks are retained. This independently
checks the newly changed geometry against the same motion inputs, plus service
paths. It is sampled nominal CAD, not live switch, wire or motor qualification.
"""
from pathlib import Path
from datetime import datetime, timezone
import sys, hashlib, json, math, time
import cadquery as cq

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from cad import rev_d_interlock_cartridge as c
from cad.rev_d_motion import overlap, bounds, _bounds_cache
from cad.rev_d_meshes import check_mesh
from cad.rev_d_front_service import SCREEN, REMOVED, positions


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def boost_poses(shapes,p):
    hy,h,l=p['panel_hinge_y_mm'],p['outlet_height_mm'],p['panel_length_mm']
    maximum=math.asin(h*(1-p['minimum_gross_outlet_ratio'])/(2*l))
    for i in range(61):
        a=maximum*i/60;s=24*math.sin(a);lo,hi=0,math.pi/3
        for _ in range(52):
            phi=(lo+hi)/2
            v=-35+10*math.sin(phi)+math.sqrt(35**2-(10*(math.cos(phi)-1))**2)
            if v<s: lo=phi
            else: hi=phi
        phi=(lo+hi)/2;ey=hy-35+10*math.sin(phi);ez=-10+10*math.cos(phi)
        rod_a=math.atan2(-ez,hy+s-ey);moving={}
        for tag,sgn in (('upper',1),('lower',-1)):
            for kind in ('panel','crank'):
                n=f'REF-mechanism-{tag}_{kind}-open'
                moving[n]=shapes[n].rotate((0,hy,sgn*h/2),(1,hy,sgn*h/2),-sgn*math.degrees(a))
        n='REF-mechanism-yoke-open';moving[n]=shapes[n].translate((0,s,0))
        n='REF-mechanism-rod-open'
        moving[n]=shapes[n].rotate((0,hy-35,0),(1,hy-35,0),math.degrees(rod_a)).translate((0,ey-(hy-35),ez))
        n='REF-mechanism-horn-open';moving[n]=shapes[n].rotate((0,hy-35,-10),(1,hy-35,-10),-math.degrees(phi))
        yield i,moving


def lever(mount_y,contact_y):
    plane=cq.Plane(origin=(-64.2,0,0),xDir=(0,1,0),normal=(1,0,0))
    return cq.Workplane(plane).polyline([(mount_y+5.5,13.2),(contact_y,25.4),
        (contact_y-.3,25.4),(mount_y+5.2,13.2)]).close().extrude(3.).val()


def main():
    _bounds_cache.clear();report_path=c.OUT/'cartridge-validation.json'
    report=json.loads(report_path.read_text())
    assert report['result']=='PASS' and not report['issues']
    for name,sha in report['input_sha256'].items(): assert digest(ROOT/name)==sha,('Stale cartridge',name)
    shapes,p=c.load_stage();candidate={};meshes=[]
    for item in report['parts']:
        path=c.OUT/(item['name']+'.step')
        assert digest(path)==item['sha256'],('Changed cartridge STEP',item['name'])
        candidate[item['name']]=cq.importers.importStep(str(path)).val()
        if item['printed']:
            mesh=check_mesh(path.with_suffix('.stl'),1)
            assert mesh['watertight'],item['name']
            meshes.append({'name':item['name'],'mesh':mesh,'sha256':digest(path.with_suffix('.stl'))})
            print('MESH PASS',item['name'],mesh['triangles'],flush=True)
    assert len(meshes)==6
    assembly={**shapes,**candidate};issues=[];counts={};maxima={}
    envelopes=json.loads((c.BASE/'motion-validation.json').read_text())['sampled_motion_envelopes_xyz_mm']
    clipped={}
    def check(kind,n,s,fn,fs,pose):
        if fn==c.HEAD and kind!='wheel':
            key=(kind,n,fn)
            if key not in clipped:
                if kind=='boost': a=envelopes[n]
                else:
                    b=bounds(assembly[n] if n in assembly else s)
                    a=[b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax]
                    if kind in ('grille_withdrawal','cartridge_withdrawal','screen_service'):
                        a[3]+={'grille_withdrawal':20.,'cartridge_withdrawal':70.,'screen_service':50.}[kind]
                    if kind=='switch_adjustment':
                        # Rigid switch parts move +/-2 mm. Wire endpoints stay
                        # in the same channel; this conservative box encloses
                        # the 14..18 mm bends and the unchanged exit tails.
                        a=[q+(-2.2 if j%2==0 else 2.2) for j,q in enumerate(a)]
                clip=c.box(a[1]-a[0]+.2,a[3]-a[2]+.2,a[5]-a[4]+.2,
                           (a[1]+a[0])/2,(a[3]+a[2])/2,(a[5]+a[4])/2)
                part=fs.intersect(clip)
                assert part.isValid(),('Invalid spatial subset',key)
                clipped[key]=part if part.Volume()>1e-8 else None
            fs=clipped[key]
        volume=0. if fs is None else overlap(s,fs)
        counts[kind]=counts.get(kind,0)+1;maxima[kind]=max(maxima.get(kind,0.),volume)
        if volume>1e-4: issues.append({'kind':kind,'moving':n,'fixed':fn,'pose':pose,'overlap_mm3':volume})
    for i,moving in boost_poses(shapes,p):
        for n,s in moving.items():
            for fn,fs in candidate.items(): check('boost',n,s,fn,fs,{'sample':i})
        if i%10==0: print('CARTRIDGE BOOST',i,'/60',flush=True)
    wheel='horizontal-encoder-thumbwheel-development';x,z=p['encoder_center_x_mm'],p['encoder_center_z_mm']
    for angle in range(0,360,15):
        spun=shapes[wheel].rotate((x,0,z),(x,1,z),angle)
        for press in (0.,.4,.8,1.5):
            s=spun.translate((0,-press,0))
            for fn,fs in candidate.items(): check('wheel',wheel,s,fn,fs,{'angle':angle,'press_mm':press})
    for i,s,pose in positions(shapes[SCREEN]):
        for fn,fs in candidate.items():
            if fn not in REMOVED: check('screen_service',SCREEN,s,fn,fs,pose)
    print('CONTROL PATHS CHECKED',flush=True)
    grille_names={n for n in assembly if n=='magnetic-front-cleaning-grille-development' or
                  n=='grille-magnet-retaining-ring-development' or n.startswith('REF-grille-D42-magnet-')}
    assert len(grille_names)==6,grille_names
    follower='REF-D2F-01L-lever-closed-envelope'
    for distance in range(21):
        fixed={n:s for n,s in assembly.items() if n not in grille_names and n!=follower}
        fixed[follower]=lever(253.3,259.85+min(distance,3.45))
        for n in grille_names:
            s=assembly[n].translate((0,distance,0))
            for fn,fs in fixed.items(): check('grille_withdrawal',n,s,fn,fs,{'distance_mm':distance})
    # Routine grille removal retains the seat and the permanent guard. For
    # cartridge replacement remove the fixed seat/keeper/magnets separately,
    # unplug J12 through bottom access and then remove the two front screws.
    seat_names={n for n in assembly if n in ('P2-fixed-magnet-seat-frame','head-magnet-retaining-ring-development') or
                n.startswith('REF-head-D42-magnet-')}
    assert len(seat_names)==6,seat_names
    front_hardware={n for n in candidate if n.startswith('REF-cartridge-') and 'ruthex' not in n}
    module={n:s for n,s in candidate.items() if n not in shapes and n not in front_hardware and 'ruthex' not in n}
    fixed={n:s for n,s in assembly.items() if n not in module and n not in grille_names|seat_names|front_hardware}
    for distance in range(71):
        for n,s in module.items():
            moved=s.translate((0,distance,0))
            for fn,fs in fixed.items(): check('cartridge_withdrawal',n,moved,fn,fs,{'distance_mm':distance})
        if distance%10==0: print('CARTRIDGE SERVICE',distance,'/70',flush=True)
    # Slide with grille removed. The lever is free, not forced through an
    # unverified elastic travel by the drawing's operating-position tolerance.
    adjusted={n for n in module if n.startswith('REF-D2F') or n=='interlock-sliding-bracket-development' or n.startswith('REF-switch-')}
    wire_names={n for n in module if '5853-insulated-route' in n}
    fixed={n:s for n,s in assembly.items() if n not in adjusted|wire_names|grille_names}
    print('SERVICE PATHS CHECKED',json.dumps(counts),'issues',len(issues),flush=True)
    for issue in issues[:12]: print('PATH COLLISION',issue,flush=True)
    bend_metrics=[]
    for i in range(9):
        dy=-2.+i*.5;moving={n:module[n].translate((0,dy,0)) for n in adjusted}
        moving[follower]=lever(253.3+dy,263.3+dy)
        for tag,z,ex in (('COM',13.32,-60.85),('NO',18.4,-59.55)):
            wire,metric=c.wire_route(z,ex,adjust_y=dy);moving['REF-'+tag+'-5853-insulated-route']=wire
            bend_metrics.append({'adjust_y_mm':dy,'tag':tag,**metric})
        for n,s in moving.items():
            for fn,fs in fixed.items(): check('switch_adjustment',n,s,fn,fs,{'adjust_y_mm':dy})
    # Tool shanks are declared conservative envelopes. Engage only their own
    # screw/insert; no main-wall or other-part overlap is permitted.
    tool_records=[]
    fixed={n:s for n,s in assembly.items() if n not in grille_names|seat_names}
    for i,(x,z) in enumerate(c.FRONT_AXES):
        tool=c.cy(1.5,265.7,50.,x,z)
        own='REF-cartridge-'+str(i)+'-ISO4762-M2x8'
        for fn,fs in fixed.items():
            if fn!=own: check('front_driver','3mm-driver-shank-'+str(i),tool,fn,fs,{'axis':[x,z]})
        # Insert installation before the cartridge and all its hardware.
        tip=c.cy(2.5,259.5,40.,x,z)
        for fn,fs in fixed.items():
            if fn not in module and fn not in front_hardware and not fn.startswith('REF-cartridge-'):
                check('insert_tool','5mm-insertion-tip-shank-'+str(i),tip,fn,fs,{'axis':[x,z]})
        tool_records.append({'axis_xz_mm':[x,z],'driver_shank_diameter_mm':3.,'insert_tool_diameter_mm':5.})
    # With the unplugged cartridge fully removed, internal screws must have
    # a straight X approach. Its outer enclosure is absent in this service step.
    for tag,stack in report['front_fastener_stacks'].items():
        if stack['axis']!='X': continue
        own=[n for n in module if n.startswith('REF-'+tag+'-ISO4762-')];assert len(own)==1
        start=stack['under_head_x_mm']-36.9 if stack['direction']>0 else stack['under_head_x_mm']+1.9
        tool=c.cx(1.5,start,35.,stack['y_mm'],stack['z_mm'])
        for fn,fs in module.items():
            if fn!=own[0]: check('removed_module_driver',tag,tool,fn,fs,{'module_removed':True})
    coupon=assembly[c.HEAD].intersect(c.box(20.,15.,13.,-60.,257.8,38.)).clean()
    assert coupon.isValid() and len(coupon.Solids())==1,'Insert-seat coupon is disconnected'
    step=c.OUT/'front-insert-seat-fit-coupon.step';cq.exporters.export(coupon,str(step))
    cq.exporters.export(coupon,str(step.with_suffix('.stl')),tolerance=.03,angularTolerance=.08)
    coupon_mesh=check_mesh(step.with_suffix('.stl'),1);assert coupon_mesh['watertight']
    result={'result':'PASS' if not issues else 'FAIL','generated_utc':datetime.now(timezone.utc).isoformat(),
            'physical_qualification':False,'counts':counts,'maxima_mm3':maxima,'issues':issues,
            'meshes':meshes,'tool_envelopes':tool_records,'adjustment_wire_metrics':bend_metrics,
            'fit_coupons':[{'name':step.stem,'step_sha256':digest(step),
                            'stl_sha256':digest(step.with_suffix('.stl')),'mesh':coupon_mesh}],
            'head_spatial_subset_policy':'Each fixed-head clip contains the full sampled moving-body envelope plus 0.1 mm. Tool labels are unique per approach. All check counts include empty spatial subsets.',
            'service_protocol':'Power off/unplug; remove cleaning grille; remove fixed magnetic seat/keeper; unplug J12 through bottom; remove two front M2x8 screws; withdraw entire cartridge +Y70mm. Fixed finger guard remains.',
            'input_sha256':{str(q.relative_to(ROOT)):digest(q) for q in (Path(__file__),Path(c.__file__),report_path,
                c.BASE/'motion-validation.json',ROOT/'cad/rev_d_motion.py',ROOT/'cad/rev_d_front_service.py',ROOT/'cad/rev_d_meshes.py')},
            'limits':['Independent candidate; main complete stage/export and Onshape adoption still required.',
                      'Sampled nominal drawing bodies, not elastic switch actuation or tolerance qualification.',
                      'Whole main loom, plugged connectors and realistic hand dexterity are not qualified by tool cylinders.',
                      'Thermal insert pullout and calibrated switch post-trip/overtravel require physical tests.']}
    (c.OUT/'service-motion-validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result['result'],sum(counts.values()),'checks;',len(issues),'collisions',flush=True)
    for issue in issues[:35]: print('COLLISION',issue,flush=True)
    if issues: raise SystemExit(1)


if __name__=='__main__': main()
