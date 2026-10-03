"""Parametric fit coupons and two-panel mechanism fixture.

Local +Y is airflow and Y=0 is the panel hinge. The parent head integrates the
frame at its outlet; this is not a removable product nozzle. Purchased-component
envelopes are explicitly approximate and are never exported as printable STLs.
"""
from pathlib import Path
import json,math,os,sys,hashlib
from datetime import datetime,timezone
import cadquery as cq
R=Path(__file__).resolve().parent
P=json.loads((R/'parameters.json').read_text())
OUT=R/'prototypes';OUT.mkdir(exist_ok=True)
results=[]
def export(name,wp,printable=True,notes=None):
 s=wp.val() if isinstance(wp,cq.Workplane) else wp
 assert s.isValid(),name
 assert s.Volume()>0,name
 cq.exporters.export(s,str(OUT/(name+'.step')))
 if printable:cq.exporters.export(s,str(OUT/(name+'.stl')),tolerance=.06,angularTolerance=.1)
 b=s.BoundingBox();results.append({'part':name,'valid_solid':True,'solids':len(s.Solids()),'printable_custom_part':printable,'bbox_mm':[round(b.xlen,3),round(b.ylen,3),round(b.zlen,3)],'volume_mm3':round(s.Volume(),1),'notes':notes})
 return s
def box(x,y,z,pos=(0,0,0)):
 return cq.Workplane('XY').box(x,y,z).translate(pos)
def cyl_x(x,y,z,r,l):
 return cq.Workplane('YZ',origin=(x,y,z)).circle(r).extrude(l)

# Magnet fit coupon: three bore clearances, supported flat base, captive cover.
m=box(48,18,5,(0,0,2.5))
for x,d in zip((-15,0,15),(6.45,6.55,6.65)):
 m=m.cut(cq.Workplane('XY',origin=(x,0,1.6)).circle(d/2).extrude(3.4))
 m=m.cut(cq.Workplane('XY',origin=(x,6.4,0)).circle(1.65).extrude(5))
export('magnet-pocket-coupon',m)
keeper=box(48,18,.8,(0,0,.4))
for x in (-15,0,15):keeper=keeper.cut(cq.Workplane('XY',origin=(x,6.4,0)).circle(1.65).extrude(1))
export('magnet-keeper-coupon',keeper)

# LED channel uses maximum published board dimensions, not the smaller vendor STEP.
ch=box(60,15,12,(0,0,6)).cut(box(55,10.8,10.4,(0,0,6.8)))
ch=ch.cut(box(8,4,5,(29,0,3)))
export('led-channel-coupon',ch)
for t in (.6,.8,1.0):export('diffuser-'+str(t).replace('.','p'),box(55,10.7,t,(0,0,t/2)))

# PETG mount panel with M7 clearance and two frame screws; shaft axis horizontal in use.
mount=box(34,28,2.4,(0,0,1.2)).cut(cq.Workplane('XY').circle(3.65).extrude(3))
for x in (-12,12):mount=mount.cut(cq.Workplane('XY',origin=(x,0,0)).circle(1.65).extrude(3))
export('encoder-mount-coupon',mount)
for clear in (.05,.15,.25):
 d=6+clear;flat=1.5+clear/2
 bore=cq.Workplane('XY').circle(d/2).extrude(8).intersect(box(12,6,9,(0,flat-3,4)))
 wheel=cq.Workplane('XY').circle(15).extrude(8).cut(bore)
 # Rounded scallops keep texture printable without unsupported knurl teeth.
 for i in range(36):
  a=math.tau*i/36
  wheel=wheel.cut(cq.Workplane('XY',origin=(15.4*math.cos(a),15.4*math.sin(a),0)).circle(.7).extrude(8))
 export('encoder-wheel-clearance-'+str(clear).replace('.','p'),wheel)

# TPU replaceable sandwich washer + radial bushing; rigid spacer limits compression.
pad=cq.Workplane('XY').circle(7).circle(2.15).extrude(2)
export('tpu-fan-pad',pad)
bush=cq.Workplane('XY').circle(4).circle(2.15).extrude(3)
bush=bush.union(cq.Workplane('XY',origin=(0,0,3)).circle(7).circle(2.15).extrude(1.2))
export('tpu-bushing-coupon',bush)

# Insert-hole coupon leaves 1.2mm floor below 6.8mm blind pilot holes.
ins=box(50,16,8,(0,0,4))
for x,d in zip((-16,0,16),(3.8,4.0,4.2)):
 ins=ins.cut(cq.Workplane('XY',origin=(x,0,1.2)).circle(d/2).extrude(6.8))
export('m3-insert-coupon',ins)

# Horizontal hinge bores reproduce the bridge roof in an edge-printed panel.
hinge_fit=box(18,46,2,(0,0,1))
for y,d in zip((-15,0,15),(3.15,3.30,3.45)):
 hinge_fit=hinge_fit.union(box(18,14,8,(0,y,6)))
 hinge_fit=hinge_fit.cut(cyl_x(-10,y,6,d/2,20))
export('horizontal-hinge-bore-coupon',hinge_fit)
slot_fit=cq.Workplane('YZ').rect(12,42).extrude(4)
for z,w in zip((-12,0,12),(3.2,3.4,3.6)):
 slot_fit=slot_fit.cut(cq.Workplane('YZ',origin=(-1,0,z)).slot2D(5,w,90).extrude(6))
export('yoke-slot-width-coupon',slot_fit)

# Nozzle test frame: airflow +Y, width X, height Z; hinges at Y=0, Z=+/-47.
# Keep controls outside the parent's maximum X=66 head wall. This local offset was
# agreed with the parent integration task; aerodynamic parameters remain shared.
OUTBOARD=17.0
W,H,L=P['outlet_width'],P['outlet_height'],P['panel_length']
wall=P['wall'];gap=P['panel_side_clearance'];th=P['panel_thickness']
cr=P['yoke_crank_radius'];sr=P['servo_crank_radius'];rl=P['servo_rod_length']
a_max=math.asin(H*(1-P['panel_min_area_ratio'])/(2*L))
stroke_max=cr*math.sin(a_max)
frame=box(W+2*wall,L+10,H+2*(wall+th+.4),(0,L/2,0)).cut(box(W,L+12,H,(0,L/2,0)))
for z in (-H/2,H/2):
 frame=frame.cut(box(W-2*gap+.2,L+7,2*(th+.4),(0,L/2,z)))
for x in (-W/2-wall/2,W/2+wall/2):
 for z in (-H/2,H/2):
  frame=frame.union(box(wall,10,10,(x,0,z)))
  frame=frame.cut(cyl_x(-W/2-wall-1,0,z,1.65,W+2*wall+OUTBOARD+20))
for z in (-H/2,H/2):
 frame=frame.cut(cyl_x(-W/2+gap-.1,0,z,3.1,W+wall+OUTBOARD+12))
 frame=frame.cut(box(W+wall+OUTBOARD+12,7,6.2,((wall+OUTBOARD)/2+6,-3.5,z)))
 # Bearing arm stays upstream of the rotating knuckle; no enclosed insertion trap.
 frame=frame.union(box(17+OUTBOARD,3,14,(62.5+OUTBOARD/2,-8.5,z)))
 # Connect the upstream arm to the duct wall; the earlier fixture had two loose
 # bearing supports because its arm ended 2 mm behind the duct body.
 frame=frame.union(box(5.3,14,14,(56.85,-3,z)))
 frame=frame.cut(cyl_x(53,0,z,3.1,7))
 frame=frame.union(box(3,20,14,(69.5+OUTBOARD,0,z)))
 frame=frame.cut(cyl_x(67+OUTBOARD,0,z,1.65,6))

panel=box(W-2*gap,L,th,(0,L/2,th/2))
knuckle=cyl_x(-W/2+gap,0,0,2.8,W/2-gap+60+OUTBOARD)
knuckle=knuckle.cut(cyl_x(-W/2+gap-1,0,0,1.65,W+OUTBOARD+20))
# The last 4 mm is a double-flat drive key. A separate clamping crank can pass
# the outboard bearing before sliding onto it; the panel itself passes the seam.
key_x=56+OUTBOARD
for z in (-5,5):knuckle=knuckle.cut(box(4.01,12,5.2,(key_x+2.005,0,z)))
crank=cq.Workplane('YZ').circle(6).extrude(4)
crank=crank.union(cq.Workplane('YZ',origin=(0,0,cr/2)).rect(8,cr).extrude(4))
crank=crank.union(cyl_x(0,0,cr,4,4))
crank=crank.union(box(4,7,10,(2,6.5,0)))
key_socket=cyl_x(-1,0,0,2.925,6).intersect(box(8,12,5.05,(2,0,0)))
crank=crank.cut(key_socket).cut(cyl_x(-1,0,cr,1.65,6))
# Split clamp removes double-flat backlash. M2 x 16 screw and M2 locknut clamp
# through Z, outside the key. Tighten only to eliminate play, never crush the key.
crank=crank.cut(box(6,11,.8,(2,5.5,0)))
crank=crank.cut(cq.Workplane('XY',origin=(2,7.5,-6)).circle(1.1).extrude(12))
export('yoke-crank-coupon',crank,notes='Separate double-flat split-clamp crank. M2 clamp fastener eliminates printed-fit backlash; verify key strength and free hinge motion.')
export('boost-panel-keyed-crank',crank)
clamp_screw=cq.Workplane('XY',origin=(2,7.5,-10.65)).circle(1).extrude(16)
clamp_screw=clamp_screw.union(cq.Workplane('XY',origin=(2,7.5,5.35)).circle(1.9).extrude(2))
clamp_nut=cq.Workplane('XY',origin=(2,7.5,-8.15)).polygon(6,4/math.cos(math.pi/6)).extrude(2.8)
clamp_nut=clamp_nut.cut(cq.Workplane('XY',origin=(2,7.5,-8.2)).circle(1).extrude(3))
for z in (-5.35,5):
 clamp_screw=clamp_screw.union(cq.Workplane('XY',origin=(2,7.5,z)).circle(2.5).circle(1.1).extrude(.35))
clamp_hardware=cq.Compound.makeCompound([clamp_screw.val(),clamp_nut.val()])
export('REF-M2x16-crank-clamp-stack',clamp_hardware,False,'M2 x 16 DIN 912 screw and M2 DIN 985 nut envelopes; no threads. Tighten lightly to remove backlash with shaft present.')
panel=panel.union(knuckle).cut(cyl_x(-W/2+gap-1,0,0,1.65,W+OUTBOARD+20))
export('boost-panel-upper-test',panel)
export('boost-panel-lower-test',panel.mirror('XY'))
key_coupon=cyl_x(0,0,0,2.8,12).cut(cyl_x(-1,0,0,1.65,14))
for z in (-5,5):key_coupon=key_coupon.cut(box(4.01,12,5.2,(10.005,0,z)))
export('panel-key-clamp-coupon',key_coupon,notes='Insert 3 mm steel shaft before tightening crank; confirm no crack, backlash or shaft binding.')

# A single centre drive hole avoids the two guide tunnels at Z=+/-30.
yoke=cq.Workplane('YZ').rect(10,H+2*cr+12).extrude(4)
for z in (-H/2,H/2):
 # A forward bridge preserves a strong web without occupying the upstream
 # bearing-arm volume. The clearance notch opens toward -Y.
 yoke=yoke.union(box(4,13.4,16,(2,1.7,z)))
 yoke=yoke.cut(cq.Workplane('YZ',origin=(-1,-stroke_max/2,z)).slot2D(stroke_max+7.6,7.6,0).extrude(6))
for z in (-H/2-cr,H/2+cr):
 yoke=yoke.cut(cq.Workplane('YZ',origin=(-1,0,z)).slot2D(P['yoke_slot_length'],P['yoke_slot_width'],90).extrude(6))
yoke=yoke.cut(cyl_x(-1,0,0,1.65,6))
export('sliding-yoke-coupon',yoke)
for z in (-30,30):
 guide=box(8,stroke_max+15,8,(62.5+OUTBOARD,stroke_max/2,z))
 guide=guide.cut(box(4.6,stroke_max+10.6,10,(62.5+OUTBOARD,stroke_max/2,z)))
 frame=frame.union(guide).union(box(4.8+OUTBOARD,8,8,(56.6+OUTBOARD/2,0,z)))

# Removable servo mount: two M3 screws insert from the outside in X. An L-shaped
# frame arm reaches around the slider's upstream stop, so it cannot obstruct it.
frame=frame.union(box(13.8+OUTBOARD,11.6,20,(61.1+OUTBOARD/2,-11.2,-27)))
frame=frame.union(box(5.3+OUTBOARD,9.5,20,(56.85+OUTBOARD/2,-.75,-27)))
for z in (-22,-32):
 # 4 mm pilot is a coupon-selected starting point for RX-M3x5.7 inserts.
 frame=frame.cut(cyl_x(61.2+OUTBOARD,-11.5,z,2.0,6.9))

# Selected servo dimensions are documented, but this placement uses an unverified
# FS90 family shaft offset of 5.4 mm and flange datum of 10.9 mm below the output.
# Long slots and a body clearance window permit adjustment after measuring FS90-FB.
sx=55+OUTBOARD;sy=-rl;sz=-sr
case_y=sy-5.4;mount_x=68.3+OUTBOARD
servo_body=box(22,23.2,12.5,(71.3+OUTBOARD,case_y,sz))
servo_lugs=box(2.4,32.6,11.8,(67.1+OUTBOARD,case_y,sz))
for y in (case_y-13.5,case_y+13.5):servo_lugs=servo_lugs.cut(cyl_x(65+OUTBOARD,y,sz,1.0,4))
servo_env=servo_body.union(servo_lugs).union(cyl_x(sx,sy,sz,3.0,5.3))
export('REF-FS90-FB-approximate-envelope',servo_env,False,'Approximate family envelope only: measure purchased feedback variant and output/horn before mount release.')
bracket=box(3,44,22,(mount_x+1.5,case_y,sz))
bracket=bracket.cut(box(5,24.2,13.5,(mount_x+1.5,case_y,sz)))
for y in (case_y-13.5,case_y+13.5):
 bracket=bracket.cut(cq.Workplane('YZ',origin=(mount_x-1,y,sz)).slot2D(5.8,2.6,0).extrude(5))
bracket=bracket.union(box(3,42,6,(mount_x+1.5,case_y+12,-23)))
bracket=bracket.union(box(3,10,20,(mount_x+1.5,-11.5,-27)))
for z in (-22,-32):bracket=bracket.cut(cyl_x(mount_x-1,-11.5,z,1.65,5))
export('servo-slotted-bracket',bracket,notes='Family-datum mount study. Slots allow about +/-1.6 mm Y adjustment with M2 screws; verify X/Z datum on FS90-FB.')

rod=cq.Workplane('YZ',origin=(0,rl/2,0)).slot2D(rl+8,8,0).extrude(4)
for y in (0,rl):rod=rod.cut(cyl_x(-1,y,0,1.65,6))
export('servo-connecting-rod',rod)
# The supplied servo horn is represented for swept-envelope clearance only. Use
# its moulded spline and centre screw; do not print a guessed replacement spline.
horn=cq.Workplane('YZ',origin=(0,0,sr/2)).slot2D(sr+8,8,90).extrude(3)
horn=horn.cut(cyl_x(-1,0,sr,1.65,5))
export('REF-supplied-servo-horn-envelope',horn,False,'Approximate trimmed supplied horn, 10 mm pin radius, no spline detail.')
export('nozzle-test-frame',frame)
assert len(frame.val().Solids())==1,'Fixture frame must be one connected solid'

# Smooth sleeves keep screw threads off the printed slots/bores. The sleeve is
# clamped between M2 washers; its axial length leaves printed eyes free to pivot.
def sleeve(x,y,z,length):return cyl_x(x,y,z,1.5,length).cut(cyl_x(x-1,y,z,1.05,length+2))
def pin_stack(x,y,z,length,screw_length=14):
 # K&S 3921 tube 3 OD / 2.1 ID, Accu HPW-M2-A2 washers at maximum .35
 # thickness, SSC-M2-L-A2 cap screw and HNN-M2-A2 nut maximum 2.8 high.
 # Sleeve ends project beyond the printed faces; washers never clamp plastic.
 parts=[sleeve(x,y,z,length).val()]
 for wx in (x-.35,x+length):
  parts.append(cyl_x(wx,y,z,2.5,.35).cut(cyl_x(wx-.1,y,z,1.1,.55)).val())
 parts.append(cyl_x(x-.35,y,z,1,screw_length).union(cyl_x(x-2.35,y,z,1.9,2)).val())
 nut=cq.Workplane('YZ',origin=(x+length+.35,y,z)).polygon(6,4/math.cos(math.pi/6)).extrude(2.8)
 parts.append(nut.cut(cyl_x(x+length+.25,y,z,1,3)).val())
 assert screw_length-length-.7-2.8>=.4,'At least one M2 thread pitch beyond nut'
 return cq.Compound.makeCompound(parts)

def solve(fraction):
 a=a_max*fraction;stroke=cr*math.sin(a);lo,hi=0,math.pi/3
 for _ in range(52):
  phi=(lo+hi)/2
  travel=-rl+sr*math.sin(phi)+math.sqrt(rl*rl-(sr*(math.cos(phi)-1))**2)
  if travel<stroke:lo=phi
  else:hi=phi
 phi=(lo+hi)/2
 end_y=sy+sr*math.sin(phi);end_z=sz+sr*math.cos(phi)
 rod_angle=math.atan2(-end_z,stroke-end_y)
 assert abs(math.hypot(stroke-end_y,-end_z)-rl)<1e-9
 upper=panel.rotate((0,0,0),(1,0,0),-math.degrees(a)).translate((0,0,H/2)).val()
 lower=panel.mirror('XY').rotate((0,0,0),(1,0,0),math.degrees(a)).translate((0,0,-H/2)).val()
 upper_crank=crank.translate((key_x,0,0)).rotate((0,0,0),(1,0,0),-math.degrees(a)).translate((0,0,H/2)).val()
 lower_crank=crank.mirror('XY').translate((key_x,0,0)).rotate((0,0,0),(1,0,0),math.degrees(a)).translate((0,0,-H/2)).val()
 upper_clamp=clamp_hardware.translate((key_x,0,0)).rotate((0,0,0),(1,0,0),-math.degrees(a)).translate((0,0,H/2))
 lower_clamp=clamp_hardware.mirror('XY').translate((key_x,0,0)).rotate((0,0,0),(1,0,0),math.degrees(a)).translate((0,0,-H/2))
 slider=yoke.translate((60.5+OUTBOARD,stroke,0)).val()
 moving_rod=rod.rotate((0,0,0),(1,0,0),math.degrees(rod_angle)).translate((55.5+OUTBOARD,end_y,end_z)).val()
 moving_horn=horn.rotate((0,0,0),(1,0,0),-math.degrees(phi)).translate((51.5+OUTBOARD,sy,sz)).val()
 moving={'upper_panel':upper,'lower_panel':lower,'upper_crank':upper_crank,'lower_crank':lower_crank,'upper_clamp':upper_clamp,'lower_clamp':lower_clamp,'yoke':slider,'rod':moving_rod,'horn':moving_horn}
 for tag,sign in (('upper',1),('lower',-1)):
  moving[tag+'_crank_pin']=pin_stack(72.7,stroke,sign*(H/2+cr*math.cos(a)),9.1)
 moving['rod_yoke_pin']=pin_stack(72.2,stroke,0,9.6)
 moving['horn_rod_pin']=pin_stack(68.2,end_y,end_z,8.6)
 return moving, {'fraction':fraction,'panel_angle_deg':math.degrees(a),'area_ratio_gross':(H-2*L*math.sin(a))/H,'yoke_stroke_mm':stroke,'servo_angle_deg':math.degrees(phi),'rod_angle_deg':math.degrees(rod_angle)}

fixed={'frame':frame.val(),'servo_bracket':bracket.val(),'servo_approximate':servo_env.val()}
# Fixed shafts are retained by real, documented DIN 705 collars outside bearings.
# The 7.6 mm spacer limits crank axial motion to 0.4 mm, preserving key engagement.
spacer=cyl_x(0,0,0,3.5,7.6).cut(cyl_x(-1,0,0,1.65,9.6))
export('crank-retaining-spacer',spacer)
collar=cyl_x(0,0,0,3.5,5).cut(cyl_x(-1,0,0,1.5,7))
export('REF-Maedler-62300300-collar-envelope',collar,False,'Manufacturer dimensions: 3 mm bore, 7 mm OD, 5 mm width, M2 x 3 set screw. Simplified envelope, not vendor CAD.')
shaft=cyl_x(-60.5,0,0,1.5,155)
export('REF-3mm-hinge-shaft-155mm',shaft,False,'Cut straight 3 mm ground steel rod to 155 mm; deburr ends. Two required.')
for tag,z in (('upper',H/2),('lower',-H/2)):
 fixed[tag+'_shaft']=shaft.translate((0,0,z)).val()
 fixed[tag+'_retaining_spacer']=spacer.translate((77.2,0,z)).val()
 fixed[tag+'_left_collar']=collar.translate((-59.7,0,z)).val()
 fixed[tag+'_right_collar']=collar.translate((88.3,0,z)).val()
def overlaps(a,b):
 aa,bb=a.BoundingBox(),b.BoundingBox()
 if any(getattr(aa,k+'max')<=getattr(bb,k+'min')+1e-7 or getattr(bb,k+'max')<=getattr(aa,k+'min')+1e-7 for k in 'xyz'):return 0.0
 return max(0.0,a.intersect(b).Volume())

# Run check_mechanism_insertion.py after regenerating the parent head.

# Sweep all 61 nominal poses against fixed objects and all non-mating moving parts.
# Tube/pin/shaft joints are intentionally in bores and are checked separately by
# nominal diametral/axial clearances rather than reported as interfering solids.
states=[];collision_pairs={};max_overlap=0.0
for i in range(61):
 moving,state=solve(i/60)
 all_pairs=[(n,s,fn,fs) for n,s in moving.items() for fn,fs in fixed.items()]
 items=list(moving.items())
 all_pairs += [(n,s,n2,s2) for j,(n,s) in enumerate(items) for n2,s2 in items[j+1:]]
 for n,s,n2,s2 in all_pairs:
  # Horn attaches to the servo output; the supplier's approximate spline envelope
  # intentionally touches/enters its hub. The rod and body still get full checks.
  if n=='horn' and n2=='servo_approximate':continue
  volume=overlaps(s,s2);key=n+' / '+n2
  collision_pairs[key]=max(collision_pairs.get(key,0.0),volume)
  max_overlap=max(max_overlap,volume)
  assert volume<1e-5,('collision',i,n,n2,volume)
 state['maximum_unintended_overlap_mm3']=max(collision_pairs.values())
 states.append(state)
 if i%15==0:print('Sweep',i,'/60 passed',flush=True)
for name,s in fixed.items():
 for other,ss in fixed.items():
  if name>=other:continue
  volume=overlaps(s,ss)
  assert volume<1e-5,('fixed collision',name,other,volume)
  collision_pairs[name+' / '+other]=volume

moving,closed=solve(1.0)
assembly=cq.Assembly(name='Windflow progressive nozzle fixture - maximum nominal boost')
colors={'frame':(.23,.26,.30),'servo_bracket':(.5,.58,.64),'servo_approximate':(.15,.30,.55),'upper_panel':(.05,.7,.8),'lower_panel':(.05,.7,.8),'upper_crank':(.2,.75,.65),'lower_crank':(.2,.75,.65),'yoke':(.95,.55,.15),'rod':(.9,.73,.2),'horn':(.87,.87,.9)}
for name in fixed:colors.setdefault(name,(.72,.73,.75))
for name in moving:colors.setdefault(name,(.72,.73,.75))
for name,s in {**fixed,**moving}.items():assembly.add(s,name=name,color=cq.Color(*colors[name]))
assembly.save(str(OUT/'nozzle-mechanism-study.step'))
for name,s in moving.items():cq.exporters.export(s,str(OUT/('installed-'+name+'-max-boost.step')))
open_moving,_=solve(0)
for name,s in open_moving.items():cq.exporters.export(s,str(OUT/('installed-'+name+'-open.step')))
for name,s in fixed.items():
 if name not in ('frame','servo_bracket','servo_approximate'):cq.exporters.export(s,str(OUT/('installed-'+name+'.step')))

mechanical_angle=math.asin((stroke_max+.3)/cr)
dp=24.0;panel_force=dp*(W-2*gap)/1000*L/1000
panel_moment=panel_force*L/2000
phi=math.radians(closed['servo_angle_deg'])
dydphi=sr*math.cos(phi)+(sr*sr*(math.cos(phi)-1)*math.sin(phi))/math.sqrt(rl*rl-(sr*(math.cos(phi)-1))**2)
yoke_force=2*panel_moment/(cr/1000*math.cos(a_max))
report={'parts':results,'coordinate_system':{'airflow':'+Y','hinges_mm':[[0,0,H/2],[0,0,-H/2]],'parent_head_translation_mm':[0,90,P['head_center_height']],'mechanism_outboard_offset_mm':OUTBOARD,'rightmost_servo_envelope_x_mm':82.3+OUTBOARD},'kinematics':states,'collision_sweep':{'poses':len(states),'angular_step_deg':math.degrees(a_max)/60,'pair_maximum_overlap_mm3':collision_pairs,'maximum_unintended_overlap_mm3':max_overlap,'excluded_mating_pair':'servo horn / approximate servo output only','bounds':'nominal solids only; not elastic deformation, tolerance extremes, harness, or parent enclosure'},'clearances_mm':{'panel_each_side':gap,'hinge_pin_diametral':.3,'slot_pin_diametral':.4,'yoke_each_side_in_x':.3,'yoke_end_stop_beyond_command':.3,'rod_to_parent_x66_wall':55.5+OUTBOARD-66,'rod_to_yoke_axial':1.0,'rod_to_servo_body_axial':.8,'body_window_each_side':.5,'frame_to_servo_bracket':.3},'mechanical_stop':{'panel_angle_deg':math.degrees(mechanical_angle),'gross_area_ratio':1-2*L*math.sin(mechanical_angle)/H,'note':'Guide ends stop yoke 0.3 mm beyond commanded travel. Software must not drive against these stops.'},'pressure_load_estimate':{'pressure_Pa':dp,'one_panel_force_N':panel_force,'one_panel_moment_Nm':panel_moment,'yoke_force_N':yoke_force,'servo_torque_Nm':yoke_force*dydphi/1000,'assumptions':'Uniform normal pressure; no hinge friction, gravity, inertial load or trapped object. Stall torque is not a continuous rating.'},'limitations':['FS90-FB envelope uses unverified family shaft/flange datums. Measure before printing the final servo bracket.','Frame is a mechanism fixture; parent assembly must union it into the non-removable outlet and repeat whole-assembly collisions.','Pressure estimate is not an airflow, noise or stability measurement.','Pins, spacers, screws and wire paths require physical assembly verification.','No measured airflow, noise, tolerance stack, wear or servo torque validation.']}
print(json.dumps({'parts_exported':len(results),'sweep_poses':len(states),'maximum_overlap_mm3':max_overlap,'maximum_boost':closed,'stop':report['mechanical_stop']},indent=2),flush=True)

# Render from the actual tessellated BReps, not an artistic illustration.
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
fig=plt.figure(figsize=(15,8.6),facecolor='#f4f6f8')
ax=fig.add_axes((.01,.10,.66,.78),projection='3d')
for name,s in {**fixed,**moving}.items():
 vertices,triangles=s.tessellate(.3,.25)
 xyz=[(v.x,v.y,v.z) for v in vertices]
 polys=[[xyz[j] for j in tri] for tri in triangles]
 ax.add_collection3d(Poly3DCollection(polys,facecolor=colors[name],edgecolor='none',alpha=.23 if name=='frame' else 1.0,rasterized=True))
ax.set(xlim=(-60,105),ylim=(-65,65),zlim=(-82,82),xlabel='X / width (mm)',ylabel='Y / airflow (mm)',zlabel='Z / height (mm)')
ax.set_box_aspect((165,130,164));ax.view_init(elev=20,azim=-45)
ax.set_facecolor('#f4f6f8');ax.grid(False)
fig.text(.05,.93,'WINDFLOW / progressive nozzle mechanism',fontsize=22,weight='bold',color='#123244')
fig.text(.05,.887,'Actual CAD geometry at 75% gross outlet area · local prototype, dimensions in mm',fontsize=12,color='#466372')
side=fig.add_axes((.73,.54,.23,.30))
side.set_aspect('equal');side.set_xlim(-65,65);side.set_ylim(-82,82)
for sign in (-1,1):
 side.plot([0,L*math.cos(a_max)],[sign*H/2,sign*(H/2-L*math.sin(a_max))],color='#14a6bd',lw=4)
 side.plot([0,stroke_max],[sign*H/2,sign*(H/2+cr*math.cos(a_max))],color='#14a6bd',lw=3)
 side.plot([0,L],[sign*H/2,sign*H/2],color='#9cb9c3',lw=1,ls='--')
side.plot([stroke_max,stroke_max],[-77,77],color='#e5952d',lw=5)
end_y=sy+sr*math.sin(phi);end_z=sz+sr*math.cos(phi)
side.plot([sy,end_y],[sz,end_z],color='#67768a',lw=4)
side.plot([end_y,stroke_max],[end_z,0],color='#d1ac30',lw=4)
side.scatter([sy],[sz],color='#234e78',s=60)
side.annotate('Airflow',xy=(53,-15),xytext=(12,-15),arrowprops={'arrowstyle':'->','color':'#123244'},color='#123244',va='center')
side.set(xlabel='Y / airflow',ylabel='Z',title='Side view / linkage outside duct')
side.grid(alpha=.15)
fig.text(.72,.36,'12.34° panels / 31.04° servo\n5.13 mm yoke stroke / 35 mm rod\nInlet: 104 × 94 mm\nExit: 104 × 70.5 mm',fontsize=11,linespacing=1.6,color='#123244')
fig.text(.72,.17,'61 poses checked\n0 unintended solid overlap\n\nAdjustable FS90-FB mount uses a\nfamily envelope, not exact vendor CAD.',fontsize=10,linespacing=1.5,color='#466372')
fig.text(.05,.035,'Orange: sliding yoke  •  Cyan: converging panels  •  Yellow: drive rod  •  Blue: approximate servo\nThe final outlet is integral to the enclosure. Physical fit, wear and airflow testing remain necessary.',fontsize=10,color='#466372')
fig.savefig(OUT/'overview.png',dpi=150,facecolor=fig.get_facecolor());plt.close(fig)
assert (OUT/'overview.png').stat().st_size>10000
report['assembly_files']={'moving':list(moving),'fixed':list(fixed),'states':['open','max-boost'],'translation_to_parent':[0,90,P['head_center_height']]}
report['build']={'completed_utc':datetime.now(timezone.utc).isoformat(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'parameters_sha256':hashlib.sha256((R/'parameters.json').read_bytes()).hexdigest(),'overview_written':True}
(OUT/'validation.json').write_text(json.dumps(report,indent=2))
print('BUILD COMPLETE: STEP/STL, 61-pose sweep, validation.json and overview.png written.',flush=True)
# This local Windows OCP/VTK combination returns exit 1 during interpreter cleanup,
# even for an import-only process. All exports are closed and checked above; avoid
# its teardown after successful generation. Exceptions/assertions still exit nonzero.
sys.stdout.flush();sys.stderr.flush();os._exit(0)
