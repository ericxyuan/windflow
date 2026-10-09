"""Check the new documented power arithmetic, pin allocation and local provenance."""
from pathlib import Path
import hashlib
import json
import math

ROOT=Path(__file__).resolve().parent
spec=json.loads((ROOT/'motor-esc-specification.json').read_text())
manifest=json.loads((ROOT/'reference-download-manifest.json').read_text())
checked=[]
for name,item in manifest.items():
    assert item['status']=='downloaded',(name,item)
    path=ROOT/item['path']
    assert path.exists(),path
    assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256'],name
    checked.append(name)

normal_accessories=1.25+.5+.113+.75
peak_accessories=5+.5+2.4+.75
motor_ceiling=spec['power_targets']['motor_esc_input_ceiling_w']
normal=motor_ceiling+normal_accessories/.85+.7
peak=motor_ceiling+peak_accessories/.80+.7
efuse_nominal=18000/7150
efuse_low=efuse_nominal*.90/1.01
efuse_high=efuse_nominal*1.10/.99
assert peak<45
assert peak/14<efuse_low
assert efuse_high<3
assert math.isclose(spec['power_targets']['system_input_efuse_nominal_a'],efuse_nominal,rel_tol=1e-9)
assert 3000*spec['motor']['pole_pairs']==spec['power_targets']['erpm_trial_ceiling']
assert len(set(spec['pin_changes_from_E3'].values()))==len(spec['pin_changes_from_E3'])
assert spec['pin_changes_from_E3']['uart0_tx']==12 and spec['pin_changes_from_E3']['uart0_rx']==13
assert spec['power_targets']['all_targets_require_measured_commissioning']
assert not spec['motion_qualified']
assert 'CURRENT_3_0_A = 0b1010' in (ROOT/'references/Adafruit_HUSB238.h').read_text()
report={
    'result':'PASS: architecture arithmetic and provenance assertions',
    'physical_qualification':False,
    'reference_files_sha256_verified':len(checked),
    'input_normal_w':normal,'input_upper_w':peak,
    'input_upper_a_at_14v':peak/14,
    'input_efuse_nominal_a':efuse_nominal,
    'conservative_current_limit_low_a':efuse_low,
    'conservative_current_limit_high_a':efuse_high,
    'worst_case_budget_headroom_at_low_current_limit_a':efuse_low-peak/14,
    'current_limit_allowance':'Analytical +/-10% plus1% resistor only; actual low-limit value requires bench test.',
    'power_budget_source':'18W motor/ESC cap; 85% normal and80% upper accessory conversion allowance, not measured efficiency.',
    'spec_sha256':hashlib.sha256((ROOT/'motor-esc-specification.json').read_bytes()).hexdigest(),
    'fetcher_sha256':hashlib.sha256((ROOT/'fetch_references.py').read_bytes()).hexdigest(),
    'pins_distinct':True,
    'pd_minimum_current_status_code':10,
    'physical_tests_required':['Actual input and phase current','True RPM','Low-speed sensorless startup','ESC temperature','PD and branch inrush','UART partial-power behavior','FDM rotor retention and guarded qualification']
}
(ROOT/'architecture-validation.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS',len(checked),'reference hashes; power/current/pin/PD assertions')
