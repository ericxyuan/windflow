"""Independent grille interlock design; does not edit main Rev B sources.

Airflow +Y. Exports use assembled coordinates, Z=head-local Z+head_center_height.
Omron case/holes/terminals follow the primary drawing. Lever shapes are declared
drawing envelopes, not manufacturer CAD or an elastic/snap-action simulation.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, math, os, sys, traceback
import cadquery as cq

ROOT = Path(__file__).resolve().parent
OUT = ROOT/'grille_interlock_study'
OUT.mkdir(exist_ok=True)
BASELINE = OUT/'baseline'
DATASHEET = ROOT.parent/'build/datasheets/grille-interlock/Omron-D2F-datasheet.pdf'
if not DATASHEET.exists():
    DATASHEET = ROOT.parent/'hardware/datasheets/D2F.pdf'


def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def box(w,d,h,x,y,z): return cq.Workplane('XY').box(w,d,h).translate((x,y,z)).val()
def cx(r,x,length,y,z): return cq.Solid.makeCylinder(r,length,cq.Vector(x,y,z),cq.Vector(1,0,0))
def cz(r,z,length,x,y): return cq.Solid.makeCylinder(r,length,cq.Vector(x,y,z),cq.Vector(0,0,1))
def nutx(x,length,y,z,af=4.2):
    return cq.Workplane(cq.Plane(origin=(x,y,z),xDir=(0,1,0),normal=(1,0,0))).polygon(6,af/math.cos(math.pi/6)).extrude(length).val()
def slotx(x,length,y,z,travel=2.,dia=2.4):
    return (cx(dia/2,x,length,y-travel,z).fuse(cx(dia/2,x,length,y+travel,z))
            .fuse(box(length,2*travel,dia,x+length/2,y,z)))
def overlap(a,b):
    aa,bb=a.BoundingBox(),b.BoundingBox()
    if any(getattr(aa,k+'max')<=getattr(bb,k+'min')+1e-6 or getattr(bb,k+'max')<=getattr(aa,k+'min')+1e-6 for k in 'xyz'): return 0.
    return max(0.,a.intersect(b).Volume())


def wire_liner(zc=0., hole_diameter=1.1, installed=False):
    """Small TPU liner; free OD has a trial 0.15 mm diametral interference."""
    height=6. if installed else 6.2
    start=-10. if installed else -10.1
    shape=cz(2. if installed else 2.075,start+zc,height,-60.2,125.5)
    for x in (-60.85,-59.55):
        shape=shape.cut(cz(hole_diameter/2,start-.1+zc,height+.2,x,125.5))
    assert shape.isValid() and len(shape.Solids())==1
    return shape


def build_geometry(left0, grille0, keeper0, zc=0.):
    """Build isolated switch geometry in the supplied head coordinate system."""
    # Four outboard attachment bosses. Nut loading channels open toward +Y;
    # switch bracket/raceway remain removable without opening the head seam.
    left=left0
    head_mounts=[(136.7,8.+zc),(136.7,29.+zc),(133.,-14.+zc),(133.,-52.+zc)]
    for i,(y,z) in enumerate(head_mounts):
        left=left.fuse(box(9.0 if i<2 else 3.1,7.,6.,-58.6 if i<2 else -55.65,y,z))
        left=left.cut(cx(1.2,-65,14,y,z)).cut(nutx(-56.1,1.8,y,z))
        left=left.cut(box(1.8,8.,4.2,-55.2,y+4.,z))
    assert left.isValid() and len(left.Solids())==1

    b=136.7; zlo=12.+zc
    bracket=box(2.4,25.,33.,-64.3,135.,16.5+zc)
    for y,z in head_mounts[:2]: bracket=bracket.cut(slotx(-65.6,2.6,y,z))
    switch_holes=[(b,zlo+3.15),(b,zlo+9.65)]
    for y,z in switch_holes:
        bracket=bracket.cut(cx(1.2,-65.6,2.6,y,z)).cut(nutx(-65.6,2.1,y,z))
    # The fixed raceway carries the wire strain clamp. Keeping it below the
    # sliding switch module prevents calibration from pinching a fixed harness.
    # A replaceable TPU liner supplies trial grip, while rigid faces limit
    # screw travel. It avoids relying on a loose rigid bore for strain relief.
    clamp_base=box(5.3,13.,6.,-62.85,125.5,-7.+zc).cut(cz(2.,-10.1+zc,6.2,-60.2,125.5))
    clamp_base=clamp_base.fuse(box(2.4,13.,10.,-64.3,125.5,-5.+zc))
    clamp=box(2.9,13.,6.,-58.75,125.5,-7.+zc).cut(cz(2.,-10.1+zc,6.2,-60.2,125.5))
    clamp_axes=[(121.5,-7.+zc),(129.5,-7.+zc)]
    for y,z in clamp_axes:
        clamp_base=clamp_base.cut(cx(1.2,-65.6,5.5,y,z)).cut(nutx(-65.6,2.1,y,z))
        clamp=clamp.cut(cx(1.2,-60.3,3.1,y,z))

    # Cover + crush posts share the two slotted mount screws. Open inboard
    # face prevents the occupied duct side from trapping the cover.
    cover=box(15.3,30.3,35.,-62.05,135.65,17.5+zc)
    cover=cover.cut(box(11.3,26.3,31.,-62.05,135.65,17.5+zc))
    cover=cover.cut(box(2.2,33.,38.,-55.3,135.65,17.5+zc))
    # Relief for the keeper/grille rim is a bounded local corner recess.
    cover=cover.cut(box(9.8,8.,36.,-57.1,149.8,16.5+zc))
    cover=cover.cut(box(9.,14.,20.,-57.8,147.,35.+zc))
    exit_slot=cz(1.5,-.2+zc,3.,-60.2,123.5).fuse(cz(1.5,-.2+zc,3.,-60.2,127.5)).fuse(box(3.,4.,3.,-60.2,125.5,1.3+zc))
    cover=cover.cut(exit_slot)
    for y,z in head_mounts[:2]:
        cover=cover.fuse(box(2.2,8.,4.8,-66.6,y,z))
        cover=cover.cut(slotx(-69.9,15.8,y,z))
    cover=cover.cut(box(2.4,25.4,33.4,-64.3,135.,16.5+zc))
    cover=cover.cut(clamp.fuse(clamp_base))
    cover=cover.cut(box(3.,14.,2.4,-59.2,125.5,1.+zc))
    cover=cover.cut(box(3.8,14.,6.,-56.8,125.5,3.+zc))

    # Integrated grille tongue keeps cleaning free of a loose detachable tab.
    # Rounded nose contacts only the lever extension outside the case end.
    nose=box(3.,8.1,3.6,-60.2,147.3,26.4+zc)
    nose=cq.Workplane(obj=nose).edges('|X').fillet(.3).val()
    # Actuation face is datum Y=143.25; no nozzle/grille opening is obstructed.
    nose=nose.cut(box(4.,20.,5.,-60.2,133.25,26.4+zc))
    grille=grille0.fuse(nose)
    keeper_window=box(3.8,2.,4.4,-60.2,150.6,26.4+zc)
    keeper=keeper0.cut(keeper_window)
    assert grille.isValid() and len(grille.Solids())==1
    assert keeper.isValid() and len(keeper.Solids())==1

    # A U raceway with a separate outboard lid accepts wires before connectors
    # are attached. Mount ears and screw axes sit beside, not through, the wire.
    raceway=box(5.8,5.8,65.,-60.1,125.5,-32.5+zc)
    raceway=raceway.cut(box(5.0,3.4,65.2,-60.9,125.5,-32.5+zc))
    raceway=raceway.fuse(clamp_base)
    # The removable clamp substitutes for this short inboard wall section.
    # Its edges have 0.1 mm nominal assembly clearance, tuned with the coupon.
    raceway=raceway.cut(box(3.2,13.2,6.2,-58.6,125.5,-7.+zc))
    raceway=raceway.cut(cz(2.,-10.1+zc,6.2,-60.2,125.5))
    for y,z in clamp_axes:
        raceway=raceway.cut(cx(1.2,-65.6,8.6,y,z))
    # The clamp's fixed backplate closes the top 10 mm of the channel. The
    # separate lid ends 0.1 mm below it and remains one removable solid.
    race_lid=box(1.2,5.8,54.9,-63.6,125.5,-37.55+zc)
    for y,z in head_mounts[2:]:
        raceway=raceway.fuse(box(5.8,9.1,6.,-60.1,130.95,z))
        race_lid=race_lid.fuse(box(1.2,9.1,6.,-63.6,130.95,z))
        raceway=raceway.cut(cx(1.2,-64.3,7.2,y,z))
        race_lid=race_lid.cut(cx(1.2,-64.3,1.4,y,z))

    # Reference purchased component: verified rectangular case and mounting
    # bores. Mold recesses, button and terminal contours are omitted.
    case=box(5.8,6.5,12.8,-60.2,b+1.75,18.4+zc)
    for y,z in switch_holes: case=case.cut(cx(1.,-63.2,6.,y,z))
    terminals=[]
    for index,z in enumerate((zlo+1.32,zlo+6.4,zlo+11.48)):
        terminals.append(box(.4,3.5,.9,-60.2,b-3.25,z))
    def lever(mount_y,contact_y):
        plane=cq.Plane(origin=(-61.7,0,0),xDir=(0,1,0),normal=(1,0,0))
        return (cq.Workplane(plane).polyline([(mount_y+5.5,13.2+zc),
             (contact_y,25.4+zc),(contact_y-.3,25.4+zc),
             (mount_y+5.2,13.2+zc)]).close().extrude(3.).val())
    lever_closed=lever(b,143.25); lever_free=lever(b,b+10.)

    return {'left':left, 'grille':grille, 'keeper':keeper, 'bracket':bracket, 'cover':cover,
      'clamp':clamp, 'raceway':raceway, 'race_lid':race_lid, 'case':case, 'terminals':terminals,
      'lever_closed':lever_closed, 'lever_free':lever_free, 'nose':nose,
      'head_mounts':head_mounts, 'switch_holes':switch_holes, 'clamp_axes':clamp_axes,
      'mount_y':b, 'case_end_z':zlo, 'lever':lever}


def integrate_head_parts(left, grille, keeper, head_z=0.):
    """Apply interlock features to caller-supplied head/grille/rim B-reps.

    Inputs and outputs use the caller's same Z datum. No export or import occurs.
    Only the left head, removable cosmetic grille and head magnet rim change.
    Call before build_head.save for these parts, or translate head-local parts
    to assembled coordinates and pass head_z=head_center_height.
    """
    g=build_geometry(left,grille,keeper,head_z)
    return {
      'head-left-integral-outlet':g['left'],
      'magnetic-front-grille':g['grille'],
      'head-magnet-retaining-rim':g['keeper'],
      'interlock-sliding-bracket':g['bracket'],
      'interlock-protective-cover':g['cover'],
      'interlock-wire-clamp':g['clamp'],
      'interlock-wire-raceway':g['raceway'],
      'interlock-raceway-lid':g['race_lid'],
      'interlock-tpu-wire-liner-free':wire_liner(head_z),
    }


def installed_reference_parts(head_z=0.):
    """Load only qualified-study installed references into a caller's Z datum.

    Run this study first. The report records each STEP hash; a stale or modified
    file is refused. Prints are generated by integrate_head_parts. Lever and
    switch-case STEP files are drawing envelopes, not manufacturer CAD.
    """
    report=json.loads((OUT/'validation.json').read_text())
    assert report['checks']['unintended_intersections']==[]
    offset=head_z-report['head_center_height_mm']
    parts={}
    for name,hash_value in report['artifact_sha256'].items():
        if not (name.startswith('REF-') and name.endswith('.step')):continue
        if 'free-lever' in name:continue
        path=OUT/name
        assert digest(path)==hash_value,('Modified study reference',name)
        parts[name[:-5]]=cq.importers.importStep(str(path)).val().translate((0,0,offset))
    return parts


def main():
    params_path=BASELINE/'parameters.json'
    p=json.loads(params_path.read_text())
    zc=p['head_center_height']
    par={
      'units':'mm','coordinate_system':'assembled: airflow +Y; head-local Z +10 mm',
      'switch_model':'Omron D2F-01L, straight PCB terminals, gold-alloy low-level contact',
      'case_mm':[5.8,6.5,12.8], 'case_axes':'X thickness, Y height, Z length',
      'case_x_span':[-63.1,-57.3], 'case_z_span_local':[12.,24.8],
      'mount_hole_diameter_nominal':2.0,'mount_pitch':6.5,'first_hole_from_case_end':3.15,
      'case_bottom_from_mount_datum':-1.5,'case_top_from_mount_datum':5.0,
      'switch_mount_y_nominal':136.7,'switch_bracket_adjustment_y':2.,
      'switch_operating_position_from_hole_datum_nominal':6.8,
      'switch_operating_position_tolerance':1.5,'free_position_maximum':10.,
      'guaranteed_overtravel_minimum':.55,'movement_differential_maximum':.5,
      'target_post_trip_travel':.25,'grille_stop_additional_travel':.20,
      'actuator_face_y':143.25,'actuator_contact_x':-60.2,
      'lever_contact_z_local_inferred':25.4,
      'bracket_plate_x_span':[-65.5,-63.1],
      'bracket_head_screw_axis_y':136.7,'bracket_head_screw_z_local':[8.,29.],
      'bracket_screws':'2 x ISO 4762 M2x16 with ISO 7089 M2 washers, DIN 934 M2 nuts',
      'switch_screws':'2 x ISO 4762 M2x10 with ISO 7089 M2 washers, DIN 934 M2 nuts',
      'strain_clamp_screws':'2 x ISO 4762 M2x10 with ISO 7089 M2 washers, DIN 934 M2 nuts',
      'raceway_screws':'2 x ISO 4762 M2x10 with ISO 7089 M2 washers, DIN 934 M2 nuts',
      'nut_pocket_across_flats':4.2,'nut_reference_across_flats':4.,'nut_reference_thickness':1.6,
      'clearance_screw_bores':2.4,'slide_slot_length':6.4,
      'wire_bundle_maximum_envelope_diameter':2.6,
      'wire_od_trial_mm':1.2,'liner_free_od_mm':4.15,'liner_installed_od_mm':4.,
      'liner_wire_hole_trial_mm':1.1,'liner_free_height_mm':6.2,'liner_installed_height_mm':6.,
      'wire_raceway_center_local':[-60.2,125.5],
      'wire_raceway_z_local_span':[-65.,0.],
      'wire_raceway_inside_y_width':3.4,
      'fixed_strain_clamp_z_local_span':[-10.,-4.],
      'fixed_clamp_backplate_z_local_span':[-10.,0.],
      'raceway_lid_z_local_span':[-65.,-10.1],
      'cover_z_local_span':[0.,35.],
      'stop_land_xz_local':[-56.5,26.8],
      'stop_land_head_face_y':150.8,'grille_rear_face_y':151.,
      'electrical':'COM to GND; NO to J12 raw guard; R5 3.9k to 5V and 5V-tolerant 3V3 buffer to GP15; NC insulated and unused',
      'terminal_mapping':'From the case end at local Z=12: COM Z=13.32, NO Z=18.4, NC Z=23.48',
      'switch_mount_torque_Nm':[.08,.10],
    }
    source_paths=[params_path,BASELINE/'build_head.py',BASELINE/'check_assembly.py',
      BASELINE/'build_prototypes.py', BASELINE/'prototypes/validation.json',
      BASELINE/'rev_b/head-left-integral-outlet.step',BASELINE/'rev_b/head-right-integral-outlet.step',
      BASELINE/'rev_b/magnetic-front-grille.step',BASELINE/'rev_b/head-magnet-retaining-rim.step',
      BASELINE/'rev_b/grille-magnet-retaining-rim.step',BASELINE/'rev_b/fixed-inner-finger-guard.step',
      BASELINE/'prototypes/installed-upper_panel-open.step',BASELINE/'prototypes/installed-lower_panel-open.step',
      BASELINE/'provenance.json']
    before={str(f.relative_to(ROOT)):digest(f) for f in source_paths}
    load=lambda n:cq.importers.importStep(str(BASELINE/'rev_b'/(n+'.step'))).val().translate((0,0,zc))
    left0=load('head-left-integral-outlet'); right=load('head-right-integral-outlet')
    grille0=load('magnetic-front-grille'); keeper0=load('head-magnet-retaining-rim')
    front_keeper=load('grille-magnet-retaining-rim'); guard=load('fixed-inner-finger-guard')

    geometry=build_geometry(left0,grille0,keeper0,zc)
    left,grille,keeper=(geometry[n] for n in ('left','grille','keeper'))
    bracket,cover,clamp,raceway,race_lid=(geometry[n] for n in ('bracket','cover','clamp','raceway','race_lid'))
    case,terminals,lever_closed,lever_free,nose=(geometry[n] for n in ('case','terminals','lever_closed','lever_free','nose'))
    head_mounts,switch_holes,clamp_axes=(geometry[n] for n in ('head_mounts','switch_holes','clamp_axes'))
    b,zlo,lever=(geometry[n] for n in ('mount_y','case_end_z','lever'))

    artifacts={}; printable=[]; parts={}
    def save(name,s,print_it=False):
        if len(s.Solids())!=1:
            print(json.dumps({'name':name,'solid_diagnostics':[{'volume':a.Volume(),'bbox':[a.BoundingBox().xmin,a.BoundingBox().xmax,a.BoundingBox().ymin,a.BoundingBox().ymax,a.BoundingBox().zmin,a.BoundingBox().zmax]} for a in s.Solids()]},indent=2),flush=True)
        assert s.isValid() and len(s.Solids())==1 and s.Volume()>0,(name,len(s.Solids()))
        f=OUT/(name+'.step'); cq.exporters.export(s,str(f)); artifacts[f.name]=digest(f)
        if print_it:
            f=OUT/(name+'.stl'); cq.exporters.export(s,str(f),tolerance=.045,angularTolerance=.12)
            artifacts[f.name]=digest(f); printable.append(name)
        return s
    for n,s in [('head-left-interlock-bosses',left),('grille-with-integral-switch-tongue',grille),
      ('head-magnet-rim-interlock-relief',keeper),('interlock-sliding-bracket',bracket),
      ('interlock-protective-cover',cover),('interlock-wire-clamp',clamp),
      ('interlock-wire-raceway',raceway),('interlock-raceway-lid',race_lid)]:
        parts[n]=save(n,s,True)
    parts.update({'head-right-unchanged':right,'grille-front-keeper-unchanged':front_keeper,
                  'fixed-inner-guard-unchanged':guard,
                  'REF-D2F-01L-drawing-case':save('REF-D2F-01L-drawing-case',case),
                  'REF-D2F-01L-installed-lever-envelope':save('REF-D2F-01L-installed-lever-envelope',lever_closed)})
    for i,s in enumerate(terminals): parts[f'REF-switch-terminal-{i+1}']=save(f'REF-switch-terminal-{i+1}',s)
    save('REF-D2F-01L-free-lever-envelope',lever_free)

    # ISO hardware is a smooth nominal envelope, with no thread/lead-in model.
    fixed_hardware=[]; switch_hardware=[]; clamp_hardware=[]; race_hardware=[]
    def fastener(prefix,under,length,y,z,direction=1,nut_at=None):
        shaft=cx(1.,under if direction>0 else under-length,length,y,z)
        head=cx(1.9,under-2 if direction>0 else under,2.,y,z)
        screw=shaft.fuse(head)
        washer=cx(2.5,under if direction>0 else under-.3,.3,y,z).cut(cx(1.1,under-.4,.8,y,z))
        nut=nutx(nut_at,1.6,y,z,4.).cut(cx(1.,nut_at-.1,1.8,y,z))
        names=[]
        for suff,s in [('screw',screw),('washer',washer),('nut',nut)]:
            n=f'REF-{prefix}-{suff}'; parts[n]=save(n,s); names.append(n)
        return names
    for i,(y,z) in enumerate(head_mounts[:2],1): fixed_hardware+=fastener(f'bracket-M2x16-{i}',-70.,16.,y,z,1,-56.1)
    for i,(y,z) in enumerate(switch_holes,1): switch_hardware+=fastener(f'switch-M2x10-{i}',-57.,10.,y,z,-1,-65.1)
    for i,(y,z) in enumerate(clamp_axes,1): clamp_hardware+=fastener(f'clamp-M2x10-{i}',-57.,10.,y,z,-1,-65.1)
    for i,(y,z) in enumerate(head_mounts[2:],1): race_hardware+=fastener(f'raceway-M2x10-{i}',-64.5,10.,y,z,1,-56.1)

    # Two Ø1.2 wire envelopes, separated in the raceway. Solder tails are
    # dimensioned corridors, not proof of strain or bend-radius qualification.
    wire_parts={}
    for label,x,z in [('COM',-60.85,zlo+1.32),('NO',-59.55,zlo+6.4)]:
        # Tangent R4 centerline bends within the terminal cavity, followed by
        # the protected straight-down raceway. Wire OD is a 1.2 mm trial value.
        bend_r=4.
        tail=cq.Solid.makeCylinder(.6,b-3.4-(125.5+bend_r),cq.Vector(x,125.5+bend_r,z),cq.Vector(0,1,0))
        down=cz(.6,-65.+zc,z-bend_r-(-65.+zc),x,125.5)
        arc=cq.Wire.assembleEdges([cq.Edge.makeThreePointArc(cq.Vector(x,125.5+bend_r,z),
          cq.Vector(x,125.5+bend_r-bend_r/math.sqrt(2),z-bend_r+bend_r/math.sqrt(2)),
          cq.Vector(x,125.5,z-bend_r))])
        elbow=cq.Workplane(cq.Plane(origin=(x,125.5+bend_r,z),xDir=(1,0,0),normal=(0,1,0))).circle(.6).sweep(cq.Workplane(obj=arc)).val()
        wire_parts['REF-'+label+'-tail']=tail
        wire_parts['REF-'+label+'-down']=down
        wire_parts['REF-'+label+'-R4-elbow']=elbow
    for n,s in wire_parts.items(): parts[n]=save(n,s)
    parts['REF-TPU-wire-liner-installed']=save('REF-TPU-wire-liner-installed',wire_liner(zc,installed=True))
    for hole in (1.,1.1,1.2):
        save('interlock-tpu-wire-liner-hole-'+str(hole).replace('.','p'),wire_liner(zc,hole),True)
    save('interlock-tpu-wire-liner-free',wire_liner(zc),True)

    # Small test pieces: actual corner section and three actuator depths. This
    # is a fixture; it never makes the product nozzle a removable part.
    corner_region=box(22.,37.,32.,-59.5,139.,21.+zc)
    corner_fixed=left.intersect(corner_region)
    save('interlock-head-corner-coupon',corner_fixed,True)
    for delta in (-.15,0.,.15):
        fixture=grille.intersect(box(15.,25.,22.,-58.5,152.,25.+zc))
        # Rebuild the tongue depth while preserving the original seating datum.
        if delta:
            fixture=fixture.cut(box(4.,10.,5.,-60.2,144.,26.4+zc))
            tip=nose.translate((0,delta,0))
            fixture=fixture.fuse(tip)
        save('grille-tongue-coupon-'+str(delta).replace('-','minus').replace('.','p'),fixture,True)
    save('wire-clamp-coupon',raceway.intersect(box(10.,14.,8.,-62.2,125.5,-7.+zc)),True)

    failures=[]; comparisons=[]; expected=[]
    def test(tag,n,s,o,t,allow=False):
        v=overlap(s,t); comparisons.append({'check':tag,'a':n,'b':o,'overlap_mm3':round(v,6)})
        if v>.01:
            item={'check':tag,'a':n,'b':o,'overlap_mm3':round(v,6)}
            (expected if allow else failures).append(item)
    # Fastener threading, nut installation material displacement and the switch
    # lever/case/contact relations have specific exclusions; no generic clash
    # blanket is applied to printed parts or the air path.
    printed_names=list(parts)[:8]
    structure={n:parts[n] for n in printed_names+['head-right-unchanged','grille-front-keeper-unchanged','fixed-inner-guard-unchanged']}
    for i,(n,s) in enumerate(structure.items()):
        for o,t in list(structure.items())[i+1:]: test('installed printed pair',n,s,o,t)
    switch_solids={n:s for n,s in parts.items() if 'D2F' in n or 'switch-terminal' in n}
    for n,s in switch_solids.items():
        for o,t in structure.items():
            test('installed switch',n,s,o,t,allow=('lever' in n and 'tongue' in o))
    for n,s in parts.items():
        if n.startswith('REF-') and any(k in n for k in ('M2x','COM-','NO-')):
            for o,t in structure.items(): test('hardware/harness',n,s,o,t)
    for n,s in wire_parts.items():
        for o,t in switch_solids.items():
            solder_pair=('COM-tail' in n and o=='REF-switch-terminal-1') or ('NO-tail' in n and o=='REF-switch-terminal-2')
            test('harness to switch',n,s,o,t,allow=solder_pair)
    references={n:s for n,s in parts.items() if n.startswith('REF-')}
    for i,(n,s) in enumerate(references.items()):
        for o,t in list(references.items())[i+1:]:
            solder_pair=('COM-tail' in n and o=='REF-switch-terminal-1') or ('NO-tail' in n and o=='REF-switch-terminal-2') or ('COM-tail' in o and n=='REF-switch-terminal-1') or ('NO-tail' in o and n=='REF-switch-terminal-2')
            liner_pair=('TPU-wire-liner' in n and (o.endswith('COM-down') or o.endswith('NO-down'))) or ('TPU-wire-liner' in o and (n.endswith('COM-down') or n.endswith('NO-down')))
            test('installed reference pair',n,s,o,t,allow=solder_pair or liner_pair)

    # Slot-end calibration poses represent OP=5.3/6.8/8.3 after actual meter
    # setup: mount datum = actuator face +target post-trip travel - actual OP.
    adjustable=['interlock-sliding-bracket','interlock-protective-cover']+switch_hardware
    calibration=[]
    for op in (5.3,6.8,8.3):
        shift=143.25+.25-op-b
        assert abs(shift)<=2.
        calibrated={n:parts[n].translate((0,shift,0)) for n in adjustable}
        calibrated.update({n:s.translate((0,shift,0)) for n,s in switch_solids.items() if 'lever' not in n})
        calibrated['REF-calibrated-lever']=lever(b+shift,143.25)
        for n,s in calibrated.items():
            for o,t in structure.items():
                if o in adjustable: continue
                test('calibration OP '+str(op),n,s,o,t,allow=('lever' in n and 'tongue' in o))
        # Nominal fixed mounting shafts clear both slot ends. Threads into the
        # nut/shaft hole are represented only as appropriate coaxial contacts.
        for n in fixed_hardware:
            for o,t in calibrated.items(): test('slot shaft calibration',n,parts[n],o,t)
        # The lower raceway and elbows remain fixed. Only the straight solder
        # tails change length with bracket adjustment, preserving tangent R4.
        varied_wires=dict(wire_parts)
        for label,x,z in [('COM',-60.85,zlo+1.32),('NO',-59.55,zlo+6.4)]:
            length=b+shift-3.4-(125.5+4.)
            assert length>0.
            varied_wires['REF-'+label+'-tail']=cq.Solid.makeCylinder(.6,length,cq.Vector(x,129.5,z),cq.Vector(0,1,0))
        for n,s in varied_wires.items():
            for o,t in calibrated.items():
                solder_pair=('COM-tail' in n and o=='REF-switch-terminal-1') or ('NO-tail' in n and o=='REF-switch-terminal-2')
                test('calibration harness OP '+str(op),n,s,o,t,allow=solder_pair)
            for o,t in structure.items():
                if o in adjustable:continue
                test('calibration fixed harness OP '+str(op),n,s,o,t)
        calibration.append({'actual_OP_mm':op,'bracket_translation_y_mm':shift,
          'commanded_post_trip_travel_mm':.25,'maximum_at_stop_mm':.45,
          'guaranteed_OT_margin_mm':.10,'straight_solder_tail_mm':length})

    # Both panels move only within X=±51.65; every interlock part stays left of
    # that air-path prism. Evaluate the actual B-reps at 61 boost angles too.
    kin=json.loads((BASELINE/'prototypes/validation.json').read_text())['kinematics']
    panel_checks=0
    interlock={n:s for n,s in parts.items() if n not in ('head-left-interlock-bosses','head-right-unchanged',
        'grille-with-integral-switch-tongue','head-magnet-rim-interlock-relief','grille-front-keeper-unchanged','fixed-inner-guard-unchanged')}
    panel_open={sign:cq.importers.importStep(str(BASELINE/'prototypes'/('installed-'+label+'_panel-open.step'))).val()
                for sign,label in [(1,'upper'),(-1,'lower')]}
    for state in kin:
        angle=state['panel_angle_deg']
        for sign,s in panel_open.items():
            pose=s.rotate((0,0,sign*p['outlet_height']/2),(1,0,sign*p['outlet_height']/2),-sign*angle).translate((0,90,zc))
            for n,t in interlock.items(): test('panel sweep '+str(round(angle,4)),n,t,'panel '+str(sign),pose); panel_checks+=1
    parts['REF-upper-panel-maximum-boost']=panel_open[1].rotate((0,0,p['outlet_height']/2),(1,0,p['outlet_height']/2),-kin[-1]['panel_angle_deg']).translate((0,90,zc))
    parts['REF-lower-panel-maximum-boost']=panel_open[-1].rotate((0,0,-p['outlet_height']/2),(1,0,-p['outlet_height']/2),kin[-1]['panel_angle_deg']).translate((0,90,zc))

    # The entire tongue/grille withdraws forward; only intended switch contact
    # is exempted. No keeper, bracket, screw or cover may obstruct removal.
    removal=[]
    moving_grille={'grille-with-integral-switch-tongue':grille,'grille-front-keeper-unchanged':front_keeper}
    fixed_for_removal={n:s for n,s in parts.items() if n not in moving_grille and n not in ('REF-D2F-01L-installed-lever-envelope',)}
    for dy in [i*.5 for i in range(61)]:
        for n,s in moving_grille.items():
            for o,t in fixed_for_removal.items(): test('grille forward '+str(dy),n,s.translate((0,dy,0)),o,t)
        contact_y=min(143.25+dy,b+10.)
        active=lever(b,contact_y)
        test('moving lever', 'lever',active,'grille',grille.translate((0,dy,0)),allow=True)
        removal.append({'forward_mm':dy,'nominal_contact_closed':dy<.25,
          'worst_MD_release_guaranteed_above_mm':.75})

    # Switch mounting screws are serviced with the module on the bench. Head
    # mount/raceway drivers have a clear straight approach from the outboard side.
    driver_checks=[]
    for name,under,y,z in [(f'bracket{i}',-70.,y,z) for i,(y,z) in enumerate(head_mounts[:2])]+[(f'raceway{i}',-64.5,y,z) for i,(y,z) in enumerate(head_mounts[2:])]:
        driver=cx(1.5,under-32.,31.8,y,z)
        for o,t in structure.items(): test('outboard driver '+name,name,driver,o,t)
        driver_checks.append({'fastener':name,'axis_yz_mm':[y,z],'tool_radius_mm':1.5,'approach_length_mm':32.})
    # Raceway lid removal after screws are taken out; wiring stays in the U.
    for dx in range(0,21):
        lidpose=race_lid.translate((-dx,0,0))
        for o,t in structure.items():
            if o=='interlock-raceway-lid':continue
            test('raceway lid removal '+str(dx),'raceway lid',lidpose,o,t)
    # Bracket/switch/cover module insertion before wires are connected and head
    # screws installed. Their bosses remain distinct; head nuts remain fixed.
    # Service order requires the removable grille to be taken off first. The
    # spring lever is then free, not falsely held in its depressed pose.
    module_names=adjustable+list(switch_solids)
    module_fixed={'head':left,'keeper':keeper,'raceway':raceway,'raceway lid':race_lid,'clamp':clamp}
    for dx in range(0,31):
        for n in module_names:
            for o,t in module_fixed.items():
                shape=lever_free if 'lever' in n else parts[n]
                test('module outward '+str(dx),n,shape.translate((-dx,0,0)),o,t)
    # The strain clamp is serviced on the bench: an inboard tool would cross
    # the integral nozzle wall. Unplug J12 and free the base continuation first,
    # remove grille and the four outboard retaining screws, then lift the whole
    # wired switch/raceway unit sideways. This preserves the soldered harness.
    unit_names=[n for n in parts if n in adjustable or n in switch_solids or
      n in clamp_hardware or n in wire_parts or n in ('interlock-wire-clamp','interlock-wire-raceway','interlock-raceway-lid','REF-TPU-wire-liner-installed')]
    unit_fixed={n:parts[n] for n in ('head-left-interlock-bosses','head-right-unchanged',
      'head-magnet-rim-interlock-relief','fixed-inner-guard-unchanged')}
    for dx in range(0,31):
        for n in unit_names:
            shape=lever_free if 'lever' in n else parts[n]
            for o,t in unit_fixed.items():test('wired unit outward '+str(dx),n,shape.translate((-dx,0,0)),o,t)
    bench_parts={n:parts[n] for n in unit_names}
    bench_drivers=[]
    for group,head_face,axes in [('switch',-55.,switch_holes),('clamp',-55.,clamp_axes)]:
        for i,(y,z) in enumerate(axes,1):
            driver=cx(1.5,head_face+.2,31.8,y,z)
            for o,t in bench_parts.items():test('bench driver '+group+str(i),'driver',driver,o,t)
            bench_drivers.append({'fastener':group+str(i),'axis_yz_mm':[y,z],
              'tool_radius_mm':1.5,'approach_length_mm':32.,'service_location':'removed wired unit on bench'})

    # Mechanical seating stop lands lie close to the actuator and retain the
    # established grille/rear-keeper faces. Actual flex is qualified physically.
    stop=box(1.4,.02,2.,-56.5,150.79,26.8+zc)
    assert overlap(stop,keeper)>.02,'Keeper stop land was removed'
    seated_grille=grille.translate((0,-.2,0))
    assert overlap(stop,seated_grille)<1e-5,'Stop faces should touch, not penetrate'
    contact_after_stop=.25+.2
    assert contact_after_stop<.55
    lever_contact_distance=lever_closed.distance(nose)
    assert lever_contact_distance<1e-5,('actuator does not touch lever',lever_contact_distance)
    # Continuous +X boundary proof independent of the angular sampling.
    xmax=max(s.BoundingBox().xmax for s in interlock.values())
    assert xmax<-52.,('interlock intrudes air passage',xmax)
    (OUT/'check-diagnostics.json').write_text(json.dumps({'failures':failures,'expected':expected,'comparisons':comparisons},indent=2))
    assert not failures, json.dumps(failures[:15],indent=2)

    assembly=cq.Assembly(name='Windflow grille interlock - isolated drawing-envelope development study')
    for n,s in parts.items():
        color=cq.Color(.26,.34,.40)
        if 'grille' in n:color=cq.Color(.04,.62,.64)
        elif 'D2F' in n or 'terminal' in n:color=cq.Color(.18,.18,.18)
        elif 'REF-' in n:color=cq.Color(.72,.68,.45)
        assembly.add(s,name=n,color=color)
    f=OUT/'mounted-grille-interlock-development.step'; assembly.save(str(f)); artifacts[f.name]=digest(f)
    assert before=={str(f.relative_to(ROOT)):digest(f) for f in source_paths},'Baseline inputs changed during study'
    report={'status':'PASS independent nominal design study; not adopted or physically qualified',
      'completed_utc':datetime.now(timezone.utc).isoformat(),'script_sha256':digest(Path(__file__)),
      'head_center_height_mm':zc,
      'source_sha256':before,'parameters':par,'printable_parts':printable,
      'checks':{'solid_pair_checks':len(comparisons),'unintended_intersections':failures,
        'expected_contact_intersections':expected,
        'boost_panel_samples':len(kin),'boost_panel_pair_checks':panel_checks,
        'grille_forward_removal_samples':len(removal),'module_outward_samples':31,
        'raceway_lid_outward_samples':21,'driver_checks':driver_checks,
        'wired_unit_outward_samples':31,'bench_driver_checks':bench_drivers,
        'continuous_air_path_left_boundary_xmax_mm':xmax,
        'air_path_x_minimum_mm':-52.,'calibration_operating_extremes':calibration,
        'stop_land_present':True,'nominal_grille_stop_travel_mm':.2,
        'post_trip_travel_at_stop_mm':contact_after_stop,'guaranteed_overtravel_margin_mm':.10,
        'actuator_to_installed_lever_distance_mm':lever_contact_distance},
      'removal_contact_assumptions':removal,
      'limitations':[
        'Case/holes/terminal dimensions are drawing-based; manufacturer CAD route needs member login',
        'Lever pivot/contact-end and intermediate poses are approximate drawing envelopes, not vendor CAD or elastic simulation',
        'Each received switch is meter-calibrated: actual OP is broad and cannot be covered by one fixed unadjusted tab',
        'Zero-clash tests are nominal rigid B-reps; printed tolerances, lever flex, grille deflection, friction/creep and actual wire bends require coupons',
        'The protected head raceway ends at head-local Z=-65 (global Z=-55); its continuation/connector routing into the electronics base is not adopted in this study',
        'COM/NO routes use nominal Ø1.2 mm insulation and R4 tangent bends; actual solder/heatshrink, wire grade and safe clamp compression need physical dressing',
        'The TPU liner free OD4.15 / installed OD4.0 and Ø1.1 wire holes are trial compression geometry; pull retention and insulation damage require coupons before approval',
        'Whole wired-unit service requires unplugging J12 and freeing the base continuation before withdrawal; the head-only study cannot prove the final base feed-through',
        'Smooth screw/nut/washer envelopes omit thread profiles and tolerances; body screw service occurs on the bench',
        'Local outboard tools are checked; full bench wiring/soldering tools and all original product fasteners are outside this study',
        'This switch supplements the captured fixed inner guard and does not stop a rotor instantaneously or provide a certified safety interlock',
        'This script does not mutate main sources; it uses a frozen repaired-fan head baseline and must be integrated and rechecked in the full assembly',
        'The head raceway strain clamp stays fixed while the switch bracket moves; cable service loop dressing is still a physical assembly task',
        'Guard input R5=3.9k to 5V through a 5V-tolerant 3V3 Schmitt buffer is the parent E3 revision; 1mA at 5V Omron reference and actual rail/contact life still require physical qualification',
      ],
      'primary_references':[{'url':'https://omronfs.omron.com/en_US/ecb/products/pdf/en-d2f.pdf',
        'local_file':'../../build/datasheets/grille-interlock/Omron-D2F-datasheet.pdf','pages':[2,3,4,5],
        'sha256':digest(DATASHEET) if DATASHEET.exists() else None},
        {'url':'https://components.omron.com/us-en/products/switches/D2F','CAD_attempt':'Manufacturer CAD listed but requires login/register; drawing-envelope fallback used'}],
      'artifact_sha256':artifacts}
    (OUT/'parameters.json').write_text(json.dumps(par,indent=2))
    (OUT/'validation.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({'status':'PASS','printable_parts':len(printable),'checks':len(comparisons),
      'panel_samples':len(kin),'panel_checks':panel_checks,'expected_lever_contacts':len(expected),
      'unintended_intersections':len(failures),'air_path_boundary_xmax':xmax},indent=2),flush=True)


if __name__=='__main__':
    try: main()
    except Exception:
        traceback.print_exc();sys.stdout.flush();sys.stderr.flush();os._exit(1)
    # Avoid the known OCP teardown fault only after all checks/exports succeed.
    sys.stdout.flush();sys.stderr.flush();os._exit(0)
