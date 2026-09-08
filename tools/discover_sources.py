"""Read public vendor download pages. No browser state or credentials are used."""
import urllib.request, urllib.parse, re, json
from concurrent.futures import ThreadPoolExecutor
SOURCES = {
 'noctua': 'https://www.noctua.at/en/products/nf-a12x25-g2-pwm/downloads',
 'pololu': 'https://www.pololu.com/product/2858/resources',
 'servo': 'https://www.pololu.com/product/3436/resources',
 'sdp': 'https://sensirion.com/de/produkte/katalog/SDP810-125Pa',
 'pico': 'https://www.raspberrypi.com/documentation/microcontrollers/pico-series.html',
 'adafruit': 'https://api.github.com/repos/adafruit/Adafruit_CAD_Parts/git/trees/main?recursive=1',
 'arduino': 'https://api.github.com/repos/arduino/arduino-cli/releases/latest',
 'husb': 'https://api.github.com/repos/adafruit/Adafruit_HUSB238/git/trees/main?recursive=1',
}
def one(item):
 name,url=item
 try:
  req=urllib.request.Request(url,headers={'User-Agent':'WindflowEngineering/0.1'})
  s=urllib.request.urlopen(req,timeout=35).read().decode('utf-8')
  if name=='adafruit':
   paths=[x['path'] for x in json.loads(s)['tree'] if any(x['path'].startswith(p) for p in ['5807 ','1426 ','1782 ']) and x['path'].lower().endswith(('.step','.stp','.md','.txt'))]
   return name,paths
  if name=='arduino':
   return name,[x['browser_download_url'] for x in json.loads(s)['assets'] if 'Windows_64bit' in x['name']]
  if name=='husb': return name,[x['path'] for x in json.loads(s)['tree'] if x['path'].endswith(('.cpp','.h'))]
  links=re.findall(r'(?:href|src)=["\']([^"\']+)["\']',s)
  return name,sorted(set(urllib.parse.urljoin(url,u.replace('&amp;','&')) for u in links if re.search(r'(step|\.stp|\.pdf|\.zip)',u,re.I)))
 except Exception as e:return name,str(e)
if __name__=='__main__':
 for key,result in ThreadPoolExecutor(max_workers=8).map(one,SOURCES.items()):
  print(json.dumps({'source':key,'links':result}))
