import copy,json,tempfile,threading,unittest
from pathlib import Path
from http.server import BaseHTTPRequestHandler,HTTPServer
from triage_bench.dataset import read_jsonl
from triage_bench.experiment3.metadata_data import DIRECTORY,build,validate
from triage_bench.experiment3.metadata_policy import scope_fact,apply_metadata_policy
from triage_bench.experiment3.metadata_trial import prepare,run_hosted,run_local,verify,aggregate,diagnostic
from triage_bench.experiment3.report_scope_trial import body
from triage_bench.experiment3.report_language_hosted import REPORT_CHOICES
from triage_bench.experiment3.transforms import MODEL

class MetadataPolicyTests(unittest.TestCase):
 def profile(self,endpoint='https://api.typesafe.ai/v1/systemone'):
  return dict(endpoint=endpoint,model=MODEL,context_tokens=32768,api_key='metadata-fixture-secret')
 def test_reproducible_pair_pack_and_independently_written_reference_diagnostic(self):
  with tempfile.TemporaryDirectory() as folder:
   manifest=build(Path(folder)/'data');self.assertEqual(manifest,json.loads((DIRECTORY/'manifest.json').read_text()))
  p,records,keys,ann,texts,_=prepare(self.profile());self.assertEqual(validate(),dict(records=48,reports=96,families=12,pairs=24,distinct_report_texts=16))
  keymap={k['id']:k for k in keys};rows=diagnostic(records,ann)
  self.assertEqual(sum(r['predictions']==keymap[r['id']]['labels'] for r in rows['asset']),28)
  self.assertEqual(sum(r['predictions']==keymap[r['id']]['labels'] for r in rows['metadata']),48)
  self.assertEqual(p['prepared_reference_diagnostic']['asset']['reference_matches'],28)
  for t in texts:self.assertGreater(len(t['occurrences']),1)
 def test_unresolved_scope_is_conservative_but_ineligible_reports_do_not_block(self):
  _,records,keys,ann,_,_=prepare(self.profile());refs={}
  for a in ann:refs.setdefault(a['id'],[]).append(a)
  for k in keys:
   if k['control'] not in {'missing','ambiguous','stale','unlinked'}:continue
   r=next(r for r in records if r['id']==k['id']);result=apply_metadata_policy(r,refs[r['id']]);self.assertEqual(result['predictions'],k['labels'])
   self.assertEqual(bool(result['trace']['unresolved_scope_reports']),k['labels']['initial_owner']=='noc')
 def test_no_domain_or_fault_classification_in_metadata_calculator(self):
  _,records,_,ann,_,_=prepare(self.profile());r=copy.deepcopy(records[0]);readings=[a for a in ann if a['id']==r['id']];before=apply_metadata_policy(r,readings)
  for o in r['input']['observations']:o['detail']='Unrelated power fault, radio fault, normal core recovery.'
  self.assertEqual(apply_metadata_policy(r,readings),before)
  for a in readings:a['reading']='unknown'
  self.assertEqual(apply_metadata_policy(r,readings)['predictions']['initial_owner'],'noc')
  with self.assertRaises(ValueError):apply_metadata_policy(r,list(reversed(readings)))
 def test_malformed_unknown_scope_and_same_function_condition_boundary(self):
  for value in [None,'bad',{},dict(status='declared',function=[],comparison_context='x'),dict(status='declared',function='not_in_schema',comparison_context='x'),dict(status='declared',function='request_intake',comparison_context=None)]:
   self.assertNotEqual(scope_fact({'measurement_scope':value})['state'],'declared')
  _,records,_,ann,_,_=prepare(self.profile());r=copy.deepcopy(records[0]);readings=[a for a in ann if a['id']==r['id']]
  self.assertEqual(apply_metadata_policy(r,readings)['predictions']['initial_owner'],'core')
  r['input']['observations'][1]['measurement_scope']['function']='request_intake';self.assertEqual(apply_metadata_policy(r,readings)['predictions']['initial_owner'],'noc')
  r['input']['observations'][1]['measurement_scope']['comparison_context']='condition-B';self.assertEqual(apply_metadata_policy(r,readings)['predictions']['initial_owner'],'core')
  r['input']['observations'][1]['measurement_scope']['comparison_context']=None;self.assertEqual(apply_metadata_policy(r,readings)['predictions']['initial_owner'],'noc')
 def test_interpreters_do_not_receive_metadata_and_requests_are_deduplicated(self):
  p,_,_,_,texts,requests=prepare(self.profile());self.assertEqual(p['maximum_requests'],32)
  self.assertEqual(len({(q['reader'],q['text_id']) for q in requests}),32)
  self.assertEqual([q['reader'] for q in requests[:4]],['jev_original','jev_focal','jev_focal','jev_original'])
  by={t['text_id']:t for t in texts}
  for q in requests:
   self.assertEqual(q['body'],body(by[q['text_id']]['text'],q['reader']))
   for forbidden in ['measurement_scope','comparison_context','reference','metadata-fixture-secret']:self.assertNotIn(forbidden,json.dumps(q['body']))
  for profile in [{**self.profile(),'model':'jev-latest'},self.profile('http://untrusted.invalid'),{**self.profile(),'context_tokens':512}]:
   with self.assertRaises(ValueError):prepare(profile)
 def fixture(self,out,status=200,malformed=False):
  captured=[]
  class Handler(BaseHTTPRequestHandler):
   def do_POST(self):
    assert len(read_jsonl(out/'requests.jsonl'))==32
    b=json.loads(self.rfile.read(int(self.headers['Content-Length'])));captured.append(b);self.send_response(status);self.end_headers()
    text=b['state'];domain=next(d for d in ['core','transport','ran','power'] if 'Independent '+d in text);reading='normal' if 'normal' in text else 'fault';pred=dict(domain=domain,reading=reading)
    raw={'answers':{}} if malformed else {'model':MODEL,'note':'metadata-fixture-secret','answers':{f:dict(choice=pred[f],probabilities={k:float(k==pred[f]) for k in c}) for f,c in REPORT_CHOICES.items()}}
    self.wfile.write(json.dumps(raw).encode())
   def log_message(self,*a):pass
  server=HTTPServer(('127.0.0.1',0),Handler);worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
  try:s=run_hosted(out,self.profile('http://127.0.0.1:'+str(server.server_port)))
  finally:server.shutdown();server.server_close();worker.join()
  return s,captured
 def test_hosted_fixture_shares_actual_readings_and_records_redacts_verifies(self):
  with tempfile.TemporaryDirectory() as folder:
   out=Path(folder)/'run';s,captured=self.fixture(out);self.assertEqual(s['attempted_predictions'],32);self.assertEqual(s['failed_predictions'],0);verified,rows,*_=verify(out/'summary.json');self.assertEqual(verified,s)
   self.assertEqual(captured,[q['body'] for q in read_jsonl(out/'requests.jsonl')])
   for reader in ['jev_original','jev_focal']:
    for identifier,r in rows[reader+'__asset'].items():self.assertEqual(r['readings'],rows[reader+'__metadata'][identifier]['readings'])
    self.assertEqual(len(s['changes'][reader]['packets_fixed']),20);self.assertFalse(s['changes'][reader]['packets_lost'])
    self.assertEqual(s['report_metrics'][reader]['fields']['both']['correct_distinct_texts'],16);self.assertEqual(s['report_metrics'][reader]['fields']['both']['correct_occurrences'],96)
   for p in out.iterdir():self.assertNotIn('metadata-fixture-secret',p.read_text())
   with self.assertRaises(ValueError):run_hosted(out,self.profile())
   p=out/'report-inputs.jsonl';p.write_text(p.read_text()+'\n')
   with self.assertRaisesRegex(ValueError,'evidence'):verify(out/'summary.json')
 def test_shared_failures_keep_distinct_and_packet_denominators(self):
  for status,malformed,n in [(429,False,1),(200,True,3)]:
   with tempfile.TemporaryDirectory() as folder:
    out=Path(folder)/'run';s,captured=self.fixture(out,status,malformed);self.assertEqual(len(captured),n);self.assertEqual(s['unattempted_predictions'],32-n)
    for arm,m in s['approaches'].items():self.assertEqual(m['metrics']['records'],48)
    for r,m in s['report_metrics'].items():self.assertEqual(m['fields']['both']['distinct_texts'],16);self.assertEqual(m['fields']['both']['report_occurrences'],96);self.assertEqual(m['fields']['both']['correct_distinct_texts'],0)
    verify(out/'summary.json')
 def test_local_frozen_training_and_actual_saved_margins_verify(self):
  with tempfile.TemporaryDirectory() as folder:
   out=Path(folder)/'run';s=run_local(out);self.assertEqual(verify(out/'summary.json')[0],s)
   self.assertEqual(s['attempted_predictions'],48)
   for r in ['narrow','broad']:self.assertEqual(s['training_metadata'][r]['training_reports'],210);self.assertEqual(len(read_jsonl(out/(r+'.inspections.jsonl'))),16)
   with self.assertRaises(ValueError):run_local(out)
