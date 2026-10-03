import json,shutil,tempfile,threading,unittest,urllib.request,urllib.error
from pathlib import Path
from http.server import ThreadingHTTPServer
from types import SimpleNamespace
from urllib.parse import urlencode
from triage_bench.app import App,handler_for
from triage_bench.dataset import ROOT
from triage_bench.experiment3.report_scope_data import DIRECTORY
from triage_bench.experiment3.report_scope_service import ReportScopeStudy
from triage_bench.experiment3.data import changed_paths
from triage_bench.study_page import render_study,return_path

class ReportScopeServiceTests(unittest.TestCase):
 def setUp(self):
  self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup);self.root=Path(self.folder.name);shutil.copytree(DIRECTORY,self.root/'data/report-scope-draft');self.study=ReportScopeStudy(self.root)
 def test_missing_runs_and_exact_question_change_without_answer_leak(self):
  c=self.study.catalog();self.assertIsNone(c['local']);self.assertIsNone(c['hosted']);self.assertIn('no saved responses',c['status']);self.assertEqual(len(c['cases']['development']),68)
  identifier=c['cases']['development'][0]['id'];old=self.study.case(identifier,arm='jev_original');new=self.study.case(identifier)
  self.assertFalse(new['outputs']);self.assertIsNone(new['saved_response']);gap=self.study.case(c['manifest']['known_policy_gaps'][0]);self.assertEqual(gap['reference_policy_diagnostic']['predictions']['initial_owner'],'noc');self.assertEqual(gap['draft_reference']['labels']['initial_owner'],'core');self.assertFalse(gap['outputs']);self.assertEqual(changed_paths(old['request'],new['request'],'request'),['request.questions.reading.instructions'])
  for forbidden in ['draft_reference','report_references','incident_family_id','known_policy_gap']:self.assertNotIn(forbidden,json.dumps(new['request']))
  for kwargs in [{'arm':'bad'},{'report_index':True},{'report_index':-1},{'report_index':99},{'split':'held-out'}]:
   with self.assertRaises(ValueError):self.study.case(identifier,**kwargs)
 def test_invalid_saved_evidence_stays_unavailable(self):
  run=self.root/'runs/report-scope-jev/fixture';run.mkdir(parents=True);(run/'summary.json').write_text('{}')
  c=ReportScopeStudy(self.root).catalog();self.assertIsNone(c['hosted']);self.assertIn('evidence differs',c['status'])
 def test_reader_links_and_local_origin_exports(self):
  back='/report-scope?case=NSS-ec1b69ec4685-a&arm=jev_focal&report=0#weights';self.assertEqual(return_path(back),back)
  page=render_study(SimpleNamespace(root=ROOT,records={'validation':{'NS-b073aba91088':{}}}),{'doc':'report-scope','return':back}).decode();self.assertIn('arm=jev_focal',page);self.assertIn('/report-scope-protocol.json',page);self.assertIn('/report-scope-jev.json',page)
  app=App();app.root=self.root;server=ThreadingHTTPServer(('127.0.0.1',0),handler_for(app));worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start();base=f'http://127.0.0.1:{server.server_port}'
  try:
   for path,mime in [('/report-scope','text/html'),('/report-scope.js','text/javascript')]:
    with urllib.request.urlopen(base+path) as response:self.assertTrue(response.headers['Content-Type'].startswith(mime));self.assertIn("script-src 'self'",response.headers['Content-Security-Policy'])
   identifier=self.study.catalog()['cases']['development'][0]['id'];q=urlencode({'id':identifier,'arm':'jev_focal','report':0})
   with urllib.request.urlopen(base+'/api/report-scope/export?'+q) as response:self.assertIn(identifier,response.headers['Content-Disposition']);self.assertEqual(json.load(response),self.study.case(identifier)['request'])
   for path,status,headers in [('/api/report-scope/case?id=bad',400,{}),('/api/report-scope/catalog',403,{'Origin':'https://outside.example'}),('/report-scope-jev.json',404,{})]:
    with self.assertRaises(urllib.error.HTTPError) as e:urllib.request.urlopen(urllib.request.Request(base+path,headers=headers))
    self.assertEqual(e.exception.code,status)
  finally:server.shutdown();server.server_close();worker.join()
