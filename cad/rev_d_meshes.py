"""Check the exact prototype STL files for boundary, winding and connectivity."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,struct
from array import array
from collections import Counter,defaultdict

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'cad/rev_d'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def check_mesh(path, expected_components):
    data=path.read_bytes();count=struct.unpack_from('<I',data,80)[0]
    assert len(data)==84+50*count,'Invalid binary STL length'
    uses=Counter();directions=Counter();vertex_faces=defaultdict(list);points=[]
    volume=0.;degenerate=0;face_volumes=array('d')
    for i in range(count):
        r=struct.unpack_from('<12fH',data,84+50*i)
        p=[tuple(round(r[k+j],5) for j in range(3)) for k in (3,6,9)]
        points.append(p)
        if len(set(p))!=3:degenerate+=1
        for v in p:vertex_faces[v].append(i)
        for a,b in zip(p,p[1:]+p[:1]):
            key=tuple(sorted((a,b)));uses[key]+=1;directions[key]+=1 if a<b else -1
        a,b,c=p;cross=(b[1]*c[2]-b[2]*c[1],b[2]*c[0]-b[0]*c[2],b[0]*c[1]-b[1]*c[0])
        signed=sum(a[j]*cross[j] for j in range(3))/6
        volume+=signed;face_volumes.append(signed)
    visited=bytearray(count);components=0;component_volumes=[]
    for start in range(count):
        if visited[start]:continue
        components+=1;todo=[start];component_volume=0.
        while todo:
            face=todo.pop()
            if visited[face]:continue
            visited[face]=1;component_volume+=face_volumes[face]
            for v in points[face]:todo.extend(f for f in vertex_faces[v] if not visited[f])
        component_volumes.append(component_volume)
    bad=[e for e,n in uses.items() if n!=2]
    winding=sum(n!=0 for n in directions.values())
    result={'triangles':count,'connected_components':components,'expected_components':expected_components,
            'nonmanifold_or_boundary_edges':len(bad),'inconsistent_winding_edges':winding,
            'degenerate_faces':degenerate,'signed_volume_mm3':volume,
            'component_signed_volumes_mm3':component_volumes,
            'boundary_edge_examples_mm':bad[:8]}
    result['watertight']=not bad and not winding and not degenerate and all(v>0 for v in component_volumes) and components==expected_components
    return result

def refine_mesh(step,path,expected_components,original_check):
    """Retessellate the unchanged B-rep; never weld or alter printed geometry."""
    import cadquery as cq
    shape=cq.importers.importStep(str(step)).val()
    cleaned=shape.clean()
    assert cleaned.isValid() and len(cleaned.Solids())==len(shape.Solids())
    # OCC face unification changes numerical integration slightly, without
    # changing topology; bound that integration difference to 0.01 mm3.
    assert abs(cleaned.Volume()-shape.Volume())<.01
    trials=[]
    scratch=ROOT/'build/rev-d-cad/stl-refinement';scratch.mkdir(parents=True,exist_ok=True)
    candidate=scratch/path.name
    for tolerance,relative in ((.002,True),(.001,False)):
        settings={'linear_tolerance_mm':tolerance,'angular_tolerance_rad':.05,
                  'relative_deflection':relative,'parallel':False}
        cleaned.exportStl(str(candidate),tolerance=tolerance,angularTolerance=.05,
                          relative=relative,parallel=False)
        check=check_mesh(candidate,expected_components)
        error=abs(check['signed_volume_mm3']-shape.Volume())/shape.Volume()
        trials.append({'settings':settings,'mesh':check,'relative_volume_error':error})
        print('REFINE',path.name,settings,'watertight',check['watertight'],flush=True)
        if check['watertight'] and error<.001:
            old_hash=sha(path)
            # The candidate has already passed; an unsuccessful trial cannot replace it.
            path.write_bytes(candidate.read_bytes())
            return check,{'step_sha256':sha(step),'original_stl_sha256':old_hash,
                          'final_stl_sha256':sha(path),'original_mesh':original_check,
                          'cad_volume_mm3':shape.Volume(),
                          'cleanup_volume_difference_mm3':abs(cleaned.Volume()-shape.Volume()),
                          'trials':trials,'accepted_settings':settings,
                          'method':'Fresh tessellation of unchanged STEP; no vertex welding.'}
    raise RuntimeError('No watertight tessellation accepted for '+path.name)
def main():
    stage=json.loads((OUT/'stage-validation.json').read_text())
    assert stage['result']=='PASS'
    for n,h in stage['input_sha256'].items():assert sha(ROOT/n)==h,('Stale stage input',n)
    refinement_path=OUT/'stl-refinements.json'
    refinements=json.loads(refinement_path.read_text()) if refinement_path.exists() else {}
    results=[]
    for r in stage['parts']:
        if not r['printed']:continue
        name=r['name'];p=OUT/(name+'.stl')
        assert sha(OUT/(name+'.step'))==r['sha256'],('Stale STEP',name)
        check=check_mesh(p,r['solid_count'])
        if not check['watertight']:
            check,refinement=refine_mesh(OUT/(name+'.step'),p,r['solid_count'],check)
            refinements[name]=refinement
            refinement_path.write_text(json.dumps(refinements,indent=2)+'\n')
        elif name in refinements:
            assert refinements[name]['step_sha256']==r['sha256']
            assert refinements[name]['final_stl_sha256']==sha(p),('Stale refinement',name)
        status='PASS' if check['watertight'] else 'FAIL'
        results.append({'name':name,'result':status,'sha256':sha(p),
                        'step_sha256':r['sha256'],'mesh':check})
        print(status,'STL',name,check['triangles'],'triangles',check['nonmanifold_or_boundary_edges'],'bad edges',check['connected_components'],'components',flush=True)
    result={'result':'PASS' if all(r['result']=='PASS' for r in results) else 'FAIL',
            'generated_utc':datetime.now(timezone.utc).isoformat(),'physical_qualification':False,
            'parts':results,'input_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),OUT/'stage-validation.json',refinement_path]},
            'limits':['Binary STL shared-edge topology, orientation and connectivity only.',
                      'No support, slicer, dimensional tolerance, printed strength or operating permission is established.']}
    (OUT/'mesh-validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result['result'],len(results),'STL files',flush=True)
    if result['result']!='PASS':raise SystemExit(1)
if __name__=='__main__':main()
