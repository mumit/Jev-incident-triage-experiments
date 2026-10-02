"""Read-only inspection of repeated robustness inputs and decisions."""
import copy
from pathlib import Path
from triage_bench.dataset import ROOT, read_jsonl
from .robustness_trial import validate, verify, REPEATS
from .robustness_inference import ARMS, verify as verify_inference
from .selection_service import SelectionStudy


class RobustnessStudy(SelectionStudy):
    def __init__(self, root=ROOT):
        self.root = Path(root)
        self.directory = self.root/'data/experiment-3-robustness-draft'
        self.manifest = validate(self.directory)
        self.records = {r['id']:r for r in read_jsonl(self.directory/'development.inputs.jsonl')}
        self.keys = {r['id']:r for r in read_jsonl(self.directory/'development.labels.jsonl')}
        self.summary, self.rows, self.requests = None, {}, {}
        self.master, self.repeats = None, {}
        self.status = 'No saved repeated robustness comparison.'
        for path in sorted((self.root/'runs/experiment-3-robustness').glob('*/summary.json'), key=lambda p:p.stat().st_mtime, reverse=True):
            try:
                master = verify(path, self.root, self.directory)
                repeats = {}
                for item in master['runs']:
                    n = item['repetition']
                    summary, rows, requests = verify_inference(path.parent/f'repetition-{n}'/'summary.json', self.root, self.directory)
                    summary['run_id'] = path.parent.name+f'/repetition-{n}'
                    repeats[n] = summary, rows, requests
                self.master, self.repeats = master, repeats
                self.status = 'Saved robustness comparison: '+master['status']+'; draft references.'
                break
            except (OSError, ValueError, KeyError, TypeError):
                self.status = 'Saved robustness evidence differs or is incomplete; scores are unavailable.'

    def snapshot(self, repetition):
        if isinstance(repetition, bool) or not isinstance(repetition, int) or not 1 <= repetition <= REPEATS:
            raise ValueError('Unknown repetition.')
        view = copy.copy(self)
        view.summary, view.rows, view.requests = self.repeats.get(repetition, (None, {}, {}))
        return view

    def catalog(self, repetition=1):
        result = SelectionStudy.catalog(self.snapshot(repetition))
        result.update(comparison='robustness', variants=ARMS, repetition=repetition, repetitions=REPEATS,
                      repeat_summary=self.master, hosted_status=self.status)
        return result

    def case(self, identifier, variant='baseline', split='development', repetition=1):
        if variant not in ARMS:
            raise ValueError('Unknown robustness input.')
        result = SelectionStudy.case(self.snapshot(repetition), identifier, variant, split)
        for field in ['packets', 'question_sets', 'hosted_outputs', 'hosted_saved_requests']:
            result[field] = {a:result[field][a] for a in ARMS}
        result['repeated_outputs'] = {str(n):{a:rows.get(a, {}).get(identifier) for a in ARMS}
                                      for n, (_, rows, _) in self.repeats.items()}
        return result
