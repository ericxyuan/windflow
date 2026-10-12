"""Export a protected working copy for bounded signal rerouting, never release CAD."""
from pathlib import Path
import hashlib
import json
import pcbnew as p

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT/'hardware/pcb/rev_c/route-study'
OUT = ROOT/'build/rev-c-board/signal-recovery-candidate'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    record = json.loads((EVIDENCE/'input-copper-development.json').read_text())
    for key in ['input_sha256', 'artifact_sha256']:
        for name, sha in record[key].items():
            assert digest(ROOT/name) == sha, ('Stale input-copper evidence', name)
    source = ROOT/'build/rev-c-board/input-copper-candidate/windflow-rev-c.kicad_pcb'
    OUT.mkdir(exist_ok=True)
    board = p.LoadBoard(str(source))
    for track in board.GetTracks():
        track.SetLocked(True)
    # KiCad's DSN export saves its board and changes THT mask flags. Export only
    # an ignored copy; the accepted input-copper board must remain byte exact.
    working = OUT/'signal-recovery.kicad_pcb'
    p.SaveBoard(str(working),board)
    assert p.ExportSpecctraDSN(board,str(OUT/'signal-recovery.dsn'))
    assert digest(source) == record['artifact_sha256'][str(source.relative_to(ROOT))]
    raw = (OUT/'signal-recovery.dsn').read_text()
    assert '(type fix)' in raw and '(plane GND (polygon In1.Cu' in raw
    (OUT/'signal-recovery.rules').write_text('(rules pcb "signal-recovery"\n'
        ' (autoroute_settings (autoroute on) (postroute off)\n'
        '  (layer_rule In1.Cu (active off))\n )\n)\n')
    print('Exported protected signal-rerouting input; source copper unchanged')


if __name__ == '__main__':
    main()
