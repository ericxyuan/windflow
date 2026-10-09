"""Rev C flowing head and service base: real development B-reps, not print release.

Airflow +Y. Native Onshape stations are mirrored, with separately printable head
halves and a rigid motor carrier. Existing mechanical prototype references are
carried forward with explicit provenance and nominal collision reports.
"""
from pathlib import Path
from datetime import datetime, timezone
import json, math, hashlib
import cadquery as cq
from rev_c_service import integrate as integrate_service
from rev_c_guards import integrate as integrate_guards
from grille_interlock_study import build_geometry as interlock_geometry, wire_liner

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'rev_c'
P = json.loads((OUT / 'head-parameters.json').read_text(encoding='utf-8'))
PARTS, RECORDS = {}, []
T, R = P['wall'], P['throat_diameter']/2
W, H, L, HY = P['outlet_width'], P['outlet_height'], P['panel_length'], P['panel_hinge_y']

def box(w,d,h,x=0,y=0,z=0):
    return cq.Workplane('XY').box(w,d,h).val().translate((x,y,z))

def cy(r,y,l,x=0,z=0):
    return cq.Solid.makeCylinder(r,l,cq.Vector(x,y,z),cq.Vector(0,1,0))

def cx(r,x,l,y=0,z=0):
    return cq.Solid.makeCylinder(r,l,cq.Vector(x,y,z),cq.Vector(1,0,0))

def cz(r,z,l,x=0,y=0):
    return cq.Solid.makeCylinder(r,l,cq.Vector(x,y,z),cq.Vector(0,0,1))

def rr(w,h,r,y,x=0,z=0):
    a,b,k=w/2,h/2,math.sqrt(.5)
    p=cq.Workplane(cq.Plane(origin=(x,y,z),xDir=(1,0,0),normal=(0,-1,0)))
    return (p.moveTo(-a+r,-b).lineTo(a-r,-b)
      .threePointArc((a-r+r*k,-b+r-r*k),(a,-b+r)).lineTo(a,b-r)
      .threePointArc((a-r+r*k,b-r+r*k),(a-r,b)).lineTo(-a+r,b)
      .threePointArc((-a+r-r*k,b-r+r*k),(-a,b-r)).lineTo(-a,-b+r)
      .threePointArc((-a+r-r*k,-b+r-r*k),(-a+r,-b)).close().val())

def rrxy(w,d,r,z,x=0,y=0):
    wire=rr(w,d,r,0).rotate((0,0,0),(1,0,0),90)
    return wire.translate((x,y,z))

def segmented_circle(r,y):
    a=(-100,-80,-10,10,80,100,170,190,260)
    def v(t):
        t=math.radians(t)
        return cq.Vector(r*math.cos(t),y,r*math.sin(t))
    return cq.Wire.assembleEdges([cq.Edge.makeThreePointArc(v(i),v((i+j)/2),v(j)) for i,j in zip(a[:-1],a[1:])])

def record(name,shape,printed=True,material='PETG prototype',source=None,one_solid=True):
    if source: source=str(source).replace('\\','/')
    assert shape.isValid(),name+' invalid'
    if one_solid: assert len(shape.Solids())==1,(name,len(shape.Solids()))
    assert shape.Volume()>0,name
    cq.exporters.export(shape,str(OUT/(name+'.step')))
    if printed: cq.exporters.export(shape,str(OUT/(name+'.stl')),tolerance=.06,angularTolerance=.12)
    b=shape.BoundingBox()
    RECORDS[:]=[r for r in RECORDS if r['name']!=name]
    RECORDS.append({'name':name,'valid':True,'solid_count':len(shape.Solids()),'printed':printed,
      'material':material,'source':source,'bounds_xyz_mm':[b.xmin,b.xmax,b.ymin,b.ymax,b.zmin,b.zmax],
      'volume_mm3':shape.Volume()})
    PARTS[name]=shape
    print('EXPORTED',name,flush=True)
    return shape

def load(name,path,translation=(0,0,0),printed=False):
    s=cq.importers.importStep(str(path)).val().translate(translation)
    return record(name,s,printed,source=str(path.relative_to(ROOT.parent)),one_solid=False)

def overlap(a,b):
    ba,bb=a.BoundingBox(),b.BoundingBox()
    if ba.xmax<=bb.xmin or bb.xmax<=ba.xmin or ba.ymax<=bb.ymin or bb.ymax<=ba.ymin or ba.zmax<=bb.zmin or bb.zmax<=ba.zmin:
        return 0.
    return a.intersect(b).Volume()

def main():
    outer=cq.Solid.makeLoft([rr(w,h,r,y) for y,w,h,r in P['outer_sections_y_w_h_r']],False)
    transition=cq.Solid.makeLoft([segmented_circle(R,P['transition_y0']),rr(W,H,3,P['transition_y1'])],True)
    front=P['outer_sections_y_w_h_r'][-1][0]
    outlet=cq.Solid.makeLoft([rr(W+.04,H+.04,3.02,HY),rr(W+.04,H+.04,3.02,front+1)],True)
    throat=cy(R,-1,P['transition_y0']+1.02)
    shell=outer.cut(throat).cut(transition).cut(outlet)
    carrier_seat=cy(P['carrier_outer_radius']+P['carrier_radial_clearance'],
                    P['carrier_y0']-P['carrier_axial_clearance'],
                    P['carrier_y1']-P['carrier_y0']+2*P['carrier_axial_clearance'])
    shell=shell.cut(carrier_seat)
    shell=shell.cut(cy(59.4,P['stator_y0']-.3,P['stator_length']+.6))
    assert shell.isValid() and len(shell.Solids())==1,'initial flow shell'
    record('head-flowing-unsplit-development',shell,False)

    # Integrate the proven linkage fixture into the permanent outlet. Its drive
    # hardware is inherited as a study, with a new whole-head clearance audit.
    # Rebuild only the drive-side bearing supports as simple connected solids.
    # Reusing the old rectangular fixture B-rep caused a non-manifold Boolean
    # at the new curved shell, so its duct geometry is not carried forward.
    fixture_path=ROOT/'prototypes/nozzle-test-frame.step'
    fixture=cq.importers.importStep(str(fixture_path)).val().translate((0,HY,0))
    # Adopt the already dimensioned bearing arms, yoke guides, stops and servo
    # bracket attachment. Trim its rectangular airflow walls at the new curved
    # head, retaining only the outboard structural skeleton.
    skeleton=fixture.intersect(box(100,200,200,104,HY,0))
    shell=shell.fuse(skeleton)
    print('BUILT drive-side supports',shell.isValid(),len(shell.Solids()),flush=True)
    for sign in (-1,1):
        z=sign*H/2
        shell=shell.cut(box(W-.5,L+7,4.0,0,HY+L/2,z))
        shell=shell.cut(cx(3.1,-W/2+.25,W+28,HY,z))
        shell=shell.cut(cx(1.65,-72,175,HY,z))
        print('CUT panel clearance',sign,shell.isValid(),len(shell.Solids()),flush=True)
    # New body was already cut to the flow; these support arms are outboard.
    shell=shell.clean()
    assert shell.isValid() and len(shell.Solids())==1,'integrated shell'
    print('BUILT panel clearance',flush=True)

    # Seam screws enter along X from the left; insert installation and screw
    # access remain outside the flow. Local bosses bridge the smooth exterior.
    seams=[];attachments=[];foot_holes=[]
    for y in P['shell_seam_positions_y']:
        # Read actual outer-section cross-section through a slender slab.
        slab=outer.intersect(box(400,.1,400,0,y,0)).BoundingBox()
        for sign in (-1,1):
            z=sign*(slab.zlen/2+2.0)
            attachments.append(cx(4.7,-9,18,y,z))
            seams.append((y,z))
    # Rigid structural feet connect to the flowing base; through-bores are
    # accessible before the open-bottom service tray is fitted.
    for x in (-38,38):
        for y in (38,81):
            ear=box(14,16,15,x,y,-65)
            attachments.append(ear);foot_holes.append(cz(2,-72.6,7.0,x,y))
    cover_axes=[(60,z,32) for z in (-60,60)]+[(130,z,53.5) for z in (-50,50)]
    for y,z,x in cover_axes:attachments.append(cx(4.7,x,106.9-x,y,z))
    shell=shell.fuse(*attachments).cut(*foot_holes)
    print('BUILT shell seam and base feet',flush=True)
    # Real clearance must be cut, never waived as an "intended" penetration.
    # Sample the yoke travel and preserve the original matched hinge axes.
    yoke_source=cq.importers.importStep(str(ROOT/'prototypes/installed-yoke-open.step')).val().translate((0,HY,0))
    stroke=24*math.sin(math.asin(H*(1-P['minimum_gross_outlet_ratio'])/(2*L)))
    for i in range(7):
        yoke_pose=yoke_source.translate((0,stroke*i/6,0))
        for dx,dz in ((0,0),(-.3,0),(.3,0),(0,-.3),(0,.3)):
            shell=shell.cut(yoke_pose.translate((dx,0,dz)))
    shell,guard_interfaces=integrate_guards(shell,P,record,box,cx,cy,rr)
    (OUT/'guard-interfaces.json').write_text(json.dumps(guard_interfaces,indent=2)+'\n')
    left=shell.intersect(box(400,400,400,-200,80,0)).clean()
    right=shell.intersect(box(400,400,400,200,80,0)).clean()
    for y,z in seams:
        left=left.cut(cx(1.7,-9.1,9.2,y,z)).cut(cx(3.2,-9.1,3,y,z))
        right=right.cut(cx(2,-.1,6.9,y,z))
    for y,z,x in cover_axes:right=right.cut(cx(2,100,7,y,z))
    # Adopt the adjustable Omron switch bracket and protected wire raceway at
    # the new grille rear datum. The switch cavity stays outside the air duct.
    delta=front+1.6-151
    g=interlock_geometry(left.translate((0,-delta,0)),
        PARTS['magnetic-front-cleaning-grille-development'].translate((0,-delta,0)),
        PARTS['head-magnet-retaining-ring-development'].translate((0,-delta,0)),0)
    left=g['left'].translate((0,delta,0)).cut(box(8,18,16,-60.2,136.7+delta+4.7,18.4))
    # Raceway has an open installation channel; remove the exact occupied
    # volume from the curved outside wall, keeping its mounting ears intact.
    for tag in ('raceway','clamp','bracket'):
        left=left.cut(g[tag].translate((0,delta,0)))
    left=left.cut(cz(2.075,-10.1,6.2,-60.2,125.5+delta))
    left=left.cut(box(3.8,16,4.4,-60.2,front-4.8,26.4))
    guard_seat=cq.Solid.makeLoft([rr(114.6,104.6,6.3,168.2),rr(114.6,104.6,6.3,170.8)],True)
    left=left.cut(guard_seat)
    record('magnetic-front-cleaning-grille-development',g['grille'].translate((0,delta,0)))
    keeper=g['keeper'].translate((0,delta,0)).cut(box(3.8,4,4.4,-60.2,front+.4,26.4))
    record('head-magnet-retaining-ring-development',keeper)
    grille_keeper=PARTS['grille-magnet-retaining-ring-development'].cut(box(3.8,4,4.4,-60.2,front+1.2,26.4))
    record('grille-magnet-retaining-ring-development',grille_keeper)
    for tag,name in (('bracket','interlock-sliding-bracket-development'),('cover','interlock-protective-cover-development'),
                    ('clamp','interlock-wire-clamp-development'),('raceway','interlock-wire-raceway-development'),
                    ('race_lid','interlock-raceway-lid-development')):
        shape=g[tag].translate((0,delta,0))
        if tag=='cover':
            # A continuous outboard backplate reconnects the protective walls
            # after relief against the curved head. Keep its screw axes aligned
            # with the adjustable switch bracket, with access from -X.
            backplate=cq.Workplane(obj=box(2.4,30.3,35,-70.5,135.65+delta,17.5)).edges('|X').fillet(2).val()
            for z in (8,29):
                backplate=backplate.cut(cx(1.2,-71.8,3,136.7+delta,z))
            shape=shape.fuse(backplate).cut(left).cut(PARTS['fixed-front-finger-guard-development'])
            # Remove the unused inboard-wall tips explicitly: after the head
            # recess they are tiny disconnected remnants, outside the cover's
            # functional outboard shell and screw crush posts.
            shape=shape.cut(box(12,34,38,-52.7,135.65+delta,17.5)).clean()
            if len(shape.Solids())!=1:
                print('COVER SOLIDS',[(s.Volume(),[getattr(s.BoundingBox(),k) for k in ('xmin','xmax','ymin','ymax','zmin','zmax')]) for s in shape.Solids()],flush=True)
        record(name,shape)
    record('REF-D2F-01L-drawing-case',g['case'].translate((0,delta,0)),False,'Omron D2F-01L drawing envelope')
    record('REF-D2F-01L-lever-closed-envelope',g['lever_closed'].translate((0,delta,0)),False,'elastic lever envelope only')
    record('TPU-interlock-wire-liner-development',wire_liner(installed=True).translate((0,delta,0)),True,'TPU95A')
    guard_interfaces['interlock']='Omron D2F-01L bracket/raceway/tongue integrated; physical trip/overtravel and harness tests required'
    (OUT/'guard-interfaces.json').write_text(json.dumps(guard_interfaces,indent=2)+'\n')
    # Normalize the long Boolean chain through STEP before the final seat cut.
    # Repeating that cut on the long-lived BOP object still gave a misleading
    # empty common; the independent exchange kernel found an annular overlap.
    record('head-left-integral-outlet',left)
    record('head-right-integral-outlet',right)
    stator_seat=cy(59.4,P['stator_y0']-.3,P['stator_length']+.6)
    for name in ('head-left-integral-outlet','head-right-integral-outlet'):
        normalized=cq.importers.importStep(str(OUT/(name+'.step'))).val()
        # Keep the exchanged face partition. Unifying the seam/seat faces with
        # clean() invalidates the right half at this curved annular interface.
        # The raw cut and its separately reopened STEP are both checked below.
        relieved=normalized.cut(stator_seat)
        record(name,relieved)

    # Quarter-circle bell mouth: real R14 inner radius and R11.6 outer radius.
    br=P['bellmouth_radius'];k=math.sqrt(.5)
    bell=(cq.Workplane('XY').moveTo(R,0)
      .threePointArc((R+br-br*k,-br*k),(R+br,-br)).lineTo(R+br,-br+T)
      .threePointArc((R+br-(br-T)*k,-(br-T)*k),(R+T,0)).close()
      .revolve(360,(0,0),(0,1)).val())
    bell=bell.fuse(cy(R+2.4,-.02,4.02).cut(cy(R,-.1,4.2)))
    bell=bell.fuse(cy(R+2.8,1,1).cut(cy(R,.9,1.2)))
    bell=bell.fuse(cy(75,-15.6,4).cut(cy(69.5,-15.7,4.2)))
    for x,z in ((-72,0),(72,0),(0,-72),(0,72)):
        bell=bell.cut(cy(1.6,-15.7,4.2,x,z))
    record('R14-bellmouth-insert-development',bell)

    ring=cy(P['carrier_outer_radius'],52,6).cut(cy(P['carrier_inner_radius'],51.9,6.2))
    carrier=ring.fuse(cy(18,52,6))
    for a in (45,135,225,315):
        support=box(P['carrier_outer_radius']-17,6,3.2,(17+P['carrier_outer_radius'])/2,55,0)
        carrier=carrier.fuse(support.rotate((0,0,0),(0,1,0),a))
    for a in (0,90,180,270):
        x,z=8*math.cos(math.radians(a)),8*math.sin(math.radians(a))
        carrier=carrier.cut(cy(1.7,51.9,6.2,x,z))
    carrier=carrier.cut(cy(4,51.9,6.2)).clean()
    carrier=carrier.intersect(cy(P['carrier_outer_radius'],51.9,6.2)).clean()
    record('rigid-motor-carrier-PCD16',carrier)
    # Structural carrier struts and an independent downstream seven-vane study
    # are deliberately distinct. Trim vane ends to the actual transition void.
    sy=P['stator_y0'];sl=P['stator_length']
    stator=cy(18,sy,sl).cut(cy(16,sy-.1,sl+.2))
    count=P['stator_vane_count']
    for i in range(count):
        vane=box(56.7-17.5,sl,P['stator_vane_thickness'],(56.7+17.5)/2,sy+sl/2,0)
        stator=stator.fuse(vane.rotate((0,0,0),(0,1,0),i*360/count))
    flow=throat.fuse(transition).fuse(outlet)
    stator=stator.intersect(flow).clean()
    stator=stator.fuse(cy(59.1,sy,sl).cut(cy(55.5,sy-.1,sl+.2))).clean()
    record('seven-vane-straightener-development',stator)
    motor=cy(15.1,29,23).fuse(cy(2.5,21,8)).clean()
    record('REF-P2406-drawing-envelope-seat-unverified',motor,False,'manufacturer drawing envelope')
    rotor_path=OUT/'impeller-P1-GUARDED-TEST-ONLY.step'
    if rotor_path.exists():
        rotor=cq.importers.importStep(str(rotor_path)).val().rotate((0,0,0),(1,0,0),180).translate((0,29,0))
        record('REF-impeller-P1-installed-test-only',rotor,False,source='cad/rev_c/impeller-P1-GUARDED-TEST-ONLY.step')

    # Carry the calibrated prototype kinematics into the new Y100 hinge datum.
    for tag in ('upper_panel','lower_panel','upper_crank','lower_crank','yoke','rod','horn'):
        source=ROOT/'prototypes'/('installed-'+tag+'-open.step')
        if source.exists():
            load('REF-mechanism-'+tag+'-open',source,(0,HY,0))
    for tag in ('upper_shaft','lower_shaft','upper_retaining_spacer','lower_retaining_spacer',
                'upper_left_collar','lower_left_collar','upper_right_collar','lower_right_collar'):
        if tag.endswith('_shaft'):
            record('REF-mechanism-'+tag,cx(1.5,-71,172,HY,H/2 if tag.startswith('upper') else -H/2),False,'3mm ground steel shaft, cut to172mm')
        else:
            load('REF-mechanism-'+tag,ROOT/'prototypes'/('installed-'+tag+'.step'),(-9.3 if 'left_collar' in tag else 0,HY,0))
    load('servo-slotted-bracket-development',ROOT/'prototypes/servo-slotted-bracket.step',(0,HY,0),True)
    load('REF-FS90-FB-family-envelope-UNVERIFIED',ROOT/'prototypes/REF-FS90-FB-approximate-envelope.step',(0,HY,0))

    # Flowing service base, open at the bottom. A separate tray permits insertion
    # and removal of the display and ESC without an inaccessible closed cavity.
    bz,by=P['base_bottom_z'],P['base_center_y']
    base_outer=cq.Solid.makeLoft([rrxy(190,175,20,bz,y=by),rrxy(190,175,20,bz+6,y=by),rrxy(184,160,22,-74,y=by)],False)
    base_inner=cq.Solid.makeLoft([rrxy(184,169,17,bz-.1,y=by),rrxy(178,154,19,-77,y=by)],False)
    base=base_outer.cut(base_inner)
    tray=cq.Solid.makeLoft([rrxy(189.4,174.4,19.7,bz-3,y=by),rrxy(189.4,174.4,19.7,bz-.2,y=by)],True)
    # Four desk-foot collars are separate replaceable parts. They do not touch
    # the shell's open-bottom rim, so keeping them out of the base B-rep avoids
    # a misleading multi-solid "base" export and reflects the intended TPU
    # isolation/foot replacement workflow.
    base_feet=[]
    for x,y in ((-79,18),(79,18),(-79,143),(79,143)):
        base_feet.append(cz(7,bz-8,5,x,y).cut(cz(1.7,bz-8.1,5.2,x,y)).cut(cz(3.2,bz-8.1,2.2,x,y)))
        tray=tray.cut(cz(1.7,bz-3.1,3,x,y))
    for x in (-38,38):
        for y in (38,81):
            pedestal=cz(7,-74,1.5,x,y)
            base=base.fuse(pedestal).cut(cz(1.7,-77.1,4.8,x,y))

    # The drive yoke and lower crank enter from the right side of the base.
    # Reserve a removable service corridor so those moving parts do not occupy
    # the base wall or the tray rim during the swept-path study.
    base=base.cut(box(18,28,14,79,112,-75)).clean()

    # Vendor 4311 glass/PCB, using verified Rev B orientation but moved to the
    # centre of the wider curved front. Current EYESPI connector is still a test.
    display_source=ROOT/'rev_b/Adafruit-ST7789-4311-display-vendor.step'
    if display_source.exists():
        display=cq.importers.importStep(str(display_source)).val().translate((-15,31,-1))
        record('REF-Adafruit-4311-IPS-vendor',display,False,source='cad/rev_b/Adafruit-ST7789-4311-display-vendor.step',one_solid=False)
        # Through-opening clears PCB insertion; external bezel retains clear lens.
        base=base.cut(box(63,24,38,0,167,-95.5))
        bezel=box(78,2.4,39.6,0,171.8,-95.5).cut(box(42.4,3,31.6,0,171.8,-95.5))
        bezel=bezel.cut(box(45.4,1.2,34.8,0,171.2,-95.5))
        window=box(45,1,34.4,0,171.1,-95.5)
        # A fascia recess accepts the bezel without burying it in the curved wall.
        base=base.cut(box(78.4,4,40,0,172.5,-95.5))
        record('display-front-bezel-development',bezel)
        record('REF-clear-display-lens-45x34p4',window,False,'1mm clear acrylic')
        # The deeper 44mm base clears the PCB without thinning its roof or tray.

    # Electronics reserve: an installed blank is not a fabricated controller.
    record('REF-A50S-V2p3c-envelope-UNVERIFIED',box(46,22,17,37,45,-99.5),False,'conservative connector-inclusive envelope')
    record('REF-ESC-connector-corridor',box(58,34,20,37,45,-99.5),False,'reserve includes wiring; deliberate envelope, excluded from solid fit checks')
    record('REF-new-power-board-reserve-NOT-ROUTED',box(80,55,18,-11,96,-101),False,'new TPS26630 circuit and PCB required')
    # Downward ambient opening and replaceable diffuser.
    tray=tray.cut(box(54,10,4,0,82,bz-1.5))
    record('ambient-diffuser-development',box(53.6,9.6,.8,0,82,bz-2.3),True,'translucent PETG')
    base,tray,fasteners,mounts,cable_reserves=integrate_service(ROOT,P,base,tray,PARTS,record,box,cx,cy,cz)
    fasteners.extend({'interface':'linkage cover M3x8 / RX-M3x5.7','axis_xyz_mm':[110,y,z],'direction':'-X'} for y,z,x in cover_axes)
    (OUT/'service-interfaces.json').write_text(json.dumps({'fasteners':fasteners,'mounts':mounts,
       'reserves':[{'name':n,'bounds_xyz_mm':[getattr(s.BoundingBox(),k) for k in ('xmin','xmax','ymin','ymax','zmin','zmax')]} for n,s in cable_reserves.items()],
       'physical_qualification':False},indent=2)+'\n')
    record('flowing-base-open-bottom',base.clean())
    record('base-replaceable-feet-development',cq.Compound.makeCompound(base_feet),True,'TPU isolation feet',one_solid=False)
    record('base-service-tray-development',tray.clean())

    # Native-profile side fairing surrounds the inherited linkage. Subtract the
    # housing so overlap of the cover and structural head is never hidden.
    fair_outer=cq.Solid.makeLoft([rr(174,110,20,0),rr(174,110,25,12),rr(168,100,32,50)],False)
    fair_inner=cq.Solid.makeLoft([rr(168,104,17,-1),rr(162,94,29,47)],False)
    fairing=fair_outer.cut(fair_inner).rotate((0,0,0),(1,1,1),-120).translate((60,95,0))
    fairing=fairing.cut(shell)
    fairing=fairing.cut(base).cut(tray)
    # A quarter-millimetre cover/base seam avoids coincident exchanged loft
    # faces and gives the printed cover useful assembly clearance.
    for shift in ((.25,0,0),(-.25,0,0),(0,.25,0),(0,-.25,0),(0,0,.25),(0,0,-.25)):
        fairing=fairing.cut(base.translate(shift))
    # Open the cover around the actual moving yoke and lower crank. These are
    # service clearances, not decorative overlaps; the fairing remains one
    # printable shell after the relief cuts.
    fairing=fairing.cut(PARTS['REF-mechanism-lower_crank-open'])
    fairing=fairing.cut(PARTS['REF-mechanism-yoke-open'])
    for y,z,x in cover_axes:
        fairing=fairing.cut(cx(1.7,106.8,8,y,z)).cut(cx(3.2,109,6,y,z))
    # Subtracting the base leaves an unfastened strip below its roof. Remove
    # that redundant strip; the four cover screws retain the continuous main
    # shell, and no detached island is presented as a printable cover.
    fairing_solids=sorted(fairing.Solids(),key=lambda s:s.Volume(),reverse=True)
    for fragment in fairing_solids[1:]:
        assert fragment.BoundingBox().zmax < -76.9 and fragment.Volume()<15000
    fairing=fairing_solids[0]
    record('curved-linkage-fairing-development',fairing)

    # Validate the actual exchange files, independently reopened. Checking only
    # the long-lived Boolean objects missed a seat loss visible in Onshape.
    for name in list(PARTS):
        PARTS[name]=cq.importers.importStep(str(OUT/(name+'.step'))).val()
        assert PARTS[name].isValid(),('Invalid exchanged geometry',name)

    # Nominal assembly checks intentionally do not treat reference reserves as
    # fabricated objects. Contacting mount faces are recorded separately.
    checks=[];issues=[]; intended=[]
    def intended_contact(a,b):
        pair={a,b}
        return None
    exclusions={'head-flowing-unsplit-development','REF-ESC-connector-corridor','REF-new-power-board-reserve-NOT-ROUTED'}
    keys=[n for n in PARTS if n not in exclusions]
    for i,a in enumerate(keys):
        if i%8==0:print('NOMINAL',i,'/',len(keys),'parts',flush=True)
        for b in keys[i+1:]:
            v=overlap(PARTS[a],PARTS[b]); checks.append({'a':a,'b':b,'overlap_mm3':v})
            if v>1e-4:
                reason=intended_contact(a,b)
                if reason: intended.append({'a':a,'b':b,'overlap_mm3':v,'reason':reason})
                else: issues.append({'a':a,'b':b,'overlap_mm3':v})
    motion=[]
    for pose in ('open','max-boost'):
        for tag in ('upper_panel','lower_panel'):
            source=ROOT/'prototypes'/('installed-'+tag+'-'+pose+'.step')
            if not source.exists(): continue
            panel=cq.importers.importStep(str(source)).val().translate((0,HY,0))
            for fixed in ('head-left-integral-outlet','head-right-integral-outlet','rigid-motor-carrier-PCD16'):
                v=overlap(panel,PARTS[fixed]);motion.append({'pose':pose,'part':tag,'fixed':fixed,'overlap_mm3':v})
                if v>1e-4:
                    issues.append(motion[-1])
    assembly=cq.Assembly(name='Windflow-Rev-C-development')
    for name,s in PARTS.items():
        if name not in exclusions: assembly.add(s,name=name)
    cq.exporters.export(assembly.toCompound(),str(OUT/'head-base-development-assembly.step'))
    report={'revision':P['revision'],'timestamp_utc':datetime.now(timezone.utc).isoformat(),'physical_qualification':False,
      'parts':RECORDS,'pair_checks':len(checks),'unintended_issues':issues,'intentional_interfaces':intended,'pair_results':checks,'panel_pose_checks':motion,
      'pair_check_geometry':'Independently reopened individual STEP exports',
      'motor_carrier_tpu_radial_thickness_mm':P['carrier_radial_clearance'],
      'motor_carrier_hard_stop_gap_mm':P['carrier_hard_stop_gap'],
      'rotor_nominal_tip_gap_mm':1.,
      'hard_stop_xy_excursion_bound_nominal_mm':math.sqrt(2)*P['carrier_hard_stop_gap'],
      'alignment_and_runout_require_physical_measurement':True,'minimum_outlet_ratio_gross':.75,
      'maximum_panel_angle_deg':math.degrees(math.asin(H*.25/(2*L))),
      'limitations':['Native Onshape architecture feature is instantiated separately; full local assembly export has no motion mates and is not a print release.',
        'Inlet and carrier are positively captured by the split head; actual retention/compression and insert pull-out require tests.',
        'Mechanism retains measured-datum assumptions for FS90-FB; consult separate source-matched motion report.',
        'No fixed fragment-containment guard qualification, CFD, stress, noise or thermal test.',
        'ESC reserve is not exact V2.3c vendor geometry; new power board is unrouted.',
        'Full installed wires/tubes, final cover attachment and tool sweeps remain unfinished design.',
        'Screen, encoder and USB-C integration are nominal; verify fascia, EYESPI harness and operation on test prints.']}
    report['input_sha256']={str(p.relative_to(ROOT.parent)):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [Path(__file__),ROOT/'rev_c_service.py',ROOT/'rev_c_guards.py',ROOT/'grille_interlock_study.py',OUT/'head-parameters.json']}
    for entry in RECORDS:
        if not entry['source']:continue
        path=ROOT.parent/entry['source'] if entry['source'].startswith('cad/') else ROOT/entry['source']
        if path.exists():report['input_sha256'][str(path.relative_to(ROOT.parent))]=hashlib.sha256(path.read_bytes()).hexdigest()
    # Hash only this generator's outputs. Build state changes after this report;
    # motion/test-piece/export reports are independent downstream artifacts.
    artifact_names={entry['name']+'.step' for entry in RECORDS}
    artifact_names.update(entry['name']+'.stl' for entry in RECORDS if entry['printed'])
    artifact_names.update(('head-base-development-assembly.step','head-parameters.json',
                           'service-interfaces.json','guard-interfaces.json'))
    hashes={str(p.relative_to(ROOT.parent)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in OUT.glob('*') if p.name in artifact_names}
    report['artifact_sha256']=hashes
    (OUT/'head-validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('VALIDATED',len(RECORDS),'parts;',len(checks),'nominal pairs;',len(issues),'issues',flush=True)
    if issues: raise SystemExit(1)

if __name__=='__main__':
    statepath=OUT/'build-state.json'
    state={'status':'BUILDING','source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
           'timestamp_utc':datetime.now(timezone.utc).isoformat()}
    statepath.write_text(json.dumps(state,indent=2)+'\n')
    try:
        main();state['status']='PASS'
    except BaseException as exc:
        state['status']='FAILED';state['failure']=str(exc);raise
    finally:
        state['finished_utc']=datetime.now(timezone.utc).isoformat()
        statepath.write_text(json.dumps(state,indent=2)+'\n')
