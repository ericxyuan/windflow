"""Export the checked four-part permanent-join study for Onshape inspection."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'cad/rev_d/print-split'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    report_path = BASE/'validation.json'
    report = json.loads(report_path.read_text())
    assert report['result'] == 'PASS' and not report['issues']
    assert not report['main_stage_adopted'] and not report['physical_qualification']
    inputs = {str(Path(__file__).relative_to(ROOT)):digest(Path(__file__)),
              str(report_path.relative_to(ROOT)):digest(report_path)}
    for name, sha in report['input_sha256'].items():
        assert digest(ROOT/name) == sha, ('Stale print candidate', name)
    items = [x for x in report['parts'] if x['scope'] == 'separate manufacturing candidate']
    assert len(items) == 4
    assembly = cq.Assembly(name='Rev-D-permanent-manufacturing-join-CANDIDATE')
    shapes = []
    for item in items:
        source = BASE/(item['name']+'.step')
        assert digest(source) == item['step_sha256']
        inputs[str(source.relative_to(ROOT))] = digest(source)
        shape = cq.importers.importStep(str(source)).val()
        assert shape.isValid() and len(shape.Solids()) == 1
        shapes.append(shape)
        rear = '-rear-' in item['name']
        color = cq.Color(.72, .78, .81) if rear else cq.Color(.26, .36, .39)
        assembly.add(shape, name=item['name'], color=color)
    path = BASE/'Windflow-Rev-D-permanent-print-join-CANDIDATE.step'
    assembly.save(str(path), exportType='STEP', mode='default')
    loaded = cq.importers.importStep(str(path)).val()
    difference = abs(loaded.Volume()-sum(s.Volume() for s in shapes))
    assert loaded.isValid() and len(loaded.Solids()) == 4 and difference < .05
    record = {'result':'PASS', 'scope':'Separate four-print manufacturing study for inspection',
              'generated_utc':datetime.now(timezone.utc).isoformat(),
              'main_stage_adopted':False, 'physical_qualification':False,
              'named_groups':4, 'round_trip_solids':4,
              'round_trip_volume_difference_mm3':difference,
              'input_sha256':inputs, 'path':str(path.relative_to(ROOT)),
              'sha256':digest(path), 'bytes':path.stat().st_size,
              'limits':['No adhesive volume, process or strength is modeled or qualified.',
                        'This study does not replace the complete 108-instance development assembly.',
                        'The final outlet is integral to each forward enclosure print; bond before hardware installation.']}
    (BASE/'integration-export-validation.json').write_text(json.dumps(record, indent=2)+'\n')
    print('PASS four-part STEP round trip; volume difference', difference, flush=True)


if __name__ == '__main__':
    main()
