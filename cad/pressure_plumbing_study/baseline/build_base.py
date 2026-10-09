"""Parametric service base, IPS screen, ambient channel, encoder and board layout.

The carrier is an explicit reserved envelope, not a fabricated PCB. All purchased
models keep provenance names. Outputs are development geometry, not print release.
"""
from pathlib import Path
import json, math, os, sys, hashlib
from datetime import datetime, timezone
import cadquery as cq
import pico_mount
import encoder_layout
ROOT=Path(__file__).resolve().parent; OUT=ROOT/'rev_b'; OUT.mkdir(exist_ok=True)
parts={}; records=[]; fasteners=[]; mounts=[]; harness=[]
HEAD_Z=json.loads((ROOT/'parameters.json').read_text())['head_center_height']
def box(w,d,h,x=0,y=0,z=0):return cq.Workplane('XY').box(w,d,h).translate((x,y,z)).val()
def cz(r,z,l,x=0,y=0):return cq.Solid.makeCylinder(r,l,cq.Vector(x,y,z),cq.Vector(0,0,1))
def cx(r,x,l,y=0,z=0):return cq.Solid.makeCylinder(r,l,cq.Vector(x,y,z),cq.Vector(1,0,0))
def cy(r,y,l,x=0,z=0):return cq.Solid.makeCylinder(r,l,cq.Vector(x,y,z),cq.Vector(0,1,0))
def save(name,s,material='PETG',printable=True):
 assert s.isValid(),name
 assert len(s.Solids())==1,(name,len(s.Solids()))
 cq.exporters.export(s,str(OUT/(name+'.step')))
 if printable:cq.exporters.export(s,str(OUT/(name+'.stl')),tolerance=.06,angularTolerance=.12)
 parts[name]=s;b=s.BoundingBox();records.append({'name':name,'valid':True,'solids':1,'material':material,'bounds_mm':[b.xlen,b.ylen,b.zlen]})
 print('EXPORTED '+name,flush=True)
 return s
def vendor(name,file,rotations,minimum):
 s=cq.importers.importStep(str(ROOT/'vendor'/file)).val()
 for axis,angle in rotations:s=s.rotate((0,0,0),axis,angle)
 b=s.BoundingBox();s=s.translate((minimum[0]-b.xmin,minimum[1]-b.ymin,minimum[2]-b.zmin))
 assert s.isValid(),name
 parts[name]=s
 return s

# Rectangular base 190 x 150 x45, radiused outside corners, bottom access.
base=cq.Workplane('XY').box(190,150,45).edges('|Z').fillet(7).val().translate((15,65,-94.5))
inside=cq.Workplane('XY').box(185.2,145.2,44).edges('|Z').fillet(4.6).val().translate((15,65,-96.4))
base=base.cut(inside) # leaves 2.4mm ceiling at -74.4..-72, open underside
base=base.cut(box(250,220,30,15,65,-129.4)) # bottom plane -114.4; lid top -114.6
lid=cq.Workplane('XY').box(189.4,149.4,2.4).edges('|Z').fillet(6.7).val().translate((15,65,-115.8))
# Front central fixing moves to the right so the display can lower out through
# the bottom. Keeping the old (15,133) post trapped its glass during service.
fix=[(-72,-2),(-72,132),(102,-2),(102,132),(15,-3),(75,133)]
for index,(x,y) in enumerate(fix):
 base=base.fuse(cz(7 if index<4 else 4.8,-114.4,10,x,y)).cut(cz(2,-114.5,6.9,x,y))
 lid=lid.cut(cz(1.65,-117.1,2.6,x,y))
for x in (-44,44):
 for y in (20,72):
  base=base.fuse(cz(6,-72,HEAD_Z,x,y)).cut(cz(1.65,-75,4+HEAD_Z,x,y))

# A single IPS screen replaces both front light bars. Desk lighting stays below.
from display_layout import integrate as integrate_display
base=integrate_display(base,parts,save,vendor,box,cy,fasteners,mounts)

# Downward light channel recessed in bottom lid, with six-millimetre mixing space.
ambient=box(60,16,10.2,15,45,-111.9).cut(box(55,10.8,9,15,45,-112.7))
lid=lid.fuse(ambient).cut(box(53,9.4,4,15,45,-116.5))
lid=lid.cut(box(55.4,12.1,1.5,15,45,-116.35))
lid=lid.cut(box(8,5,5,43.5,45,-110.5))
# Two insert bosses lie outside the diffuser and LED PCB. Inserts install from
# below; the keeper can be removed without disturbing the electrical assembly.
for x in (-17,47):
 lid=lid.fuse(cz(4,-117,8.2,x,51.5)).cut(cz(2,-117.1,6.9,x,51.5))
 fasteners.append({'location':'ambient diffuser keeper','axis_mm':[x,51.5,-117],
                   'hardware':'M3x6 screw and Ruthex RX-M3x5.7 insert'})
save('ambient-light-diffuser',box(55,11.7,.8,15,45,-116.2),'translucent PETG')
ambient_keeper=box(72,20,1.2,15,45,-117.6).cut(box(53,9.4,1.4,15,45,-117.6))
for x in (-17,47):ambient_keeper=ambient_keeper.cut(cz(1.65,-118.3,1.5,x,51.5))
save('ambient-diffuser-keeper',ambient_keeper)
# The two M2 PCB holes come from the 1426 vendor STEP: (12.7,8.128) and
# (38.1,8.128). Screws enter from the LED side; hex nuts load from above.
for x in (2.15,27.55):
 y=41.922
 boss=cz(2.8,-109,5.6,x,y)
 nut=cq.Workplane('XY').polygon(6,4.2/math.cos(math.pi/6)).extrude(3.5).val().translate((x,y,-106.8))
 lid=lid.fuse(boss).cut(cz(1.1,-109.1,5.8,x,y)).cut(nut)
 fasteners.append({'location':'ambient LED PCB','axis_mm':[x,y,-109],
                   'hardware':'M2x6 screw and DIN 934 M2 hex nut; nut pocket 4.2 mm AF'})

# Four TPU desk feet isolate desk vibration and provide underglow clearance.
for i,(x,y) in enumerate(((-65,7),(-65,122),(95,7),(95,122))):
 lid=lid.cut(cz(1.65,-117.1,3,x,y))
 foot=cz(7,-122,5,x,y).cut(cz(1.65,-122.1,5.2,x,y)).cut(cz(3.2,-122.1,2.2,x,y))
 save('tpu-desk-foot-'+str(i+1),foot,'TPU 95A')

# Board support locations either follow manufacturer geometry or remain explicitly
# marked reserves. M2 hold-downs use nuts accessible from underneath the tray.
# Layout separates raw PD input, regulator cluster, control board and MCU.
layouts=[('carrier-reserved',90,65,22,(5,55,-106)),
         ('pico',21,52.3,8,(-55,61,-106)),
         ('regulator12',17.8,17.8,9,(-53,18,-106)),
         ('regulator5logic',17.8,17.8,9,(-27,18,-106)),
         ('regulator5servo',17.8,17.8,9,(-1,18,-106)),
         ('pressure',29,27.05,17.95,(40,8,-106)),
         ('pd',20.32,24.608,14,(72,-8.2,-106))]
for name,w,d,h,(x,y,z) in layouts:
 # Reserved bounding box appears only in the layout assembly, never a print file.
 if name=='carrier-reserved':parts['REF-driver-carrier-90x65x22-NOT-DESIGNED']=box(w,d,h,x+w/2,y+d/2,z+h/2)

def nut_standoff(name,x,y,pcb_bottom,screw,drill=2.2,nut_af=4.2,nut_description='DIN 934 M2'):
 global lid
 # Hex slot opens on the tray underside and ends 2.7 mm above the tray top.
 # Nut seats against its blind end when the top-side screw is tightened.
 post=cz(2.7,-114.6,pcb_bottom+114.6,x,y)
 hex_slot=cq.Workplane('XY').polygon(6,nut_af/math.cos(math.pi/6)).extrude(5.2).val().translate((x,y,-117.1))
 lid=lid.fuse(post).cut(cz(drill/2,-117.1,pcb_bottom+117.3,x,y)).cut(hex_slot)
 fasteners.append({'location':name,'axis_mm':[x,y,pcb_bottom],
                   'hardware':screw+' and '+nut_description+' hex nut; nut pocket '+str(nut_af)+' mm AF'})

# The carrier PCB designer must place four 2.4 mm NPTH mounting holes on these
# datums. This commits the mounting interface without claiming a routed board.
for x in (8,92):
 for y in (58,117):nut_standoff('carrier required NPTH mounting datum',x,y,-106,'M2x10 screw')
mounts.append({'component':'unrouted carrier','required_pcb_outline_mm':[90,65],
 'minimum_xyz_mm':[5,55,-106],'required_hole_centers_xy_mm':[[8,58],[8,117],[92,58],[92,117]],
 'required_hole_diameter_mm':2.4,'instruction':'Route PCB to these holes; no hardware release implied'})

# Pico: preserve vendor hole positions, using selected small cap heads to clear
# the adjacent header bodies. No washer is fitted at these four locations.
for x,y in pico_mount.HOLES:
 nut_standoff('Pico',x,y,-106,pico_mount.SCREW_MODEL,pico_mount.DRILL,
              pico_mount.NUT_POCKET_AF,pico_mount.NUT_MODEL)
parts.update(pico_mount.references())
# Pololu: two diagonal holes at (15.494,2.286)/(2.286,15.494).
# The STEP's lowest underside component is 1.1 mm below its PCB datum.
for offset in (-53,-27,-1):
 for x,y in ((15.494,2.286),(2.286,15.494)):
  nut_standoff('Pololu D24V22',offset+x,18+y,-104.9,'M2x12 screw')
# HUSB238: the actual USB shell extends along vendor +Y. Rotate the board 180
# degrees. Its two 2.5 mm mounting holes transform to the coordinates below.
# The minimum Z is a terminal pin, 1.920176512 mm below the PCB underside.
for x in (74.667,89.907):nut_standoff('HUSB238 PD',x,-4.547,-104.079823488,'M2x12 screw')

# Product 1782 is the original non-STEMMA board. The manufacturer confirms
# its 2023 update changed silkscreen only; product 5027 is the different board.
# STEP holes: (2.54,10.16), (17.78,10.16), 2.5 mm diameter, PCB bottom Z=0.
for tag,tx,ty in [('TEMP1',-53,42),('TEMP2',-55,117)]:
 for hx in (2.54,17.78):
  nut_standoff(tag,tx+hx,ty+10.16,-103,'M2x14 screw with 0.4 mm washer')
 mounts.append({'component':tag+' Adafruit 1782 non-STEMMA',
  'hole_centers_xyz_mm':[[tx+2.54,ty+10.16,-103],[tx+17.78,ty+10.16,-103]],
  'clear_board_envelope_mm':[21.6,13.6,3.7],
  'revision_source':'https://www.adafruit.com/product/1782: 2023 silkscreen-only update',
  'remaining_test':'Verify actual board edges/holes, soldered pigtail clearance and thermal lag'})

# The SDP810 pins are on 2 mm pitch. Solder them directly to a separately
# restrained daughterboard; reviewed sockets require more insertion depth than
# the shortest permitted pins. Housing screws take tubing forces.
pressure_board=box(18,1.6,12,54.5,33.05,-99.775)
for x in (51.5,53.5,55.5,57.5):
 pressure_board=pressure_board.cut(cy(.4,32.15,1.8,x,-99.775))
for x in (42.5,66.5):
 post=box(5.8,4.2,20.575,x,37.35,-104.3125)
 # Narrow stand-off neck avoids the real package's rear clips. The tall
 # support starts behind the furthest clip, Y=35.05, with 0.2 mm clearance.
 post=post.fuse(cy(2.4,31.95,3.3,x,-97.025))
 lid=lid.fuse(post).cut(cy(1.1,31.8,7.8,x,-97.025))
 nut=cq.Workplane('XZ').polygon(6,4.2/math.cos(math.pi/6)).extrude(-2.0).val().translate((x,37.65,-97.025))
 lid=lid.cut(nut)
 fasteners.append({'location':'SDP810 housing restraint','axis_mm':[x,21.5,-97.025],
  'hardware':'M2x20 screw, 0.4 mm washer and DIN 934 M2 nut; nominal 1.85 mm tip protrusion'})
for x in (47.5,61.5):
 post=box(6,4.0,13.825,x,35.85,-107.6875)
 lid=lid.fuse(post).cut(cy(1.1,33.75,4.3,x,-103.775))
 nut=cq.Workplane('XZ').polygon(6,4.2/math.cos(math.pi/6)).extrude(-1.8).val().translate((x,36.05,-103.775))
 lid=lid.cut(nut)
 pressure_board=pressure_board.cut(cy(1.2,32.15,1.8,x,-103.775))
 fasteners.append({'location':'SDP810 daughterboard','axis_mm':[x,32.25,-103.775],
  'hardware':'M2x6 screw and DIN 934 M2 nut; nominal 0.6 mm tip protrusion'})
save('REF-SDP810-daughterboard-required-outline',pressure_board,'unrouted FR4 interface',False)
mounts.append({'component':'SDP810 pressure sensor','housing_hole_axes_xyz_mm':[[42.5,21.5,-97.025],[66.5,21.5,-97.025]],
 'daughterboard_outline_mm':[18,12,1.6],'daughterboard_minimum_xyz_mm':[45.5,32.25,-105.775],
 'pin_pitch_mm':2.0,'pin_axes_x_mm':[51.5,53.5,55.5,57.5],'pin_axis_z_mm':-99.775,
 'pin_drill_mm':0.8,'mounting_drill_mm':2.4,
 'electrical_interface':'Direct solder; removable sensor/PCB module, strain-relieved four-wire pigtail',
 'remaining_test':'Confirm actual pin projection, washer/nut fit and tubing bend radius on coupon'})

# USB mouth is 1.8 mm behind the outer wall. This 14 x 9 mm opening also clears
# a 12 x 7 mm plug overmould. Actual cable shape and strain loads require a test.
# A flush fascia belongs to the removable tray, so the USB connector cannot trap
# the populated tray behind the shell wall during straight downward removal.
usb_center=(82.16,-101.409823488)
base=base.cut(box(18,8,18.3,usb_center[0],-10,-105.85))
lid=lid.fuse(box(17.6,2.4,18.1,usb_center[0],-8.8,-105.95))
lid=lid.cut(box(14,8,9,usb_center[0],-10,usb_center[1]))
# Air vents for the electronics work independently of rotor operation.
for x in range(-40,51,10):base=base.cut(box(5,7,2.0,x,-9,-80))
for y in range(72,122,10):base=base.cut(box(7,5,2.0,109,y,-82))

# Encoder: shaft is horizontal X, wheel rotates in the YZ wall plane. The front
# rim is exposed for up/down rolling; the shallow side shroud covers the disc face.
ey,ez=3.,-90.
base=base.cut(box(8,32,34,-78,ey,ez))
mount=box(2.4,32,28,-71.2,10,ez).cut(cx(3.65,-73,4,ey,ez))
for z in (ez-9,ez+9):
 mount=mount.cut(cx(1.65,-73,4,23,z))
 base=base.fuse(cx(3.6,-80,7.4,23,z)).cut(cx(2,-79.4,6.9,23,z))
for z in (ez-12.5,ez+12.5):mount=mount.fuse(box(3,28,3,-68.5,10,z))
# The bushing/nut carries the approximately 6 N press force into the shell.
# A small daughterboard has two separately supported holes; solder joints carry
# no operating load. Board connector/pin routing remains a PCB design task.
encoder_board=encoder_layout.board()
for z in (ez-8.5,ez+8.5):
 mount=mount.fuse(cx(3,-70,7.5,22,z)).cut(cx(1.1,-71.2,8.8,22,z))
 nut=cq.Workplane('YZ').polygon(6,4.2/math.cos(math.pi/6)).extrude(2.3).val().translate((-70.1,22,z))
 mount=mount.cut(nut)
 fasteners.append({'location':'encoder daughterboard','axis_mm':[-62.5,22,z],
                   'hardware':'M2x10 screw and M2 hex nut inserted before mounting encoder bracket'})
save('horizontal-encoder-mount',mount)
save('encoder-daughterboard-P1-FR4',encoder_board,'routed FR4 prototype P1 datum',False)
parts.update(encoder_layout.references(box,cx))
encoder_nut=cq.Workplane('YZ').polygon(6,11/math.cos(math.pi/6)).extrude(2).val().translate((-74.7,ey,ez)).cut(cx(3.6,-74.8,2.2,ey,ez))
save('REF-M7x0p75-encoder-panel-nut',encoder_nut,'purchased steel nut envelope',False)
mounts.append({'component':'encoder','panel_nut':'M7 x 0.75, 11 mm AF, maximum 2 mm thick',
 'wheel_to_nut_axial_gap_mm':2.8,'assessed_button_travel_mm':1.5,
 'daughterboard_holes_xyz_mm':[[-62.5,22,ez-8.5],[-62.5,22,ez+8.5]],
 'daughterboard_pcb_revision':'P1, native KiCad ERC/DRC and 1.6mm mechanical datum',
 'daughterboard_outline_mm':[29.5,24,1.6],
 'remaining_test':'Verify supplied nut dimensions, switch travel, D-shaft fit and lateral wheel force'})
wheel=cq.importers.importStep(str(ROOT/'prototypes/encoder-wheel-clearance-0p15.step')).val()
wheel=wheel.rotate((0,0,0),(0,1,0),90).translate((-85.5,ey,ez))
save('horizontal-encoder-thumbwheel',wheel)
shroud=cx(17,-88.5,11.5,ey,ez).cut(cx(15.8,-86,10.2,ey,ez))
shroud=shroud.cut(box(17,15,22,-81,ey-14,ez))
base=base.fuse(shroud)
# Explicit dimensional reconstruction, not a downloaded exact encoder model.
enc=box(6.5,11.8,13.6,-66.75,ey,ez).fuse(cx(3.5,-75,5,ey,ez)).fuse(cx(3,-85,15,ey,ez))
parts['REF-Bourns-PEC11H-drawing-envelope']=enc

save('electronics-base-shell',base.clean())
save('electronics-service-tray',lid.clean())

vendor('Raspberry-Pi-Pico-SC0915-vendor','Pico-R3.step',[((1,0,0),90)],(-55,61,-106))
for name,x in [('12V',-53),('5V-logic',-27),('5V-servo',-1)]:
 vendor('Pololu-D24V22-'+name+'-vendor','D24V22Fx.step',[],(x,18,-106))
vendor('Sensirion-SDP810-125Pa-vendor','SDP810.step',[],(40,8,-106))
vendor('Adafruit-HUSB238-5807-vendor','5807.step',[((0,0,1),180)],(72,-8.2,-106))
vendor('Adafruit-NeoPixel-1426-ambient-vendor','1426.step',[((1,0,0),180)],(-10.55,39.89,-111.6))
# Temp modules placed on separate insulating mounts near power region and air.
vendor('MCP9808-temp1-Adafruit1782-vendor','1782.step',[],(-53,42,-103))
vendor('MCP9808-temp2-Adafruit1782-vendor','1782.step',[],(-55,117,-103))

assembly=cq.Assembly(name='Windflow Rev B electronics layout development')
for name,s in parts.items():
 cq.exporters.export(s,str(OUT/(name+'.step')))
 col=(.18,.55,.32) if 'vendor' in name else ((.8,.55,.15) if name.startswith('REF-') else (.28,.32,.37))
 assembly.add(s,name=name,color=cq.Color(*col))
assembly.save(str(OUT/'electronics-layout-development.step'))
checks=[]
for name,s in parts.items():
 if name=='electronics-base-shell':continue
 volume=base.intersect(s).Volume()
 if volume>0.01:checks.append({'pair':['electronics-base-shell',name],'overlap_mm3':volume})
for name in ('Raspberry-Pi-Pico-SC0915-vendor','Pololu-D24V22-12V-vendor',
             'Pololu-D24V22-5V-logic-vendor','Pololu-D24V22-5V-servo-vendor',
             'Adafruit-HUSB238-5807-vendor','Adafruit-NeoPixel-1426-ambient-vendor',
             'Sensirion-SDP810-125Pa-vendor','REF-SDP810-daughterboard-required-outline',
             'MCP9808-temp1-Adafruit1782-vendor','MCP9808-temp2-Adafruit1782-vendor'):
 volume=lid.intersect(parts[name]).Volume()
 if volume>0.01:checks.append({'pair':['electronics-service-tray',name],'overlap_mm3':volume})
plug=box(12,35,7,usb_center[0],-28.5,usb_center[1])
plug_overlap=base.intersect(plug).Volume()+lid.intersect(plug).Volume()
assert not checks,checks
assert plug_overlap<.01,plug_overlap
removal=[]
for distance in (1,3,6,12,25,45):
 for name in ('electronics-service-tray','Adafruit-HUSB238-5807-vendor'):
  volume=base.intersect(parts[name].translate((0,0,-distance))).Volume()
  removal.append({'part':name,'downward_mm':distance,'overlap_mm3':volume})
  assert volume<.01,removal[-1]
(OUT/'base-validation.json').write_text(json.dumps({'parts':records,'assembly_files':[n+'.step' for n in parts],'layout_envelopes':layouts,
 'build':{'completed_utc':datetime.now(timezone.utc).isoformat(),
  'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
  'pico_mount_sha256':hashlib.sha256((ROOT/'pico_mount.py').read_bytes()).hexdigest(),
  'encoder_layout_sha256':hashlib.sha256((ROOT/'encoder_layout.py').read_bytes()).hexdigest(),
  'encoder_pcb_inputs_sha256':{str(path.relative_to(ROOT.parent)):hashlib.sha256(path.read_bytes()).hexdigest()
   for path in [encoder_layout.PCB_DIR/'windflow-encoder-mechanical-datum.step',encoder_layout.PCB_DIR/'mechanical-interface.json']},
  'parameters_sha256':hashlib.sha256((ROOT/'parameters.json').read_bytes()).hexdigest()},
 'fasteners':fasteners,'shell_component_and_board_support_intersections':checks,
 'tray_and_USB_downward_removal_samples':removal,
 'usb':{'vendor_shell_faces':'+Y before Z180 rotation','mouth_y_mm':-8.2,
 'outer_wall_y_mm':-10,'aperture_mm':[14,9],'plug_overmould_check_mm':[12,35,7],
 'plug_to_shell_overlap_mm3':plug_overlap,'mount_holes_source':'5807 STEP PCB circular edges, radii 1.25 mm',
 'service_access':'USB fascia is integral with tray; connector exits through open-bottom shell slot',
 'critical_remaining_test':'Verify supplied USB cable overmould and insertion load in printed receptacle coupon'},
 'mounting_interfaces':mounts,
 'status':'development, not print release','remaining':['carrier and daughterboard PCB design',
 'all component and harness interference checks','physical USB plug/insertion-load test',
 'sensor pigtail strain relief and safe pin clearance','complete populated-tray removal and harness service paths']},indent=2))
print('BASE BUILD COMPLETE',flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
