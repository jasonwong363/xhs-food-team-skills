"""Validate human/agent reading evidence and render a portable review page."""
import argparse
import csv
import datetime as dt
import html
import json
import re
from pathlib import Path


def source_ref(record):
    return f"{record['source']}/{record['sheet']}/{record['row']}"


def validate(pool, review):
    mode = review.get('mode')
    if mode not in ('strict', 'adaptive'):
        raise ValueError('Choose strict or adaptive mode')
    raw = pool['records']
    sources = {source_ref(r): r for r in raw}
    if len(sources) != len(raw):
        raise ValueError('Duplicate source references')
    seen, decisions, selected_ids = set(), {}, set()
    for d in review['decisions']:
        key = d['source_ref']
        if key in seen or key not in sources:
            raise ValueError(f'Duplicate or unknown source: {key}')
        seen.add(key)
        r = sources[key]
        if d.get('id') != r.get('id'):
            raise ValueError(f'ID/source mismatch: {key}')
        if d.get('decision') not in ('selected', 'backup', 'observe', 'reject', 'pending'):
            raise ValueError(f'Invalid decision: {key}')
        if d.get('reconsidered_from') and not d.get('reconsideration_reason', '').strip():
            raise ValueError(f'Reconsideration needs a reason: {key}')
        if d['decision'] == 'selected':
            body = str(r.get('body') or '')
            prose = re.sub(r'#[^#\n]*(?:#|$)', '', body).strip()
            required = ('subject', 'dishes', 'structure', 'evidence', 'reason', 'rewrite_plan', 'family')
            if (d.get('read_status') != 'full' or d.get('body_status') != 'complete'
                    or not prose or any(not d.get(k) for k in required)
                    or not isinstance(d.get('limits'), list)):
                raise ValueError(f'Missing full-body evidence: {key}')
            if not isinstance(d['dishes'], list) or not isinstance(d['structure'], list):
                raise ValueError(f'Dishes/structure must be arrays: {key}')
            if not isinstance(d['evidence'], str) or d['evidence'] not in body:
                raise ValueError(f'Evidence is not an exact body excerpt: {key}')
            allowed = ('strict',) if mode == 'strict' else ('strict', 'adaptive')
            if d.get('adaptation') not in allowed:
                raise ValueError(f'Mode mismatch: {key}')
            try:
                date = dt.date.fromisoformat(r['published'])
                within = dt.date.fromisoformat(pool['cutoff']) <= date <= dt.date.fromisoformat(pool['asof'])
            except (ValueError, TypeError, KeyError):
                within = False
            if not within or r.get('likes') is None or not r.get('id') or not r.get('url'):
                raise ValueError(f'Missing date/likes/source or outside window: {key}')
            if r['id'] in selected_ids:
                raise ValueError(f'Duplicate selected ID: {r["id"]}')
            selected_ids.add(r['id'])
        decisions[key] = d
    return [dict(r, review=decisions.get(source_ref(r), {'decision': 'pending', 'read_status': 'initial'})) for r in raw]


def render(pool, review, output):
    records = validate(pool, review)
    output = Path(output)
    if output.exists():
        raise FileExistsError('Use a new output directory')
    output.mkdir(parents=True)
    selected = [r for r in records if r['review']['decision'] == 'selected']
    (output / 'audit.json').write_text(json.dumps(dict(pool, records=records, mode=review['mode']), ensure_ascii=False, indent=2), encoding='utf-8')
    columns = ['id', 'title', 'body', 'published', 'likes', 'saves', 'comments', 'shares', 'author', 'source', 'sheet', 'row', 'url', 'review']
    for filename, rows in [('selected.csv', selected), ('audit.csv', records)]:
        with (output / filename).open('w', encoding='utf-8-sig', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=columns, extrasaction='ignore')
            writer.writeheader()
            for row in rows:
                values = {k: row.get(k) for k in columns}
                values['review'] = json.dumps(row['review'], ensure_ascii=False)
                # Spreadsheet exports must not execute untrusted original text.
                values = {k: ("'" + v if isinstance(v, str) and v.lstrip().startswith(('=', '+', '-', '@')) else v) for k, v in values.items()}
                writer.writerow(values)
    esc = lambda v: html.escape(str(v if v is not None else '未知'), quote=True)
    cards = []
    for r in records:
        d = r['review']; likes = r.get('likes')
        heat = '未知' if likes is None else '1000+' if likes >= 1000 else '300—999' if likes >= 300 else '100—299' if likes >= 100 else '低于100'
        url = str(r.get('url') or '')
        link = f'<a href="{esc(url)}" rel="noopener noreferrer">原帖</a>' if url.startswith(('https://', 'http://')) else '原帖链接缺失'
        detail = '\n'.join(f'{k}：{json.dumps(d.get(k), ensure_ascii=False)}' for k in ['subject', 'dishes', 'structure', 'evidence', 'reason', 'limits', 'adaptation', 'rewrite_plan', 'family', 'reconsidered_from', 'reconsideration_reason'])
        cards.append(f'<article data-decision="{esc(d["decision"])}" data-heat="{heat}"><h2>{esc(r.get("title"))}</h2><p>{esc(r.get("author"))} · {esc(r.get("published"))} · {heat}赞 · {esc(d.get("read_status"))} · {esc(d["decision"])}</p><p>赞 {esc(likes)} / 藏 {esc(r.get("saves"))} / 评 {esc(r.get("comments"))} / 分享 {esc(r.get("shares"))}</p><p>{esc(source_ref(r))} · {link}</p><pre>{esc(detail)}</pre><details><summary>完整原文（含原标签）</summary><pre>{esc(r.get("body"))}</pre></details></article>')
    unique = len({r.get('id') or source_ref(r) for r in records})
    full = sum(r['review'].get('read_status') == 'full' for r in records)
    page = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>对标筛选核对</title><style>body{max-width:1100px;margin:30px auto;padding:20px;background:#f5f3ed;color:#233b34;font:17px/1.7 system-ui}article{background:white;border:1px solid #b4c4bb;border-radius:12px;padding:24px;margin:20px 0}pre{white-space:pre-wrap;font:inherit;overflow-wrap:anywhere}input,select{padding:12px;margin:6px;max-width:90%}h2{font-size:24px}a{color:#25614e}</style>'''
    page += f'<h1>对标筛选核对</h1><p>{len(records)}条来源 → {unique}篇独立笔记 → {len(selected)}篇入选；全文审阅记录{full}条。模式：{esc(review["mode"])}。时间窗口：{esc(pool["cutoff"])}—{esc(pool["asof"])}。</p><p>互动仅为导出快照；页面校验不等于语义质量验收。未读记录不算精读，低赞不称热门，缺失数据不记0。</p><p><a href="selected.csv">入选CSV（含全文）</a> · <a href="audit.csv">全量审计CSV</a> · <a href="audit.json">来源及分析JSON</a></p>'
    page += '<input id="q" placeholder="搜索标题、正文、作者、菜品"><select id="decision"><option value="">全部记录</option>' + ''.join(f'<option>{v}</option>' for v in ['selected','backup','observe','reject','pending']) + '</select><select id="heat"><option value="">全部热度</option>' + ''.join(f'<option>{v}</option>' for v in ['1000+','300—999','100—299','低于100','未知']) + '</select><span id="count"></span>'
    page += ''.join(cards) + '''<script>const q=document.querySelector('#q'),d=document.querySelector('#decision'),h=document.querySelector('#heat');function filter(){let n=0;document.querySelectorAll('article').forEach(a=>{a.hidden=!(a.textContent.toLowerCase().includes(q.value.toLowerCase())&&(!d.value||a.dataset.decision===d.value)&&(!h.value||a.dataset.heat===h.value));if(!a.hidden)n++});document.querySelector('#count').textContent=n+'条'}[q,d,h].forEach(e=>e.addEventListener('input',filter));filter();</script></html>'''
    (output / '00-对标筛选核对.html').write_text(page, encoding='utf-8')
    return len(selected)


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('pool'); p.add_argument('review'); p.add_argument('output'); a = p.parse_args()
    print('Selected:', render(json.loads(Path(a.pool).read_text(encoding='utf-8-sig')), json.loads(Path(a.review).read_text(encoding='utf-8-sig')), a.output))
