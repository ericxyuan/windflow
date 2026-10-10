"""150 mm stage, hollow flowing shell and real purchased-part packaging.

This is a new development candidate. Rev C references and user's prior work
remain intact. All collision checks re-open the exchanged STEP independently.
Airflow +Y, all lengths mm. No fan curve, acoustic or structural release.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import math
import cadquery as cq
if __package__:
    from .rev_d_power_access import design as design_power_access
else:
    from rev_d_power_access import design as design_power_access

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'cad/rev_d'
P = json.loads((OUT/'head-parameters.json').read_text())
PARTS, RECORDS, SOURCES = {}, [], [Path(__file__), OUT/'head-parameters.json',
                                 Path(__file__).with_name('rev_d_power_access.py'),
                                 OUT/'rotor-validation.json', ROOT/'cad/rev_c/head-validation.json']
T, R = P['wall_mm'], P['throat_diameter_mm']/2


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def box(w, d, h, x=0, y=0, z=0):
    return cq.Workplane('XY').box(w, d, h).val().translate((x, y, z))


def cy(r, y, length, x=0, z=0):
    return cq.Solid.makeCylinder(r, length, cq.Vector(x, y, z), cq.Vector(0, 1, 0))


def cx(r, x, length, y=0, z=0):
    return cq.Solid.makeCylinder(r, length, cq.Vector(x, y, z), cq.Vector(1, 0, 0))


def cz(r, z, length, x=0, y=0):
    return cq.Solid.makeCylinder(r, length, cq.Vector(x, y, z), cq.Vector(0, 0, 1))


def rr(w, h, r, y, x=0, z=0):
    a, b, k = w/2, h/2, math.sqrt(.5)
    wp = cq.Workplane(cq.Plane(origin=(x, y, z), xDir=(1, 0, 0), normal=(0, -1, 0)))
    return (wp.moveTo(-a+r, -b).lineTo(a-r, -b)
            .threePointArc((a-r+r*k, -b+r-r*k), (a, -b+r)).lineTo(a, b-r)
            .threePointArc((a-r+r*k, b-r+r*k), (a-r, b)).lineTo(-a+r, b)
            .threePointArc((-a+r-r*k, b-r+r*k), (-a, b-r)).lineTo(-a, -b+r)
            .threePointArc((-a+r-r*k, -b+r-r*k), (-a+r, -b)).close().val())


def rrxy(w, d, r, z, x=0, y=0):
    return rr(w, d, r, 0).rotate((0, 0, 0), (1, 0, 0), 90).translate((x, y, z))


def record(name, shape, printed=True, source=None, one=True, material='PETG prototype'):
    assert shape.isValid() and shape.Volume() > 0, (name, 'invalid')
    if one and len(shape.Solids()) != 1:
        print('DISCONNECTED', name, [(s.Volume(), [getattr(s.BoundingBox(), k) for k in
              ('xmin', 'xmax', 'ymin', 'ymax', 'zmin', 'zmax')]) for s in shape.Solids()], flush=True)
    assert not one or len(shape.Solids()) == 1, (name, len(shape.Solids()))
    step = OUT/(name+'.step')
    cq.exporters.export(shape, str(step))
    restored = cq.importers.importStep(str(step)).val()
    assert restored.isValid() and len(restored.Solids()) == len(shape.Solids()), name
    assert abs(restored.Volume()-shape.Volume()) < max(.1, shape.Volume()*1e-5), name
    if printed:
        cq.exporters.export(restored, str(OUT/(name+'.stl')), tolerance=.06, angularTolerance=.12)
    b = restored.BoundingBox()
    RECORDS[:] = [r for r in RECORDS if r['name'] != name]
    RECORDS.append({'name': name, 'printed': printed, 'material': material,
                    'valid': True, 'solid_count': len(restored.Solids()),
                    'bounds_xyz_mm': [b.xmin, b.xmax, b.ymin, b.ymax, b.zmin, b.zmax],
                    'volume_mm3': restored.Volume(), 'source': source,
                    'sha256': digest(step)})
    PARTS[name] = restored
    print('EXPORTED', name, flush=True)
    return restored


def reuse(oldname, newname=None, shift=(0, 0, 0), printed=False):
    source = ROOT/'cad/rev_c'/(oldname+'.step')
    SOURCES.append(source)
    shape = cq.importers.importStep(str(source)).val().translate(shift)
    return record(newname or oldname, shape, printed, str(source.relative_to(ROOT)), one=False,
                  material='PETG prototype' if printed else 'Purchased/drawing reference; see source')


def at_min(oldname, xmin, ymin, zmin):
    source = ROOT/'cad/rev_c'/(oldname+'.step')
    b = cq.importers.importStep(str(source)).val().BoundingBox()
    return reuse(oldname, shift=(xmin-b.xmin, ymin-b.ymin, zmin-b.zmin))


_bounds_cache = {}


def cached_bounds(shape):
    key = id(shape)
    if key not in _bounds_cache:
        _bounds_cache[key] = (shape, shape.BoundingBox())
    return _bounds_cache[key][1]


def overlap(a, b):
    aa, bb = cached_bounds(a), cached_bounds(b)
    if any(getattr(aa, hi) <= getattr(bb, lo) or getattr(bb, hi) <= getattr(aa, lo)
           for lo, hi in (('xmin', 'xmax'), ('ymin', 'ymax'), ('zmin', 'zmax'))):
        return 0.
    return a.intersect(b).Volume()


def build():
    _bounds_cache.clear()
    OUT.mkdir(exist_ok=True)
    (OUT/'stage-build-state.json').write_text(json.dumps({'status': 'RUNNING'})+'\n')
    rotor_report = json.loads((OUT/'rotor-validation.json').read_text())
    assert rotor_report['result'] == 'PASS'
    for name, sha in rotor_report['input_sha256'].items():
        assert digest(ROOT/name) == sha, ('stale rotor source', name)
    rotor_path = OUT/'impeller-P2-150mm-GUARDED-TEST-ONLY.step'
    assert digest(rotor_path) == rotor_report['parts'][0]['sha256'][rotor_path.name]
    SOURCES.append(rotor_path)
    front, hy = P['front_y_mm'], P['panel_hinge_y_mm']
    width, height = P['outlet_width_mm'], P['outlet_height_mm']
    stations = P['outer_sections_y_w_h_r']
    outer = cq.Solid.makeLoft([rr(w, h, r, y) for y, w, h, r in stations], False)
    # A bounding plane makes the complete height a real geometric constraint.
    outer = outer.intersect(box(400, 600, P['head_height_mm'], 0, 130, 0))
    inner_stations = [rr(w-2*T, h-2*T, r-T, min(front-T, max(T, y)))
                      for y, w, h, r in stations]
    inner_exterior = cq.Solid.makeLoft(inner_stations, False)

    def transition(extra):
        profiles = []
        for u in (0, .20, .40, .60, .80, 1):
            ease = u*u*(3-2*u)
            y = P['transition_y0_mm'] + u*(P['transition_y1_mm']-P['transition_y0_mm'])
            w = 2*R*(1-ease)+width*ease+2*extra
            h = 2*R*(1-ease)+height*ease+2*extra
            radius = (R-.1)*(1-ease)+P['outlet_corner_radius_mm']*ease+extra
            profiles.append(rr(w, h, radius, y))
        return cq.Solid.makeLoft(profiles, False)

    airway = cy(R, -1, P['transition_y0_mm']+1.02).fuse(transition(0)).fuse(
        cq.Solid.makeLoft([rr(width, height, 3, hy-.02), rr(width, height, 3, front+1)], True))
    flow_envelope = cy(R+T, -1, P['transition_y0_mm']+1.02).fuse(transition(T)).fuse(
        cq.Solid.makeLoft([rr(width+2*T, height+2*T, 3+T, hy-.02),
                           rr(width+2*T, height+2*T, 3+T, front+1)], True))
    # Hollow exterior with a separate integral air duct; electronics pockets
    # are isolated from the air path by the 2.4 mm duct wall.
    shell = outer.cut(inner_exterior.cut(flow_envelope)).cut(airway)
    carrier_y, carrier_l = P['carrier_y0_mm'], P['carrier_length_mm']
    carrier_seat_r = P['carrier_outer_radius_mm']+P['carrier_radial_isolation_mm']+.15
    collar = cy(carrier_seat_r+2.4, carrier_y-2, carrier_l+4).cut(
        cy(R, carrier_y-2.1, carrier_l+4.2))
    shell = shell.fuse(collar).cut(cy(carrier_seat_r, carrier_y-.4, carrier_l+.8))
    sy, sl = P['stator_y0_mm'], P['stator_length_mm']
    shell = shell.fuse(cy(80.7, sy-1, sl+2).cut(cy(R, sy-1.1, sl+2.2)))
    shell = shell.cut(cy(P['stator_outer_radius_mm']+.3, sy-.3, sl+.6))

    # Positive bolted seam lands inside the outer skin, with flush recesses.
    for y in P['seam_screw_y_mm']:
        for z in (-87.6, 87.6):
            shell = shell.fuse(cx(4.5, -8, 16, y, z))

    # Adopt the existing matched two-panel single-servo linkage, with no new
    # linkage scale factor or incompatible hinge axes.
    mech_shift = (0, hy-110, 0)
    old_report = json.loads((ROOT/'cad/rev_c/head-validation.json').read_text())
    for item in old_report['parts']:
        if item['name'].startswith('REF-mechanism-') or item['name'] in (
                'servo-slotted-bracket-development', 'REF-FS90-FB-family-envelope-UNVERIFIED'):
            custom = item['name'].endswith(('panel-open','crank-open','yoke-open','rod-open'))
            reuse(item['name'], shift=mech_shift, printed=item['printed'] or custom)
    # Bearings attach to the permanent duct. Side mechanisms occupy the hollow
    # shoulder instead of a separate tall external fairing.
    for sign in (-1, 1):
        z = sign*height/2
        shell = shell.fuse(cx(5.0, 54, 53.5, hy, z)).fuse(cx(5.0, -70.5, 16, hy, z))
        shell = shell.cut(cx(1.65, -72, 177, hy, z))
        # Full-width hinge barrel needs a coaxial recess, including the short
        # inboard segment of the right bearing. Preserve the shaft bearing
        # beyond the barrel rather than clipping the rotating part.
        shell = shell.cut(cx(2.95, -52, 129.15, hy, z))
        shell = shell.cut(cx(3.55, 77.0, 18, hy, z))
        shell = shell.cut(cx(3.55, -69.3, 5.6, hy, z))
        shell = shell.cut(box(width-.5, P['panel_length_mm']+7, 4, 0,
                               hy+P['panel_length_mm']/2, z))
    # Cranks/yoke/rod/horn must have physical space, never an overlap waiver.
    for name in ('REF-mechanism-upper_crank-open', 'REF-mechanism-lower_crank-open',
                 'REF-mechanism-yoke-open', 'REF-mechanism-rod-open', 'REF-mechanism-horn-open'):
        b = PARTS[name].BoundingBox()
        shell = shell.cut(box(b.xlen+.6, b.ylen+12, b.zlen+.6,
                               (b.xmin+b.xmax)/2, (b.ymin+b.ymax)/2+2.5,
                               (b.zmin+b.zmax)/2))
    # Servo bracket attaches to an inward land; the outer wall remains smooth.
    b = PARTS['servo-slotted-bracket-development'].BoundingBox()
    shell = shell.cut(box(b.xlen+.6, b.ylen+.6, b.zlen+.6,
                           (b.xmin+b.xmax)/2, (b.ymin+b.ymax)/2, (b.zmin+b.zmax)/2))

    # Real rotor, rigid carrier and separate TPU ring.
    record('P2-150mm-rotor-installed-TEST-ONLY', cq.importers.importStep(str(rotor_path)).val()
           .rotate((0, 0, 0), (1, 0, 0), 180).translate((0, P['motor_prop_seat_y_assumed_mm'], 0)),
           False, str(rotor_path.relative_to(ROOT)))
    seat = P['motor_prop_seat_y_assumed_mm']
    motor = cy(15.1, seat, P['motor_mount_face_y_assumed_mm']-seat).fuse(cy(2.5, seat-8, 8))
    record('REF-P2406-manufacturer-envelope-seat-UNVERIFIED', motor, False,
           'Manufacturer 30.2 mm diameter / 16 mm M3 pitch circle, shaft shoulder not measured')
    carrier = cy(P['carrier_outer_radius_mm'], carrier_y, carrier_l).cut(
        cy(P['carrier_inner_radius_mm'], carrier_y-.1, carrier_l+.2)).fuse(cy(20, carrier_y, carrier_l))
    for angle in (45, 135, 225, 315):
        beam = box(P['carrier_inner_radius_mm']-19, carrier_l, 3.2,
                   (P['carrier_inner_radius_mm']+19)/2, carrier_y+carrier_l/2, 0)
        carrier = carrier.fuse(beam.rotate((0, 0, 0), (0, 1, 0), angle))
    for angle in (0, 90, 180, 270):
        carrier = carrier.cut(cy(P['motor_mount_clearance_mm']/2, carrier_y-.1, carrier_l+.2,
                                8*math.cos(math.radians(angle)), 8*math.sin(math.radians(angle))))
    carrier = carrier.cut(cy(4, carrier_y-.1, carrier_l+.2)).clean()
    record('P2-rigid-motor-carrier-PCD16', carrier)
    isolation = cy(carrier_seat_r-.15, carrier_y-.35, carrier_l+.7).cut(
        cy(P['carrier_outer_radius_mm'], carrier_y-.45, carrier_l+.9))
    record('P2-TPU-carrier-isolation-ring', isolation, material='TPU95A, unqualified compression')

    # Curved trial stator: inlet slope 20 degrees, trailing slope zero. Actual
    # incidence still needs a swirl survey; the angle is a tunable hypothesis.
    stator = cy(20, sy, sl).cut(cy(18, sy-.1, sl+.2))
    profiles = []
    slope = math.tan(math.radians(P['stator_inlet_angle_deg']))
    for u in (0, .25, .5, .75, 1):
        centre = slope*sl*(u-.5*u*u-.5)
        profiles.append(rr(56.1, P['stator_vane_thickness_mm'], .25,
                           sy+u*sl, x=(19.7+75.8)/2, z=centre))
    vane = cq.Solid.makeLoft(profiles, False)
    for i in range(P['stator_vane_count']):
        stator = stator.fuse(vane.rotate((0, 0, 0), (0, 1, 0), i*360/P['stator_vane_count']))
    ring = cy(P['stator_outer_radius_mm'], sy, sl).cut(cy(75.5, sy-.1, sl+.2))
    stator = stator.fuse(ring).clean()
    record('P2-seven-curved-vane-stator-TRIAL', stator)
    record('P2-stator-open-comparison-spacer', ring, True)

    # Quarter-round inlet, and fixed rear guard; no inlet-facing motor braces.
    br, k = P['bellmouth_radius_mm'], math.sqrt(.5)
    bell = (cq.Workplane('XY').moveTo(R, 0)
            .threePointArc((R+br-br*k, -br*k), (R+br, -br)).lineTo(R+br, -br+T)
            .threePointArc((R+br-(br-T)*k, -(br-T)*k), (R+T, 0)).close()
            .revolve(360, (0, 0), (0, 1)).val())
    bell = bell.fuse(cy(R+T, -.02, 4.02).cut(cy(R, -.1, 4.2)))
    bell = bell.fuse(cy(P['inlet_flange_radius_mm'], -br-T, 2.8).cut(cy(R+br-.1, -br-T-.1, 3)))
    # The bell-mouth collar is replaced by this inserted part at the rear.
    shell = shell.cut(cy(R+T+.3, -.1, 4.4))
    # Rear bulkhead joins the integral duct and outer skin beyond the inlet
    # insert seat; it occupies only the annulus outside the clear throat.
    bulkhead = outer.intersect(box(400, 3, 400, 0, 6, 0)).cut(cy(R, 4.4, 3.2))
    shell = shell.fuse(bulkhead)
    record('P2-R12-bellmouth-insert', bell)
    rear = cy(P['inlet_flange_radius_mm'], -17.1, 2.4).cut(cy(R+br-1, -17.2, 2.6))
    grid = box(190, 2.4, 1.2, 0, -15.9, 0)
    for x in range(-84, 85, 6):
        grid = grid.fuse(box(1.2, 2.4, 180, x, -15.9, 0))
    rear = rear.fuse(grid.intersect(cy(R+br-.8, -17.1, 2.4))).clean()
    record('P2-fixed-rear-inlet-guard', rear)

    # Fixed finger guard stays in place when magnetic cleaning grille is off.
    gy = P['fixed_guard_y_mm']
    guard = cq.Solid.makeLoft([rr(114, 104, 6, gy), rr(114, 104, 6, gy+2)], True).cut(
        cq.Solid.makeLoft([rr(width, height, 3, gy-.1), rr(width, height, 3, gy+2.1)], True))
    grid = box(width, 2, 1.2, 0, gy+1, 0)
    for x in range(-48, 49, 6): grid = grid.fuse(box(1.2, 2, height, x, gy+1, 0))
    guard = guard.fuse(grid.intersect(box(width, 2, height, 0, gy+1, 0))).clean()
    guard_seat = cq.Solid.makeLoft([rr(114.6, 104.6, 6.3, gy-.3), rr(114.6, 104.6, 6.3, gy+2.3)], True)
    # The downstream sleeve connects the duct, fixed guard seat and front
    # enclosure skin, including material outside the cleaning-grille recess.
    sleeve = cq.Solid.makeLoft([rr(130, 120, 10, gy-3), rr(130, 120, 10, front)], True).cut(airway)
    shell = shell.fuse(sleeve)
    shell = shell.cut(guard_seat)
    record('P2-fixed-front-finger-guard', guard)
    # A compact magnetic frame avoids the screen. Magnet pockets sit in the
    # side rails, outside the unchanged 104 x 94 airflow aperture. Two pilot
    # pins carry shear and align the grille; magnets provide pull retention.
    def front_ring(w, h, radius, y, depth):
        return cq.Solid.makeLoft([rr(w,h,radius,y),rr(w,h,radius,y+depth)], True).cut(
            cq.Solid.makeLoft([rr(width,height,3,y-.1),rr(width,height,3,y+depth+.1)],True))
    magnet_seat = front_ring(122,100,5,front-6,6)
    head_retainer = front_ring(120,100,5,front,.8)
    grille_retainer = front_ring(120,100,5,front+.8,.8)
    grille = front_ring(120,100,5,front+1.6,4.4)
    grille_grid = box(width,4.4,1.2,0,front+3.8,0)
    for x in range(-48,49,6): grille_grid=grille_grid.fuse(box(1.2,4.4,height,x,front+3.8,0))
    grille = grille.fuse(grille_grid.intersect(box(width,4.4,height,0,front+3.8,0)))
    grille = grille.fuse(box(6,2.4,16,-59,front+5.6,0))
    for x in (-55,55):
        for z in (-40,40):
            magnet_seat=magnet_seat.cut(cy(3.375,front-3.5,3.6,x,z))
            grille=grille.cut(cy(3.375,front+1.5,3.6,x,z))
            record(f'REF-head-D42-magnet-{x}-{z}',cy(3.175,front-3.3,3.175,x,z),False,
                   'K&J D42 6.35 x 3.175 mm, retention/adhesive tests required')
            record(f'REF-grille-D42-magnet-{x}-{z}',cy(3.175,front+1.7,3.175,x,z),False,
                   'K&J D42 6.35 x 3.175 mm, paired opposite polarity')
        for z in (-22,22):
            grille=grille.fuse(cy(1.2,front-1.4,3.1,x,z))
            magnet_seat=magnet_seat.cut(cy(1.5,front-1.7,1.8,x,z))
            head_retainer=head_retainer.cut(cy(1.5,front-.1,1,x,z))
            grille_retainer=grille_retainer.cut(cy(1.5,front+.7,1,x,z))
        for z in (-10,10):
            magnet_seat=magnet_seat.cut(cy(1.1,front-6.1,6.2,x,z)).cut(cy(2,front-1.2,1.3,x,z))
            head_retainer=head_retainer.cut(cy(2,front-.1,1,x,z))
            shell=shell.fuse(cy(3.6,front-9,3,x,z)).cut(cy(1.6,front-9.1,3.2,x,z))
    shell=shell.cut(cq.Solid.makeLoft([rr(122.6,100.6,5.3,front-6.3),
                                    rr(122.6,100.6,5.3,front+.1)],True))
    record('P2-fixed-magnet-seat-frame',magnet_seat.clean())
    record('head-magnet-retaining-ring-development',head_retainer.clean())
    record('grille-magnet-retaining-ring-development',grille_retainer.clean())
    record('magnetic-front-cleaning-grille-development',grille.clean())

    # Screen and encoder occupy the lower front, not a tall lower box. Wheel
    # plane stays parallel to the screen as requested.
    control_shift = (P['screen_center_x_mm'], front-170,
                     P['screen_center_z_mm']+95.5)
    for name, printed in (('REF-Adafruit-4311-IPS-vendor', False),
                          ('REF-clear-display-lens-45x34p4', False),
                          ('display-removable-cradle-development', True),
                          ('display-front-bezel-development', True),
                          ('horizontal-encoder-thumbwheel-development', True),
                          ('REF-Bourns-PEC11H-drawing-envelope', False),
                          ('encoder-daughterboard-P1-FR4', False),
                          ('REF-M7x0p75-encoder-panel-nut', False),
                          ('horizontal-encoder-mount-development', True)):
        reuse(name, shift=control_shift, printed=printed)
    sx, sz = P['screen_center_x_mm'], P['screen_center_z_mm']
    ex, ez = P['encoder_center_x_mm'], P['encoder_center_z_mm']
    shell = shell.cut(box(63, 16, 38, sx, front-1, sz))
    shell = shell.cut(box(35.6, 11, 28.6, ex+5.5, front-2.9, ez))
    shell = shell.cut(cy(15.8, front-5, 8, ex, ez))
    for x in (sx-38, sx+34):
        for z in (sz+13.9, sz-13.9):
            shell = shell.fuse(cy(4, front-15.1, 14.8, x, z)).cut(cy(2, front-15.2, 7, x, z))
    # Encoder M3 bosses and independent brace, outside the PCB and case.
    shell = shell.fuse(box(3, 25.2, 36, ex-15, front-13.7, ez))
    for z in (ez+10, ez-10):
        shell = shell.fuse(cy(3.6, front-13.1, 6.8, ex-8.5, z))
        shell = shell.fuse(box(8.5, 6.8, 4, ex-12.25, front-9.7, z))
        shell = shell.cut(cy(2, front-13.2, 6.9, ex-8.5, z))
    shell = shell.fuse(cy(17.5, front-.3, 5.7, ex, ez).cut(cy(15.8, front-.4, 5.9, ex, ez)))
    shell = shell.cut(PARTS['display-removable-cradle-development'])
    # Relief below the permanent air duct for the top of the encoder PCB and
    # mounting brace; it does not cut the clear 104 x 94 airflow passage.
    shell = shell.cut(box(36.1,11.3,5.5,ex+5.5,front-11.1,ez+13))

    # Component placement uses exact existing vendor solids. Board routing and
    # looms remain development tasks; the reserve is excluded from the export.
    at_min('Raspberry-Pi-Pico-SC0915-vendor', -87, 160, -72)
    at_min('Pololu-D24V22-5V-logic-vendor', -62, 226, -82)
    at_min('Pololu-D24V22-5V-servo-vendor', 56, 227, -82)
    at_min('Adafruit-HUSB238-5807-vendor', -94, 228, -75)
    at_min('REF-A50S-V2p3c-envelope-UNVERIFIED', 37, 151, -80)
    at_min('MCP9808-temp1-Adafruit1782-vendor', -64, 202, -77)
    at_min('MCP9808-temp2-Adafruit1782-vendor', 68, 201, -77)
    at_min('Sensirion-SDP810-125Pa-vendor', 15, 226, -82)
    at_min('Adafruit-NeoPixel-1426-ambient-vendor', -25.4, 203, -88)
    record('REF-main-PCB-population-and-loom-reserve-NOT-INTEGRATED', box(80, 55, 20, 0, 197.5, -72), False)
    # The retained side port is applied after the bolted shell split. This
    # earlier shoulder relief remains available for the output/I2C loom.
    shell = shell.cut(box(32, 20, 16, -80, 225, -69))

    # Low structural plinth and removable tray. All electronics occupy the
    # hollow head; the plinth adds only 6 mm plus 4 mm replaceable feet.
    opening = box(178, 116, 20, 0, 206, -92)
    shell = shell.cut(opening)
    plinth = cq.Solid.makeLoft([rrxy(194, 248, 22, P['plinth_bottom_z_mm'], y=139),
                                rrxy(194, 248, 22, P['plinth_top_z_mm'], y=139)], True).cut(opening)
    record('P2-low-structural-plinth', plinth)
    tray = cq.Solid.makeLoft([rrxy(174, 112, 10, P['service_tray_z0_mm'], y=206),
                             rrxy(174, 112, 10, P['service_tray_z0_mm']+2.4, y=206)], True)
    tray = tray.cut(box(54, 12, 4, 0, 208, -90.5))
    # Cradle mounting ledge projects into the tray; a relief avoids using the
    # tray as an accidental display clamp and permits independent servicing.
    tray = tray.cut(box(67,4,4,sx-2,253.3,-90.5))
    record('P2-bottom-electronics-service-tray', tray)
    diffuser = box(53.4, 11.4, .8, 0, 208, -91.4)
    record('P2-downward-ambient-diffuser', diffuser, material='Translucent PETG')
    feet = []
    for x in (-77, 77):
        for y in (38, 239): feet.append(cz(7, P['foot_bottom_z_mm'], 4, x, y))
    record('P2-replaceable-TPU-desk-feet', cq.Compound.makeCompound(feet), one=False, material='TPU95A')
    # Mounting/service implementation remains explicitly open, rather than
    # interpreting bought-part containment as insertion or fastening proof.
    cache = ROOT/'build/rev-d-cad'
    cache.mkdir(parents=True, exist_ok=True)
    cq.exporters.export(shell, str(cache/'pre-split-shell.step'))
    left = shell.intersect(box(400, 600, 400, -200, 130, 0))
    right = shell.intersect(box(400, 600, 400, 200, 130, 0))
    for y in P['seam_screw_y_mm']:
        for z in (-87.6, 87.6):
            left = left.cut(cx(1.7, -8.1, 8.2, y, z)).cut(cx(3.2, -8.1, 3.1, y, z))
            right = right.cut(cx(2, -.1, 7.1, y, z))
    left, usb, screws, nuts, coupon, trial_plug, usb_metadata = design_power_access(
        left, PARTS['Adafruit-HUSB238-5807-vendor'], P['usb_side_port'])
    record('Adafruit-HUSB238-5807-vendor', usb, False,
           'Manufacturer 5807, intact board; rotated -90 degrees about Z for side port', one=False)
    for i, shape in enumerate(screws):
        record(f'REF-PD-ISO4762-M2x6-{i+1}', shape, False,
               'ISO 4762 M2x6 ideal envelope; physical thread and driver access unqualified')
    for i, shape in enumerate(nuts):
        record(f'REF-PD-ISO4032-M2-{i+1}', shape, False,
               'ISO 4032 M2 ideal envelope; physical nut fit unqualified')
    testpieces = OUT/'testpieces'
    testpieces.mkdir(exist_ok=True)
    cq.exporters.export(coupon, str(testpieces/'USB-side-port-fit-coupon.step'))
    cq.exporters.export(coupon, str(testpieces/'USB-side-port-fit-coupon.stl'),
                        tolerance=.02, angularTolerance=.08)
    usb_metadata['trial_plug_overlap_mm3'] = overlap(left, trial_plug)
    assert usb_metadata['trial_plug_overlap_mm3'] < 1e-4
    record('P2-flowing-head-left-INTEGRAL-OUTLET', left)
    record('P2-flowing-head-right-INTEGRAL-OUTLET', right)

    # Mutually exclusive spacer and reserved PCB are not physical instances.
    excluded = {'P2-stator-open-comparison-spacer', 'REF-main-PCB-population-and-loom-reserve-NOT-INTEGRATED'}
    names = [r['name'] for r in RECORDS if r['name'] not in excluded]
    checks, issues = 0, []
    for i, a in enumerate(names):
        for b in names[i+1:]:
            checks += 1
            vol = overlap(PARTS[a], PARTS[b])
            if vol > .05: issues.append({'a': a, 'b': b, 'overlap_mm3': vol})
        if i%10==0: print('NOMINAL PAIRS',checks,'/',len(names)*(len(names)-1)//2,flush=True)
    complete_bounds = [min(r['bounds_xyz_mm'][0] for r in RECORDS if r['name'] in names),
                       max(r['bounds_xyz_mm'][1] for r in RECORDS if r['name'] in names),
                       min(r['bounds_xyz_mm'][2] for r in RECORDS if r['name'] in names),
                       max(r['bounds_xyz_mm'][3] for r in RECORDS if r['name'] in names),
                       min(r['bounds_xyz_mm'][4] for r in RECORDS if r['name'] in names),
                       max(r['bounds_xyz_mm'][5] for r in RECORDS if r['name'] in names)]
    total_height = complete_bounds[5]-complete_bounds[4]
    assert total_height <= P['maximum_product_height_mm'], total_height
    report = {'result': 'PASS' if not issues else 'FAIL - resolve collisions',
              'generated_utc': datetime.now(timezone.utc).isoformat(), 'physical_qualification': False,
              'parts': RECORDS, 'pair_checks': checks, 'unintended_issues': issues,
              'complete_bounds_xyz_mm': complete_bounds, 'complete_height_mm': total_height,
              'maximum_height_mm': P['maximum_product_height_mm'],
              'head_height_constraint_mm': P['head_height_mm'], 'excluded_alternative_and_reserves': sorted(excluded),
              'usb_side_port': usb_metadata,
              'testpiece_sha256': {str(path.relative_to(ROOT)): digest(path)
                                  for path in sorted(testpieces.glob('USB-side-port-fit-coupon.*'))},
              'input_sha256': {str(p.relative_to(ROOT)): digest(p) for p in dict.fromkeys(SOURCES)},
              'limits': ['Nominal placement only; motion, connected harness, tolerances and screw/tool approaches need revalidation.',
                         'Main PCB population, pressure hoses/taps, component retention and grille interlock are not yet integrated.',
                         'Motor/servo/ESC drawing envelopes remain unverified.',
                         'Curved stator incidence and boost benefit require physical flow/power/noise tests.',
                         'Finger guards are not a qualified printed-rotor fragment containment enclosure.',
                         'No operating speed or increased current is approved for the larger rotor.']}
    (OUT/'stage-validation.json').write_text(json.dumps(report, indent=2)+'\n')
    (OUT/'stage-build-state.json').write_text(json.dumps({'status': report['result']})+'\n')
    print(report['result'], len(names), 'part groups', checks, 'pairs; height', total_height, flush=True)
    for issue in issues: print('COLLISION', issue, flush=True)
    assert not issues, issues


if __name__ == '__main__': build()
