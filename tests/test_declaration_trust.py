import copy,json,tempfile,threading,unittest
from pathlib import Path
from http.server import BaseHTTPRequestHandler,HTTPServer
from triage_bench.dataset import read_jsonl
from triage_bench.experiment3.trust_data import DIRECTORY,build,validate
from triage_bench.experiment3.trust_trial import prepare,body,aggregate,diagnostic,run_local,run_hosted,verify
from triage_bench.experiment3.trust_policy import header_fact,effective_readings,apply_trust_policy
from triage_bench.experiment3.declared_trial import body as frozen_body
from triage_bench.experiment3.report_language_hosted import REPORT_CHOICES
from triage_bench.experiment3.transforms import MODEL

class DeclarationTrustTests(unittest.TestCase):
 def profile(self,endpoint='https://api.typesafe.ai/v1/systemone'):return dict(endpoint=endpoint,model=MODEL,context_tokens=32768,api_key='trust-fixture-secret')
 def test_pack_reproducibility_annotations_and_independent_diagnostic(self):
  with tempfile.TemporaryDirectory() as f:self.assertEqual(build(Path(f)/'data'),json.loads((DIRECTORY/'manifest.json').read_text()))
  p,records,keys,ann,texts,qs=prepare(self.profile());self.assertEqual(validate(),dict(records=80,reports=160,families=20,pairs=40,distinct_report_texts=40));self.assertEqual(p['prepared_reference_diagnostic']['reference_matches'],80)
  refs={k['id']:k['labels'] for k in keys}
  for r in diagnostic(records,ann):self.assertEqual(r['predictions'],refs[r['id']])
  self.assertLess(sum(r['predictions']==refs[r['id']] for r in diagnostic(records,ann,False)),80)
  self.assertEqual(len(qs),40)
  for q in qs:self.assertEqual(q['body'],frozen_body(next(t['text'] for t in texts if t['text_id']==q['text_id']),'jev_declared'));self.assertNotIn('instrument_domain',json.dumps(q['body']));self.assertNotIn('trust-fixture-secret',json.dumps(q))
 def test_parser_does_not_infer_technical_domain_or_operation(self):
  for text in ['radio failure power supply','No declared domain: core','Instrument domain: unavailable.','Instrument domain: core. Instrument domain: core.','Instrument domain: core and ran.','Instrument domain: radio.']:
   self.assertEqual(header_fact(text)['domain'],'none')
  self.assertEqual(header_fact('Instrument domain: RAN. Operation normal. core failed.'),dict(state='declared',domain='ran'))
 def test_occurrence_specific_domain_and_matching_readings(self):
  _,records,keys,ann,texts,_=prepare(self.profile());r=next(r for r,k in zip(records,keys) if k['control']=='fault_conflict' and r['id'].endswith('-b'));a=next(x for x in records if x['id']==r['id'][:-1]+'a');raw=[dict(observation_index=i,domain='none',reading=reading,probabilities=dict(domain={'none':1},reading={reading:1})) for i,reading in enumerate(['fault','normal'])];saved=copy.deepcopy(raw);ar=effective_readings(a,raw);br=effective_readings(r,raw)
  self.assertEqual(raw,saved);self.assertNotEqual(ar[0]['domain'],br[0]['domain']);self.assertEqual(ar[0]['reading'],br[0]['reading']);self.assertNotIn('domain',br[0]['probabilities'])
  before=apply_trust_policy(r,br,False);after=apply_trust_policy(r,br);self.assertNotEqual(before['predictions']['initial_owner'],'noc');self.assertEqual(after['predictions']['initial_owner'],'noc');self.assertEqual(before['predictions']['priority'],after['predictions']['priority']);self.assertEqual(after['trace']['declaration_guard']['blocked_observations'],[0])
 def test_normal_conflicts_eligibility_and_clean_scope_controls(self):
  _,records,keys,ann,*_=prepare(self.profile());refs={}
  for a in ann:refs.setdefault(a['id'],[]).append(a)
  for r,k in zip(records,keys):
   out=apply_trust_policy(r,effective_readings(r,refs[r['id']]));self.assertEqual(out['predictions'],k['labels']);facts=out['trace']['declaration_guard']
   if k['control']=='stale' and r['id'].endswith('-b'):self.assertEqual(facts['blocked_observations'],[]);self.assertTrue(facts['facts'][1]['conflict']);self.assertFalse(facts['facts'][1]['eligible'])
   if k['control']=='unlinked' and r['id'].endswith('-a'):self.assertEqual(facts['blocked_observations'],[]);self.assertTrue(facts['facts'][1]['conflict']);self.assertFalse(facts['facts'][1]['eligible'])
 def fixture(self,out,status=200,malformed=False):
  captured=[]
  class Handler(BaseHTTPRequestHandler):
   def do_POST(self):
    assert len(read_jsonl(out/'requests.jsonl'))==40
    b=json.loads(self.rfile.read(int(self.headers['Content-Length'])));captured.append(b);self.send_response(status);self.end_headers();pred=dict(domain=header_fact(b['state'])['domain'],reading='normal' if 'logs normal execution' in b['state'] else 'fault');raw={'answers':{}} if malformed else {'model':MODEL,'note':'trust-fixture-secret','answers':{f:dict(choice=pred[f],probabilities={k:float(k==pred[f]) for k in choices}) for f,choices in REPORT_CHOICES.items()}};self.wfile.write(json.dumps(raw).encode())
   def log_message(self,*a):pass
  server=HTTPServer(('127.0.0.1',0),Handler);worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
  try:s=run_hosted(out,self.profile('http://127.0.0.1:'+str(server.server_port)))
  finally:server.shutdown();server.server_close();worker.join()
  return s,captured
 def test_recording_redaction_and_frozen_shared_reads(self):
  with tempfile.TemporaryDirectory() as f:
   out=Path(f)/'run';s,cap=self.fixture(out);self.assertEqual(s['attempted_predictions'],40);self.assertEqual(verify(out/'summary.json')[0],s);self.assertEqual(cap,[q['body'] for q in read_jsonl(out/'requests.jsonl')]);self.assertEqual(s['approaches']['jev_declared__guarded']['metrics']['all_fields_accuracy'],1)
   _,rows,*_=verify(out/'summary.json')
   for identifier,r in rows['jev_declared__guarded'].items():self.assertEqual(r['readings'],rows['jev_declared__unguarded'][identifier]['readings']);self.assertEqual(r['raw_readings'],rows['jev_declared__unguarded'][identifier]['raw_readings'])
   for p in out.iterdir():self.assertNotIn('trust-fixture-secret',p.read_text())
   with self.assertRaises(ValueError):run_hosted(out,self.profile())
   p=out/'jev_declared__guarded.jsonl';p.write_text(p.read_text()+'\n')
   with self.assertRaisesRegex(ValueError,'evidence'):verify(out/'summary.json')
 def test_shared_failure_cannot_become_valid_by_guard(self):
  for status,malformed,n in [(429,False,1),(200,True,3)]:
   with tempfile.TemporaryDirectory() as f:
    out=Path(f)/'run';s,cap=self.fixture(out,status,malformed);self.assertEqual(len(cap),n);self.assertEqual(s['unattempted_predictions'],40-n)
    for arm,m in s['approaches'].items():self.assertEqual(m['metrics']['records'],80);self.assertEqual(m['metrics']['all_fields_accuracy'],0)
    self.assertEqual(s['report_metrics']['jev_declared']['fields']['both']['distinct_texts'],40);verify(out/'summary.json')
 def test_frozen_local_recipes_actual_margins_and_no_hidden_retraining(self):
  with tempfile.TemporaryDirectory() as f:
   out=Path(f)/'run';s=run_local(out);self.assertEqual(verify(out/'summary.json')[0],s);self.assertEqual(s['attempted_predictions'],120)
   for r in ['narrow','broad']:self.assertEqual(s['training_metadata'][r]['training_reports'],210);self.assertEqual(len(read_jsonl(out/(r+'.inspections.jsonl'))),40)
