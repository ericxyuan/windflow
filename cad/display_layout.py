"""Real Adafruit 4311 display, removable cradle and clear front window.

Coordinates follow the supplier STEP, checked against the current EYESPI board.
The 2019 CAD is a dimensional reference; cable/connector fit needs qualification.
"""
import math
import cadquery as cq

def integrate(base, parts, save, vendor, box, cy, fasteners, mounts):
    # Transform original X into -Z, original Y into X, display face into +Y.
    # Supplier active face centre: (17.77946544,31.47224905,-2.49119780).
    x0=-16.4722490462148
    z0=-76.7205345602586
    face_y=139.0
    y0=face_y-2.49119779854318
    display=vendor('Adafruit-ST7789-4311-display-vendor','4311.step',
                   [((0,0,1),-90),((1,0,0),90)],
                   (x0,y0-3.45,z0-35.56))
    # Opening is slightly larger than the actual 40.8 x30.6 active area.
    base=base.cut(box(62.0,15,37.0,13.05525,134.8,-94.5))
    frame=box(64.6,1.6,39.2,13.05525,126.3,-94.5)
    frame=frame.cut(box(56.6,2,32.0,13.05525,126.3,-94.5))
    # Header exits the left end; no plastic crosses the solder/pigtail region.
    frame=frame.cut(box(8,4,29,x0,126.3,-94.5))
    # Two genuine supplier PCB holes; the cradle has rear-accessible captive nuts.
    for orig_x in (2.54,33.02):
        x=x0+56.515; z=z0-orig_x
        post=cy(2.6,125.5,9.4388022014568,x,z)
        frame=frame.fuse(post).cut(cy(1.1,125.4,9.65,x,z))
        nut=cq.Workplane('XZ').polygon(6,4.2/math.cos(math.pi/6)).extrude(-2.0).val().translate((x,125.4,z))
        frame=frame.cut(nut)
        fasteners.append({'location':'4311 display PCB','axis_mm':[x,136.5088022014568,z],
                          'hardware':'M2x12 screw and DIN934 M2 nut; screw through PCB, nut loaded from rear'})
    # Rear-accessible frame screws, positioned outside the whole vendor PCB.
    for x in (-23,49):
        for z in (-80.6,-108.4):
            frame=frame.fuse(box(9,1.6,7,x,126.3,z)).cut(cy(1.65,125.4,1.8,x,z))
            base=base.fuse(cy(4.0,127.4,10.2,x,z)).cut(cy(2,127.3,6.9,x,z))
            fasteners.append({'location':'display removable cradle','axis_mm':[x,125.5,z],
                              'hardware':'M3x8 screw and Ruthex RX-M3x5.7 insert, installed from rear'})
    # Clear sheet, not a diffuser. 0.2 mm edge clearance and 0.76 mm module gap.
    window=box(45.0,1.0,34.4,15,140.4,-94.5)
    save('REF-display-clear-window-45x34p4x1',window,'clear acrylic sheet, cut to drawing',False)
    bezel=box(78,1.6,39.6,13,140.8,-94.5)
    bezel=bezel.cut(box(42.4,2,31.6,15,140.8,-94.5))
    bezel=bezel.cut(box(45.4,1.2,34.8,15,140.35,-94.5))
    for x in (-23,49):
        for z in (-85.5,-103.5):
            base=base.fuse(cy(3.2,135.5,4.5,x,z)).cut(cy(1.6,135.4,4.7,x,z))
            bezel=bezel.cut(cy(1.1,139.9,1.8,x,z))
            fasteners.append({'location':'display front bezel','axis_mm':[x,141.6,z],
                              'hardware':'M2x6 screw and Ruthex RX-M2x4 insert, 3.2 mm initial pilot; clear sheet retained with 3M467MP perimeter film'})
    save('display-removable-cradle',frame)
    save('display-front-bezel',bezel)
    b=display.BoundingBox()
    mounts.append({'component':'Adafruit 4311 ST7789 IPS display',
       'source':'Manufacturer STEP and EYESPI Eagle board; current product page confirms unchanged size/pinout',
       'vendor_bounds_mm':[b.xlen,b.ylen,b.zlen],
       'active_area_mm':[40.8,30.6], 'active_center_xz_mm':[15,-94.5],
       'pcb_hole_axes_xyz_mm':[[x0+56.515,136.5088022014568,z0-h] for h in (2.54,33.02)],
       'cover_mm':[45,34.4,1], 'lens_to_module_nominal_gap_mm':139.9-b.ymax,
       'cradle_removal':'Unplug display pigtail; remove front bezel/window and service tray; undo four rear screws; withdraw cradle rearward 2 mm then lower through open bottom',
       'remaining_test':'Check current EYESPI rear connector, right-angle solder pigtail, optical alignment, clear-sheet fit and screw pilots on coupon'})
    assert abs(b.xlen-59.055)<.01 and abs(b.zlen-35.56)<.01
    return base
