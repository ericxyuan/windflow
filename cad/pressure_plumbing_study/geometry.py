"""Pure reusable pressure-layout geometry. All coordinates are globalmm.

Call make_pressure_layout(head_z), apply_base(shell,tray,layout), and
apply_head(head_global,layout). Skip the old main sensor-support block before
apply_base; it adds the newly rotated supports. No I/O occurs on import.
Fittings and connector are explicitly drawing/reserve envelopes.
"""
import math
import cadquery as cq
R_OUT = 7.14375/2
R_IN = 3.96875/2
def box(w, d, h, x, y, z):
    return cq.Workplane('XY').box(w, d, h).translate((x, y, z)).val()

def cyl(r, length, p, direction):
    return cq.Solid.makeCylinder(r, length, cq.Vector(*p), cq.Vector(*direction))

def sensor_transform(shape):
    return shape.rotate((54.5, 21.525, 0), (54.5, 21.525, 1), 180).translate((0, 0, -.5))

def original_supports():
    old_restraints = []
    for x in (42.5, 66.5):
        post = box(5.8, 4.2, 20.575, x, 37.35, -104.3125)
        post = post.fuse(cyl(2.4, 3.3, (x, 31.95, -97.025), (0, 1, 0)))
        post = post.cut(cyl(1.1, 7.8, (x, 31.8, -97.025), (0, 1, 0)))
        nut = cq.Workplane('XZ').polygon(6, 4.2/math.cos(math.pi/6)).extrude(-2).val().translate((x, 37.65, -97.025))
        old_restraints.append(post.cut(nut))
    for x in (47.5, 61.5):
        post = box(6, 4, 13.825, x, 35.85, -107.6875)
        post = post.cut(cyl(1.1, 4.3, (x, 33.75, -103.775), (0, 1, 0)))
        nut = cq.Workplane('XZ').polygon(6, 4.2/math.cos(math.pi/6)).extrude(-1.8).val().translate((x, 36.05, -103.775))
        old_restraints.append(post.cut(nut))
    return old_restraints

class Route:
    def __init__(self, start):
        self.start = tuple(start)
        self.point = self.start
        self.edges = []
        self.segments = []
    def line(self, end):
        end = tuple(end)
        length = math.dist(self.point, end)
        if length > 1e-8:
            self.edges.append(cq.Edge.makeLine(cq.Vector(*self.point), cq.Vector(*end)))
            self.segments.append({'kind': 'line', 'start': self.point, 'end': end, 'length_mm': length})
            self.point = end
        return self
    def arc(self, middle, end, radius, angle):
        end = tuple(end)
        self.edges.append(cq.Edge.makeThreePointArc(cq.Vector(*self.point), cq.Vector(*middle), cq.Vector(*end)))
        self.segments.append({'kind': 'arc', 'start': self.point, 'end': end,
                              'radius_mm': radius, 'angle_deg': math.degrees(angle),
                              'length_mm': radius*angle})
        self.point = end
        return self
    @property
    def length(self):
        return sum(s['length_mm'] for s in self.segments)
    def solid(self, radius=R_OUT, inside=None):
        tangent = self.edges[0].tangentAt(0)
        path = cq.Wire.assembleEdges(self.edges)
        outer = cq.Wire.makeCircle(radius,cq.Vector(*self.start),tangent)
        body = cq.Solid.sweep(outer,[],path,True,False,transitionMode='transformed')
        if inside is not None:
            inner = cq.Wire.makeCircle(inside,cq.Vector(*self.start),tangent)
            bore = cq.Solid.sweep(inner,[],path,True,False,transitionMode='transformed')
            body = body.cut(bore)
        # Nested-wire sweep silently truncated this route in the installed OCP
        # version. Verify physical volume independently, rather than accepting
        # a valid but incomplete B-rep as a successful hose model.
        expected = math.pi*(radius**2-(inside or 0)**2)*self.length
        assert abs(body.Volume()-expected)<max(.02,expected*1e-5),(body.Volume(),expected)
        assert body.isValid() and len(body.Solids())==1
        return body

def routes(head_z=10.0):
    k = math.sqrt(.5)
    positive = Route((48.2, 24.8, -93.025))
    positive.line((48.2, 39, -93.025)).arc((33.2+15*k, 39+15*k, -93.025),
                                          (33.2, 54, -93.025), 15, math.pi/2)
    # Four rounded turns make a low serpentine, clear of the sensor body. This
    # supplies equal hose length without crossing the reference lead or kinking.
    positive.arc((33.2-15*k,39+15*k,-93.025),(18.2,39,-93.025),15,math.pi/2)
    positive.arc((3.2+15*k,39-15*k,-93.025),(3.2,24,-93.025),15,math.pi/2)
    positive.line((-28,24,-93.025))
    positive.arc((-28-15*k,39-15*k,-93.025),(-43,39,-93.025),15,math.pi/2)
    positive.arc((-58+15*k,39+15*k,-93.025),(-58,54,-93.025),15,math.pi/2)
    positive.arc((-58-15*k, 54, -78.025-15*k),
                                        (-73, 54, -78.025), 15, math.pi/2)
    distance = math.hypot(1.5, 11)
    theta = math.acos(1-distance/(2*15))
    rise = 2*15*math.sin(theta)
    start_z = head_z-30-rise
    u = (-1.5/distance, 11/distance)
    positive.line((-73, 54, start_z))
    def s_arc1(t):
        return (-73+u[0]*15*(1-math.cos(t)), 54+u[1]*15*(1-math.cos(t)), start_z+15*math.sin(t))
    mid_s = s_arc1(theta)
    positive.arc(s_arc1(theta/2), mid_s, 15, theta)
    def s_arc2(t):
        return (mid_s[0]+u[0]*15*(math.cos(theta-t)-math.cos(theta)),
                mid_s[1]+u[1]*15*(math.cos(theta-t)-math.cos(theta)),
                mid_s[2]+15*(math.sin(theta)-math.sin(theta-t)))
    positive.arc(s_arc2(theta/2), s_arc2(theta), 15, theta).line((-74.5, 65, head_z-7.653))
    
    reference = Route((60.8, 24.8, -93.025))
    reference.line((60.8, 39, -93.025)).arc((75.8-15*k, 39+15*k, -93.025),
                                          (75.8, 54, -93.025), 15, math.pi/2)
    reference.line((82, 54, -93.025)).arc((82+15*k, 69-15*k, -93.025),
                                    (97, 69, -93.025), 15, math.pi/2)
    # Keep the long reference loop above the display cradle.  Moving its
    # centre 8 mm left adds 8 mm at the loop entry and 8 mm at the elbow
    # exit; the resulting 16 mm lower centre keeps both hose lengths equal
    # without introducing a kink or a tighter bend.
    loop_x = 55.0
    loop_radius = 34.0
    end_x = 83.5-17.653+10
    loop_right = loop_x + loop_radius
    fixed_length = (reference.length + (97-loop_right)
                    + 3*math.pi/2*loop_radius + end_x-loop_x)
    loop_y = 69 + positive.length-fixed_length
    reference.line((loop_right, loop_y, -93.025))
    reference.arc((loop_x+loop_radius*k, loop_y+loop_radius*k, -93.025),
                  (loop_x, loop_y+loop_radius, -93.025), loop_radius, math.pi/2)
    reference.arc((loop_x-loop_radius*k, loop_y+loop_radius*k, -93.025),
                  (loop_x-loop_radius, loop_y, -93.025), loop_radius, math.pi/2)
    reference.arc((loop_x-loop_radius*k, loop_y-loop_radius*k, -93.025),
                  (loop_x, loop_y-loop_radius, -93.025), loop_radius, math.pi/2)
    reference.line((end_x, loop_y-loop_radius, -93.025))
    assert abs(positive.length-reference.length)<1e-6
    
    return positive, reference, loop_y

def elbow(center, inlet=(-1, 0, 0)):
    """Drawing envelope, core length17.653; bore, tips/barb diameters published.

    Undimensioned taper lengths are conservatively enveloped by max-barb Ø.
    This is sufficient for clearance; it is not a manufacturing reconstruction.
    """
    body = box(9.398, 9.398, 9.398, *center)
    for direction in (inlet, (0, 0, -1)):
        p = tuple(center[i]+direction[i]*4.699 for i in range(3))
        body = body.fuse(cyl(5.8928/2, 17.653-4.699, p, direction))
        body = body.cut(cyl(2.54/2, 17.8, center, direction))
    return body

def make_pressure_layout(head_z=10.0):
    positive, reference, loop_y = routes(head_z)
    head_center = (-74.5, 65, head_z)
    ref_center = (83.5, loop_y-34, -93.025)
    head_elbow = elbow(head_center, (1, 0, 0))
    ref_elbow = elbow(ref_center)
    head_receiver = cyl(4.9, 16.5, (-71, 65, 10), (1, 0, 0))
    head_receiver = head_receiver.cut(cyl(3.2, 14.4, (-71.1, 65, 10), (1, 0, 0)))
    head_receiver = head_receiver.cut(cyl(1.27, 18, (-72, 65, 10), (1, 0, 0)))
    head_additions = [head_receiver]
    head_cuts = []
    tray_additions = []
    tray_cuts = []
    # The old socket is entirely inside the new receiver. The channel terminates at
    # the existing duct surface; clip additions against a copied passage-free head.
    head_cuts.append(cyl(1.27, 18, (-72, 65, 10), (1, 0, 0)))
    # New receiver holds a nylon leg with a flexible seal; clamp takes pull forces.
    head_clamp = box(12, 24, 13, -75, 65, 10).cut(box(10.1, 10.1, 10.1, -74.5,65,10))
    head_clamp = head_clamp.cut(cyl(3.25, 14, (-75, 65, -3), (0, 0, 1)))
    head_clamp = head_clamp.cut(box(8, 16, 14, -69, 65, 10))
    for y in (57, 73):
        head_additions.append(cyl(3.8, 4.8, (-72, y, 10), (1, 0, 0)))
        head_cuts.append(cyl(1.1, 5, (-72.1, y, 10), (1, 0, 0)))
        nut = cq.Workplane('YZ').polygon(6,4.2/math.cos(math.pi/6)).extrude(1.9).val().translate((-68.9,y,10))
        head_cuts.append(nut)
        head_clamp = head_clamp.cut(cyl(1.1, 14, (-82, y, 10), (1, 0, 0)))
    # Move the capture half toward the enclosure exterior.  Its original
    # 2 mm overlap with the enlarged head receiver was an unintended solid
    # intersection; the translated opening still captures the elbow body and
    # leaves a nominal receiver clearance.
    head_clamp = head_clamp.translate((-2.25, 0, 0))
    
    
    ref_receiver = cyl(5, 16.6, (ref_center[0], ref_center[1], -114.6), (0, 0, 1))
    ref_receiver = ref_receiver.cut(cyl(3.2, 14, (ref_center[0], ref_center[1], -111.9), (0, 0, 1)))
    ref_receiver = ref_receiver.cut(cyl(1.27, 22, (ref_center[0], ref_center[1], -118), (0, 0, 1)))
    tray_additions.append(ref_receiver)
    tray_cuts.append(cyl(1.27, 22, (ref_center[0], ref_center[1], -118), (0, 0, 1)))
    ref_clamp = box(17, 19, 14.5, ref_center[0], ref_center[1], -93.95).cut(box(10.1, 10.1, 10.1, *ref_center))
    ref_clamp = ref_clamp.cut(cyl(3.25, 14, (ref_center[0], ref_center[1], -102), (0, 0, 1)))
    ref_clamp = ref_clamp.cut(cyl(5.2, 4.3, (ref_center[0], ref_center[1], -102), (0, 0, 1)))
    # The hose OD and its temporary installation sleeve both pass through
    # this clearance bore.  Ø10 mm keeps the printed capture wall substantial
    # while avoiding a false clamp-versus-hose interference.
    ref_clamp = ref_clamp.cut(cyl(5.0, 34, (ref_center[0]-24, ref_center[1], -93.025), (1, 0, 0)))
    ref_clamp = ref_clamp.cut(box(9, 9.6, 14, ref_center[0]-7, ref_center[1], -96.6))
    for x in (ref_center[0]-6, ref_center[0]+6):
        tray_additions.append(cyl(3.5, 13, (x, ref_center[1], -114.6), (0, 0, 1)))
        tray_cuts.append(cyl(1.1, 8, (x, ref_center[1], -107), (0, 0, 1)))
        nut = cq.Workplane('XY').polygon(6,4.2/math.cos(math.pi/6)).extrude(5).val().translate((x,ref_center[1],-104.5))
        tray_cuts.append(nut)
        lower_nut = cq.Workplane('XY').polygon(6,4.2/math.cos(math.pi/6)).extrude(5).val().translate((x,ref_center[1],-118.7))
        tray_cuts.append(lower_nut)
        tray_cuts.append(cyl(1.1,8,(x,ref_center[1],-120.9),(0,0,1)))
        ref_clamp = ref_clamp.cut(cyl(1.1, 16, (x, ref_center[1], -106), (0, 0, 1)))
    # A baffled downward ambient entry stays clear of the underglow and desk feet.
    baffle = cyl(7, 2.4, (ref_center[0], ref_center[1], -121), (0, 0, 1))
    for x in (ref_center[0]-6, ref_center[0]+6):
        baffle = baffle.fuse(cyl(2.8, 1.9, (x, ref_center[1], -119), (0, 0, 1))).cut(cyl(1.1, 8, (x, ref_center[1], -122), (0, 0, 1)))
    
    # Ceiling hole and slit TPU seal let the tubing pull free without threading a
    # permanently attached head/fitting through the enclosure during assembly.
    shell_cuts = [cyl(4.7, 4, (-73, 54, -75), (0, 0, 1))]
    shell_additions = []
    grommet = cyl(5.7, 1.0, (-73, 54, -74.6), (0, 0, 1)).fuse(cyl(4.6, 2.4, (-73, 54, -74.4), (0, 0, 1)))
    grommet = grommet.cut(cyl(3.7, 4, (-73, 54, -75), (0, 0, 1))).cut(box(.6, 13, 5, -73, 59, -73))
    
    # An outward-mounted C clip reserves the long reference loop without posts
    # piercing the carrier. Its two bolts are above/below the hose centreline.
    clip_y = (69+loop_y)/2
    clip_x = loop_right
    clip = box(9.6,10,24,clip_x+5.8,clip_y,-93.025).fuse(cyl(5.2,10,(clip_x,clip_y-5,-93.025),(0,1,0)))
    clip = clip.cut(cyl(R_OUT+.35,12,(clip_x,clip_y-6,-93.025),(0,1,0)))
    clip = clip.cut(box(10,12,6,clip_x-5.5,clip_y,-93.025))
    for z in (-101.025,-85.025):
        clip = clip.cut(cyl(1.1,10,(clip_x+.9,clip_y,z),(1,0,0)))
        shell_cuts.append(cyl(1.1,4,(clip_x+10,clip_y,z),(1,0,0)))
        nut = cq.Workplane('YZ').polygon(6,4.2/math.cos(math.pi/6)).extrude(1.9).val().translate((108.2,clip_y,z))
        shell_cuts.append(nut.translate((clip_x-97,0,0)))
    clamps = {'pressure-reference-wall-clip':clip}
    
    # Direct solder tails leave the component face toward-Y. A flexible pigtail
    # disconnects at the carrier; no invented inline connector is fitted here.
    pigtail_exit = box(7.5,6,3,54.5,5.2,-103)
    
    
    head_additions = [a.translate((0,0,head_z-10)) for a in head_additions]
    head_cuts = [a.translate((0,0,head_z-10)) for a in head_cuts]
    head_clamp = head_clamp.translate((0,0,head_z-10))
    positive_hose = positive.solid(inside=R_IN)
    reference_hose = reference.solid(inside=R_IN)
    # Conservative installed sleeves reserve max wall thickness outside real barbs;
    # exclude only the corresponding vendor/fitting engagement from collision tests.
    sleeves = {}
    for tag, p, direction, outer in (
        ('positive-sensor', (48.2, 24.8, -93.025), (0, 1, 0), (5.4+3.175)/2),
        ('reference-sensor', (60.8, 24.8, -93.025), (0, 1, 0), (5.4+3.175)/2),
        ('positive-elbow', (-74.5, 65, head_z-17.653), (0, 0, 1), (6.0198+3.175)/2),
        ('reference-elbow', (ref_center[0]-17.653, ref_center[1], -93.025), (1, 0, 0), (6.0198+3.175)/2),
    ):
        sleeves['REF-expanded-hose-sleeve-'+tag] = cyl(outer, 10, p, direction)
    
    candidate = {
        'pressure-head-elbow-capture': head_clamp,
        'pressure-reference-elbow-capture': ref_clamp,
        'pressure-reference-ambient-baffle': baffle,
        'tpu-pressure-ceiling-split-grommet': grommet,
        'REF-Arkplas-MCX19-NY2-head-elbow': head_elbow,
        'REF-Arkplas-MCX19-NY2-reference-elbow': ref_elbow,
        'REF-Tygon-ACF00010-positive-hose': positive_hose,
        'REF-Tygon-ACF00010-reference-hose': reference_hose,
        'REF-pressure-board-solder-tail-exit-reserve': pigtail_exit,
        **clamps,
    }
    
    return {'parts':candidate,'sleeves':sleeves,'head_additions':head_additions,'head_cuts':head_cuts,'tray_additions':tray_additions,'tray_cuts':tray_cuts,'shell_additions':shell_additions,'shell_cuts':shell_cuts,'positive':positive,'reference':reference,'loop_y':loop_y,'head_center':head_center,'reference_center':ref_center}

def add_sensor_supports(tray):
    for support in original_supports():
        moved = sensor_transform(support)
        moved = moved.intersect(box(300,250,100,15,65,-64.6))
        tray = tray.fuse(moved)
    return tray


def daughterboard():
    board = box(18,1.6,12,54.5,33.05,-99.775)
    for x in (51.5,53.5,55.5,57.5):
        board = board.cut(cyl(.4,1.8,(x,32.15,-99.775),(0,1,0)))
    for x in (47.5,61.5):
        board = board.cut(cyl(1.2,1.8,(x,32.15,-103.775),(0,1,0)))
    return sensor_transform(board)


def apply_base(shell, tray, layout, include_sensor_supports=True):
    if include_sensor_supports:
        tray = add_sensor_supports(tray)
    for addition in layout['tray_additions']:
        tray = tray.fuse(addition)
    for cutter in layout['tray_cuts']:
        tray = tray.cut(cutter)
    for addition in layout['shell_additions']:
        shell = shell.fuse(addition)
    for cutter in layout['shell_cuts']:
        shell = shell.cut(cutter)
    return shell, tray


def apply_head(head_global, layout):
    for addition in layout['head_additions']:
        head_global = head_global.fuse(addition)
    for cutter in layout['head_cuts']:
        head_global = head_global.cut(cutter)
    return head_global
