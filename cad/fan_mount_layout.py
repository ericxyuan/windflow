"""Shared free-state print and installed-state fan mount geometry, millimetres.

The imported fan retains its manufacturer silicone geometry. Soft pad compression
is a trial envelope, not a measured material deformation. Heat-set insertion is
handled separately by the assembly checker, leaving printable pilots unchanged.
"""
from pathlib import Path
import json
import math
import cadquery as cq

PARAMETER_PATH = Path(__file__).with_name('fan_mount_parameters.json')

def parameters():
    p = json.loads(PARAMETER_PATH.read_text())
    assert 0 < p['tube_id_mm'] < p['tube_od_mm'] < 4.3
    assert p['pad_bore_mm'] > p['tube_od_mm'] + 2*p['tube_od_id_tolerance_mm']
    compressed = p['tube_cut_length_mm'] - p['fan_depth_with_vendor_pads_mm']
    assert .5 <= compressed <= p['pad_free_thickness_mm']
    assert p['bell_screw_relief_diameter_mm'] >= p['washer_od_mm'] + .6
    return p

def cy(radius, y, length, x=0., z=0.):
    return cq.Solid.makeCylinder(radius,length,cq.Vector(x,y,z),cq.Vector(0,1,0))

def ring(od, bore, y, length, x=0., z=0.):
    return cy(od/2,y,length,x,z).cut(cy(bore/2,y-.01,length+.02,x,z))

def reliefs(bell):
    p = parameters()
    for x in (-52.5,52.5):
        for z in (-52.5,52.5):
            bell = bell.cut(cy(p['bell_screw_relief_diameter_mm']/2,-2.5,2.6,x,z))
    return bell

def free_pad():
    p = parameters()
    return ring(p['pad_od_mm'],p['pad_bore_mm'],27,p['pad_free_thickness_mm'])

def tube_reference():
    p = parameters()
    return ring(p['tube_od_mm'],p['tube_id_mm'],0,p['tube_cut_length_mm'])

def installed_parts(head_z):
    p = parameters()
    seat = p['fan_mount_seat_y_mm']
    rear = seat-p['tube_cut_length_mm']
    compressed = p['tube_cut_length_mm']-p['fan_depth_with_vendor_pads_mm']
    parts = {}
    for index,(x,z) in enumerate(((x,z+head_z) for x in (-52.5,52.5) for z in (-52.5,52.5)),1):
        washer_y = rear-p['washer_thickness_mm']
        head_y = washer_y-p['screw_head_height_mm']
        head = cy(p['screw_head_od_mm']/2,head_y,p['screw_head_height_mm'],x,z)
        key = (cq.Workplane(cq.Plane(origin=(x,head_y-.01,z),xDir=(1,0,0),normal=(0,1,0)))
               .polygon(6,2.5/math.cos(math.pi/6)).extrude(1.31).val())
        parts['TPU-fan-compressed-pad-'+str(index)] = ring(p['pad_od_mm'],p['pad_bore_mm'],rear+p['fan_depth_with_vendor_pads_mm'],compressed,x,z)
        parts['REF-KS8128-fan-limiter-'+str(index)] = ring(p['tube_od_mm'],p['tube_id_mm'],rear,p['tube_cut_length_mm'],x,z)
        parts['REF-ISO7089-fan-M3-washer-'+str(index)] = ring(p['washer_od_mm'],p['washer_id_mm'],washer_y,p['washer_thickness_mm'],x,z)
        parts['REF-ISO4762-fan-M3x35-'+str(index)] = cy(1.5,washer_y,p['screw_underhead_length_mm'],x,z).fuse(head.cut(key))
        parts['REF-RX-M3x5p7-fan-insert-'+str(index)] = ring(p['insert_od_envelope_mm'],3,seat,p['insert_length_mm'],x,z)
    assert all(s.isValid() and len(s.Solids())==1 for s in parts.values())
    return parts

def insert_allowances(head_z):
    p = parameters()
    return [cy(p['insert_od_envelope_mm']/2,p['fan_mount_seat_y_mm'],p['insert_length_mm'],x,z+head_z)
            for x in (-52.5,52.5) for z in (-52.5,52.5)]

def fan_rear_shift_mm():
    p = parameters()
    return p['fan_mount_seat_y_mm']-p['tube_cut_length_mm']
