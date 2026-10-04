"""Public-data preflight. No model inference or scoring; references stay separate."""
import hashlib
import json
import math
from pathlib import Path
import re
from urllib.request import urlopen

REVISION = 'afeacb11bcc94dadfd1c8f483ee4377b2b8b614e'
REPOSITORY = 'phamquiluan/RCAEval'
AUDIT_CASES = ('re2ob_checkoutservice_cpu_1', 're2ob_currencyservice_delay_1',
               're2ob_emailservice_socket_1')
FILES = ('inject_time.txt', 'metrics.parquet', 'logs.parquet', 'traces.parquet')
METRICS = {'cpu', 'mem', 'diskio', 'socket', 'workload', 'error', 'latency-50', 'latency-90'}
MAX_FILE_BYTES = 30_000_000


def sha(data):
    return hashlib.sha256(data).hexdigest()


def fetch(url, limit=MAX_FILE_BYTES):
    with urlopen(url, timeout=45) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError('Download exceeds the preflight size limit.')
    return data


def download(folder):
    """Download three fixed exploratory cases, checking pinned publisher hashes."""
    folder = Path(folder)
    manifest = folder / 'manifest.json'
    if manifest.exists():
        raise ValueError('A recorded download already exists; use another folder.')
    folder.mkdir(parents=True, exist_ok=True)
    base = f'https://huggingface.co/datasets/{REPOSITORY}/resolve/{REVISION}'
    entries = []
    for case in AUDIT_CASES:
        tree = json.loads(fetch(f'https://huggingface.co/api/datasets/{REPOSITORY}/tree/{REVISION}/{case}'))
        by_name = {row['path']: row for row in tree if row['type'] == 'file'}
        for name in FILES:
            path = f'{case}/{name}'
            source = by_name[path]
            if not 0 < source['size'] <= MAX_FILE_BYTES:
                raise ValueError('Source size exceeds preflight limit.')
            destination = folder / 'raw' / path
            data = destination.read_bytes() if destination.exists() else fetch(f'{base}/{path}', source['size'])
            if len(data) != source['size']:
                raise ValueError('Downloaded size does not match publisher metadata.')
            if 'lfs' in source:
                expected, actual = source['lfs']['oid'], sha(data)
            else:
                expected = source['oid']
                actual = hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest()
            if actual != expected:
                raise ValueError('Downloaded content does not match publisher hash.')
            destination.parent.mkdir(parents=True, exist_ok=True)
            if not destination.exists():
                destination.write_bytes(data)
            entries.append({'path': path, 'bytes': len(data), 'sha256': sha(data),
                            'publisher_hash': expected})
    index = fetch(f'{base}/cases.parquet', 100_000)
    index_path = folder / 'cases.parquet'
    if index_path.exists() and index_path.read_bytes() != index:
        raise ValueError('Existing index differs; use another folder.')
    index_path.write_bytes(index)
    result = {'schema': 'public-data-download-1', 'repository': REPOSITORY,
              'revision': REVISION, 'index_sha256': sha(index), 'files': entries}
    manifest.write_text(json.dumps(result, indent=2) + '\n')
    return result


def verify(folder):
    folder = Path(folder)
    manifest = json.loads((folder / 'manifest.json').read_text())
    if manifest['revision'] != REVISION:
        raise ValueError('Unexpected public-data revision.')
    expected = {f'{case}/{name}' for case in AUDIT_CASES for name in FILES}
    paths = [row['path'] for row in manifest['files']]
    if len(paths) != len(expected) or set(paths) != expected:
        raise ValueError('Unexpected, duplicate or missing source files.')
    for row in manifest['files']:
        data = (folder / 'raw' / row['path']).read_bytes()
        if sha(data) != row['sha256'] or len(data) != row['bytes']:
            raise ValueError('Public source fingerprint changed.')
    if sha((folder / 'cases.parquet').read_bytes()) != manifest['index_sha256']:
        raise ValueError('Public index fingerprint changed.')
    return manifest


def percentile(values, fraction):
    if not values:
        return None
    values = sorted(values)
    position = (len(values) - 1) * fraction
    low, high = math.floor(position), math.ceil(position)
    return values[low] + (values[high] - values[low]) * (position - low)


def finite(values):
    return [float(v) for v in values if isinstance(v, (int, float)) and math.isfinite(v)]


def metric_packet(columns, boundary, limit=12):
    """Uses metric columns and a known incident boundary, never an index row."""
    times = columns.get('time', [])
    if not times or any(not isinstance(t, int) or not 1_000_000_000 <= t < 10_000_000_000 for t in times):
        raise ValueError('Expected epoch-second metric timestamps.')
    if times != sorted(set(times)) or not min(times) < boundary <= max(times):
        raise ValueError('Invalid timeline or incident boundary.')
    before = [i for i, t in enumerate(times) if t < boundary]
    after = [i for i, t in enumerate(times) if t >= boundary]
    evidence, services = [], set()
    for column, values in columns.items():
        if column == 'time':
            continue
        if not re.fullmatch(r'[a-z][a-z0-9-]*_[a-z][a-z0-9-]*', column) or len(values) != len(times):
            raise ValueError('Unsupported metric schema.')
        service, metric = column.split('_', 1)
        if metric not in METRICS:
            raise ValueError('Unrecognized metric; do not forward answer metadata.')
        services.add(service)
        left, right = finite([values[i] for i in before]), finite([values[i] for i in after])
        a, b = percentile(left, .5), percentile(right, .5)
        q10, q90 = percentile(left, .1), percentile(left, .9)
        scale = max(q90 - q10, abs(a) * .01, 1e-12) if a is not None else None
        score = abs(b - a) / scale if a is not None and b is not None else None
        evidence.append({'service': service, 'metric': metric, 'source_column': column,
                         'before_valid': len(left), 'before_missing': len(before) - len(left),
                         'after_valid': len(right), 'after_missing': len(after) - len(right),
                         'before_median': a, 'before_p10': q10, 'before_p90': q90,
                         'after_median': b, 'baseline_scale': scale, 'change_score': score})
    ranked = sorted(evidence, key=lambda r: (-(r['change_score'] if r['change_score'] is not None else -1), r['source_column']))
    return {'task': 'Identify the faulty service from observed metric changes, or withhold if evidence is insufficient.',
            'window_condition': 'Known fault-injection boundary; not automatic incident detection.',
            'windows': {'start_epoch_seconds': min(times), 'boundary_epoch_seconds': boundary,
                        'end_epoch_seconds': max(times), 'before_rows': len(before), 'after_rows': len(after)},
            'candidate_services': sorted(services), 'metric_count': len(evidence),
            'summary_rule': 'Top absolute median shifts divided by max(baseline p90-p10, 1% absolute baseline median, 1e-12); this is change evidence, not a causal probability.',
            'metric_evidence': ranked[:limit]}


def prepare(folder):
    """Write draft metric inputs separately from references; leave raw files intact."""
    import pyarrow.parquet as pq
    folder = Path(folder)
    manifest = verify(folder)
    for output in ('prepared-inputs.json', 'references.json', 'profile.json'):
        if (folder / output).exists():
            raise ValueError('Prepared evidence exists; do not overwrite it.')
    index = pq.read_table(folder / 'cases.parquet').to_pylist()
    indexed = {row['case']: row for row in index}
    packets, references, profiles = [], [], []
    for case in AUDIT_CASES:
        source = folder / 'raw' / case
        boundary = int((source / 'inject_time.txt').read_text())
        row = indexed[case]
        if boundary != row['inject_time']:
            raise ValueError('Injection boundary differs from the source index.')
        metrics = pq.read_table(source / 'metrics.parquet')
        columns = metrics.to_pydict()
        state = metric_packet(columns, boundary)
        if (state['windows']['before_rows'], state['windows']['after_rows']) != (row['normal_timesteps'], row['faulty_timesteps']):
            raise ValueError('Metric windows differ from the source index.')
        identifier = 'PUB-' + sha(case.encode())[:12]
        packets.append({'case_id': identifier, 'state': state})
        references.append({'case_id': identifier, 'source_case': case,
                           'root_cause_service': row['root_cause_service'], 'fault': row['fault'],
                           'group': f"{row['system']}/{row['root_cause_service']}/{row['fault']}"})
        profile = {'case_id': identifier, 'rows': {}, 'schemas': {}}
        for kind in ('metrics', 'logs', 'traces'):
            metadata = pq.read_metadata(source / f'{kind}.parquet')
            profile['rows'][kind] = metadata.num_rows
            profile['schemas'][kind] = metadata.schema.names
        if (profile['rows']['logs'], profile['rows']['traces']) != (row['n_logs'], row['n_traces']):
            raise ValueError('Log or trace row count differs from the source index.')
        profiles.append(profile)
    profile = {'schema': 'public-data-preflight-1', 'revision': REVISION,
               'index_cases': len(index), 'dataset': 'RE2-OB',
               'dataset_cases': sum(row['dataset'] == 'RE2-OB' for row in index),
               'download_bytes': sum(row['bytes'] for row in manifest['files']),
               'scope': 'Exploratory audit; no inference, training or performance evaluation.',
               'files': manifest['files'], 'index_sha256': manifest['index_sha256'],
               'cases': profiles, 'input_sha256': sha(json.dumps(packets, sort_keys=True).encode()),
               'references_sha256': sha(json.dumps(references, sort_keys=True).encode())}
    root = Path(__file__).resolve().parents[1]
    profile['source_sha256'] = {name: sha((root / name).read_bytes()) for name in
                                ('triage_bench/public_data.py', 'scripts/prepare_public_data.py')}
    for name, data in [('prepared-inputs.json', packets), ('references.json', references), ('profile.json', profile)]:
        (folder / name).write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')
    return profile
