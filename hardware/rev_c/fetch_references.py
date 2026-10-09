"""Fetch primary Rev C references; keep vendor payloads local and hash their provenance."""
from pathlib import Path
import hashlib
import json
import urllib.request
import re

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'references'
OUT.mkdir(exist_ok=True)
ASSETS = {
    'Pacer-V4-Juicy-product.html': 'https://www.ligpower.com/product/p2406-fpv-freestyle-motor.html',
    'Pacer-V4-Juicy-draw.png': 'https://www.ligpower.com/images/202508/Pacer-V4-Juicy-draw.png',
    'A50S-v2-3c-product.html': 'https://teamtriforceuk.com/a50s-v2/',
    'A50S-v2-3-pinout.png': 'https://cdn11.bigcommerce.com/s-4t55i5fv4j/images/stencil/original/image-manager/pinout-v2.3.png?t=1684596909',
    'A50S-manufacturer-cad-folder.html': 'https://drive.google.com/drive/folders/1Uu2ekqWRjQy-1kAd9qATjfwv0aw9FCOZ?usp=sharing',
    'tps2663.pdf': 'https://www.ti.com/lit/ds/symlink/tps2663.pdf',
    'csd19537q3.pdf': 'https://www.ti.com/lit/ds/symlink/csd19537q3.pdf',
    '61202021621.pdf': 'https://www.we-online.com/katalog/datasheet/61202021621.pdf',
    '61202023021.pdf': 'https://www.we-online.com/katalog/datasheet/61202023021.pdf',
    'HUSB238-5807-product.html': 'https://www.adafruit.com/product/5807',
    'RP2040-datasheet.pdf': 'https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf',
    'hw_a50s_v23_core.h': 'https://raw.githubusercontent.com/vedderb/bldc/master/hwconf/teamtriforceuk/a50s_v23/hw_a50s_v23_core.h',
    'vesc-commands.c': 'https://raw.githubusercontent.com/vedderb/bldc/master/comm/commands.c',
    'Adafruit_HUSB238.h': 'https://raw.githubusercontent.com/adafruit/Adafruit_HUSB238/master/Adafruit_HUSB238.h',
    '74LVC2G125_Q100.pdf': 'https://assets.nexperia.com/documents/data-sheet/74LVC2G125_Q100.pdf',
}

def fetch(name, url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Windflow-reference-fetch/1.0'})
    path = OUT / name
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            data = response.read()
        if name.endswith('.step') and not data.lstrip().startswith(b'ISO-10303-21'):
            raise ValueError('response is not a STEP model')
        path.write_bytes(data)
        return {'url': url, 'path': str(path.relative_to(ROOT)), 'bytes': len(data),
                'sha256': hashlib.sha256(data).hexdigest(), 'status': 'downloaded'}
    except Exception as exc:
        return {'url': url, 'status': 'failed', 'error': str(exc)}

manifest = {name: fetch(name, url) for name, url in ASSETS.items()}
folder = OUT / 'A50S-manufacturer-cad-folder.html'
if folder.exists():
    html = folder.read_text(encoding='utf-8')
    names = ('A50S V2.2 3D Model.step', 'A50S V2.2 With Case 3D Model.step')
    for name in names:
        match = re.search(r'data-id="([^"]+)"[^>]+data-tooltip="' + re.escape(name), html)
        if match:
            url = 'https://drive.google.com/uc?export=download&id=' + match.group(1)
            manifest[name] = fetch(name, url)
            manifest[name]['applicability'] = 'Vendor V2.2 reference only; not verified as V2.3c mechanical geometry.'

(ROOT / 'reference-download-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
for name, result in manifest.items():
    print(result['status'], name, result.get('bytes', result.get('error', '')))
