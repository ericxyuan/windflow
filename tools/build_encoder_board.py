"""Generate/check the passive PEC11H daughterboard using portable KiCad 10.0.6.

Run with .tools/kicad-10.0.6/bin/python.exe tools/build_encoder_board.py.
No carrier pullups or capacitors are duplicated. Hardware qualification remains
necessary; exported fabrication files are a prototype candidate, not a measured
encoder/assembly approval.
"""
from __future__ import annotations
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import uuid
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hardware/pcb/encoder"
RUNTIME = ROOT / ".tools/kicad-10.0.6"
CLI = RUNTIME / "bin/kicad-cli.exe"
LIB = OUT / "WindflowEncoder.pretty"
NAME = "windflow-encoder"
NS = uuid.UUID("3d8b7b01-429d-5ff8-9627-0c72b2f0db43")
ROOT_UUID = str(uuid.uuid5(NS, "schematic-root"))
WIDTH, HEIGHT, THICKNESS = 29.5, 24.0, 1.6
AXIS = (8.5, 12.0)
MOUNTS = ((27.5, 3.5), (27.5, 20.5))
PINS = {"A": (-2.5, 7.5), "C": (0, 7.5), "B": (2.5, 7.5),
        "S1": (-2.5, -7.0), "S2": (2.5, -7.0)}
ENC_NETS = {"A": "ENC_A", "C": "GND", "B": "ENC_B", "S1": "ENC_PUSH", "S2": "GND", "SH": "GND"}
CONNECTOR_NETS = {"1": "GND", "2": "ENC_A", "3": "ENC_B", "4": "ENC_PUSH"}
COMMANDS = []

def uid(name):
    return str(uuid.uuid5(NS, name))

def write(path, content):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(content, encoding="utf-8", newline="\n")

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def call(*args):
    command = [str(CLI), *map(str, args)]
    result = subprocess.run(command, cwd=OUT, text=True, capture_output=True)
    COMMANDS.append({"arguments": list(map(str, args)), "exit_code": result.returncode,
                     "stdout": result.stdout.strip(), "stderr": result.stderr.strip()})
    print(result.stdout.strip(), flush=True)
    if result.returncode:
        write(OUT / "verification-commands.json", json.dumps(COMMANDS, indent=2) + "\n")
        raise RuntimeError(f"KiCad command failed ({result.returncode}): {command}\n{result.stderr}")
    return result

def property_text(name, value, x=0, y=0, hide=False):
    return f'(property "{name}" "{value}" (at {x} {y} 0) {"(hide yes)" if hide else ""} (effects (font (size 1.0 1.0))))'

def symbol(name, reference, value, footprint, pins, body=""):
    props = property_text("Reference", reference, 0, 12.7) + property_text("Value", value, 0, -12.7)
    props += property_text("Footprint", footprint, hide=True) + property_text("Datasheet", "https://www.bourns.com/docs/product-datasheets/pec11h.pdf" if reference == "ENC" else "", hide=True)
    if not body:
        body = '(rectangle (start -7.62 10.16) (end 7.62 -10.16) (stroke (width 0.254) (type default)) (fill (type background)))'
    pin_text = "".join(f'(pin passive line (at -10.16 {y} 0) (length 2.54) (name "{label}" (effects (font (size 1 1)))) (number "{number}" (effects (font (size 1 1)))))' for number, label, y in pins)
    return f'(symbol "{name}" (pin_names (offset 0.5)) (exclude_from_sim no) (in_bom yes) (on_board yes) {props} (symbol "{name}_0_1" {body}) (symbol "{name}_1_1" {pin_text}))'

def schematic():
    enc_pins = [("A", "A", 7.62), ("C", "COMMON", 5.08), ("B", "B", 2.54), ("S1", "PUSH", 0), ("S2", "PUSH COMMON", -2.54), ("SH", "MOUNT TABS", -5.08)]
    j_pins = [(str(i), CONNECTOR_NETS[str(i)], 7.62 - 2.54 * (i - 1)) for i in range(1, 5)]
    definitions = {
        "PEC11H_4215F_S0024": symbol("PEC11H_4215F_S0024", "ENC", "PEC11H-4215F-S0024", "WindflowEncoder:PEC11H_4215F_S0024", enc_pins),
        "XH4": symbol("XH4", "J", "B4B-XH-A(LF)(SN)", "WindflowEncoder:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical", j_pins),
        "M2_Mount": symbol("M2_Mount", "H", "M2 / 2.4mm NPTH", "WindflowEncoder:MountingHole_2p4_M2", [], '(circle (center 0 0) (radius 2.54) (stroke (width 0.254) (type default)) (fill (type none)))'),
    }
    write(OUT / "WindflowEncoder.kicad_sym", '(kicad_symbol_lib (version 20250114) (generator "kicad_symbol_editor")\n' + "\n".join(definitions.values()) + '\n)\n')
    write(OUT / "sym-lib-table", '(sym_lib_table (version 7) (lib (name "WindflowEncoder") (type "KiCad") (uri "${KIPRJMOD}/WindflowEncoder.kicad_sym") (options "") (descr "Windflow passive encoder interfaces")))\n')
    embedded = []
    for name, data in definitions.items():
        embedded.append(data.replace(f'(symbol "{name}"', f'(symbol "WindflowEncoder:{name}"', 1))
    items = []
    instances = [("ENC1", "PEC11H_4215F_S0024", (60.96, 50.8), enc_pins, ENC_NETS),
                 ("J1", "XH4", (116.84, 50.8), j_pins, CONNECTOR_NETS),
                 ("H1", "M2_Mount", (60.96, 86.36), [], {}),
                 ("H2", "M2_Mount", (116.84, 86.36), [], {})]
    for ref, name, (x, y), pins, mapping in instances:
        value = "PEC11H-4215F-S0024" if ref == "ENC1" else "B4B-XH-A(LF)(SN)" if ref == "J1" else "M2 / 2.4mm NPTH"
        fp_name = "PEC11H_4215F_S0024" if ref == "ENC1" else "JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical" if ref == "J1" else "MountingHole_2p4_M2"
        properties = property_text("Reference", ref, x, y-13.97) + property_text("Value", value, x, y+13.97)
        properties += property_text("Footprint", f"WindflowEncoder:{fp_name}", x, y, hide=True)
        items.append(f'(symbol (lib_id "WindflowEncoder:{name}") (at {x} {y} 0) (unit 1) (in_bom {"no" if ref.startswith("H") else "yes"}) (on_board yes) (dnp no) (uuid "{uid(ref)}") {properties} ' + " ".join(f'(pin "{number}" (uuid "{uid(ref+number)}"))' for number, _, _ in pins) + f' (instances (project "{NAME}" (path "/{ROOT_UUID}" (reference "{ref}") (unit 1)))))')
        for number, _, py in pins:
            yy = round(y-py, 5)
            end = round(x-10.16, 5)
            start = round(x-15.24, 5)
            items.append(f'(wire (pts (xy {start} {yy}) (xy {end} {yy})) (stroke (width 0) (type default)) (uuid "{uid(ref+number+"wire")}"))')
            items.append(f'(label "{mapping[number]}" (at {start} {yy} 0) (effects (font (size 1.0 1.0)) (justify left bottom)) (uuid "{uid(ref+number+"label")}"))')
    notes = ["Passive encoder daughterboard / 3.3V dry contacts", "J1: 1 GND / 2 A (GP0) / 3 B (GP1) / 4 PUSH (GP2)",
             "10k pullups R1-R3 and 10nF C26-C28 remain on carrier only.", "Both push common and quadrature C connect to GND.",
             "SH is a board mechanical tab alias; do not use it instead of C.", "29.5 x 24mm, 1.6mm total PCB; connector F side, encoder B side."]
    for i, note in enumerate(notes):
        items.append(f'(text "{note}" (at 35.56 {110+i*5.08} 0) (effects (font (size 1.1 1.1)) (justify left)) (uuid "{uid("note"+str(i))}"))')
    write(OUT / f"{NAME}.kicad_sch", f'(kicad_sch (version 20250114) (generator "eeschema") (uuid "{ROOT_UUID}") (paper "A4") (title_block (title "Windflow E3 encoder daughterboard") (rev "P1")) (lib_symbols {" ".join(embedded)}) {" ".join(items)} (sheet_instances (path "/" (page "1"))))\n')

def footprints():
    LIB.mkdir(parents=True, exist_ok=True)
    content = ['(footprint "PEC11H_4215F_S0024" (version 20250108) (generator "pcbnew") (layer "F.Cu")',
               '(descr "Bourns PEC11H-4xxxF-Sxxxx 08/23 drawing; front mounting-face pattern") (attr through_hole)',
               '(property "Reference" "REF**" (at 0 10 0) (layer "F.SilkS") (effects (font (size 0.8 0.8) (thickness 0.12))))',
               '(property "Value" "PEC11H-4215F-S0024" (at 0 -10 0) (layer "F.Fab") (effects (font (size 0.8 0.8) (thickness 0.12))))',
               '(fp_rect (start -5.9 -6.8) (end 5.9 6.8) (stroke (width 0.1) (type default)) (fill none) (layer "F.Fab"))',
               '(fp_rect (start -8.35 -8.15) (end 8.35 8.65) (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd"))',
               '(fp_circle (center 0 0) (end 3 0) (stroke (width 0.1) (type default)) (fill none) (layer "F.Fab"))']
    for number, (x, y) in PINS.items():
        shape = "rect" if number == "A" else "circle"
        content.append(f'(pad "{number}" thru_hole {shape} (at {x} {y}) (size 1.9 1.9) (drill 1.1) (layers "*.Cu" "*.Mask"))')
    for x in (-6.4, 6.4):
        content.append(f'(pad "SH" thru_hole oval (at {x} 0) (size 3.4 2.6) (drill oval 2.4 1.6) (layers "*.Cu" "*.Mask"))')
    content.append(')')
    write(LIB / "PEC11H_4215F_S0024.kicad_mod", "\n".join(content) + "\n")
    write(LIB / "MountingHole_2p4_M2.kicad_mod", '(footprint "MountingHole_2p4_M2" (version 20250108) (generator "pcbnew") (layer "F.Cu") (attr exclude_from_pos_files exclude_from_bom) (property "Reference" "REF**" (at 0 0 0) (layer "F.Fab") (hide yes) (effects (font (size 0.8 0.8) (thickness 0.12)))) (property "Value" "M2 / 2.4mm NPTH" (at 0 0 0) (layer "F.Fab") (hide yes) (effects (font (size 0.8 0.8) (thickness 0.12)))) (pad "" np_thru_hole circle (at 0 0) (size 2.4 2.4) (drill 2.4) (layers "*.Cu" "*.Mask")) (fp_circle (center 0 0) (end 2.2 0) (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd")))\n')
    vendor_fp = RUNTIME / "share/kicad/footprints/Connector_JST.pretty/JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical.kicad_mod"
    write(LIB / vendor_fp.name, vendor_fp.read_text(encoding="utf-8"))
    write(OUT / "fp-lib-table", '(fp_lib_table (version 7) (lib (name "WindflowEncoder") (type "KiCad") (uri "${KIPRJMOD}/WindflowEncoder.pretty") (options "") (descr "Encoder footprint from Bourns drawing; JST from KiCad 10 library")))\n')

def board():
    import pcbnew as p
    def point(xy):
        return p.VECTOR2I(p.FromMM(xy[0]), p.FromMM(xy[1]))
    b = p.BOARD()
    b.SetCopperLayerCount(2)
    settings = b.GetDesignSettings()
    settings.SetBoardThickness(p.FromMM(THICKNESS))
    settings.m_MinClearance = p.FromMM(.25)
    settings.m_TrackMinWidth = p.FromMM(.25)
    settings.m_ViasMinSize = p.FromMM(.6)
    settings.m_MinThroughDrill = p.FromMM(.3)
    settings.m_SilkClearance = p.FromMM(.15)
    nets = {}
    for name in ("GND", "ENC_A", "ENC_B", "ENC_PUSH"):
        nets[name] = p.NETINFO_ITEM(b, "/" + name)
        b.Add(nets[name])
    def footprint(ref, name, at, angle=0, back=False):
        f = p.FootprintLoad(str(LIB), name)
        assert f, name
        b.Add(f)
        f.SetReference(ref)
        f.SetFPIDAsString(f"WindflowEncoder:{name}")
        f.SetPosition(point(at))
        f.SetOrientationDegrees(angle)
        if back:
            f.Flip(f.GetPosition(), False)
        f.SetPath(p.KIID_PATH(f"/{ROOT_UUID}/{uid(ref)}"))
        f.Reference().SetVisible(False)
        f.Value().SetVisible(False)
        return f
    enc = footprint("ENC1", "PEC11H_4215F_S0024", AXIS, back=True)
    enc.SetValue("PEC11H-4215F-S0024")
    header = footprint("J1", "JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical", (21.5, 8.25), 270)
    header.SetValue("B4B-XH-A(LF)(SN)")
    for f, mapping in ((enc, ENC_NETS), (header, CONNECTOR_NETS)):
        for pad in f.Pads():
            pad.SetNet(nets[mapping[pad.GetNumber()]])
    for i, at in enumerate(MOUNTS, 1):
        footprint(f"H{i}", "MountingHole_2p4_M2", at).SetValue("M2 / 2.4mm NPTH")
    for start, end in [((0, 0), (WIDTH, 0)), ((WIDTH, 0), (WIDTH, HEIGHT)), ((WIDTH, HEIGHT), (0, HEIGHT)), ((0, HEIGHT), (0, 0))]:
        item = p.PCB_SHAPE(b)
        item.SetShape(p.SHAPE_T_SEGMENT);item.SetLayer(p.Edge_Cuts);item.SetWidth(p.FromMM(.05))
        item.SetStart(point(start));item.SetEnd(point(end));b.Add(item)
    def route(net, xy, layer):
        for a, c in zip(xy, xy[1:]):
            t = p.PCB_TRACK(b);t.SetStart(point(a));t.SetEnd(point(c));t.SetWidth(p.FromMM(.35));t.SetLayer(layer);t.SetNet(nets[net]);b.Add(t)
    route("ENC_A", [(11,19.5),(11,22.3),(18.8,22.3),(20,21.1),(20,10.75),(21.5,10.75)], p.F_Cu)
    route("ENC_B", [(6,19.5),(6,21),(15,21),(17,19),(17,13.25),(21.5,13.25)], p.B_Cu)
    route("ENC_PUSH", [(11,5),(11,2.2),(17,2.2),(18.2,3.4),(18.2,15.75)], p.F_Cu)
    via = p.PCB_VIA(b);via.SetPosition(point((18.2,15.75)));via.SetWidth(p.FromMM(.6));via.SetDrill(p.FromMM(.3));via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(nets["ENC_PUSH"]);b.Add(via)
    route("ENC_PUSH", [(18.2,15.75),(21.5,15.75)], p.B_Cu)
    route("GND", [(8.5,19.5),(8.5,10),(6,7.5),(6,5)], p.F_Cu)
    route("GND", [(2.1,12),(2.1,10),(8.5,10)], p.F_Cu)
    route("GND", [(14.9,12),(14.9,6.5),(8,6.5),(6,5)], p.F_Cu)
    route("GND", [(14.9,12),(15.4,9.5),(16.65,8.25),(21.5,8.25)], p.B_Cu)
    def keepout(name, vertices, layers, pads=True):
        z = p.ZONE(b);z.SetIsRuleArea(True);z.SetZoneName(name)
        layer_set = p.LSET()
        for layer in layers:layer_set.AddLayer(layer)
        z.SetLayerSet(layer_set)
        z.SetDoNotAllowTracks(True);z.SetDoNotAllowVias(True);z.SetDoNotAllowZoneFills(True);z.SetDoNotAllowPads(pads);z.SetDoNotAllowFootprints(False)
        poly = z.Outline();poly.NewOutline()
        for xy in vertices:poly.Append(point(xy))
        b.Add(z)
    # Notch the metal-tab pads out of the body rule area; their own plated copper
    # is intentional. Foreign component-side copper cannot occupy the body area.
    keepout("Encoder underside / no exposed foreign copper", [(3.2,6.5),(13.8,6.5),(13.8,10.5),(13,10.5),(13,13.5),(13.8,13.5),(13.8,17.5),(3.2,17.5),(3.2,13.5),(4,13.5),(4,10.5),(3.2,10.5)], [p.B_Cu])
    for i, (x,y) in enumerate(MOUNTS, 1):
        keepout(f"M2 screw/washer copper exclusion {i}", [(x+2.2*math.cos(j*math.pi/12),y+2.2*math.sin(j*math.pi/12)) for j in range(24)], [p.F_Cu,p.B_Cu], False)
    for text, at, layer in [("ENC P1", (22,22.9), p.F_SilkS), ("P1 G A B P", (21.5,22.9), p.B_SilkS)]:
        item=p.PCB_TEXT(b);item.SetText(text);item.SetPosition(point(at));item.SetTextSize(point((.8,.8)));item.SetTextThickness(p.FromMM(.12));item.SetLayer(layer)
        if layer==p.B_SilkS:item.SetMirrored(True)
        b.Add(item)
    p.SaveBoard(str(OUT / f"{NAME}.kicad_pcb"), b)
    # Mechanical/body checks must use component-side extents, not text boxes.
    header_pads={x.GetNumber():[round(p.ToMM(x.GetPosition().x),6),round(p.ToMM(x.GetPosition().y),6)] for x in header.Pads()}
    assert header_pads == {"1":[21.5,8.25],"2":[21.5,10.75],"3":[21.5,13.25],"4":[21.5,15.75]}, header_pads
    pads=[]
    for f in b.GetFootprints():
        for pad in f.Pads():
            pos=pad.GetPosition();size=pad.GetSize()
            pads.append({"ref":f.GetReference(),"number":pad.GetNumber(),"net":pad.GetNetname(),"xy_mm":[p.ToMM(pos.x),p.ToMM(pos.y)],"size_mm":[p.ToMM(size.x),p.ToMM(size.y)],"drill_mm":[p.ToMM(pad.GetDrillSize().x),p.ToMM(pad.GetDrillSize().y)]})
    # The manufacturer's pattern is viewed toward the shaft/mounting face.
    # KiCad flips local X when this footprint moves to B.Cu. Verify the actual
    # placed pads so a future flip/rotation change cannot silently swap A/B.
    encoder_pads = {item["number"]: item["xy_mm"] for item in pads if item["ref"] == "ENC1" and item["number"] != "SH"}
    assert encoder_pads == {"A": [11.0,19.5], "C": [8.5,19.5], "B": [6.0,19.5],
                            "S1": [11.0,5.0], "S2": [6.0,5.0]}, encoder_pads
    tab_centers = sorted(item["xy_mm"] for item in pads if item["ref"] == "ENC1" and item["number"] == "SH")
    assert tab_centers == [[2.1,12.0],[14.9,12.0]], tab_centers
    tracks=[{"net":t.GetNetname(),"layer":t.GetLayerName(),"a_mm":[p.ToMM(t.GetStart().x),p.ToMM(t.GetStart().y)],"b_mm":[p.ToMM(t.GetEnd().x),p.ToMM(t.GetEnd().y)],"width_mm":p.ToMM(t.GetWidth(p.F_Cu) if isinstance(t,p.PCB_VIA) else t.GetWidth()),"via":isinstance(t,p.PCB_VIA)} for t in b.GetTracks()]
    mechanical={"board_size_mm":[WIDTH,HEIGHT,THICKNESS],"encoder_axis_xy_mm":list(AXIS),"mount_holes_xy_mm":MOUNTS,
        "proposed_cad_mapping":{"encoder_component_face_x_mm":-62.5,"connector_component_face_x_mm":-60.9,"global_y_mm":"u - 5.5","global_z_mm":"-78 - v","connector_on":"F side / toward +X","encoder_on":"B side / toward -X","kicad_step_transform":"global X=-62.5+STEP z; global Y=-5.5+STEP x; global Z=-78+STEP y; STEP y=-v"},
        "required_cad_changes":["Extend board Y minimum from 0 to -5.5; keep Ymax 24 and Z[-102,-78].","Move encoder component face from X -61.5 to -62.5; trim bracket support ends by 1mm.","Preserve M2 centers Y22, Z-81.5/-98.5.","Model F-side header toward +X, 9.8mm mated-height envelope and wire bend beyond PCB face X-60.9."],
        "nominal_terminal_stack_mm":{"rear_body_x":-63.5,"rear_pin_tip_x":-60.5,"body_to_board_gap":1.0,"board_thickness":1.6,"pin_projection_beyond_solder_face":.4},
        "physical_qualification":["Measure rear pin/tab projection and body-to-PCB seating with actual encoder; 1mm spacing is a nominal engineering choice.","Confirm A/B direction and pin1 mapping using continuity before connecting carrier.","Verify mated XH plug and cable insertion/removal/strain clearance in final assembly.","Bourns does not recommend hand soldering; qualify selective/wave process at260C+-5 for3+-1seconds."],
        "component_envelopes_global_mm": {
            "encoder_body_nominal": {"min": [-70.0,-2.9,-96.8], "max": [-63.5,8.9,-83.2], "source": "Bourns 6.5 x 11.8 x 13.6mm body; manufacturer dimensional tolerances apply"},
            "encoder_terminal_tips_nominal": {"x_mm": -60.5, "source": "3mm terminals extending from rear body X-63.5; actual seating requires measurement"},
            "header_body_nominal": {"min": [-60.9,12.6,-96.2], "max": [-53.9,18.35,-83.8], "source": "JST B4B-XH-A, 12.4 x 5.75 x 7mm rotated 270 degrees on F side"},
            "mated_header_housing_reserve": {"min": [-60.9,12.6,-96.2], "max": [-51.1,18.35,-83.8], "source": "9.8mm mated board height; includes header, not cable bend or withdrawal space"},
            "header_solder_pin_tips_nominal": {"x_mm": -64.3, "source": "3.4mm JST terminal from F face X-60.9 through 1.6mm PCB"}
        },
        "pads":pads,"tracks":tracks,"net_count":4,"footprint_count":4,"rule_area_count":3,"header_pads_xy_mm":header_pads,
        "placed_encoder_pads_xy_mm": encoder_pads, "placed_encoder_tabs_xy_mm": tab_centers}
    write(OUT / "mechanical-interface.json",json.dumps(mechanical,indent=2)+"\n")
    return mechanical

def validate_netlist():
    root=ET.parse(OUT / f"{NAME}.net.xml").getroot()
    actual={net.attrib["name"]:{(n.attrib["ref"],n.attrib["pin"]) for n in net.findall("node")} for net in root.findall("nets/net")}
    expected={"/"+name:set() for name in ("GND","ENC_A","ENC_B","ENC_PUSH")}
    for pin,net in ENC_NETS.items():expected["/"+net].add(("ENC1",pin))
    for pin,net in CONNECTOR_NETS.items():expected["/"+net].add(("J1",pin))
    assert actual==expected,(actual,expected)
    return {name:sorted(nodes) for name,nodes in actual.items()}

def validate_mechanical_step():
    """Check native STEP and create a full 1.6mm assembly datum with real drills.

    KiCad --board-only exports the dielectric substrate (1.51mm for this stack),
    omitting copper and mask. Component planes still use the total board 1.6mm.
    Keep both exports, clearly named, rather than scaling a component model.
    """
    sys.path.insert(0, str(ROOT / ".tools"))
    import cadquery as cq
    data = json.loads((OUT / "mechanical-interface.json").read_text(encoding="utf-8"))
    native = cq.importers.importStep(str(OUT / f"{NAME}-board-only.step")).val()
    native_box = native.BoundingBox()
    expected_bounds = [0, WIDTH, -HEIGHT, 0, 0, 1.51]
    actual_bounds = [native_box.xmin, native_box.xmax, native_box.ymin, native_box.ymax, native_box.zmin, native_box.zmax]
    assert all(abs(a-b) < 1e-6 for a,b in zip(actual_bounds,expected_bounds)), actual_bounds
    assert native.isValid() and len(native.Solids()) == 1
    datum = cq.Workplane("XY").box(WIDTH, HEIGHT, THICKNESS, centered=False).val().translate((0,-HEIGHT,0))
    holes = []
    area_removed = 0.0
    for pad in data["pads"]:
        u,v = pad["xy_mm"]
        dx,dy = pad["drill_mm"]
        if abs(dx-dy) < 1e-8:
            cutter = cq.Workplane("XY").center(u,-v).circle(dx/2).extrude(THICKNESS+2).val().translate((0,0,-1))
            area_removed += math.pi*(dx/2)**2
        else:
            assert dx > dy, "This footprint only uses horizontal plated slots"
            cutter = cq.Workplane("XY").center(u,-v).slot2D(dx,dy).extrude(THICKNESS+2).val().translate((0,0,-1))
            area_removed += (dx-dy)*dy+math.pi*(dy/2)**2
        datum = datum.cut(cutter)
        holes.append({"ref":pad["ref"],"pin":pad["number"],"step_xy_mm":[u,-v],
                      "drill_mm":[dx,dy],"global_yz_mm":[u-5.5,-78-v]})
    assert datum.isValid() and len(datum.Solids()) == 1
    expected_volume = (WIDTH*HEIGHT-area_removed)*THICKNESS
    assert abs(datum.Volume()-expected_volume) < 1e-5, (datum.Volume(), expected_volume)
    datum_path = OUT/f"{NAME}-mechanical-datum.step"
    cq.exporters.export(datum,str(datum_path))
    reimported = cq.importers.importStep(str(datum_path)).val()
    assert reimported.isValid() and len(reimported.Solids()) == 1
    box = reimported.BoundingBox()
    datum_bounds = [box.xmin,box.xmax,box.ymin,box.ymax,box.zmin,box.zmax]
    assert all(abs(a-b) < 1e-6 for a,b in zip(datum_bounds,[0,WIDTH,-HEIGHT,0,0,THICKNESS]))
    assert abs(reimported.Volume()-expected_volume) < 1e-5
    write(OUT/"mechanical-validation.json",json.dumps({
        "generator_sha256":digest(__file__),
        "native_step":{"sha256":digest(OUT/f"{NAME}-board-only.step"),"bounds_mm":actual_bounds,
                       "valid":True,"solid_count":1,"substrate_thickness_mm":1.51},
        "assembly_datum":{"sha256":digest(datum_path),"bounds_mm":datum_bounds,"valid":True,
                          "solid_count":1,"total_board_thickness_mm":THICKNESS,
                          "volume_mm3":reimported.Volume(),"analytical_volume_mm3":expected_volume},
        "verified_drill_count":len(holes),"holes":holes,
        "scope":"Drilled PCB datum only. Component envelopes are explicit drawing reconstructions; final enclosure insertion/collision check belongs to main CAD."
    },indent=2)+"\n")
    print("PASS native STEP origin and exact 1.6mm drilled assembly datum",flush=True)

def main():
    if not CLI.exists():raise RuntimeError("Run tools/setup_kicad.ps1 before building the board")
    OUT.mkdir(parents=True,exist_ok=True)
    source=ROOT/"hardware/datasheets/PEC11H.pdf"
    assert digest(source)=="bf7cd10e676fa2be14ace1d6dc671b1d05a77b2fc6639c701316fe4180bffdac","Manufacturer reference changed; recheck footprint"
    footprints();schematic()
    write(OUT/f"{NAME}.kicad_pro",json.dumps({"meta":{"filename":f"{NAME}.kicad_pro","version":1},"board":{"design_settings":{"rule_severities":{key:"warning" for key in ("missing_courtyard","track_not_centered_on_via","tuning_profile_track_geometries","footprint_filters_mismatch","footprint_type_mismatch")}}},"net_settings":{"classes":[{"name":"Default","clearance":.25,"track_width":.35,"via_diameter":.6,"via_drill":.3,"pcb_color":"rgba(0, 0, 0, 0.000)"}],"meta":{"version":4}}},indent=2)+"\n")
    write(OUT/f"{NAME}.kicad_dru",'(version 1)\n(rule "Prototype copper clearance" (constraint clearance (min 0.25mm)))\n(rule "Trace minimum" (constraint track_width (min 0.25mm)))\n(rule "Copper to board edge" (constraint edge_clearance (min 0.25mm)))\n')
    mechanical=board()
    sch=OUT/f"{NAME}.kicad_sch";pcb=OUT/f"{NAME}.kicad_pcb"
    call("sch","export","netlist","--format","kicadxml","-o",OUT/f"{NAME}.net.xml",sch)
    nodes=validate_netlist()
    call("sch","erc","--format","json","--severity-all","--exit-code-violations","-o",OUT/"erc.json",sch)
    call("pcb","drc","--format","json","--all-track-errors","--schematic-parity","--severity-all","--exit-code-violations","-o",OUT/"drc.json",pcb)
    fab=OUT/"fabrication";fab.mkdir(exist_ok=True)
    call("pcb","export","gerbers","-l","F.Cu,B.Cu,F.Mask,B.Mask,F.SilkS,B.SilkS,Edge.Cuts","-o",fab,pcb)
    call("pcb","export","drill","--format","excellon","--excellon-separate-th","--excellon-oval-format","route","--generate-map","--map-format","svg","--generate-report","--report-path",fab/"drill-report.txt","-o",fab,pcb)
    call("pcb","export","step","--board-only","--force","-o",OUT/f"{NAME}-board-only.step",pcb)
    geometry_command = [str(ROOT/".tools/venv/Scripts/python.exe"),str(Path(__file__).resolve()),"--mechanical-check"]
    geometry_result = subprocess.run(geometry_command,cwd=ROOT,text=True,capture_output=True)
    COMMANDS.append({"arguments":geometry_command,"exit_code":geometry_result.returncode,
                     "stdout":geometry_result.stdout.strip(),"stderr":geometry_result.stderr.strip()})
    print(geometry_result.stdout.strip(),flush=True)
    if geometry_result.returncode:
        raise RuntimeError(f"Mechanical STEP verification failed: {geometry_result.stderr}")
    call("pcb","export","svg","--mode-single","--fit-page-to-board","--exclude-drawing-sheet","-l","F.Cu,F.SilkS,Edge.Cuts","-o",OUT/"front.svg",pcb)
    call("pcb","export","svg","--mode-single","--fit-page-to-board","--exclude-drawing-sheet","--mirror","-l","B.Cu,B.SilkS,Edge.Cuts","-o",OUT/"back.svg",pcb)
    call("sch","export","svg","--exclude-drawing-sheet","-o",OUT/"schematic-svg",sch)
    assert len(mechanical["tracks"])>=20 and len(mechanical["pads"])==13
    write(OUT/"verification-commands.json",json.dumps(COMMANDS,indent=2)+"\n")
    provenance={"generator":"tools/build_encoder_board.py","generator_sha256":digest(__file__),"kicad_version":"10.0.6","manufacturer_reference":{"url":"https://www.bourns.com/docs/product-datasheets/pec11h.pdf","sha256":digest(source),"dimension_revision":"08/23"},"connector_reference":"https://www.jst-mfg.com/product/pdf/eng/eXH.pdf","functional_nets":nodes,"carrier_rc_duplicate_count":0,"verification":{"native_erc":"all severities, exit-code-violations","native_drc":"all tracks, schematic parity, all severities, exit-code-violations","route_segments_and_vias":len(mechanical["tracks"]),"pads_including_mechanical":len(mechanical["pads"]),"manufacturing_status":"prototype candidate; exact encoder seating and assembly clearance require hardware/CAD adoption"},"files":{str(path.relative_to(OUT)).replace("\\","/"):digest(path) for path in sorted(OUT.rglob("*")) if path.is_file() and path.name!="provenance.json" and path.suffix != ".kicad_prl"}}
    write(OUT/"provenance.json",json.dumps(provenance,indent=2)+"\n")
    print("PASS native encoder schematic/netlist/ERC/DRC/fabrication generation",flush=True)

if __name__=="__main__":
    if "--mechanical-check" in sys.argv:
        # The bundled OCP process can fail during extension teardown on Windows.
        # Exit only after all geometry, reload and volume assertions passed.
        try:
            validate_mechanical_step()
        except Exception:
            import traceback
            traceback.print_exc()
            sys.stdout.flush();sys.stderr.flush();os._exit(1)
        sys.stdout.flush();sys.stderr.flush();os._exit(0)
    try:import pcbnew
    except ImportError:
        raise SystemExit(subprocess.call([str(RUNTIME/"bin/python.exe"),str(Path(__file__).resolve()),*sys.argv[1:]]))
    main()
