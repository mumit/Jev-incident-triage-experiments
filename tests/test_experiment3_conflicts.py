import json
from pathlib import Path
import tempfile,threading,unittest
from http.server import BaseHTTPRequestHandler,HTTPServer
from triage_bench.dataset import read_jsonl
from triage_bench.policy import OPTIONS
from triage_bench.experiment3.conflict_trial import DIRECTORY,build,validate,prepare,run,verify
from triage_bench.experiment3.transforms import MODEL

class ConflictTrialTests(unittest.TestCase):
    def profile(self,endpoint='https://api.typesafe.ai/v1/systemone'):
        return {'model':MODEL,'endpoint':endpoint,'context_tokens':32768,'api_key':'conflict-fixture-secret'}

    def fixture(self,out,status=200):
        captured=[]
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                assert len(read_jsonl(out/'planned_requests.jsonl'))==48
                captured.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
                self.send_response(status);self.end_headers()
                owner='power' if 16<len(captured)<=32 else 'noc'
                predictions={'initial_owner':owner,'priority':'P2','next_check':'gather_evidence','insufficient_evidence':'yes'}
                raw={'model':MODEL,'note':'conflict-fixture-secret','answers':{f:{'choice':predictions[f],'probabilities':{k:1/len(c) for k in c}} for f,c in OPTIONS.items()}}
                self.wfile.write(json.dumps(raw).encode())
            def log_message(self,*args):pass
        server=HTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:result=run(out,self.profile(f'http://127.0.0.1:{server.server_port}/v1/systemone'))
        finally:server.shutdown();server.server_close();thread.join()
        return result,captured

    def test_fresh_pairs_are_reproducible_and_normal_measurement_moves_to_stale(self):
        with tempfile.TemporaryDirectory() as folder:
            manifest=build(Path(folder)/'data');self.assertEqual(manifest,validate())
        keys=read_jsonl(DIRECTORY/'development.labels.jsonl');self.assertEqual(len(keys),8)
        self.assertTrue(all(k['pair_kind']=='decision_change' for k in keys))
        self.assertTrue(any(k['changed_path']=='input.observations[0].measured_at' for k in keys))
        self.assertEqual({k['labels']['initial_owner'] for k in keys},{'power','transport','ran','noc'})

    def test_plan_binds_three_identical_repetitions_before_any_call(self):
        plan,requests=prepare(self.profile());self.assertEqual(plan['maximum_requests'],48)
        self.assertEqual([{k:v for k,v in r.items() if k!='repetition'} for r in requests[:16]],
                         [{k:v for k,v in r.items() if k!='repetition'} for r in requests[16:32]])
        self.assertNotIn('conflict-fixture-secret',json.dumps(plan))

    def test_repetition_variation_is_visible_and_full_wire_plan_is_used(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)/'run';s,captured=self.fixture(out)
            self.assertEqual(s['attempted_requests'],48);self.assertEqual(s['failed_requests'],0)
            self.assertEqual(captured,[r['body'] for r in read_jsonl(out/'planned_requests.jsonl')])
            for arm,a in s['approaches'].items():
                self.assertEqual(a['cases_complete'],8);self.assertEqual(a['cases_with_identical_decisions'],0)
                self.assertEqual(a['planned_packet_responses'],24);self.assertEqual(a['planned_pairs'],12)
            verify(out/'summary.json')
            for p in out.rglob('*'):
                if p.is_file():self.assertNotIn('conflict-fixture-secret',p.read_text())
            s['approaches']['original']['all_fields_accuracy']=.123;(out/'summary.json').write_text(json.dumps(s))
            with self.assertRaisesRegex(ValueError,'recomputed'):verify(out/'summary.json')

    def test_rate_limit_stops_entire_study_and_missing_repetitions_count(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)/'run';s,captured=self.fixture(out,status=429)
            self.assertEqual(len(captured),1);self.assertEqual(s['unattempted_requests'],47);self.assertEqual(len(s['runs']),1)
            self.assertEqual(s['approaches']['precedence']['all_fields_accuracy'],0)
            self.assertEqual(s['approaches']['precedence']['cases_complete'],0);verify(out/'summary.json')

    def test_read_only_service_selects_repetition_without_mutating_other_views(self):
        from triage_bench.experiment3.conflict_service import ConflictStudy
        study=ConflictStudy();identifier=next(iter(study.records))
        first=study.catalog(1);third=study.catalog(3)
        self.assertEqual((first['repetition'],third['repetition']),(1,3));self.assertEqual(first['manifest']['records'],8)
        case=study.case(identifier,'precedence',repetition=2)
        self.assertEqual(case['request'],study.case(identifier,'precedence',repetition=1)['request'])
        with self.assertRaises(ValueError):study.catalog(4)
        with self.assertRaises(ValueError):study.case(identifier,split='train')
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);build(root/'data/experiment-3-conflict-draft');missing=ConflictStudy(root)
            self.assertIsNone(missing.catalog(3)['hosted_pilot']);self.assertTrue(all(r is None for r in missing.case(identifier)['hosted_outputs'].values()))

    def test_http_repetition_and_export_preserve_exact_questions(self):
        import urllib.request,urllib.error
        from http.server import ThreadingHTTPServer
        from triage_bench.app import App,handler_for
        server=ThreadingHTTPServer(('127.0.0.1',0),handler_for(App()));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        url='http://127.0.0.1:'+str(server.server_port)
        try:
            with urllib.request.urlopen(url+'/api/experiment3/catalog?trial=conflicts&repetition=2') as r:catalog=json.load(r)
            self.assertEqual(catalog['comparison'],'conflicts');self.assertEqual(catalog['repetition'],2)
            identifier=catalog['cases']['development'][0]['id']
            with urllib.request.urlopen(url+'/api/experiment3/export?trial=conflicts&repetition=2&variant=precedence&id='+identifier) as r:request=json.load(r)
            from triage_bench.experiment3.question_trial import body
            record=next(r for r in read_jsonl(DIRECTORY/'development.inputs.jsonl') if r['id']==identifier);self.assertEqual(request,body(record,'precedence'))
            with self.assertRaises(urllib.error.HTTPError):urllib.request.urlopen(url+'/api/experiment3/catalog?trial=conflicts&repetition=4')
        finally:server.shutdown();server.server_close();thread.join()
