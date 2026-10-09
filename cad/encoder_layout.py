"""E3 encoder PCB P1 assembly integration from verified native KiCad datums.

The full-thickness FR4 datum follows routed pads, not an invented PCB outline.
Header/housing and terminal references are conservative drawing-based envelopes.
"""
from pathlib import Path
import json
import math
import cadquery as cq

ROOT = Path(__file__).resolve().parents[1]
PCB_DIR = ROOT/'hardware/pcb/encoder'

def board():
    s = cq.importers.importStep(str(PCB_DIR/'windflow-encoder-mechanical-datum.step')).val()
    s = s.rotate((0,0,0),(1,1,1),120).translate((-62.5,-5.5,-78))
    b = s.BoundingBox()
    assert s.isValid() and len(s.Solids())==1
    assert abs(b.xlen-1.6)<1e-6 and abs(b.ylen-29.5)<1e-6 and abs(b.zlen-24)<1e-6
    return s

def references(box,cx):
    # The mated envelope includes the header body. Export one non-overlapping
    # reserve instead of stacking two solids that occupy the same volume.
    result = {'REF-encoder-JST-XH4-mated-envelope':box(9.8,5.75,12.4,-56.0,15.475,-90)}
    interface = json.loads((PCB_DIR/'mechanical-interface.json').read_text())
    for pad in interface['pads']:
        ref,number = pad['ref'],pad['number']
        if ref not in ('ENC1','J1'):continue
        u,v = pad['xy_mm']; y,z = u-5.5,-78-v
        if ref=='J1':
            # Drawing nominal 0.64 mm square contacts. The forward mating
            # contact lies inside the already included housing reserve.
            s = box(3.4,.64,.64,-62.6,y,z)
        elif number=='SH':
            # Conservative terminal-slot reserve; actual tab seating is a
            # coupon measurement. These fit the verified 2.4 x1.6 slots.
            s = box(3.,2.,1.,-62.,y,z)
        else:
            s = cx(.4,-63.5,3.,y,z)
        name='REF-encoder-'+ref+'-'+number+'-terminal'
        if name in result:name+='-other'
        result[name]=s
    for index,z in enumerate((-81.5,-98.5),1):
        screw=cx(1.,-70.9,10.,22,z).fuse(cx(1.9,-60.9,2.,22,z))
        socket=(cq.Workplane(cq.Plane(origin=(-58.89,22,z),xDir=(0,1,0),normal=(-1,0,0)))
                .polygon(6,1.5/math.cos(math.pi/6)).extrude(1.).val())
        result['REF-encoder-M2x10-screw-'+str(index)]=screw.cut(socket)
        nut=(cq.Workplane('YZ').polygon(6,4./math.cos(math.pi/6)).extrude(1.6)
             .val().translate((-69.4,22,z))).cut(cx(1.,-69.5,1.8,22,z))
        result['REF-encoder-M2-hex-nut-'+str(index)]=nut
    return result
