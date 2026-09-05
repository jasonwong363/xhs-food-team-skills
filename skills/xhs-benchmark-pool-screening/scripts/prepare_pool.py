"""Read standard Xiaohongshu xlsx exports into an auditable JSON pool."""
import argparse
import calendar
import datetime as dt
import json
import re
from pathlib import Path
import openpyxl

def number(value):
    if value is None or str(value).strip() in ('', '-', '赞'):
        return None
    text = str(value).strip().replace(',', '').rstrip('+')
    factor = 10000 if text.endswith('万') else 1000 if text.lower().endswith('k') else 1
    if factor != 1:
        text = text[:-1]
    try:
        return float(text) * factor
    except ValueError:
        return None

def date_value(value):
    if isinstance(value, dt.datetime):
        return value.date().isoformat()
    if isinstance(value, dt.date):
        return value.isoformat()
    text = str(value or '')
    if re.match(r'^\d{4}[-/]\d{1,2}[-/]\d{1,2}', text):
        try:
            return dt.datetime.fromisoformat(text.replace('/', '-')).date().isoformat()
        except ValueError:
            pass
    return None

def cutoff(day):
    month = day.year * 12 + day.month - 1 - 6
    year, zero_month = divmod(month, 12)
    month = zero_month + 1
    return dt.date(year, month, min(day.day, calendar.monthrange(year, month)[1]))

def prepare(folder, asof):
    files = sorted(Path(folder).glob('*.xlsx'))
    if not files:
        raise ValueError('No xlsx input files')
    records = []
    start = cutoff(asof).isoformat()
    for path in files:
        book = openpyxl.load_workbook(path, read_only=True, data_only=True)
        for sheet in book:
            iterator = sheet.iter_rows(values_only=True)
            headers = next(iterator, ())
            if not {'笔记标题', '笔记内容', '发布时间', '点赞量'}.issubset(headers):
                raise ValueError(f'Unsupported headers: {path.name}/{sheet.title}')
            for rownum, values in enumerate(iterator, 2):
                if not any(v is not None for v in values):
                    continue
                raw = dict(zip(headers, values))
                published = date_value(raw.get('发布时间'))
                records.append(dict(source=path.name, sheet=sheet.title, row=rownum,
                    id=str(raw.get('笔记ID') or ''), url=raw.get('笔记链接'),
                    title=raw.get('笔记标题') or '', body=raw.get('笔记内容') or '',
                    author=raw.get('博主昵称'), type=raw.get('笔记类型'),
                    published=published, likes=number(raw.get('点赞量')),
                    saves=number(raw.get('收藏量')), comments=number(raw.get('评论量')),
                    shares=number(raw.get('分享量')),
                    recent=(start <= published <= asof.isoformat()) if published else None,
                    raw={k:str(v) if isinstance(v,(dt.datetime,dt.date)) else v for k,v in raw.items()}))
        book.close()
    ids = [r['id'] for r in records if r['id']]
    return dict(asof=asof.isoformat(), cutoff=start, total=len(records),
                duplicate_id_rows=len(ids)-len(set(ids)), records=records)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('folder')
    parser.add_argument('output')
    parser.add_argument('--asof', required=True)
    args = parser.parse_args()
    result = prepare(args.folder, dt.date.fromisoformat(args.asof))
    target = Path(args.output)
    if target.exists():
        raise FileExistsError('Choose a new output path')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='records'},ensure_ascii=False))
