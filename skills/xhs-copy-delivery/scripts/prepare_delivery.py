"""Prepare portable delivery payloads without network or credentials."""
import argparse
import json
from pathlib import Path

HEADERS = ['编号','标题','正文','标签','审核状态','参考稿编号','原文标题','原文链接','改写备注','完整文案（复制用）']
KEYS = ['number','title','body','tags','status','source_code','source_title','source_url','remark']


def prepare(notes, expected, sheet_name):
    if expected <= 0 or len(notes) != expected or not sheet_name.strip():
        raise ValueError('Expected count or sheet name invalid')
    seen, rows, formulas = set(), [], []
    for i, n in enumerate(notes, 2):
        for k in ('number','title','body'):
            if not isinstance(n.get(k), str) or not n[k].strip():
                raise ValueError(f'Missing string {k}')
        if n['number'] in seen:
            raise ValueError('Duplicate note number')
        seen.add(n['number'])
        if n.get('status') not in ('待审核','已确认','待修改'):
            raise ValueError('Explicit review status required')
        if n['status'] == '已确认' and not n.get('approval_evidence', '').strip():
            raise ValueError('Confirmed notes require approval evidence')
        if any(not isinstance(n.get(k, ''), str) for k in KEYS):
            raise ValueError('All delivery fields must be strings')
        values = [n.get(k, '') for k in KEYS]
        full = n['title'] + '\n\n' + n['body'] + ('\n\n' + n['tags'] if n.get('tags') else '')
        rows.append(values + [full])
        formulas.append([{'formula': f'=B{i}&CHAR(10)&CHAR(10)&C{i}&IF(D{i}="","",CHAR(10)&CHAR(10)&D{i})'}])
    last = expected + 1
    styles = [{'range':f'A1:J{last}','font_size':13,'vertical_alignment':'top','word_wrap':'auto-wrap'}, {'range':'A1:J1','font_weight':'bold','background_color':'#173B4D','font_color':'#FFFFFF'}]
    colors = {'已确认':'#DCF3E5','待审核':'#FFF2CC','待修改':'#FCE4D6'}
    styles.extend({'range':f'E{i}','background_color':colors[n['status']]} for i,n in enumerate(notes,2))
    return {
        'delivery': {'columns':HEADERS,'data':rows},
        'sheets': {'sheets':[{'name':sheet_name,'columns':HEADERS[:9],'data':[r[:9] for r in rows],'dtypes':dict.fromkeys(HEADERS[:9],'object')}]},
        'formulas': {'header':{'range':'J1','cells':[[{'value':HEADERS[9]}]]},'range':f'J2:J{last}','cells':formulas},
        'styles': {'styles':[{'name':sheet_name,'cell_styles':styles,'row_sizes':[{'range':'1:1','type':'pixel','size':36},{'range':f'2:{last}','type':'pixel','size':330}], 'col_sizes':[{'range':c+':'+c,'type':'pixel','size':w} for c,w in zip('ABCDEFGHIJ',[60,240,400,240,90,90,240,160,230,400])]}]}
    }


if __name__ == '__main__':
    p=argparse.ArgumentParser(); p.add_argument('input'); p.add_argument('output'); p.add_argument('--expected',type=int,required=True); p.add_argument('--sheet-name',required=True); a=p.parse_args()
    result=prepare(json.loads(Path(a.input).read_text(encoding='utf-8-sig')),a.expected,a.sheet_name)
    target=Path(a.output)
    if target.exists(): raise FileExistsError('Use a new output directory')
    target.mkdir(parents=True)
    for name,data in result.items(): (target/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Prepared',a.expected,'notes; not uploaded.')
