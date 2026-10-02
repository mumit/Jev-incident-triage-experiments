"""Capture and audit a study baseline, or compare a new run without hosted calls."""
import argparse
from datetime import date
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess

from scripts.study_bundle import ROOT, RUNS, allowed_paths, local_secrets, portable, review
from triage_bench.dataset import read_jsonl
from triage_bench.evaluate import evaluate

METRICS = ['records', 'attempted_records', 'missing_records', 'failed_records',
           'all_fields_accuracy', 'semantic_decisions_accuracy', 'with_software_priority_accuracy',
           'p1_miss_rate', 'p1_records', 'pair_all_fields_accuracy', 'paired_families', 'successful_latency_ms']
FIELD_METRICS = ['accuracy', 'macro_f1', 'brier_score', 'brier_records', 'probability_records',
                 'confusion_matrix', 'family_bootstrap_95_percent_interval', 'families']
META = ['provider', 'requested_model', 'request_variant', 'declared_context_tokens',
        'input_sha256', 'policy_sha256', 'questions_sha256', 'execution', 'benchmark_version',
        'successful_records', 'failed_records', 'attempted_records', 'not_attempted_records']
TRAINING = ['method', 'training_records', 'training_families', 'training_inputs_sha256',
            'training_labels_sha256', 'sklearn_version', 'parameters', 'feature_count', 'calibration']


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(path.read_text())


def evidence_bytes(path, root):
    # Release restoration normalizes metadata paths and JSON formatting. Compare
    # their portable content, while preserving exact prediction/input JSONL bytes.
    if path.suffix == '.json':
        return (json.dumps(portable(load(path), root), indent=2, ensure_ascii=False) + '\n').encode()
    return path.read_bytes()


def summarize(metrics):
    return {**{key: metrics.get(key) for key in METRICS},
            'fields': {field: {key: values.get(key) for key in FIELD_METRICS}
                       for field, values in metrics['fields'].items()}}


def metadata(meta):
    result = {key: meta[key] for key in META if key in meta}
    if 'training' in meta:
        result['training'] = {key: meta['training'][key] for key in TRAINING if key in meta['training']}
    return result


def audited_run(directory):
    """Recompute saved scores and check the job, metadata and prediction records."""
    job = load(directory / 'job.json')
    keys = read_jsonl(directory / 'labels.jsonl')
    input_hash = digest((directory / 'inputs.jsonl').read_bytes())
    providers = {}
    for provider, result in job['results'].items():
        if provider not in {'baseline', 'ml', 'ml_structured', 'jev', 'jev_focused'}:
            raise ValueError('Unknown recorded approach; register its comparison mapping first.')
        rows = read_jsonl(directory / (provider + '.jsonl'))
        meta = load(directory / (provider + '.meta.json'))
        metrics = load(directory / (provider + '.metrics.json'))
        computed = evaluate(directory / 'labels.jsonl', directory / (provider + '.jsonl'),
                            inputs_path=directory / 'inputs.jsonl')
        if any(computed.get(key) != value for key, value in metrics.items()):
            raise ValueError('Saved scores differ from recomputed predictions.')
        if meta != result['metadata'] or metrics != result['metrics'] or meta['input_sha256'] != input_hash:
            raise ValueError('Job, score or metadata fingerprints disagree.')
        if [{k: v for k, v in row.items() if k != 'raw_response'} for row in rows] != result['predictions']:
            raise ValueError('Job and prediction rows disagree.')
        by_id = {row['id']: row for row in rows}
        errors = {}
        for field in metrics['fields']:
            wrong, high = [], []
            for key in keys:
                row = by_id.get(key['id'], {})
                choice = row.get('predictions', {}).get(field)
                if row.get('status') != 'ok' or choice not in key['accepted_answers'][field]:
                    wrong.append(key['id'])
                    if row.get('status') == 'ok' and row.get('probabilities', {}).get(field, {}).get(choice, 0) >= .8:
                        high.append(key['id'])
            errors[field] = {'wrong_records': len(wrong), 'high_probability_wrong_records': len(high),
                             'high_probability_wrong_examples': high[:5]}
        providers[provider] = {'metadata': metadata(meta), 'metrics': summarize(metrics), 'errors': errors,
                               'resolved_models': sorted({row['resolved_model'] for row in rows
                                                          if row.get('status') == 'ok' and row.get('resolved_model')})}
    return {'id': job['id'], 'split': job['split'], 'count': job['count'],
            'input_sha256': input_hash, 'label_sha256': digest((directory / 'labels.jsonl').read_bytes()),
            'providers': providers}


def capture(path, as_of, root=ROOT):
    date.fromisoformat(as_of)
    if path.exists():
        raise ValueError('Checkpoint exists; choose a new filename. Baselines are not overwritten.')
    root = Path(root).resolve()
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    tracked = subprocess.check_output(['git', 'ls-files'], cwd=root, text=True).splitlines()
    sources = [name for name in tracked if name.startswith('triage_bench/') or
               name in {'pyproject.toml', 'uv.lock', 'requirements.txt', 'start.command', 'scripts/review_performance.py', 'scripts/study_checkpoint.py'}]
    for name in sources:
        if (root / name).read_bytes() != subprocess.check_output(['git', 'show', commit + ':' + name], cwd=root):
            raise ValueError('Commit application changes before capturing their source baseline.')
    dataset = load(root / 'data/manifest.json')
    freeze = load(root / 'runs/performance-freeze.json')
    for name, expected in {**{('data/' + k): v for k, v in dataset['sha256'].items()}, **freeze['files']}.items():
        if digest((root / name).read_bytes()) != expected:
            raise ValueError('Dataset or frozen inference fingerprint differs.')
    runs = {name: audited_run(root / 'runs/app' / identifier) for name, identifier in RUNS.items()}
    for name, run in runs.items():
        split = 'validation' if name == 'initial_validation' else name
        if run['id'] != RUNS[name] or run['split'] != split or run['count'] != dataset['splits'][split]['records']:
            raise ValueError('Recorded run identity or size differs.')
        if run['input_sha256'] != dataset['sha256'][split + '.inputs.jsonl'] or run['label_sha256'] != dataset['sha256'][split + '.labels.jsonl']:
            raise ValueError('Recorded run dataset differs.')
        for entry in run['providers'].values():
            training = entry['metadata'].get('training')
            if training and (training['training_inputs_sha256'] != dataset['sha256']['train.inputs.jsonl'] or
                             training['training_labels_sha256'] != dataset['sha256']['train.labels.jsonl']):
                raise ValueError('ML training fingerprints differ.')
    snapshot = {'schema_version': 1, 'as_of': as_of, 'operator': 'Northstar Telecom', 'synthetic': True,
                'source_commit': commit, 'inference_checkpoint': '6a44f62',
                'capture_tool_sha256': digest(Path(__file__).read_bytes()),
                'evidence_release': 'study-evidence-v1',
                'evidence_normalization': 'JSON metadata paths are repository-relative and formatting normalized; JSONL bytes unchanged.',
                'dataset': dataset, 'freeze': freeze, 'runs': runs,
                'source_files': {name: digest((root / name).read_bytes()) for name in sources},
                'data_files': {'data/manifest.json': digest((root / 'data/manifest.json').read_bytes()),
                               **{('data/' + k): v for k, v in dataset['sha256'].items()}},
                'evidence_files': {name: digest(evidence_bytes(root / name, root)) for name in sorted(allowed_paths())}}
    review(snapshot, local_secrets(root))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        stream.write(json.dumps(snapshot, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
    return snapshot


def verify(snapshot, root=ROOT):
    if snapshot.get('schema_version') != 1:
        raise ValueError('Unsupported checkpoint schema.')
    report = {}
    for group in ['source_files', 'data_files', 'evidence_files']:
        missing, changed = [], []
        for name, expected in snapshot[group].items():
            relative = PurePosixPath(name)
            if relative.is_absolute() or '..' in relative.parts:
                raise ValueError('Unsafe checkpoint path.')
            path = Path(root) / name
            if not path.is_file():
                missing.append(name)
            elif digest(evidence_bytes(path, Path(root).resolve()) if group == 'evidence_files' else path.read_bytes()) != expected:
                changed.append(name)
        report[group] = {'checked': len(snapshot[group]), 'changed': changed, 'missing': missing}
    results = {'checked': 0, 'changed': [], 'missing': []}
    for name, expected in snapshot.get('runs', {}).items():
        directory = Path(root) / 'runs/app' / expected['id']
        required = [directory / 'job.json', directory / 'labels.jsonl', directory / 'inputs.jsonl']
        for provider in expected['providers']:
            required.extend(directory / (provider + suffix) for suffix in ['.jsonl', '.meta.json', '.metrics.json'])
        if not all(path.is_file() for path in required):
            results['missing'].append(name)
            continue
        results['checked'] += len(expected['providers'])
        try:
            if audited_run(directory) != expected:
                results['changed'].append(name)
        except (ValueError, KeyError):
            results['changed'].append(name)
    report['recorded_results'] = results
    report['matches'] = all(not item['changed'] and not item['missing'] for item in report.values())
    return report


def compare(snapshot, directory, reference, root=ROOT):
    candidate = audited_run(directory)
    baseline = snapshot['runs'][reference]
    checks = {'inputs_match': candidate['input_sha256'] == baseline['input_sha256'],
              'answer_keys_match': candidate['label_sha256'] == baseline['label_sha256']}
    result = {'reference_run': baseline['id'], 'candidate_run': candidate['id'], 'checks': checks,
              'direct_score_comparison': False, 'providers': {}}
    for provider, entry in candidate['providers'].items():
        old = baseline['providers'].get(provider)
        compatible = old is not None and all(checks.values()) and entry['metadata'].get('policy_sha256') == old['metadata'].get('policy_sha256')
        result['providers'][provider] = {'direct_score_comparison': compatible,
                                       'candidate_metrics': entry['metrics'], 'candidate_errors': entry['errors']}
        if old:
            result['providers'][provider]['changed_settings'] = [key for key in sorted(set(entry['metadata']) | set(old['metadata']))
                                                                if entry['metadata'].get(key) != old['metadata'].get(key)]
            if entry['resolved_models'] != old['resolved_models']:
                result['providers'][provider]['changed_settings'].append('resolved_models')
        if compatible:
            result['providers'][provider]['accuracy_change_percentage_points'] = {
                key: (entry['metrics'][key] - old['metrics'][key]) * 100
                for key in ['all_fields_accuracy', 'semantic_decisions_accuracy', 'with_software_priority_accuracy']
                if entry['metrics'][key] is not None and old['metrics'][key] is not None}
            result['providers'][provider]['field_accuracy_change_percentage_points'] = {
                field: (values['accuracy'] - old['metrics']['fields'][field]['accuracy']) * 100
                for field, values in entry['metrics']['fields'].items()}
    result['direct_score_comparison'] = bool(result['providers']) and all(p['direct_score_comparison'] for p in result['providers'].values())
    result['interpretation'] = ('Matched evaluation inputs, answer keys and policy; inspect changed settings before attributing gains.'
                               if result['direct_score_comparison'] else
                               'Different data, policy or unregistered approaches: candidate scores are descriptive. Run baseline and changed variants on the same new evaluation set before reporting gains.')
    review(result, local_secrets(root))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['capture', 'verify', 'compare'])
    parser.add_argument('checkpoint', type=Path)
    parser.add_argument('--as-of', help='Client-local date, YYYY-MM-DD; required for capture')
    parser.add_argument('--run', type=Path, help='Candidate run directory for compare')
    parser.add_argument('--reference', choices=list(RUNS), default='test')
    args = parser.parse_args()
    if args.action == 'capture':
        if not args.as_of:
            parser.error('capture requires --as-of')
        snapshot = capture(args.checkpoint, args.as_of)
        print(f"Captured {len(snapshot['runs'])} audited runs from {snapshot['source_commit'][:7]}.")
    elif args.action == 'verify':
        report = verify(load(args.checkpoint))
        print(json.dumps(report, indent=2))
        if not report['matches']:
            raise SystemExit(1)
    else:
        if not args.run:
            parser.error('compare requires --run')
        print(json.dumps(compare(load(args.checkpoint), args.run, args.reference), indent=2))


if __name__ == '__main__':
    main()
