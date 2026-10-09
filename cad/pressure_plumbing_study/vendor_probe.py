import cadquery as cq,json,os,sys
from pathlib import Path
from OCP.BRepAdaptor import BRepAdaptor_Surface
p=Path('cad/rev_b/Sensirion-SDP810-125Pa-vendor.step');s=cq.importers.importStep(str(p)).val();r=[]
for i,b in enumerate(s.Solids()):
 bb=b.BoundingBox();q={'solid':i,'box':[bb.xmin,bb.xmax,bb.ymin,bb.ymax,bb.zmin,bb.zmax],'cylinders':[]}
 for f in b.Faces():
  if f.geomType()=='CYLINDER':
   c=BRepAdaptor_Surface(f.wrapped).Cylinder();a=c.Axis().Location();d=c.Axis().Direction();fb=f.BoundingBox()
   q['cylinders'].append({'radius':c.Radius(),'origin':[a.X(),a.Y(),a.Z()],'direction':[d.X(),d.Y(),d.Z()],'box':[fb.xmin,fb.xmax,fb.ymin,fb.ymax,fb.zmin,fb.zmax]})
 r.append(q)
Path('cad/pressure_plumbing_study/vendor-port-inspection.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2),flush=True);sys.stdout.flush();os._exit(0)
