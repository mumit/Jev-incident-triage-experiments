import json,shutil,tempfile,threading,unittest,urllib.request,urllib.error
from pathlib import Path
from http.server import ThreadingHTTPServer
from types import SimpleNamespace
from urllib.parse import urlencode
from triage_bench.app import App,handler_for
from triage_bench.dataset import ROOT
from triage_bench.experiment3.metadata_data import DIRECTORY
from triage_bench.experiment3.metadata_service import MetadataStudy
from triage_bench.study_page import render_study,return_path

class MetadataServiceTests(unittest.TestCase):
 def setUp(self):
  self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup);self.root=Path(self.folder.name);shutil.copytree(DIRECTORY,self.root/'data/metadata-policy-draft');self.study=MetadataStudy(self.root)
 def test_missing_runs_shared_requests_and_separate_policy_diagnostics(self):
  c=self.study.catalog();self.assertIsNone(c['local']);self.assertIsNone(c['hosted']);self.assertEqual(len(c['cases']['development']),48)
  identifier=next(r['id'] for r in c['cases']['development'] if r['control']=='function' and r['id'].endswith('-a'))
  old=self.study.case(identifier,arm='jev_focal__asset');new=self.study.case(identifier)
  self.assertFalse(new['outputs']);self.assertIsNone(new['saved_response']);self.assertEqual(old['request'],new['request']);self.assertGreater(len(new['shared_report']['occurrences']),1)
  self.assertEqual(new['reference_policy_comparison']['asset']['predictions']['initial_owner'],'noc');self.assertNotEqual(new['reference_policy_comparison']['metadata']['predictions']['initial_owner'],'noc')
  self.assertIn('measurement_scope',new['policy_facts'])
  for forbidden in ['draft_reference','report_references','incident_family_id','measurement_scope','condition-A']:self.assertNotIn(forbidden,json.dumps(new['request']))
  for kwargs in [{'arm':'bad'},{'arm':'jev_focal'},{'report_index':True},{'report_index':-1},{'report_index':99},{'split':'held-out'}]:
   with self.assertRaises(ValueError):self.study.case(identifier,**kwargs)
 def test_invalid_saved_evidence_stays_unavailable(self):
  run=self.root/'runs/metadata-policy-jev/fixture';run.mkdir(parents=True);(run/'summary.json').write_text('{}')
  c=MetadataStudy(self.root).catalog();self.assertIsNone(c['hosted']);self.assertIn('evidence differs',c['status'])
 def test_reader_context_and_guarded_exact_exports(self):
  back='/metadata-policy?case=NMP-db6cbccd8070-a&arm=jev_focal__metadata&report=1#weights';self.assertEqual(return_path(back),back)
  page=render_study(SimpleNamespace(root=ROOT,records={'validation':{'NS-b073aba91088':{}}}),{'doc':'metadata-policy','return':back}).decode();self.assertIn('arm=jev_focal__metadata',page);self.assertIn('/metadata-policy-protocol.json',page);self.assertIn('/metadata-policy-jev.json',page)
  review=render_study(SimpleNamespace(root=ROOT,records={'validation':{'NS-b073aba91088':{}}}),{'doc':'metadata-domain-review'}).decode();self.assertIn('href="/metadata-policy?case=NMP-99de43f119cf-a',review)
  app=App();app.root=self.root;server=ThreadingHTTPServer(('127.0.0.1',0),handler_for(app));worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start();base=f'http://127.0.0.1:{server.server_port}'
  try:
   for path,mime in [('/metadata-policy','text/html'),('/metadata-policy.js','text/javascript')]:
    with urllib.request.urlopen(base+path) as response:self.assertTrue(response.headers['Content-Type'].startswith(mime));self.assertIn("script-src 'self'",response.headers['Content-Security-Policy'])
   identifier=self.study.catalog()['cases']['development'][0]['id']
   for policy in ['asset','metadata']:
    q=urlencode({'id':identifier,'arm':'jev_focal__'+policy,'report':1})
    with urllib.request.urlopen(base+'/api/metadata-policy/export?'+q) as response:self.assertIn(identifier,response.headers['Content-Disposition']);self.assertEqual(json.load(response),self.study.case(identifier,arm='jev_focal__'+policy,report_index=1)['request'])
   for path,status,headers in [('/api/metadata-policy/case?id=bad',400,{}),('/api/metadata-policy/catalog',403,{'Origin':'https://outside.example'}),('/metadata-policy-jev.json',404,{})]:
    with self.assertRaises(urllib.error.HTTPError) as e:urllib.request.urlopen(urllib.request.Request(base+path,headers=headers))
    self.assertEqual(e.exception.code,status)
  finally:server.shutdown();server.server_close();worker.join()
