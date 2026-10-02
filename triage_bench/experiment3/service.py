"""Inspection and explicit local pilot execution, isolated from historical runs."""
import json
from pathlib import Path
import threading
import uuid

from triage_bench.dataset import ROOT, read_jsonl
from triage_bench.evaluate import evaluate
from .data import validate, changed_paths
from .local import run
from .transforms import VARIANTS, MODEL, sha, dependency_facts, measurement_facts, transformed_packet, request_body


class PilotStudy:
    def __init__(self, root=ROOT):
        self.root = Path(root)
        self.directory = self.root / 'data/experiment-3-draft'
        validate(self.directory)
        self.manifest = json.loads((self.directory / 'manifest.json').read_text())
        self.records, self.keys = {}, {}
        for split in ['train', 'development']:
            self.records[split] = {r['id']: r for r in read_jsonl(self.directory / (split + '.inputs.jsonl'))}
            self.keys[split] = {k['id']: k for k in read_jsonl(self.directory / (split + '.labels.jsonl'))}
        self.lock = threading.Lock()
        self.summary, self.rows = None, {}
        self.status = 'No saved local pilot. Run the four variants locally to compare draft decisions.'
        candidates = sorted((self.root / 'runs/experiment-3').glob('*/summary.json'), key=lambda p: p.stat().st_mtime, reverse=True)
        for candidate in candidates:
            try:
                if self.load_pilot(candidate):
                    break
            except (OSError, ValueError, KeyError, TypeError):
                self.status = 'A saved pilot is incomplete or invalid. Run a new local pilot.'

    def load_pilot(self, path):
        summary = json.loads(path.read_text())
        expected = self.manifest['sha256']
        if set(summary['approaches']) != {*VARIANTS, 'rules'}:
            raise ValueError('Unexpected local approaches.')
        for filename, digest in [('inputs.jsonl', summary['input_sha256']), ('labels.jsonl', summary['label_sha256'])]:
            if sha((path.parent / filename).read_bytes()) != digest:
                raise ValueError('Saved pilot scoring data differ.')
        if summary.get('input_sha256') != expected['development.inputs.jsonl'] or summary.get('label_sha256') != expected['development.labels.jsonl']:
            self.status = 'Saved pilot data differ from this draft pack. Run a new local pilot.'
            return False
        if not summary.get('source_sha256') or any(not (self.root / p).is_file() or sha((self.root / p).read_bytes()) != digest for p, digest in summary['source_sha256'].items()):
            self.status = 'Saved pilot source differs from this implementation. Run a new local pilot.'
            return False
        for variant in VARIANTS:
            training = summary['approaches'][variant]['training']
            if training['training_inputs_sha256'] != expected['train.inputs.jsonl'] or training['training_labels_sha256'] != expected['train.labels.jsonl']:
                self.status = 'Saved training data differ. Run a new local pilot.'
                return False
        rows = {}
        for approach, result in summary['approaches'].items():
            prediction_path = path.parent / (approach + '.jsonl')
            if not prediction_path.exists() or sha(prediction_path.read_bytes()) != result['metrics']['prediction_sha256']:
                self.status = 'Saved predictions do not match their score fingerprints.'
                return False
            if evaluate(path.parent / 'labels.jsonl', prediction_path, inputs_path=path.parent / 'inputs.jsonl') != result['metrics']:
                raise ValueError('Saved pilot scores differ from recomputed results.')
            rows[approach] = {r['id']: r for r in read_jsonl(prediction_path)}
        self.summary, self.rows = summary, rows
        self.summary['run_id'] = path.parent.name
        self.status = 'Saved local development pilot; provisional references, no hosted Jev calls.'
        return True

    def catalog(self):
        return {'manifest': self.manifest, 'variants': VARIANTS, 'status': self.status, 'model': MODEL,
                'hosted_requests_if_run': len(self.records['development']) * len(VARIANTS), 'jev_status': 'not_run',
                'cases': {split: [{'id': r['id'], 'family': self.keys[split][r['id']]['incident_family_id'],
                                   'pair_id': self.keys[split][r['id']]['pair_id'], 'pair_kind': self.keys[split][r['id']]['pair_kind']}
                                  for r in records.values()] for split, records in self.records.items()},
                'pilot': self.summary}

    def case(self, identifier, variant='baseline', split='development'):
        if split not in self.records or identifier not in self.records[split] or variant not in VARIANTS:
            raise ValueError('Unknown development case or variant.')
        record, key = self.records[split][identifier], self.keys[split][identifier]
        partner = next(r for r in self.records[split].values() if r['id'] != identifier and self.keys[split][r['id']]['pair_id'] == key['pair_id'])
        body = request_body(record, variant)
        outputs = {p: rows.get(identifier) if split == 'development' else None for p, rows in self.rows.items()}
        return {'record': record, 'draft_reference': key, 'paired': partner,
                'changed_paths': changed_paths(record['input'], partner['input']),
                'dependency_facts': dependency_facts(record['input']), 'measurement_facts': measurement_facts(record['input']),
                'packets': {v: transformed_packet(record, v) for v in VARIANTS},
                'request': body, 'state_sha256': sha(body['state'].encode()),
                'questions_sha256': sha(json.dumps(body['questions'], sort_keys=True).encode()),
                'request_bytes': len(json.dumps(body, ensure_ascii=False).encode()),
                'outputs': outputs, 'jev_status': 'not_run'}

    def run_local(self):
        if not self.lock.acquire(blocking=False):
            raise ValueError('A local pilot is already running.')
        try:
            destination = self.root / 'runs/experiment-3' / ('development-' + uuid.uuid4().hex[:12])
            run(destination, self.directory)
            if not self.load_pilot(destination / 'summary.json'):
                raise ValueError(self.status)
            return self.catalog()
        finally:
            self.lock.release()
