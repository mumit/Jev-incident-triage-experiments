import copy,json,tempfile,unittest
from pathlib import Path
from triage_bench.dataset import read_jsonl
from triage_bench.experiment3.report_language_data import DIRECTORY,build,validate
from triage_bench.experiment3.report_language_trial import run,verify,changes
from triage_bench.experiment3.interpretation_model import ReportClassifier,report_inputs,apply_policy,pipeline_input

class ReportLanguageTests(unittest.TestCase):
    def test_matched_pack_rebuilds_without_nontext_or_target_changes(self):
        self.assertEqual(validate(),{'train_per_arm':186,'development':140,'development_families':35,'reports':{'train':210,'development':156}})
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'data';build(p)
            for f in DIRECTORY.rglob('*'):
                if f.is_file():self.assertEqual(f.read_bytes(),(p/f.relative_to(DIRECTORY)).read_bytes())
        for s,kinds in [('train',['labels','observations']),('development',['inputs','labels','observations'])]:
            for k in kinds:self.assertEqual((DIRECTORY/'narrow'/f'{s}.{k}.jsonl').read_bytes(),(DIRECTORY/'broad'/f'{s}.{k}.jsonl').read_bytes())

    def test_probe_language_spans_all_domain_readings_in_broader_training(self):
        records={r['id']:r for r in read_jsonl(DIRECTORY/'broad/train.inputs.jsonl')}
        meanings=read_jsonl(DIRECTORY/'broad/train.observations.jsonl')
        for a in meanings:
            if a['domain']!='none':self.assertIn('service probes',records[a['id']]['input']['observations'][a['observation_index']]['detail'])

    def test_clause_targets_are_separate_from_packet_targets_and_policy_matches(self):
        ann={}
        for a in read_jsonl(DIRECTORY/'narrow/development.observations.jsonl'):ann.setdefault(a['id'],[]).append(a)
        keys={k['id']:k for k in read_jsonl(DIRECTORY/'narrow/development.labels.jsonl')}
        for r in read_jsonl(DIRECTORY/'narrow/development.inputs.jsonl'):
            self.assertEqual(apply_policy(r,ann[r['id']])['predictions'],keys[r['id']]['labels'])
            if keys[r['id']]['control']=='scope_uncertainty' and r['id'].endswith('-a'):
                self.assertIn('unconfirmed',r['input']['observations'][0]['detail']);self.assertEqual(ann[r['id']][0]['reading'],'fault')
            if keys[r['id']]['control']=='age' and r['id'].endswith('-b'):self.assertEqual(ann[r['id']][0]['reading'],'fault');self.assertEqual(keys[r['id']]['labels']['initial_owner'],'noc')

    def test_model_settings_and_report_boundary_stay_frozen(self):
        models={a:ReportClassifier(DIRECTORY/a) for a in ['narrow','broad']}
        self.assertEqual(models['narrow'].metadata['parameters'],models['broad'].metadata['parameters'])
        self.assertEqual(models['narrow'].metadata['training_annotations_sha256'],models['broad'].metadata['training_annotations_sha256'])
        r=read_jsonl(DIRECTORY/'narrow/development.inputs.jsonl')[0];before=report_inputs(r);x=copy.deepcopy(r);x['labels']={'reading':'normal'};x['input']['observations'][0]['reading']='normal';x['input']['topology']={}
        self.assertEqual(before,report_inputs(x));self.assertNotIn('labels',pipeline_input(x))
        for model in models.values():self.assertNotIn('energize',model.words.vocabulary_)

    def test_recorded_evidence_recomputes_and_refuses_overwrite_or_tampering(self):
        with tempfile.TemporaryDirectory() as folder:
            out=Path(folder)/'run';s=run(out);self.assertEqual(verify(out/'summary.json')[0],s)
            with self.assertRaises(ValueError):run(out)
            p=out/'broad.inspections.jsonl';p.write_text(p.read_text()+'\n')
            with self.assertRaisesRegex(ValueError,'evidence'):verify(out/'summary.json')

    def test_regressions_include_fields_on_already_failed_packets(self):
        t={'initial_owner':'power','priority':'P2','next_check':'inspect_power','insufficient_evidence':'no'}
        before={**t,'insufficient_evidence':'yes'};after={**before,'initial_owner':'noc'}
        rows={a:{'case':{'predictions':p}} for a,p in [('narrow',before),('broad',after)]};keys={'case':{'accepted_answers':{f:[v] for f,v in t.items()}}}
        c=changes(rows,keys)['broad'];self.assertEqual(c['newly_wrong_fields']['initial_owner'],['case']);self.assertFalse(c['packets_lost'])
