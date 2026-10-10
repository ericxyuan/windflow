"""Validate the exact USB-C fit-coupon STL after the B-rep study passes."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from cad.rev_d_meshes import check_mesh

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    folder=ROOT/'cad/rev_d/power-access-study'
    report=folder/'power-access-validation.json'
    study=json.loads(report.read_text())
    assert study['result']=='PASS'
    for name,sha in study['input_sha256'].items():assert digest(ROOT/name)==sha,('Stale study',name)
    step=folder/'USB-side-port-fit-coupon.step'
    stl=folder/'USB-side-port-fit-coupon.stl'
    expected=next(p['sha256'] for p in study['parts'] if p['name']=='USB-side-port-fit-coupon')
    assert digest(step)==expected
    mesh=check_mesh(stl,1)
    assert mesh['watertight'],mesh
    result={'result':'PASS','generated_utc':datetime.now(timezone.utc).isoformat(),
            'physical_qualification':False,'mesh':mesh,
            'geometry_sha256':{str(p.relative_to(ROOT)):digest(p) for p in (step,stl)},
            'input_sha256':{str(p.relative_to(ROOT)):digest(p) for p in
                            (Path(__file__),ROOT/'cad/rev_d_meshes.py',report)},
            'limits':['Mesh topology only; supplied cable, print fit, retention and assembly tools remain unqualified.']}
    (folder/'coupon-mesh-validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS',mesh['triangles'],'triangles; one component; zero boundary/winding/degenerate edges',flush=True)

if __name__=='__main__':main()
