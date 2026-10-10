"""Verify the exact small test-print outputs declared by the current stage."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from cad.rev_d_meshes import check_mesh

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    folder=ROOT/'cad/rev_d';report_path=folder/'stage-validation.json'
    stage=json.loads(report_path.read_text())
    assert stage['result']=='PASS'
    assert json.loads((folder/'stage-build-state.json').read_text())['status']=='PASS'
    for name,sha in stage['input_sha256'].items():assert digest(ROOT/name)==sha,('Stale stage',name)
    results=[]
    geometry=stage['testpiece_sha256']
    for name,sha in geometry.items():
        path=ROOT/name;assert digest(path)==sha,('Changed test piece',name)
        if path.suffix=='.stl':
            mesh=check_mesh(path,1);assert mesh['watertight'],(name,mesh)
            results.append({'path':name,'mesh':mesh,'sha256':sha})
    assert results,'No declared test-print meshes'
    result={'result':'PASS','generated_utc':datetime.now(timezone.utc).isoformat(),
            'physical_qualification':False,'parts':results,'geometry_sha256':geometry,
            'input_sha256':{str(p.relative_to(ROOT)):digest(p) for p in
                            (Path(__file__),ROOT/'cad/rev_d_meshes.py',report_path)},
            'limits':['Mesh topology only; physical print/plug/fastener/driver fit remains unqualified.']}
    (folder/'testpieces/testpiece-validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS',len(results),'current small test-print meshes',flush=True)

if __name__=='__main__':main()
