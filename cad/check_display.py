"""Nominal screen cradle service path after unplugging/removing the tray.

Fasteners, soldered harness and tools are excluded. This is not physical fit proof.
"""
from pathlib import Path
import hashlib,json,os,sys
from datetime import datetime,timezone
import cadquery as cq
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'rev_b'
names=['electronics-base-shell','display-front-bezel','REF-display-clear-window-45x34p4x1',
       'display-removable-cradle','Adafruit-ST7789-4311-display-vendor']
parts={n:cq.importers.importStep(str(OUT/(n+'.step'))).val() for n in names}
shell=parts['electronics-base-shell'];samples=[];issues=[]
def check(name,shift):
    s=parts[name].translate(shift);v=max(0,shell.intersect(s).Volume())
    samples.append({'part':name,'translation_mm':shift,'overlap_mm3':v})
    if v>.01:issues.append(samples[-1])
# Remove front cover/bezel outward, then release the two-piece cradle rearward.
for d in range(21):
    for n in ('display-front-bezel','REF-display-clear-window-45x34p4x1'):check(n,(0,d,0))
for dy in (0,-.5,-1,-1.5,-2):
    for n in ('display-removable-cradle','Adafruit-ST7789-4311-display-vendor'):check(n,(0,dy,0))
for d in range(61):
    for n in ('display-removable-cradle','Adafruit-ST7789-4311-display-vendor'):check(n,(0,-2,-d))
report={'completed_utc':datetime.now(timezone.utc).isoformat(),
    'source_sha256':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ('display_layout.py','build_base.py','check_display.py')},
    'input_sha256':{n:hashlib.sha256((OUT/(n+'.step')).read_bytes()).hexdigest() for n in names},
    'samples':samples,'intersections_to_resolve':issues,
    'sequence':'Unplug screen; remove service tray and front bezel/window; undo cradle screws; pull cradle rearward 2 mm then lower through open bottom.',
    'limits':'Nominal B-rep/sampled path; excludes screws, harness, tools, tolerance stack and physical printed fit.'}
(OUT/'display-validation.json').write_text(json.dumps(report,indent=2))
print('DISPLAY SERVICE PATH',len(samples),'samples; unintended intersections',len(issues),flush=True)
if issues:print(json.dumps(issues,indent=2),flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(1 if issues else 0)
