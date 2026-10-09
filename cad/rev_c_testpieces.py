"""Small source-matched fit coupons and an optional aiming trial stand."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,math
import cadquery as cq

ROOT=Path(__file__).resolve().parents[1]
CAD=ROOT/'cad/rev_c'
OUT=CAD/'testpieces'

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def box(w,d,h,x=0,y=0,z=0):return cq.Workplane('XY').box(w,d,h).val().translate((x,y,z))
def cyl(r,z,h,x=0,y=0):return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z))

def main():
    report=json.loads((CAD/'head-validation.json').read_text())
    assert json.loads((CAD/'build-state.json').read_text())['status']=='PASS'
    assert not report['unintended_issues']
    for n,d in report['input_sha256'].items():assert digest(ROOT/n)==d,('Stale source',n)
    OUT.mkdir(exist_ok=True);parts=[]
    def save(n,s,material,orientation,purpose,solids=1):
        assert s.isValid() and len(s.Solids())==solids,(n,len(s.Solids()))
        cq.exporters.export(s,str(OUT/(n+'.step')))
        cq.exporters.export(s,str(OUT/(n+'.stl')),tolerance=.04,angularTolerance=.1)
        b=s.BoundingBox()
        parts.append({'name':n,'material':material,'orientation':orientation,'purpose':purpose,
            'valid_solids':len(s.Solids()),'bounds_mm':[b.xlen,b.ylen,b.zlen],'volume_mm3':s.Volume()})
    for label,bores,radius,height in [('M3',[3.8,4.0,4.2],4.5,8),('M2',[3.0,3.2,3.4],3.4,5.5)]:
        s=box(64,18,2,z=1)
        for x,d in zip((-20,0,20),bores):
            s=s.fuse(cyl(radius,2,height,x)).cut(cyl(d/2,2.2,height+.1,x))
        save('insert-'+label+'-pilot-ladder',s,'PETG','flat plate on bed',
             'Left to right: '+str(bores)+'mm bores. Heat-set real ruthex inserts; measure pull-out, wall damage and screw bottoming.')
    hinge=box(64,18,2,z=1)
    for x,d in zip((-20,0,20),(3.2,3.3,3.4)):
        hinge=hinge.fuse(box(14,14,10,x,0,7)).cut(cq.Solid.makeCylinder(d/2,18,cq.Vector(x,-9,7),cq.Vector(0,1,0)))
    save('hinge-3mm-horizontal-bore-ladder',hinge,'PETG','flat plate on bed',
         'Left to right3.2/3.3/3.4mm. Test actual ground rod, bridge sag and light reaming; do not scale entire mechanism.')
    pockets=box(72,20,4.8,z=2.4)
    for x,d in zip((-20,0,20),(6.45,6.55,6.65)):pockets=pockets.cut(cyl(d/2,1.4,3.5,x))
    for x in (-32,32):pockets=pockets.cut(cyl(1.1,-.1,5,x))
    save('D42-magnet-pocket-ladder',pockets,'PETG','flat bottom on bed',
         'Left to right6.45/6.55/6.65mm blind3.4mm pockets. Use6.35x3.175D42; test glue, polarity and trapped retention.')
    keeper=box(72,20,.8,z=.4)
    for x in (-32,32):keeper=keeper.cut(cyl(1.1,-.1,1,x))
    save('D42-test-keeper',keeper,'PETG','flat','0.8mm retention skin. Magnet fit is not assembled pull-force qualification.')
    for thickness in (.8,1.,1.2):
        save('ambient-diffuser-'+str(thickness).replace('.','p'),box(54.6,11.6,thickness,z=thickness/2),
             'translucent PETG','flat','Compare glare/hot spots and low/night brightness with the real strip at5.3mm minimum separation.')
    # Crops preserve the exact current B-rep, including the radial hard stop
    # and its corresponding TPU clearance window. These are separate pieces.
    crop=box(14,9,28,61,54.5,0)
    for name,material in [('head-right-integral-outlet','PETG'),('rigid-motor-carrier-PCD16','PETG'),
                           ('TPU-carrier-isolation-ring-development','TPU95A')]:
        s=cq.importers.importStep(str(CAD/(name+'.step'))).val().intersect(crop).clean()
        save('carrier-fit-section-'+name,s,material,'axial face on bed; orient individually in slicer',
             'Source-matched side section: test0.8mm radial TPU,0.4mm axial lips and0.3mm rigid stop gap; assess compression and captive fit.')
    post=cyl(2.4,0,5.5).fuse(cyl(1.45,5.5,2.5)).cut(cyl(.9,-.1,8.2))
    save('ambient-M1p6-post-coupon',post,'PETG','bottom face on bed',
         'Test3mm-diameter M1.6 cap head on genuine1426 hole with adjacent rear package. Nominal head clearance is only0.12mm.')
    for name in ('horizontal-encoder-mount-development','horizontal-encoder-thumbwheel-development'):
        s=cq.importers.importStep(str(CAD/(name+'.step'))).val()
        # Convert the +Y shaft to +Z and center the source-matched part on bed.
        s=s.rotate((0,0,0),(1,0,0),90)
        bounds=s.BoundingBox()
        s=s.translate((-(bounds.xmin+bounds.xmax)/2,-(bounds.ymin+bounds.ymax)/2,-bounds.zmin))
        save('front-encoder-'+name,s,'PETG','flat front plate or disk face on bed',
             'Current front encoder: test D-flat grip, nut trap, separate PCB support, in-plane rotation and actual switch travel before full base.')
    fascia=cq.importers.importStep(str(CAD/'flowing-base-open-bottom.step')).val()
    p=json.loads((CAD/'head-parameters.json').read_text())
    fascia=fascia.intersect(box(40,26,38,p['encoder_center_x']-2,164,p['encoder_center_z'])).clean()
    fascia=fascia.rotate((0,0,0),(1,0,0),90)
    b=fascia.BoundingBox();fascia=fascia.translate((-(b.xmin+b.xmax)/2,-(b.ymin+b.ymax)/2,-b.zmin))
    save('front-encoder-fascia-section',fascia,'PETG','cut rear face on bed',
         'Assemble wheel/mount/PCB here. Check rim, press force, 9.4mm projection from LCD face, screen-side hand clearance and fastener access.')
    # Optional low-cost aiming trial, not the product's fitted tilt mechanism.
    # Each rail raises the front at6deg and prints on its broad side without an
    # enclosed roof. Use both rails and nonslip pads before a stability trial.
    angle=6;length=150;rise=math.tan(math.radians(angle))*length
    wedge=cq.Workplane('YZ').polyline([(0,0),(length,0),(length,4+rise),(0,4)]).close().extrude(18).val()
    for y in (20,65,110):
        wedge=wedge.cut(box(20,24,5,9,y,5.5))
    save('aiming-6deg-trial-rail-print-two',wedge,'PETG','large X side on bed',
         'Optional paired trial under four feet. Add nonslip pads. Measure desk slip/tip under6N wheel press and cable pull; no qualified tilt claim.')
    manifest={'result':'PASS: valid printable coupon solids','timestamp_utc':datetime.now(timezone.utc).isoformat(),
        'physical_qualification':False,'parts':parts,'input_sha256':{str(p.relative_to(ROOT)):digest(p)
            for p in [Path(__file__),CAD/'head-validation.json']},
        'artifact_sha256':{str(p.relative_to(ROOT)):digest(p) for p in OUT.glob('*') if p.suffix in ('.step','.stl')}}
    (OUT/'testpiece-validation.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('PASS',len(parts),'coupon geometries; physical fit tests pending',flush=True)

if __name__=='__main__':main()
