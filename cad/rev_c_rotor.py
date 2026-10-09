"""Parametric Rev C low-speed FDM impeller test article; all lengths mm.

Axis +Y, motor prop-seat datum Y=0. This produces actual closed B-reps and
watertight meshes, not CFD, stress qualification, or permission to spin them.
Run with .tools/rev-c-cad-venv/Scripts/python.exe cad/rev_c_rotor.py.
"""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter, defaultdict
import hashlib
import json
import math
import struct
import sys
from importlib.metadata import version

import cadquery as cq

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "rev_c"
P = json.loads((OUT / "rotor-parameters.json").read_text(encoding="utf-8"))


def cy(radius, y, length):
    return cq.Solid.makeCylinder(radius, length, cq.Vector(0, y, 0), cq.Vector(0, 1, 0))


def profile(radius, chord, thickness, lead, trail, camber, pitch):
    """Rounded four-edge section. Both nose and tail are true semicircles.

    Chord coordinate is tangential +Z. Positive pitch gives positive +Y
    geometric pitch for negative-angle rotation when viewed from downstream.
    FDM-rounded tails deliberately trade drag for durable finite thickness.
    """
    sine, cosine = math.sin(pitch), math.cos(pitch)

    def v(s, t):
        return cq.Vector(radius, P["section_center_y_mm"] + s * sine + t * cosine,
                         s * cosine - t * sine)

    front, rear = -chord / 2 + lead, chord / 2 - trail
    upper = [(front, lead), (-chord * .24, thickness / 2 + camber),
             (chord * .10, thickness * .46 + camber),
             (chord * .28, thickness * .34 + camber * .5), (rear, trail)]
    lower = [(rear, -trail), (chord * .28, -thickness * .34 + camber * .5),
             (chord * .10, -thickness * .46 + camber),
             (-chord * .24, -thickness / 2 + camber), (front, -lead)]
    return cq.Wire.assembleEdges([
        cq.Edge.makeSpline([v(*point) for point in upper], tangents=(cq.Vector(0, sine, cosine), cq.Vector(0, sine, cosine))),
        cq.Edge.makeThreePointArc(v(rear, trail), v(chord / 2, 0), v(rear, -trail)),
        cq.Edge.makeSpline([v(*point) for point in lower], tangents=(cq.Vector(0, -sine, -cosine), cq.Vector(0, -sine, -cosine))),
        cq.Edge.makeThreePointArc(v(front, -lead), v(-chord / 2, 0), v(front, lead)),
    ])


def mesh_check(path):
    """Check exported binary STL shared edges, orientation and connectivity."""
    data = path.read_bytes()
    count = struct.unpack_from("<I", data, 80)[0]
    assert len(data) == 84 + 50 * count, (path, "not binary STL")
    edge_uses = Counter()
    edge_directions = Counter()
    vertex_faces = defaultdict(list)
    vertices = set()
    volume = 0.0
    face_points = []
    for i in range(count):
        raw = struct.unpack_from("<12fH", data, 84 + i * 50)
        points = [tuple(round(raw[k + q], 5) for q in range(3)) for k in (3, 6, 9)]
        assert len(set(points)) == 3, (path, i, "degenerate face")
        face_points.append(points)
        for point in points:
            vertices.add(point)
            vertex_faces[point].append(i)
        for a, b in zip(points, points[1:] + points[:1]):
            key = tuple(sorted((a, b)))
            edge_uses[key] += 1
            edge_directions[key] += 1 if a < b else -1
        a, b, c = points
        cross = (b[1] * c[2] - b[2] * c[1], b[2] * c[0] - b[0] * c[2],
                 b[0] * c[1] - b[1] * c[0])
        volume += sum(a[k] * cross[k] for k in range(3)) / 6
    bad_edges = sum(n != 2 for n in edge_uses.values())
    bad_winding = sum(n != 0 for n in edge_directions.values())
    todo, visited = [0], set()
    while todo:
        face = todo.pop()
        if face in visited:
            continue
        visited.add(face)
        for point in face_points[face]:
            todo.extend(other for other in vertex_faces[point] if other not in visited)
    assert bad_edges == 0 and bad_winding == 0 and len(visited) == count
    assert volume > 0
    return {"triangles": count, "unique_vertices": len(vertices),
            "nonmanifold_or_boundary_edges": bad_edges,
            "inconsistent_winding_edges": bad_winding, "connected_components": 1,
            "signed_volume_mm3": volume, "watertight": True}


def export(name, shape):
    assert shape.isValid(), name + " invalid"
    assert len(shape.Solids()) == 1 and shape.Volume() > 0, name
    step, stl = OUT / (name + ".step"), OUT / (name + ".stl")
    cq.exporters.export(shape, str(step))
    cq.exporters.export(shape, str(stl), tolerance=.025, angularTolerance=.075)
    roundtrip = cq.importers.importStep(str(step)).val()
    assert roundtrip.isValid() and len(roundtrip.Solids()) == 1
    volume_difference = abs(roundtrip.Volume() - shape.Volume())
    assert volume_difference <= max(.01, shape.Volume() * 1e-5), (name, "STEP volume delta", volume_difference, shape.Volume())
    bounds = shape.BoundingBox()
    print("EXPORTED", name, flush=True)
    return {"name": name, "valid_solid": True, "solids": 1,
            "step_round_trip": True, "step_round_trip_volume_difference_mm3": volume_difference,
            "bounds_mm": [bounds.xlen, bounds.ylen, bounds.zlen],
            "volume_mm3": shape.Volume(), "mesh": mesh_check(stl),
            "sha256": {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in (step, stl)}}


def build():
    OUT.mkdir(exist_ok=True)
    rpm = P["pitch_design_rpm"]
    omega = rpm * 2 * math.pi / 60
    station_data = []
    wires = []
    keys = ("section_radii_mm", "section_chords_mm", "section_max_thickness_mm",
            "section_leading_radius_mm", "section_trailing_radius_mm", "section_camber_mm")
    assert len({len(P[key]) for key in keys}) == 1
    raw_stations = list(zip(*(P[key] for key in keys)))
    # Root transition is built into the blade sections. A quarter-circle offset
    # grows the section smoothly into the hub instead of relying on a fragile
    # multi-spline rolling-ball operation. It has vertical tangent at the hub
    # and zero slope at the outer end. The loft is the approximation to those
    # analytic section offsets; it is not claimed to be an exact surface fillet.
    blend_radius = P["hub_root_blend_radius_mm"]
    hub_radius = P["hub_diameter_mm"] / 2
    flare_radii = [hub_radius + blend_radius * q for q in (0, .03, .10, .22, .40, .62, .82, 1)]
    all_radii = sorted(set(P["section_radii_mm"] + flare_radii))

    def interpolated_station(radius):
        for a, b in zip(raw_stations, raw_stations[1:]):
            if a[0] <= radius <= b[0]:
                t = (radius - a[0]) / (b[0] - a[0])
                return [radius] + [a[i] * (1 - t) + b[i] * t for i in range(1, 6)]
        raise ValueError(radius)

    for radius in all_radii:
        radius, chord, thick, lead, trail, camber = interpolated_station(radius)
        q = max(0, min(blend_radius, radius - hub_radius))
        flare = blend_radius - math.sqrt(max(0, blend_radius ** 2 - (q - blend_radius) ** 2))
        chord += 2 * flare
        thick += 2 * flare
        lead += flare
        trail += flare
        pitch = math.atan2(P["pitch_design_axial_velocity_m_s"], omega * radius / 1000)
        pitch += math.radians(P["pitch_incidence_deg"])
        wires.append(profile(radius, chord, thick, lead, trail, camber, pitch))
        station_data.append({"radius_mm": radius, "chord_mm": chord,
                             "maximum_thickness_nominal_mm": thick,
                             "leading_edge_diameter_mm": 2 * lead,
                             "trailing_edge_diameter_mm": 2 * trail,
                             "root_flare_offset_mm": flare,
                             "pitch_deg": math.degrees(pitch)})
    root_index = all_radii.index(hub_radius + blend_radius)
    root_blend = cq.Solid.makeLoft(wires[:root_index + 1], True)
    outer_blade = cq.Solid.makeLoft(wires[root_index:], False)
    blade = root_blend.fuse(outer_blade).clean()
    blade = blade.intersect(cy(P["rotor_diameter_mm"] / 2,
                              P["minimum_motor_side_axial_clearance_mm"],
                              P["hub_length_mm"] - P["minimum_motor_side_axial_clearance_mm"])).clean()
    assert blade.isValid() and len(blade.Solids()) == 1
    hub = cy(P["hub_diameter_mm"] / 2, 0, P["hub_length_mm"])
    hub = cq.Workplane(obj=hub).edges().fillet(P["hub_outer_round_mm"]).val()
    rotor = hub
    for i in range(P["blade_count"]):
        rotor = rotor.fuse(blade.rotate((0, 0, 0), (0, 1, 0), 360 * i / P["blade_count"]))
    rotor = rotor.clean()
    print("ROOT BLEND RADIUS", blend_radius, "STATIONS", len(flare_radii), flush=True)
    rotor = rotor.cut(cy(P["nut_access_diameter_mm"] / 2, P["clamp_web_mm"], 30))
    rotor = rotor.cut(cy(P["shaft_bore_mm"] / 2, -.1, 30)).clean()
    assert rotor.isValid() and len(rotor.Solids()) == 1
    result = export("impeller-P1-GUARDED-TEST-ONLY", rotor)

    # Three bore fits plus an exact thin clamp-web/washer seating ring; these
    # are stationary fit coupons, never a substitute for rotor spin proof.
    coupon = cq.Workplane("XY").box(54, 20, P["clamp_web_mm"]).translate((0, 0, P["clamp_web_mm"] / 2)).val()
    for x, bore in ((-17, 5.1), (0, 5.2), (17, 5.3)):
        coupon = coupon.cut(cq.Solid.makeCylinder(bore / 2, 4, cq.Vector(x, 0, -.1)))
    coupon_result = export("M5-shaft-clamp-fit-coupon", coupon.clean())

    blade_mass = blade.Volume() * P["material_density_kg_m3_for_mass_estimate"] * 1e-9
    blade_com = blade.Center()
    blade_com_radius = math.hypot(blade_com.x, blade_com.z) / 1000
    mass = rotor.Volume() * P["material_density_kg_m3_for_mass_estimate"] * 1e-9
    analyses = []
    for speed in (P["pitch_design_rpm"], P["analytical_overspeed_case_rpm"]):
        angular_speed = speed * 2 * math.pi / 60
        # Integrating r^2 over tessellated closed volume is unnecessary here:
        # m*R^2/2 is NOT a precise rotor inertia. Use m*R^2 upper bound.
        radius_m = P["rotor_diameter_mm"] / 2000
        analyses.append({"rpm": speed, "tip_velocity_m_s": angular_speed * radius_m,
                         "blade_centrifugal_load_N_one_blade_estimate": blade_mass * angular_speed ** 2 * blade_com_radius,
                         "rotor_kinetic_energy_upper_bound_J": .5 * mass * radius_m ** 2 * angular_speed ** 2,
                         "not_structural_or_operating_qualification": True})
    bounds = rotor.BoundingBox()
    # OCC's conservative B-spline bounding boxes can extend beyond a plane by
    # more than its modeling tolerance. Test actual volume, not that bound.
    motor_side_intrusion = rotor.intersect(cy(100, -10, 9.999)).Volume()
    assert motor_side_intrusion < 1e-7, ("motor-side intrusion", motor_side_intrusion)
    blade_surface_points = blade.tessellate(.025, .075)[0]
    blade_motor_side_clearance = min(point.y for point in blade_surface_points)
    assert blade_motor_side_clearance >= P["minimum_motor_side_axial_clearance_mm"] - 1e-5
    duct = cy(P["duct_throat_diameter_mm"] / 2, -1, 50)
    outside = rotor.cut(duct).Volume()
    assert outside < 1e-7
    # Coincident-surface Boolean differences are unreliable on reparameterized
    # fillet B-splines. Validate final CAD mass distribution using five disjoint
    # equal-angle sectors and its radial center of mass instead.
    half_angle = math.pi / P["blade_count"]
    wedge = (cq.Workplane(cq.Plane(origin=(0, -1, 0), xDir=(1, 0, 0), normal=(0, 1, 0)))
             .polyline([(0, 0), (100 * math.cos(half_angle), -100 * math.sin(half_angle)),
                        (100 * math.cos(half_angle), 100 * math.sin(half_angle))])
             .close().extrude(50).val())
    sector_volumes = [rotor.intersect(wedge.rotate((0, 0, 0), (0, 1, 0), 360 * i / P["blade_count"])).Volume()
                      for i in range(P["blade_count"])]
    sector_spread = max(sector_volumes) - min(sector_volumes)
    assert sector_spread < rotor.Volume() * 1e-4, ("sector volume spread", sector_volumes)
    centroid = rotor.Center()
    radial_centroid = math.hypot(centroid.x, centroid.z)
    assert radial_centroid < .005, ("nominal CAD imbalance", radial_centroid)
    profile_guide = {"axis": P["axis"], "sections": [dict(station, points_xyz_mm=[
        list(edge.positionAt(j / 12).toTuple()) for edge in wire.Edges() for j in range(12)])
        for station, wire in zip(station_data, wires)]}
    (OUT / "rotor-section-profiles.json").write_text(json.dumps(profile_guide, indent=2) + "\n", encoding="utf-8")
    report = {"revision": P["revision"], "generated_utc": datetime.now(timezone.utc).isoformat(),
              "runtime": {"python": sys.version, "cadquery": cq.__version__, "cadquery_ocp": version("cadquery-ocp")},
              "source_sha256": {str(path.relative_to(ROOT.parent)): hashlib.sha256(path.read_bytes()).hexdigest()
                                for path in (Path(__file__), OUT / "rotor-parameters.json")},
              "parts": [result, coupon_result], "sections": station_data,
              "root_blend_radius_mm": blend_radius, "root_blend_stations": len(flare_radii),
              "root_blend_method": "Lofted quarter-circle section flare, not an exact rolling-ball fillet",
              "radial_tip_clearance_nominal_mm": (P["duct_throat_diameter_mm"] - P["rotor_diameter_mm"]) / 2,
              "outside_duct_volume_mm3": outside, "motor_side_intrusion_beyond_0p001mm_mm3": motor_side_intrusion,
              "blade_motor_side_clearance_tessellated_mm": blade_motor_side_clearance,
              "final_equal_angle_sector_volumes_mm3": sector_volumes,
              "final_equal_angle_sector_volume_spread_mm3": sector_spread,
              "final_radial_centroid_offset_mm": radial_centroid,
              "shaft_bore_mm": P["shaft_bore_mm"], "clamp_web_mm": P["clamp_web_mm"],
              "nut_access_diameter_mm": P["nut_access_diameter_mm"],
              "estimated_rotor_mass_g": mass * 1000, "estimated_single_blade_mass_g_before_hub_union": blade_mass * 1000,
              "calculation_cases": analyses, "rotor_axial_extent_mm": [bounds.ymin, bounds.ymax],
              "validation_scope": "B-rep, mesh, nominal dimensions and isolated duct containment only. No CFD/FEA/spin/fit/balance evidence.",
              "physical_requirements": ["Measure actual shaft shoulder, prop-seat OD and usable M5 thread; test clamp coupon and washers/nut engagement",
                                        "Check radial runout, concentricity and static/dynamic balance of actual print",
                                        "Guarded containment spin tests with tachometer and independent overspeed cutoff, staged below 3000rpm",
                                        "Qualify fatigue, creep, layer adhesion, temperature, print defects and nut retention",
                                        "Revalidate rear/front guards and rotor axial clearances in completed Rev C assembly",
                                        "Measure fan curves, noise and outlet velocity; geometric pitch does not guarantee target flow"]}
    (OUT / "rotor-validation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"valid": True, "mass_g": mass * 1000, "cases": analyses, "parts": len(report["parts"])}), flush=True)


if __name__ == "__main__":
    build()
