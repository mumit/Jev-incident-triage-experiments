import json
from pathlib import Path
import tempfile
import unittest

from triage_bench.public_data import AUDIT_CASES, FILES, REVISION, metric_packet, sha, verify


class PublicDataPreflightTests(unittest.TestCase):
    def columns(self):
        return {'time': [1700000000 + i for i in range(6)],
                'handler_cpu': [1., 1., 1., 9., 9., 9.],
                'other_mem': [None, 2., float('nan'), 2., None, 2.]}

    def test_missing_values_do_not_become_successful_measurements(self):
        state = metric_packet(self.columns(), 1700000003)
        metric = next(row for row in state['metric_evidence'] if row['source_column'] == 'other_mem')
        self.assertEqual((metric['before_valid'], metric['before_missing']), (1, 2))
        self.assertEqual((metric['after_valid'], metric['after_missing']), (2, 1))
        self.assertEqual(metric['before_median'], 2.)
        self.assertEqual(metric['change_score'], 0.)
        json.dumps(state, allow_nan=False)

    def test_input_builder_rejects_answer_columns(self):
        for name in ['root_cause_service', 'fault_label', 'source_case', 'scoring_points']:
            columns = self.columns()
            columns[name] = [1] * 6
            with self.subTest(name=name), self.assertRaises(ValueError):
                metric_packet(columns, 1700000003)

    def test_metric_timestamps_require_seconds_and_two_valid_windows(self):
        for times, boundary in [([1700000000000 + i for i in range(6)], 1700000000003),
                                ([1700000000] * 6, 1700000003),
                                (list(reversed(self.columns()['time'])), 1700000003),
                                (self.columns()['time'], 1700000000),
                                (self.columns()['time'], 1700000006)]:
            with self.subTest(times=times), self.assertRaises(ValueError):
                metric_packet({**self.columns(), 'time': times}, boundary)

    def test_after_window_cannot_change_baseline_scale(self):
        columns = self.columns()
        first = metric_packet(columns, 1700000003)['metric_evidence'][0]
        columns['handler_cpu'][3:] = [100., 100., 100.]
        second = metric_packet(columns, 1700000003)['metric_evidence'][0]
        self.assertEqual(first['baseline_scale'], second['baseline_scale'])
        self.assertGreater(second['change_score'], first['change_score'])

    def test_missing_series_stays_unknown_and_candidates_are_not_answer_selected(self):
        columns = self.columns()
        columns['absent_socket'] = [None] * 6
        state = metric_packet(columns, 1700000003, limit=1)
        self.assertEqual(state['candidate_services'], ['absent', 'handler', 'other'])
        self.assertEqual(len(state['metric_evidence']), 1)
        complete = metric_packet(columns, 1700000003)
        absent = next(row for row in complete['metric_evidence'] if row['service'] == 'absent')
        self.assertIsNone(absent['change_score'])

    def test_source_verification_rejects_changes_and_foreign_paths(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            entries = []
            for case in AUDIT_CASES:
                for name in FILES:
                    path = f'{case}/{name}'
                    target = folder / 'raw' / path
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(b'fixture')
                    entries.append({'path': path, 'bytes': 7, 'sha256': sha(b'fixture')})
            (folder / 'cases.parquet').write_bytes(b'index')
            manifest = {'revision': REVISION, 'files': entries, 'index_sha256': sha(b'index')}
            source = folder / 'manifest.json'
            source.write_text(json.dumps(manifest))
            verify(folder)
            target.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError, 'fingerprint changed'):
                verify(folder)
            target.write_bytes(b'fixture')
            for bad_path in ['../outside', entries[1]['path']]:
                manifest['files'][0]['path'] = bad_path
                source.write_text(json.dumps(manifest))
                with self.assertRaisesRegex(ValueError, 'Unexpected, duplicate or missing'):
                    verify(folder)


if __name__ == '__main__':
    unittest.main()
