import copy
import json
import tempfile
import unittest
from pathlib import Path
from triage_bench.dataset import read_jsonl
from triage_bench.experiment3.task_fit_data import build, validate
from triage_bench.experiment3.task_fit_trial import ARMS, MODEL, body, card, examples, normalize, prepare, score, curves, check_freeze

class TaskFitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        cls.directory=Path(cls.tmp.name)/'data'
        build(cls.directory)
        cls.records=read_jsonl(cls.directory/'development.inputs.jsonl')
        cls.annotations=read_jsonl(cls.directory/'development.observations.jsonl')
        cls.keys=read_jsonl(cls.directory/'development.labels.jsonl')

    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()

    def test_equivalent_facts_and_isolated_changes(self):
        r=self.records[0]; ex=examples(self.directory); bodies={a:body(r,a,ex) for a in ARMS}
        self.assertEqual(bodies['prose']['questions'],bodies['structured']['questions'])
        self.assertEqual(bodies['structured']['state'],bodies['focused']['state'])
        self.assertEqual(bodies['focused']['questions'],bodies['examples']['questions'])
        c=card(r)
        self.assertEqual(set(c),{'report_text','focal_function'})
        for v in c.values(): self.assertIn(v,bodies['prose']['state'])
        self.assertEqual(json.loads(bodies['structured']['state']),c)
        e=json.loads(bodies['examples']['state']); self.assertEqual(e.pop('training_examples'),ex); self.assertEqual(e,c)
        poisoned=copy.deepcopy(r); poisoned['labels']={'reading':'SECRET'}
        self.assertEqual(body(poisoned,'structured',ex),bodies['structured'])

    def test_preflight_is_read_only_and_counts_distinct_calls(self):
        profile={'model':MODEL,'endpoint':'https://api.typesafe.ai/v1/systemone','context_tokens':32768}
        plan,records,requests=prepare(profile,directory=self.directory)
        self.assertEqual(plan['maximum_requests'],96)
        self.assertEqual(len(records),24)
        p,r,q=prepare(profile,directory=self.directory,repeat=True)
        self.assertEqual((len(r),len(q)),(6,72))
        self.assertEqual(q[0]['request_sha256'],q[24]['request_sha256'])
        with self.assertRaises(ValueError): prepare({**profile,'context_tokens':512},directory=self.directory)
        with self.assertRaises(ValueError): prepare(profile,split='calibration',directory=self.directory)
        with self.assertRaises(ValueError): check_freeze(None,'focused',self.directory)

    def test_invalid_and_missing_probabilities_never_become_success(self):
        valid={'model':MODEL,'answers':{'reading':{'choice':'fault','probabilities':{'fault':.8,'normal':.1,'unknown':.1},'confidence':.7}}}
        self.assertEqual(normalize(valid)[0],'fault')
        for change in [None,{'fault':1,'normal':True,'unknown':0},{'fault':float('nan'),'normal':.1,'unknown':.1},{'fault':.8,'normal':.8,'unknown':0}]:
            bad=copy.deepcopy(valid); bad['answers']['reading']['probabilities']=change
            with self.assertRaises(ValueError): normalize(bad)
        with self.assertRaises(ValueError): normalize({**valid,'model':'jev-latest'})

    def test_wrong_unknown_is_masked_but_reported_and_failures_keep_denominator(self):
        # First report is normal: a wrong unknown retains identical NOC triage.
        r=self.records[:2]
        rows=[{'id':r[0]['id'],'arm':'structured','status':'ok','reading':'unknown','probabilities':{'fault':.01,'normal':.01,'unknown':.98}}]
        m=score(r,self.annotations,self.keys,rows,'structured')
        self.assertEqual(m['reports'],2); self.assertEqual(m['failed_or_missing'],1)
        self.assertEqual(m['masked_wrong_readings'],1); self.assertEqual(m['correct_readings'],0)
        self.assertEqual(len(m['fault_read_as_nonfault']),1)
        curve=curves(r,self.annotations,self.keys,rows,'structured')['points'][0]
        self.assertEqual(curve['eligible_recommendations'],0); self.assertEqual(curve['review_reports'],2)
        self.assertIsNone(curve['reading_error_rate'])

    def test_probability_threshold_uses_selected_class_and_retains_unknown(self):
        r=self.records[:2]
        rows=[{'id':x['id'],'arm':'focused','status':'ok','reading':a['reading'],
               'probabilities':{v:.9 if v==a['reading'] else .05 for v in ('fault','normal','unknown')}} for x,a in zip(r,self.annotations)]
        curve=curves(r,self.annotations,self.keys,rows,'focused')['points']
        point=next(p for p in curve if p['threshold']==.9)
        self.assertEqual(point['coverage'],1); self.assertEqual(point['reading_errors'],0)
        self.assertGreater(point['zero_errors_upper95'],.7)
        self.assertEqual(next(p for p in curve if p['threshold']==.95)['coverage'],0)

    def test_checksums_detect_split_or_annotation_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp)/'data'; build(d)
            p=d/'calibration.observations.jsonl'; p.write_text(p.read_text().replace('"normal"','"fault"',1))
            with self.assertRaises(ValueError): validate(d)
