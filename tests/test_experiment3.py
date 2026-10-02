import copy
import json
from pathlib import Path
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from unittest.mock import patch

from triage_bench.app import App, handler_for
from triage_bench.dataset import ROOT, read_jsonl, write_jsonl
from triage_bench.experiments import compact_packet, focused_questions
from triage_bench.experiment3.data import DIRECTORY, TRAIN, build, changed_paths, make_pair, validate
from triage_bench.experiment3.local import PilotClassifier, run
from triage_bench.experiment3.service import PilotStudy
from triage_bench.experiment3.transforms import VARIANTS, dependency_facts, measurement_facts, request_body, transformed_packet


class TransformTests(unittest.TestCase):
    def setUp(self):
        self.records, self.keys = make_pair(TRAIN[0], 'train', 0)
        self.packet = self.records[0]['input']

    def test_baseline_is_frozen_compact_state_and_questions_are_identical(self):
        self.assertEqual(transformed_packet(self.records[0], 'baseline'), compact_packet(self.packet))
        requests = [request_body(self.records[0], v) for v in VARIANTS]
        self.assertTrue(all(set(r) == {'model', 'state', 'questions'} for r in requests))
        self.assertTrue(all(r['questions'] == focused_questions() for r in requests))
        self.assertEqual({r['model'] for r in requests}, {'jev-1.13.0'})

    def test_allowlist_excludes_labels_and_does_not_mutate(self):
        record = copy.deepcopy(self.records[0])
        record['labels'] = record['input']['labels'] = {'secret': 'REFERENCE_SENTINEL'}
        record['input']['topology']['generation_metadata'] = 'REFERENCE_SENTINEL'
        record['input']['observations'][0]['label_rationale'] = 'REFERENCE_SENTINEL'
        before = copy.deepcopy(record)
        for variant in VARIANTS:
            self.assertNotIn('REFERENCE_SENTINEL', json.dumps(request_body(record, variant)))
        self.assertEqual(record, before)

    def test_only_the_selected_fact_blocks_change(self):
        baseline = transformed_packet(self.records[0], 'baseline')
        for variant, added in [('dependency', {'dependency_facts'}), ('measurement', {'measurement_facts'}), ('combined', {'dependency_facts', 'measurement_facts'})]:
            result = transformed_packet(self.records[0], variant)
            self.assertEqual(set(result) - set(baseline), added)
            self.assertEqual({k: v for k, v in result.items() if k not in added}, baseline)

    def test_report_age_is_not_measurement_age_and_missing_time_stays_unknown(self):
        obs = self.packet['observations'][0]
        obs['measured_at'] = '2026-06-10T00:00:00Z'
        facts = measurement_facts(self.packet)[0]
        self.assertEqual(facts['report_age_minutes'], 1)
        self.assertEqual(facts['freshness_status'], 'stale')
        obs['measured_at'] = None
        self.assertEqual(measurement_facts(self.packet)[0]['freshness_status'], 'unknown')
        self.assertIsNone(measurement_facts(self.packet)[0]['measurement_age_minutes'])

    def test_freshness_boundary_and_undeclared_limit(self):
        from datetime import timedelta
        from triage_bench.experiment3.transforms import timestamp
        now = timestamp(self.packet['decision_timestamp'])
        obs = self.packet['observations'][0]
        obs['measured_at'] = (now - timedelta(minutes=15)).isoformat()
        self.assertEqual(measurement_facts(self.packet)[0]['freshness_status'], 'current')
        obs['measured_at'] = (now - timedelta(minutes=15, seconds=1)).isoformat()
        self.assertEqual(measurement_facts(self.packet)[0]['freshness_status'], 'stale')
        obs.pop('valid_for_minutes')
        self.assertEqual(measurement_facts(self.packet)[0]['freshness_status'], 'unknown')

    def test_impossible_time_or_invalid_validity_is_rejected(self):
        for field, value in [('measured_at', '2030-01-01T00:00:00Z'), ('observed_at', '2030-01-01T00:00:00Z'), ('measured_at', '2026-06-10T00:00:00'), ('valid_for_minutes', True), ('valid_for_minutes', float('nan'))]:
            packet = copy.deepcopy(self.packet); packet['observations'][0][field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                measurement_facts(packet)

    def test_directional_paths_and_complete_exclusion(self):
        connected = dependency_facts(self.packet)[0]
        disconnected = dependency_facts(self.records[1]['input'])[0]
        self.assertEqual(connected['relation'], 'all_listed_sites_depend')
        self.assertEqual(disconnected['relation'], 'no_listed_sites_depend')
        self.assertEqual(connected['supporting_paths'][0]['path'][0], self.packet['service_impact']['affected_site_ids'][0])
        self.assertEqual(connected['supporting_paths'][0]['path'][-1], self.packet['observations'][0]['asset_id'])
        packet = copy.deepcopy(self.packet); packet['topology']['edges'] = [e[::-1] for e in packet['topology']['edges']]
        self.assertEqual(dependency_facts(packet)[0]['relation'], 'no_listed_sites_depend')

    def test_partial_map_supports_paths_but_cannot_prove_absence(self):
        self.packet['topology']['coverage'] = 'partial'
        self.assertEqual(dependency_facts(self.packet)[0]['relation'], 'all_listed_sites_depend')
        other = self.records[1]['input']; other['topology']['coverage'] = 'partial'
        self.assertEqual(dependency_facts(other)[0]['relation'], 'unknown')
        self.assertEqual(dependency_facts(other)[0]['excluded_site_count'], 0)

    def test_missing_scope_cycle_and_missing_graph_stay_unknown(self):
        packet = self.records[1]['input']
        packet['topology']['edges'].append([packet['topology']['edges'][0][1], packet['topology']['edges'][0][0]])
        self.assertEqual(dependency_facts(packet)[0]['relation'], 'unknown')
        for replacement in [{}, {'edge_semantics': 'adjacent_to', 'coverage': 'complete'}]:
            packet = copy.deepcopy(self.packet); packet['topology'] = replacement
            self.assertEqual(dependency_facts(packet)[0]['relation'], 'unknown')
        self.packet['service_impact']['affected_sites'] = 2
        self.assertFalse(dependency_facts(self.packet)[0]['affected_site_scope_known'])

    def test_age_pairs_have_identical_baseline_inputs_and_distinct_age_inputs(self):
        records, keys = make_pair(TRAIN[2], 'train', 0)
        self.assertEqual(request_body(records[0], 'baseline'), request_body(records[1], 'baseline'))
        self.assertNotEqual(request_body(records[0], 'measurement'), request_body(records[1], 'measurement'))
        self.assertNotEqual(keys[0]['labels'], keys[1]['labels'])


class PilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.folder = tempfile.TemporaryDirectory()
        cls.root = Path(cls.folder.name)
        cls.data = cls.root / 'data/experiment-3-draft'
        build(cls.data)
        # Source fingerprints resolve relative to this fixture root.
        import shutil
        for name in ['policy.py', 'experiments.py', 'runner.py', 'evaluate.py', 'experiment3/data.py', 'experiment3/transforms.py', 'experiment3/local.py']:
            destination = cls.root / 'triage_bench' / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / 'triage_bench' / name, destination)
        cls.output = cls.root / 'runs/experiment-3/pilot'
        with patch('urllib.request.urlopen', side_effect=AssertionError('No hosted inference in local pilot')):
            cls.summary = run(cls.output, cls.data)
        cls.study = PilotStudy(cls.root)

    @classmethod
    def tearDownClass(cls):
        cls.folder.cleanup()

    def test_draft_pack_validates_and_is_reproducible(self):
        self.assertEqual(validate(self.data), {'train': 72, 'development': 36})
        self.assertEqual(json.loads((self.data / 'manifest.json').read_text()), json.loads((DIRECTORY / 'manifest.json').read_text()))
        with self.assertRaises(ValueError): build(self.data)

    def test_pair_integrity_rejects_an_undeclared_change(self):
        with tempfile.TemporaryDirectory() as folder:
            import shutil
            target = Path(folder) / 'pack'; shutil.copytree(self.data, target)
            rows = read_jsonl(target / 'development.inputs.jsonl')
            rows[0]['input']['change_record']['detail'] = 'An additional change'
            write_jsonl(target / 'development.inputs.jsonl', rows)
            with self.assertRaisesRegex(ValueError, 'more than the declared field'):
                validate(target)

    def test_matched_models_use_training_only(self):
        with tempfile.TemporaryDirectory() as folder:
            import shutil
            target = Path(folder) / 'pack'; shutil.copytree(self.data, target)
            (target / 'development.labels.jsonl').write_text('this is deliberately not JSON')
            model = PilotClassifier('combined', target)
            self.assertEqual(model.metadata['training_records'], 72)
            record = read_jsonl(target / 'development.inputs.jsonl')[0]
            row = model.predict(record)
            expected = read_jsonl(self.output / 'combined.jsonl')[0]
            self.assertEqual(row['predictions'], expected['predictions'])
            self.assertEqual(row['probabilities'], expected['probabilities'])

    def test_saved_pilot_refuses_overwrite_and_records_recipe(self):
        with self.assertRaises(ValueError): run(self.output, self.data)
        self.assertEqual(self.summary['jev_status'], 'not_run')
        parameters = [self.summary['approaches'][v]['training']['parameters'] for v in VARIANTS]
        self.assertTrue(all(p == parameters[0] for p in parameters))
        self.assertEqual(set(self.summary['approaches']), {*VARIANTS, 'rules'})

    def test_service_keeps_references_separate_and_training_unscored(self):
        identifier = next(iter(self.study.records['development']))
        case = self.study.case(identifier, 'combined')
        self.assertEqual(set(case['request']), {'model', 'state', 'questions'})
        self.assertNotIn('incident_family_id', case['request']['state'])
        self.assertEqual(case['changed_paths'], [case['draft_reference']['changed_path']])
        self.assertTrue(all(case['outputs'][v] for v in VARIANTS))
        training = self.study.case(next(iter(self.study.records['train'])), split='train')
        self.assertTrue(all(row is None for row in training['outputs'].values()))
        self.assertEqual(self.study.catalog()['hosted_requests_if_run'], 144)

    def test_saved_scores_are_recomputed_and_source_drift_is_rejected(self):
        altered = json.loads((self.output / 'summary.json').read_text())
        altered['approaches']['baseline']['metrics']['all_fields_accuracy'] = 1
        with tempfile.TemporaryDirectory(dir=self.output.parent) as folder:
            import shutil
            for path in self.output.iterdir(): shutil.copyfile(path, Path(folder) / path.name)
            (Path(folder) / 'summary.json').write_text(json.dumps(altered))
            with self.assertRaisesRegex(ValueError, 'recomputed'):
                self.study.load_pilot(Path(folder) / 'summary.json')
        source = self.root / 'triage_bench/experiment3/local.py'
        before = source.read_bytes(); source.write_bytes(before + b'\n')
        try: self.assertFalse(self.study.load_pilot(self.output / 'summary.json'))
        finally: source.write_bytes(before)

    def test_manifest_does_not_accept_arbitrary_paths(self):
        with tempfile.TemporaryDirectory() as folder:
            import shutil
            target = Path(folder) / 'pack'; shutil.copytree(self.data, target)
            manifest = json.loads((target / 'manifest.json').read_text())
            manifest['sha256']['../outside.jsonl'] = 'x'
            (target / 'manifest.json').write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, 'Unexpected draft manifest paths'): validate(target)

    def test_app_exposes_requests_without_secret_or_hosted_calls(self):
        server = ThreadingHTTPServer(('127.0.0.1', 0), handler_for(App()))
        worker = threading.Thread(target=server.serve_forever, daemon=True); worker.start()
        base = f'http://127.0.0.1:{server.server_port}'
        try:
            for path in ['/experiment-3', '/experiment3.js', '/experiment3.css', '/api/experiment3/catalog']:
                with urllib.request.urlopen(base + path) as response: self.assertEqual(response.status, 200)
            identifier = next(iter(self.study.records['development']))
            with urllib.request.urlopen(base + '/api/experiment3/export?id=' + identifier + '&variant=combined') as response:
                self.assertIn('attachment;', response.headers['Content-Disposition'])
                request = json.load(response)
                self.assertEqual(set(request), {'model', 'state', 'questions'})
            for path, headers in [('/api/experiment3/case?id=missing', {}), ('/api/experiment3/catalog', {'Origin':'https://outside.example'})]:
                with self.assertRaises(urllib.error.HTTPError) as error:
                    urllib.request.urlopen(urllib.request.Request(base + path, headers=headers))
                self.assertEqual(error.exception.code, 400 if not headers else 403)
        finally:
            server.shutdown(); server.server_close(); worker.join()
