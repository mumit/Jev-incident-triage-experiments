import copy,json,tempfile,threading,unittest
from pathlib import Path
from http.server import BaseHTTPRequestHandler,HTTPServer
from triage_bench.dataset import read_jsonl
from triage_bench.experiment3.declared_data import DIRECTORY,build,validate,declaration_fact
from triage_bench.experiment3.declared_trial import prepare,body,aggregate,diagnostic,run_local,run_hosted,verify,domain_controls
from triage_bench.experiment3.report_scope_trial import body as frozen_body
from triage_bench.experiment3.report_language_hosted import REPORT_CHOICES
from triage_bench.experiment3.data import changed_paths
from triage_bench.experiment3.transforms import MODEL

class DeclaredDomainTests(unittest.TestCase):
 def profile(self,endpoint='https://api.typesafe.ai/v1/systemone'):return dict(endpoint=endpoint,model=MODEL,context_tokens=32768,api_key='declared-fixture-secret')
 def test_fresh_reproducible_pack_and_independent_reference_diagnostic(self):
  with tempfile.TemporaryDirectory() as folder:self.assertEqual(build(Path(folder)/'data'),json.loads((DIRECTORY/'manifest.json').read_text()))
  p,records,keys,ann,texts,_=prepare(self.profile());self.assertEqual(validate(),dict(records=64,reports=128,families=16,pairs=32,distinct_report_texts=30));self.assertEqual(p['prepared_reference_diagnostic']['reference_matches'],64)
  refs={k['id']:k['labels'] for k in keys}
  for r in diagnostic(records,ann):self.assertEqual(r['predictions'],refs[r['id']])
 def test_only_domain_definition_changes_and_no_structured_policy_or_references_enter_requests(self):
  p,records,keys,ann,texts,qs=prepare(self.profile());self.assertEqual(len(qs),60);self.assertEqual(len({(q['reader'],q['text_id']) for q in qs}),60);self.assertEqual([q['reader'] for q in qs[:4]],['jev_focal','jev_declared','jev_declared','jev_focal'])
  for t in texts:
   a=body(t['text'],'jev_focal');b=body(t['text'],'jev_declared');self.assertEqual(a,frozen_body(t['text'],'jev_focal'));self.assertEqual(a['state'],b['state']);self.assertEqual(a['questions']['reading'],b['questions']['reading']);self.assertTrue(all(x.startswith('request.questions.domain.') for x in changed_paths(a,b,'request')))
   for forbidden in ['instrument_domain','measurement_scope','affected_sites','observation_references','incident_family_id','declared-fixture-secret']:self.assertNotIn(forbidden,json.dumps(b))
  for profile in [{**self.profile(),'model':'jev-latest'},self.profile('http://untrusted.invalid'),{**self.profile(),'context_tokens':512}]:
   with self.assertRaises(ValueError):prepare(profile)
 def test_software_uses_only_valid_declaration_and_never_interprets_fault(self):
  for value in [None,'ran',{},dict(status='declared',domain=[]),dict(status='declared',domain='radio'),dict(status='ambiguous',domain='ran')]:self.assertEqual(declaration_fact({'instrument_domain':value})['domain'],'none')
  _,records,_,_,texts,_=prepare(self.profile());t=texts[0];responses=[dict(reader='jev_focal',text_id=t['text_id'],status='ok',predictions=dict(domain='none',reading='unknown'),probabilities=dict(domain={'none':1},reading={'unknown':1}),provider_confidence={'domain':.8,'reading':.6})];before=copy.deepcopy(responses);d=domain_controls(records,texts,responses)[1];self.assertEqual(responses,before);self.assertNotEqual(d['predictions']['domain'],'none');self.assertEqual(d['predictions']['reading'],'unknown');self.assertNotIn('domain',d['probabilities']);self.assertNotIn('domain',d['provider_confidence'])
  records=copy.deepcopy(records)
  for r in records:
   for o in r['input']['observations']:o['detail']='power failed radio unknown'
  self.assertEqual(domain_controls(records,texts,responses)[1],d)
 def fixture(self,out,status=200,malformed=False):
  captured=[]
  class Handler(BaseHTTPRequestHandler):
   def do_POST(self):
    assert len(read_jsonl(out/'requests.jsonl'))==60
    b=json.loads(self.rfile.read(int(self.headers['Content-Length'])));captured.append(b);self.send_response(status);self.end_headers();text=b['state'];domain=next((d for d in ['core','transport','ran','power'] if 'Instrument domain: '+d+'.' in text),'none');reading='normal' if 'records normal execution' in text else 'fault'
    if b['questions']['domain']['instructions'].startswith('Interpret'):domain='none'
    pred=dict(domain=domain,reading=reading);raw={'answers':{}} if malformed else {'model':MODEL,'note':'declared-fixture-secret','answers':{f:dict(choice=pred[f],probabilities={k:float(k==pred[f]) for k in c}) for f,c in REPORT_CHOICES.items()}};self.wfile.write(json.dumps(raw).encode())
   def log_message(self,*a):pass
  server=HTTPServer(('127.0.0.1',0),Handler);worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
  try:s=run_hosted(out,self.profile('http://127.0.0.1:'+str(server.server_port)))
  finally:server.shutdown();server.server_close();worker.join()
  return s,captured
 def test_recording_redaction_matched_software_readings_and_verified_metrics(self):
  with tempfile.TemporaryDirectory() as folder:
   out=Path(folder)/'run';s,cap=self.fixture(out);self.assertEqual(s['attempted_predictions'],60);self.assertEqual(s['failed_predictions'],0);self.assertEqual(verify(out/'summary.json')[0],s);self.assertEqual(cap,[q['body'] for q in read_jsonl(out/'requests.jsonl')]);self.assertEqual(s['report_metrics']['jev_declared']['fields']['both']['correct_distinct_texts'],30)
   self.assertEqual(s['approaches']['jev_declared']['metrics']['all_fields_accuracy'],1);self.assertEqual(s['approaches']['jev_focal_fact']['metrics']['all_fields_accuracy'],1)
   _,rows,*_=verify(out/'summary.json')
   for reader in ['jev_focal','jev_declared']:
    for identifier,r in rows[reader].items():self.assertEqual([o['reading'] for o in r['readings']],[o['reading'] for o in rows[reader+'_fact'][identifier]['readings']])
   for p in out.iterdir():self.assertNotIn('declared-fixture-secret',p.read_text())
   with self.assertRaises(ValueError):run_hosted(out,self.profile())
   p=out/'jev_focal_fact.jsonl';p.write_text(p.read_text()+'\n')
   with self.assertRaisesRegex(ValueError,'evidence'):verify(out/'summary.json')
 def test_failures_do_not_become_valid_through_software_domain(self):
  for status,malformed,n in [(429,False,1),(200,True,3)]:
   with tempfile.TemporaryDirectory() as folder:
    out=Path(folder)/'run';s,cap=self.fixture(out,status,malformed);self.assertEqual(len(cap),n);self.assertEqual(s['unattempted_predictions'],60-n)
    for arm,m in s['approaches'].items():self.assertEqual(m['metrics']['records'],64);self.assertEqual(m['metrics']['all_fields_accuracy'],0)
    for reader,m in s['report_metrics'].items():self.assertEqual(m['fields']['both']['distinct_texts'],30);self.assertEqual(m['fields']['both']['correct_distinct_texts'],0)
    verify(out/'summary.json')
 def test_local_models_keep_frozen_training_and_save_actual_margins(self):
  with tempfile.TemporaryDirectory() as folder:
   out=Path(folder)/'run';s=run_local(out);self.assertEqual(verify(out/'summary.json')[0],s);self.assertEqual(s['attempted_predictions'],90)
   for r in ['narrow','broad']:self.assertEqual(s['training_metadata'][r]['training_reports'],210);self.assertEqual(len(read_jsonl(out/(r+'.inspections.jsonl'))),30)
   with self.assertRaises(ValueError):run_local(out)
