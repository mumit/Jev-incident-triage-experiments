import copy,json,math,tempfile,unittest
from pathlib import Path
from triage_bench.dataset import read_jsonl
from triage_bench.experiment3.interpretation_data import DIRECTORY,build,validate
from triage_bench.experiment3.interpretation_model import ReportClassifier,report_inputs,pipeline_input,apply_policy,rule_reading
from triage_bench.experiment3.interpretation_trial import run,verify,report_metrics,matched_changes

class InterpretationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records=read_jsonl(DIRECTORY/'development.inputs.jsonl');cls.keys={r['id']:r for r in read_jsonl(DIRECTORY/'development.labels.jsonl')}
        cls.annotations={}
        for a in read_jsonl(DIRECTORY/'development.observations.jsonl'):cls.annotations.setdefault(a['id'],[]).append(a)
        cls.reader=ReportClassifier()

    def test_pack_is_reproducible_and_report_references_are_distinct_from_triage(self):
        self.assertEqual(validate(),{'train':186,'development':108,'observations':{'train':210,'development':124}})
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'pack';build(path)
            for p in DIRECTORY.glob('*'):self.assertEqual(p.read_bytes(),(path/p.name).read_bytes())
        for r in self.records:
            key=self.keys[r['id']]
            if key['incident_family_id'].endswith('age') and r['id'].endswith('-b'):
                self.assertEqual(key['labels']['initial_owner'],'noc');self.assertEqual(self.annotations[r['id']][0]['reading'],'fault')

    def test_reader_input_excludes_policy_context_and_reference_fields(self):
        r=copy.deepcopy(self.records[0]);before=report_inputs(r);r['labels']={'initial_owner':'core'};r['input']['reference_answer']='core'
        r['input']['observations'][0]['domain']='core';r['input']['observations'][0]['reading']='normal';r['input']['observations'][0]['measured_at']=None
        r['input']['topology']={};r['input']['service_impact']['affected_sites']=100
        self.assertEqual(before,report_inputs(r));self.assertNotIn('reference_answer',json.dumps(pipeline_input(r)))
        r['input']['observations'][0]['detail']='developmentonlysentinel';self.reader.predict(r)
        self.assertNotIn('developmentonlysentinel',self.reader.words.vocabulary_)

    def test_policy_reference_readings_match_prewritten_teaching_decisions(self):
        for r in self.records:self.assertEqual(apply_policy(r,self.annotations[r['id']])['predictions'],self.keys[r['id']]['labels'])

    def test_policy_uses_currentness_paths_and_keeps_conflicts(self):
        pair=[r for r in self.records if self.keys[r['id']]['incident_family_id']=='cabinet voltage probe conflict'][:2]
        a,b=[apply_policy(r,self.annotations[r['id']]) for r in pair]
        self.assertEqual(a['predictions']['initial_owner'],'noc');self.assertTrue(a['trace']['current_conflicts'])
        self.assertEqual(b['predictions']['initial_owner'],'power');self.assertFalse(b['trace']['current_conflicts'])
        r=copy.deepcopy(pair[1]);r['input']['topology']={};self.assertEqual(apply_policy(r,self.annotations[r['id']])['predictions']['initial_owner'],'noc')
        with self.assertRaises(ValueError):apply_policy(r,[])
        with self.assertRaises(ValueError):apply_policy(r,[{**x,'observation_index':9} for x in self.annotations[r['id']]])

    def test_rule_negation_and_uncertainty_precede_fault_words(self):
        self.assertEqual(rule_reading('Power tests report supply is not failing; checks pass.',0)['reading'],'normal')
        self.assertEqual(rule_reading('Power supply failure is suspected; the measurement is inconclusive.',0)['reading'],'unknown')
        self.assertEqual(rule_reading('Power supply is absent.',0)['reading'],'fault')
        self.assertEqual(rule_reading('Unclassified telemetry.',0)['domain'],'none')

    def test_report_explanations_reconstruct_probabilities_and_vectors(self):
        text=report_inputs(self.records[0])[0]['text'];inspection=self.reader.inspect(text);vector={v['feature']:v['value'] for v in inspection['vector']['nonzero']}
        for e in inspection['fields'].values():
            margin=e['intercept_difference']+sum(v['contribution'] for v in e['top_contributions'])+e['remaining_contribution']
            self.assertAlmostEqual(margin,math.log(e['probabilities'][e['selected']]/e['probabilities'][e['compared_with']]),places=8)
            for c in e['top_contributions']:self.assertAlmostEqual(c['value'],vector[c['feature']]);self.assertAlmostEqual(c['value']*c['coefficient_difference'],c['contribution'])

    def test_evidence_is_immutable_and_policy_attribution_is_verified(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)/'run';s=run(out);self.assertEqual(s,verify(out/'summary.json')[0]);self.assertIn('not model performance',s['reference_policy_diagnostic']['label'])
            with self.assertRaises(ValueError):run(out)
            p=out/'reading.jsonl';p.write_text(p.read_text()+'\n')
            with self.assertRaisesRegex(ValueError,'evidence'):verify(out/'summary.json')

    def test_correct_triage_can_hide_a_wrong_report_interpretation(self):
        truth={'initial_owner':'noc','priority':'P2','next_check':'gather_evidence','insufficient_evidence':'yes'}
        rows={a:{'case':{'predictions':truth,'readings':[{'observation_index':0,'domain':'power','reading':'unknown'}]}} for a in ['reading','reading_rules']}
        ann=[{'id':'case','observation_index':0,'domain':'power','reading':'fault'}];keys={'case':{'accepted_answers':{f:[v] for f,v in truth.items()}}}
        d=report_metrics(rows,ann,keys)['reading'];self.assertEqual(d['fields']['both']['correct'],0);self.assertEqual(d['attribution']['readings_wrong_triage_correct'],['case'])

    def test_missing_run_keeps_boundaries_and_references_separate(self):
        import shutil
        from triage_bench.experiment3.interpretation_service import InterpretationStudy
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);shutil.copytree(DIRECTORY,root/'data/experiment-3-interpretation-draft');study=InterpretationStudy(root)
            self.assertIsNone(study.catalog()['pilot'])
            identifier=next(iter(study.records['train']))
            case=study.case(identifier,'reading','train')
            self.assertFalse(case['outputs']);self.assertIsNone(case['pipeline']);self.assertIsNone(case['report_inspections'])
            self.assertIsNone(case['request']['fitted_report_vectors'])
            self.assertEqual(case['request']['reports'],report_inputs(case['record']))
            self.assertNotIn('report_references',case['request']);self.assertNotIn('draft_reference',case['request'])
            self.assertTrue(case['report_references'])
            with self.assertRaises(ValueError):study.case(identifier,'invented','train')

    def test_http_exports_preserve_interpreter_boundary_and_guide_links(self):
        import threading,urllib.request
        from http.server import ThreadingHTTPServer
        from triage_bench.app import App,handler_for
        server=ThreadingHTTPServer(('127.0.0.1',0),handler_for(App()));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url='http://127.0.0.1:'+str(server.server_port)
        try:
            with urllib.request.urlopen(url+'/api/experiment3/catalog?trial=interpretation') as r:catalog=json.load(r)
            self.assertEqual(catalog['manifest']['splits']['development']['records'],108);self.assertIsNone(catalog['hosted_pilot'])
            identifier=catalog['cases']['train'][0]['id']
            with urllib.request.urlopen(url+'/api/experiment3/export?trial=interpretation&split=train&variant=reading&id='+identifier) as r:bundle=json.load(r)
            self.assertEqual(bundle['inference_arm'],'reading');self.assertIn('policy_inputs',bundle)
            self.assertIsNone(bundle['fitted_report_vectors']);self.assertNotIn('questions',bundle);self.assertNotIn('report_references',bundle)
            with urllib.request.urlopen(url+'/study?doc=experiment-3-interpretation') as r:html=r.read().decode()
            self.assertIn('/experiment-3-interpretation-report.json',html);self.assertNotIn('checkpoints/experiment-3-interpretation',html)
            with urllib.request.urlopen(url+'/experiment-3-interpretation-report.json') as r:report=json.load(r)
            self.assertEqual(report['development_packets'],108)
        finally:server.shutdown();server.server_close();thread.join()
