"""Import a narrowly supported offline SES route into an isolated candidate.

The bundled KiCad Specctra importer returns False for this router's session.
This strict converter accepts only unchanged placements, straight wires and
600/300 um through-vias. Native KiCad DRC/parity remains the acceptance check.
It does not certify current capacity, return paths, thermal behavior or EMC.
"""
from pathlib import Path
import argparse, json, re, shutil, hashlib
import pcbnew as p
from build_rev_c_board import retain_tht_apertures

ROOT=Path(__file__).resolve().parents[1]

def sexpr(raw):
    tokens=re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',raw)
    stack=[]; result=None
    for token in tokens:
        if token=='(':
            a=[]
            if stack:stack[-1].append(a)
            stack.append(a)
        elif token==')':
            assert stack,'Unbalanced session'
            result=stack.pop()
        else:
            assert stack,'Text outside session'
            stack[-1].append(json.loads(token) if token.startswith('"') else token)
    assert not stack and result and result[0]=='session'
    return result

def item(parent,key):
    found=[x for x in parent[1:] if isinstance(x,list) and x[0]==key]
    assert len(found)==1,(key,len(found))
    return found[0]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--session',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    source=ROOT/'hardware/pcb/rev_c'
    target=args.output.resolve()
    assert target.is_relative_to((ROOT/'build').resolve()),'Candidate must remain under build/'
    target.mkdir(parents=True,exist_ok=True)
    for f in source.iterdir():
        if f.suffix in ('.kicad_pcb','.kicad_pro','.kicad_dru','.kicad_sch','.kicad_sym') or f.name in ('fp-lib-table','sym-lib-table'):
            shutil.copyfile(f,target/f.name)
    shutil.copytree(source/'WindflowCarrier.pretty',target/'WindflowCarrier.pretty',dirs_exist_ok=True)
    raw=args.session.read_text()
    data=sexpr(raw)
    assert item(data,'base_design')[1]=='windflow-rev-c'
    board=p.LoadBoard(str(target/'windflow-rev-c.kicad_pcb'))
    assert not list(board.GetTracks()),'Start from unrouted placement only'
    fps={f.GetReference():f for f in board.GetFootprints()}
    placement=item(data,'placement')
    assert item(placement,'resolution')[1:]==['um','10']
    placement_count=0
    for component in placement[1:]:
        if not isinstance(component,list) or component[0]=='resolution':continue
        assert component[0]=='component'
        for place in component[2:]:
            assert place[0]=='place'
            ref,x,y,side,angle=place[1:6]
            fp=fps[ref]
            actual=(p.ToMM(fp.GetPosition().x),p.ToMM(fp.GetPosition().y))
            assert abs(actual[0]-float(x)/10000)<.00011 and abs(actual[1]+float(y)/10000)<.00011,(ref,'Placement moved')
            assert (side=='front')==(fp.GetLayer()==p.F_Cu),(ref,'Side changed')
            # The back-side library image carries KiCad's 180-degree flip.
            expected=fp.GetOrientationDegrees()+(0 if side=='front' else 180)
            assert abs((float(angle)-expected+180)%360-180)<.0001,(ref,'Rotation changed',angle,expected)
            placement_count+=1
    routes=item(data,'routes')
    assert item(routes,'resolution')[1:]==['um','10']
    library=item(routes,'library_out')
    assert len(library)==2 and library[1][0:2]==['padstack','Via[0-3]_600:300_um']
    for shape in library[1][2:]:
        if shape[0]=='shape':assert shape[1][0]=='circle' and shape[1][2:] == ['6000','0','0']
        else:assert shape==['attach','off']
    layers={'F.Cu':p.F_Cu,'In1.Cu':p.In1_Cu,'In2.Cu':p.In2_Cu,'B.Cu':p.B_Cu}
    nets={n.GetNetname():n for n in board.GetNetInfo().NetsByNetcode().values()}
    counts={'placements':placement_count,'tracks':0,'vias':0}
    for net in item(routes,'network_out')[1:]:
        assert net[0]=='net' and net[1] in nets
        ni=nets[net[1]]
        for element in net[2:]:
            if element[0]=='wire':
                assert len(element)==2 and element[1][0]=='path'
                path=element[1];layer=layers[path[1]];width=float(path[2])/10000
                assert len(path[3:])%2==0 and .1<=width<=5
                points=[p.VECTOR2I(p.FromMM(float(path[i])/10000),p.FromMM(-float(path[i+1])/10000)) for i in range(3,len(path),2)]
                for a,b in zip(points,points[1:]):
                    assert a!=b
                    track=p.PCB_TRACK(board);track.SetStart(a);track.SetEnd(b)
                    track.SetWidth(p.FromMM(width));track.SetLayer(layer);track.SetNet(ni);board.Add(track)
                    counts['tracks']+=1
            elif element[0]=='via':
                assert len(element)==4 and element[1]=='Via[0-3]_600:300_um'
                via=p.PCB_VIA(board);via.SetPosition(p.VECTOR2I(p.FromMM(float(element[2])/10000),p.FromMM(-float(element[3])/10000)))
                via.SetWidth(p.FromMM(.6));via.SetDrill(p.FromMM(.3));via.SetViaType(p.VIATYPE_THROUGH)
                via.SetLayerPair(p.F_Cu,p.B_Cu);via.SetNet(ni);board.Add(via);counts['vias']+=1
            else:raise AssertionError(('Unsupported session element',element[0]))
    path=target/'windflow-rev-c.kicad_pcb'
    p.SaveBoard(str(path),board);retain_tht_apertures(path)
    print(json.dumps({'candidate_only':True,**counts,'source_session_sha256':hashlib.sha256(args.session.read_bytes()).hexdigest()}))

if __name__=='__main__':main()
