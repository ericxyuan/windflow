"""Render the exact checked manufacturing split; previews are not qualification."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

import cadquery as cq
import vtk

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'cad/rev_d/print-split'
EVIDENCE = ROOT/'cad/evidence'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def actor(poly, color):
    normals = vtk.vtkPolyDataNormals()
    normals.SetInputData(poly)
    normals.SetFeatureAngle(45)
    normals.Update()
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(normals.GetOutput())
    mapper.ScalarVisibilityOff()
    result = vtk.vtkActor()
    result.SetMapper(mapper)
    result.GetProperty().SetColor(*color)
    result.GetProperty().SetAmbient(.25)
    result.GetProperty().SetDiffuse(.75)
    return result


def render(label, items, bed=False):
    renderer = vtk.vtkRenderer()
    renderer.SetBackground(.965, .97, .975)
    for poly, color, shift in items:
        item = actor(poly, color)
        item.SetPosition(*shift)
        renderer.AddActor(item)
    camera = renderer.GetActiveCamera()
    camera.SetViewUp(0, 0, 1)
    camera.ParallelProjectionOn()
    if bed:
        for i in range(4):
            x, y = (i % 2)*280, (i//2)*280
            plate = vtk.vtkPlaneSource()
            plate.SetOrigin(x, y, -.3)
            plate.SetPoint1(x+256, y, -.3)
            plate.SetPoint2(x, y+256, -.3)
            plate.Update()
            renderer.AddActor(actor(plate.GetOutput(), (.84, .87, .89)))
        camera.SetPosition(830, -550, 780)
        camera.SetFocalPoint(265, 265, 60)
        camera.SetParallelScale(485)
        subtitle = 'Four separate 256 mm plates; supports and bond process remain unqualified'
    else:
        camera.SetPosition(-360, 555, 220)
        camera.SetFocalPoint(0, 115, 0)
        camera.SetParallelScale(205)
        subtitle = 'Rear prints withdrawn 30 mm; dark forward prints retain the complete final outlet'
    for text, y, size in [
        ('Windflow Rev D - permanent manufacturing join candidate', 962, 24),
        (subtitle, 927, 18),
        ('Source-matched geometry preview only. No printed fit, adhesive strength or operating RPM approval.', 22, 16)
    ]:
        caption = vtk.vtkTextActor()
        caption.SetInput(text)
        caption.SetPosition(25, y)
        caption.GetTextProperty().SetColor(.12, .17, .23)
        caption.GetTextProperty().SetFontSize(size)
        renderer.AddActor2D(caption)
    window = vtk.vtkRenderWindow()
    window.SetOffScreenRendering(1)
    window.SetSize(1400, 1050)
    window.SetMultiSamples(4)
    window.AddRenderer(renderer)
    renderer.ResetCameraClippingRange()
    window.Render()
    capture = vtk.vtkWindowToImageFilter()
    capture.SetInput(window)
    capture.ReadFrontBufferOff()
    capture.Update()
    path = EVIDENCE/f'rev-d-print-split-{label}-2026-10-12.png'
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(str(path))
    writer.SetInputConnection(capture.GetOutputPort())
    writer.Write()
    window.Finalize()
    assert path.stat().st_size > 10000
    return {'path':str(path.relative_to(ROOT)), 'sha256':digest(path)}


def main():
    report = json.loads((BASE/'validation.json').read_text())
    assert report['result'] == 'PASS' and not report['issues']
    for name, sha in report['input_sha256'].items():
        assert digest(ROOT/name) == sha, ('Stale print candidate', name)
    exploded, plates, sources = [], [], {}
    prints = [item for item in report['parts'] if item['scope']=='separate manufacturing candidate']
    assert len(prints) == 4
    for i, item in enumerate(prints):
        step = BASE/(item['name']+'.step')
        stl = BASE/(item['name']+'-PRINT.stl')
        assert digest(step) == item['step_sha256']
        assert digest(stl) == item['mesh']['sha256']
        sources[str(step.relative_to(ROOT))] = digest(step)
        sources[str(stl.relative_to(ROOT))] = digest(stl)
        rear = '-rear-' in item['name']
        color = (.72, .78, .81) if rear else (.26, .36, .39)
        poly = cq.importers.importStep(str(step)).val().toVtkPolyData(.015, .15, True)
        exploded.append((poly, color, (0, -30 if rear else 0, 0)))
        reader = vtk.vtkSTLReader()
        reader.SetFileName(str(stl))
        reader.Update()
        poly = reader.GetOutput()
        plates.append((poly, color, ((i % 2)*280, (i//2)*280, 0)))
    EVIDENCE.mkdir(exist_ok=True)
    images = [render('exploded', exploded), render('beds', plates, bed=True)]
    record = {'result':'PASS preview generation', 'rendering_not_verification':True,
              'physical_qualification':False, 'generated_utc':datetime.now(timezone.utc).isoformat(),
              'input_sha256':{str(Path(__file__).relative_to(ROOT)):digest(Path(__file__)),
                              'cad/rev_d/print-split/validation.json':digest(BASE/'validation.json')},
              'geometry_sha256':sources, 'images':images}
    (BASE/'preview-record.json').write_text(json.dumps(record, indent=2)+'\n')
    print('PASS', len(images), 'source-matched manufacturing review images', flush=True)


if __name__ == '__main__':
    main()
