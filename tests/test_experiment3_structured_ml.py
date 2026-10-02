import copy,json,math,tempfile,unittest
from pathlib import Path
import numpy as np
from triage_bench.dataset import read_jsonl
from triage_bench.experiment3.structured_data import DIRECTORY,build,validate
from triage_bench.experiment3.structured_features import ARMS,descriptors
from triage_bench.experiment3.structured_ml import FeatureSpace,StructuredClassifier,run,verify

class StructuredMLTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.train=read_jsonl(DIRECTORY/'train.inputs.jsonl');cls.dev=read_jsonl(DIRECTORY/'development.inputs.jsonl')
        cls.space=FeatureSpace(cls.train);cls.model=StructuredClassifier('combined',space=cls.space)

    def test_pack_rebuilds_with_disjoint_families_and_single_interventions(self):
        self.assertEqual(validate(),{'train':96,'development':64})
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'pack';build(path)
            for name in ['manifest.json','train.inputs.jsonl','train.labels.jsonl','development.inputs.jsonl','development.labels.jsonl']:
                self.assertEqual((path/name).read_bytes(),(DIRECTORY/name).read_bytes())
        families=[{k['incident_family_id'] for k in read_jsonl(DIRECTORY/(s+'.labels.jsonl'))} for s in ['train','development']]
        self.assertFalse(families[0]&families[1])

    def test_features_allowlist_metadata_and_do_not_mutate_inputs(self):
        source=copy.deepcopy(self.dev[0]);before=copy.deepcopy(source);original=descriptors(source,'combined')
        source['labels']={'initial_owner':'core'};source['incident_family_id']='leaked-family';source['input']['reference_decision']='core'
        source['input']['observations'][0]['reference_answer']='core'
        self.assertEqual(descriptors(source,'combined'),original)
        self.assertEqual(before,self.dev[0]);self.assertNotIn('leaked-family',json.dumps(original))
        for arm in ARMS:
            self.assertEqual(descriptors(self.dev[0],arm)['state'],original['state'])

    def test_pair_changes_are_bound_to_the_correct_observation(self):
        keys={k['id']:k for k in read_jsonl(DIRECTORY/'development.labels.jsonl')}
        family='cabinet output circuit instrument disagreement'
        pair=[r for r in self.dev if keys[r['id']]['incident_family_id']==family][:2]
        a,b=[descriptors(r,'combined') for r in pair]
        self.assertEqual(a['state'],b['state'])
        self.assertEqual(a['observations'][0]['bucket'],b['observations'][0]['bucket'])
        self.assertEqual((a['observations'][1]['bucket'],b['observations'][1]['bucket']),('supported/current','supported/stale'))
        self.assertIn('normal',b['observations'][1]['text'])
        reverse=copy.deepcopy(pair[1]);reverse['input']['observations'].reverse()
        x=self.space.matrix([pair[1],reverse],'combined');start=len(self.space.names('baseline'))
        self.assertLess(abs(x[0,start:]-x[1,start:]).sum(),1e-10)

    def test_vocabularies_are_fit_only_on_training_and_unknowns_stay_unknown(self):
        copy_record=copy.deepcopy(self.dev[0]);copy_record['input']['observations'][0]['detail']='developmentonlysentinel'
        before=self.space.words.vocabulary_.copy();self.model.predict(copy_record)
        self.assertEqual(before,self.space.words.vocabulary_);self.assertNotIn('developmentonlysentinel',before)
        copy_record['input']['observations'][0]['measured_at']=None;copy_record['input']['topology']={}
        self.assertEqual(descriptors(copy_record,'combined')['observations'][0]['bucket'],'unknown/unknown')
        self.assertNotIn('developmentonlysentinel',self.space.obs_words.vocabulary_)

    def test_priority_is_shared_and_score_explanation_reconstructs_log_odds(self):
        baseline=StructuredClassifier('baseline',space=self.space)
        for r in [self.dev[0],self.dev[-1]]:
            self.assertEqual(baseline.predict(r)['probabilities']['priority'],self.model.predict(r)['probabilities']['priority'])
            for field in ['initial_owner','next_check','insufficient_evidence','priority']:
                e=self.model.explain(r,field,limit=7);p=e['probabilities']
                reconstructed=e['intercept_difference']+sum(v['contribution'] for v in e['top_contributions'])+e['remaining_contribution']
                self.assertAlmostEqual(reconstructed,e['log_odds_margin'],places=8)
                self.assertAlmostEqual(e['log_odds_margin'],math.log(p[e['selected']]/p[e['compared_with']]),places=8)
        # The baseline retains the earlier training recipe and compact input.
        from triage_bench.experiment3.local import PilotClassifier
        old_recipe=PilotClassifier('baseline',DIRECTORY)
        for r in [self.dev[0],self.dev[-1]]:
            self.assertEqual(old_recipe.predict(r)['predictions'],baseline.predict(r)['predictions'])
            for field in old_recipe.heads:
                for label,p in old_recipe.predict(r)['probabilities'][field].items():self.assertAlmostEqual(p,baseline.predict(r)['probabilities'][field][label],places=10)

    def test_run_is_immutable_and_saved_scores_and_explanations_are_verified(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)/'run';s=run(out);saved,rows,explanations=verify(out/'summary.json')
            self.assertEqual(s,saved);self.assertEqual(set(rows),{*ARMS,'rules'});self.assertEqual(len(explanations['combined']),64)
            self.assertEqual(len({json.dumps(v['training']['parameters'],sort_keys=True) for a,v in s['approaches'].items() if a!='rules'}),1)
            with self.assertRaises(ValueError):run(out)
            p=out/'combined.explanations.jsonl';p.write_text(p.read_text()+'\n')
            with self.assertRaisesRegex(ValueError,'evidence'):verify(out/'summary.json')

    def test_missing_results_expose_prepared_features_without_training_predictions(self):
        from triage_bench.experiment3.structured_service import StructuredStudy
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);build(root/'data/experiment-3-structured-ml-draft');study=StructuredStudy(root)
            self.assertIsNone(study.catalog()['pilot'])
            case=study.case(self.dev[0]['id'],'combined');self.assertIsNone(case['request']['fitted_vector']);self.assertIsNone(case['explanation'])
            self.assertNotIn('draft_reference',case['request']);self.assertTrue(case['request']['observation_channels'])
            for arm in ARMS:self.assertIsNone(study.case(self.train[0]['id'],arm,'train')['request']['fitted_vector'])
            with self.assertRaises(ValueError):study.case(self.dev[0]['id'],'invalid')

    def test_http_ml_export_is_a_feature_bundle_and_invalid_training_routes_are_rejected(self):
        import threading,urllib.request,urllib.error
        from http.server import ThreadingHTTPServer
        from triage_bench.app import App,handler_for
        server=ThreadingHTTPServer(('127.0.0.1',0),handler_for(App()));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url='http://127.0.0.1:'+str(server.server_port)
        try:
            with urllib.request.urlopen(url+'/api/experiment3/catalog?trial=structured') as r:c=json.load(r)
            self.assertEqual(c['manifest']['splits']['train']['records'],96);self.assertIsNone(c['hosted_pilot'])
            with urllib.request.urlopen(url+'/api/experiment3/export?trial=structured&variant=combined&id='+self.dev[0]['id']) as r:bundle=json.load(r)
            self.assertEqual(bundle['schema'],'experiment-3-ml-input-1');self.assertNotIn('questions',bundle);self.assertNotIn('model',bundle)
            request=urllib.request.Request(url+'/api/experiment3/run?trial=questions',data=b'{}',headers={'Content-Type':'application/json'})
            with self.assertRaises(urllib.error.HTTPError):urllib.request.urlopen(request)
        finally:server.shutdown();server.server_close();thread.join()

    def test_field_regressions_count_even_on_previously_wrong_packets(self):
        from triage_bench.experiment3.structured_service import compare_to_baseline
        truth={'initial_owner':'power','priority':'P2','next_check':'inspect_power','insufficient_evidence':'no'}
        before={**truth,'insufficient_evidence':'yes'};after={**truth,'initial_owner':'noc'}
        rows={a:{'sample':{'predictions':before if a=='baseline' else after}} for a in ARMS}
        keys={'sample':{'accepted_answers':{f:[v] for f,v in truth.items()}}}
        c=compare_to_baseline(rows,keys)['combined'];self.assertFalse(c['packets_lost']);self.assertFalse(c['packets_fixed']);self.assertEqual(c['newly_wrong_fields']['initial_owner'],['sample'])
