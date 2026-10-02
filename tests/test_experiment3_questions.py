import copy
import json
from pathlib import Path
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler,HTTPServer
from unittest.mock import patch
from triage_bench.dataset import read_jsonl,write_jsonl
from triage_bench.experiments import focused_questions
from triage_bench.policy import OPTIONS
from triage_bench.experiment3.question_trial import DIRECTORY,ARMS,body,build,prepare,run,validate,verify
from triage_bench.experiment3.transforms import MODEL,sha


class QuestionTrialTests(unittest.TestCase):
    def profile(self,endpoint='https://api.typesafe.ai/v1/systemone'):
        return {'model':MODEL,'endpoint':endpoint,'context_tokens':32768,'api_key':'trial-fixture-secret'}

    def fixture(self,output,status=200,model=MODEL,malformed=False):
        captured=[]
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                assert len(read_jsonl(output/'requests.jsonl'))==32 and (output/'protocol.json').is_file()
                captured.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
                self.send_response(status);self.end_headers()
                raw={'model':model,'note':'trial-fixture-secret','answers':{f:{'choice':next(iter(v)),'probabilities':{c:1/len(v) for c in v}} for f,v in OPTIONS.items()}}
                if malformed:raw['answers']={}
                self.wfile.write(json.dumps(raw).encode())
            def log_message(self,*args):pass
        server=HTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:summary=run(output,self.profile(f'http://127.0.0.1:{server.server_port}/v1/systemone'))
        finally:server.shutdown();server.server_close();thread.join()
        return summary,captured

    def test_new_pack_reproduces_and_has_six_changing_two_invariant_pairs(self):
        with tempfile.TemporaryDirectory() as folder:
            new=Path(folder)/'data';manifest=build(new)
            self.assertEqual(manifest,validate(DIRECTORY))
            keys=read_jsonl(new/'development.labels.jsonl')
            self.assertEqual(sum(k['pair_kind']=='decision_change' for k in keys),12)
            self.assertEqual(manifest['reference_status'],'draft_not_specialist_reviewed')
            with self.assertRaises(ValueError):build(new)

    def test_same_combined_state_unchanged_priority_choices_and_no_label_leak(self):
        r=read_jsonl(DIRECTORY/'development.inputs.jsonl')[0];r['input']['labels']='REFERENCE_SENTINEL';r['labels']='REFERENCE_SENTINEL';before=copy.deepcopy(r)
        old,new=body(r,'original'),body(r,'precedence')
        self.assertEqual(old['questions'],focused_questions())
        self.assertEqual(old['state'],new['state'])
        self.assertEqual(old['questions']['priority'],new['questions']['priority'])
        for field in OPTIONS:self.assertEqual(old['questions'][field]['criteria'],new['questions'][field]['criteria'])
        self.assertNotIn('REFERENCE_SENTINEL',json.dumps(new));self.assertEqual(r,before)
        self.assertNotEqual(old['questions']['initial_owner']['instructions'],new['questions']['initial_owner']['instructions'])

    def test_preflight_binds_all_inputs_questions_and_alternating_order(self):
        protocol,records,keys,requests=prepare(self.profile())
        self.assertEqual((len(records),len(keys),len(requests)),(16,16,32))
        self.assertEqual([r['variant'] for r in requests[:4]],['original','precedence','precedence','original'])
        self.assertEqual(len(protocol['question_sha256']),2)
        with self.assertRaises(ValueError):prepare({**self.profile(),'context_tokens':512})
        with self.assertRaises(ValueError):prepare({**self.profile(),'model':'different'})

    def test_uncontrolled_pair_change_rejected_even_with_updated_checksum(self):
        with tempfile.TemporaryDirectory() as folder:
            new=Path(folder)/'data';build(new);rows=read_jsonl(new/'development.inputs.jsonl')
            rows[1]['input']['change_record']['detail']='Second intervention';write_jsonl(new/'development.inputs.jsonl',rows)
            manifest=json.loads((new/'manifest.json').read_text());manifest['sha256']['development.inputs.jsonl']=sha((new/'development.inputs.jsonl').read_bytes());(new/'manifest.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError,'Uncontrolled'):validate(new)

    def test_saved_before_send_exact_requests_redaction_and_metric_audit(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)/'run';summary,captured=self.fixture(out)
            self.assertEqual(summary['attempted_requests'],32);self.assertEqual(summary['failed_requests'],0)
            self.assertEqual(captured,[r['body'] for r in read_jsonl(out/'requests.jsonl')])
            for path in out.iterdir():self.assertNotIn('trial-fixture-secret',path.read_text())
            verify(out/'summary.json')
            summary['approaches']['original']['metrics']['all_fields_accuracy']=.123;(out/'summary.json').write_text(json.dumps(summary))
            with self.assertRaisesRegex(ValueError,'metrics'):verify(out/'summary.json')

    def test_rate_limit_checkpoint_and_malformed_stops_keep_missing_denominator(self):
        for kwargs,n,reason in [({'status':429},1,'provider_http_429'),({'model':'other'},1,'checkpoint_mismatch'),({'malformed':True},3,'three_consecutive_failures')]:
            with self.subTest(kwargs=kwargs),tempfile.TemporaryDirectory() as folder:
                out=Path(folder)/'run';summary,captured=self.fixture(out,**kwargs)
                self.assertEqual(len(captured),n);self.assertEqual(summary['stopped_reason'],reason);self.assertEqual(summary['unattempted_requests'],32-n)
                self.assertEqual(summary['approaches']['precedence']['metrics']['records'],16);verify(out/'summary.json')

    def test_no_key_or_existing_output_never_sends(self):
        with tempfile.TemporaryDirectory() as folder,patch('urllib.request.build_opener',side_effect=AssertionError('No call')):
            out=Path(folder)/'run'
            with self.assertRaises(ValueError):run(out,{**self.profile(),'api_key':''})
            self.assertFalse(out.exists());out.mkdir()
            with self.assertRaises(ValueError):run(out,self.profile())

    def test_question_service_never_invents_missing_predictions(self):
        from triage_bench.experiment3.question_service import QuestionStudy
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);build(root/'data/experiment-3-question-draft');study=QuestionStudy(root)
            catalog=study.catalog();self.assertIsNone(catalog['hosted_pilot']);self.assertIsNone(catalog['pilot'])
            case=study.case(next(iter(study.records)),'precedence')
            self.assertTrue(all(v is None for v in case['hosted_outputs'].values()))
            self.assertEqual(case['question_sets']['original']['priority'],case['question_sets']['precedence']['priority'])
            with self.assertRaises(ValueError):study.case(next(iter(study.records)),split='train')

    def test_question_http_inspection_and_export_routes_match_exact_request(self):
        import urllib.request
        from http.server import ThreadingHTTPServer
        from triage_bench.app import App,handler_for
        server=ThreadingHTTPServer(('127.0.0.1',0),handler_for(App()));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        origin='http://127.0.0.1:'+str(server.server_port)
        try:
            with urllib.request.urlopen(origin+'/api/experiment3/catalog?trial=questions') as response:catalog=json.load(response)
            self.assertEqual(catalog['comparison'],'questions');identifier=catalog['cases']['development'][0]['id']
            with urllib.request.urlopen(origin+'/api/experiment3/export?trial=questions&id='+identifier+'&variant=precedence') as response:export=json.load(response)
            record=next(r for r in read_jsonl(DIRECTORY/'development.inputs.jsonl') if r['id']==identifier)
            self.assertEqual(export,body(record,'precedence'))
            with self.assertRaises(Exception):urllib.request.urlopen(origin+'/api/experiment3/catalog?trial=unrecognized')
        finally:server.shutdown();server.server_close();thread.join()
