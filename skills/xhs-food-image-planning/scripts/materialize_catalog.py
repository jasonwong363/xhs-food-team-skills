#!/usr/bin/env python3
"""Copy a visually reviewed catalog; previews never modify source images."""
import argparse
import csv
import hashlib
import html
import io
import json
import shutil
from pathlib import Path
from PIL import Image, ImageOps

CATEGORIES = {'dish_closeup', 'dish_combo', 'table_spread', 'preparation', 'environment', 'storefront', 'unconfirmed'}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('plan')
    parser.add_argument('output')
    args = parser.parse_args()
    rows = json.loads(Path(args.plan).read_text(encoding='utf-8-sig'))
    output = Path(args.output).resolve()
    if output.exists():
        raise ValueError('Output exists; choose a new review directory')
    seen_ids, seen_sources = set(), set()
    for r in rows:
        source = Path(r['source']).resolve()
        folder = Path(r['folder'])
        if not r['id'] or r['id'] in {'.', '..'} or any(c in r['id'] for c in '/\\:') or r['id'] in seen_ids:
            raise ValueError('Invalid or duplicate id')
        if not r['subject'] or r['subject'] in {'.', '..'} or any(c in r['subject'] for c in '/\\:'):
            raise ValueError('Subject must be a safe single folder name')
        if folder.is_absolute() or '..' in folder.parts or not (output / folder).resolve().is_relative_to(output):
            raise ValueError('Folder must stay inside output')
        if source in seen_sources or not source.is_file():
            raise ValueError('Duplicate or missing source')
        if r['category'] not in CATEGORIES or r['decision'] not in {'优选', '备选', '不建议使用', '待核对'}:
            raise ValueError('Invalid category or decision')
        if r['cover_candidate'] and (r['category'] != 'dish_closeup' or r['decision'] != '优选'):
            raise ValueError('Cover must be a selected single-dish image')
        if not r.get('reason') or not r.get('name_status'):
            raise ValueError('Missing review evidence')
        seen_ids.add(r['id']); seen_sources.add(source)
    if not rows:
        raise ValueError('Empty catalog')
    output.mkdir(parents=True)
    preview = output / '00-分类预览'
    preview.mkdir()
    for i, r in enumerate(rows, 1):
        source = Path(r['source'])
        data = source.read_bytes()
        name = r['id'] + '-' + source.name
        dest = output / r['folder'] / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data); shutil.copystat(source, dest)
        digest = hashlib.sha256(data).hexdigest()
        assert hashlib.sha256(dest.read_bytes()).hexdigest() == digest
        r['sha256'] = digest
        r['copied_to'] = str(dest.relative_to(output))
        with Image.open(io.BytesIO(data)) as im:
            im.draft('RGB', (400, 400))
            thumb = ImageOps.exif_transpose(im).convert('RGB')
            thumb.thumbnail((240, 300))
            thumb.save(preview / (r['id'] + '.jpg'), quality=85)
        if r['cover_candidate']:
            cover = output / '00-首图候选' / r['subject'] / name
            cover.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dest, cover)
        if i % 50 == 0:
            print(f'Copied and verified {i}/{len(rows)}', flush=True)
    (output / '图片分类清单.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf8')
    fields = list(dict.fromkeys(k for r in rows for k in r))
    with (output / '图片分类清单.csv').open('w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fields); w.writeheader(); w.writerows(rows)
    e = html.escape
    page = ['<!doctype html><html lang="zh"><meta charset="utf-8"><title>图片分类核对</title><style>body{font:16px sans-serif;padding:24px;background:#f6f5f1}nav a{margin:8px;display:inline-block}section{display:flex;flex-wrap:wrap;gap:12px}article{background:white;width:240px;padding:10px}img{width:240px;height:300px;object-fit:contain}small{display:block;color:#555}h2{margin-top:40px}b{color:#945200}</style><h1>图片分类核对</h1><p>原图全部保留。先看首图候选，再按菜品核对名称；点击图片查看原尺寸。旧精选仅为来源标记。首图候选是同一原图的便利副本。</p>']
    folders = sorted(set(r['folder'] for r in rows))
    page.append('<nav><a href="#covers">首图候选</a>' + ''.join(f'<a href="#g{n}">{e(folder)}</a>' for n, folder in enumerate(folders)) + '</nav>')
    def cards(items):
        return '<section>' + ''.join(f'<article><a href="{e(Path(r["copied_to"]).as_posix())}"><img loading="lazy" src="00-分类预览/{r["id"]}.jpg"></a><strong>{r["id"]} {e(r["subject"])}</strong><small>{e(r["decision"])} · {"旧精选" if r["old_selected"] else "原精选之外"}</small><small>{e(r["name_status"])}</small><small>{e(r["reason"])}</small></article>' for r in items) + '</section>'
    page.append('<h2 id="covers">首图候选（尚待用户核对）</h2>' + cards([r for r in rows if r['cover_candidate']]))
    for n, folder in enumerate(folders):
        page.append(f'<h2 id="g{n}">{e(folder)}</h2>' + cards([r for r in rows if r['folder'] == folder]))
    (output / '00-图片核对.html').write_text('\n'.join(page) + '</html>', encoding='utf8')
    print(f'CATALOG_OK {len(rows)} source images; {sum(r["cover_candidate"] for r in rows)} cover copies', flush=True)

if __name__ == '__main__':
    main()
