"""Load vendor B-reps, record bounds/validity, never infer unseen Onshape assembly fit."""
from pathlib import Path
import json, cadquery as cq
ROOT=Path(__file__).resolve().parents[1]
rows=[]
for p in (ROOT/'cad/vendor').iterdir():
 if p.suffix.lower() not in ('.step','.stp') or p.name.startswith('._'):continue
 try:
  s=cq.importers.importStep(str(p)).val();b=s.BoundingBox()
  r={'file':p.name,'valid':s.isValid(),'solids':len(s.Solids()),'bounds_mm':{'x':round(b.xlen,4),'y':round(b.ylen,4),'z':round(b.zlen,4)},'origin_min_mm':[b.xmin,b.ymin,b.zmin]}
 except Exception as e:r={'file':p.name,'error':str(e)}
 rows.append(r);print(json.dumps(r),flush=True)
(ROOT/'cad/vendor-checks.json').write_text(json.dumps(rows,indent=2))
