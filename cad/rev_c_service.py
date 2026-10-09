"""Rev C service interfaces, bought-part datums and replaceable board supports.

All dimensions in mm. Drawing envelopes remain explicitly unverified. This
module does not create a routed power PCB or certify a real harness bend.
"""
import math
import cadquery as cq


def integrate(root, p, base, tray, parts, record, box, cx, cy, cz):
    fasteners = []
    mounts = []
    reserves = {}

    def imported(name, source, shift, printed=False, rotation=None):
        s = cq.importers.importStep(str(root/source)).val()
        if rotation is not None:
            s=s.rotate((0,0,0),(0,0,1),rotation)
        s=s.translate(shift)
        record(name, s, printed, source=str(source), one_solid=False)
        # Bake the located transform before subsequent Boolean reliefs. Cuts
        # on the translated source otherwise disappeared in the exchanged
        # cradle and D-shaft, despite an empty in-memory common.
        normalized = cq.importers.importStep(str(root/'rev_c'/(name+'.step'))).val()
        parts[name] = normalized
        return normalized

    def post(name, x, y, top, drill=2.2, radius=2.8, nut_af=4.2,neck_radius=None):
        nonlocal tray
        floor = p['base_bottom_z'] - .2
        s = cz(radius, floor, top-floor, x, y)
        if neck_radius is not None:
            s=cz(radius,floor,top-2.5-floor,x,y).fuse(cz(neck_radius,top-2.5,2.5,x,y))
        tray = tray.fuse(s).cut(cz(drill/2, floor-3.1, top-floor+3.3, x, y))
        nut = (cq.Workplane('XY').polygon(6,nut_af/math.cos(math.pi/6)).extrude(2.2)
               .val().translate((x,y,floor-1.4)))
        tray = tray.cut(nut)
        fasteners.append({'interface':name, 'axis_xyz_mm':[x,y,top],
                          'direction':'+Z', 'hole_diameter_mm':drill,
                          'nut_af_mm':nut_af, 'nut_loaded_from':'tray underside'})

    # Vendor Pico and two 5 V regulators. The 12 V fan buck is superseded.
    imported('Raspberry-Pi-Pico-SC0915-vendor','rev_b/Raspberry-Pi-Pico-SC0915-vendor.step',(-20,-3,-4))
    for x in (-70.2,-58.8):
        for y in (60,107): post('Pico M1.6x12 / DIN934 M1.6',x,y,-110,1.8,2.4,3.3)
    for tag,shift in (('logic',(0,-8,-4)),('servo',(2,-8,-4))):
        old = 'rev_b/Pololu-D24V22-5V-'+tag+'-vendor.step'
        imported('Pololu-D24V22-5V-'+tag+'-vendor',old,shift)
        # Logic vendor offset -27; servo vendor offset -1.
        offset = -27 if tag == 'logic' else 1
        for hx,hy in ((15.494,2.286),(2.286,15.494)):
            post('D24V22F5 M2x14',offset+hx,10+hy,-108.9)

    imported('Adafruit-HUSB238-5807-vendor','rev_b/Adafruit-HUSB238-5807-vendor.step',(-30,13.2,-4))
    for x in (44.667,59.907): post('HUSB238 M2x14',x,8.653,-108.079823488)
    base = base.cut(box(24,24,12,52,0,-102))
    reserves['USB-C plug and bend'] = box(20,32,14,52,-14,-102)
    mounts.append({'component':'HUSB238','connector_access':'rear -Y',
                   'remaining':'Actual Type-C plug/captive cable fit and strain at port'})

    # One NeoPixel stick illuminates down through a recessed diffuser. These
    # genuine vendor hole axes are retained. Keeper screws load from below.
    imported('Adafruit-NeoPixel-1426-ambient-vendor','rev_b/Adafruit-NeoPixel-1426-ambient-vendor.step',(-15,37,-3))
    tray=tray.cut(box(55,12,1.05,0,82,-120.95))
    # The vendor's rear component is only1.62mm from the right hole centre.
    # M2 cap heads and a broad post collide here; use a3mm-head M1.6 screw
    # and a narrower replaceable neck while retaining the genuine hole axes.
    for x in (-12.85,12.55): post('ambient PCB M1.6x8 / DIN934 M1.6',x,78.922,-113.6,
                                 drill=1.8,radius=2.4,nut_af=3.3,neck_radius=1.45)
    keeper=box(74,18,1.2,0,82,-121.6).cut(box(51.8,8.6,1.5,0,82,-121.6))
    keeper=keeper.cut(box(55,12,.4,0,82,-121.1))
    for x in (-32,32):
        tray=tray.fuse(cz(3.5,-121,6,x,82)).cut(cz(1.6,-121.1,6.2,x,82))
        keeper=keeper.cut(cz(1.1,-122.3,1.5,x,82))
    record('ambient-diffuser-keeper-development',keeper)
    record('ambient-diffuser-development',box(54.6,11.6,.8,0,82,-120.9),True,'translucent PETG')
    mounts.append({'component':'ambient #1426','LED_to_diffuser_minimum_mm':5.3,
                   'service':'Undo two M2 keeper screws, remove diffuser, remove LED PCB screws and unplug harness.'})

    # Reuse the genuine screen hole datums, not a rectangle approximating glass.
    cradle=imported('display-removable-cradle-development','rev_b/display-removable-cradle.step',(-15,31,-1),True)
    cradle=cradle.cut(box(200,200,20,0,150,-67.3))
    record('display-removable-cradle-development',cradle)
    for x in (-38,34):
        for z in (-81.6,-109.4):
            base=base.fuse(cy(4,158.1,12,x,z)).cut(cy(2,158,6.9,x,z))
            fasteners.append({'interface':'screen cradle M3x8 / RX-M3x5.7',
                              'axis_xyz_mm':[x,158.1,z],'direction':'+Y'})
    bezel=parts['display-front-bezel-development']
    for x in (-36,36):
        for z in (-85.5,-105.5):
            base=base.fuse(cy(3.2,166.7,3.9,x,z)).cut(cy(1.6,166.6,4.2,x,z))
            bezel=bezel.cut(cy(1.1,170.5,2.7,x,z))
            fasteners.append({'interface':'bezel M2x6 / RX-M2x4',
                              'axis_xyz_mm':[x,173,z],'direction':'-Y'})
    record('display-front-bezel-development',bezel)
    mounts.append({'component':'Adafruit4311 screen','active_center_xz_mm':[0,-95.5],
                   'cradle_path':'Unplug loom; remove bezel/lens and tray; unscrew cradle; pull -Y4mm then lower -Z.',
                   'remaining':'Current EYESPI cable and actual glare/viewing angle'})

    # User's 8 October clarification: the wheel is beside the LCD, and its
    # rotation plane is parallel to that face. Its horizontal shaft is +Y;
    # pushing toward the desk fan is -Y. Reuse the actual routed board datum,
    # but give its mount screws a different axis from the PCB support screws.
    ex,ez=p['encoder_center_x'],p['encoder_center_z']
    face=p['encoder_mount_face_y']
    offset=face-72.4
    shift=(ex-3,offset,ez+90)
    imported('horizontal-encoder-thumbwheel-development','rev_b/horizontal-encoder-thumbwheel.step',shift,True,-90)
    enc=cq.importers.importStep(str(root/'rev_b/REF-Bourns-PEC11H-drawing-envelope.step')).val()
    # True nominal D-flat: 1.5mm from the shaft axis, not a round shaft
    # intersecting the existing D-shaped printed bore.
    enc=enc.cut(box(10.2,6,8,-80,7.5,-90)).rotate((0,0,0),(0,0,1),-90).translate(shift)
    record('REF-Bourns-PEC11H-drawing-envelope',enc,False,'Bourns drawing D-shaft envelope')
    imported('encoder-daughterboard-P1-FR4','rev_b/encoder-daughterboard-P1-FR4.step',shift,False,-90)
    imported('REF-M7x0p75-encoder-panel-nut','rev_b/REF-M7x0p75-encoder-panel-nut.step',shift,False,-90)
    plate_back=face-2.4
    pcb_front=62.5+offset
    mount=box(35,2.4,28,ex+5.5,face-1.2,ez).cut(cy(3.65,plate_back-.1,2.6,ex,ez))
    for z in (ez-8.5,ez+8.5):
        xx=ex+19
        mount=mount.fuse(cy(3,pcb_front,plate_back-pcb_front+.15,xx,z))
        mount=mount.cut(cy(1.1,pcb_front-.1,face-pcb_front+.2,xx,z))
        trap=(cq.Workplane(cq.Plane(origin=(xx,pcb_front-.1,z),xDir=(1,0,0),normal=(0,1,0)))
              .polygon(6,4.2/math.cos(math.pi/6)).extrude(2.4).val())
        mount=mount.cut(trap)
        fasteners.append({'interface':'encoder PCB M2x10 / DIN934 M2',
                          'axis_xyz_mm':[xx,pcb_front-1.6,z],'direction':'+Y',
                          'nut_loaded_from':'PCB-facing mouth before installing board'})
    base=base.cut(cy(15.8,face-3.5,18,ex,ez))
    base=base.cut(box(35.6,11,28.6,ex+5.5,face-5.2,ez))
    # A narrow left brace joins the face's curved wall to both mounting bosses
    # without passing through the encoder case or its soldered daughterboard.
    base=base.fuse(box(3,25.2,36,ex-15,face-10,ez))
    for z in (ez-10,ez+10):
        xx=ex-8.5
        mount=mount.cut(cy(1.65,plate_back-.1,2.6,xx,z))
        base=base.fuse(box(8.5,6.8,4,ex-12.25,plate_back-3.6,z))
        base=base.fuse(cy(3.6,plate_back-7,6.8,xx,z))
        base=base.cut(cy(2,plate_back-6.9,6.7,xx,z))
        fasteners.append({'interface':'encoder mount M3x8 / RX-M3x5.7',
                          'axis_xyz_mm':[xx,face,z],'direction':'-Y'})
    record('horizontal-encoder-mount-development',mount)
    # Rounded local fascia surrounds the rim, while the whole disk face is
    # exposed for in-plane rotation. No former side-wall opening remains.
    rim=cy(17.5,face+.3,5.4,ex,ez).cut(cy(15.8,face+.2,5.6,ex,ez))
    base=base.fuse(rim)
    mounts.append({'component':'Bourns PEC11H-4215F-S0024','axis':'horizontal +Y',
                   'rotation_plane':'XZ, parallel to screen face',
                   'wheel_center_xz_mm':[ex,ez],
                   'wheel_axial_bounds_y_mm':[77.5+offset,85.5+offset],
                   'PCB':'routed P1 datum, separate captive-nut M2 supports',
                   'press_direction':'-Y, toward enclosure',
                   'remaining':'Actual press travel, direction preference, reach and one-handed desk stability'})

    # Sensors: power-board-adjacent temperature, motor-area air temperature and
    # real pressure housing. They remain serviceable on the tray. Motor-area
    # temperature is a proxy; it cannot replace ESC telemetry or winding tests.
    for tag,shift,offset in (
            ('temp1', (8,-4,-7),(-45,38,-110)),
            ('temp2',(-17,12,-7),(-72,129,-110))):
        imported('MCP9808-'+tag+'-Adafruit1782-vendor','rev_b/MCP9808-'+tag+'-Adafruit1782-vendor.step',shift)
        tx,ty,tz=offset
        for hx in (2.54,17.78):post('MCP9808 M2x12',tx+hx,ty+10.16,tz)
    imported('Sensirion-SDP810-125Pa-vendor','rev_b/Sensirion-SDP810-125Pa-vendor.step',(7,73,-4))
    for x in (47.2,75.8):post('SDP810 restrained housing M2',x,92.75,-104.675)
    mounts.append({'component':'SDP810-125Pa','remaining':'Direct-soldered2mm-pitch board, compliant housing cradle, tubes and port routing'})

    # New driver-board mounting datum and ESC cradle; no fabricated circuit is
    # implied by these mechanical interfaces. Soft strap contacts the real case
    # only after exact V2.3c dimensions are verified.
    for x in (-48,26):
        for y in (71.5,120.5):post('new80x55 carrier M2x12',x,y,-110)
    mounts.append({'component':'new power/control PCB','outline_mm':[80,55,1.6],
                   'minimum_xyz_mm':[-51,68.5,-110],
                   'holes_xy_mm':[[-48,71.5],[-48,120.5],[26,71.5],[26,120.5]],
                   'status':'139-component circuit captured and ERC checked; mechanical target only, PCB unrouted'})
    cradle=box(52,28,2.4,37,45,-111.2)
    for x in (12.5,61.5):
        cradle=cradle.fuse(box(3,28,4,x,45,-108))
        tray=tray.fuse(cz(3,-118.2,5.8,x,45)).cut(cz(1.6,-121.2,11.4,x,45))
        cradle=cradle.cut(cz(1.1,-112.5,2.7,x,45))
    record('ESC-service-cradle-development',cradle)
    # Strap slots accept a removable 3mm-wide nonconducting tie, away from PCB.
    for x in (12.5,61.5):
        cradle=cradle.cut(box(1.4,5,5,x,45,-108))
    record('ESC-service-cradle-development',cradle)
    mounts.append({'component':'A50S V2.3c','envelope_mm':[46,22,17],
                   'service':'Unplug UART, XT30 and MR30; release insulating strap; lift out.',
                   'remaining':'Exact case/connector CAD and actual strap pressure/air gap'})

    # Four closed-bottom base insert pillars and separate replaceable desk feet.
    # Foot top is below the tray: the downward lighting has real desk clearance.
    for x,y in ((-79,18),(79,18),(-79,143),(79,143)):
        base=base.fuse(cz(4.7,-118,43,x,y)).cut(cz(2,-118.1,6.9,x,y))
        fasteners.append({'interface':'tray/foot M3x12 / RX-M3x5.7',
                          'axis_xyz_mm':[x,y,-126],'direction':'+Z'})

    # High rear passive vents and a harness exit in the servo cover corridor.
    # These vents cool electronics independently of rotor motion.
    for x in (-65,-53,-41,-29,-17,-5):base=base.cut(box(5,12,3,x,3,-78))
    base=base.cut(box(8,12,10,75,100,-76))
    return base.clean(),tray.clean(),fasteners,mounts,reserves
