import json,shutil,tempfile,threading,unittest,urllib.request,urllib.error
from pathlib import Path
from http.server import ThreadingHTTPServer
from types import SimpleNamespace
from urllib.parse import urlencode
from triage_bench.app import App,handler_for
from triage_bench.dataset import ROOT
from triage_bench.experiment3.report_language_data import DIRECTORY
from triage_bench.experiment3.report_language_service import ReportLanguageStudy
from triage_bench.study_page import render_study,return_path

class ReportLanguageServiceTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup);self.root=Path(self.folder.name)
        shutil.copytree(DIRECTORY,self.root/'data/report-language-draft')
        self.study=ReportLanguageStudy(self.root)

    def test_missing_runs_expose_matched_words_without_invented_predictions(self):
        catalog=self.study.catalog();self.assertIsNone(catalog['local']);self.assertIsNone(catalog['hosted']);self.assertIn('No saved local predictions',catalog['status'])
        id=catalog['cases']['train'][0]['id'];d=self.study.case(id,'train','broad')
        self.assertEqual(d['outputs'],{});self.assertIsNone(d['saved_response']);self.assertNotEqual(d['training_reports']['narrow'],d['training_reports']['broad'])
        self.assertNotIn('draft_reference',d['request']);self.assertNotIn('report_references',d['request'])
        self.assertIn('service probes',d['training_reports']['broad'][0]['text'])
        for arm in ['jev_direct','jev_reading','bridge']:
            d=self.study.case(catalog['cases']['development'][0]['id'],arm=arm);self.assertEqual(d['outputs'],{});self.assertIsNone(d['saved_response'])
        for kwargs in [{'arm':'bad'},{'report_index':True},{'report_index':-1},{'report_index':99},{'split':'held-out'}]:
            with self.assertRaises(ValueError):self.study.case(id,**kwargs)

    def test_reader_preserves_new_workbench_context_and_checkpoint_links(self):
        back='/report-language?split=development&case=NSL-c9841c3176a5-a&arm=jev_reading&report=0#weights'
        self.assertEqual(return_path(back),back);self.assertNotEqual(return_path('/report-language#unknown'),'/report-language#unknown')
        page=render_study(SimpleNamespace(root=ROOT,records={'validation':{'NS-b073aba91088':{}}}),{'doc':'report-language','return':back}).decode()
        self.assertIn('arm=jev_reading',page);self.assertIn('/report-language-protocol.json',page)

    def test_http_exports_exact_inputs_without_inference_or_reference_keys(self):
        app=App();app.root=self.root;server=ThreadingHTTPServer(('127.0.0.1',0),handler_for(app));worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
        base=f'http://127.0.0.1:{server.server_port}'
        try:
            for path,mime in [('/report-language','text/html'),('/report-language.js','text/javascript'),('/report-language.css','text/css')]:
                with urllib.request.urlopen(base+path) as response:self.assertTrue(response.headers['Content-Type'].startswith(mime));self.assertIn("script-src 'self'",response.headers['Content-Security-Policy'])
            id=self.study.catalog()['cases']['train'][0]['id'];q=urlencode({'id':id,'split':'train','arm':'broad','report':0})
            with urllib.request.urlopen(base+'/api/report-language/export?'+q) as response:
                self.assertIn(id,response.headers['Content-Disposition']);self.assertEqual(json.load(response),self.study.case(id,'train','broad')['request'])
            for path,status,headers in [('/api/report-language/case?id=bad',400,{}),('/api/report-language/catalog',403,{'Origin':'https://outside.example'}),('/report-language-jev.json',404,{})]:
                with self.assertRaises(urllib.error.HTTPError) as e:urllib.request.urlopen(urllib.request.Request(base+path,headers=headers))
                self.assertEqual(e.exception.code,status)
        finally:server.shutdown();server.server_close();worker.join()
