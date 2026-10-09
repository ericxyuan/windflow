"""150 mm five-blade, cambered/twisted/forward-swept axial development rotor.

Produces B-reps, printable fit articles and independent geometry checks. The
pitch-design speed is a geometry input, never an approved operating speed.
The Rev C 112 mm source and its artifacts are preserved.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import math
import sys
import cadquery as cq
from rev_c_rotor import mesh_check

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'cad/rev_d'
P = json.loads((OUT / 'rotor-parameters.json').read_text(encoding='utf-8'))


def cy(r, y, length):
    return cq.Solid.makeCylinder(r, length, cq.Vector(0, y, 0), cq.Vector(0, 1, 0))


def section(radius, chord, thickness, lead, trail, camber, sweep, pitch):
    """Finite rounded edges, smooth camber, sweep about the rotor axis.

    Forward sweep is +local tangential Z for the intended negative-angle
    rotation viewed from downstream before the installation transform.
    This is a defined prototype profile, not an airfoil performance database.
    """
    sine, cosine = math.sin(pitch), math.cos(pitch)
    sweep_r = math.radians(sweep)

    def v(s, t):
        z = s * cosine - t * sine
        return cq.Vector(radius * math.cos(sweep_r) - z * math.sin(sweep_r),
                         P['section_center_y_mm'] + s * sine + t * cosine,
                         radius * math.sin(sweep_r) + z * math.cos(sweep_r))

    def tangent(sign):
        return cq.Vector(-sign * cosine * math.sin(sweep_r), sign * sine,
                         sign * cosine * math.cos(sweep_r))

    front, rear = -chord/2 + lead, chord/2 - trail
    upper = [(front, lead), (-chord*.24, thickness/2+camber),
             (chord*.10, thickness*.46+camber),
             (chord*.28, thickness*.34+camber*.5), (rear, trail)]
    lower = [(rear, -trail), (chord*.28, -thickness*.34+camber*.5),
             (chord*.10, -thickness*.46+camber),
             (-chord*.24, -thickness/2+camber), (front, -lead)]
    return cq.Wire.assembleEdges([
        cq.Edge.makeSpline([v(*pt) for pt in upper], tangents=(tangent(1), tangent(1))),
        cq.Edge.makeThreePointArc(v(rear, trail), v(chord/2, 0), v(rear, -trail)),
        cq.Edge.makeSpline([v(*pt) for pt in lower], tangents=(tangent(-1), tangent(-1))),
        cq.Edge.makeThreePointArc(v(front, -lead), v(-chord/2, 0), v(front, lead))])


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export(name, shape, mesh=True):
    assert shape.isValid() and len(shape.Solids()) == 1 and shape.Volume() > 0, name
    step = OUT/(name+'.step')
    cq.exporters.export(shape, str(step))
    restored = cq.importers.importStep(str(step)).val()
    assert restored.isValid() and len(restored.Solids()) == 1, name
    delta = abs(restored.Volume()-shape.Volume())
    assert delta < max(.01, shape.Volume()*1e-5), (name, delta)
    result = {'name': name, 'valid_solid': True, 'step_round_trip': True,
              'round_trip_volume_difference_mm3': delta,
              'volume_mm3': shape.Volume(), 'sha256': {step.name: digest(step)}}
    if mesh:
        stl = OUT/(name+'.stl')
        cq.exporters.export(shape, str(stl), tolerance=.025, angularTolerance=.075)
        result['mesh'] = mesh_check(stl)
        result['sha256'][stl.name] = digest(stl)
    b = restored.BoundingBox()
    result['bounds_xyz_mm'] = [b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax]
    print('EXPORTED', name, flush=True)
    return result


def build():
    OUT.mkdir(exist_ok=True)
    (OUT/'rotor-build-state.json').write_text(json.dumps({'status': 'RUNNING'})+'\n')
    keys = ('section_radii_mm', 'section_chords_mm', 'section_max_thickness_mm',
            'section_leading_radius_mm', 'section_trailing_radius_mm',
            'section_camber_mm', 'section_forward_sweep_deg')
    assert len({len(P[k]) for k in keys}) == 1
    assert P['approved_operating_rpm'] is None
    raw = list(zip(*(P[k] for k in keys)))
    hub_r, blend = P['hub_diameter_mm']/2, P['hub_root_blend_radius_mm']
    flare_r = [hub_r + blend*q for q in (0, .03, .10, .22, .40, .62, .82, 1)]
    radii = sorted(set(P['section_radii_mm'] + flare_r))
    omega = P['pitch_design_rpm']*2*math.pi/60
    wires, stations = [], []

    def interpolate(r):
        for a, b in zip(raw, raw[1:]):
            if a[0] <= r <= b[0]:
                t = (r-a[0])/(b[0]-a[0])
                return [r] + [a[i]*(1-t)+b[i]*t for i in range(1, len(keys))]
        raise ValueError(r)

    for r in radii:
        r, chord, thick, lead, trail, camber, sweep = interpolate(r)
        q = min(blend, max(0, r-hub_r))
        flare = blend - math.sqrt(max(0, blend**2-(q-blend)**2))
        chord += 2*flare
        thick += 2*flare
        lead += flare
        trail += flare
        pitch = math.atan2(P['pitch_design_axial_velocity_m_s'], omega*r/1000)
        pitch += math.radians(P['pitch_incidence_deg'])
        wires.append(section(r, chord, thick, lead, trail, camber, sweep, pitch))
        stations.append({'radius_mm': r, 'chord_mm': chord, 'section_thickness_mm': thick,
                         'leading_edge_diameter_mm': 2*lead,
                         'trailing_edge_diameter_mm': 2*trail, 'camber_mm': camber,
                         'forward_sweep_deg': sweep, 'pitch_deg': math.degrees(pitch),
                         'root_flare_mm': flare,
                         'local_solidity': P['blade_count']*chord/(2*math.pi*r)})
    join = radii.index(hub_r+blend)
    blade = cq.Solid.makeLoft(wires[:join+1], True).fuse(
        cq.Solid.makeLoft(wires[join:], False)).clean()
    blade = blade.intersect(cy(P['rotor_diameter_mm']/2,
                              P['minimum_motor_side_axial_clearance_mm'],
                              P['hub_length_mm']-P['minimum_motor_side_axial_clearance_mm'])).clean()
    assert blade.isValid() and len(blade.Solids()) == 1
    hub = cq.Workplane(obj=cy(hub_r, 0, P['hub_length_mm'])).edges().fillet(
        P['hub_outer_round_mm']).val()
    rotor = hub
    for i in range(P['blade_count']):
        rotor = rotor.fuse(blade.rotate((0, 0, 0), (0, 1, 0), i*360/P['blade_count']))
    rotor = rotor.cut(cy(P['nut_access_diameter_mm']/2, P['clamp_web_mm'],
                         P['hub_length_mm'])).cut(cy(P['shaft_bore_mm']/2, -.1,
                                                     P['hub_length_mm']+.2)).clean()
    result = export('impeller-P2-150mm-GUARDED-TEST-ONLY', rotor)

    coupon = cq.Workplane('XY').box(54, 20, P['clamp_web_mm']).val().translate(
        (0, 0, P['clamp_web_mm']/2))
    for x, bore in ((-17, 5.1), (0, 5.2), (17, 5.3)):
        coupon = coupon.cut(cq.Solid.makeCylinder(bore/2, P['clamp_web_mm']+.2,
                                                 cq.Vector(x, 0, -.1)))
    coupon_result = export('P2-M5-clamp-web-fit-coupon', coupon.clean())
    # A static root section helps evaluate print orientation and support scars.
    root_coupon = rotor.intersect(cq.Workplane('XY').box(80, 60, 28).val().translate((25, 15, 0)))
    if len(root_coupon.Solids()) == 1:
        coupon_result_root = export('P2-root-and-edge-stationary-coupon', root_coupon)
    else:
        raise AssertionError(('root coupon disconnected', len(root_coupon.Solids())))

    # Checks operate on the separately reopened STEP, never the live Boolean.
    restored = cq.importers.importStep(str(OUT/'impeller-P2-150mm-GUARDED-TEST-ONLY.step')).val()
    duct = cy(P['duct_throat_diameter_mm']/2, -1, P['hub_length_mm']+2)
    outside = restored.cut(duct).Volume()
    assert outside < 1e-6, outside
    points = restored.tessellate(.025, .075)[0]
    max_radius = max(math.hypot(v.x, v.z) for v in points)
    assert max_radius <= P['rotor_diameter_mm']/2+1e-4
    # 120 mm wedge reach exceeds the complete 75 mm rotor radius.
    half = math.pi/P['blade_count']
    wedge = (cq.Workplane(cq.Plane(origin=(0, -1, 0), xDir=(1, 0, 0), normal=(0, 1, 0)))
             .polyline([(0, 0), (120*math.cos(half), -120*math.sin(half)),
                        (120*math.cos(half), 120*math.sin(half))])
             .close().extrude(P['hub_length_mm']+2).val())
    sectors = [restored.intersect(wedge.rotate((0, 0, 0), (0, 1, 0), i*360/P['blade_count'])).Volume()
               for i in range(P['blade_count'])]
    spread = max(sectors)-min(sectors)
    assert spread < restored.Volume()*1e-4, sectors
    centroid = restored.Center()
    radial_centroid = math.hypot(centroid.x, centroid.z)
    assert radial_centroid < .005, radial_centroid
    rho = P['material_density_kg_m3_for_mass_estimate']
    mass = restored.Volume()*rho*1e-9
    bm = blade.Volume()*rho*1e-9
    bc = blade.Center()
    cases = []
    for speed in P['analytical_rpm_cases']:
        w = speed*2*math.pi/60
        cases.append({'rpm': speed, 'tip_speed_m_s': w*P['rotor_diameter_mm']/2000,
                      'single_blade_centrifugal_load_N': bm*w*w*math.hypot(bc.x, bc.z)/1000,
                      'kinetic_energy_upper_bound_J': .5*mass*(P['rotor_diameter_mm']/2000)**2*w*w,
                      'operating_permission': False})
    sources = [Path(__file__), OUT/'rotor-parameters.json', ROOT/'cad/rev_c_rotor.py',
               ROOT/'rotor_selection/docs/fan-shape-analysis-2026-10-09.md']
    report = {'result': 'PASS', 'revision': P['revision'],
              'generated_utc': datetime.now(timezone.utc).isoformat(),
              'runtime': {'python': sys.version, 'cadquery': cq.__version__},
              'physical_qualification': False, 'approved_operating_rpm': None,
              'input_sha256': {str(p.relative_to(ROOT)): digest(p) for p in sources},
              'parts': [result, coupon_result, coupon_result_root], 'sections': stations,
              'nominal_radial_tip_gap_mm': (P['duct_throat_diameter_mm']-P['rotor_diameter_mm'])/2,
              'outside_duct_volume_mm3': outside, 'maximum_tessellated_radius_mm': max_radius,
              'equal_angle_sector_volumes_mm3': sectors, 'sector_spread_mm3': spread,
              'nominal_radial_centroid_mm': radial_centroid,
              'estimated_mass_g': mass*1000, 'analytical_cases': cases,
              'limits': ['Section pitch-design velocity and RPM are not performance predictions.',
                         'Swept planform and finite edges are prototype choices, not CFD/FEA or noise proof.',
                         'M5 shoulder, nut thread and motor screw depth require measurement.',
                         'No operating speed, print strength, balance or containment is qualified.',
                         '150 mm rotor does not inherit 112 mm motor/rotor commissioning values.']}
    (OUT/'rotor-section-profiles.json').write_text(json.dumps({'sections': [
        dict(st, points_xyz_mm=[list(e.positionAt(j/12).toTuple()) for e in wire.Edges() for j in range(12)])
        for st, wire in zip(stations, wires)]}, indent=2)+'\n')
    (OUT/'rotor-validation.json').write_text(json.dumps(report, indent=2)+'\n')
    (OUT/'rotor-build-state.json').write_text(json.dumps({'status': 'PASS'})+'\n')
    print('PASS P2 rotor; nominal mass g', mass*1000, 'sector spread mm3', spread, flush=True)


if __name__ == '__main__':
    build()
