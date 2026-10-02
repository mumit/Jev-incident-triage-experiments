"""Read-only inspection of evidence selection and recorded hosted results."""
import json
from pathlib import Path
from triage_bench.dataset import ROOT, read_jsonl
from .data import changed_paths
from .selection import ARMS, body, packet, eligibility
from .selection_data import validate
from .selection_trial import verify
from .transforms import MODEL, dependency_facts, measurement_facts, sha


class SelectionStudy:
    def __init__(self, root=ROOT):
        self.root = Path(root)
        self.directory = self.root / 'data/experiment-3-selection-draft'
        self.manifest = validate(self.directory)
        self.records = {r['id']: r for r in read_jsonl(self.directory / 'development.inputs.jsonl')}
        self.keys = {r['id']: r for r in read_jsonl(self.directory / 'development.labels.jsonl')}
        self.summary, self.rows, self.requests = None, {}, {}
        self.status = 'No saved evidence-selection comparison.'
        for path in sorted((self.root / 'runs/experiment-3-selection').glob('*/summary.json'), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                self.summary, self.rows, self.requests = verify(path, self.root, self.directory)
                self.summary['run_id'] = path.parent.name
                self.status = 'Saved evidence-selection comparison: ' + self.summary['status'] + '; draft references.'
                break
            except (OSError, ValueError, KeyError, TypeError):
                self.status = 'Saved selection evidence differs or is incomplete; scores are unavailable.'

    def catalog(self):
        return {'comparison': 'selection', 'manifest': self.manifest, 'variants': ARMS,
                'status': 'Fixed explicit questions; input eligibility and selection vary. No ML fitting occurs.',
                'model': MODEL, 'pilot': None, 'hosted_pilot': self.summary, 'hosted_status': self.status,
                'jev_status': self.summary['status'] if self.summary else 'not_run',
                'cases': {'train': [], 'development': [{'id': r['id'], 'family': self.keys[r['id']]['incident_family_id'],
                          'pair_id': self.keys[r['id']]['pair_id'], 'pair_kind': self.keys[r['id']]['pair_kind']} for r in self.records.values()]}}

    def case(self, identifier, variant='baseline', split='development'):
        if split != 'development' or identifier not in self.records or variant not in ARMS:
            raise ValueError('Unknown evidence-selection case or arm.')
        r, key = self.records[identifier], self.keys[identifier]
        partner = next(other for id, other in self.records.items() if id != identifier and self.keys[id]['pair_id'] == key['pair_id'])
        request = body(r, variant)
        return {'record': r, 'draft_reference': key, 'paired': partner, 'changed_paths': changed_paths(r['input'], partner['input']),
                'dependency_facts': dependency_facts(r['input']), 'measurement_facts': measurement_facts(r['input']),
                'eligibility': eligibility(r['input']), 'packets': {a: packet(r, a) for a in ARMS},
                'question_sets': {a: body(r, a)['questions'] for a in ARMS}, 'request': request,
                'state_sha256': sha(request['state'].encode()), 'questions_sha256': sha(json.dumps(request['questions'], sort_keys=True).encode()),
                'request_bytes': len(json.dumps(request, ensure_ascii=False).encode()), 'outputs': {},
                'hosted_outputs': {a: self.rows.get(a, {}).get(identifier) for a in ARMS},
                'hosted_saved_requests': {a: self.requests.get((identifier, a)) for a in ARMS},
                'jev_status': self.summary['status'] if self.summary else 'not_run'}
