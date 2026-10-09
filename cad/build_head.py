"""Windflow Rev B parametric housing development model, millimetres.

Airflow +Y; X width; Z vertical. The final nozzle belongs to the two structural
head halves. This script creates real B-reps/STLs; its development status and
checks are written alongside the exports. Run after build_prototypes.py.
"""
from pathlib import Path
import json, math, os, sys, hashlib
from datetime import datetime, timezone
import cadquery as cq
import fan_mount_layout
import grille_interlock_study

ROOT=Path(__file__).resolve().parent
P=json.loads((ROOT/'parameters.json').read_text())
OUT=ROOT/'rev_b'; OUT.mkdir(exist_ok=True)
W,H,L=P['outlet_width'],P['outlet_height'],P['panel_length']
T=P['wall']; R=P['throat_diameter']/2; BR=P['bellmouth_radius']
HINGE=90.; FAN_END=27.; records=[]; parts={}

def box(w,d,h,x=0,y=0,z=0):
    return cq.Workplane('XY').box(w,d,h).translate((x,y,z)).val()
def cy(r,y,length,x=0,z=0):
    return cq.Solid.makeCylinder(r,length,cq.Vector(x,y,z),cq.Vector(0,1,0))
def cx(r,x,length,y=0,z=0):
    return cq.Solid.makeCylinder(r,length,cq.Vector(x,y,z),cq.Vector(1,0,0))
def cz(r,z,length,x=0,y=0):
    return cq.Solid.makeCylinder(r,length,cq.Vector(x,y,z),cq.Vector(0,0,1))
def rr(w,h,r,y):
    a,b=w/2,h/2; k=math.sqrt(.5)
    p=cq.Workplane(cq.Plane(origin=(0,y,0),xDir=(1,0,0),normal=(0,-1,0)))
    return (p.moveTo(-a+r,-b).lineTo(a-r,-b)
      .threePointArc((a-r+r*k,-b+r-r*k),(a,-b+r)).lineTo(a,b-r)
      .threePointArc((a-r+r*k,b-r+r*k),(a-r,b)).lineTo(-a+r,b)
      .threePointArc((-a+r-r*k,b-r+r*k),(-a,b-r)).lineTo(-a,-b+r)
      .threePointArc((-a+r-r*k,-b+r-r*k),(-a+r,-b)).close().val())
def rrsolid(w,h,r,y0,y1):
    return cq.Solid.makeLoft([rr(w,h,r,y0),rr(w,h,r,y1)],True)
def circlewire(radius,y):
    return cq.Wire.makeCircle(radius,cq.Vector(0,y,0),cq.Vector(0,1,0))

def segmented_circle(radius,y):
    # Eight exact circular arcs match the eight rounded-rectangle edges without
    # the 0.02 mm straight edges of an almost-circular rounded rectangle. Those
    # sliver surfaces passed OCP but made both housing halves faulty in Onshape.
    angles=(-100,-80,-10,10,80,100,170,190,260)
    def point(a):
        a=math.radians(a)
        return cq.Vector(radius*math.cos(a),y,radius*math.sin(a))
    return cq.Wire.assembleEdges([cq.Edge.makeThreePointArc(point(a),point((a+b)/2),point(b))
        for a,b in zip(angles[:-1],angles[1:])])

def nut_y(x,z,y,length,across_flats=4.25):
    # M2 nut pocket; flats dimension includes a small printing allowance.
    return cq.Workplane(cq.Plane(origin=(x,y,z),xDir=(1,0,0),normal=(0,1,0))).polygon(6,across_flats/math.cos(math.pi/6)).extrude(length).val()
def save(name,shape,material='PETG',printable=True):
    assert shape.isValid(), name+' invalid'
    assert len(shape.Solids())==1, (name,len(shape.Solids()))
    assert shape.Volume()>0,name
    cq.exporters.export(shape,str(OUT/(name+'.step')))
    if printable: cq.exporters.export(shape,str(OUT/(name+'.stl')),tolerance=.055,angularTolerance=.12)
    b=shape.BoundingBox()
    records.append(dict(name=name,valid=True,solids=1,bounds_mm=[b.xlen,b.ylen,b.zlen],volume_mm3=shape.Volume(),material=material))
    parts[name]=shape
    print('EXPORTED '+name,flush=True)
    return shape

# Native loft stations define the head, avoiding a tight 90-degree airflow bend.
outer=cq.Solid.makeLoft([rr(132,132,8,0),rr(132,132,8,29),
    rr(W+2*T,H+2*(T+P['panel_thickness']+.4),4,HINGE)],True)
fan_bay=rrsolid(120.6,120.6,2,-1,29.01)
throat=cy(R,28.99,31.01)
transition=cq.Solid.makeLoft([segmented_circle(R,60),rr(W,H,3,HINGE+.02)],True)
head=outer.cut(fan_bay).cut(throat).cut(transition)

# Join the physically checked mechanism frame to the same structural housing.
frame_path=ROOT/'prototypes/nozzle-test-frame.step'
frame=cq.importers.importStep(str(frame_path)).val().translate((0,HINGE,0))
head=head.fuse(frame).cut(transition).clean()

# Four M3 fan screws enter from the rear into replaceable insert bosses.
# The original Noctua silicone pads remain; 2 mm TPU pads add compliance.
for x in (-52.5,52.5):
    for z in (-52.5,52.5):
        head=head.fuse(cy(6.8,29,8,x,z))
        head=head.cut(cy(2.0,28.9,6.9,x,z))

# Six seam joints lie outside the air passage; right-side heat-set inserts.
seams=[]
for y in (18.,53.,116.):
    outer_h=132 if y<=29 else (132+(H+2*(T+P['panel_thickness']+.4)-132)*min(1,(y-29)/61))
    for sign in (-1,1):
        z=sign*(outer_h/2+1.5); seams.append((y,z))
        head=head.fuse(cx(4.2,-9,18,y,z))

# Main head/base structural attachment ears, accessible before bottom cover.
for x in (-44,44):
    for y in (20,72):
        ear=box(12,14,19 if y>50 else 10,x,y,-62.5 if y>50 else -67)
        head=head.fuse(ear).cut(cz(2.0,-72.1,6.9,x,y))

# Pressure tap upstream of nozzle; flush 1 mm bore, tube socket outside airflow.
head=head.fuse(cx(3.8,-65,8,65,0)).cut(cx(.5,-66,14,65,0))
head=head.cut(cx(1.65,-65.1,5.0,65,0))

# M3 rear inlet fasteners: axial inserts accessible from the rear face.
for x in (-62.,62.):
    for z in (-62.,62.):
        head=head.fuse(cy(4,0,9,x,z)).cut(cy(2.,-.1,6.9,x,z))

# Re-trim mounting additions against the defined passage, then split for assembly.
head=head.cut(fan_bay).cut(throat).cut(transition).clean()
# The newly joined upstream housing also needs the knuckle clearance cuts.
for z in (-H/2,H/2):
    head=head.cut(cx(3.1,-W/2+P['panel_side_clearance']-.1,W+26,HINGE,z))
    head=head.cut(box(W+26,7,6.2,13,HINGE-3.5,z))
    # The housing union must preserve the full metal shaft bore and left collar
    # clearance, including the short length outside the panel's plastic knuckle.
    head=head.cut(cx(1.65,-62,160,HINGE,z))
    head=head.cut(cx(3.8,-61,6.5,HINGE,z))
# Guard ring captured in a clamshell seat; rear ring captures the stator insert.
head=head.cut(cy(R-.2,60.9,2.6))
head=head.fuse(cy(R+.5,41,1).cut(cy(R-1.7,40.9,1.2)))
# Front magnet cups are open from the front for polarity checking and adhesive.
# A separate thin screw-retained rim closes all four cups; no trapped magnets.
magnet_centres=[(x,z) for x in (-W/2-4.1,W/2+4.1) for z in (-H/2-4.1,H/2+4.1)]
keeper_screws=[(x,z) for x in (-W/2-4.5,W/2+4.5) for z in (-33.,33.)]
grille_screws=[(x,z) for x in (-W/2-4.5,W/2+4.5) for z in (-20.,20.)]
for x,z in magnet_centres:
    head=head.fuse(cy(5.1,142,8.2,x,z)).cut(cy(P['magnet_pocket_diameter']/2,146.8,3.5,x,z))
for x,z in keeper_screws:
    head=head.fuse(cy(3.5,142.8,7.4,x,z)).cut(cy(1.15,142.7,7.6,x,z))
    head=head.cut(nut_y(x,z,142.7,2.0))
# Clearance for the ends of the separate grille-cover screws when grille is on.
for x,z in grille_screws: head=head.cut(cy(1.8,149.1,1.3,x,z))
# Keep magnet cups out of the open panel-tip envelope as well as the boost pose.
for sign in (-1,1):
    head=head.cut(box(W-2*P['panel_side_clearance']+.4,L+.5,3.9,0,HINGE+(L+.5)/2,sign*(H/2+.65)))

# Four outboard supports hold a screw-removable linkage cover. Front supports
# start outside X=52.2 and the open-panel air surface; their Y=112 location is
# beyond the translating yoke/guide region. Rear supports join the solid shell.
cover_mounts=[]
for sign in (-1,1):
    for y in (37.,112.):
        z=sign*58.;cover_mounts.append((y,z))
        head=head.fuse(box(48 if y==37 else 52,8,12,80.2 if y==37 else 78.2,y,z))
        if y==112:head=head.fuse(box(5.4,8,16.5,54.9,y,sign*55.75))
        head=head.cut(cx(2.0,97.4,6.9,y,z))
# Cut into assembly halves only after the integral nozzle/frame is joined.
left=head.intersect(box(400,500,500,-200,50,0))
right=head.intersect(box(400,500,500,200,50,0))
for y,z in seams:
    left=left.cut(cx(1.65,-10,10.05,y,z)).cut(cx(3.1,-10,3.2,y,z))
    right=right.cut(cx(2.0,-.05,6.85,y,z))
# Same-domain face unification creates invalid trimming on the intersecting
# collar reliefs in this OCP version. The pre-unification solids are valid;
# retain those exact boolean results and still apply every validity assertion.
# Save the structural halves after adding the grille switch interface below.

# Outward-removable cover with an open inner face around the parent duct. Moving
# hardware stays inside the 2.4 mm shell. Print on its broad outside X face; it
# slides off to +X for access to shafts, clamps, horn and bracket screws.
cover=box(53.2,96,165,80.1,71,.9).cut(box(48.4,91.2,160.2,80.1,71,.9))
# Leave the complete inward X face open so the cover can withdraw to +X
# around the tall yoke; a closed inner wall would trap the assembled linkage.
cover=cover.cut(box(2.5,98,167,54.7,71,.9))
cover_clear=cq.Solid.makeLoft([rr(133.2,133.2,8,22.9),rr(133.2,133.2,8,28.9),
    rr(W+2*T+1.2,H+2*(T+P['panel_thickness']+.4)+1.2,4,HINGE)],True)
cover_clear=cover_clear.fuse(rrsolid(W+2*T+1.2,H+2*(T+P['panel_thickness']+.4)+1.2,4,HINGE,120))
cover=cover.cut(cover_clear)
for y,z in cover_mounts:
    cover=cover.cut(cx(1.65,104.2,2.6,y,z))
    # Front mounting webs cross the cover's inner wall through fitted reliefs.
    if y==112:cover=cover.cut(box(6.2,8.6,17.1,54.9,y,math.copysign(55.75,z)))
# Harness exits under the servo, clear of rod, yoke and panel sweeps. The fitted
# silicone grommet is slit so the original servo plug does not need removal.
cover=cover.cut(cz(3.2,-82,4,96,47))
save('linkage-service-cover',cover)
save('tpu-servo-cable-grommet',cz(4.2,-79.2,.8,96,47).fuse(cz(3.15,-81.6,2.4,96,47))
    .cut(cz(2,-81.7,3.5,96,47)).cut(box(.6,10,5,96,51,-81)),'TPU 95A')

# True quarter-circle bell-mouth cross-section, not an aesthetic edge fillet.
k=math.sqrt(.5)
bell=(cq.Workplane('XY').moveTo(R,0)
    .threePointArc((R+BR-BR*k,-BR*k),(R+BR,-BR))
    .lineTo(R+BR,-BR+T)
    .threePointArc((R+BR-(BR-T)*k,-(BR-T)*k),(R+T,0))
    .close().revolve(360,(0,0),(0,1)).val().translate((0,-T,0)))
plate=rrsolid(132,132,7,-T,0).cut(cy(R,-T-.1,T+.2))
bell=bell.fuse(plate)
for x in (-62.,62.):
    for z in (-62.,62.): bell=bell.cut(cy(1.65,-T-.1,T+.2,x,z))
bell=fan_mount_layout.reliefs(bell)
save('bellmouth-rear-inlet',bell.clean())

# Thin radial vanes are a replaceable comparison insert; no long honeycomb.
# All aerodynamic choices remain trial parameters until actual velocity mapping.
stator=cy(R-.3,42,P['stator_length']).cut(cy(R-1.5,41.9,P['stator_length']+.2))
hub=cy(7,42,P['stator_length']).cut(cy(5,41.9,P['stator_length']+.2))
stator=stator.fuse(hub)
for i in range(P['stator_vanes']):
    vane=box(R-7,P['stator_length'],P['stator_thickness'],(R+7)/2-.7,42+P['stator_length']/2,0)
    stator=stator.fuse(vane.rotate((0,0,0),(0,1,0),i*360/P['stator_vanes']))
save('radial-straightener-trial',stator.clean())
save('tpu-stator-axial-shim',cy(R-.4,60,1).cut(cy(R-1.7,59.9,1.2)),'TPU 95A')

# Fixed guard seats in the opened clamshell. Its ring is captured by the head,
# independent of the front cosmetic grille and guard-present switch.
def circular_guard(rad,y,depth):
    g=cy(rad,y,depth).cut(cy(rad-3,y-.1,depth+.2))
    clip=cy(rad-.2,y,depth)
    for x in range(-int(rad)+7,int(rad)-6,7): g=g.fuse(box(1.2,depth,2*rad,x,y+depth/2,0).intersect(clip))
    for z in (-25,0,25): g=g.fuse(box(2*rad,depth,1.2,0,y+depth/2,z).intersect(clip))
    return g.clean()
save('fixed-inner-finger-guard',circular_guard(R-.3,61,2.4))

# Fixed rear guard: long screws pass through its posts and bell-mouth into head.
# Flat rear face is the print-bed face; posts grow vertically without supports.
rear=circular_guard(R+BR+3,-29,2.4)
for x in (-62.,62.):
    for z in (-62.,62.):
        spoke=box(26,2.4,8,81, -27.8,0).rotate((0,0,0),(0,1,0),-math.degrees(math.atan2(z,x)))
        rear=rear.fuse(spoke).fuse(cy(4.2,-26.6,24.2,x,z))
        rear=rear.cut(cy(1.65,-29.1,27,x,z))
save('rear-inlet-finger-guard',rear.clean())

# Front grille: magnetic, 5.2 mm nominal clear rib spacing, removable for wiping.
g=rrsolid(W+18,H+18,6,151,154.8).cut(rrsolid(W,H,3,150.9,154.9))
clip=rrsolid(W+.1,H+.1,3,151,154)
for x in [i*6.4 for i in range(-8,9)]:
    g=g.fuse(box(1.2,3,H+.1,x,152.5,0).intersect(clip))
for z in (-24,0,24): g=g.fuse(box(W+.1,3,1.2,0,152.5,z).intersect(clip))
head_keeper=rrsolid(W+18,H+18,6,150.2,150.8).cut(rrsolid(W,H,3,150.1,150.9))
front_keeper=rrsolid(W+18,H+18,6,154.8,155.6).cut(rrsolid(W,H,3,154.7,155.7))
for x,z in magnet_centres:
    g=g.cut(cy(P['magnet_pocket_diameter']/2,151.4,3.5,x,z))
    save('REF-head-magnet-'+str(x)+'-'+str(z),cy(P['magnet_diameter']/2,146.9,P['magnet_depth'],x,z),'N42 magnet',False)
    save('REF-grille-magnet-'+str(x)+'-'+str(z),cy(P['magnet_diameter']/2,151.5,P['magnet_depth'],x,z),'N42 magnet',False)
for x,z in keeper_screws: head_keeper=head_keeper.cut(cy(1.2,150.1,.8,x,z))
for x,z in grille_screws:
    g=g.cut(cy(1.15,150.9,4,x,z)).cut(nut_y(x,z,150.9,1.9))
    front_keeper=front_keeper.cut(cy(1.2,154.7,1,x,z))
    head_keeper=head_keeper.cut(cy(1.8,150.1,.8,x,z))
interlock=grille_interlock_study.integrate_head_parts(left,g.clean(),head_keeper.clean(),0.)
left=interlock['head-left-integral-outlet']
g=interlock['magnetic-front-grille']
head_keeper=interlock['head-magnet-retaining-rim']
save('head-left-integral-outlet',left)
save('head-right-integral-outlet',right)
save('head-magnet-retaining-rim',head_keeper)
save('grille-magnet-retaining-rim',front_keeper.clean())
save('magnetic-front-grille',g)
for name,shape in interlock.items():
    if name in ('head-left-integral-outlet','magnetic-front-grille','head-magnet-retaining-rim'):continue
    save(name,shape,'TPU 95A' if 'tpu' in name else 'PETG')
for name,shape in grille_interlock_study.installed_reference_parts(0.).items():
    save(name,shape,'drawing/reference envelope',False)

# Separate printable TPU isolators and rigid compression limiters around M3.
save('tpu-fan-pad-m3',fan_mount_layout.free_pad(),'TPU 95A')
save('fan-compression-limiter-reference',fan_mount_layout.tube_reference(),'K&S 8128 brass',False)

checks={
    'head_halves_overlap_mm3':left.intersect(right).Volume(),
    'bellmouth_inner_radius_mm':BR,'inlet_mouth_diameter_mm':2*(R+BR),
    'throat_area_mm2':math.pi*R*R,'normal_outlet_gross_area_mm2':W*H,
    'minimum_outlet_gross_area_mm2':W*H*P['panel_min_area_ratio'],
    'max_panel_angle_deg':math.degrees(math.asin(H*(1-P['panel_min_area_ratio'])/(2*L))),
    'structural_seam_screws':len(seams),
    'grille_magnet_pairs':len(magnet_centres),
    'magnet_retention':'front-loaded pockets with screw-retained cover rims; adhesive removes rattle',
    'nominal_magnet_face_gap_mm':151.5-(146.9+P['magnet_depth']),
    'rear_guard_to_fan_rear_mm':26.6+fan_mount_layout.fan_rear_shift_mm(),
    'cover_screw_axes_local_yz_mm':cover_mounts,
    'head_center_height_mm':P['head_center_height'],
    'cover_fasteners':'4 x M3x8 into Ruthex RX-M3x5.7; verify insertion depth on coupon',
    'fan_mount_parameters':fan_mount_layout.parameters(),
}
assert checks['head_halves_overlap_mm3']<1e-5
assembly=cq.Assembly(name='Windflow Rev B housing development')
for name,s in parts.items():
    if name in ('tpu-fan-pad-m3','fan-compression-limiter-reference','interlock-tpu-wire-liner-free'):continue
    color=cq.Color(.12,.65,.68) if ('grille' in name or 'straightener' in name) else cq.Color(.32,.36,.42)
    assembly.add(s,name=name,color=color)
assembly.save(str(OUT/'housing-development.step'))
(OUT/'validation.json').write_text(json.dumps({'parts':records,'checks':checks,
    'build':{'completed_utc':datetime.now(timezone.utc).isoformat(),
      'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
      'fan_mount_layout_sha256':hashlib.sha256((ROOT/'fan_mount_layout.py').read_bytes()).hexdigest(),
      'fan_mount_parameters_sha256':hashlib.sha256((ROOT/'fan_mount_parameters.json').read_bytes()).hexdigest(),
      'interlock_script_sha256':hashlib.sha256((ROOT/'grille_interlock_study.py').read_bytes()).hexdigest(),
      'interlock_validation_sha256':hashlib.sha256((ROOT/'grille_interlock_study/validation.json').read_bytes()).hexdigest(),
      'parameters_sha256':hashlib.sha256((ROOT/'parameters.json').read_bytes()).hexdigest()},
    'status':'development, not print release',
    'assembly_files':[n+'.step' for n in parts if n not in ('tpu-fan-pad-m3','fan-compression-limiter-reference','interlock-tpu-wire-liner-free')],
    'remaining':['carrier PCB and wire/pressure-hose integration','whole-product interference and mechanism insertion checks',
        'grille interlock mounting','guard deflection and magnet pull testing',
        'full assembly sequence/tool clearance and physical trials',
        'native Onshape feature regeneration and integration']},indent=2))
print(json.dumps(checks,indent=2),flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
