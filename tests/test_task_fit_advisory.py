import copy
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from triage_bench.dataset import ROOT, read_jsonl, write_jsonl
from triage_bench.experiment3.task_fit_data import build
from triage_bench.experiment3.task_fit_trial import SOURCES, MODEL, body, examples, prepare, finish, verify
from triage_bench.experiment3.task_fit_advisory import CRITERIA, decision, freeze_boundary, check_boundary, run_evaluation
from triage_bench.experiment3.transforms import sha


class AdvisoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
        self.data = self.root/'data'; build(self.data)
        self.profile = {'model': MODEL, 'endpoint': 'http://127.0.0.1:12345', 'context_tokens': 32768, 'api_key': 'fixture-key'}
        self.candidate = self.root/'candidate.json'
        self.candidate.write_text(json.dumps({'schema': 'task-fit-candidate-1', 'arm': 'structured', 'model': MODEL,
            'data_sha256': json.loads((self.data/'manifest.json').read_text())['sha256'],
            'source_sha256': {name: sha((ROOT/name).read_bytes()) for name in SOURCES}}))
        plan, records, requests = prepare(self.profile, 'calibration', ['structured'], self.data)
        refs = read_jsonl(self.data/'calibration.observations.jsonl'); rows = []
        for i, (r, ref, req) in enumerate(zip(records, refs, requests)):
            reading = 'fault' if i == 0 else ref['reading']
            probabilities = {'fault': .51, 'normal': .48, 'unknown': .01} if i == 0 else {v: .9 if v == reading else .05 for v in ('fault', 'normal', 'unknown')}
            raw = {'model': MODEL, 'answers': {'reading': {'choice': reading, 'probabilities': probabilities}}}
            rows.append({'id': r['id'], 'arm': 'structured', 'repetition': 1, 'status': 'ok', 'reading': reading,
                         'probabilities': probabilities, 'provider_confidence': None, 'raw_response': raw, 'request_sha256': req['request_sha256']})
        self.cal = self.root/'calibration'; self.cal.mkdir()
        write_jsonl(self.cal/'observations.jsonl', refs); write_jsonl(self.cal/'labels.jsonl', read_jsonl(self.data/'calibration.labels.jsonl'))
        write_jsonl(self.cal/'inputs.jsonl', records); write_jsonl(self.cal/'requests.jsonl', requests); write_jsonl(self.cal/'responses.jsonl', rows)
        finish(self.cal, plan, records, rows, directory=self.data)
        self.boundary = self.root/'boundary.json'
        self.frozen = freeze_boundary(self.candidate, self.cal, self.boundary, self.data)
        self.record = records[0]

    def tearDown(self): self.tmp.cleanup()

    def test_calibration_selects_threshold_without_evaluation_references(self):
        self.assertEqual(self.frozen['advisory_threshold'], .6)
        self.assertEqual(self.frozen['research_criteria'], CRITERIA)
        self.assertNotIn('evaluation.inputs.jsonl', self.frozen)
        self.assertEqual(check_boundary(self.boundary, self.candidate, self.cal, self.data), self.frozen)
        with self.assertRaises(ValueError): freeze_boundary(self.candidate, self.cal, self.boundary, self.data)
        changed = copy.deepcopy(self.frozen); changed['advisory_threshold'] = .9
        self.boundary.write_text(json.dumps(changed))
        with self.assertRaises(ValueError): check_boundary(self.boundary, self.candidate, self.cal, self.data)

    def test_all_suggestions_retain_analyst_review_and_uncertain_readings_hold_back(self):
        fault = {'status': 'ok', 'reading': 'fault', 'probabilities': {'fault': .9, 'normal': .05, 'unknown': .05}}
        d = decision(self.record, fault, .6)
        self.assertEqual(d['domain_recommendation'], 'ran')
        self.assertTrue(d['analyst_review_required']); self.assertFalse(d['automatic_assignment'])
        for row in (None, {'status': 'error'}, {**fault, 'reading': 'unknown'}, {**fault, 'probabilities': {'fault': .51}}):
            d = decision(self.record, row, .6)
            self.assertFalse(d['qualifying_reading']); self.assertIsNone(d['domain_recommendation'])
            self.assertTrue(d['analyst_review_required'])
        normal = decision(self.record, {**fault, 'reading': 'normal', 'probabilities': {'normal': .9}}, .6)
        self.assertTrue(normal['qualifying_reading']); self.assertIsNone(normal['domain_recommendation'])
        self.assertEqual(normal['disposition'], 'policy_retains_noc')

    def test_rate_limit_preserves_denominators_and_preregistration_precedes_calls(self):
        class LimitedOpener:
            def open(inner, request, timeout):
                output = self.root/self.frozen['evaluation_output']
                self.assertTrue((output/'protocol.json').exists())
                self.assertEqual(len(read_jsonl(output/'requests.jsonl')), 24)
                raise urllib.error.HTTPError(request.full_url, 429, 'fixture-key', {}, None)
        with patch('triage_bench.experiment3.task_fit_advisory.check_boundary', return_value=self.frozen), \
             patch('triage_bench.experiment3.task_fit_advisory.ROOT', self.root), \
             patch('triage_bench.experiment3.task_fit_advisory.verify'), \
             patch('triage_bench.experiment3.task_fit_advisory.urllib.request.build_opener', return_value=LimitedOpener()):
            result = run_evaluation(self.profile, self.boundary, self.candidate, self.cal, self.data)
            self.assertEqual(result['reports'], 24); self.assertEqual(result['failed_or_missing'], 24)
            self.assertFalse(result['meets_research_criteria'])
            output = self.root/self.frozen['evaluation_output']
            self.assertNotIn('fixture-key', (output/'responses.jsonl').read_text())
            summary = json.loads((output/'summary.json').read_text())
            self.assertEqual(summary['attempted_requests'], 1); self.assertEqual(summary['unattempted_requests'], 23)
            with self.assertRaises(ValueError): run_evaluation(self.profile, self.boundary, self.candidate, self.cal, self.data)
