"""Download cited public vendor data with a local provenance/hash manifest."""
import urllib.request, urllib.parse, hashlib, json, zipfile, io
from datetime import date
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parents[1]
ASSETS={
 'cad/vendor/NF-A12x25_G2_Public-CAD.zip':'https://cdn.noctua.at/media/a7b1158c/NF-A12x25_G2_Public-CAD.zip?download=true',
 'cad/vendor/Pico-R3-step.zip':'https://datasheets.raspberrypi.com/pico/Pico-R3-step.zip',
 'cad/vendor/D24V22Fx.step':'https://www.pololu.com/file/0J1413/d24v22fx-step-down-voltage-regulator.step',
 'cad/vendor/SDP810.step':'https://sensirion.com/media/documents/80D8D41F/63D0F25B/Sensirion_Differential_Pressure_Sensors_SDP810_STEP_file.step',
 'hardware/datasheets/SDP800.pdf':'https://sensirion.com/media/documents/90500156/6167E43B/Sensirion_Differential_Pressure_Datasheet_SDP8xx_Digital.pdf',
 'hardware/datasheets/FS90.pdf':'https://www.pololu.com/file/0J1435/FS90-specs.pdf',
 'hardware/datasheets/D24V22Fx.pdf':'https://www.pololu.com/file/0J1031/d24v22fx-step-down-voltage-regulator-dimension-diagram.pdf',
 'hardware/datasheets/PEC11H.pdf':'https://www.bourns.com/docs/product-datasheets/pec11h.pdf',
 'hardware/datasheets/Noctua-PWM.pdf':'https://cdn.noctua.at/media/Noctua_PWM_specifications_white_paper.pdf',
 'hardware/datasheets/Pico.pdf':'https://datasheets.raspberrypi.com/pico/pico-datasheet.pdf',
 'hardware/datasheets/HUSB238.pdf':'https://cdn-learn.adafruit.com/assets/assets/000/125/150/original/husb238_datasheet_full.pdf',
 'hardware/reference/Adafruit_HUSB238.cpp':'https://raw.githubusercontent.com/adafruit/Adafruit_HUSB238/main/Adafruit_HUSB238.cpp',
 'hardware/reference/Adafruit_HUSB238.h':'https://raw.githubusercontent.com/adafruit/Adafruit_HUSB238/main/Adafruit_HUSB238.h',
 'hardware/datasheets/TPS22810.pdf':'https://www.ti.com/lit/ds/symlink/tps22810.pdf',
 'hardware/datasheets/D2F.pdf':'https://omronfs.omron.com/en_US/ecb/products/pdf/en-d2f.pdf',
 'cad/vendor/4311.step':'https://raw.githubusercontent.com/adafruit/Adafruit_CAD_Parts/main/4311%202in%20TFT%20IPS%20Display/4311%202in%20TFT%20IPS%20Display.step',
 'hardware/reference/Adafruit-4311-EYESPI.brd':'https://raw.githubusercontent.com/adafruit/Adafruit-2.0-inch-240x320-TFT-PCB/master/Adafruit%20EYESPI%202.0%20Inch%20240x320%20IPS%20TFT.brd',
 'hardware/reference/Adafruit-4311-EYESPI.sch':'https://raw.githubusercontent.com/adafruit/Adafruit-2.0-inch-240x320-TFT-PCB/master/Adafruit%20EYESPI%202.0%20Inch%20240x320%20IPS%20TFT.sch',
 'cad/vendor/ruthex-RX-M2x4.step':'https://cdn.shopify.com/s/files/1/0567/7019/9760/files/ruthex_RX-M2x4.step?v=1621264078',
 'hardware/datasheets/Ruthex-RX.pdf':'https://www.igo3d.com/mediafiles/Sonstiges/Ruthex/ruthex_Datenblatt_RX-Serie.pdf',
}
for folder in ['1426 8x NeoPixel Stick','1782 MCP9808','5807 HUSB238 Breakout']:
 ASSETS['cad/vendor/'+folder.split(' ')[0]+'.step']='https://raw.githubusercontent.com/adafruit/Adafruit_CAD_Parts/main/'+urllib.parse.quote(folder+'/'+folder+'.step')
def fetch(item):
 name,url=item
 p=ROOT/name;p.parent.mkdir(parents=True,exist_ok=True)
 try:
  if p.exists():data=p.read_bytes()
  else:
   data=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'WindflowEngineering/0.1'}),timeout=60).read()
   if name.endswith('.pdf') and not data.startswith(b'%PDF'):raise ValueError('Not PDF')
   if name.endswith('.step') and b'ISO-10303-21' not in data[:200]:raise ValueError('Not STEP')
   p.write_bytes(data)
  digest=hashlib.sha256(data).hexdigest()
  old=PREVIOUS.get(name,{})
  recorded=old.get('date') if old.get('sha256')==digest else date.today().isoformat()
  return {'path':name,'url':url,'bytes':len(data),'sha256':digest,'status':'downloaded','date':recorded or date.today().isoformat()}
 except Exception as e:return {'path':name,'url':url,'status':'failed','error':str(e)}
PREVIOUS={r['path']:r for r in json.loads((ROOT/'hardware/sources.json').read_text())} if (ROOT/'hardware/sources.json').exists() else {}
if __name__=='__main__':
 # Preserve supplementary sources added by later engineering work. Re-fetch
 # every recorded URL if its local cache is absent; do not drop manifest rows.
 assets={r['path']:r['url'] for r in PREVIOUS.values() if 'url' in r}
 assets.update(ASSETS)
 rows=list(ThreadPoolExecutor(max_workers=6).map(fetch,assets.items()))
 (ROOT/'hardware/sources.json').write_text(json.dumps(rows,indent=2))
 for r in rows:print(r['path'],r['status'],r.get('bytes',r.get('error')))
 for p in (ROOT/'cad/vendor').glob('*.zip'):
  with zipfile.ZipFile(p) as z:
   for n in z.namelist():
    if n.lower().endswith(('.step','.stp','.pdf','.txt')) and not Path(n).name.startswith('._'):
     (ROOT/'cad/vendor'/Path(n).name).write_bytes(z.read(n))
