"""Assemble real component geometry, diagnose intersections and render CAD.
No mechanical-performance or physical-fit claims are inferred from these checks.
"""
from pathlib import Path
import json, math, os, sys, hashlib
from datetime import datetime, timezone
import cadquery as cq
ROOT=Path(__file__).resolve().parent; OUT=ROOT/'rev_b'
parts={}; colors={}
HEAD_Z=json.loads((ROOT/'parameters.json').read_text())['head_center_height']
def add(name,path,shift=(0,0,0),color=(.28,.32,.37)):
 s=cq.importers.importStep(str(path)).val().translate(shift)
 assert s.isValid(),name
 parts[name]=s;colors[name]=color
 return s
for f in json.loads((OUT/'validation.json').read_text())['assembly_files']:
 add(f[:-5],OUT/f,(0,0,HEAD_Z))
for f in json.loads((OUT/'base-validation.json').read_text())['assembly_files']:
 name=f[:-5]
 add(name,OUT/f,color=(.15,.5,.32) if 'vendor' in name else (.34,.37,.42))
mechanism=json.loads((ROOT/'prototypes/validation.json').read_text())
moving_names=mechanism['assembly_files']['moving']
for n in moving_names:
 add(n,ROOT/'prototypes'/('installed-'+n+'-max-boost.step'),(0,90,HEAD_Z),(.04,.66,.74) if 'panel' in n else (.9,.6,.15))
add('servo-bracket',ROOT/'prototypes/servo-slotted-bracket.step',(0,90,HEAD_Z))
add('FS90-FB-APPROXIMATE',ROOT/'prototypes/REF-FS90-FB-approximate-envelope.step',(0,90,HEAD_Z),(.15,.3,.6))
for n in mechanism['assembly_files']['fixed']:
 if n not in ('frame','servo_bracket','servo_approximate'):
  add(n,ROOT/'prototypes'/('installed-'+n+'.step'),(0,90,HEAD_Z),(.72,.73,.75))
fan=cq.importers.importStep(str(ROOT/'vendor/NF-A12x25_G2_Public-CAD.stp')).val()
fan=fan.rotate((0,0,0),(1,0,0),-90).translate((0,1,HEAD_Z))
parts['Noctua-NF-A12x25-G2-vendor']=fan;colors['Noctua-NF-A12x25-G2-vendor']=(.53,.40,.30)
for x in (-52.5,52.5):
 for z in (-52.5,52.5):add('TPU-fan-pad-'+str(x)+'-'+str(z),OUT/'tpu-fan-pad-m3.step',(x,0,z+HEAD_Z),(.2,.2,.2))

def overlap(a,b):
 aa,bb=a.BoundingBox(),b.BoundingBox()
 if any(getattr(aa,k+'max')<=getattr(bb,k+'min')+1e-5 or getattr(bb,k+'max')<=getattr(aa,k+'min')+1e-5 for k in 'xyz'):return 0.
 return max(0.,a.intersect(b).Volume())
issues=[];pairs=0;cover_removal=[]
items=list(parts.items())
for i,(name,s) in enumerate(items):
 for other,t in items[i+1:]:
  # Original servo output enters its horn; encoder shaft intentionally enters wheel.
  if set((name,other)) in [set(('horn','FS90-FB-APPROXIMATE')),set(('REF-Bourns-PEC11H-drawing-envelope','horizontal-encoder-thumbwheel'))]:continue
  v=overlap(s,t);pairs+=1
  if v>.01:issues.append({'pose':'maximum boost','a':name,'b':other,'overlap_mm3':round(v,4)})
 print('CHECKED '+name,flush=True)
# Check open and halfway poses against every other part, including the housing.
# Motion is solved analytically from the same dimensions as the prototype model.
p=json.loads((ROOT/'parameters.json').read_text())
for state in (mechanism['kinematics'][0],mechanism['kinematics'][30],mechanism['kinematics'][-1]):
 a=state['panel_angle_deg']; phi=state['servo_angle_deg']; stroke=state['yoke_stroke_mm']
 end_y=-p['servo_rod_length']+p['servo_crank_radius']*math.sin(math.radians(phi))
 end_z=-p['servo_crank_radius']+p['servo_crank_radius']*math.cos(math.radians(phi))
 varied=dict(parts)
 for n in moving_names:
  s=cq.importers.importStep(str(ROOT/'prototypes'/('installed-'+n+'-open.step'))).val()
  if n in ('upper_panel','upper_crank','upper_clamp'):
   s=s.rotate((0,0,p['outlet_height']/2),(1,0,p['outlet_height']/2),-a)
  elif n in ('lower_panel','lower_crank','lower_clamp'):
   s=s.rotate((0,0,-p['outlet_height']/2),(1,0,-p['outlet_height']/2),a)
  elif n in ('yoke','rod_yoke_pin'):s=s.translate((0,stroke,0))
  elif n=='horn':s=s.rotate((0,-p['servo_rod_length'],-p['servo_crank_radius']),(1,-p['servo_rod_length'],-p['servo_crank_radius']),-phi)
  elif n=='rod':
   s=s.rotate((0,-p['servo_rod_length'],0),(1,-p['servo_rod_length'],0),state['rod_angle_deg']).translate((0,end_y+p['servo_rod_length'],end_z))
  elif n=='horn_rod_pin':s=s.translate((0,end_y+p['servo_rod_length'],end_z))
  elif n in ('upper_crank_pin','lower_crank_pin'):
   sign=1 if n.startswith('upper') else -1
   s=s.translate((0,stroke,sign*p['yoke_crank_radius']*(math.cos(math.radians(a))-1)))
  else:raise ValueError('Missing motion mapping '+n)
  varied[n]=s.translate((0,90,HEAD_Z))
 pose='open' if not a else ('maximum boost' if state is mechanism['kinematics'][-1] else 'halfway')
 names=list(varied)
 for i,name in enumerate(names):
  for other in names[i+1:]:
   if name not in moving_names and other not in moving_names:continue
   if set((name,other))==set(('horn','FS90-FB-APPROXIMATE')):continue
   v=overlap(varied[name],varied[other]);pairs+=1
   if v>.01:issues.append({'pose':pose,'a':name,'b':other,'overlap_mm3':round(v,4)})
 print('CHECKED POSE '+pose,flush=True)
 # Both the open and intermediate mechanisms must allow the service cover
 # and its captive cable grommet to withdraw outward along X.
 for dx in range(0,61):
  worst=0.
  for moving in ('linkage-service-cover','tpu-servo-cable-grommet'):
   shifted=varied[moving].translate((dx,0,0))
   for other,t in varied.items():
    if other in ('linkage-service-cover','tpu-servo-cable-grommet'):continue
    v=overlap(shifted,t);worst=max(worst,v)
    if v>.01:issues.append({'pose':pose+' cover removal','a':moving,'b':other,'outward_mm':dx,'overlap_mm3':round(v,4)})
  cover_removal.append({'pose':pose,'outward_x_mm':dx,'maximum_overlap_mm3':worst})
report={'part_count':len(parts),'pairs_checked':pairs,'poses':['open','halfway','maximum boost'],
 'completed_utc':datetime.now(timezone.utc).isoformat(),
 'source_sha256':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ('build_head.py','build_base.py','build_prototypes.py','check_assembly.py','parameters.json')},
 'cover_removal_samples':cover_removal,
 'input_sha256':{str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest()
  for path in [OUT/'validation.json',OUT/'base-validation.json',ROOT/'prototypes/validation.json']},
 'intersections_to_resolve':issues,'limitations':['Unrouted carrier and servo/encoder envelopes are marked approximate',
 'Sampled static nominal solid check, not tolerance stack, wiring sweep or assembly insertion test']}
(OUT/'assembly-interference.json').write_text(json.dumps(report,indent=2))
asm=cq.Assembly(name='Windflow Rev B development - unresolved items in interference report')
for name,s in parts.items():asm.add(s,name=name,color=cq.Color(*colors[name]))
asm.save(str(OUT/'full-development-assembly.step'))
print(json.dumps(report,indent=2),flush=True)

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
fig=plt.figure(figsize=(15,10),facecolor='#eef2f5')
ax=fig.add_axes((0,.07,.80,.82),projection='3d')
hidden={'head-left-integral-outlet','electronics-base-shell','magnetic-front-grille','main-led-retaining-frame','encoder-rim-shroud'}
for name,s in parts.items():
 if name in hidden:continue
 vertices,tris=s.tessellate(.45,.4);xyz=[(v.x,v.y,v.z) for v in vertices]
 ax.add_collection3d(Poly3DCollection([[xyz[j] for j in t] for t in tris],facecolor=colors[name],edgecolor='none',
   alpha=.2 if name in {'head-right-integral-outlet','REF-driver-carrier-90x65x22-NOT-DESIGNED'} else 1,rasterized=True))
ax.set(xlim=(-90,115),ylim=(-25,160),zlim=(-125,85),xlabel='X / width (mm)',ylabel='Y / airflow (mm)',zlabel='Z / height (mm)')
ax.set_box_aspect((205,185,210));ax.view_init(elev=24,azim=135);ax.grid(False);ax.set_facecolor('#eef2f5')
fig.text(.045,.94,'WINDFLOW / integrated development CAD',fontsize=23,weight='bold',color='#17394a')
fig.text(.045,.903,'Actual B-reps and manufacturer component models. Left shell and front grille hidden for inspection.',fontsize=11,color='#526a78')
fig.text(.79,.66,'142 mm bell-mouth\n114 mm throat\n120 mm PWM fan\n7 trial radial vanes\n104 × 94 mm outlet\n75% minimum gross area',fontsize=12,linespacing=1.8,color='#17394a')
fig.text(.79,.37,'Horizontal thumbwheel\n16-pixel main display\n8-pixel downward light\nUSB-C PD / no battery\nRemovable service tray',fontsize=11,linespacing=1.8,color='#526a78')
fig.text(.045,.025,'DEVELOPMENT — not a manufacturing release. See assembly-interference.json; physical airflow, noise, retention and fit remain untested.',fontsize=10,color='#78582b')
fig.savefig(OUT/'assembly-cutaway.png',dpi=140);plt.close(fig)
assert (OUT/'assembly-cutaway.png').stat().st_size>10000
print('ASSEMBLY CHECK/RENDER COMPLETE',flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(1 if issues else 0)
