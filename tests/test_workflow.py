import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

review=load('review','skills/xhs-benchmark-pool-screening/scripts/build_review.py')
delivery=load('delivery','skills/xhs-copy-delivery/scripts/prepare_delivery.py')


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.pool={'asof':'2026-09-17','cutoff':'2026-03-17','records':[{'id':'n1','url':'https://example.org/n1','source':'demo.xlsx','sheet':'Sheet1','row':2,'title':'<script>bad()</script>','body':'逛街后来吃鱼头泡饼。\n饼蘸汤。\n#美食','published':'2026-03-17','likes':83,'saves':None}]}
        self.review={'mode':'adaptive','decisions':[{'id':'n1','source_ref':'demo.xlsx/Sheet1/2','decision':'selected','read_status':'full','body_status':'complete','subject':'单店','dishes':['鱼头泡饼'],'structure':['逛街','菜品'],'evidence':'鱼头泡饼','reason':'吃法匹配','limits':[],'adaptation':'adaptive','rewrite_plan':'替换菜品段','family':'逛吃'}]}
        self.note={'number':'01','title':'标题','body':'第一段\n\n第二段','tags':'#美食','status':'待审核'}

    def test_report_and_escaping(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'report'; self.assertEqual(review.render(self.pool,self.review,out),1)
            page=(out/'00-对标筛选核对.html').read_text(encoding='utf-8')
            self.assertIn('&lt;script&gt;',page); self.assertNotIn('<script>bad()',page)
            self.assertIn('鱼头泡饼',page); self.assertIn('低于100',page)
            self.assertEqual(len(json.loads((out/'audit.json').read_text(encoding='utf-8'))['records']),1)
            with self.assertRaises(FileExistsError): review.render(self.pool,self.review,out)

    def test_missing_reading_and_fabricated_excerpt(self):
        for field,value in [('read_status','initial'),('body_status','truncated'),('structure',[]),('evidence','原文没有')]:
            d=copy.deepcopy(self.review); d['decisions'][0][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError): review.validate(self.pool,d)

    def test_missing_body_and_tags_only(self):
        for body in ['', '#美食[话题]# #菜品[话题]#']:
            pool=copy.deepcopy(self.pool); pool['records'][0]['body']=body
            with self.assertRaises(ValueError): review.validate(pool,self.review)

    def test_mode_dates_metrics(self):
        d=copy.deepcopy(self.review); d['mode']='strict'
        with self.assertRaises(ValueError): review.validate(self.pool,d)
        for field,value in [('likes',None),('published','2026-03-16'),('published',None)]:
            pool=copy.deepcopy(self.pool); pool['records'][0][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError): review.validate(pool,self.review)

    def test_duplicate_snapshots_and_reconsideration(self):
        pool=copy.deepcopy(self.pool); r=copy.deepcopy(pool['records'][0]); r['row']=3; pool['records'].append(r)
        d=copy.deepcopy(self.review); x=copy.deepcopy(d['decisions'][0]); x['source_ref']='demo.xlsx/Sheet1/3'; d['decisions'].append(x)
        with self.assertRaises(ValueError): review.validate(pool,d)
        self.assertEqual(len(review.validate(pool,self.review)),2)
        d=copy.deepcopy(self.review); d['decisions'][0]['reconsidered_from']='reject'
        with self.assertRaises(ValueError): review.validate(self.pool,d)

    def test_delivery_full_and_blank_tags(self):
        n=copy.deepcopy(self.note); n['number']='02'; n['tags']=''
        data=delivery.prepare([self.note,n],2,'文案')
        self.assertEqual(data['delivery']['data'][0][-1],'标题\n\n第一段\n\n第二段\n\n#美食')
        self.assertEqual(data['delivery']['data'][1][-1],'标题\n\n第一段\n\n第二段')
        self.assertIn('B3',data['formulas']['cells'][1][0]['formula'])
        self.assertEqual(data['delivery']['data'][0][0],'01')

    def test_delivery_refuses_wrong_count_duplicate_and_false_approval(self):
        with self.assertRaises(ValueError): delivery.prepare([self.note],50,'文案')
        with self.assertRaises(ValueError): delivery.prepare([self.note,self.note],2,'文案')
        n=copy.deepcopy(self.note); n['status']='已确认'
        with self.assertRaises(ValueError): delivery.prepare([n],1,'文案')
        n['approval_evidence']='用户确认编号01'; delivery.prepare([n],1,'文案')

if __name__=='__main__': unittest.main()
