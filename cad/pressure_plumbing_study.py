"""Concrete pressure-hose and sensor-orientation study, independent of main CAD.

The frozen input files preserve the state against which this nominal study was
checked. REF fittings are drawing-based envelopes, not vendor STEP models.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import math
import os
import shutil
import sys
import cadquery as cq

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'pressure_plumbing_study'
BASELINE = OUT / 'baseline'
OUT.mkdir(exist_ok=True)
BASELINE.mkdir(exist_ok=True)
HEAD_Z = 10.0
R_OUT = 7.14375 / 2
R_IN = 3.96875 / 2
R_BEND = 15.0

manifest_file = BASELINE / 'base-validation.json'
if not manifest_file.exists():
    shutil.copyfile(ROOT / 'rev_b/base-validation.json', manifest_file)
    manifest = json.loads(manifest_file.read_text())
    for filename in manifest['assembly_files']:
        if 'driver-carrier' not in filename:
            shutil.copyfile(ROOT / 'rev_b' / filename, BASELINE / filename)
    for filename in ('head-left-integral-outlet.step', 'head-right-integral-outlet.step'):
        shutil.copyfile(ROOT / 'rev_b' / filename, BASELINE / filename)
    for filename in ('build_base.py', 'build_head.py', 'parameters.json', 'pico_mount.py'):
        if (ROOT / filename).exists():
            shutil.copyfile(ROOT / filename, BASELINE / filename)
manifest = json.loads(manifest_file.read_text())

def box(w, d, h, x, y, z):
    return cq.Workplane('XY').box(w, d, h).translate((x, y, z)).val()

def cyl(r, length, p, direction):
    return cq.Solid.makeCylinder(r, length, cq.Vector(*p), cq.Vector(*direction))

def overlap(a, b):
    aa, bb = a.BoundingBox(), b.BoundingBox()
    if any(getattr(aa, k+'max') <= getattr(bb, k+'min')+1e-6 or
           getattr(bb, k+'max') <= getattr(aa, k+'min')+1e-6 for k in 'xyz'):
        return 0.0
    return max(0.0, a.intersect(b).Volume())

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

parts = {f[:-5]: cq.importers.importStep(str(BASELINE/f)).val()
         for f in manifest['assembly_files'] if 'driver-carrier' not in f}
for name in ('head-left-integral-outlet', 'head-right-integral-outlet'):
    parts[name] = cq.importers.importStep(str(BASELINE/(name+'.step'))).val().translate((0, 0, HEAD_Z))

from pressure_plumbing_study import geometry as pressure_geometry
layout = pressure_geometry.make_pressure_layout(HEAD_Z)
positive = layout['positive']; reference = layout['reference']; loop_y = layout['loop_y']
head_center = layout['head_center']; ref_center = layout['reference_center']
original_sensor = parts.pop('Sensirion-SDP810-125Pa-vendor')
original_board = parts.pop('REF-SDP810-daughterboard-required-outline')
sensor = pressure_geometry.sensor_transform(original_sensor)
board = pressure_geometry.daughterboard()
tray = parts.pop('electronics-service-tray')
frozen_tray = tray
for support in pressure_geometry.original_supports():
    tray = tray.cut(support)
# Repair only the old tray floor, preserving ambient channels and all other features.
floor = box(180,140,2.4,15,65,-115.8)
tray = tray.fuse(floor.intersect(frozen_tray))
shell = parts.pop('electronics-base-shell')
shell, tray = pressure_geometry.apply_base(shell,tray,layout)
head = parts.pop('head-left-integral-outlet')
head = pressure_geometry.apply_head(head,layout)
parts['STUDY-head-left-pressure-receiver'] = head
parts['STUDY-SDP810-rotated-vendor'] = sensor
parts['STUDY-SDP810-rotated-daughterboard-outline'] = board
candidate = {'STUDY-electronics-service-tray-pressure':tray,'STUDY-electronics-base-shell-pressure':shell,**layout['parts']}
sleeves = layout['sleeves']
connector_path = box(7.5,6,3,54.5,2.2,-103)
clamps = {n:b for n,b in candidate.items() if n.endswith('wall-clip')}
issues = []
checks = []
# The receiver and its fitting are intentionally bonded/captured, and installed
# hose sleeves intentionally encompass the sensor/nylon barbs. Record those
# interfaces explicitly; no other nominal collision is ignored.
intentional = [
    frozenset(('STUDY-head-left-pressure-receiver', 'REF-Arkplas-MCX19-NY2-head-elbow')),
    frozenset(('STUDY-electronics-service-tray-pressure', 'REF-Arkplas-MCX19-NY2-reference-elbow')),
    frozenset(('STUDY-SDP810-rotated-vendor', 'REF-Tygon-ACF00010-positive-hose')),
    frozenset(('STUDY-SDP810-rotated-vendor', 'REF-Tygon-ACF00010-reference-hose')),
    frozenset(('REF-Arkplas-MCX19-NY2-head-elbow', 'REF-Tygon-ACF00010-positive-hose')),
    frozenset(('REF-Arkplas-MCX19-NY2-reference-elbow', 'REF-Tygon-ACF00010-reference-hose')),
    frozenset(('STUDY-electronics-base-shell-pressure', 'tpu-pressure-ceiling-split-grommet')),
]
all_parts = {**parts, **candidate}
for index, (name, body) in enumerate(candidate.items()):
    assert body.isValid(), name
    assert len(body.Solids()) == 1, (name, len(body.Solids()))
    for other, obstacle in parts.items():
        volume = overlap(body, obstacle)
        checks.append({'a': name, 'b': other, 'overlap_mm3': volume})
        if volume > .01 and frozenset((name, other)) not in intentional:
            issues.append(checks[-1])
    for other, obstacle in list(candidate.items())[index+1:]:
        volume = overlap(body, obstacle)
        checks.append({'a': name, 'b': other, 'overlap_mm3': volume})
        if volume > .01 and frozenset((name, other)) not in intentional:
            issues.append(checks[-1])
    print('CHECKED '+name, flush=True)

for name, sleeve in sleeves.items():
    for other, obstacle in all_parts.items():
        if 'hose' in other or 'rotated-vendor' in other or 'MCX19' in other:
            continue
        volume = overlap(sleeve, obstacle)
        checks.append({'a': name, 'b': other, 'overlap_mm3': volume})
        if volume > .01:
            issues.append(checks[-1])

path_checks = []
for name, obstacle in all_parts.items():
    if name in ('REF-pressure-board-solder-tail-exit-reserve',):
        continue
    volume = overlap(connector_path, obstacle)
    path_checks.append({'connector_path': name, 'overlap_mm3': volume})
    if volume > .01:
        issues.append(path_checks[-1])

printable = {'pressure-head-elbow-capture', 'pressure-reference-elbow-capture',
             'pressure-reference-ambient-baffle', 'tpu-pressure-ceiling-split-grommet',
             *clamps}
for name, body in {**candidate, 'STUDY-head-left-pressure-receiver': head,
                   'STUDY-SDP810-rotated-vendor': sensor,
                   'STUDY-SDP810-rotated-daughterboard-outline': board,
                   **sleeves}.items():
    cq.exporters.export(body, str(OUT/(name+'.step')))
    if name in printable:
        cq.exporters.export(body, str(OUT/(name+'.stl')), tolerance=.08, angularTolerance=.15)

# Conservative Hagen-Poiseuille equivalent length, useful for static sensor
# through-flow error estimates only; no CFD, acoustic or fan restriction claim.
equiv_elbow = 2*17.653*(3.96875/2.54)**4
equiv_head = 3.0*(3.96875/2.54)**4
equiv_ref = 5.2*(3.96875/2.54)**4
report = {
    'completed_utc': datetime.now(timezone.utc).isoformat(),
    'script_sha256': digest(Path(__file__)),
    'geometry_sha256': digest(OUT/'geometry.py'),
    'baseline_sha256': {str(p.relative_to(OUT)): digest(p) for p in BASELINE.iterdir() if p.is_file()},
    'tube': {'manufacturer': 'Saint-Gobain', 'model': 'Tygon E-3603 ACF00010',
             'id_mm': 3.96875, 'od_mm': 7.14375, 'minimum_published_bend_radius_mm': 12.7,
             'minimum_design_centerline_bend_radius_mm': 15,
             'nominal_installed_centerline_length_each_mm': positive.length,
             'trial_cut_length_each_mm': math.ceil(positive.length+10),
             'cut_instruction': 'Cut both equally with10mm trial service allowance; fit without reducing bends, trim only after checking sensor/head seating.'},
    'positive_route': positive.segments,
    'reference_route': reference.segments,
    'reference_loop': {'radius_mm': 34, 'angle_deg': 270, 'center_xy_mm': [55, loop_y]},
    'sensor_transform': {'rotation_z_deg': 180, 'center_xy_mm': [54.5, 21.525], 'delta_z_mm': -.5,
                         'ports_xyz_mm': [[48.2, 34.8, -93.025], [60.8, 34.8, -93.025]],
                         'housing_mounts_xyz_mm': [[66.5,21.55,-97.525],[42.5,21.55,-97.525]],
                         'daughterboard_minimum_xyz_mm': [45.5,9.2,-106.275]},
    'fitting': {'manufacturer': 'Ark-Plas', 'model': 'MCX19-NY2',
                'overall_mm': 22.352, 'body_mm': 9.398, 'center_to_tip_mm': 17.653,
                'maximum_barb_mm': 5.8928, 'published_three_decimal_tolerance_mm': .127,
                'drawing_url': 'https://arkplas.com/document/view/44761',
                'head_center_xyz_mm': head_center, 'reference_center_xyz_mm': ref_center,
                'model_limitation': 'Published dimensions with conservative undimensioned full-max-barb cylinder; not exact tapered CAD.'},
    'reference_ambient_port': {'downward_xyz_mm': [ref_center[0], ref_center[1], -117],
                              'protected_by_baffle': True},
    'hose_retention': 'Clearance clamps on tray, split ceiling grommet; removable elbow capture collars; housing restraints take hose loads.',
    'pressure_equivalent_4mm_hose_lengths_mm': {
        'positive_including_two_leg_elbow_and_short_tap': positive.length+equiv_elbow+equiv_head,
        'reference_including_two_leg_elbow_and_lid_bore': reference.length+equiv_elbow+equiv_ref,
        'comparison': 'Both below1m screening limit from Sensirion engineering guide; laminar equivalent-length calculation assumes smooth bores and does not establish transient response.'},
    'nominal_static_pairs_checked': len(checks), 'connector_corridor_checks': len(path_checks),
    'intersections_to_resolve': issues,
    'intentional_interface_pairs': [sorted(x) for x in intentional],
    'artifact_sha256': {p.name: digest(p) for p in OUT.iterdir() if p.suffix in ('.step', '.stl')},
    'limitations': ['Separate nominal study; not adopted in main CAD or Onshape.',
                    'Carrier is unpopulated. The reference hose reserves a low lane over the board; future components/connectors must respect the exported hose envelope.',
                    'Pressure daughterboard and downward connector are mechanical reserves, not an electrical PCB or proven connector model.',
                    'FDM receiver bores need reaming and airtight seal testing; mechanically captured RTV seals require actual material compatibility and leak testing.',
                    'Sensor port P1/P2 identity and signal sign must be verified before commissioning; physical hose fit, flow response and quiet-reference bias are untested.',
                    '10mm trial service allowance is not included in the tight nominal swept path; physical slack needs routing and removal validation.',
                    'M2 screws/nuts and insertion tools not yet integrated in this study; collars are geometric mounting interfaces only.'],
}
(OUT/'validation.json').write_text(json.dumps(report, indent=2))
print(json.dumps({k:v for k,v in report.items() if k not in ('baseline_sha256','artifact_sha256','positive_route','reference_route')},indent=2),flush=True)
sys.stdout.flush(); sys.stderr.flush(); os._exit(1 if issues else 0)
