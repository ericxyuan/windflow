"""Build/validate the E3 carrier mechanical blank using local KiCad 10.

Run from any directory with the existing CadQuery venv Python:
  .tools/venv/Scripts/python.exe tools/build_carrier_mechanical.py
Deliverables go to hardware/pcb/carrier-mechanical; disposable negative probes
go to ignored build/carrier-mechanical-validation. No assembly is regenerated.
"""
import argparse
import hashlib
import json
import math
import os
import pathlib
import subprocess
import sys
import traceback
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "hardware/pcb/carrier-mechanical"
PARAMS = OUT / "parameters.json"
RUNTIME = ROOT / ".tools/kicad-10.0.6/bin"
BOARD = OUT / "carrier-mechanical.kicad_pcb"
WORK = ROOT / "build/carrier-mechanical-validation"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def kicad_stage(params):
    import pcbnew as p

    def vec(x, y):
        return p.VECTOR2I(p.FromMM(x), p.FromMM(y))

    width, height = params["outline_mm"]
    diameter = params["hole_diameter_mm"]
    radius = params["mounting_keepout_radius_mm"]
    count = params["keepout_polygon_segments"]
    board = p.BOARD()
    board.SetCopperLayerCount(params["provisional_copper_layers"])
    board.GetDesignSettings().SetBoardThickness(p.FromMM(params["thickness_mm"]))
    # A four-layer mechanical placeholder does not establish a fabrication stackup.
    copper = p.LSET.AllCuMask(params["provisional_copper_layers"])
    corners = [(0, 0), (width, 0), (width, height), (0, height)]
    for start, end in zip(corners, corners[1:] + corners[:1]):
        shape = p.PCB_SHAPE(board)
        shape.SetShape(p.SHAPE_T_SEGMENT)
        shape.SetStart(vec(*start))
        shape.SetEnd(vec(*end))
        shape.SetWidth(p.FromMM(.05))
        shape.SetLayer(p.Edge_Cuts)
        board.Add(shape)

    library = OUT / "WindflowMechanical.pretty"
    library.mkdir(exist_ok=True)
    template = p.FOOTPRINT(board)
    template.SetFPID(p.LIB_ID("WindflowMechanical", "MountingHole_2.4mm_M2_Keepout"))
    template.SetReference("H?")
    template.SetValue("NPTH_2.4mm_R3.5_KEEP_OUT")
    template.SetAttributes(p.FP_BOARD_ONLY | p.FP_EXCLUDE_FROM_BOM | p.FP_EXCLUDE_FROM_POS_FILES)
    template.Reference().SetVisible(False)
    template.Value().SetVisible(False)
    pad = p.PAD(template)
    pad.SetAttribute(p.PAD_ATTRIB_NPTH)
    pad.SetShape(p.PAD_SHAPE_CIRCLE)
    pad.SetSize(vec(diameter, diameter))
    pad.SetDrillSize(vec(diameter, diameter))
    pad_layers = p.LSET.AllCuMask()
    pad_layers.AddLayer(p.F_Mask)
    pad_layers.AddLayer(p.B_Mask)
    pad.SetLayerSet(pad_layers)
    template.Add(pad)

    for layer in [p.F_CrtYd, p.B_CrtYd, p.F_Fab, p.B_Fab]:
        circle = p.PCB_SHAPE(template)
        circle.SetShape(p.SHAPE_T_CIRCLE)
        circle.SetStart(vec(0, 0))
        circle.SetEnd(vec(radius, 0))
        circle.SetWidth(p.FromMM(.05))
        circle.SetLayer(layer)
        template.Add(circle)

    zone = p.ZONE(template)
    zone.SetIsRuleArea(True)
    zone.SetZoneName("M2 fastener: copper and component keepout")
    zone.SetLayerSet(copper)
    zone.SetDoNotAllowTracks(True)
    zone.SetDoNotAllowVias(True)
    # NPTH holes are represented by pads, so blanket pad prohibition would
    # falsely reject each owning mounting hole. The custom rule below excludes
    # only mechanical NPTH and forbids electrical pads in these same areas.
    zone.SetDoNotAllowPads(False)
    zone.SetDoNotAllowZoneFills(True)
    zone.SetDoNotAllowFootprints(True)
    polygon = p.SHAPE_LINE_CHAIN()
    # Circumscribed polygon: minimum tangent clearance equals the stated radius.
    vertex_radius = radius / math.cos(math.pi / count)
    for index in range(count):
        angle = 2 * math.pi * index / count
        polygon.Append(vec(vertex_radius * math.cos(angle), vertex_radius * math.sin(angle)))
    polygon.SetClosed(True)
    zone.AddPolygon(polygon)
    template.Add(zone)
    # Choose the native plugin explicitly: portable runtime library guessing
    # does not necessarily register GUI plugin factories in a Python process.
    plugin = p.PCB_IO_KICAD_SEXPR()
    plugin.FootprintSave(str(library), template)
    for index, centre in enumerate(params["hole_centres_mm"], 1):
        footprint = plugin.FootprintLoad(str(library), "MountingHole_2.4mm_M2_Keepout")
        footprint.SetFPID(p.LIB_ID("WindflowMechanical", "MountingHole_2.4mm_M2_Keepout"))
        footprint.SetReference("H%d" % index)
        footprint.SetPosition(vec(*centre))
        board.Add(footprint)

    for label, y in [
        ("WINDFLOW E3 - MECHANICAL BLANK", 23),
        ("NO ELECTRICAL NETLIST / ROUTING", 28),
        ("NOT FOR FABRICATION", 33),
        ("90 x 65 x 1.6 mm; 4 x NPTH 2.4 mm", 41),
        ("R3.5 KEEP OUT - ALL COPPER + COMPONENTS", 46),
        ("22 mm TOTAL HEIGHT RESERVE FROM UNDERSIDE", 51),
    ]:
        text = p.PCB_TEXT(board)
        text.SetText(label)
        text.SetPosition(vec(width / 2, y))
        text.SetTextSize(vec(1, 1))
        text.SetTextThickness(p.FromMM(.15))
        text.SetLayer(p.Dwgs_User)
        board.Add(text)
    p.SaveBoard(str(BOARD), board)
    custom_rules = (
        '(version 1)\n'
        '(rule "No electrical pads in M2 mounting keepouts"\n'
        ' (condition "A.Type == \'Pad\' && A.Pad_Type != \'NPTH, mechanical\' && '
        'A.intersectsArea(\'M2 fastener: copper and component keepout\')")\n'
        ' (constraint disallow pad))\n'
    )
    BOARD.with_suffix('.kicad_dru').write_text(custom_rules, encoding='utf-8')
    (OUT / "fp-lib-table").write_text(
        '(fp_lib_table (version 7)\n'
        ' (lib (name "WindflowMechanical")(type "KiCad")'
        '(uri "${KIPRJMOD}/WindflowMechanical.pretty")(options "")'
        '(descr "Mechanical mounting footprint only - no electrical design"))\n)\n',
        encoding="utf-8",
    )

    reloaded = p.LoadBoard(str(BOARD))
    checks = []

    def check(name, valid, detail):
        checks.append({"name": name, "passed": bool(valid), "detail": detail})
        if not valid:
            raise AssertionError(name + ": " + str(detail))

    outlines = p.SHAPE_POLY_SET()
    check("native KiCad outline parser", reloaded.GetBoardPolygonOutlines(outlines, False), "closed Edge.Cuts contour")
    # Outline polygon is the routed edge; graphic bounding boxes include stroke.
    box = outlines.BBox()
    check("90 x 65 mm Edge.Cuts extent", (box.GetWidth(), box.GetHeight()) == (p.FromMM(width), p.FromMM(height)), [p.ToMM(box.GetWidth()), p.ToMM(box.GetHeight())])
    check("1.6 mm native board thickness", reloaded.GetDesignSettings().GetBoardThickness() == p.FromMM(params["thickness_mm"]), params["thickness_mm"])
    check("four provisional copper layers", reloaded.GetCopperLayerCount() == 4, "no stackup or routing approval")
    check("zero electrical nets", len(reloaded.GetNetsByNetcode()) == 1, "only reserved empty net 0")
    check("zero tracks/vias", len(list(reloaded.GetTracks())) == 0, 0)
    check("four mechanical hole footprints only", len(list(reloaded.GetFootprints())) == 4, 4)
    for index, centre in enumerate(params["hole_centres_mm"], 1):
        fp = reloaded.FindFootprintByReference("H%d" % index)
        pads = list(fp.Pads())
        check("H%d centre" % index, fp.GetPosition() == vec(*centre), centre)
        check("H%d nonplated drill" % index, len(pads) == 1 and pads[0].GetAttribute() == p.PAD_ATTRIB_NPTH and pads[0].GetDrillSize() == vec(diameter, diameter), diameter)
        check("H%d edge ligament" % index, min(centre[0], centre[1], width-centre[0], height-centre[1])-diameter/2 >= 1.8-1e-9, "1.8 mm nominal hole wall to board edge")
        zones = list(fp.Zones())
        z = zones[0]
        blocked = [z.GetDoNotAllowTracks(), z.GetDoNotAllowVias(), z.GetDoNotAllowZoneFills(), z.GetDoNotAllowFootprints()]
        check("H%d mounting rule area" % index, len(zones) == 1 and z.GetIsRuleArea() and all(blocked) and not z.GetDoNotAllowPads() and z.GetLayerSet().FmtHex() == copper.FmtHex(), "all copper layers; tracks/vias/pours/other footprints forbidden; companion rule forbids electrical pads and permits NPTH")
    (OUT / "native-load-validation.json").write_text(json.dumps({"kicad_version": p.GetBuildVersion(), "checks": checks}, indent=2)+"\n")

    # Deliberate, separate negative cases prove the stored keepouts are enforced.
    # They are not electrical designs and never overwrite the deliverable board.
    validation = WORK
    validation.mkdir(parents=True, exist_ok=True)
    probe = p.LoadBoard(str(BOARD))
    track = p.PCB_TRACK(probe)
    track.SetStart(vec(4.5, 3))
    track.SetEnd(vec(5.5, 3))
    track.SetWidth(p.FromMM(.25))
    track.SetLayer(p.F_Cu)
    probe.Add(track)
    copper_probe = validation / "probe-copper.kicad_pcb"
    p.SaveBoard(str(copper_probe), probe)
    copper_probe.with_suffix('.kicad_dru').write_text(custom_rules)
    probe = p.LoadBoard(str(BOARD))
    component = p.FOOTPRINT(probe)
    component.SetReference("U_PROBE")
    component.SetValue("INTENTIONAL KEEP_OUT VIOLATION")
    component.SetAttributes(p.FP_BOARD_ONLY | p.FP_EXCLUDE_FROM_BOM | p.FP_EXCLUDE_FROM_POS_FILES)
    component.Reference().SetVisible(False)
    component.Value().SetVisible(False)
    for layer in [p.F_CrtYd, p.B_CrtYd]:
        square = [(5.1, 2.6), (5.9, 2.6), (5.9, 3.4), (5.1, 3.4)]
        for a, b in zip(square, square[1:]+square[:1]):
            shape = p.PCB_SHAPE(component)
            shape.SetShape(p.SHAPE_T_SEGMENT)
            shape.SetStart(vec(*a))
            shape.SetEnd(vec(*b))
            shape.SetWidth(p.FromMM(.05))
            shape.SetLayer(layer)
            component.Add(shape)
    probe.Add(component)
    component_probe = validation / "probe-component.kicad_pcb"
    p.SaveBoard(str(component_probe), probe)
    component_probe.with_suffix('.kicad_dru').write_text(custom_rules)
    probe = p.LoadBoard(str(BOARD))
    owner = probe.FindFootprintByReference('H1')
    electrical_pad = p.PAD(owner)
    electrical_pad.SetAttribute(p.PAD_ATTRIB_SMD)
    electrical_pad.SetShape(p.PAD_SHAPE_CIRCLE)
    electrical_pad.SetSize(vec(.5,.5))
    electrical_pad.SetPosition(vec(5.5,3))
    layers = p.LSET()
    layers.AddLayer(p.F_Cu)
    electrical_pad.SetLayerSet(layers)
    owner.Add(electrical_pad)
    pad_probe = validation / 'probe-pad.kicad_pcb'
    p.SaveBoard(str(pad_probe), probe)
    pad_probe.with_suffix('.kicad_dru').write_text(custom_rules)


def run(command, name, expected=0):
    result = subprocess.run([str(arg) for arg in command], cwd=ROOT, capture_output=True, text=True)
    (OUT / (name+".log")).write_text(result.stdout+result.stderr+"\nEXIT="+str(result.returncode)+"\n", encoding="utf-8")
    if expected is not None and result.returncode != expected:
        raise RuntimeError(name+" exited "+str(result.returncode)+"; inspect "+name+".log")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--generate-kicad", action="store_true")
    args = parser.parse_args()
    params = json.loads(PARAMS.read_text(encoding="utf-8"))
    if args.generate_kicad:
        kicad_stage(params)
        return
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "validation.json").write_text(json.dumps({"status": "IN PROGRESS - NOT A VALIDATED OR ROUTED PCB"}, indent=2)+"\n")
    run([RUNTIME/"python.exe", pathlib.Path(__file__), "--generate-kicad"], "generate")
    cli = RUNTIME / "kicad-cli.exe"
    version = run([cli, "version"], "kicad-version").stdout.strip()
    run([cli, "pcb", "export", "svg", "--mode-single", "--output", OUT/"carrier-mechanical.svg", "--layers", "Edge.Cuts,F.Fab,Dwgs.User", "--fit-page-to-board", "--exclude-drawing-sheet", BOARD], "svg-export")
    run([cli, "pcb", "export", "step", "--board-only", "--force", "--output", OUT/"carrier-mechanical-kicad.step", BOARD], "step-export")
    base_result = run([cli, "pcb", "drc", "--format", "json", "--severity-all", "--exit-code-violations", "--output", OUT/"drc.json", BOARD], "drc", expected=None)
    drc = json.loads((OUT/"drc.json").read_text(encoding="utf-8"))
    probes = []
    for kind in ["copper", "component", "pad"]:
        file = WORK/("probe-"+kind+".kicad_pcb")
        report = OUT/"negative-probes"/("probe-"+kind+".json")
        report.parent.mkdir(exist_ok=True)
        result = run([cli, "pcb", "drc", "--format", "json", "--severity-all", "--exit-code-violations", "--output", report, file], "probe-"+kind, expected=None)
        errors = json.loads(report.read_text(encoding="utf-8"))
        violations = errors.get("violations", [])
        keepout = [v for v in violations if v.get("type") == "items_not_allowed"]
        if result.returncode == 0 or not keepout:
            raise AssertionError("Negative "+kind+" probe did not detect its keepout violation")
        probes.append({"kind": kind, "exit_code": result.returncode, "detected_keepout_violations": len(keepout), "passed": True})

    import cadquery as cq
    native = cq.importers.importStep(str(OUT/"carrier-mechanical-kicad.step")).val()
    box = native.BoundingBox()
    assert native.isValid() and len(native.Solids()) == 1
    width,height = params['outline_mm']
    thickness = params['thickness_mm']
    holes_area = len(params['hole_centres_mm'])*math.pi*(params['hole_diameter_mm']/2)**2
    assert abs(box.xlen-width) < .001 and abs(box.ylen-height) < .001 and 1.4 < box.zlen <= thickness+.001
    # KiCad STEP negates drawing-Y. Its board-only body omits unpopulated outer
    # copper/mask: the 1.6 mm nominal blank exports a 1.51 mm substrate here.
    # Preserve that raw file, and extrude its real drilled profile to the full
    # nominal PCB thickness for a separately named mechanical CAD envelope.
    assert abs(box.xmin) < .001 and abs(box.ymax) < .001 and abs(box.zmin) < .001
    assert abs(native.Volume()-(width*height-holes_area)*box.zlen) < .01
    bottom = min(native.Faces(), key=lambda face: face.Center().z)
    assert abs(bottom.Center().z) < .001 and len(bottom.innerWires()) == len(params['hole_centres_mm'])
    full_thickness = cq.Solid.extrudeLinear(bottom.outerWire(), bottom.innerWires(), cq.Vector(0,0,thickness))
    assert full_thickness.isValid() and len(full_thickness.Solids()) == 1
    expected_volume = (width*height-holes_area)*thickness
    assert abs(full_thickness.Volume()-expected_volume) < .01
    datum = params['cad_bottom_datum_xyz_mm']
    placed = full_thickness.rotate((0,0,0),(1,0,0),180).translate((datum[0],datum[1],datum[2]+thickness))
    placed_box = placed.BoundingBox()
    cq.exporters.export(placed, str(OUT/"carrier-mechanical-cad-datum.step"))
    solid_checks = []
    for centre in params["hole_centres_mm"]:
        x, y, z = params["cad_bottom_datum_xyz_mm"]
        cylinder = cq.Workplane("XY").center(x+centre[0], y+centre[1]).circle(params["hole_diameter_mm"]/2-.001).extrude(params["thickness_mm"]+.2).val().translate((0,0,z-.1))
        overlap = placed.intersect(cylinder).Volume()
        assert overlap < .000001
        solid_checks.append({"hole_centre_global_xy_mm": [x+centre[0], y+centre[1]], "probe_overlap_mm3": overlap})
    outputs = [BOARD, BOARD.with_suffix('.kicad_dru'), OUT/"carrier-mechanical.svg", OUT/"carrier-mechanical-kicad.step", OUT/"carrier-mechanical-cad-datum.step", OUT/"drc.json", OUT/"native-load-validation.json", OUT/'WindflowMechanical.pretty/MountingHole_2.4mm_M2_Keepout.kicad_mod']
    record = {
        "status": "MECHANICAL BLANK - NOT AN ELECTRICAL/FABRICATION RELEASE",
        "recorded_utc": datetime.now(timezone.utc).isoformat(),
        "kicad_version": version,
        "runtime": "Explicit post-validation exit avoids the local CadQuery/OCP interpreter-teardown access violation; generation, assertions and child-process checks still fail with nonzero exit.",
        "source_sha256": {"parameters.json": digest(PARAMS), "tools/build_carrier_mechanical.py": digest(pathlib.Path(__file__)), "cad/build_base.py_read_only_datum_source": digest(ROOT/"cad/build_base.py")},
        "artifact_sha256": {p.name: digest(p) for p in outputs},
        "native_load_checks": json.loads((OUT/"native-load-validation.json").read_text()),
        "cli_drc": {"exit_code": base_result.returncode, "violations": drc.get("violations", []), "unconnected_items": drc.get("unconnected_items", []), "schematic_parity_checked": False, "scope": "empty electrical board; native mechanical constraints only"},
        "negative_keepout_probes": probes,
        "step": {"single_valid_solid": True, "native_bbox_mm": [box.xmin,box.ymin,box.zmin,box.xmax,box.ymax,box.zmax], "placed_bbox_mm": [placed_box.xmin,placed_box.ymin,placed_box.zmin,placed_box.xmax,placed_box.ymax,placed_box.zmax], "native_substrate_thickness_mm": box.zlen, "mechanical_envelope_thickness_mm": thickness, "volume_mm3": placed.Volume(), "expected_volume_mm3": expected_volume, "hole_axis_probes": solid_checks, "placement": "Extrude KiCad's validated drilled profile to nominal1.6mm; rotate180degrees aboutX; translate(5,55,-104.4) so board underside datum is(5,55,-106)"},
        "limits": params["limits"]+["A clean empty-board DRC cannot validate power circuits, connectivity, EMC, thermal layout, manufacturing stackup or populated assembly.","No schematic parity/ ERC, connector placement, harness routing or electrical component fit is claimed.","Native board-only STEP omits unpopulated outer copper/mask and has1.51mm substrate height. The separately named CAD datum STEP is a1.6mm full-thickness mechanical envelope from the same drilled profile."]
    }
    (OUT/"validation.json").write_text(json.dumps(record, indent=2)+"\n")
    print(json.dumps({"board": str(BOARD.relative_to(ROOT)), "native_checks": len(record["native_load_checks"]["checks"]), "drc_exit": base_result.returncode, "drc_violations": len(record["cli_drc"]["violations"]), "keepout_probes": probes, "step_bbox_global_mm": record["step"]["placed_bbox_mm"]}, indent=2))
    if base_result.returncode != 0:
        raise RuntimeError("Mechanical DRC has findings; validation.json records them")


if __name__ == "__main__":
    # This bundled CadQuery/OCP environment crashes during interpreter teardown,
    # even after an import-only script. Exit only after all work has completed;
    # preserve actual calculation, parsing and subprocess failures as EXIT=1.
    try:
        main()
    except Exception:
        traceback.print_exc()
        sys.stdout.flush(); sys.stderr.flush()
        os._exit(1)
    sys.stdout.flush(); sys.stderr.flush()
    os._exit(0)
