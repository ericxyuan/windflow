"""Export the separately checked Rev D development assembly, preserving names."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,re
import cadquery as cq

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'cad/rev_d'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify(r):
    assert r['result']=='PASS', r['result']
    for group in ('input_sha256','geometry_sha256'):
        for n,h in r.get(group,{}).items():assert digest(ROOT/n)==h,('Stale report',n)

def verify_firmware_profile(rotor):
    path=ROOT/'firmware/WindflowRevC/validation.json'
    firmware=json.loads(path.read_text(encoding='utf-8-sig'))
    for n,h in firmware['source_sha256'].items():assert digest(ROOT/n)==h,('Stale firmware source',n)
    assert all(c['exit_code']==0 for c in firmware['commands']), 'Firmware verification failed'
    assert digest(ROOT/firmware['uf2']['path'])==firmware['uf2']['sha256'], 'Stale firmware image'
    assert firmware['default_motion_build_flag']==0 and not firmware['hardware_motion_qualified']
    config=(ROOT/'firmware/WindflowRevC/Config.h').read_text()
    article=rotor['parts'][0]
    expected=article['sha256'][article['name']+'.step']
    assert digest(OUT/(article['name']+'.step'))==expected, 'Changed rotor article'
    diameter=json.loads((OUT/'rotor-parameters.json').read_text())['rotor_diameter_mm']
    head=json.loads((OUT/'head-parameters.json').read_text())
    assert float(re.search(r'kRotorDiameterMm=(\d+)',config)[1])==diameter==head['rotor_diameter_mm']
    assert re.search(r'kRotorArticleSha256\[\]="([0-9a-f]{64})"',config)[1]==expected
    assert firmware['rotor_article_sha256']==expected and firmware['rotor_diameter_mm']==diameter
    assert int(re.search(r'kSchema=(\d+)',config)[1])==firmware['schema']==5
    assert re.search(r'#define\s+WF_MOTION_BUILD_QUALIFIED\s+(\d+)',config)[1]=='0'
    assert firmware['approved_operating_rpm'] is None and rotor['approved_operating_rpm'] is None
    return {'rotor_diameter_mm':diameter,'rotor_article_sha256':expected,'settings_schema':firmware['schema'],
            'distributed_motion_inhibited':True,'approved_operating_rpm':None,'uf2_sha256':firmware['uf2']['sha256']}
def main():
    stage=json.loads((OUT/'stage-validation.json').read_text())
    motion=json.loads((OUT/'motion-validation.json').read_text())
    rotor=json.loads((OUT/'rotor-validation.json').read_text())
    mesh=json.loads((OUT/'mesh-validation.json').read_text())
    assert json.loads((OUT/'stage-build-state.json').read_text())['status']=='PASS'
    verify(stage);verify(motion);verify(rotor);verify(mesh)
    firmware_profile=verify_firmware_profile(rotor)
    for r in mesh['parts']:assert digest(OUT/(r['name']+'.stl'))==r['sha256'],('Stale STL',r['name'])
    excluded=set(stage['excluded_alternative_and_reserves'])
    assembly=cq.Assembly(name='Windflow-Rev-D-150mm-development')
    components=[]
    for r in stage['parts']:
        n=r['name']
        assert digest(OUT/(n+'.step'))==r['sha256'], ('Changed part',n)
        if n in excluded:continue
        s=cq.importers.importStep(str(OUT/(n+'.step'))).val()
        if 'TPU' in n:color=cq.Color(.17,.19,.22)
        elif 'rotor' in n or 'carrier' in n or 'stator' in n:color=cq.Color(.31,.35,.41)
        elif 'vendor' in n:color=cq.Color(.10,.40,.25)
        elif 'magnet' in n and n.startswith('REF-'):color=cq.Color(.6,.64,.68)
        elif 'lens' in n:color=cq.Color(.54,.78,.91,.35)
        elif 'diffuser' in n:color=cq.Color(.88,.92,.95,.45)
        elif 'mechanism' in n:color=cq.Color(.35,.39,.44)
        else:color=cq.Color(.78,.81,.85)
        assembly.add(s,name=n,color=color)
        components.append({'name':n,'solid_count':len(s.Solids()),'source_sha256':r['sha256']})
    target=OUT/'Windflow-Rev-D-150mm-integration-2026-10-09.step'
    assembly.export(str(target),exportType='STEP',mode='default')
    restored=cq.importers.importStep(str(target)).val();original=assembly.toCompound()
    delta=abs(restored.Volume()-original.Volume())
    assert restored.isValid() and delta<.1, (restored.isValid(),delta)
    assert len(restored.Solids())==sum(c['solid_count'] for c in components)
    raw=target.read_text(errors='replace')
    assert all(n in raw for n in ('P2-flowing-head-left-INTEGRAL-OUTLET','P2-150mm-rotor-installed-TEST-ONLY','REF-Adafruit-4311-IPS-vendor'))
    result={'result':'PASS','generated_utc':datetime.now(timezone.utc).isoformat(),
            'physical_qualification':False,'path':str(target.relative_to(ROOT)),'sha256':digest(target),
            'bytes':target.stat().st_size,'named_part_groups':len(components),
            'round_trip_solids':len(restored.Solids()),'round_trip_volume_difference_mm3':delta,
            'components':components,'excluded_alternative_and_reserves':sorted(excluded),
            'firmware_profile':firmware_profile,
            'input_sha256':{str(p.relative_to(ROOT)):digest(p) for p in [Path(__file__),OUT/'stage-validation.json',OUT/'motion-validation.json',OUT/'rotor-validation.json',OUT/'mesh-validation.json',
                ROOT/'firmware/WindflowRevC/validation.json',ROOT/'firmware/WindflowRevC/Config.h',ROOT/'firmware/dist/rev-c/WindflowRevC.ino.uf2']},
            'limits':['Development STEP hierarchy has no native assembly mates.',
                      'Main PCB, connected harness, pressure plumbing, interlock and all fasteners are unfinished integration.',
                      'Rotor/servo/ESC physical qualification remains required; this is not an operating or production release.']}
    (OUT/'integration-export-validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS',len(components),'groups;',len(restored.Solids()),'solids;',delta,'mm3 round trip',flush=True)
if __name__=='__main__':main()
