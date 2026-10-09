"""Independent, dimensioned fan isolation repair; does not mutate Rev B sources.

Coordinates match check_assembly.py: airflow +Y, fan centre Z=head_center_height.
Printed exports are explicitly free-state geometry; the assembly uses a separate
compressed-pad envelope. Smooth fasteners are nominal references, not thread CAD.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import math
import os
import sys
import traceback
import cadquery as cq
from OCP.BRepAdaptor import BRepAdaptor_Surface

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'fan_mount_study'
OUT.mkdir(exist_ok=True)
BASELINE = OUT / 'baseline'
BASELINE_COMMIT = 'ee3ddc9cbf206eec5d336ee8c083fa07e3193e1a'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cy(radius, y, length, x=0., z=0.):
    return cq.Solid.makeCylinder(radius, length, cq.Vector(x, y, z), cq.Vector(0, 1, 0))


def ring(od, bore, y, length, x=0., z=0.):
    return cy(od/2, y, length, x, z).cut(cy(bore/2, y-.01, length+.02, x, z))


def box(w, d, h, x, y, z):
    return cq.Workplane('XY').box(w, d, h).translate((x, y, z)).val()


def overlap(a, b):
    aa, bb = a.BoundingBox(), b.BoundingBox()
    if any(getattr(aa, k+'max') <= getattr(bb, k+'min')+1e-6 or
           getattr(bb, k+'max') <= getattr(aa, k+'min')+1e-6 for k in 'xyz'):
        return 0.
    return max(0., a.intersect(b).Volume())


def main():
    ppath = BASELINE/'parameters.json'
    p = json.loads(ppath.read_text())
    zc = p['head_center_height']
    params = {
        'tube_manufacturer': 'K&S Precision Metals', 'tube_sku': '8128',
        'tube_material': 'brass alloy260/272',
        'tube_od_mm': 3.96875, 'tube_id_mm': 3.2512,
        'tube_od_id_tolerance_mm': .0508,
        'tube_length_mm': 28.7, 'tube_length_tolerance_mm': .05,
        'tpu_pad_od_mm': 14., 'tpu_pad_bore_mm': 4.4,
        'tpu_pad_free_thickness_mm': 2., 'trial_compression_fraction': .15,
        'insert_od_reference_mm': 4.6, 'insert_length_mm': 5.7,
        'insert_pilot_mm': 4., 'insert_pilot_depth_mm': 6.8,
        'washer_od_mm': 7., 'washer_id_mm': 3.2, 'washer_thickness_mm': .5,
        'screw_length_mm': 35., 'screw_nominal_shank_mm': 3.,
        'screw_head_od_mm': 5.5, 'screw_head_height_mm': 3.,
        'bellplate_clearance_bore_mm': 7.6,
    }
    # Fan bay in current build_head removes the first .01 mm of the Y=29 boss.
    seat = 29.01
    fan_depth = 27.
    compressed = params['tpu_pad_free_thickness_mm']*(1-params['trial_compression_fraction'])
    rear = seat-params['tube_length_mm']
    assert abs((rear+fan_depth+compressed)-seat) < 1e-8
    centres = [(x, z+zc) for x in (-52.5, 52.5) for z in (-52.5, 52.5)]
    tube_od=params['tube_od_mm'];tube_id=params['tube_id_mm']

    paths = [ppath, BASELINE/'build_head.py', BASELINE/'check_assembly.py',
             ROOT/'vendor/NF-A12x25_G2_Public-CAD.stp',
             BASELINE/'head-left-integral-outlet.step',
             BASELINE/'head-right-integral-outlet.step',
             BASELINE/'bellmouth-rear-inlet.step',
             BASELINE/'tpu-fan-pad-m3.step']
    fan0 = cq.importers.importStep(str(paths[3])).val().rotate((0,0,0),(1,0,0),-90).translate((0,1,zc))
    fan = fan0.translate((0,rear,0))
    assert fan.isValid()
    assert abs(fan0.BoundingBox().ylen-fan_depth) < 1e-5

    measured = []
    for si, solid in enumerate(fan0.Solids()):
        for face in solid.Faces():
            if face.geomType() != 'CYLINDER':
                continue
            c = BRepAdaptor_Surface(face.wrapped).Cylinder()
            a, d = c.Axis().Location(), c.Axis().Direction()
            if abs(d.Y()) < .999 or not any(abs(a.X()-x)<.001 and abs(a.Z()-z)<.001 for x,z in centres):
                continue
            if abs(c.Radius()-2.15) > .001:
                continue
            b = face.BoundingBox()
            measured.append({'solid_index':si, 'diameter_mm':2*c.Radius(),
                             'axis_xz_mm':[a.X(),a.Z()], 'y_span_mm':[b.ymin,b.ymax]})
    assert len(measured)==8, 'Expected two Ø4.3 rigid mounting bores at each corner'
    print('MEASURED vendor rigid fan bores',flush=True)

    # Every corner fastener remains inside this prism. Trimming the detailed
    # supplier component once avoids repeating full impeller booleans for each
    # small tube pose. A subset proof below guards against an undersized prism.
    fan_regions={i:fan.intersect(box(16,70,16,x,0,z))
                 for i,(x,z) in enumerate(centres,1)}
    for i,s in fan_regions.items():
        assert s.isValid() and s.Volume()>0,('fan corner trim',i)
    print('TRIMMED four vendor fan corner regions',flush=True)

    head = {n:cq.importers.importStep(str(BASELINE/(n+'.step'))).val().translate((0,0,zc))
            for n in ('head-left-integral-outlet','head-right-integral-outlet')}
    bell0 = cq.importers.importStep(str(BASELINE/'bellmouth-rear-inlet.step')).val().translate((0,0,zc))
    bell = bell0
    for x,z in centres:
        bell = bell.cut(cy(params['bellplate_clearance_bore_mm']/2,-2.5,2.6,x,z))
    assert bell.isValid() and len(bell.Solids())==1

    artifacts = {}
    def save(name, shape, printable=False):
        assert shape.isValid(), name
        assert len(shape.Solids())==1, (name,len(shape.Solids()))
        assert shape.Volume()>0, name
        f = OUT/(name+'.step')
        cq.exporters.export(shape,str(f))
        artifacts[f.name] = digest(f)
        if printable:
            f = OUT/(name+'.stl')
            cq.exporters.export(shape,str(f),tolerance=.045,angularTolerance=.12)
            artifacts[f.name] = digest(f)
        return shape

    pad_free = save('tpu-fan-pad-sleeve-4p4-free',ring(14,4.4,0,2),True)
    for bore in (4.2,4.6):
        save('tpu-fan-pad-bore-coupon-'+str(bore).replace('.','p'),ring(14,bore,0,2),True)
    save('bellmouth-rear-inlet-mount-reliefs',bell.translate((0,0,-zc)),True)
    tube_ref = save('REF-KS8128-brass-tube-cut-28p7',ring(tube_od,tube_id,0,28.7))

    # Small print fixture exercises pilot installation, tube fit and stop stack.
    # The 27 mm surrogate is rigid and deliberately does not simulate silicone.
    boss_coupon = box(20,8,20,0,seat+4,0).cut(cy(2,seat-.1,6.9))
    save('fan-insert-boss-coupon',boss_coupon.translate((0,-seat,0)),True)
    surrogate = box(18,27,18,0,13.5,0).cut(cy(2.15,-.1,27.2))
    save('fan-corner-27mm-stack-coupon',surrogate,True)

    parts = {'Noctua-NF-A12x25-G2-vendor-shifted':fan,
             'bellmouth-rear-inlet-mount-reliefs':bell, **head}
    test_pairs = []
    expected_contacts = []
    old_pad = cq.importers.importStep(str(BASELINE/'tpu-fan-pad-m3.step')).val()
    old_clash = overlap(old_pad,tube_ref.translate((0,0,0)))
    assert old_clash > 1., 'Old pad/tube incompatibility must be detectable'
    failures = []
    for i,(x,z) in enumerate(centres,1):
        pad = ring(14,4.4,rear+27,compressed,x,z)
        tube = ring(tube_od,tube_id,rear,28.7,x,z)
        washer = ring(7,3.2,rear-.5,.5,x,z)
        screw_head = cy(2.75,rear-.5-3,3,x,z)
        # ISO4762 hex key socket, nominal 2.5 mm across flats, shallow reference.
        keyhole = cq.Workplane(cq.Plane(origin=(x,rear-.5-3-.01,z),xDir=(1,0,0),normal=(0,1,0))).polygon(6,2.5/math.cos(math.pi/6)).extrude(1.31).val()
        screw = cy(1.5,rear-.5,35,x,z).fuse(screw_head.cut(keyhole))
        insert = ring(4.6,3,seat,5.7,x,z)
        corner = {f'TPU-compressed-envelope-{i}':pad,f'REF-KS8128-brass-tube-{i}':tube,
                  f'REF-ISO7089-M3-washer-{i}':washer,f'REF-ISO4762-M3x35-{i}':screw,
                  f'REF-RX-M3x5p7-smooth-insert-{i}':insert}
        for name,shape in corner.items():
            save(name,shape)
        # Expanded heat-set cavity is only an assembled-state allowance. The
        # source head and printable boss retain their Ø4.0 mm insertion pilots.
        for hn,h in head.items():
            v=overlap(insert,h)
            if v>.00001:
                expected_contacts.append({'a':f'REF-RX-M3x5p7-smooth-insert-{i}',
                                          'b':hn,'raw_pilot_displacement_mm3':v,
                                          'reason':'heat-set insert intentionally displaces Ø4.0 pilot material'})
        parts.update(corner)

    # Physical insert installation makes an expanded cavity. Record that exact
    # adjustment rather than silently accepting arbitrary hardware intersections.
    assembled_head = dict(head)
    for hn,h in head.items():
        for x,z in centres:
            h=h.cut(cy(2.3,seat,5.7,x,z))
        assembled_head[hn]=h
    checked = {**parts,**assembled_head}
    items = list(checked.items())
    for i,(name,s) in enumerate(items):
        for other,t in items[i+1:]:
            # Manufacturer fan CAD includes intentional internal pad/rotor
            # contacts, all in the single supplied component, not pair bypasses.
            a,b=s,t
            if name=='Noctua-NF-A12x25-G2-vendor-shifted' and other.rsplit('-',1)[-1].isdigit():
                corner_id=int(other.rsplit('-',1)[-1])
                x,z=centres[corner_id-1]
                bb=t.BoundingBox()
                assert bb.xmin>=x-8-1e-5 and bb.xmax<=x+8+1e-5
                assert bb.zmin>=z-8-1e-5 and bb.zmax<=z+8+1e-5
                a=fan_regions[corner_id]
            v=overlap(a,b)
            test_pairs.append({'a':name,'b':other,'overlap_mm3':v})
            if v>.01:
                failures.append(test_pairs[-1])
        print('STATIC CHECKED '+name,flush=True)
    assert not failures, failures

    old_bell_clashes = []
    for n,s in parts.items():
        if 'washer' in n or 'M3x35' in n:
            v=overlap(s,bell0)
            if v>.01:old_bell_clashes.append({'hardware':n,'old_bellplate_overlap_mm3':v})
    assert len(old_bell_clashes)==8

    # Insert the tubes from the rear before washers/screws. End positions have
    # 4 mm nominal OD/4.3 mm frame bore clearance. No rotor or frame cuts used.
    insertion=[]
    sweeps=[]
    for i,(x,z) in enumerate(centres,1):
        # The union of the axially translated annular tube from -32 to0 mm
        # is exactly this longer annulus; this proves the entire continuous
        # insertion path, beyond the33 recorded pose samples. Initial tube tip
        # is at -2.99 mm, behind the bell plate's -2.4 mm rear face at this axis.
        sweep=ring(tube_od,tube_id,rear-32,28.7+32,x,z)
        obstacles={'fan_corner':fan_regions[i], 'repaired_bell':bell, **assembled_head}
        for n,o in obstacles.items():
            v=overlap(sweep,o)
            sweeps.append({'corner':i,'obstacle':n,'overlap_mm3':v})
            assert v<.01,sweeps[-1]
        for step in range(33):
            dy=-32+step
            # Same radii andaxis; interval containment is exact for this motion.
            assert rear+dy>=rear-32-1e-8 and rear+dy+28.7<=seat+1e-8
            insertion.append({'corner':i,'step':step,'translation_y_mm':dy,
                              'contained_in_checked_sweep':True})
        print('INSERTION SWEEP CHECKED corner '+str(i),flush=True)

    # Straight 2.5 mm hex driver clearance, before the rear guard is fitted.
    # Radius2 is a larger round shaft than the actual key's circumscribed radius.
    tools=[]
    for i,(x,z) in enumerate(centres,1):
        tool=cy(2,rear-.5-3-50,50,x,z)
        for n,o in {'repaired_bell':bell,'fan_corner':fan_regions[i],**assembled_head}.items():
            v=overlap(tool,o)
            tools.append({'corner':i,'obstacle':n,'overlap_mm3':v})
            assert v<.01,tools[-1]

    screw_tip=rear-.5+35
    report={
        'completed_utc':datetime.now(timezone.utc).isoformat(),
        'status':'independent mechanical repair study; not integrated or print qualified',
        'frozen_baseline_commit':BASELINE_COMMIT,
        'frozen_baseline_note':'Seven baseline files preserved byte-for-byte before mount repair adoption; vendor fan remains reproducibly downloaded',
        'script_sha256':digest(Path(__file__)),
        'input_sha256':{str(f.relative_to(ROOT.parent)):digest(f) for f in paths},
        'parameters':params,
        'manufacturer_cad_measurements':{
            'fan_with_pads_depth_mm':fan0.BoundingBox().ylen,
            'rigid_mounting_bores':measured,
            'nominal_mount_pitch_mm':105.,
            'tube_to_rigid_fan_bore_radial_clearance_mm':(4.3-tube_od)/2,
            'tube_to_tpu_pad_radial_clearance_mm':(4.4-tube_od)/2,
            'm3_shank_to_tube_radial_clearance_mm':(tube_id-3)/2,
            'worst_stock_od_to_nominal_fan_bore_radial_clearance_mm':(4.3-(tube_od+.0508))/2,
            'worst_stock_od_to_nominal_tpu_bore_radial_clearance_mm':(4.4-(tube_od+.0508))/2,
            'worst_stock_id_to_nominal_m3_shank_radial_clearance_mm':((tube_id-.0508)-3)/2,
        },
        'stack':{
            'head_insert_front_y_mm':seat, 'fan_rear_silicone_face_y_mm':rear,
            'fan_front_silicone_face_y_mm':rear+27,
            'tpu_compressed_thickness_mm':compressed,
            'tpu_nominal_compression_mm':2-compressed,
            'rear_washer_span_y_mm':[rear-.5,rear],
            'screw_tip_y_mm':screw_tip,
            'thread_engagement_length_mm':min(screw_tip-seat,5.7),
            'screw_extension_past_insert_mm':max(0,screw_tip-(seat+5.7)),
            'blind_pilot_end_y_mm':35.8,
            'screw_tip_to_blind_pilot_nominal_margin_mm':35.8-screw_tip,
            'head_rear_face_rigid_frame_gap_mm':rear+1,
            'fan_front_shift_from_current_assembly_mm':rear,
        },
        'checks':{
            'valid_printable_solids':6,
            'old_tpu_pad_tube_overlap_mm3':old_clash,
            'old_bellplate_hardware_clashes':old_bell_clashes,
            'static_pairs_checked':len(test_pairs),'unintended_intersections':failures,
            'tube_insertion_checks':len(insertion),'tube_insertion_unintended_intersections':0,
            'tube_continuous_sweep_boolean_checks':len(sweeps),
            'driver_checks':len(tools),'driver_unintended_intersections':0,
            'insert_installation_contacts':expected_contacts,
        },
        'limitations':[
            'TPU deformation is represented by an axial compressed envelope; stiffness and lateral bulge are unmeasured',
            'Vendor silicone pads are unchanged; their compression and tolerance require physical measurement',
            'K&S8128 stock has OD/ID tolerances, but fan bores, pad print tolerances and received stock remain unmeasured',
            'Brass tube ends bear on a flush insert face; a recessed insert changes the stack and must be measured',
            'Current printed head pilots are not re-cut; heat-setting is represented explicitly for assembly interference',
            'Nominal ISO screw, washer and smooth insert references omit threads, knurls and tolerance variation',
            'Current full76-instance assembly, its hashes and Onshape imports are unchanged',
            'No whole fan axial insertion or rear guard service path qualification; tube/driver paths are before the rear guard is fitted',
            'No evidence of isolation transmissibility, creep, rotor rubbing, tightening torque or acoustic improvement',
        ],
        'primary_references':[
            'https://www.noctua.at/en/products/nf-a12x25-g2-pwm/specifications',
            'https://cdn.noctua.at/media/a7b1158c/NF-A12x25_G2_Public-CAD.zip?download=true',
            'https://www.ruthex.de/products/ruthex-gewindeeinsatz-m3-100-stuck-rx-m3x5-7-messing-gewindebuchsen',
            'https://ksmetals.com/products/br014-5-32',
        ],
    }
    asm=cq.Assembly(name='Windflow fan mount repair - independent 15 percent preload study')
    for n,s in parts.items():
        col=cq.Color(.2,.2,.2) if 'TPU' in n else cq.Color(.66,.68,.70)
        if 'Noctua' in n:col=cq.Color(.53,.40,.30)
        if n.startswith('head') or 'bellmouth' in n:col=cq.Color(.3,.35,.4)
        asm.add(s,name=n,color=col)
    asm.save(str(OUT/'fan-mount-repaired-development.step'))
    artifacts['fan-mount-repaired-development.step']=digest(OUT/'fan-mount-repaired-development.step')
    report['artifact_sha256']=artifacts
    (OUT/'validation.json').write_text(json.dumps(report,indent=2))
    (OUT/'vendor-inspection.json').write_text(json.dumps(report['manufacturer_cad_measurements'],indent=2))
    (OUT/'parameters.json').write_text(json.dumps(params,indent=2))
    print(json.dumps({'status':'PASS','static_pairs':len(test_pairs),
                      'tube_insertion_checks':len(insertion),'driver_checks':len(tools),
                      'stack':report['stack'],'old_pad_tube_overlap_mm3':old_clash,
                      'old_bellplate_clashes':len(old_bell_clashes)},indent=2),flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.stdout.flush();sys.stderr.flush();os._exit(1)
    # This runtime's OCP interpreter teardown crashes independently of checks.
    # Exit explicitly only after every assertion, export and report succeeds.
    sys.stdout.flush();sys.stderr.flush();os._exit(0)
