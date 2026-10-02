import copy,json,tempfile,unittest
from pathlib import Path
from triage_bench.dataset import read_jsonl
from triage_bench.experiment3.wording_data import DIRECTORY,ARMS,build,validate,training,word_counts
from triage_bench.experiment3.structured_features import input_bundle
from triage_bench.experiment3.structured_ml import StructuredClassifier,PARAMETERS
from triage_bench.experiment3.wording_ml import changes,run,verify

class WordingTests(unittest.TestCase):
    def test_rebuild_matches_and_balances_words_without_changing_training_targets(self):
        self.assertEqual(validate()['development_per_arm'],80)
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'data';build(path)
            for p in DIRECTORY.rglob('*'):
                if p.is_file():self.assertEqual(p.read_bytes(),(path/p.relative_to(DIRECTORY)).read_bytes())
        train=training();self.assertEqual(word_counts(train['balanced']),{'fault':{'tests':36,'diagnostics':36},'normal':{'tests':12,'diagnostics':12}})
        for arm in ARMS:self.assertEqual((DIRECTORY/arm/'train.labels.jsonl').read_bytes(),(DIRECTORY/'baseline/train.labels.jsonl').read_bytes())
        # Each member of a controlled training pair keeps the same method word.
        for a,b in zip(train['balanced'][::2],train['balanced'][1::2]):
            for x,y in zip(a['input']['observations'],b['input']['observations']):self.assertEqual(x['detail'],y['detail'])

    def test_new_development_is_identical_across_training_arms_with_synonym_controls(self):
        records=read_jsonl(DIRECTORY/'baseline/development.inputs.jsonl');keys={k['id']:k for k in read_jsonl(DIRECTORY/'baseline/development.labels.jsonl')}
        synonyms=[r for r in records if keys[r['id']]['changed_path']=='input.observations[0].detail'];self.assertEqual(len(synonyms),16)
        for a,b in zip(synonyms[::2],synonyms[1::2]):self.assertEqual(keys[a['id']]['labels'],keys[b['id']]['labels'])
        for arm in ARMS:
            self.assertEqual(records,read_jsonl(DIRECTORY/arm/'development.inputs.jsonl'))
            for r,other in zip(records,read_jsonl(DIRECTORY/arm/'development.inputs.jsonl')):self.assertEqual(input_bundle(r,'combined'),input_bundle(other,'combined'))

    def test_frozen_feature_recipe_and_priority_remain_matched(self):
        models={a:StructuredClassifier('combined',DIRECTORY/a) for a in ['coupled','balanced']}
        record=read_jsonl(DIRECTORY/'baseline/development.inputs.jsonl')[0]
        for m in models.values():self.assertEqual(m.metadata['parameters'],PARAMETERS)
        self.assertEqual(models['coupled'].predict(record)['probabilities']['priority'],models['balanced'].predict(record)['probabilities']['priority'])
        x=copy.deepcopy(record);x['labels']={'initial_owner':'core'};x['input']['answer']='core'
        self.assertEqual(input_bundle(record,'combined'),input_bundle(x,'combined'))
        self.assertNotIn('equalization',models['balanced'].space.words.vocabulary_)

    def test_evidence_is_immutable_recomputed_and_tamper_checked(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'run';summary=run(path);self.assertEqual(verify(path/'summary.json')[0],summary)
            self.assertEqual(summary['primary_comparison'],'balanced versus coupled; baseline is the unchanged original training bridge')
            with self.assertRaises(ValueError):run(path)
            p=path/'balanced.weights.jsonl';p.write_text(p.read_text()+'\n')
            with self.assertRaisesRegex(ValueError,'evidence'):verify(path/'summary.json')

    def test_field_regressions_are_counted_on_failed_packets(self):
        truth={'initial_owner':'transport','priority':'P2','next_check':'inspect_transport','insufficient_evidence':'no'}
        before={**truth,'insufficient_evidence':'yes'};after={**truth,'initial_owner':'noc'}
        rows={a:{'case':{'predictions':before if a=='coupled' else after}} for a in ARMS}
        result=changes(rows,{'case':{'accepted_answers':{f:[v] for f,v in truth.items()}}},'coupled')['balanced']
        self.assertEqual(result['newly_wrong_fields']['initial_owner'],['case']);self.assertFalse(result['packets_lost'])

    def test_missing_evidence_has_actual_training_wording_and_no_fabricated_predictions(self):
        import shutil
        from triage_bench.experiment3.wording_service import WordingStudy
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);shutil.copytree(DIRECTORY,root/'data/experiment-3-wording-draft');study=WordingStudy(root)
            self.assertIsNone(study.catalog()['pilot']);self.assertIsNone(study.catalog()['diagnostics'])
            identifier=next(iter(study.keys['train']));case=study.case(identifier,'balanced','train')
            self.assertEqual(set(case['training_wordings']),set(ARMS));self.assertFalse(case['outputs']);self.assertIsNone(case['request']['fitted_vector'])
            self.assertNotIn('draft_reference',case['request'])
            with self.assertRaises(ValueError):study.case(identifier,'invented','train')

    def test_synonym_agreement_is_distinct_from_correctness(self):
        from triage_bench.experiment3.wording_service import diagnostic_summary
        keys={i:{'id':i,'pair_id':'pair','incident_family_id':'sample method synonym','labels':{'initial_owner':'power'}} for i in ['a','b']}
        rows={arm:{i:{'predictions':{'initial_owner':'noc'}} for i in keys} for arm in ARMS}
        d=diagnostic_summary(rows,keys)['balanced'];self.assertEqual(d['synonym_agreement'],1);self.assertEqual(d['synonym_pairs_correct'],0)

    def test_http_exports_preserve_selected_training_arm_and_guide_link(self):
        import threading,urllib.request
        from http.server import ThreadingHTTPServer
        from triage_bench.app import App,handler_for
        server=ThreadingHTTPServer(('127.0.0.1',0),handler_for(App()));thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start();url='http://127.0.0.1:'+str(server.server_port)
        try:
            with urllib.request.urlopen(url+'/api/experiment3/catalog?trial=wording') as r:catalog=json.load(r)
            self.assertEqual(catalog['manifest']['splits']['development']['records'],80);self.assertIsNone(catalog['hosted_pilot'])
            identifier=catalog['cases']['train'][0]['id']
            with urllib.request.urlopen(url+'/api/experiment3/export?trial=wording&split=train&variant=balanced&id='+identifier) as r:bundle=json.load(r)
            self.assertEqual(bundle['training_arm'],'balanced');self.assertIsNone(bundle['fitted_vector']);self.assertNotIn('questions',bundle)
            with urllib.request.urlopen(url+'/study?doc=experiment-3-wording') as r:html=r.read().decode()
            self.assertIn('/experiment-3-wording-report.json',html);self.assertNotIn('checkpoints/experiment-3-wording',html)
        finally:server.shutdown();server.server_close();thread.join()
