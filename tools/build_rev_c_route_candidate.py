"""Reproduce a connected, minimum-fabrication-rule PCB route candidate.

This is not a power-layout or fabrication release. It preserves the current
placement, pad nets and fabrication rules, then checks native KiCad DRC/parity.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, sys, subprocess, collections
import pcbnew as p
from repair_rev_c_route_widths import placement

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'hardware/pcb/rev_c'
SESSION=SOURCE/'route-study/initial-candidate.ses'
OUT=ROOT/'build/rev-c-board/minimum-route-candidate'
EVIDENCE=SOURCE/'route-study'

# Junction edits retain every track/via incident at a given net coordinate.
# They move copper only; they never move pads or relax clearance constraints.
JUNCTIONS={
    ('GND',67147100,33753500):(67147100,33803500),
    ('GND',43573800,35394100):(43473800,35394100),
    ('GND',43573800,35537000):(43473800,35537000),
    ('AMBIENT5_SWITCHED',42726400,30374100):(42776400,30374100),
    ('AMBIENT5_SWITCHED',42726400,30670600):(42776400,30670600),
    ('AMBIENT5_SWITCHED',42812900,30287600):(42800000,30287600),
    ('UART_DISABLE',61899200,37825200):(61899200,37855200),
    ('UART_DISABLE',60826500,37825200):(60826500,37855200),
    ('UART_TO_ESC_RX',69992400,41951000):(69992400,41991000),
    ('UART_TO_ESC_RX',70351300,41951000):(70351300,41991000),
}
POWER_NETS=('PD_RAW','RAW_FUSED','EF1_IN','BUS_PROTECTED','ESC_FUSED','ESC_15V',
            'REG5_SERVO','SERVO_FUSED','SERVO5_SWITCHED','REG5_LOGIC',
            'AMBIENT5_SWITCHED','PICO_VSYS','GND')


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert OUT.resolve().is_relative_to((ROOT/'build').resolve())
    manifest=json.loads((EVIDENCE/'session-manifest.json').read_text())
    assert digest(SESSION)==manifest['sha256']
    assert digest(ROOT/manifest['source_board_path'])==manifest['source_board_sha256'],'Session no longer matches its placed board'
    run=subprocess.run([sys.executable,str(ROOT/'tools/import_rev_c_routing.py'),
                        '--session',str(SESSION),'--output',str(OUT)],capture_output=True,text=True)
    assert run.returncode==0,(run.stdout,run.stderr)
    print(run.stdout.strip(),flush=True)
    path=OUT/'windflow-rev-c.kicad_pcb';board=p.LoadBoard(str(path))
    baseline=p.LoadBoard(str(SOURCE/'windflow-rev-c.kicad_pcb'))
    assert placement(board)==placement(baseline),'Route differs from current placement or pad nets'
    minimum=json.loads((SOURCE/'windflow-rev-c.kicad_pro').read_text())['board']['design_settings']['rules']['min_track_width']
    assert minimum==.2,'Review changed fabrication rules before applying the junction edits'
    widened=0;endpoints=0;used=collections.Counter();nets=collections.defaultdict(list)
    for t in board.GetTracks():
        if not isinstance(t,p.PCB_VIA) and p.ToMM(t.GetWidth())<minimum:
            t.SetWidth(p.FromMM(minimum));widened+=1
        for end in ('Start','End'):
            q=getattr(t,'Get'+end)()
            # DSN coordinates are 0.1 um; binary float conversion can differ
            # by one nm. Match only the declared router grid, not nearby pads.
            key=(t.GetNetname(),round(q.x/100)*100,round(q.y/100)*100)
            if key in JUNCTIONS:
                getattr(t,'Set'+end)(p.VECTOR2I(*JUNCTIONS[key]));used[key]+=1;endpoints+=1
    assert set(used)==set(JUNCTIONS) and endpoints==22,('Changed route junctions',dict(used),endpoints)
    assert placement(board)==placement(baseline)
    for t in board.GetTracks():
        if not isinstance(t,p.PCB_VIA):
            assert t.GetStart()!=t.GetEnd()
            nets[t.GetNetname()].append({'width_mm':p.ToMM(t.GetWidth()),'length_mm':p.ToMM(t.GetLength()),
                                       'layer':board.GetLayerName(t.GetLayer())})
    p.SaveBoard(str(path),board)
    cli=ROOT/'.tools/kicad-10.0.6/bin/kicad-cli.exe';native_path=OUT/'drc.json'
    checked=subprocess.run([str(cli),'pcb','drc',str(path),'--format','json','--schematic-parity',
                            '--severity-all','--exit-code-violations','--output',str(native_path)],
                           capture_output=True,text=True)
    native=json.loads(native_path.read_text())
    counts={k:len(native[k]) for k in ('violations','unconnected_items','schematic_parity')}
    assert checked.returncode==0 and not any(counts.values()),(checked.returncode,counts,native['violations'])
    # The four-layer signal route contains narrow power nets. Keep these
    # explicit rather than interpreting connectivity as a current rating.
    power={n:{'minimum_track_width_mm':min(t['width_mm'] for t in nets[n]),
              'maximum_track_width_mm':max(t['width_mm'] for t in nets[n]),
              'total_track_length_mm':sum(t['length_mm'] for t in nets[n]),
              'layers':sorted({t['layer'] for t in nets[n]})}
           for n in POWER_NETS if n in nets}
    result={'result':'PASS','scope':'Minimum fabrication geometry and connectivity candidate only',
            'generated_utc':datetime.now(timezone.utc).isoformat(),'physical_qualification':False,
            'adopted_as_main_board':False,'power_layout_approved':False,'native_exit_code':checked.returncode,
            'native_counts':counts,'widened_track_count':widened,'adjusted_endpoints':endpoints,
            'current_placement_and_pad_nets_unchanged':True,'fabrication_rules_unchanged':True,
            'power_track_metrics':power,
            'input_sha256':{str(q.relative_to(ROOT)):digest(q) for q in
                (Path(__file__),ROOT/'tools/import_rev_c_routing.py',ROOT/'tools/repair_rev_c_route_widths.py',
                 SOURCE/'windflow-rev-c.kicad_pcb',SOURCE/'windflow-rev-c.kicad_pro',SOURCE/'windflow-rev-c.kicad_dru',
                 SOURCE/'windflow-rev-c.kicad_sch',SESSION,EVIDENCE/'session-manifest.json')},
            'artifact_sha256':{str(q.relative_to(ROOT)):digest(q) for q in (path,native_path)},
            'limits':['Power tracks remain only 0.2 mm in places; this route is not the 3 A power design.',
                      'Power copper, short pad necks, return paths, thermal reliefs and decoupling placement require redesign/review.',
                      'The un-routed authoritative board remains unchanged; no Gerbers or fabrication approval are produced.']}
    (EVIDENCE/'minimum-route-validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print('PASS native DRC/connectivity/parity',counts,'EXIT',checked.returncode,flush=True)
    print('Power layout remains unapproved; authoritative board unchanged',flush=True)


if __name__=='__main__': main()
