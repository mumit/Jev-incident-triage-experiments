import json
from pathlib import Path
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from unittest.mock import patch
from triage_bench.dataset import ROOT,read_jsonl
from triage_bench.experiment3.audit_hosted import verify
from triage_bench.experiment3.service import PilotStudy
from triage_bench.policy import OPTIONS
from triage_bench.experiment3.data import DIRECTORY
from triage_bench.experiment3.hosted import encoded,prepare,run
from triage_bench.experiment3.review import review
from triage_bench.experiment3.transforms import MODEL,sha


PAIR=read_jsonl(DIRECTORY/'development.labels.jsonl')[0]['pair_id']


class HostedTests(unittest.TestCase):
    def profile(self,endpoint='https://api.typesafe.ai/v1/systemone'):
        return {'model':MODEL,'endpoint':endpoint,'context_tokens':32768,'deployment':'Fixture','api_key':'fixture-secret'}

    def fixture(self,output,status=200,model=MODEL,malformed=False):
        captured=[]
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                assert (output/'protocol.json').exists() and len(read_jsonl(output/'requests.jsonl'))==8
                captured.append({'header':self.headers['Authorization'],'body':json.loads(self.rfile.read(int(self.headers['Content-Length'])))})
                self.send_response(status);self.send_header('Content-Type','application/json');self.end_headers()
                raw={'model':model,'answers':{f:{'choice':next(iter(c)),'probabilities':{k:1/len(c) for k in c}} for f,c in OPTIONS.items()},'fixture_note':'fixture-secret'}
                if malformed:raw['answers']={}
                self.wfile.write(json.dumps(raw).encode())
            def log_message(self,*args):pass
        server=HTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:summary=run(output,self.profile(f'http://127.0.0.1:{server.server_port}/v1/systemone'),pair_ids=[PAIR])
        finally:server.shutdown();server.server_close();thread.join()
        return summary,captured

    def test_review_identifies_input_information_loss_without_signoff(self):
        report=review()
        self.assertEqual(report['network_specialist_review'],'pending')
        self.assertEqual(len(report['variants']['baseline']['indistinguishable_pairs_with_different_references']),8)
        self.assertEqual(len(report['variants']['measurement']['indistinguishable_pairs_with_different_references']),0)
        self.assertEqual(report['pairs'],18)

    def test_preflight_preserves_pairs_fixed_questions_and_rotating_order(self):
        protocol,records,keys,requests=prepare(self.profile(),pair_ids=[PAIR])
        self.assertEqual((len(records),len(keys),len(requests)),(2,2,8))
        self.assertEqual([r['variant'] for r in requests[:4]],['baseline','dependency','measurement','combined'])
        self.assertEqual([r['variant'] for r in requests[4:]],['dependency','measurement','combined','baseline'])
        for r in requests:
            self.assertEqual(r['request_sha256'],sha(encoded(r['body'])))
            self.assertEqual(set(r['body']),{'model','state','questions'})
            self.assertNotIn('incident_family_id',r['body']['state'])
        self.assertEqual(protocol['maximum_requests'],8)
        self.assertNotIn('fixture-secret',json.dumps(protocol))

    def test_invalid_capacity_model_endpoint_and_pair_fail_before_inference(self):
        for change in [{'context_tokens':512},{'model':'other-checkpoint'},{'endpoint':'https://api.typesafe.ai/v1/systemone?key=secret'},{'endpoint':'http://outside.example/api'}]:
            with self.subTest(change=change),self.assertRaises(ValueError):prepare({**self.profile(),**change})
        with self.assertRaises(ValueError):prepare(self.profile(),pair_ids=['missing'])

    def test_no_key_and_immutable_output_do_not_call_provider(self):
        with tempfile.TemporaryDirectory() as folder,patch('urllib.request.build_opener',side_effect=AssertionError('No call')):
            out=Path(folder)/'out'
            with self.assertRaises(ValueError):run(out,{**self.profile(),'api_key':''},pair_ids=[PAIR])
            self.assertFalse(out.exists());out.mkdir()
            with self.assertRaises(ValueError):run(out,self.profile(),pair_ids=[PAIR])

    def test_exact_wire_requests_saved_before_calls_and_secret_redacted(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)/'run';summary,captured=self.fixture(out)
            saved=read_jsonl(out/'requests.jsonl')
            self.assertEqual(len(captured),8)
            self.assertTrue(all(r['header']=='Bearer fixture-secret' for r in captured))
            self.assertEqual([r['body'] for r in captured],[r['body'] for r in saved])
            self.assertEqual(summary['status'],'completed')
            self.assertEqual(summary['failed_requests'],0)
            for path in out.iterdir():self.assertNotIn('fixture-secret',path.read_text())
            for variant in summary['approaches']:
                self.assertEqual(summary['approaches'][variant]['metrics']['attempted_records'],2)

    def test_rate_limit_stops_without_retry_and_missing_counts_against_scores(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)/'run';summary,captured=self.fixture(out,status=429)
            self.assertEqual(len(captured),1)
            self.assertEqual(summary['unattempted_requests'],7)
            self.assertEqual(summary['stopped_reason'],'provider_http_429')
            self.assertEqual(summary['approaches']['dependency']['metrics']['missing_records'],2)
            self.assertEqual(summary['approaches']['dependency']['metrics']['all_fields_accuracy'],0)
            self.assertNotIn('fixture-secret',(out/'baseline.jsonl').read_text())

    def test_checkpoint_mismatch_stops_and_cannot_be_scored_as_success(self):
        with tempfile.TemporaryDirectory() as folder:
            summary,captured=self.fixture(Path(folder)/'run',model='other-checkpoint')
            self.assertEqual(len(captured),1)
            self.assertEqual(summary['stopped_reason'],'checkpoint_mismatch')
            self.assertEqual(summary['failed_requests'],1)

    def test_saved_hosted_evidence_is_verified_and_edited_scores_are_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)/'run';self.fixture(out)
            study=PilotStudy()
            summary,rows,requests=verify(out/'summary.json',ROOT,study.manifest,study.records['development'],study.keys['development'])
            self.assertEqual(summary['attempted_requests'],8)
            self.assertEqual(len(requests),8)
            value=json.loads((out/'summary.json').read_text());value['approaches']['baseline']['metrics']['all_fields_accuracy']=.12345
            (out/'summary.json').write_text(json.dumps(value))
            with self.assertRaisesRegex(ValueError,'recomputed'):verify(out/'summary.json',ROOT,study.manifest,study.records['development'],study.keys['development'])

    def test_changed_saved_request_cannot_be_presented_as_exact(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)/'run';self.fixture(out)
            study=PilotStudy();path=out/'requests.jsonl'
            path.write_text(path.read_text().replace('Current incident evidence:','Altered incident evidence:'))
            with self.assertRaisesRegex(ValueError,'fingerprint'):verify(out/'summary.json',ROOT,study.manifest,study.records['development'],study.keys['development'])

    def test_partial_hosted_coverage_is_explicit_and_training_remains_unscored(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)/'run';self.fixture(out)
            study=PilotStudy();study.load_hosted(out/'summary.json')
            ids=[id for id,k in study.keys['development'].items() if k['pair_id']==PAIR]
            self.assertTrue(study.case(ids[0])['hosted_outputs']['baseline'])
            other=next(id for id,k in study.keys['development'].items() if k['pair_id']!=PAIR)
            self.assertIsNone(study.case(other)['hosted_outputs']['baseline'])
            training=study.case(next(iter(study.records['train'])),split='train')
            self.assertTrue(all(row is None for row in training['hosted_outputs'].values()))
            self.assertTrue(all(req is None for req in training['hosted_saved_requests'].values()))

    def test_three_bad_responses_stop_without_fabricated_predictions(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)/'run';summary,captured=self.fixture(out,malformed=True)
            self.assertEqual(len(captured),3)
            self.assertEqual(summary['stopped_reason'],'three_consecutive_failures')
            self.assertTrue(all(not r['predictions'] for variant in summary['approaches'] for r in read_jsonl(out/(variant+'.jsonl'))))
