"""Check display screw-head and rear-tip envelopes against the installed base.

This supplements the body/service-path checks. It does not model threads, torque,
heat-set installation or the complete hand/tool sweep.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import sys
import cadquery as cq

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'rev_b'
manifest = json.loads((OUT / 'base-validation.json').read_text())
parts = {f[:-5]: cq.importers.importStep(str(OUT / f)).val()
         for f in manifest['assembly_files']}

def overlap(a, b):
    aa, bb = a.BoundingBox(), b.BoundingBox()
    if any(getattr(aa, k + 'max') <= getattr(bb, k + 'min') + 1e-5 or
           getattr(bb, k + 'max') <= getattr(aa, k + 'min') + 1e-5 for k in 'xyz'):
        return 0.0
    return max(0.0, a.intersect(b).Volume())

checks = []
issues = []
for index, f in enumerate(manifest['fasteners']):
    if f['location'] not in ('4311 display PCB', 'display removable cradle', 'display front bezel'):
        continue
    x, y, z = f['axis_mm']
    # ISO4762 nominal maximum head envelopes: M2 dk3.8,k2; M3 dk5.5,k3.
    m3 = f['location'] == 'display removable cradle'
    radius, height = (2.75, 3.0) if m3 else (1.9, 2.0)
    direction = 1 if m3 else -1  # Screw advances into the joint along this Y sign.
    head = cq.Solid.makeCylinder(radius, height, cq.Vector(x, y, z), cq.Vector(0, -direction, 0))
    geometries = {'head': head}
    if f['location'] == '4311 display PCB':
        # M2x12 projects slightly beyond the rear of the cradle's captive nut.
        geometries['rear tip'] = cq.Solid.makeCylinder(1.0, 1.0,
            cq.Vector(x, y - 12, z), cq.Vector(0, 1, 0))
    for name, solid in geometries.items():
        worst = 0.0
        for other, body in parts.items():
            v = overlap(solid, body)
            worst = max(worst, v)
            if v > .01:
                issues.append({'mount': index, 'location': f['location'], 'envelope': name,
                               'other': other, 'overlap_mm3': v})
        checks.append({'mount': index, 'location': f['location'], 'axis_mm': [x, y, z],
                       'envelope': name, 'maximum_overlap_mm3': worst})

report = {'completed_utc': datetime.now(timezone.utc).isoformat(),
    'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'base_manifest_sha256': hashlib.sha256((OUT / 'base-validation.json').read_bytes()).hexdigest(),
    'checks': checks, 'intersections_to_resolve': issues,
    'source': 'ISO4762 head envelopes from Bossard BN610/BN8 supplier tables: M2 dk3.8/k2; M3 dk5.5/k3',
    'references': ['https://nederland.bossard.com/en-us/standard-fastening-elements/screws/screws-and-bolts-with-internal-drive/912x00200020003',
      'https://www.traceparts.com/en/product/bossard-bn-610-din-912-iso-4762-hex-socket-head-cap-screws-fully-threaded?Product=34-04042013-122015'],
    'limits': ['Nominal heads/rear tips only; threads and intentional nut/insert engagement excluded',
              'No tolerance, pullout, hand or complete driver sweep qualification',
              'Verify purchased screw head dimensions; other head styles require a fresh check']}
(OUT / 'display-fastener-validation.json').write_text(json.dumps(report, indent=2) + '\n')
print(f'DISPLAY FASTENER CHECK: {len(checks)} envelopes; {len(issues)} intersections', flush=True)
sys.stdout.flush()
os._exit(1 if issues else 0)
