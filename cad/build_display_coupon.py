"""Small screen fascia and M2-insert samples before printing the enclosure."""
from pathlib import Path
import json,os,sys,hashlib
import cadquery as cq
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'prototypes'
base=cq.importers.importStep(str(ROOT/'rev_b/electronics-base-shell.step')).val()
crop=cq.Workplane('XY').box(92,20,45).val().translate((13,133,-94.5))
fascia=base.intersect(crop)
block=cq.Workplane('XY').box(36,12,6).val().translate((18,6,3))
for x,d in ((6,3.1),(18,3.2),(30,3.3)):
    block=block.cut(cq.Solid.makeCylinder(d/2,4.5,cq.Vector(x,6,6),cq.Vector(0,0,-1)))
records=[]
for name,shape in [('display-fascia-coupon',fascia),('m2-display-insert-coupon-3p1-3p2-3p3',block)]:
    assert shape.isValid() and len(shape.Solids())==1,name
    cq.exporters.export(shape,str(OUT/(name+'.step')))
    cq.exporters.export(shape,str(OUT/(name+'.stl')),tolerance=.06,angularTolerance=.12)
    records.append({'name':name,'valid':True,'solids':1,'volume_mm3':shape.Volume()})
(OUT/'display-coupons.json').write_text(json.dumps({'parts':records,
    'input_sha256':hashlib.sha256((ROOT/'rev_b/electronics-base-shell.step').read_bytes()).hexdigest(),
    'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'purpose':'Test real screen, cradle, window alignment, insert fit and service motion before large prints.',
    'limits':'Nominal geometry only. Use original orientations/material and the real purchased display.'},indent=2))
print('DISPLAY COUPONS PASS',flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
