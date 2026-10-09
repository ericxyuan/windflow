"""Captive inlet/carrier interfaces and guarded removable cleaning grille.

Nominal geometry only: the printed guards have no fragment-containment rating.
"""
import cadquery as cq


def integrate(shell,p,record,box,cx,cy,rr):
    radius=p['throat_diameter']/2
    front=p['outer_sections_y_w_h_r'][-1][0]
    # Split shell captures this bell spigot and its shallow annular bead.
    # The front stop remains integrated with the structural head.
    shell=shell.cut(cy(radius+2.7,-.1,4.5))
    shell=shell.cut(cy(radius+3.1,.7,1.6))
    # Two nominal nozzle widths radially and two0.2mm layers axially. The former
    #0.3mm sleeve was not a reliable FDM part. Four rigid radial stops bound
    # carrier travel; the TPU has clearance windows around those stops.
    ro,ri=p['carrier_outer_radius'],p['carrier_inner_radius']
    radial,axial=p['carrier_radial_clearance'],p['carrier_axial_clearance']
    y0,y1=p['carrier_y0'],p['carrier_y1']
    tpu=cy(ro+radial,y0-axial,y1-y0+2*axial).cut(cy(ro,y0-axial-.1,y1-y0+2*axial+.2))
    for y in (y0-axial,y1):tpu=tpu.fuse(cy(ro+radial,y,axial).cut(cy(ri,y-.01,axial+.02)))
    for angle in (0,90,180,270):
        gap=p['carrier_hard_stop_gap']
        stop=box(2,5,4,ro+gap+1,(y0+y1)/2,0).rotate((0,0,0),(0,1,0),angle)
        window=box(3,5.4,4.4,ro+radial,(y0+y1)/2,0).rotate((0,0,0),(0,1,0),angle)
        shell=shell.fuse(stop)
        tpu=tpu.cut(window)
    record('TPU-carrier-isolation-ring-development',tpu.clean(),True,'TPU95A prototype')

    # Fixed inner front guard. 4.8 mm nominal clear slots plus one cross rib.
    # Screw access is exposed only after peeling off the magnetic grille.
    gy=168.5
    outer=cq.Solid.makeLoft([rr(114,104,6,gy),rr(114,104,6,gy+2)],True)
    inner=cq.Solid.makeLoft([rr(104,94,3,gy-.1),rr(104,94,3,gy+2.1)],True)
    guard=outer.cut(inner)
    for x in range(-48,49,6):guard=guard.fuse(box(1.2,2,96,x,gy+1,0))
    guard=guard.fuse(box(106,2,1.2,0,gy+1,0)).intersect(outer)
    seat=cq.Solid.makeLoft([rr(114.6,104.6,6.3,gy-.3),rr(114.6,104.6,6.3,gy+2.3)],True)
    shell=shell.cut(seat)
    for z in (-49.5,49.5):
        guard=guard.cut(cy(1.1,gy-.1,2.2,0,z))
        shell=shell.cut(cy(1.6,gy-4.1,4,0,z))
    record('fixed-front-finger-guard-development',guard.clean())

    # Rear inlet guard is independently attached to the bell/inlet flange.
    # A broad aperture preserves the rounded entry; no cells are added to the
    # rotor wake as an unsubstantiated honeycomb straightener.
    ry=-18
    rear=cy(75,ry,2.4).cut(cy(69,ry-.1,2.6))
    lattice=cy(69,ry,2.4)
    ribs=box(1.2,2.4,140,0,ry+1.2,0)
    for x in range(-66,67,6):ribs=ribs.fuse(box(1.2,2.4,140,x,ry+1.2,0))
    ribs=ribs.fuse(box(140,2.4,1.2,0,ry+1.2,0))
    rear=rear.fuse(ribs.intersect(lattice))
    for x,z in ((-72,0),(72,0),(0,-72),(0,72)):
        rear=rear.cut(cy(1.1,ry-.1,2.6,x,z))
    record('fixed-rear-inlet-guard-development',rear.clean())

    # Magnets load into front-facing blind pockets. Thin screw-on rings retain
    # every magnet mechanically. Mark all head outward faces N (or all S), and
    # opposite grille faces with the attracting polarity before installation.
    axes=[(x,z) for x in (-55,55) for z in (-50,50)]
    grille=cq.Solid.makeLoft([rr(120,110,8,front+1.6),rr(120,110,8,front+6)],True)
    grille=grille.cut(cq.Solid.makeLoft([rr(104,94,3,front+1.5),rr(104,94,3,front+6.1)],True))
    # Sparse cosmetic ribs align with every other fixed guard rib.
    for x in range(-48,49,12):grille=grille.fuse(box(.8,1.2,96,x,front+5.4,0))
    for x,z in axes:
        shell=shell.cut(cy(3.275,front-3.4,3.5,x,z))
        grille=grille.cut(cy(3.275,front+1.5,3.5,x,z))
        record(f'REF-head-D42-magnet-{x}-{z}',cy(3.175,front-3.3,3.175,x,z),False,'K&J D42 N42')
        record(f'REF-grille-D42-magnet-{x}-{z}',cy(3.175,front+1.7,3.175,x,z),False,'K&J D42 N42')
    for target,y,name in (('head',front,'head-magnet-retaining-ring-development'),
                           ('grille',front+.8,'grille-magnet-retaining-ring-development')):
        keeper=cq.Solid.makeLoft([rr(120,110,8,y),rr(120,110,8,y+.8)],True)
        keeper=keeper.cut(cq.Solid.makeLoft([rr(104.6,94.6,3.3,y-.1),rr(104.6,94.6,3.3,y+.9)],True))
        for x,z in ((-56,0),(56,0),(0,-51),(0,51)):
            keeper=keeper.cut(cy(1.1,y-.1,1,x,z))
            if target=='head':shell=shell.cut(cy(1.6,front-4.1,4.2,x,z))
            else:grille=grille.cut(cy(1.6,front+1.5,4.1,x,z))
        record(name,keeper.clean())
    record('magnetic-front-cleaning-grille-development',grille.clean())
    # Finger peel recess allows intentional removal without a projecting tab.
    shell=shell.cut(box(10,4,3.5,0,front-1,-54.5))
    return shell.clean(),{'front_fixed_guard_slot_mm':4.8,'rear_fixed_guard_slot_mm':4.8,
      'front_guard_y_mm':gy,'magnet_pocket_diameter_mm':6.55,
      'magnet_count':8,'magnet_nominal_gap_between_faces_mm':1.925,
      'keepers':'Two0.8mm rings, fourM2x6 screws each',
      'guard_qualification':'Finger-access geometry only; not certified fragment containment',
      'rear_attachment':'FourM2x10 through-bolts at radius72 with ISO4032 M2 nuts and ISO7089 washers; install nuts before closing head, qualify measured stack on coupon',
      'interlock':'OmronD2F-01L mounting and tongue remain to integrate; firmware motion inhibited'}
