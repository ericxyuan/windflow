"""Adapt the adjustable Omron grille interlock to the compact Rev D front.

The switch/lever are primary-drawing envelopes, not manufacturer CAD or an
elastic switch simulation. The independent pilot never changes the main stage.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,math
import cadquery as cq
if __package__:
    from .grille_interlock_study import build_geometry,wire_liner,nutx
    from .rev_d_power_access import rounded_yz
else:
    from grille_interlock_study import build_geometry,wire_liner,nutx
    from rev_d_power_access import rounded_yz

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'cad/rev_d'
OUT=BASE/'interlock-study'

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def box(w,d,h,x,y,z):return cq.Workplane('XY').box(w,d,h).val().translate((x,y,z))

def cx(r,x,length,y,z):return cq.Solid.makeCylinder(r,length,cq.Vector(x,y,z),cq.Vector(1,0,0))

def cz(r,z,length,x,y):return cq.Solid.makeCylinder(r,length,cq.Vector(x,y,z),cq.Vector(0,0,1))

def front_shape(w,h,r,y0,y1):
    return rounded_yz(w,h,r,y0,y1,0,0).rotate((0,0,0),(0,0,1),90)

def switch_wire_route(start_z,offset_x,radius=.55):
    # Alpha 5853 OD .039 +/- .004 in: <=1.0922 mm, bend >=10*OD.
    # 14 mm quarter bend plus a gentle lateral separation fits a 1.1 mm
    # envelope. The insulated route begins 0.1 mm beyond the terminal tip;
    # the bare solder bond is not part of this mechanical keepout.
    bend=14.;channel_y=235.;theta0=math.asin(.8/bend)
    def position(theta):
        u=theta/(math.pi/2);ease=u*u*(3-2*u)
        return cq.Vector(-60.2+offset_x*ease,channel_y+bend-bend*math.sin(theta),
                         start_z-bend*(1-math.cos(theta)))
    angles=[theta0+(math.pi/2-theta0)*i/32 for i in range(33)]
    points=[position(theta) for theta in angles]
    u=theta0/(math.pi/2)
    tangent=cq.Vector(offset_x*6*u*(1-u)*2/math.pi,-bend*math.cos(theta0),-bend*math.sin(theta0))
    curve=cq.Edge.makeSpline(points,tangents=(tangent,cq.Vector(0,0,-bend)),
                             parameters=angles,scale=False)
    end=points[-1];line=cq.Edge.makeLine(end,cq.Vector(end.x,end.y,-65))
    path=cq.Wire.assembleEdges([curve,line])
    plane=cq.Plane(origin=curve.startPoint(),xDir=(1,0,0),normal=curve.tangentAt(0))
    shape=cq.Workplane(plane).circle(radius).sweep(path,isFrenet=False,transition='round').val()
    curvature=[curve.curvatureAt(i/160) for i in range(161)]
    minimum_radius=1/max(curvature)
    assert minimum_radius>=11.,('Signal wire bend is below selected-wire minimum',minimum_radius)
    assert shape.isValid() and len(shape.Solids())==1
    return shape,{'wire_od_mm':2*radius,'quarter_bend_input_mm':bend,
                  'sampled_minimum_centerline_radius_mm':minimum_radius,
                  'curvature_samples':161,'route_length_mm':path.Length(),
                  'required_radius_for_max_selected_od_mm':10*.043*25.4}

def design(shapes,parameters):
    front=parameters['front_y_mm'];delta=front+1.6-151
    left_name='P2-flowing-head-left-INTEGRAL-OUTLET'
    grille_name='magnetic-front-cleaning-grille-development'
    keeper_name='head-magnet-retaining-ring-development'
    g=build_geometry(shapes[left_name].translate((0,-delta,0)),
                     shapes[grille_name].translate((0,-delta,0)),
                     shapes[keeper_name].translate((0,-delta,0)),0)
    race_shift=235-(125.5+delta)
    left=shapes[left_name]
    mounts=[(136.7+delta,8),(136.7+delta,29),
            (133+delta+race_shift,-14),(133+delta+race_shift,-52)]
    for i,(y,z) in enumerate(mounts):
        left=left.fuse(box(9. if i<2 else 3.1,7,6,-58.6 if i<2 else -55.65,y,z))
        if i==3:
            # The narrow anchor meets the rounded duct corner while staying
            # 0.3 mm outboard of the lower panel's full 104 mm width. Extending
            # inward beneath the floor would intersect that panel when open.
            left=left.fuse(box(4.9,7,7.9,-54.75,y,-51.05))
        left=left.cut(cx(1.2,-65,14,y,z)).cut(nutx(-56.1,1.8,y,z))
        left=left.cut(box(1.8,8,4.2,-55.2,y+4,z))
    left=left.cut(box(8,18,16,-60.2,136.7+delta+4.7,18.4))
    for tag in ('raceway','clamp','bracket'):
        left=left.cut(g[tag].translate((0,delta+(race_shift if tag!='bracket' else 0),0)))
    # Remove material inside the bracket's screw/nut voids as well as its
    # plastic body. Those voids are occupied by hardware, not enclosure islands.
    left=left.cut(box(2.4,25,33,-64.3,135+delta,16.5))
    left=left.cut(cz(2.075,-10.1,6.2,-60.2,235))
    tongue_window=box(3.8,16,4.4,-60.2,front-4.8,26.4)
    left=left.cut(tongue_window)
    gy=parameters['fixed_guard_y_mm']
    left=left.cut(front_shape(114.6,104.6,6.3,gy-.3,gy+2.3))
    changed={left_name:left,
             grille_name:g['grille'].translate((0,delta,0)).fuse(
                 box(3,4.4,3.6,-60.2,front+3.4,26.4)),
             keeper_name:g['keeper'].translate((0,delta,0)).cut(box(3.8,4,4.4,-60.2,front+.4,26.4)),
             'grille-magnet-retaining-ring-development':shapes['grille-magnet-retaining-ring-development'].cut(
                 box(3.8,4,4.4,-60.2,front+1.2,26.4)),
             'P2-fixed-magnet-seat-frame':shapes['P2-fixed-magnet-seat-frame'].cut(tongue_window)}
    wires={};wire_metrics={};wire_clearances=[]
    for tag,z,offset in (('COM',13.32,-.65),('NO',18.4,.65)):
        wires['REF-'+tag+'-5853-insulated-route'],wire_metrics[tag]=switch_wire_route(z,offset)
        wire_clearances.append(switch_wire_route(z,offset,.85)[0])
    printed={}
    for tag,name in (('bracket','interlock-sliding-bracket-development'),
                     ('cover','interlock-protective-cover-development'),
                     ('clamp','interlock-wire-clamp-development'),
                     ('raceway','interlock-wire-raceway-development'),
                     ('race_lid','interlock-raceway-lid-development')):
        shape=g[tag].translate((0,delta+(race_shift if tag in ('clamp','raceway','race_lid') else 0),0))
        if tag=='cover':
            backplate=cq.Workplane(obj=box(2.4,30.3,35,-70.5,135.65+delta,17.5)).edges('|X').fillet(2).val()
            for z in (8,29):backplate=backplate.cut(cx(1.2,-71.8,3,136.7+delta,z))
            shape=shape.fuse(backplate).cut(left).cut(shapes['P2-fixed-front-finger-guard'])
            shape=shape.cut(box(12,34,38,-52.7,135.65+delta,17.5)).clean()
            # End the shield behind the permanent grille-seat face. The
            # inherited forward wall would cross that face and lose its
            # connection when the head is relieved. The lower inboard corner
            # is an open lever/guard access window, not a hanging cover tab.
            shape=shape.cut(box(30,20,40,-65,front-2.5+10,17.5))
            shape=shape.cut(box(3.4,4.2,2.4,-60,261.05,1))
            for clearance in wire_clearances:shape=shape.cut(clearance)
        printed[name]=shape
    printed['TPU-interlock-wire-liner-development']=wire_liner(hole_diameter=1.2,installed=True).translate((0,delta+race_shift,0))
    purchased={'REF-D2F-01L-drawing-case':g['case'].translate((0,delta,0)),
               'REF-D2F-01L-lever-closed-envelope':g['lever_closed'].translate((0,delta,0))}
    for tag,shape in zip(('COM','NO','NC'),g['terminals']):
        purchased['REF-D2F-01L-'+tag+'-terminal-envelope']=shape.translate((0,delta,0))
    purchased.update(wires)
    metadata={'switch_model':'Omron D2F-01L; primary drawing envelope',
              'translation_y_mm':delta,'case_center_xyz_mm':[-60.2,138.45+delta,18.4],
              'actuator_face_y_mm':143.25+delta,'grille_rear_y_mm':front+1.6,
              'mount_adjustment_y_mm':[-2,2],'nominal_post_trip_mm':.25,
              'additional_stop_travel_mm':.2,'guaranteed_overtravel_min_mm':.55,
              'tongue_root_embed_length_mm':4.,
              'wire_trial_od_mm':1.1,'liner_trial_hole_mm':1.2,
              'raceway_shift_y_mm':race_shift,'wire_routes':wire_metrics,
              'wire_source':'https://www.alphawire.com/en/products/wire/hook-up-wire/premium/5853'}
    return changed,printed,purchased,metadata

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    stage=json.loads((BASE/'stage-validation.json').read_text())
    assert stage['result']=='PASS'
    assert json.loads((BASE/'stage-build-state.json').read_text())['status']=='PASS'
    for name,sha in stage['input_sha256'].items():assert digest(ROOT/name)==sha,('Stale stage',name)
    parameters=json.loads((BASE/'head-parameters.json').read_text())
    shapes={}
    for item in stage['parts']:
        name=item['name'];path=BASE/(name+'.step')
        assert digest(path)==item['sha256'],('Changed part',name)
        if name not in stage['excluded_alternative_and_reserves']:shapes[name]=cq.importers.importStep(str(path)).val()
    changed,printed,purchased,metadata=design(shapes,parameters)
    candidates={**changed,**printed,**purchased}
    for name,shape in candidates.items():
        if len(shape.Solids())!=1:
            diagnostics=[]
            for solid in shape.Solids():
                bb=solid.BoundingBox()
                diagnostics.append({'volume_mm3':solid.Volume(),
                                    'bounds_xyz_mm':[bb.xmin,bb.xmax,bb.ymin,bb.ymax,bb.zmin,bb.zmax]})
            scratch=ROOT/'build/rev-d-cad/interlock-debug';scratch.mkdir(parents=True,exist_ok=True)
            cq.exporters.export(shape,str(scratch/(name+'.step')))
            print('DISCONNECTED',name,json.dumps(diagnostics),flush=True)
        assert shape.isValid() and len(shape.Solids())==1,(name,shape.isValid(),len(shape.Solids()))
    fixed={n:s for n,s in shapes.items() if n not in changed}
    bounds={n:s.BoundingBox() for n,s in {**fixed,**candidates}.items()}
    issues=[];count=0;items=list(candidates.items())
    for i,(name,shape) in enumerate(items):
        for other,solid in list(fixed.items())+items[i+1:]:
            aa,bb=bounds[name],bounds[other]
            separate=any(getattr(aa,k+'max')<=getattr(bb,k+'min')+1e-6 or
                         getattr(bb,k+'max')<=getattr(aa,k+'min')+1e-6 for k in 'xyz')
            volume=0. if separate else max(0.,shape.intersect(solid).Volume())
            count+=1
            if volume>1e-4:issues.append({'a':name,'b':other,'overlap_mm3':volume})
        print('INTERLOCK CHECKED',name,flush=True)
    records=[]
    for name,shape in candidates.items():
        path=OUT/(name+'.step');cq.exporters.export(shape,str(path))
        restored=cq.importers.importStep(str(path)).val()
        assert restored.isValid() and abs(shape.Volume()-restored.Volume())<.1,name
        if name in printed:cq.exporters.export(restored,str(OUT/(name+'.stl')),tolerance=.03,angularTolerance=.08)
        records.append({'name':name,'sha256':digest(path),'printed':name in printed,'solid_count':1})
    report={'result':'PASS' if not issues else 'FAIL','generated_utc':datetime.now(timezone.utc).isoformat(),
            'physical_qualification':False,'pair_checks':count,'issues':issues,**metadata,
            'parts':records,'input_sha256':{str(path.relative_to(ROOT)):digest(path)
              for path in [Path(__file__),ROOT/'cad/grille_interlock_study.py',ROOT/'cad/rev_d_power_access.py',
                           BASE/'stage-validation.json',BASE/'head-parameters.json']},
            'limits':['Independent pilot only; not yet integrated in stage/motion/export reports.',
                      'Primary drawing switch/lever/terminals; no elastic snap-action or trip qualification.',
                      'Nominal connected switch-wire trial only; full connector/service slack and main harness remain unfinished.',
                      'Screw/nut/driver paths, tolerance extremes, slide endpoints and full grille withdrawal require further design checks.',
                      'Fixed guards are not a qualified rotor-fragment containment system.']}
    (OUT/'interlock-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report['result'],count,'checks;',len(issues),'collisions',flush=True)
    for issue in issues:print('COLLISION',issue,flush=True)
    if issues:raise SystemExit(1)

if __name__=='__main__':main()
