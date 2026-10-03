import copy,json,tempfile,threading,unittest
from pathlib import Path
from http.server import BaseHTTPRequestHandler,HTTPServer
from triage_bench.dataset import read_jsonl
from triage_bench.policy import OPTIONS
from triage_bench.experiment3.report_language_hosted import prepare,run,verify,report_body,normalize_report,REPORT_CHOICES,aggregate
from triage_bench.experiment3.selection import body
from triage_bench.experiment3.interpretation_model import report_inputs
from triage_bench.experiment3.transforms import MODEL

class ReportLanguageHostedTests(unittest.TestCase):
    def profile(self,endpoint='https://api.typesafe.ai/v1/systemone'):
        return {'model':MODEL,'endpoint':endpoint,'context_tokens':32768,'api_key':'language-fixture-secret'}

    def test_frozen_direct_input_and_text_only_report_plan(self):
        plan,records,keys,requests=prepare(self.profile());self.assertEqual(plan['maximum_requests'],296);self.assertEqual(len(records),140)
        direct=next(q for q in requests if q['arm']=='jev_direct');self.assertEqual(direct['body'],body(records[0],'selected'))
        reading=next(q for q in requests if q['arm']=='jev_reading');self.assertEqual(reading['body'],report_body(report_inputs(records[0])[0]['text']))
        self.assertNotIn('language-fixture-secret',json.dumps(plan));self.assertNotIn('draft_reference',json.dumps(requests));self.assertNotIn('current incident evidence',reading['body']['state'].lower())
        self.assertEqual([q['arm'] for q in requests[:4]],['jev_direct','jev_reading','jev_reading','jev_direct'])
        for p in [{**self.profile(),'model':'jev-latest'},self.profile('http://untrusted.invalid'),{**self.profile(),'context_tokens':512}]:
            with self.assertRaises(ValueError):prepare(p)

    def test_report_normalizer_rejects_invalid_choices_and_distributions(self):
        raw={'answers':{f:{'choice':next(iter(c)),'probabilities':{k:1/len(c) for k in c}} for f,c in REPORT_CHOICES.items()}}
        self.assertEqual(set(normalize_report(raw)[0]),{'domain','reading'})
        for bad in ['choice','probabilities']:
            x=copy.deepcopy(raw)
            if bad=='choice':x['answers']['reading']['choice']='noc'
            else:x['answers']['reading']['probabilities']['normal']=float('nan')
            with self.assertRaises(ValueError):normalize_report(x)
        x=copy.deepcopy(raw);x['answers']['reading']['probabilities']={'fault':.34,'normal':.34,'unknown':.33};self.assertAlmostEqual(sum(normalize_report(x)[1]['reading'].values()),1)

    def fixture(self,out,status=200,malformed=False):
        captured=[]
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                assert len(read_jsonl(out/'requests.jsonl'))==296
                b=json.loads(self.rfile.read(int(self.headers['Content-Length'])));captured.append(b);self.send_response(status);self.end_headers()
                if malformed:raw={'answers':{}}
                else:
                    choices=REPORT_CHOICES if 'domain' in b['questions'] else OPTIONS
                    predicted={'domain':'none','reading':'unknown','initial_owner':'noc','priority':'P2','next_check':'gather_evidence','insufficient_evidence':'yes'}
                    raw={'model':MODEL,'note':'language-fixture-secret','answers':{f:{'choice':predicted[f],'probabilities':{k:1/len(c) for k in c}} for f,c in choices.items()}}
                self.wfile.write(json.dumps(raw).encode())
            def log_message(self,*a):pass
        server=HTTPServer(('127.0.0.1',0),Handler);t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
        try:s=run(out,self.profile('http://127.0.0.1:'+str(server.server_port)))
        finally:server.shutdown();server.server_close();t.join()
        return s,captured

    def test_full_fixture_records_wire_order_redacts_key_and_verifies_aggregation(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)/'run';s,bodies=self.fixture(out);self.assertEqual(s['attempted_requests'],296);self.assertEqual(s['failed_requests'],0)
            self.assertEqual(bodies,[q['body'] for q in read_jsonl(out/'requests.jsonl')]);self.assertEqual(verify(out/'summary.json')[0],s)
            for p in out.iterdir():self.assertNotIn('language-fixture-secret',p.read_text())
            with self.assertRaises(ValueError):run(out,self.profile())
            p=out/'responses.jsonl';p.write_text(p.read_text()+'\n')
            with self.assertRaisesRegex(ValueError,'evidence'):verify(out/'summary.json')

    def test_fatal_and_malformed_stops_preserve_planned_denominators(self):
        for status,malformed,n in [(429,False,1),(200,True,3)]:
            with tempfile.TemporaryDirectory() as folder:
                out=Path(folder)/'run';s,c=self.fixture(out,status,malformed);self.assertEqual(len(c),n);self.assertEqual(s['unattempted_requests'],296-n)
                self.assertEqual(s['approaches']['jev_reading']['metrics']['records'],140);self.assertEqual(s['report_metrics']['fields']['both']['reports'],156)
                self.assertEqual(s['report_metrics']['fields']['both']['correct'],0);verify(out/'summary.json')
                if n==1:self.assertEqual(s['approaches']['jev_reading']['metrics']['missing_records'],140)

    def test_incomplete_report_replies_cannot_produce_a_policy_answer(self):
        _,records,_,_=prepare(self.profile());r=next(r for r in records if len(r['input']['observations'])==2)
        responses=[{'id':r['id'],'arm':'jev_reading','observation_index':0,'status':'ok','predictions':{'domain':'power','reading':'fault'},'probabilities':{}}]
        result=aggregate([r],responses);self.assertFalse(result['jev_direct']);self.assertEqual(result['jev_reading'][0]['status'],'error');self.assertFalse(result['jev_reading'][0]['predictions'])
