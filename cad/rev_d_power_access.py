"""Side-facing USB-C port and a retained, intact HUSB238 board.

Development study against the checked Rev D shell. No supplied cable dimensions
or physical fastener fit are inferred from the vendor board model.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, math
import cadquery as cq

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'cad/rev_d'
OUT=BASE/'power-access-study'
PARAMETERS={
    'socket_face_x_mm':-110.5,'socket_center_y_mm':235.,
    'outer_port_face_x_mm':-112.1,'port_opening_y_mm':16.5,
    'port_opening_z_mm':9.2,'port_corner_radius_mm':2.2,
    'side_patch_width_y_mm':28.,'side_patch_height_z_mm':20.,
    'side_patch_corner_radius_mm':6.,'side_patch_inner_x_mm':-101.,
    'board_clearance_mm':.3,'post_radius_mm':3.5,
    'mount_screw_clearance_diameter_mm':2.2,'nut_pocket_af_mm':4.3,
    'nut_pocket_height_mm':1.9,'nut_pocket_top_below_pcb_mm':2.4,
    'screw_length_mm':6.,'screw_head_diameter_mm':3.8,'screw_head_height_mm':2.,
    'nominal_nut_af_mm':4.,'nominal_nut_height_mm':1.6,
    'trial_plug_width_y_mm':15.,'trial_plug_height_z_mm':7.5,
    'trial_plug_length_x_mm':30.,
}

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def box(x0,x1,y0,y1,z0,z1):
    return cq.Solid.makeBox(x1-x0,y1-y0,z1-z0,cq.Vector(x0,y0,z0))

def rounded_yz(w,h,r,x0,x1,y,z):
    a,b,k=w/2,h/2,math.sqrt(.5)
    wp=cq.Workplane(cq.Plane(origin=(x0,y,z),xDir=(0,1,0),normal=(1,0,0)))
    wire=(wp.moveTo(-a+r,-b).lineTo(a-r,-b)
          .threePointArc((a-r+r*k,-b+r-r*k),(a,-b+r)).lineTo(a,b-r)
          .threePointArc((a-r+r*k,b-r+r*k),(a-r,b)).lineTo(-a+r,b)
          .threePointArc((-a+r-r*k,b-r+r*k),(-a,b-r)).lineTo(-a,-b+r)
          .threePointArc((-a+r-r*k,-b+r-r*k),(-a+r,-b)).close().val())
    return cq.Solid.extrudeLinear(wire,[],cq.Vector(x1-x0,0,0))

def cylinder(r,z,h,x,y):
    return cq.Solid.makeCylinder(r,h,cq.Vector(x,y,z),cq.Vector(0,0,1))

def hexagon(af,z,h,x,y):
    return cq.Workplane('XY').polygon(6,2*af/math.sqrt(3)).extrude(h).val().translate((x,y,z))

def overlap(a,b):
    aa,bb=a.BoundingBox(),b.BoundingBox()
    if any(getattr(aa,k+'max')<=getattr(bb,k+'min')+1e-7 or
           getattr(bb,k+'max')<=getattr(aa,k+'min')+1e-7 for k in 'xyz'):return 0.
    return max(0.,a.intersect(b).Volume())

def design(original_left,original_usb,p=PARAMETERS):
    # Identify the PCB and its actual mounting holes, rather than treating
    # the 1 mm header holes as structural mounts.
    pcb=max(original_usb.Solids(),key=lambda solid:solid.Volume())
    holes=[]
    for face in pcb.Faces():
        if face.geomType()!='CYLINDER':continue
        c=face._geomAdaptor().Cylinder()
        if abs(c.Radius()-1.25)<1e-5:
            holes.append((c.Location().X(),c.Location().Y(),c.Location().Z()))
    assert len(holes)==2,('Expected two 2.5 mm PCB mounting holes',holes)
    shell_candidates=[s for s in original_usb.Solids()
                      if abs(s.BoundingBox().xlen-8.94)<.01 and
                         abs(s.BoundingBox().ylen-7.9)<.01 and
                         abs(s.BoundingBox().zlen-4.2)<.01]
    assert len(shell_candidates)==1,'Cannot uniquely identify USB-C shell'
    socket=shell_candidates[0];sb=socket.BoundingBox()
    usb_bounds=original_usb.BoundingBox()
    pivot=((sb.xmin+sb.xmax)/2,(usb_bounds.ymin+usb_bounds.ymax)/2,0)
    rotated=original_usb.rotate(pivot,(pivot[0],pivot[1],1),-90)
    rs=socket.rotate(pivot,(pivot[0],pivot[1],1),-90).BoundingBox()
    shift=(p['socket_face_x_mm']-rs.xmin,
           p['socket_center_y_mm']-(rs.ymin+rs.ymax)/2,0)
    usb=rotated.translate(shift)
    transformed_pcb=pcb.rotate(pivot,(pivot[0],pivot[1],1),-90).translate(shift)
    socket=socket.rotate(pivot,(pivot[0],pivot[1],1),-90).translate(shift)
    pb,sb,ub=transformed_pcb.BoundingBox(),socket.BoundingBox(),usb.BoundingBox()
    yc,zc=(sb.ymin+sb.ymax)/2,(sb.zmin+sb.zmax)/2
    mount=[]
    for hx,hy,hz in holes:
        mount.append((pivot[0]+hy-pivot[1]+shift[0],
                      pivot[1]-hx+pivot[0]+shift[1]))
    patch=rounded_yz(p['side_patch_width_y_mm'],p['side_patch_height_z_mm'],
                     p['side_patch_corner_radius_mm'],p['outer_port_face_x_mm'],
                     p['side_patch_inner_x_mm'],yc,zc)
    clearance=p['board_clearance_mm']
    # The large internal clearance starts at the PCB edge. The protruding
    # USB shell receives its own narrow relief, preserving the side-wall thickness.
    cavity=box(pb.xmin-clearance,ub.xmax+clearance,ub.ymin-clearance,ub.ymax+clearance,
               ub.zmin-clearance,ub.zmax+clearance)
    socket_relief=box(sb.xmin-clearance,sb.xmax+clearance,sb.ymin-clearance,sb.ymax+clearance,
                      sb.zmin-clearance,sb.zmax+clearance)
    plug_opening=rounded_yz(p['port_opening_y_mm'],p['port_opening_z_mm'],
                            p['port_corner_radius_mm'],p['outer_port_face_x_mm']-1,
                            sb.xmax+clearance,yc,zc)
    candidate=original_left.fuse(patch).cut(cavity).cut(socket_relief).cut(plug_opening)
    screws=[];nuts=[];post_bottom=zc-p['side_patch_height_z_mm']/2
    for x,y in mount:
        post=cylinder(p['post_radius_mm'],post_bottom,pb.zmin-post_bottom,x,y)
        rib=box(p['outer_port_face_x_mm']+1,p['side_patch_inner_x_mm'],
                y-2.4,y+2.4,post_bottom,pb.zmin-2.3)
        post=post.fuse(rib)
        nut_top=pb.zmin-p['nut_pocket_top_below_pcb_mm']
        pocket=hexagon(p['nut_pocket_af_mm'],nut_top-p['nut_pocket_height_mm'],
                       p['nut_pocket_height_mm'],x,y)
        pocket=pocket.fuse(box(x,x+6,y-2.2,y+2.2,
                               nut_top-p['nut_pocket_height_mm'],nut_top))
        candidate=candidate.fuse(post).cut(pocket).cut(
            cylinder(p['mount_screw_clearance_diameter_mm']/2,post_bottom-.1,
                     pb.zmin-post_bottom+.2,x,y))
        screws.append(cylinder(.99,pb.zmax-p['screw_length_mm'],p['screw_length_mm'],x,y).fuse(
            cylinder(p['screw_head_diameter_mm']/2,pb.zmax,p['screw_head_height_mm'],x,y)))
        nuts.append(hexagon(p['nominal_nut_af_mm'],nut_top-p['nominal_nut_height_mm']-.15,
                             p['nominal_nut_height_mm'],x,y).cut(
                                 cylinder(1.01,nut_top-2,2.2,x,y)))
    candidate=candidate.clean()
    trial_plug=rounded_yz(p['trial_plug_width_y_mm'],p['trial_plug_height_z_mm'],1.8,
                         sb.xmin-p['trial_plug_length_x_mm'],sb.xmin,yc,zc)
    coupon=candidate.intersect(box(p['outer_port_face_x_mm']-1,ub.xmax+2,
                                   yc-17,yc+17,zc-13,zc+13))
    metadata={'socket_face_x_mm':sb.xmin,'socket_center_yz_mm':[yc,zc],
              'pcb_bottom_z_mm':pb.zmin,'pcb_top_z_mm':pb.zmax,
              'pcb_mount_centers_xy_mm':mount,
              'socket_recess_mm':sb.xmin-p['outer_port_face_x_mm'],
              'patch_wall_before_port_cut_mm':pb.xmin-clearance-p['outer_port_face_x_mm'],
              'original_usb_transform':{'rotation_axis':list(pivot),'rotation_z_deg':-90,'translation_xyz_mm':list(shift)}}
    return candidate,usb,screws,nuts,coupon,trial_plug,metadata

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    stage=json.loads((BASE/'stage-validation.json').read_text())
    assert stage['result']=='PASS'
    for name,sha in stage['input_sha256'].items():assert digest(ROOT/name)==sha,('Stale stage',name)
    names={r['name']:r for r in stage['parts'] if r['name'] not in stage['excluded_alternative_and_reserves']}
    shapes={}
    for name,record in names.items():
        path=BASE/(name+'.step')
        assert digest(path)==record['sha256'],name
        shapes[name]=cq.importers.importStep(str(path)).val()
    left='P2-flowing-head-left-INTEGRAL-OUTLET';pd='Adafruit-HUSB238-5807-vendor'
    candidate,usb,screws,nuts,coupon,plug,metadata=design(shapes[left],shapes[pd])
    replacements={'USB-side-port-head-left-CANDIDATE':candidate,
                  'HUSB238-side-port-vendor-CANDIDATE':usb,
                  **{f'REF-PD-ISO4762-M2x6-{i+1}':s for i,s in enumerate(screws)},
                  **{f'REF-PD-ISO4032-M2-{i+1}':s for i,s in enumerate(nuts)}}
    for name,shape in replacements.items():
        assert shape.isValid(),name
        assert len(shape.Solids())==(34 if name.startswith('HUSB') else 1),(name,len(shape.Solids()))
    existing={n:s for n,s in shapes.items() if n not in (left,pd)}
    issues=[];counts=0
    items=list(replacements.items())
    for i,(name,shape) in enumerate(items):
        for other,fixed in list(existing.items())+items[i+1:]:
            volume=overlap(shape,fixed);counts+=1
            if volume>1e-4:issues.append({'a':name,'b':other,'overlap_mm3':volume})
        print('POWER ACCESS CHECKED',name,flush=True)
    plug_overlap=overlap(candidate,plug)
    if plug_overlap>1e-4:issues.append({'a':'UNVERIFIED trial plug','b':'side-port shell','overlap_mm3':plug_overlap})
    assert coupon.isValid() and len(coupon.Solids())==1,('Coupon disconnected',len(coupon.Solids()))
    records=[]
    for name,shape in {**replacements,'USB-side-port-fit-coupon':coupon,
                       'REF-USB-plug-size-TRIAL-UNVERIFIED':plug}.items():
        path=OUT/(name+'.step');cq.exporters.export(shape,str(path))
        restored=cq.importers.importStep(str(path)).val()
        assert restored.isValid() and abs(restored.Volume()-shape.Volume())<.1,name
        if name.endswith('coupon'):cq.exporters.export(restored,str(OUT/(name+'.stl')),tolerance=.02,angularTolerance=.08)
        records.append({'name':name,'sha256':digest(path),'solid_count':len(restored.Solids()),
                        'volume_mm3':restored.Volume()})
    report={'result':'PASS' if not issues else 'FAIL','generated_utc':datetime.now(timezone.utc).isoformat(),
            'physical_qualification':False,'parameters':PARAMETERS,**metadata,
            'pair_checks':counts,'issues':issues,'trial_plug_overlap_mm3':plug_overlap,
            'parts':records,'input_sha256':{str(path.relative_to(ROOT)):digest(path)
              for path in [Path(__file__),BASE/'stage-validation.json',BASE/(left+'.step'),BASE/(pd+'.step')]},
            'limits':['Intact manufacturer HUSB238 CAD; actual board revision/PCB/socket dimensions require fit check.',
                      'ISO fastener envelopes omit threads; actual screw/nut dimensions, engagement and tool access need verification.',
                      '15 x 7.5 mm trial cable boot is not supplied-cable CAD or a confirmed cable dimension.',
                      'Coupon only: not yet integrated into the complete stage, motion or export reports.',
                      'Power and I2C loom/strain relief are not yet installed; no mechanical or electrical qualification.']}
    (OUT/'power-access-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report['result'],counts,'checks;',len(issues),'collisions',flush=True)
    for issue in issues:print('COLLISION',issue,flush=True)
    if issues:raise SystemExit(1)

if __name__=='__main__':main()
