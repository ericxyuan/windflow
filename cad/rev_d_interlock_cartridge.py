"""Front-removable grille interlock cartridge against the checked Rev D stage.

All X-axis adjustment/clamp screws are assembled outside the head. Two Y-axis
mounting screws are accessible from the front after the grille seat is removed.
The rotor remains inhibited: these are nominal development assembly checks.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, math
import cadquery as cq
if __package__:
    from . import rev_d_interlock as pilot
    from .grille_interlock_study import nutx, slotx, wire_liner
else:
    import rev_d_interlock as pilot
    from grille_interlock_study import nutx, slotx, wire_liner

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'cad/rev_d'
OUT = BASE/'interlock-cartridge'
HEAD = 'P2-flowing-head-left-INTEGRAL-OUTLET'
CARRIER = 'interlock-front-cartridge-development'
FRONT_AXES = ((-70., -38.), (-65., 38.))


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def box(w,d,h,x,y,z): return pilot.box(w,d,h,x,y,z)
def cx(r,x,length,y,z): return pilot.cx(r,x,length,y,z)
def cz(r,z,length,x,y): return pilot.cz(r,z,length,x,y)
def cy(r,y,length,x,z):
    return cq.Solid.makeCylinder(r,length,cq.Vector(x,y,z),cq.Vector(0,1,0))


def bolt_x(x,length,y,z):
    return cx(1.,x-length,length,y,z).fuse(cx(1.9,x,2.,y,z)).clean()


def bolt_x_forward(x,length,y,z):
    return cx(1.,x,length,y,z).fuse(cx(1.9,x-2.,2.,y,z)).clean()


def washer_x(x,y,z): return cx(2.5,x,.3,y,z).cut(cx(1.1,x-.01,.32,y,z))
def nut_x(x,y,z): return nutx(x,1.6,y,z,af=4.).cut(cx(1.,x-.01,1.62,y,z))


def wire_route(start_z,end_x,radius=.55,adjust_y=0.):
    bend=16.+adjust_y;channel_y=233.;theta0=math.asin(.8/bend)
    offset=end_x-(-62.7)
    def position(theta):
        u=theta/(math.pi/2);ease=u*u*(3-2*u)
        return cq.Vector(-62.7+offset*ease,channel_y+bend-bend*math.sin(theta),
                         start_z-bend*(1-math.cos(theta)))
    angles=[theta0+(math.pi/2-theta0)*i/32 for i in range(33)]
    u=theta0/(math.pi/2)
    tangent=cq.Vector(offset*6*u*(1-u)*2/math.pi,-bend*math.cos(theta0),-bend*math.sin(theta0))
    curve=cq.Edge.makeSpline([position(t) for t in angles],tangents=(tangent,cq.Vector(0,0,-bend)),
                             parameters=angles,scale=False)
    end=curve.endPoint();path=cq.Wire.assembleEdges([curve,cq.Edge.makeLine(end,cq.Vector(end.x,end.y,-52.))])
    plane=cq.Plane(origin=curve.startPoint(),xDir=(1,0,0),normal=curve.tangentAt(0))
    wire=cq.Workplane(plane).circle(radius).sweep(path,isFrenet=False,transition='round').val()
    minimum=1/max(curve.curvatureAt(i/160) for i in range(161))
    assert minimum>=11.,('Wire below selected minimum bend radius',minimum)
    return wire,{'wire_od_mm':2*radius,'quarter_bend_input_mm':bend,
                 'sampled_minimum_centerline_radius_mm':minimum,'curvature_samples':161,
                 'route_length_mm':path.Length(),'exit_z_mm':-52.,
                 'required_radius_for_max_selected_od_mm':10*.043*25.4}


def make_raceway():
    """Shortened captive loom channel; all its parts travel with the cartridge."""
    race=box(5.8,5.8,52.,-60.1,235.,-26.)
    race=race.cut(box(5.,3.4,52.2,-60.9,235.,-26.))
    base=box(5.3,18.8,6.,-62.85,235.,-7.).cut(cz(2.,-10.1,6.2,-60.2,235.))
    base=base.fuse(box(2.4,18.8,10.,-64.3,235.,-5.))
    clamp=box(3.5,18.8,7.,-59.05,235.,-7.).cut(cz(2.,-10.6,7.2,-60.2,235.))
    for y in (229.3,240.7):
        base=base.cut(cx(1.2,-65.6,5.5,y,-7.))
        clamp=clamp.cut(cx(1.2,-60.9,3.7,y,-7.)).cut(nutx(-59.6,2.41,y,-7.,af=4.3))
    race=race.fuse(base).cut(box(3.8,19.,7.2,-58.95,235.,-7.))
    race=race.cut(cz(2.,-10.1,6.2,-60.2,235.))
    for y in (229.3,240.7): race=race.cut(cx(1.2,-65.6,8.6,y,-7.))
    lid=box(1.2,5.8,41.9,-63.6,235.,-31.05)
    for z in (-16.,-46.):
        race=race.fuse(box(5.8,10.6,8.,-60.1,241.2,z))
        lid=lid.fuse(box(1.2,10.6,8.,-63.6,241.2,z))
        race=race.cut(cx(1.2,-64.3,7.2,242.5,z)).cut(nutx(-60.6,3.5,242.5,z,af=4.3))
        lid=lid.cut(cx(1.2,-64.3,1.4,242.5,z))
    return race.clean(),clamp.clean(),lid.clean()


def design(shapes,parameters):
    changed,old_printed,purchased,metadata=pilot.design(shapes,parameters)
    front=parameters['front_y_mm']
    assert front==266.,'Recalculate this front datum before changing the stage length'
    # A long, open-sided spine makes the switch, liner and short raceway one
    # removable service module. Its bottom clears the encoder by 3.5 mm.
    carrier=cq.Workplane(obj=box(2.4,40.2,94.5,-70.5,241.4,-4.75)).edges('|X').fillet(2.).val()
    flange=cq.Workplane(obj=box(13.7,4.8,94.5,-67.15,263.6,-4.75)).edges('|Y').fillet(2.).val()
    carrier=carrier.fuse(flange)
    for z in (8.,29.):
        carrier=carrier.fuse(box(1.3,8.,7.,-68.65,253.3,z))
        carrier=carrier.cut(cx(1.2,-71.8,6.4,253.3,z))
        carrier=carrier.cut(nutx(-71.8,2.5,253.3,z,af=4.3))
    for z in (-16.,-46.):
        carrier=carrier.fuse(box(5.1,8.,7.,-66.75,240.5,z))
        carrier=carrier.cut(cx(1.2,-71.8,7.7,240.5,z))
    for y in (227.3,238.7):
        carrier=carrier.fuse(box(3.8,7.6,7.6,-67.4,y,-7.)).cut(cx(1.2,-71.8,6.4,y,-7.))
        carrier=carrier.cut(cx(2.7,-71.8,.4,y,-7.))
    for x,z in FRONT_AXES:
        carrier=carrier.fuse(cy(3.2,259.5,2.,x,z))
        carrier=carrier.cut(cy(1.2,259.4,6.7,x,z)).cut(cy(2.7,263.5,2.6,x,z))
    # An open horizontal slot passes over the lower head bridge during front
    # withdrawal. The front flange joins both spine branches and stays forward
    # of that bridge, rather than trapping a hidden bolt behind the shell.
    carrier=carrier.cut(box(5.,40.,7.,-70.5,241.1,-38.))
    carrier=carrier.cut(box(3.8,16.,4.4,-60.2,261.2,26.4)).clean()
    bracket=old_printed['interlock-sliding-bracket-development'].translate((-2.5,0,0))
    bracket=bracket.cut(box(10.,20.,40.,-65.,268.8,16.5)).clean()
    # Keep the plate behind the cartridge face throughout its +/-2 mm slide.
    # Outboard movement of the switch clears the fixed guard's edge by 0.5 mm
    # even with its case screw heads and washers included.
    for n,s in list(purchased.items()):
        if n.startswith('REF-D2F-01L'): purchased[n]=s.translate((-2.5,0,0))
    for z in (15.15,21.65): carrier=carrier.cut(slotx(-71.8,6.,253.3,z,travel=2.2,dia=2.4))
    nose=changed['magnetic-front-cleaning-grille-development'].cut(shapes['magnetic-front-cleaning-grille-development'])
    changed['magnetic-front-cleaning-grille-development']=shapes['magnetic-front-cleaning-grille-development'].fuse(
        nose.translate((-2.5,0,0))).fuse(box(5.5,4.4,3.6,-61.45,269.4,26.4)).clean()
    tongue_window=box(6.3,16.,4.4,-61.25,261.2,26.4)
    carrier=carrier.cut(tongue_window).clean()
    carrier=carrier.cut(box(6.4,6.4,15.8,-61.3,264.,20.7)).clean()
    for n in ('head-magnet-retaining-ring-development','grille-magnet-retaining-ring-development','P2-fixed-magnet-seat-frame'):
        changed[n]=shapes[n].cut(tongue_window)
    changed['P2-fixed-magnet-seat-frame']=changed['P2-fixed-magnet-seat-frame'].cut(box(6.4,16.,16.4,-62.7,257.5,18.4))
    race,clamp,lid=make_raceway()
    race=race.translate((0,-2.,0));clamp=clamp.translate((0,-2.,0));lid=lid.translate((0,-2.,0))
    liner=wire_liner(hole_diameter=1.2,installed=True).translate((0,107.5,0))
    # Existing reference wire curvature is preserved. Its free tails end at
    # the cartridge exit; the board connector and full main loom are separate.
    metadata['wire_routes']={}
    for tag,z,x in (('COM',13.32,-60.85),('NO',18.4,-59.55)):
        purchased['REF-'+tag+'-5853-insulated-route'],metadata['wire_routes'][tag]=wire_route(z,x)
    # Two front-loaded RX-M2x4 seats: 3.2 mm printing bore, five mm depth,
    # >=1.3 mm radial wall. Thermal insertion intentionally displaces plastic.
    left=shapes[HEAD]
    for x,z in FRONT_AXES:
        if z<0:
            # Support the lower fixing from the outer flowing wall, outboard
            # of the travelling raceway. The spine's open slot passes over it.
            left=left.fuse(box(40.2,6.2,6.4,-86.9,256.4,z))
        else:
            left=left.fuse(box(14.6,6.2,7.,-61.4,256.4,z))
        left=left.cut(cy(1.6,254.5,5.1,x,z))
    spine_clearance=box(2.8,45.1,94.9,-70.5,243.65,-4.75).cut(box(8.,50.,7.,-70.5,244.,-38.))
    left=left.cut(spine_clearance)
    left=left.cut(box(2.8,29.4,33.4,-66.8,251.6,16.5))
    left=left.cut(box(8.,21.,16.,-62.7,256.3,18.4))
    left=left.cut(box(9.,19.,52.4,-61.3,237.5,-26.))
    left=left.cut(tongue_window)
    gy=parameters['fixed_guard_y_mm']
    left=left.cut(pilot.front_shape(114.6,104.6,6.3,gy-.3,gy+2.3)).clean()
    printed={CARRIER:carrier,'interlock-sliding-bracket-development':bracket,
             'interlock-wire-raceway-development':race,'interlock-wire-clamp-development':clamp,
             'interlock-raceway-lid-development':lid,'TPU-interlock-wire-liner-development':liner}
    stacks={}
    def stack(tag,under_x,length,y,z,nut_start,direction=-1):
        names=['REF-'+tag+'-ISO4762-M2x'+str(length),
               'REF-'+tag+'-ISO7089-M2-washer','REF-'+tag+'-ISO4032-M2-nut']
        purchased[names[0]]=(bolt_x_forward if direction>0 else bolt_x)(under_x,length,y,z)
        purchased[names[1]]=washer_x(under_x if direction>0 else under_x-.3,y,z)
        purchased[names[2]]=nut_x(nut_start,y,z)
        low,high=sorted((under_x,under_x+direction*length))
        engagement=max(0.,min(high,nut_start+1.6)-max(low,nut_start))
        assert engagement>=1.6-1e-6,(tag,engagement)
        stacks[tag]={'axis':'X','direction':direction,'under_head_x_mm':under_x,'length_mm':length,
                     'y_mm':y,'z_mm':z,'full_nut_thread_engagement_mm':engagement}
    for i,z in enumerate((8.,29.)): stack('slide-'+str(i),-65.3,6,253.3,z,-70.9)
    for i,z in enumerate((15.15,21.65)): stack('switch-'+str(i),-59.5,10,253.3,z,-67.6)
    for i,y in enumerate((227.3,238.7)): stack('clamp-'+str(i),-71.7,14,y,-7.,-59.6,direction=1)
    for i,z in enumerate((-16.,-46.)): stack('race-'+str(i),-72.,14,240.5,z,-60.6,direction=1)
    vendor=ROOT/'cad/vendor/ruthex-RX-M2x4.step'
    insert=cq.importers.importStep(str(vendor)).val()
    bb=insert.BoundingBox()
    assert abs(bb.zlen-4.)<1e-3 and abs(max(bb.xlen,bb.ylen)-3.6)<1e-3
    intended={}
    for i,(x,z) in enumerate(FRONT_AXES):
        bolt='REF-cartridge-'+str(i)+'-ISO4762-M2x8'
        ins='REF-cartridge-'+str(i)+'-ruthex-RX-M2x4-vendor'
        purchased[bolt]=cy(1.,255.8,8.,x,z).fuse(cy(1.9,263.8,2.,x,z)).clean()
        purchased['REF-cartridge-'+str(i)+'-ISO7089-M2-washer']=cy(2.5,263.5,.3,x,z).cut(cy(1.1,263.49,.32,x,z))
        purchased[ins]=insert.rotate((0,0,0),(1,0,0),-90).translate((x,259.5-max(0.,bb.zmax),z))
        intended[frozenset((HEAD,ins))]={'kind':'thermal insert seat',
            'envelope':cy(1.81,255.49,4.03,x,z),'maximum_mm3':math.pi*(1.8**2-1.6**2)*4.01}
        intended[frozenset((bolt,ins))]={'kind':'ideal screw major-cylinder / vendor female thread',
            'envelope':cy(1.01,255.79,3.73,x,z),'maximum_mm3':math.pi*1.01**2*3.73}
        stacks['front-'+str(i)]={'axis':'Y','under_head_y_mm':263.8,'length_mm':8,
            'x_mm':x,'z_mm':z,'insert_thread_engagement_mm':3.7,
            'insert_outer_mm':3.6,'printed_seat_mm':3.2,'blind_depth_mm':5.,
            'minimum_radial_plastic_mm':1.4 if z<0 else 1.7}
    # Relieve cartridge body and fastener approaches, not the entire airway.
    # Seat contacts remain at Y=259.5; the final outlet itself stays integral.
    left=left.cut(carrier)
    left=left.cut(box(14.1,5.2,94.9,-67.15,263.6,-4.75))
    # Bounded straight withdrawal corridors retain the two attachment
    # bridges. They end outside the useful duct (X <= -54.6 mm).
    left=left.cut(box(9.1,44.,52.4,-61.35,244.2,-26.))
    left=left.cut(box(11.,29.5,33.4,-62.7,251.45,16.5))
    for z in (8.,29.): left=left.cut(box(8.8,17.1,7.3,-67.4,257.65,z))
    for z in (-16.,-46.): left=left.cut(box(17.4,30.,8.4,-65.6,251.2,z))
    left=left.cut(box(17.4,45.1,7.9,-65.6,243.65,-7.))
    for z in (8.,29.): left=left.cut(cx(2.8,-74.,12.,253.3,z))
    for z in (15.15,21.65): left=left.cut(slotx(-70.,13.,253.3,z,travel=2.2,dia=5.6))
    for x,z in FRONT_AXES: left=left.cut(cy(2.8,259.5,6.7,x,z))
    changed[HEAD]=left.clean()
    changed['P2-fixed-magnet-seat-frame']=changed['P2-fixed-magnet-seat-frame'].cut(carrier).clean()
    metadata['case_center_xyz_mm']=[-62.7,255.05,18.4]
    metadata['actuator_contact_x_mm']=-62.7
    metadata['wire_channel_y_mm']=233.
    metadata['raceway_shift_y_mm']=-9.1
    metadata.update({'architecture':'Front-removable cartridge; fixed grille seat removed first; all internal X screws preassembled outside head',
                     'free_wire_exit_z_mm':-52.,'front_mount_axes_xz_mm':FRONT_AXES,
                     'front_fastener_stacks':stacks,'insert_vendor_sha256':digest(vendor),
                     'insert_datasheet_sha256':digest(ROOT/'hardware/datasheets/Ruthex-RX.pdf'),
                     'insert_source':'https://www.ruthex.de/en/products/ruthex-gewindeeinsatz-m2-70-stuck-rx-m2x4-messing-gewindebuchsen',
                     'fixed_seat_removed_for_cartridge_service':True,
                     'wire_routes_scope':'Terminal-to-cartridge-exit trial only; main J12 connector unplugged before service'})
    return changed,printed,purchased,metadata,intended


def load_stage():
    stage=json.loads((BASE/'stage-validation.json').read_text())
    assert stage['result']=='PASS' and json.loads((BASE/'stage-build-state.json').read_text())['status']=='PASS'
    for n,h in stage['input_sha256'].items(): assert digest(ROOT/n)==h,('Stale stage',n)
    shapes={}
    for item in stage['parts']:
        path=BASE/(item['name']+'.step')
        assert digest(path)==item['sha256'],('Changed stage part',item['name'])
        if item['name'] not in stage['excluded_alternative_and_reserves']:
            shapes[item['name']]=cq.importers.importStep(str(path)).val()
    return shapes,json.loads((BASE/'head-parameters.json').read_text())


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    shapes,parameters=load_stage()
    changed,printed,purchased,metadata,intended=design(shapes,parameters)
    candidates={**changed,**printed,**purchased}
    for name,shape in candidates.items():
        if not shape.isValid() or len(shape.Solids())!=1:
            details=[]
            for s in shape.Solids():
                b=s.BoundingBox();details.append({'volume':s.Volume(),'bounds':[b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax]})
            print('INVALID',name,json.dumps(details),flush=True)
        assert shape.isValid() and len(shape.Solids())==1,name
    fixed={n:s for n,s in shapes.items() if n not in changed}
    bounds={n:s.BoundingBox() for n,s in {**fixed,**candidates}.items()}
    issues=[];couplings=[];count=0;items=list(candidates.items())
    for i,(n,s) in enumerate(items):
        for fn,fs in list(fixed.items())+items[i+1:]:
            a,b=bounds[n],bounds[fn]
            separate=any(getattr(a,k+'max')<=getattr(b,k+'min')+1e-6 or
                         getattr(b,k+'max')<=getattr(a,k+'min')+1e-6 for k in 'xyz')
            intersection=None if separate else s.intersect(fs)
            volume=0. if separate else max(0.,intersection.Volume())
            count+=1
            if volume<=1e-4: continue
            key=frozenset((n,fn))
            if key in intended:
                rule=intended[key];outside=intersection.cut(rule['envelope']).Volume()
                assert outside<1e-4 and volume<=rule['maximum_mm3'],('Invalid intended coupling',n,fn,volume,outside)
                couplings.append({'a':n,'b':fn,'kind':rule['kind'],'overlap_mm3':volume,'outside_declared_seat_mm3':outside})
            else: issues.append({'a':n,'b':fn,'overlap_mm3':volume})
        print('CARTRIDGE CHECKED',n,flush=True)
    records=[]
    for n,s in candidates.items():
        path=OUT/(n+'.step');cq.exporters.export(s,str(path))
        restored=cq.importers.importStep(str(path)).val()
        assert restored.isValid() and len(restored.Solids())==1 and abs(s.Volume()-restored.Volume())<.1,n
        if n in printed: cq.exporters.export(restored,str(path.with_suffix('.stl')),tolerance=.03,angularTolerance=.08)
        records.append({'name':n,'sha256':digest(path),'printed':n in printed,'solid_count':1})
    sources=[Path(__file__),ROOT/'cad/rev_d_interlock.py',ROOT/'cad/grille_interlock_study.py',
             ROOT/'cad/rev_d_power_access.py',BASE/'stage-validation.json',BASE/'head-parameters.json',
             ROOT/'cad/vendor/ruthex-RX-M2x4.step',ROOT/'hardware/datasheets/Ruthex-RX.pdf']
    report={'result':'PASS' if not issues else 'FAIL','generated_utc':datetime.now(timezone.utc).isoformat(),
            'physical_qualification':False,'pair_checks':count,'issues':issues,'intended_couplings':couplings,
            'parts':records,'input_sha256':{str(p.relative_to(ROOT)):digest(p) for p in sources},**metadata,
            'limits':['Independent cartridge candidate; not yet in current main stage or Onshape checkpoint.',
                      'Primary switch drawing envelopes; no elastic snap-action or trip qualification.',
                      'Thread cylinders and thermal-insert material displacement are declared interfaces, not fit or strength qualification.',
                      'Main wire connectors, complete loom, tolerance extremes and physical actuation remain to qualify.',
                      'Fixed finger guards are not qualified rotor-fragment containment.']}
    (OUT/'cartridge-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report['result'],count,'checks;',len(issues),'unintended collisions',flush=True)
    for issue in issues: print('COLLISION',issue,flush=True)
    if issues: raise SystemExit(1)


if __name__=='__main__': main()
