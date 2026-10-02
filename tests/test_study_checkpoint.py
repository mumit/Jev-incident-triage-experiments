import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scripts import study_checkpoint as checkpoint


class StudyCheckpointTests(unittest.TestCase):
    def test_capture_refuses_to_replace_an_existing_checkpoint(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / 'baseline.json'
            target.write_text('existing baseline')
            with self.assertRaisesRegex(ValueError, 'not overwritten'):
                checkpoint.capture(target, '2026-10-01', Path(folder))
            self.assertEqual(target.read_text(), 'existing baseline')

    def test_verification_distinguishes_changed_files_and_missing_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / 'source.py').write_text('original')
            snapshot = {'schema_version': 1, 'source_files': {'source.py': checkpoint.digest(b'original')},
                        'data_files': {}, 'evidence_files': {'runs/missing.jsonl': checkpoint.digest(b'')}, 'runs': {}}
            report = checkpoint.verify(snapshot, root)
            self.assertFalse(report['matches'])
            self.assertEqual(report['evidence_files']['missing'], ['runs/missing.jsonl'])
            (root / 'source.py').write_text('changed')
            report = checkpoint.verify(snapshot, root)
            self.assertEqual(report['source_files']['changed'], ['source.py'])
            snapshot['source_files'] = {'../outside': checkpoint.digest(b'')}
            with self.assertRaisesRegex(ValueError, 'Unsafe'):
                checkpoint.verify(snapshot, root)

    def test_release_metadata_normalization_preserves_prediction_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            original = root / 'meta.json'
            original.write_text('{"input_file":"' + str(root / 'runs/inputs.jsonl') + '"}')
            portable = checkpoint.evidence_bytes(original, root)
            original.write_bytes(portable)
            self.assertEqual(checkpoint.evidence_bytes(original, root), portable)
            predictions = root / 'model.jsonl'
            predictions.write_bytes(b'{"id": "one"}\n')
            self.assertEqual(checkpoint.evidence_bytes(predictions, root), predictions.read_bytes())

    def test_score_deltas_require_matching_inputs_keys_and_policy(self):
        entry = {'metadata': {'policy_sha256': 'policy', 'questions_sha256': 'old'},
                 'resolved_models': ['model'], 'errors': {}, 'metrics': {
                     'all_fields_accuracy': .5, 'semantic_decisions_accuracy': .5,
                     'with_software_priority_accuracy': .5,
                     'fields': {'initial_owner': {'accuracy': .5}}}}
        baseline = {'id': 'baseline', 'input_sha256': 'inputs', 'label_sha256': 'labels', 'providers': {'jev_focused': entry}}
        candidate = copy.deepcopy(baseline)
        candidate['id'] = 'candidate'
        candidate['providers']['jev_focused']['metrics']['all_fields_accuracy'] = .75
        candidate['providers']['jev_focused']['metadata']['questions_sha256'] = 'new'
        with patch.object(checkpoint, 'audited_run', return_value=candidate):
            compared = checkpoint.compare({'runs': {'test': baseline}}, Path('.'), 'test')
            self.assertTrue(compared['direct_score_comparison'])
            self.assertEqual(compared['providers']['jev_focused']['accuracy_change_percentage_points']['all_fields_accuracy'], 25)
            self.assertIn('questions_sha256', compared['providers']['jev_focused']['changed_settings'])
            for container, key in [(candidate, 'input_sha256'), (candidate, 'label_sha256'),
                                   (candidate['providers']['jev_focused']['metadata'], 'policy_sha256')]:
                previous = container[key]
                container[key] = 'changed'
                compared = checkpoint.compare({'runs': {'test': baseline}}, Path('.'), 'test')
                self.assertFalse(compared['direct_score_comparison'])
                self.assertNotIn('accuracy_change_percentage_points', compared['providers']['jev_focused'])
                container[key] = previous

    def test_verification_detects_edited_summary_even_when_file_hashes_match(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            directory = root / 'runs/app/example'
            directory.mkdir(parents=True)
            for name in ['job.json', 'labels.jsonl', 'inputs.jsonl']:
                (directory / name).write_text('{}')
            saved = {'id': 'example', 'providers': {}, 'count': 1}
            snapshot = {'schema_version': 1, 'source_files': {}, 'data_files': {}, 'evidence_files': {},
                        'runs': {'test': saved}}
            with patch.object(checkpoint, 'audited_run', return_value={**saved, 'count': 2}):
                report = checkpoint.verify(snapshot, root)
            self.assertFalse(report['matches'])
            self.assertEqual(report['recorded_results']['changed'], ['test'])
