"""Verify installed skill resources against the release manifest."""
import argparse
import hashlib
import json
from pathlib import Path

if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('skills_directory'); a=p.parse_args()
    manifest=json.loads((Path(__file__).resolve().parents[1]/'manifest.json').read_text(encoding='utf-8'))
    root=Path(a.skills_directory); errors=[]
    for name,digest in manifest['files'].items():
        file=root/name
        if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest()!=digest: errors.append(name)
    if errors: raise SystemExit('Missing or changed resources: '+', '.join(errors))
    print('MATCH',manifest['version'],len(manifest['files']),'resources')
