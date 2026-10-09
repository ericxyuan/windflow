"""Download pinned routing tools locally, verify hashes, never install globally."""
from pathlib import Path
import hashlib,json,urllib.request,zipfile
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((Path(__file__).with_name('routing-dependencies.json')).read_text())
for item in manifest['dependencies']:
    if item.get('optional'):continue
    target=ROOT/item['path'];target.parent.mkdir(parents=True,exist_ok=True)
    if not target.exists():urllib.request.urlretrieve(item['url'],target)
    assert hashlib.sha256(target.read_bytes()).hexdigest()==item['sha256'],item['name']
    if item.get('extract_to'):
        directory=ROOT/item['extract_to']
        with zipfile.ZipFile(target) as archive:
            for member in archive.infolist():
                destination=(directory/member.filename).resolve()
                assert destination.is_relative_to(directory.resolve())
            archive.extractall(directory)
    print('VERIFIED',item['name'],flush=True)
