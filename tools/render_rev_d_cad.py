"""Render the source-matched installed Rev D geometry for design review.

Preview tessellation and display colors are not fit, strength or mesh tests.
The STEP/STL articles are read only. Purchased drawing envelopes stay labeled.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json
import cadquery as cq
import vtk

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'cad/rev_d'
EVIDENCE=ROOT/'cad/evidence'

def digest(path):
    value=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):value.update(block)
    return value.hexdigest()

def color(name):
    if name.startswith('REF-PD-ISO'):return (.65,.68,.70)
    if 'UNVERIFIED' in name or 'drawing-envelope' in name:return (.70,.46,.22)
    if 'rotor' in name:return (.29,.34,.40)
    if 'TPU' in name or 'thumbwheel' in name:return (.16,.19,.23)
    if 'vendor' in name:return (.14,.40,.28)
    if 'lens' in name:return (.08,.18,.22)
    if 'diffuser' in name:return (.94,.94,.91)
    if 'mechanism' in name or 'carrier' in name or 'stator' in name:return (.36,.40,.46)
    if name.startswith('REF-') and ('magnet' in name or 'shaft' in name or 'nut' in name):return (.65,.68,.70)
    return (.76,.79,.81)

def main():
    report=json.loads((OUT/'stage-validation.json').read_text())
    assert report['result']=='PASS'
    for name,sha in report['input_sha256'].items():assert digest(ROOT/name)==sha,('Stale stage',name)
    mesh=json.loads((OUT/'mesh-validation.json').read_text())
    assert mesh['result']=='PASS'
    for name,sha in mesh['input_sha256'].items():assert digest(ROOT/name)==sha,('Stale meshes',name)
    mesh_hashes={part['name']:part['sha256'] for part in mesh['parts']}
    EVIDENCE.mkdir(exist_ok=True)
    actors={};geometry={}
    for part in report['parts']:
        name=part['name']
        if name in report['excluded_alternative_and_reserves']:continue
        step=OUT/(name+'.step')
        assert digest(step)==part['sha256'],('Changed part',name)
        geometry[str(step.relative_to(ROOT))]=part['sha256']
        stl=OUT/(name+'.stl')
        if stl.exists():
            assert name in mesh_hashes and digest(stl)==mesh_hashes[name],('Unchecked preview mesh',name)
            geometry[str(stl.relative_to(ROOT))]=mesh_hashes[name]
            reader=vtk.vtkSTLReader();reader.SetFileName(str(stl));reader.Update()
            poly=reader.GetOutput()
            if poly.GetNumberOfCells()>250000:
                reduce=vtk.vtkQuadricDecimation();reduce.SetInputData(poly)
                reduce.SetTargetReduction(1-250000/poly.GetNumberOfCells());reduce.Update()
                poly=reduce.GetOutput()
        else:
            poly=cq.importers.importStep(str(step)).val().toVtkPolyData(.01,.15,True)
        normals=vtk.vtkPolyDataNormals();normals.SetInputData(poly)
        normals.SetFeatureAngle(45);normals.SplittingOn();normals.Update()
        mapper=vtk.vtkPolyDataMapper();mapper.SetInputData(normals.GetOutput());mapper.ScalarVisibilityOff()
        actor=vtk.vtkActor();actor.SetMapper(mapper)
        actor.GetProperty().SetColor(*color(name));actor.GetProperty().SetAmbient(.23)
        actor.GetProperty().SetDiffuse(.77);actor.GetProperty().SetSpecular(.12)
        actor.GetProperty().SetSpecularPower(25)
        actors[name]=actor
    outputs=[]
    views=[('front',(350,670,210),'Installed layout - screen and wheel on the front',False),
           ('rear',(345,-370,200),'Rounded inlet and fixed rear guard',False),
           ('controls-and-power',(-350,670,190),'Screen, thumbwheel and recessed side USB-C port',False),
           ('internal',(390,660,230),'Shells hidden - installed positions, no harness shown',True)]
    for label,position,subtitle,internal in views:
        renderer=vtk.vtkRenderer();renderer.SetBackground(.965,.971,.977)
        renderer.SetAmbient(.7,.7,.7)
        for name,actor in actors.items():
            if internal and (name.startswith('P2-flowing-head-') or 'bellmouth' in name or 'guard' in name or 'grille' in name):continue
            renderer.AddActor(actor)
        window=vtk.vtkRenderWindow();window.SetOffScreenRendering(1)
        window.SetSize(1400,1050);window.SetMultiSamples(4);window.AddRenderer(renderer)
        camera=renderer.GetActiveCamera();camera.SetPosition(*position)
        camera.SetFocalPoint(0,132,-5);camera.SetViewUp(0,0,1);camera.ParallelProjectionOn()
        camera.SetParallelScale(165)
        for text,y,size in [('Windflow Rev D - 150 mm development CAD',972,25),(subtitle,935,19),
                            ('Drawing envelopes in bronze; no operating RPM approved. Physical qualification remains required.',22,16)]:
            caption=vtk.vtkTextActor();caption.SetInput(text);caption.SetPosition(25,y)
            caption.GetTextProperty().SetColor(.12,.17,.23);caption.GetTextProperty().SetFontSize(size)
            renderer.AddActor2D(caption)
        window.Render()
        capture=vtk.vtkWindowToImageFilter();capture.SetInput(window);capture.ReadFrontBufferOff();capture.Update()
        path=EVIDENCE/('rev-d-installed-'+label+'-2026-10-10.png')
        writer=vtk.vtkPNGWriter();writer.SetFileName(str(path));writer.SetInputConnection(capture.GetOutputPort());writer.Write()
        window.Finalize()
        assert path.stat().st_size>10000
        outputs.append({'path':str(path.relative_to(ROOT)),'sha256':digest(path),'bytes':path.stat().st_size})
        print('RENDERED',label,flush=True)
    record={'result':'PASS preview generation','generated_utc':datetime.now(timezone.utc).isoformat(),
            'physical_qualification':False,'rendering_not_verification':True,'named_groups':len(actors),
            'source_sha256':{str(Path(__file__).relative_to(ROOT)):digest(Path(__file__)),
                             'cad/rev_d/stage-validation.json':digest(OUT/'stage-validation.json'),
                             'cad/rev_d/mesh-validation.json':digest(OUT/'mesh-validation.json')},
            'geometry_sha256':geometry,'images':outputs,
            'limits':['Preview meshes may be decimated to 250000 cells; STEP/STL files are not changed.',
                      'Drawing-envelope colors do not assert accurate purchased-component dimensions.',
                      'Images do not establish airflow, moving clearance, physical fit, printability or operation.']}
    (OUT/'preview-record.json').write_text(json.dumps(record,indent=2)+'\n')
    print('PASS',len(actors),'installed groups;',len(views),'source-matched review images',flush=True)

if __name__=='__main__':main()
