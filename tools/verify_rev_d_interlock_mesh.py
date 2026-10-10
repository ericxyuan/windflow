"""Check the exact six printed parts of the isolated interlock pilot."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cad.rev_d_meshes import check_mesh

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    folder = ROOT/'cad/rev_d/interlock-study'
    report_path = folder/'interlock-validation.json'
    pilot = json.loads(report_path.read_text())
    assert pilot['result'] == 'PASS' and not pilot['issues']
    for name, sha in pilot['input_sha256'].items():
        assert digest(ROOT/name) == sha, ('Stale pilot source', name)
    parts = []
    for item in pilot['parts']:
        step = folder/(item['name']+'.step')
        assert digest(step) == item['sha256'], ('Changed pilot part', item['name'])
        if not item['printed']:
            continue
        path = step.with_suffix('.stl')
        mesh = check_mesh(path, 1)
        parts.append({'name': item['name'], 'sha256': digest(path),
                      'step_sha256': item['sha256'], 'mesh': mesh})
        print('PASS' if mesh['watertight'] else 'FAIL', item['name'], mesh['triangles'], flush=True)
    assert len(parts) == 6
    result = {'result': 'PASS' if all(p['mesh']['watertight'] for p in parts) else 'FAIL',
              'generated_utc': datetime.now(timezone.utc).isoformat(),
              'physical_qualification': False, 'parts': parts,
              'input_sha256': {str(p.relative_to(ROOT)): digest(p) for p in
                               (Path(__file__), ROOT/'cad/rev_d_meshes.py', report_path)},
              'limits': ['Isolated pilot only; no main-stage integration or physical fit is established.',
                         'STL shared-edge/winding/connectivity checks do not prove print strength or switch actuation.']}
    (folder/'mesh-validation.json').write_text(json.dumps(result, indent=2)+'\n')
    print(result['result'], len(parts), 'interlock pilot meshes', flush=True)
    if result['result'] != 'PASS':
        raise SystemExit(1)

if __name__ == '__main__':
    main()
