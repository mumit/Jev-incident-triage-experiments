import copy,json,tempfile,threading,unittest
from http.server import BaseHTTPRequestHandler,HTTPServer
from pathlib import Path
from triage_bench.dataset import read_jsonl
from triage_bench.experiment3.data import changed_paths
from triage_bench.experiment3.report_scope_data import build,validate,DIRECTORY
from triage_bench.experiment3.report_scope_trial import body,prepare,diagnostic,run_local,run_hosted,verify,aggregate,report_changes
from triage_bench.experiment3.report_language_hosted import REPORT_CHOICES,report_body
from triage_bench.experiment3.interpretation_model import report_inputs
from triage_bench.experiment3.transforms import MODEL

class ReportScopeTests(unittest.TestCase):
 def profile(self,endpoint='https://api.typesafe.ai/v1/systemone'):
  return dict(endpoint=endpoint,model=MODEL,context_tokens=32768,api_key='scope-fixture-secret')
 def test_reproducible_pack_and_predeclared_policy_gap(self):
  with tempfile.TemporaryDirectory() as folder:
   manifest=build(Path(folder)/'data');self.assertEqual(manifest,json.loads((DIRECTORY/'manifest.json').read_text()))
   self.assertEqual(validate()['records'],68);self.assertEqual(validate()['reports'],88)
   _,records,keys,ann,_=prepare(self.profile());rows,diag=diagnostic(records,ann,keys)
   self.assertEqual(diag['mismatched_packets'],manifest['known_policy_gaps']);self.assertEqual(len(diag['mismatched_packets']),2)
   for r in records:
    if r['id'] in diag['mismatched_packets']:
     self.assertEqual([a['reading'] for a in ann if a['id']==r['id']],['fault','normal'])
     self.assertEqual(next(x for x in rows if x['id']==r['id'])['predictions']['initial_owner'],'noc')
     self.assertEqual(next(k for k in keys if k['id']==r['id'])['labels']['initial_owner'],'core')
 def test_measured_scope_and_expected_rejection_references_remain_separate(self):
  _,records,keys,ann,_=prepare(self.profile());by={k['id']:k for k in keys}
  for family,states in [('core intake scope versus completion scope',['normal','unknown']),('core credential gate expected rejection versus malfunction',['normal','fault']),('core batch admission partial malfunction',['normal','fault'])]:
   ids=[r['id'] for r in records if by[r['id']]['incident_family_id']==family][:2]
   self.assertEqual([a['reading'] for a in ann if a['id'] in ids],states)
   if 'scope versus' in family:self.assertEqual(by[ids[0]]['labels'],by[ids[1]]['labels'])
 def test_only_reading_instruction_changes_and_wire_order_is_matched(self):
  p,records,_,_,requests=prepare(self.profile());self.assertEqual(p['maximum_requests'],176)
  for i in range(0,len(requests),2):
   qs=requests[i:i+2];self.assertEqual(qs[0]['id'],qs[1]['id']);self.assertEqual(qs[0]['observation_index'],qs[1]['observation_index'])
   self.assertEqual(changed_paths(qs[0]['body'],qs[1]['body'],'request'),['request.questions.reading.instructions'])
   old=next(q for q in qs if q['arm']=='jev_original');self.assertEqual(old['body'],report_body(old['body']['state'].removeprefix('Report text only:\n')))
  self.assertEqual([q['arm'] for q in requests[:4]],['jev_original','jev_focal','jev_focal','jev_original'])
  self.assertNotIn('scope-fixture-secret',json.dumps(p));self.assertNotIn('review_status',json.dumps(requests))
  for profile in [{**self.profile(),'model':'jev-latest'},self.profile('http://untrusted.invalid'),{**self.profile(),'context_tokens':512}]:
   with self.assertRaises(ValueError):prepare(profile)
 def fixture(self,out,status=200,malformed=False):
  captured=[]
  class Handler(BaseHTTPRequestHandler):
   def do_POST(self):
    assert len(read_jsonl(out/'requests.jsonl'))==176
    b=json.loads(self.rfile.read(int(self.headers['Content-Length'])));captured.append(b);self.send_response(status);self.end_headers()
    raw={'answers':{}} if malformed else {'model':MODEL,'note':'scope-fixture-secret','answers':{f:{'choice':('none' if f=='domain' else 'unknown'),'probabilities':{k:1/len(c) for k in c}} for f,c in REPORT_CHOICES.items()}}
    self.wfile.write(json.dumps(raw).encode())
   def log_message(self,*a):pass
  server=HTTPServer(('127.0.0.1',0),Handler);t=threading.Thread(target=server.serve_forever,daemon=True);t.start()
  try:s=run_hosted(out,self.profile('http://127.0.0.1:'+str(server.server_port)))
  finally:server.shutdown();server.server_close();t.join()
  return s,captured
 def test_hosted_fixture_saved_before_calls_redacted_verified_immutable(self):
  with tempfile.TemporaryDirectory() as folder:
   out=Path(folder)/'run';s,bodies=self.fixture(out);self.assertEqual(s['attempted_requests'],176);self.assertEqual(s['failed_requests'],0)
   self.assertEqual(bodies,[q['body'] for q in read_jsonl(out/'requests.jsonl')]);self.assertEqual(verify(out/'summary.json')[0],s)
   for p in out.iterdir():self.assertNotIn('scope-fixture-secret',p.read_text())
   with self.assertRaises(ValueError):run_hosted(out,self.profile())
   p=out/'responses.jsonl';p.write_text(p.read_text()+'\n')
   with self.assertRaisesRegex(ValueError,'evidence'):verify(out/'summary.json')
 def test_failure_stops_keep_full_denominators_and_incomplete_packets(self):
  for status,malformed,n in [(429,False,1),(200,True,3)]:
   with tempfile.TemporaryDirectory() as folder:
    out=Path(folder)/'run';s,c=self.fixture(out,status,malformed);self.assertEqual(len(c),n);self.assertEqual(s['unattempted_requests'],176-n)
    for arm in ['jev_original','jev_focal']:
     self.assertEqual(s['approaches'][arm]['metrics']['records'],68);self.assertEqual(s['report_metrics'][arm]['fields']['both']['reports'],88);self.assertEqual(s['report_metrics'][arm]['fields']['both']['correct'],0)
    verify(out/'summary.json')
  _,records,_,_,_=prepare(self.profile());r=next(r for r in records if len(report_inputs(r))==2)
  result=aggregate([r],[dict(id=r['id'],arm='jev_focal',observation_index=0,status='ok',predictions={'domain':'core','reading':'fault'},probabilities={})])
  self.assertEqual(result['jev_focal'][0]['status'],'error');self.assertFalse(result['jev_focal'][0]['predictions']);self.assertFalse(result['jev_original'])
 def test_local_controls_fit_only_frozen_training_and_verify_saved_margins(self):
  with tempfile.TemporaryDirectory() as folder:
   out=Path(folder)/'run';s=run_local(out);self.assertEqual(verify(out/'summary.json')[0],s)
   self.assertEqual(len(s['reference_policy_diagnostic']['mismatched_packets']),2)
   for arm in ['narrow','broad']:
    self.assertEqual(s['approaches'][arm]['training']['training_reports'],210)
   with self.assertRaises(ValueError):run_local(out)
 def test_field_regression_on_already_wrong_report_is_retained(self):
  ann=[dict(id='x',observation_index=0,domain='core',reading='normal')]
  responses=[dict(id='x',observation_index=0,arm=a,status='ok',predictions=dict(domain=d,reading='fault')) for a,d in [('jev_original','core'),('jev_focal','power')]]
  result=report_changes(responses,ann);self.assertFalse(result['reports_lost']);self.assertEqual(result['newly_wrong_domain'],[dict(id='x',observation_index=0)])
