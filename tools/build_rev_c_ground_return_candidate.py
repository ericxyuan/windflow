"""Build a separate, incomplete wider-power routing study with short ground escapes.

Native violations, missing nets and the native nonzero exit remain explicit.
This is not the authoritative board and does not grant a current rating.
"""
from pathlib import Path
import math, json, shutil, collections, heapq, hashlib, subprocess
from datetime import datetime, timezone
import pcbnew as p
import sys
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root/'tools'))
from repair_rev_c_route_widths import placement
SOURCE=root/'hardware/pcb/rev_c'
EVIDENCE=SOURCE/'route-study'
out=root/'build/rev-c-board/ground-return-candidate';out.mkdir(exist_ok=True)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
manifest=json.loads((EVIDENCE/'power-session-manifest.json').read_text())
session=root/manifest['path']
assert digest(session)==manifest['sha256']
assert digest(root/manifest['source_board_path'])==manifest['source_board_sha256']
baseline=p.LoadBoard(str(SOURCE/'windflow-rev-c.kicad_pcb'))
assert not list(baseline.GetTracks())
seed=p.LoadBoard(str(SOURCE/'windflow-rev-c.kicad_pcb'))
zone=p.ZONE(seed);zone.SetZoneName('Dedicated In1 GND return');zone.SetLayer(p.In1_Cu)
zone.SetNet(next(n for n in seed.GetNetInfo().NetsByNetcode().values() if n.GetNetname()=='GND'))
zone.SetLocalClearance(p.FromMM(.2));zone.SetMinThickness(p.FromMM(.2));zone.SetPadConnection(p.ZONE_CONNECTION_FULL)
poly=zone.Outline();poly.NewOutline()
for x,y in [(.7,.7),(79.3,.7),(79.3,54.3),(.7,54.3)]:poly.Append(p.VECTOR2I(p.FromMM(x),p.FromMM(y)))
seed.Add(zone);seed_path=out/'ground-plane-seed.kicad_pcb';p.SaveBoard(str(seed_path),seed)
imported=subprocess.run([sys.executable,str(root/'tools/import_rev_c_routing.py'),'--session',str(session),
 '--base-board',str(seed_path),'--design-name',manifest['session_design_name'],'--output',str(out)],capture_output=True,text=True)
assert imported.returncode==0,(imported.stdout,imported.stderr)
b=p.LoadBoard(str(out/'windflow-rev-c.kicad_pcb'))
assert placement(b)==placement(baseline)
assert not any(t.GetLayer()==p.In1_Cu for t in b.GetTracks() if not isinstance(t,p.PCB_VIA)),'Return plane must not contain signal tracks'
mm=p.FromMM
layers=[p.F_Cu,p.In1_Cu,p.In2_Cu,p.B_Cu]
pads=[];refs={}
for f in b.GetFootprints():
 for q in f.Pads():pads.append(q);refs[id(q)]=f.GetReference()
obstacles={layer:[] for layer in layers}
for q in pads:
 for layer in layers:
  if q.GetLayerSet().Contains(layer):obstacles[layer].append((q.GetNetname(),q.GetEffectiveShape(layer),q))
for t in b.GetTracks():
 for layer in layers:
  if t.GetLayerSet().Contains(layer):obstacles[layer].append((t.GetNetname(),t.GetEffectiveShape(layer),t))
holes=[(3,3),(77,3),(3,52),(77,52)]
drills=[(q.GetPosition(),max(q.GetDrillSize().x,q.GetDrillSize().y)/2) for q in pads if q.GetAttribute() in [p.PAD_ATTRIB_PTH,p.PAD_ATTRIB_NPTH]]
drills.extend((t.GetPosition(),t.GetDrillValue()/2) for t in b.GetTracks() if isinstance(t,p.PCB_VIA))
clear=mm(.21)

def acceptable(shape, layer, net, via=False):
 if any(p.SHAPE.Collide(shape,p.SHAPE_CIRCLE(p.VECTOR2I(mm(x),mm(y)),mm(2.8)),0) for x,y in holes):return False
 for other,ob,item in obstacles[layer]:
  if other!=net and p.SHAPE.Collide(shape,ob,clear):return False
  if via and isinstance(item,p.PAD) and item.GetAttribute()==p.PAD_ATTRIB_SMD and p.SHAPE.Collide(shape,ob,mm(.15)):return False
 return True

records=[];failed=[]
targets=sorted([q for q in pads if q.GetNetname()=='GND' and q.GetAttribute()==p.PAD_ATTRIB_SMD],key=lambda q:(refs[id(q)],q.GetNumber()))
for q in targets:
 layer=p.B_Cu if q.GetLayerSet().Contains(p.B_Cu) else p.F_Cu
 start=q.GetPosition(); net=q.GetNetname()
 size=min(p.ToMM(q.GetSize().x),p.ToMM(q.GetSize().y));width=min(.5,max(.2,size-.05))
 selected=None
 for distance in [.65,.8,1.,1.2,1.5,1.8]:
  for angle in range(0,360,15):
   theta=math.radians(angle);end=start+p.VECTOR2I(mm(distance*math.cos(theta)),mm(distance*math.sin(theta)))
   if not (mm(.7)<end.x<mm(79.3) and mm(.7)<end.y<mm(54.3)):continue
   if any(math.hypot(end.x-at.x,end.y-at.y)<radius+mm(.15)+mm(.26) for at,radius in drills):continue
   circle=p.SHAPE_CIRCLE(end,mm(.3));segment=p.SHAPE_SEGMENT(start,end,mm(width))
   if not all(acceptable(circle,l,net,via=True) for l in layers):continue
   if not acceptable(segment,layer,net):continue
   selected=(end,distance,angle);break
  if selected:break
 if not selected:
  failed.append((refs[id(q)],q.GetNumber(),[p.ToMM(start.x),p.ToMM(start.y)]));continue
 end,distance,angle=selected
 t=p.PCB_TRACK(b);t.SetStart(start);t.SetEnd(end);t.SetWidth(mm(width));t.SetLayer(layer);t.SetNet(q.GetNet());b.Add(t)
 v=p.PCB_VIA(b);v.SetPosition(end);v.SetWidth(mm(.6));v.SetDrill(mm(.3));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(q.GetNet());b.Add(v)
 drills.append((end,mm(.15)))
 for l in layers:obstacles[l].append((net,p.SHAPE_CIRCLE(end,mm(.3)),v))
 obstacles[layer].append((net,p.SHAPE_SEGMENT(start,end,mm(width)),t))
 records.append({'ref':refs[id(q)],'pin':q.GetNumber(),'layer':b.GetLayerName(layer),'distance_mm':distance,'width_mm':width,'via_xy_mm':[p.ToMM(end.x),p.ToMM(end.y)]})
 print('GROUND',refs[id(q)],q.GetNumber(),distance,flush=True)
anchors=[q.GetPosition() for q in pads if q.GetNetname()=='GND' and q.GetAttribute()==p.PAD_ATTRIB_PTH]
anchors.extend(t.GetPosition() for t in b.GetTracks() if isinstance(t,p.PCB_VIA) and t.GetNetname()=='GND')
failed_keys={(ref,pin) for ref,pin,xy in failed};remaining=[];linked=[]
for q in targets:
 ref,pin=refs[id(q)],q.GetNumber()
 if (ref,pin) not in failed_keys:continue
 start=q.GetPosition();layer=p.B_Cu if q.GetLayerSet().Contains(p.B_Cu) else p.F_Cu
 if any(p.SHAPE.Collide(q.GetEffectiveShape(layer),p.SHAPE_CIRCLE(at,mm(.05)),0) for at in anchors):
  linked.append({'ref':ref,'pin':pin,'already_reaches_ground_via':True});continue
 selected=None
 for width in [.5,.3,.2]:
  if width>min(p.ToMM(q.GetSize().x),p.ToMM(q.GetSize().y))-.025:continue
  for end in sorted(anchors,key=lambda a:math.hypot(a.x-start.x,a.y-start.y))[:30]:
   if math.hypot(end.x-start.x,end.y-start.y)>mm(8.):continue
   paths=[[start,end],[start,p.VECTOR2I(start.x,end.y),end],[start,p.VECTOR2I(end.x,start.y),end]]
   for offset in [-1.,-.5,.5,1.,-1.5,1.5,-2.,2.]:
    paths.append([start,start+p.VECTOR2I(mm(offset),0),p.VECTOR2I(start.x+mm(offset),end.y),end])
    paths.append([start,start+p.VECTOR2I(0,mm(offset)),p.VECTOR2I(end.x,start.y+mm(offset)),end])
   for path in paths:
    path=[at for i,at in enumerate(path) if i==0 or at!=path[i-1]]
    length=sum(math.hypot(c.x-a.x,c.y-a.y) for a,c in zip(path,path[1:]))
    if width==.2 and length>mm(4. if ref.startswith(('BUF','ISO','SUP','U','R')) else 2.):continue
    if all(acceptable(p.SHAPE_SEGMENT(a,c,mm(width)),layer,'GND') for a,c in zip(path,path[1:])):
     selected=(path,width,length);break
   if selected:break
  if selected:break
 if not selected:remaining.append((ref,pin,[p.ToMM(start.x),p.ToMM(start.y)]));continue
 path,width,length=selected
 for a,c in zip(path,path[1:]):
  t=p.PCB_TRACK(b);t.SetStart(a);t.SetEnd(c);t.SetWidth(mm(width));t.SetLayer(layer);t.SetNet(q.GetNet());b.Add(t)
  obstacles[layer].append(('GND',p.SHAPE_SEGMENT(a,c,mm(width)),t))
 linked.append({'ref':ref,'pin':pin,'width_mm':width,'length_mm':p.ToMM(length),'path_xy_mm':[[p.ToMM(at.x),p.ToMM(at.y)] for at in path]})
 print('GROUND LINK',ref,pin,p.ToMM(length),flush=True)
failed=[];bent=[]
for ref,pin,xy in remaining:
 q=next(q for q in targets if refs[id(q)]==ref and q.GetNumber()==pin)
 start=q.GetPosition();layer=p.B_Cu if q.GetLayerSet().Contains(p.B_Cu) else p.F_Cu
 width=.2
 step=mm(.1);queue=[(0.,0,0)];costs={(0,0):0.};parents={};goal=None
 while queue:
  cost,ix,iy=heapq.heappop(queue)
  if cost!=costs[(ix,iy)]:continue
  at=start+p.VECTOR2I(ix*step,iy*step)
  if not (mm(.7)<at.x<mm(79.3) and mm(.7)<at.y<mm(54.3)):continue
  if cost>.0 and cost<=mm(3.):
   circle=p.SHAPE_CIRCLE(at,mm(.3))
   if not any(math.hypot(at.x-pos.x,at.y-pos.y)<radius+mm(.41) for pos,radius in drills) and all(acceptable(circle,l,'GND',via=True) for l in layers):
    goal=(ix,iy);break
  for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]:
   other=(ix+dx,iy+dy);new=cost+step*math.hypot(dx,dy)
   if abs(other[0])>30 or abs(other[1])>30 or new>mm(3.) or new>=costs.get(other,float('inf')):continue
   end=start+p.VECTOR2I(other[0]*step,other[1]*step)
   if not acceptable(p.SHAPE_SEGMENT(at,end,mm(width)),layer,'GND'):continue
   costs[other]=new;parents[other]=(ix,iy);heapq.heappush(queue,(new,*other))
 if goal is None:failed.append((ref,pin,xy));continue
 path=[goal]
 while path[-1]!=(0,0):path.append(parents[path[-1]])
 path.reverse();vertices=[start+p.VECTOR2I(ix*step,iy*step) for ix,iy in path]
 # Keep corners but merge collinear grid edges before exporting.
 reduced=[vertices[0]]
 for i in range(1,len(vertices)-1):
  a,c,e=vertices[i-1:i+2]
  if (c.x-a.x)*(e.y-c.y)!=(c.y-a.y)*(e.x-c.x):reduced.append(c)
 reduced.append(vertices[-1]);end=reduced[-1]
 for a,c in zip(reduced,reduced[1:]):
  t=p.PCB_TRACK(b);t.SetStart(a);t.SetEnd(c);t.SetWidth(mm(width));t.SetLayer(layer);t.SetNet(q.GetNet());b.Add(t)
  obstacles[layer].append(('GND',p.SHAPE_SEGMENT(a,c,mm(width)),t))
 v=p.PCB_VIA(b);v.SetPosition(end);v.SetWidth(mm(.6));v.SetDrill(mm(.3));v.SetViaType(p.VIATYPE_THROUGH);v.SetLayerPair(p.F_Cu,p.B_Cu);v.SetNet(q.GetNet());b.Add(v)
 drills.append((end,mm(.15)))
 for l in layers:obstacles[l].append(('GND',p.SHAPE_CIRCLE(end,mm(.3)),v))
 bent.append({'ref':ref,'pin':pin,'width_mm':width,'length_mm':p.ToMM(costs[goal]),'path_xy_mm':[[p.ToMM(at.x),p.ToMM(at.y)] for at in reduced]})
 print('GROUND BENT',ref,pin,p.ToMM(costs[goal]),flush=True)
for z in b.Zones():
 if not z.GetIsRuleArea():z.SetPadConnection(p.ZONE_CONNECTION_FULL)
b.BuildConnectivity();p.ZONE_FILLER(b).Fill(b.Zones())
assert placement(b)==placement(baseline)
p.SaveBoard(str(out/'windflow-rev-c.kicad_pcb'),b)
(out/'ground-escape-record.json').write_text(json.dumps({'added':records,'links':linked,'bent':bent,'failed':failed},indent=2))
print('DONE',len(records),'added',len(failed),'failed',failed,flush=True)

native_path=out/'drc.json'
checked=subprocess.run([str(root/'.tools/kicad-10.0.6/bin/kicad-cli.exe'),'pcb','drc',str(out/'windflow-rev-c.kicad_pcb'),
 '--format','json','--schematic-parity','--severity-all','--exit-code-violations','--output',str(native_path)],capture_output=True,text=True)
native=json.loads(native_path.read_text())
counts={k:len(native[k]) for k in ('violations','unconnected_items','schematic_parity')}
assert not counts['violations'] and not counts['schematic_parity'],(checked.returncode,counts,native['violations'])
assert 0<counts['unconnected_items']<123,'Review a materially changed route before updating this incomplete study'
assert checked.returncode==5,'Missing connections must remain a failing native exit, never a full DRC pass'
missing=collections.Counter(i['items'][0]['description'].split('[')[1].split(']')[0] for i in native['unconnected_items'])
inputs=[Path(__file__),root/'tools/import_rev_c_routing.py',root/'tools/repair_rev_c_route_widths.py',
 root/'tools/build_rev_c_board.py',session,EVIDENCE/'power-session-manifest.json']
inputs.extend(SOURCE.glob('*.kicad_sch'));inputs.extend(SOURCE.glob('*.kicad_pro'));inputs.extend(SOURCE.glob('*.kicad_dru'))
inputs.append(SOURCE/'windflow-rev-c.kicad_pcb');inputs.extend((SOURCE/'WindflowCarrier.pretty').glob('*.kicad_mod'))
artifacts=[out/'windflow-rev-c.kicad_pcb',out/'ground-escape-record.json',native_path]
record={'result':'INCOMPLETE','scope':'Wider-power routing development with improved return connections',
 'generated_utc':datetime.now(timezone.utc).isoformat(),'physical_qualification':False,'adopted_as_main_board':False,
 'power_layout_approved':False,'native_exit_code':checked.returncode,'native_counts':counts,'missing_by_net':dict(missing),
 'added_direct_ground_vias':len(records),'shared_ground_links':len(linked),'added_bent_ground_vias':len(bent),
 'remaining_ground_escape_pads':failed,'dedicated_return_layer':'In1.Cu','fabrication_rules_unchanged':True,
 'placement_and_pad_nets_unchanged':placement(b)==placement(baseline),
 'input_sha256':{str(q.relative_to(root)):digest(q) for q in inputs},
 'artifact_sha256':{str(q.relative_to(root)):digest(q) for q in artifacts},
 'limits':['Missing connections prevent manufacture; native exit code 5 is recorded explicitly.',
 'High-current pads, broad supply/return paths, pad-neck current allocation, decoupling loops and thermal spreading remain under review.',
 'The authoritative board and the separately connected minimum-width study remain unchanged.',
 'Neither current capacity, physical temperature/drop, EMC nor assembly is qualified.']}
(EVIDENCE/'ground-return-development.json').write_text(json.dumps(record,indent=2)+'\n')
print('INCOMPLETE native check',counts,'EXIT',checked.returncode,'missing by net',dict(missing),flush=True)
