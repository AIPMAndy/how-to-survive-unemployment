import json
import re
import unittest
from pathlib import Path
import subprocess
import sys
from urllib.parse import urlparse

ROOT=Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/'data/guide.json').read_text(encoding='utf-8'))

class GuideValidation(unittest.TestCase):
    def test_stages_and_task_volume(self):
        self.assertEqual([s['id'] for s in DATA['stages']], ['before','week','month3','month6','year'])
        self.assertEqual(len(DATA['tasks']), 53)
        self.assertEqual(len(DATA['sources']), 24)
    def test_unique_ids_and_valid_refs(self):
        stage_ids={s['id'] for s in DATA['stages']}
        source_ids={s['id'] for s in DATA['sources']}
        task_ids=[t['id'] for t in DATA['tasks']]
        self.assertEqual(len(task_ids),len(set(task_ids)))
        self.assertEqual(len(source_ids),len(DATA['sources']))
        for t in DATA['tasks']:
            with self.subTest(task=t['id']):
                self.assertIn(t['stage'],stage_ids)
                self.assertIn(t['city'],('all','beijing','shanghai','guangzhou'))
                self.assertTrue(t['steps'])
                self.assertTrue(t['title'].strip())
                self.assertTrue(t['detail'].strip())
                self.assertTrue(set(t['sources'])<=source_ids)
    def test_source_links_and_review_dates(self):
        for s in DATA['sources']:
            with self.subTest(source=s['id']):
                p=urlparse(s['url'])
                self.assertEqual(p.scheme,'https')
                self.assertTrue(p.netloc.endswith(('.gov.cn','.beijing.gov.cn','.shanghai.gov.cn')))
                self.assertLessEqual(s['reviewed_at'],DATA['reviewed_at'])
                self.assertRegex(s['reviewed_at'],r'^\d{4}-\d\d-\d\d$')
    def test_policy_claims_match_sources(self):
        beijing=next(t for t in DATA['tasks'] if t['id']=='w3')
        shanghai=next(t for t in DATA['tasks'] if t['id']=='w4')
        med=next(t for t in DATA['tasks'] if t['id']=='w6')
        self.assertIn('2129',beijing['detail'])
        self.assertIn('2286',beijing['detail'])
        self.assertEqual(beijing['city'],'beijing')
        self.assertIn('2340',shanghai['detail'])
        self.assertIn('1872',shanghai['detail'])
        self.assertIn('3个月',med['detail'])
        self.assertIn('等待期',med['detail'])
        guangzhou=next(t for t in DATA['tasks'] if t['id']=='gz1')
        self.assertEqual(guangzhou['city'],'guangzhou')
        self.assertIn('90%',guangzhou['detail'])
        self.assertIn('2250',guangzhou['detail'])
        self.assertIn('2680',guangzhou['detail'])
        self.assertIn('24个月',guangzhou['detail'])
        gzpage=(ROOT/'guides/guangzhou.md').read_text(encoding='utf-8')
        for part in ('2026-10-30','rsj.gz.gov.cn','gjj.gz.gov.cn','hsa.gd.gov.cn','以官方为准'):
            self.assertIn(part,gzpage)
    def test_generated_offline_html_is_current(self):
        original=(ROOT/'index.html').read_bytes()
        result=subprocess.run([sys.executable,str(ROOT/'build.py')],cwd=str(ROOT),capture_output=True,text=True)
        self.assertEqual(result.returncode,0, result.stderr)
        self.assertEqual(original,(ROOT/'index.html').read_bytes(),'index.html is stale: rerun python3 build.py')
        index=original.decode('utf-8')
        self.assertIn('application/json',index)
        self.assertNotIn('<script src=',index)
        self.assertNotIn('<link rel="stylesheet"',index)
        self.assertEqual(index.count('<html'),1)
        self.assertIn('progress-fill',index)
        self.assertIn('id="cash"',index)
        self.assertIn('id="download"',index)
    def test_actionable_completion_and_blocked_for_all_tasks(self):
        for t in DATA['tasks']:
            with self.subTest(task=t['id']):
                self.assertGreaterEqual(len(t['steps']),2)
                self.assertGreaterEqual(len(t['proof']),10)
                self.assertGreaterEqual(len(t['blocked']),10)
                self.assertIn(t['risk'],('高','中','低'))

    def test_order_and_adversarial_routes(self):
        order={s['id']:i for i,s in enumerate(DATA['stages'])}
        self.assertEqual([order[t['stage']] for t in DATA['tasks']],sorted(order[t['stage']] for t in DATA['tasks']))
        taskids={t['id'] for t in DATA['tasks']}
        for needed in ('w12','w13','w14','w15','m3x1','m3x3','m6x2'):
            self.assertIn(needed,taskids)
        audit=(ROOT/'audit/ADVERSARIAL_REVIEW.md').read_text(encoding='utf-8')
        for issue in ('医保','N+1','债务','顺风车','隐私'):
            self.assertIn(issue,audit)

    def test_offline_reader_pages_are_generated(self):
        required=['guides/00-start-here.html','guides/beijing.html','guides/shanghai.html','guides/guangzhou.html','playbooks/01-labor-exit.html','playbooks/02-benefits-insurance.html','playbooks/03-cashflow-rescue.html','playbooks/04-job-search.html','playbooks/05-first-customer.html','playbooks/06-family-reset.html']
        for rel in required:
            with self.subTest(path=rel):
                p=ROOT/rel
                self.assertTrue(p.exists())
                txt=p.read_text(encoding='utf-8')
                self.assertIn('<html',txt)
                self.assertIn('index.html',txt)
        index=(ROOT/'index.html').read_text(encoding='utf-8')
        self.assertIn('id="triage"',index)
        self.assertIn('id="n-result"',index)
        self.assertIn('做完后留什么凭证',index)
        self.assertIn('UnemploymentMath',index)

    def test_readme_completeness(self):
        readme=(ROOT/'README.md').read_text(encoding='utf-8')
        for part in ('N+1','医保','公积金','现金流','CC BY 4.0','53 项','2026-10-08','广州'):
            self.assertIn(part,readme)

if __name__=='__main__':unittest.main()
