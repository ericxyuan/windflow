"""Nominal remote-Pico connector clearance study, independent of E3 assembly.

Drawing-based socket/header envelopes are deliberately marked REF. This does
not update the full assembly or establish a routed cable/PCB design.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import sys
import cadquery as cq
import pico_mount

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'interface_study'
OUT.mkdir(exist_ok=True)
manifest_path = ROOT / 'rev_b/base-validation.json'
manifest = json.loads(manifest_path.read_text())
parts = {}
for file in manifest['assembly_files']:
    if 'driver-carrier' not in file:
        parts[file[:-5]] = cq.importers.importStep(str(ROOT / 'rev_b' / file)).val()

def box(w, d, h, x, y, bottom):
    return cq.Workplane('XY').box(w, d, h).translate((x, y, bottom+h/2)).val()

def overlap(a, b):
    aa, bb = a.BoundingBox(), b.BoundingBox()
    if any(getattr(aa, k+'max') <= getattr(bb, k+'min')+1e-5 or
           getattr(bb, k+'max') <= getattr(aa, k+'min')+1e-5 for k in 'xyz'):
        return 0.0
    return max(0.0, a.intersect(b).Volume())

# Pico manufacturer model: FR4 bottom -106, thickness 1, board 21 x51.
# Header centres use the official 17.78 mm row spacing / 2.54 mm pitch.
pico = parts['Raspberry-Pi-Pico-SC0915-vendor']
pcb = [s for s in pico.Solids() if s.BoundingBox().xlen>20 and
       s.BoundingBox().ylen>50 and s.BoundingBox().zlen<1.1]
assert len(pcb)==1
b = pcb[0].BoundingBox()
assert abs(b.xlen-21)<.001 and abs(b.ylen-51)<.001 and abs(b.zmax+105)<.001

candidate = {}
centres = [(-53.39,86.5,-105.0,'Pico-left'),(-35.61,86.5,-105.0,'Pico-right'),
           (13.0,86.5,-104.4,'carrier-J15'),(22.0,86.5,-104.4,'carrier-J16')]
for x,y,z,name in centres:
    candidate['REF-'+name+'-TSW-body'] = box(2.54,50.8,2.54,x,y,z)
    # 51.28 mm length and9.27 mm reference height from the IDSS catalogue.
    # Width3 is a conservative allowance over the2.54 mm single-row callout.
    candidate['REF-'+name+'-IDSS-socket'] = box(3.0,51.28,9.27,x,y,z+2.54)

# Flat portions of two candidate cable corridors only. The bends, connector
# retention and service slack need a subsequent harness design. Reserve these
# volumes while placing carrier components; no part here is a real cable model.
for x1,x2,z,name in [(-53.39,13,-85,'left'),(-35.61,22,-81,'right')]:
    candidate['REF-'+name+'-ribbon-corridor'] = box(x2-x1,51.28,2,(x1+x2)/2,86.5,z)

checks=[]
issues=[]
head_clearances=[]
for x,y in pico_mount.HOLES:
    row_x=min((-53.39,-35.61),key=lambda value:abs(value-x))
    clearance=abs(row_x-x)-2.54/2-3./2
    assert clearance>=.4,clearance
    head_clearances.append({'pico_hole_xy_mm':[x,y],'header_body_head_gap_mm':clearance,
        'bare_header_slim_driver_diameter_mm':3.4,'driver_gap_mm':abs(row_x-x)-2.54/2-3.4/2,
        'instruction':'Unplug IDSS sockets before accessing Pico screws; no washers'})
for name, body in candidate.items():
    assert body.isValid() and len(body.Solids())==1,name
    cq.exporters.export(body,str(OUT/(name+'.step')))
    for other, obstacle in parts.items():
        v=overlap(body,obstacle)
        checks.append({'candidate':name,'obstacle':other,'overlap_mm3':v})
        if v>.01: issues.append(checks[-1])
for i,(name,body) in enumerate(candidate.items()):
    for other,obstacle in list(candidate.items())[i+1:]:
        v=overlap(body,obstacle)
        checks.append({'candidate':name,'obstacle':other,'overlap_mm3':v})
        if v>.01: issues.append(checks[-1])

board=cq.Workplane('XY').box(90,65,1.6).translate((50,87.5,-105.2)).val()
for x in (8,92):
    for y in (58,117):
        board=board.cut(cq.Solid.makeCylinder(1.2,2,cq.Vector(x,y,-106.2),cq.Vector(0,0,1)))
assert board.isValid() and len(board.Solids())==1
cq.exporters.export(board,str(OUT/'REF-carrier-mechanical-board.step'))

report={
 'completed_utc':datetime.now(timezone.utc).isoformat(),
 'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
 'base_manifest_sha256':hashlib.sha256(manifest_path.read_bytes()).hexdigest(),
 'input_sha256':{file:hashlib.sha256((ROOT/'rev_b'/file).read_bytes()).hexdigest()
                 for file in manifest['assembly_files'] if 'driver-carrier' not in file},
 'candidate_count':len(candidate),'checks':len(checks),'intersections_to_resolve':issues,
 'connector_centres_xyz_mm':centres,
 'carrier_component_height_under_ribbon_limit_mm':18,
 'pico_mount_head_clearances':head_clearances,
 'pico_mount_sha256':hashlib.sha256((ROOT/'pico_mount.py').read_bytes()).hexdigest(),
 'existing_top_ceiling_mm':-74.4,
 'corridor_top_mm':-79,
 'pico_pin_keying':{'left_removed_physical_pin':12,'right_removed_physical_pin':30},
 'limitations':[
  'Drawing-based envelopes only; no manufacturer connector STEP obtained',
  'No electrical netlist, PCB placement/routing or schematic/ERC validation',
  'Cable corridor excludes bends, retention, physical cable shape and service slack',
  'Selected M1.6 cap heads have0.42mm nominal lateral gap to header bodies; '
  'placement/fastener tolerances and cable removal require physical qualification',
  '22mm carrier reserve omitted as an obstacle; future component placement must honor cable keepouts',
  'This candidate study does not establish that remote connectors/cables are adopted in Onshape'],
}
(OUT/'validation.json').write_text(json.dumps(report,indent=2))
asm=cq.Assembly(name='Windflow remote-Pico candidate - mechanical study only')
asm.add(board,name='REF-carrier-mechanical-board',color=cq.Color(.15,.48,.33))
for name,body in candidate.items():asm.add(body,name=name,color=cq.Color(.2,.6,.85,.6))
for name in ['electronics-service-tray','Raspberry-Pi-Pico-SC0915-vendor',
             'Pololu-D24V22-12V-vendor','Pololu-D24V22-5V-logic-vendor','Pololu-D24V22-5V-servo-vendor']:
    asm.add(parts[name],name=name,color=cq.Color(.5,.5,.5))
asm.save(str(OUT/'remote-pico-candidate.step'))
print(json.dumps({k:v for k,v in report.items() if k!='input_sha256'},indent=2),flush=True)
sys.stdout.flush();sys.stderr.flush()
os._exit(1 if issues else 0)
