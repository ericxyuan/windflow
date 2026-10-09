"""Selected small Pico fasteners; all coordinates are assembly coordinates.

Four M1.6 cap screws leave room for the remote-harness header insulators.
The geometric models omit threads and are explicitly drawing-based references.
"""
import math
import cadquery as cq

HOLES = [(x, y) for x in (-50.2, -38.8) for y in (63., 110.)]
SCREW_MODEL = 'Accu SSCF-M1.6-10-A2'
NUT_MODEL = 'Accu HPN-M1.6-A4'
DRILL = 1.8
NUT_POCKET_AF = 3.3

def references():
    result = {}
    for index, (x, y) in enumerate(HOLES, 1):
        shank = cq.Solid.makeCylinder(.8, 10, cq.Vector(x,y,-115), cq.Vector(0,0,1))
        head = cq.Solid.makeCylinder(1.5, 1.6, cq.Vector(x,y,-105), cq.Vector(0,0,1))
        socket = (cq.Workplane('XY').polygon(6,1.5/math.cos(math.pi/6)).extrude(.8)
                  .val().translate((x,y,-104.1)))
        result['REF-Pico-M1p6x10-cap-screw-'+str(index)] = shank.fuse(head).cut(socket)
        nut = (cq.Workplane('XY').polygon(6,3.2/math.cos(math.pi/6)).extrude(1.3)
               .val().translate((x,y,-113.2)))
        result['REF-Pico-M1p6-hex-nut-'+str(index)] = nut.cut(
            cq.Solid.makeCylinder(.8, 1.5, cq.Vector(x,y,-113.3), cq.Vector(0,0,1)))
    return result
