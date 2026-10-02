"""Train matched local variants on the draft training split; no hosted calls."""
import json
from pathlib import Path
import time

import sklearn
from scipy.sparse import hstack
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from triage_bench.dataset import read_jsonl, write_jsonl
from triage_bench.evaluate import evaluate
from triage_bench.experiments import structured_features
from triage_bench.policy import OPTIONS
from triage_bench.runner import baseline
from .data import DIRECTORY, validate
from .transforms import VARIANTS, request_body, sha


class PilotClassifier:
    def __init__(self, variant, directory=DIRECTORY):
        if variant not in VARIANTS:
            raise ValueError('Unknown experiment 3 input variant.')
        directory = Path(directory)
        self.variant = variant
        inputs, labels = directory / 'train.inputs.jsonl', directory / 'train.labels.jsonl'
        records = read_jsonl(inputs)
        keys = {k['id']: k for k in read_jsonl(labels)}
        if len(keys) != len(records) or set(keys) != {r['id'] for r in records}:
            raise ValueError('Training IDs must match.')
        started = time.perf_counter()
        states = [request_body(r, variant)['state'] for r in records]
        self.words = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)
        self.chars = TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5), min_df=2, sublinear_tf=True)
        self.impact = DictVectorizer()
        impact = self.impact.fit_transform([structured_features(r['input']) for r in records])
        semantic = hstack([self.words.fit_transform(states), self.chars.fit_transform(states), impact], format='csr')
        self.heads = {}
        for field, choices in OPTIONS.items():
            targets = [keys[r['id']]['labels'][field] for r in records]
            if set(targets) != set(choices):
                raise ValueError('Training does not cover every class for ' + field)
            head = LogisticRegression(C=2.0, max_iter=2000, random_state=17, class_weight='balanced')
            head.fit(impact if field == 'priority' else semantic, targets)
            self.heads[field] = head
        self.metadata = {'variant': variant, 'method': 'Matched word/character TF-IDF plus impact; only input facts vary',
                         'training_records': len(records), 'training_families': len({k['incident_family_id'] for k in keys.values()}),
                         'training_inputs_sha256': sha(inputs.read_bytes()), 'training_labels_sha256': sha(labels.read_bytes()),
                         'sklearn_version': sklearn.__version__, 'training_seconds': time.perf_counter() - started,
                         'parameters': {'C': 2.0, 'max_iter': 2000, 'random_state': 17, 'class_weight': 'balanced',
                                        'word_ngrams': [1, 2], 'character_ngrams': [3, 5], 'min_df': 2,
                                        'sublinear_tf': True, 'character_analyzer': 'char_wb', 'priority_features': 'impact_only'},
                         'calibration': 'Uncalibrated development probabilities; draft references.'}

    def predict(self, record):
        body = request_body(record, self.variant)
        impact = self.impact.transform([structured_features(record['input'])])
        features = hstack([self.words.transform([body['state']]), self.chars.transform([body['state']]), impact], format='csr')
        predictions, probabilities = {}, {}
        for field, head in self.heads.items():
            values = head.predict_proba(impact if field == 'priority' else features)[0]
            dist = {str(c): float(p) for c, p in zip(head.classes_, values)}
            probabilities[field] = dist
            predictions[field] = max(dist, key=dist.get)
        return {'id': record['id'], 'status': 'ok', 'predictions': predictions, 'probabilities': probabilities,
                'state_sha256': sha(body['state'].encode())}


def run(output, directory=DIRECTORY):
    """Save an immutable local development pilot, separate from app history."""
    directory, output = Path(directory), Path(output)
    validate(directory)
    if output.exists():
        raise ValueError('Pilot output exists; choose a new run directory.')
    output.mkdir(parents=True)
    records = read_jsonl(directory / 'development.inputs.jsonl')
    write_jsonl(output / 'inputs.jsonl', records)
    write_jsonl(output / 'labels.jsonl', read_jsonl(directory / 'development.labels.jsonl'))
    summary = {'reference_status': 'draft_not_specialist_reviewed', 'split': 'development',
               'training_records': len(read_jsonl(directory / 'train.inputs.jsonl')),  'development_records': len(records), 'jev_status': 'not_run',
               'input_sha256': sha((output / 'inputs.jsonl').read_bytes()),
               'label_sha256': sha((output / 'labels.jsonl').read_bytes()), 'approaches': {},
               'source_sha256': {'triage_bench/experiment3/' + name: sha((Path(__file__).parent / name).read_bytes()) for name in ['data.py', 'transforms.py', 'local.py']}
               | {'triage_bench/' + name: sha((Path(__file__).parent.parent / name).read_bytes()) for name in ['policy.py', 'experiments.py', 'runner.py', 'evaluate.py']}}
    for variant in VARIANTS:
        model = PilotClassifier(variant, directory)
        rows = []
        for record in records:
            started = time.perf_counter(); row = model.predict(record)
            row['latency_ms'] = (time.perf_counter() - started) * 1000
            rows.append(row)
        path = output / (variant + '.jsonl'); write_jsonl(path, rows)
        metrics = evaluate(output / 'labels.jsonl', path, output / (variant + '.metrics.json'), output / 'inputs.jsonl')
        summary['approaches'][variant] = {'training': model.metadata, 'metrics': metrics}
        (output / (variant + '.meta.json')).write_text(json.dumps(model.metadata, indent=2) + '\n')
    rows = [{'id': r['id'], 'status': 'ok', 'predictions': baseline(r['input'])} for r in records]
    write_jsonl(output / 'rules.jsonl', rows)
    summary['approaches']['rules'] = {'metrics': evaluate(output / 'labels.jsonl', output / 'rules.jsonl', output / 'rules.metrics.json', output / 'inputs.jsonl')}
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    return summary
