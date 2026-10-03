import json,shutil,tempfile,threading,unittest,urllib.request,urllib.error
from pathlib import Path
from http.server import ThreadingHTTPServer
from types import SimpleNamespace
from urllib.parse import urlencode
from triage_bench.app import App,handler_for
from triage_bench.dataset import ROOT
from triage_bench.experiment3.declared_data import DIRECTORY
from triage_bench.experiment3.declared_service import DeclaredStudy
from triage_bench.study_page import render_study,return_path

class DeclaredServiceTests(unittest.TestCase):
 def setUp(self):
  self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup);self.root=Path(self.folder.name);shutil.copytree(DIRECTORY,self.root/'data/declared-domain-draft');self.study=DeclaredStudy(self.root)
 def test_missing_results_and_software_source_preserves_exact_interpreter_request(self):
  c=self.study.catalog();self.assertIsNone(c['local']);self.assertIsNone(c['hosted']);self.assertEqual(len(c['cases']['development']),64)
  identifier=c['cases']['development'][0]['id'];base=self.study.case(identifier);sw=self.study.case(identifier,arm='jev_declared_fact');old=self.study.case(identifier,arm='jev_focal')
  self.assertFalse(sw['outputs']);self.assertIsNone(sw['saved_response']);self.assertEqual(base['request'],sw['request']);self.assertEqual(base['request']['state'],old['request']['state']);self.assertEqual(base['request']['questions']['reading'],old['request']['questions']['reading']);self.assertNotEqual(base['request']['questions']['domain'],old['request']['questions']['domain']);self.assertGreater(len(sw['shared_report']['occurrences']),1)
  self.assertEqual(sw['reference_policy_diagnostic']['predictions'],sw['draft_reference']['labels']);self.assertIn('instrument_domain',sw['policy_facts'])
  for forbidden in ['draft_reference','report_references','incident_family_id','measurement_scope','instrument_domain']:self.assertNotIn(forbidden,json.dumps(sw['request']))
  for kwargs in [{'arm':'bad'},{'report_index':True},{'report_index':-1},{'report_index':99},{'split':'held-out'}]:
   with self.assertRaises(ValueError):self.study.case(identifier,**kwargs)
 def test_invalid_saved_evidence_stays_unavailable(self):
  run=self.root/'runs/declared-domain-jev/fixture';run.mkdir(parents=True);(run/'summary.json').write_text('{}')
  c=DeclaredStudy(self.root).catalog();self.assertIsNone(c['hosted']);self.assertIn('evidence differs',c['status'])
 def test_reader_context_and_guarded_exact_exports(self):
  identifier=self.study.catalog()['cases']['development'][0]['id'];back=f'/declared-domain?case={identifier}&arm=jev_declared_fact&report=1#weights';self.assertEqual(return_path(back),back)
  page=render_study(SimpleNamespace(root=ROOT,records={'validation':{'NS-b073aba91088':{}}}),{'doc':'declared-domain','return':back}).decode();self.assertIn('arm=jev_declared_fact',page);self.assertIn('/declared-domain-protocol.json',page)
  app=App();app.root=self.root;server=ThreadingHTTPServer(('127.0.0.1',0),handler_for(app));worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start();base=f'http://127.0.0.1:{server.server_port}'
  try:
   for path,mime in [('/declared-domain','text/html'),('/declared-domain.js','text/javascript')]:
    with urllib.request.urlopen(base+path) as response:self.assertTrue(response.headers['Content-Type'].startswith(mime));self.assertIn("script-src 'self'",response.headers['Content-Security-Policy'])
   for arm in ['jev_declared','jev_declared_fact']:
    q=urlencode({'id':identifier,'arm':arm,'report':1})
    with urllib.request.urlopen(base+'/api/declared-domain/export?'+q) as response:self.assertIn(identifier,response.headers['Content-Disposition']);self.assertEqual(json.load(response),self.study.case(identifier,arm=arm,report_index=1)['request'])
   for path,status,headers in [('/api/declared-domain/case?id=bad',400,{}),('/api/declared-domain/catalog',403,{'Origin':'https://outside.example'}),('/declared-domain-jev.json',404,{})]:
    with self.assertRaises(urllib.error.HTTPError) as e:urllib.request.urlopen(urllib.request.Request(base+path,headers=headers))
    self.assertEqual(e.exception.code,status)
  finally:server.shutdown();server.server_close();worker.join()
