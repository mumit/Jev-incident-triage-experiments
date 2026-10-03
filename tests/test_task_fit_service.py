import json
import shutil
import tempfile
import threading
import unittest
from unittest.mock import patch
from triage_bench.experiment3.task_fit_review import routing_review
from triage_bench.experiment3.task_fit_data import build
from triage_bench.dataset import read_jsonl
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from triage_bench.dataset import ROOT
from triage_bench.app import App, handler_for
from triage_bench.experiment3.task_fit_service import TaskFitStudy
from triage_bench.study_page import return_path

class TaskFitServiceTests(unittest.TestCase):
    def test_fresh_clone_exposes_prepared_inputs_without_fabricated_results(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); shutil.copytree(ROOT/'data/task-fit-draft',root/'data/task-fit-draft')
            study=TaskFitStudy(root); catalog=study.catalog()
            self.assertEqual(catalog['summaries'],{})
            self.assertEqual(set(catalog['cases']),{'development','calibration'})
            identifier=catalog['cases']['development'][0]['id']
            case=study.case(identifier)
            self.assertIsNone(case['response']); self.assertIsNone(case['saved_request']); self.assertIsNone(case['trace'])
            self.assertEqual(set(case['request']['questions']),{'reading'})
            with self.assertRaises(ValueError): study.case(identifier,'evaluation')
            with self.assertRaises(ValueError): study.case(identifier,arm='unknown')

    def test_http_rejects_sealed_split_and_reader_preserves_task_fit_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); shutil.copytree(ROOT/'data/task-fit-draft',root/'data/task-fit-draft')
            server=ThreadingHTTPServer(('127.0.0.1',0),handler_for(App(root)))
            thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
            try:
                base=f'http://127.0.0.1:{server.server_port}'
                with urllib.request.urlopen(base+'/api/task-fit/catalog') as response: catalog=json.load(response)
                self.assertNotIn('evaluation',catalog['cases'])
                with self.assertRaises(urllib.error.HTTPError) as error:
                    urllib.request.urlopen(base+'/api/task-fit/case?split=evaluation&id=anything')
                self.assertEqual(error.exception.code,400)
                with urllib.request.urlopen(base+'/task-fit') as response:
                    html=response.read().decode(); self.assertIn('Reveal draft references',html)
                back='/task-fit?split=calibration&arm=structured#coverage'
                self.assertEqual(return_path(back),back)
                self.assertNotEqual(return_path('/task-fit#unknown'),'/task-fit#unknown')
            finally: server.shutdown(); server.server_close(); thread.join()

    def test_accepted_readings_are_distinct_from_domain_recommendations(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); build(root/'data')
            records=read_jsonl(root/'data/development.inputs.jsonl')[:2]
            labels=read_jsonl(root/'data/development.labels.jsonl')[:2]
            (root/'summary.json').write_text(json.dumps({'repeat_diagnostic':False,'arms':['structured']}))
            (root/'inputs.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in records))
            (root/'labels.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in labels))
            rows=[{'id':r['id'],'arm':'structured','status':'ok','reading':reading,
                   'probabilities':{v:.9 if v==reading else .05 for v in ('fault','normal','unknown')}}
                  for r,reading in zip(records,('normal','fault'))]
            (root/'responses.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
            before=(root/'responses.jsonl').read_bytes()
            with patch('triage_bench.experiment3.task_fit_review.verify'):
                points=routing_review(root)['arms']['structured']
            accepted=next(p for p in points if p['threshold']==.9)
            self.assertEqual(accepted['accepted_report_readings'],2)
            self.assertEqual(accepted['domain_recommendations'],1)
            self.assertEqual(accepted['wrong_domain_recommendations'],0)
            self.assertEqual(accepted['noc_or_review'],1)
            self.assertEqual(next(p for p in points if p['threshold']==.95)['domain_recommendations'],0)
            self.assertEqual((root/'responses.jsonl').read_bytes(),before)

    def test_evaluation_opens_only_after_complete_verified_boundary_and_assessment(self):
        from triage_bench.experiment3.task_fit_trial import prepare, finish, MODEL
        from triage_bench.experiment3.task_fit_advisory import assess, CRITERIA
        from triage_bench.experiment3.transforms import sha
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); directory=root/'data/task-fit-draft'
            shutil.copytree(ROOT/'data/task-fit-draft',directory)
            (root/'checkpoints').mkdir()
            boundary={'arm':'structured','advisory_threshold':.6,'research_criteria':CRITERIA}
            (root/'checkpoints/task-fit-analyst-boundary-2026-10-03.json').write_text(json.dumps(boundary))
            profile={'model':MODEL,'endpoint':'http://127.0.0.1:12345','context_tokens':32768}
            plan,records,requests=prepare(profile,'evaluation',['structured'],directory)
            plan['analyst_boundary']=boundary
            output=root/'runs/task-fit/evaluation-2026-10-03-v1'; output.mkdir(parents=True)
            refs=read_jsonl(directory/'evaluation.observations.jsonl'); rows=[]
            for record,ref,request in zip(records,refs,requests):
                probs={v:.9 if v==ref['reading'] else .05 for v in ('fault','normal','unknown')}
                rows.append({'id':record['id'],'arm':'structured','repetition':1,'status':'ok',
                    'request_sha256':request['request_sha256'],'reading':ref['reading'],'probabilities':probs,
                    'provider_confidence':None,'raw_response':{'model':MODEL,'answers':{'reading':{'choice':ref['reading'],'probabilities':probs}}}})
            for name,values in [('inputs',records),('requests',requests),('responses',rows),('observations',refs),('labels',read_jsonl(directory/'evaluation.labels.jsonl'))]:
                (output/f'{name}.jsonl').write_text(''.join(json.dumps(v)+'\n' for v in values))
            finish(output,plan,records,rows,directory=directory)
            with patch('triage_bench.experiment3.task_fit_service.check_boundary',return_value=boundary):
                # A summary alone cannot open sealed cases.
                self.assertNotIn('evaluation',TaskFitStudy(root).catalog()['cases'])
                assessment=assess(output,boundary,directory)
                (output/'analyst-assessment.json').write_text(json.dumps(assessment))
                study=TaskFitStudy(root); self.assertIn('evaluation',study.catalog()['cases'])
                self.assertIsNone(study.catalog()['first_wrong_suggestion'])
                case=study.case(records[0]['id'],'evaluation','structured')
                self.assertTrue(case['advisory']['analyst_review_required'])
                with self.assertRaises(ValueError):study.case(records[0]['id'],'evaluation','examples')
                # Altering even a displayed assessment count reseals the cases.
                assessment['domain_recommendations']+=1
                (output/'analyst-assessment.json').write_text(json.dumps(assessment))
                self.assertNotIn('evaluation',TaskFitStudy(root).catalog()['cases'])
