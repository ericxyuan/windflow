"""Partition the current head into permanent rear/forward manufacturing prints.

Straight axial joggle masks divide the existing material. No positive material
is added to the airpath, exterior or component pockets. This is a separate
manufacturing candidate; it never overwrites the adopted assembly geometry.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import math
import sys

import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'cad'))
from rev_d_meshes import check_mesh

BASE = ROOT / 'cad/rev_d'
OUT = BASE / 'print-split'
OFFSET_RECORDS = []


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def box(w, d, h, x=0., y=0., z=0.):
    return cq.Workplane('XY').box(w, d, h).val().translate((x, y, z))


def rr(w, h, radius, y):
    a, b, k = w / 2, h / 2, math.sqrt(.5)
    wp = cq.Workplane(cq.Plane(origin=(0, y, 0), xDir=(1, 0, 0), normal=(0, -1, 0)))
    return (wp.moveTo(-a + radius, -b).lineTo(a - radius, -b)
            .threePointArc((a-radius+radius*k, -b+radius-radius*k), (a, -b+radius))
            .lineTo(a, b-radius).threePointArc((a-radius+radius*k, b-radius+radius*k), (a-radius, b))
            .lineTo(-a+radius, b).threePointArc((-a+radius-radius*k, b-radius+radius*k), (-a, b-radius))
            .lineTo(-a, -b+radius).threePointArc((-a+radius-radius*k, -b+radius-radius*k), (-a+radius, -b))
            .close().val())


def transition(p, extra):
    profiles = []
    radius = p['throat_diameter_mm'] / 2
    for u in (0., .2, .4, .6, .8, 1.):
        ease = u*u*(3-2*u)
        y = p['transition_y0_mm'] + u*(p['transition_y1_mm']-p['transition_y0_mm'])
        width = 2*radius*(1-ease)+p['outlet_width_mm']*ease+2*extra
        height = 2*radius*(1-ease)+p['outlet_height_mm']*ease+2*extra
        corner = (radius-.1)*(1-ease)+p['outlet_corner_radius_mm']*ease+extra
        profiles.append(rr(width, height, corner, y))
    return cq.Solid.makeLoft(profiles, False)


def section_wire(shape, y):
    cut = shape.intersect(cq.Face.makeFromWires(rr(600., 600., 1., y)))
    faces = cut.Faces()
    assert len(faces) == 1 and not faces[0].innerWires(), 'Unexpected divider section'
    return faces[0].outerWire()


def offset_wire(wire, delta):
    wires = wire.offset2D(delta)
    assert len(wires) == 1, 'Divider offset disconnected'
    before = cq.Face.makeFromWires(wire).Area()
    after = cq.Face.makeFromWires(wires[0]).Area()
    assert (after-before)*delta > 0, 'Offset direction differs from the expected inside/outside'
    # OCC's offset curves can form extrusion surfaces which its STEP reader
    # drops, reopening the solid as an open shell. Convert these divider curves
    # to supported NURBS before extrusion, and bound the representation change.
    converted = wires[0].toNURBS()
    area_difference = abs(cq.Face.makeFromWires(converted).Area()-after)
    assert area_difference < max(.001, wires[0].Length()*.0001)
    assert abs(converted.Length()-wires[0].Length()) < .001
    distances = []
    for a, b in [(wires[0], converted), (converted, wires[0])]:
        for edge in a.Edges():
            for sample in range(21):
                point = edge.positionAt(sample/20)
                distances.append(cq.Vertex.makeVertex(point.x, point.y, point.z).distance(b))
    assert max(distances) < .0001, 'Divider conversion moved beyond its numerical allowance'
    OFFSET_RECORDS.append({'offset_mm':delta, 'bidirectional_distance_samples':len(distances),
                           'maximum_sampled_deviation_mm':max(distances),
                           'area_integration_difference_mm2':area_difference})
    return converted


def prism(wire, start_y, length):
    moved = wire.translate((0, start_y-wire.Center().y, 0))
    return cq.Solid.extrudeLinear(moved, [], cq.Vector(0, length, 0))


def volume_overlap(a, b):
    aa, bb = a.BoundingBox(), b.BoundingBox()
    if any(getattr(aa, hi) <= getattr(bb, lo) or getattr(bb, hi) <= getattr(aa, lo)
           for lo, hi in [('xmin', 'xmax'), ('ymin', 'ymax'), ('zmin', 'zmax')]):
        return 0.
    return a.intersect(b).Volume()


def lip_samples(rear, forward, cut, lap, gap, p, side, source):
    """Radial section samples, not a global minimum-wall-thickness proof."""
    records = []
    sign = -1. if side == 'left' else 1.
    for y in [cut+gap+.05, cut+lap/2, cut+lap-.05]:
        for angle in [-80., -60., -40., -20., 0., 20., 40., 60., 80.]:
            theta = math.radians(angle)
            ray = cq.Edge.makeLine(cq.Vector(sign*35*math.cos(theta), y, 35*math.sin(theta)),
                                   cq.Vector(sign*140*math.cos(theta), y, 140*math.sin(theta)))
            parent_count = len(source.intersect(ray).Edges())
            assert parent_count > 0, 'Probe missed the parent material'
            for label, shape in [('rear', rear), ('forward', forward)]:
                lengths = [edge.Length() for edge in shape.intersect(ray).Edges()]
                # The bottom electronics opening removes outer skin at some
                # angles; compare with this exact parent, not an assumed tube.
                assert len(lengths) == parent_count, ('Missing parent-wall lip', label, y, angle, lengths)
                assert min(lengths) >= p['minimum_nominal_lip_mm'], ('Thin sampled lip', label, y, angle, lengths)
                records.append({'part':label, 'y_mm':y, 'angle_degrees':angle,
                                'parent_material_intervals':parent_count,
                                'radial_lip_lengths_mm':lengths})
    return records


def mesh_export(shape, path):
    # Validate each exact accepted STL. A failed trial stays in the ignored
    # build folder and cannot replace an accepted manufacturing article.
    scratch = ROOT/'build/rev-d-cad/print-split'
    scratch.mkdir(parents=True, exist_ok=True)
    trial = scratch/path.name
    attempts = []
    for linear, angular in [(.02, .08), (.005, .06), (.001, .05)]:
        shape.exportStl(str(trial), tolerance=linear, angularTolerance=angular,
                        relative=False, parallel=False)
        checked = check_mesh(trial, len(shape.Solids()))
        error = abs(checked['signed_volume_mm3']-shape.Volume())/shape.Volume()
        attempts.append({'linear_tolerance_mm':linear, 'angular_tolerance_rad':angular,
                         'mesh':checked, 'relative_volume_error':error})
        print('MESH', path.name, linear, checked['watertight'], checked['triangles'], flush=True)
        if checked['watertight'] and error < .001:
            assert trial.stat().st_size < 100*1024*1024, 'STL exceeds the repository file limit'
            path.write_bytes(trial.read_bytes())
            return {'sha256':digest(path), 'bytes':path.stat().st_size,
                    'accepted_settings':attempts[-1], 'attempts':attempts}
    raise RuntimeError('No accepted mesh: '+str(path))


def print_orientation(shape, rear, p):
    # Print each lip last from its full-thickness parent wall. The forward
    # fascia has protruding features and will need accessible local supports.
    rotated = shape.rotate((0, 0, 0), (1, 0, 0), 90 if rear else -90)
    b = rotated.BoundingBox()
    reserve = p['bed_edge_reserve_mm']
    translated = rotated.translate((reserve-b.xmin, reserve-b.ymin, -b.zmin))
    b = translated.BoundingBox()
    dims = [b.xlen, b.ylen, b.zlen]
    assert dims[0]+2*reserve <= p['bed_size_xy_mm'][0]
    assert dims[1]+2*reserve <= p['bed_size_xy_mm'][1]
    assert abs(translated.Volume()-shape.Volume()) < .01
    return translated, {'rotation_x_degrees':90 if rear else -90,
                        'bed_edge_reserve_mm':reserve, 'dimensions_xyz_mm':dims,
                        'translation_xyz_mm':[reserve-rotated.BoundingBox().xmin,
                                              reserve-rotated.BoundingBox().ymin,
                                              -rotated.BoundingBox().zmin]}


def main():
    OFFSET_RECORDS.clear()
    p = json.loads((OUT/'parameters.json').read_text())
    head = json.loads((BASE/'head-parameters.json').read_text())
    stage = json.loads((BASE/'stage-validation.json').read_text())
    assert stage['result'] == 'PASS'
    for n, sha in stage['input_sha256'].items():
        assert digest(ROOT/n) == sha, ('Stale parent stage', n)
    cut, lap, gap = p['split_y_mm'], p['lap_length_mm'], p['bondline_clearance_mm']
    assert cut >= head['stator_y0_mm']+head['stator_length_mm']+2.
    assert cut+lap+gap < head['panel_hinge_y_mm'], 'Final nozzle must remain integral'
    t = head['wall_mm']
    outer_mid = cq.Solid.makeLoft([rr(w-t, h-t, r-t/2, y)
                                  for y, w, h, r in head['outer_sections_y_w_h_r']], False)
    reference_y = cut+lap/2
    outer_wire = section_wire(outer_mid, reference_y)
    duct_wire = section_wire(transition(head, t/2), reference_y)
    base_mask = box(800., 600., 800., 0, cut-300., 0)
    band = prism(outer_wire, cut, lap).cut(prism(duct_wire, cut-.01, lap+.02))
    rear_mask = base_mask.fuse(band)
    outer_clearance = prism(offset_wire(outer_wire, gap), cut, lap+gap)
    duct_clearance = prism(offset_wire(duct_wire, -gap), cut-.01, lap+gap+.02)
    clear_mask = box(800., 600., 800., 0, cut+gap-300., 0).fuse(outer_clearance.cut(duct_clearance))
    records, checks, all_issues, candidates = [], [], [], {}
    inputs = [Path(__file__), OUT/'parameters.json', BASE/'head-parameters.json',
              BASE/'stage-validation.json', ROOT/'cad/rev_d_meshes.py']
    for side in ['left', 'right']:
        name = f'P2-flowing-head-{side}-INTEGRAL-OUTLET'
        source_path = BASE/(name+'.step')
        expected = next(item['sha256'] for item in stage['parts'] if item['name'] == name)
        assert digest(source_path) == expected, ('Changed parent article', name)
        inputs.append(source_path)
        source = cq.importers.importStep(str(source_path)).val()
        rear = source.intersect(rear_mask).clean()
        forward = source.cut(clear_mask).clean()
        nominal_forward = source.cut(rear)
        # Three small stops restore only axial bondline material in the outer
        # skin. They register the nominal axial datum without filling long laps.
        sign = -1. if side == 'left' else 1.
        outer_b = cq.Face.makeFromWires(outer_wire).BoundingBox()
        stops = [(0., head['head_height_mm']/2-t/2),
                 (0., -head['head_height_mm']/2+t/2),
                 (sign*outer_b.xlen/2, 0.)]
        pad_volumes = []
        for x, z in stops:
            cylinder = cq.Solid.makeCylinder(p['registration_pad_radius_mm'], gap+1.,
                                              cq.Vector(x, cut, z), cq.Vector(0, 1, 0))
            pad = nominal_forward.intersect(cylinder)
            if pad.Volume() > 1e-5:
                pad_volumes.append(pad.cut(forward).Volume())
                forward = forward.fuse(pad)
            else:
                pad_volumes.append(0.)
        forward = forward.clean()
        assert rear.isValid() and forward.isValid()
        assert len(rear.Solids()) == len(forward.Solids()) == 1, ('Disconnected print', side)
        assert rear.cut(source).Volume() < .01 and forward.cut(source).Volume() < .01
        assert volume_overlap(rear, forward) < .01
        removed = source.cut(rear.fuse(forward))
        # No inserted obstruction is possible: both pieces are subsets of the
        # original validated head. The adhesive volume is deliberately omitted.
        result = {'side':side, 'parent_volume_mm3':source.Volume(),
                  'removed_bondline_volume_mm3':removed.Volume(),
                  'registration_pad_volumes_mm3':pad_volumes,
                  'positive_volume_outside_parent_mm3':rear.cut(source).Volume()+forward.cut(source).Volume()}
        result['lip_section_samples'] = lip_samples(rear, forward, cut, lap, gap, p, side, source)
        for sample in range(p['assembly_samples']):
            distance = p['withdrawal_distance_mm']*sample/(p['assembly_samples']-1)
            value = volume_overlap(rear, forward.translate((0, distance, 0)))
            checks.append({'side':side, 'forward_offset_y_mm':distance, 'overlap_mm3':value})
            if value > .01:
                all_issues.append({'kind':'axial_join', **checks[-1]})
        print('JOIN', side, max(c['overlap_mm3'] for c in checks if c['side']==side), flush=True)
        for tag, shape in [('rear', rear), ('forward-INTEGRAL-OUTLET', forward)]:
            stem = f'P2-{side}-{tag}-PERMANENT-JOIN-CANDIDATE'
            path = OUT/(stem+'.step')
            cq.exporters.export(shape, str(path))
            restored = cq.importers.importStep(str(path)).val()
            assert restored.isValid() and len(restored.Solids()) == 1, ('STEP did not reopen as a solid', stem)
            assert abs(restored.Volume()-shape.Volume()) < .05
            printable, pose = print_orientation(restored, tag=='rear', p)
            mesh = mesh_export(printable, OUT/(stem+'-PRINT.stl'))
            records.append({'name':stem, 'scope':'separate manufacturing candidate',
                            'step_sha256':digest(path), 'mesh':mesh, 'print_pose':pose,
                            'volume_mm3':restored.Volume(), 'side_joint':result})
            candidates[(side, tag)] = restored
        # Crop actual outer-wall and duct sections, not simplified rectangular
        # approximations, to test lip fit and the selected permanent bond process.
        if side == 'left':
            for label, x, w in [('outer-wall', -outer_b.xlen/2, 14.),
                                ('duct-wall', -cq.Face.makeFromWires(duct_wire).BoundingBox().xlen/2, 10.)]:
                crop = box(w, p['coupon_axial_length_mm'], p['coupon_height_mm'],
                           x, reference_y, 0.)
                for tag, shape in [('rear', rear), ('forward', forward)]:
                    coupon = shape.intersect(crop).clean()
                    assert coupon.isValid() and len(coupon.Solids()) == 1, (label, tag)
                    stem = f'{label}-{tag}-fit-bond-coupon'
                    path = OUT/(stem+'.step')
                    cq.exporters.export(coupon, str(path))
                    printable, pose = print_orientation(coupon, tag=='rear', p)
                    mesh = mesh_export(printable, OUT/(stem+'-PRINT.stl'))
                    records.append({'name':stem, 'scope':'fit/bond coupon', 'step_sha256':digest(path),
                                    'mesh':mesh, 'print_pose':pose, 'volume_mm3':coupon.Volume()})
    report = {'result':'PASS' if not all_issues else 'FAIL',
              'generated_utc':datetime.now(timezone.utc).isoformat(),
              'physical_qualification':False, 'main_stage_adopted':False,
              'parent_geometry_commit':'490e61d5d556170cc9f5e24441dd916cae07fa5e',
              'split_y_mm':cut, 'lap_length_mm':lap, 'bondline_clearance_mm':gap,
              'divider_reference_y_mm':reference_y, 'parts':records, 'join_checks':checks,
              'divider_curve_representation':OFFSET_RECORDS,
              'issues':all_issues, 'input_sha256':{str(q.relative_to(ROOT)):digest(q) for q in inputs},
              'assembly_protocol':'Bond rear and forward head prints into each permanent head half before installing rotor, stator, electronics or looms. Final nozzle stays integral to the forward enclosure.',
              'limits':['Candidate print envelopes, native shape and STL topology only; not an approved print process.',
                        'Support removal, lip thickness, coupon fit, seal finish, adhesive choice/strength, creep and print warping require further review or physical tests.',
                        'The primary 108-group Onshape assembly and stage are unchanged; this candidate is not an online geometry update.',
                        'No airflow performance, fragment containment, structural strength or operating RPM qualification.']}
    (OUT/'validation.json').write_text(json.dumps(report, indent=2)+'\n')
    print(report['result'], len(records), 'prints/coupons;', len(checks), 'axial join comparisons', flush=True)
    if all_issues:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
