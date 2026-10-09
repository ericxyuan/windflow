"""Reconstruct missing inherited placements from hash-pinned manufacturer CAD.

Existing placed references are validated and preserved. Download vendor assets
with fetch_assets.py first. Regenerate validation reports after reconstruction.
"""
from pathlib import Path
import hashlib,json
import cadquery as cq

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'cad/rev_d/vendor-model-inputs.json'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check(shape,row):
    b=shape.BoundingBox()
    size_error=max(abs(a-bb) for a,bb in zip(row['target_size_xyz_mm'],[b.xlen,b.ylen,b.zlen]))
    assert size_error<.001,(row['name'],'dimensions',size_error)
    actual=[]
    for s in shape.Solids():
        c=s.Center();actual.append([s.Volume(),c.x,c.y,c.z])
    expected=row['solid_signatures_volume_center_xyz']
    assert len(actual)==len(expected),(row['name'],'body count')
    for e in expected:
        errors=[max(abs(a-bb) for a,bb in zip(e,r)) for r in actual]
        i=min(range(len(errors)),key=errors.__getitem__)
        assert errors[i]<.002,(row['name'],'body volume/centroid',errors[i])
        actual.pop(i)
def main():
    manifest=json.loads(MANIFEST.read_text())
    for row in manifest['models']:
        source=(ROOT/row['source']).resolve();target=(ROOT/row['target']).resolve()
        assert source.is_relative_to(ROOT/'cad/vendor') and target.is_relative_to(ROOT/'cad/rev_c')
        assert source.exists(),('Download vendor source first',row['source'],row['download']['url'])
        assert digest(source)==row['source_sha256'],('Vendor source differs',row['source'])
        if target.exists():
            check(cq.importers.importStep(str(target)).val(),row)
            print('PRESERVED',row['name'],flush=True)
            continue
        shape=cq.importers.importStep(str(source)).val()
        for axis,angle in row['rotation_axes_degrees']:shape=shape.rotate((0,0,0),tuple(axis),angle)
        b=shape.BoundingBox();minimum=[b.xmin,b.ymin,b.zmin]
        shape=shape.translate(tuple(a-bb for a,bb in zip(row['target_min_xyz_mm'],minimum)))
        check(shape,row)
        target.parent.mkdir(parents=True,exist_ok=True)
        cq.exporters.export(shape,str(target))
        check(cq.importers.importStep(str(target)).val(),row)
        print('RECONSTRUCTED',row['name'],flush=True)
    print('PASS',len(manifest['models']),'vendor placement inputs; fresh CAD reports still required',flush=True)
if __name__=='__main__':main()
