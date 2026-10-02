"""Further paired development cases for software evidence selection."""
import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from triage_bench.dataset import ROOT, read_jsonl, stamp, write_jsonl
from triage_bench.policy import VERSION as POLICY_VERSION
from .question_trial import DECISION, label, validate as validate_questions
from .transforms import sha
from .selection import ARMS, body

DIRECTORY = ROOT / 'data/experiment-3-selection-draft'
SPECS = [
    ('rectifier output comparison', 'power', 'conflict', 'outage',
     'Two independent instruments measure the same rectifier output at {asset} under the same load conditions. Instrument F reports 0 V, a supply malfunction; instrument N reports 48 V, a nominal supply reading.'),
    ('optical attenuation comparison', 'transport', 'conflict', 'outage',
     'Independent probes measure the same receive channel at {asset} under comparable conditions. Probe F reports optical loss of signal at -43 dBm, a transport malfunction; probe N reports -11 dBm and nominal receive operation.'),
    ('radio phase comparison', 'ran', 'conflict_first_nominal', 'degraded',
     'Independent radio instruments measure the same phase reference at {asset} under comparable conditions. Probe F reports a 280 microsecond offset and failed timing, a radio malfunction; probe N reports zero offset and nominal timing.'),
    ('packet discard measurement expiry', 'transport', 'stale_fault', 'degraded',
     'An independent diagnostic at {asset} records persistent egress packet discards, a transport malfunction. Current end-to-end probes confirm service degradation.'),
    ('antenna timing measurement gap', 'ran', 'unknown_fault', 'degraded',
     'An independent phase-lock diagnostic at {asset} reports failed antenna timing, a radio malfunction. Current independent service checks confirm degradation.'),
    ('dc feeder service association', 'power', 'relationship', 'outage',
     'An independent equipment-side meter at {asset} reports an open DC feeder and no equipment supply voltage, a power malfunction. Independent current service checks confirm an outage.'),
]


def build(directory=DIRECTORY):
    directory = Path(directory)
    if directory.exists():
        raise ValueError('Choose a new selection data directory.')
    records, keys = [], []
    for index, (family, domain, change, status, text) in enumerate(SPECS):
        opaque = sha(('selection-v1:' + family).encode())[:12]
        pair = 'NSS-' + opaque
        prefix = opaque[:5]
        sites = [prefix + '-s0', prefix + '-s1']
        asset, relay, spare = [prefix + '-' + suffix for suffix in ['sensor', 'branch', 'spare']]
        now = datetime(2026, 9, 4, 10, tzinfo=timezone.utc) + timedelta(hours=index)
        impact = {'status': status, 'affected_sites': len(sites), 'affected_site_ids': sites,
                  'basis': 'Independent current end-to-end service probes'}
        edges = [[site, relay] for site in sites] + [[relay, asset]]
        obs = {'asset_id': asset, 'detail': text.format(asset=asset),
               'observed_at': stamp(now - timedelta(minutes=1)), 'measured_at': stamp(now - timedelta(minutes=5)),
               'valid_for_minutes': 15, 'source': 'Synthetic independent diagnostic'}
        # Individual reports each describe only their own measurement.
        if change.startswith('conflict'):
            whole = text.format(asset=asset)
            first, second = whole.split('; ')
            intro, fault = first.rsplit('. ', 1)
            obs['detail'] = intro + '. ' + fault + '.'
            nominal = copy.deepcopy(obs)
            nominal['detail'] = intro + '. ' + second
            observations = [nominal, obs] if change == 'conflict_first_nominal' else [obs, nominal]
        else:
            observations = [obs]
        packet = {'operator': 'Northstar Telecom', 'decision_timestamp': stamp(now),
                  'ticket': {'title': 'Service measurement packet', 'description': 'Review independent service probes and instrument reports.'},
                  'service_impact': impact, 'observations': observations,
                  'topology': {'nodes': sites + [asset, relay, spare], 'edges': edges, 'coverage': 'complete',
                               'edge_semantics': 'depends_on', 'scope': 'required_service_dependencies',
                               'note': 'Required service dependencies, without protection or root-cause inference.'},
                  'change_record': {'status': 'none_reported', 'detail': 'No relevant change is reported.'}}
        a = {'id': pair + '-a', 'policy_version': POLICY_VERSION, 'input': packet}
        b = copy.deepcopy(a); b['id'] = pair + '-b'
        if change.startswith('conflict'):
            normal_index = 0 if change == 'conflict_first_nominal' else 1
            b['input']['observations'][normal_index]['measured_at'] = stamp(now - timedelta(minutes=91))
            path = f'input.observations[{normal_index}].measured_at'
            rationale = 'Comparable current measurements conflict in A. In B the nominal measurement is stale, so the current related malfunction supports its domain diagnostic.'
        elif change in {'stale_fault', 'unknown_fault'}:
            a['input']['observations'][0]['measured_at'] = None if change == 'unknown_fault' else stamp(now - timedelta(minutes=91))
            path = 'input.observations[0].measured_at'
            rationale = 'A lacks a current fault measurement. B supplies a current measurement on a visible affected-service path.'
        else:
            a['input']['topology']['edges'] = [[u, spare if v == asset else v] for u, v in edges]
            path = 'input.topology.edges'
            rationale = 'The complete map in A excludes the fault from affected-service dependencies. B establishes a visible path; neither map proves root cause.'
        records += [a, b]
        for r, answer in [(a, label('noc', impact, True)), (b, label(domain, impact))]:
            keys.append({'id': r['id'], 'split': 'development', 'incident_family_id': family, 'pair_id': pair,
                         'pair_kind': 'decision_change', 'changed_path': path, 'labels': answer,
                         'accepted_answers': {f: [v] for f, v in answer.items()}, 'label_rationale': rationale,
                         'review_status': 'draft_not_specialist_reviewed'})
    directory.mkdir(parents=True)
    write_jsonl(directory / 'development.inputs.jsonl', records); write_jsonl(directory / 'development.labels.jsonl', keys)
    manifest = {'version': 'experiment-3-selection-draft-1', 'operator': 'Northstar Telecom', 'synthetic': True,
                'reference_status': 'draft_not_specialist_reviewed', 'evaluation_status': 'development_only_no_held_out_set',
                'records': len(records), 'pairs': len(SPECS), 'families': len(SPECS),
                'human_decision': {'date': '2026-10-02', 'scope': 'Synthetic teaching decision; not network-specialist signoff', 'decision': DECISION},
                'telemetry_assumption': '15-minute validity, instrument classifications and conflict disposition are teaching assumptions, not validated network thresholds.',
                'sha256': {p.name: sha(p.read_bytes()) for p in directory.glob('*.jsonl')}}
    (directory / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    validate(directory)
    return manifest


def validate(directory=DIRECTORY):
    manifest = validate_questions(directory)
    records = read_jsonl(Path(directory) / 'development.inputs.jsonl')
    keys = read_jsonl(Path(directory) / 'development.labels.jsonl')
    old_ids, old_families = set(), set()
    for folder in ['experiment-3-question-draft', 'experiment-3-conflict-draft']:
        for key in read_jsonl(ROOT / 'data' / folder / 'development.labels.jsonl'):
            old_ids.add(key['id']); old_families.add(key['incident_family_id'])
    if any(k['id'] in old_ids or k['incident_family_id'] in old_families for k in keys):
        raise ValueError('A previously inspected family is reused.')
    for record in records:
        requests = [body(record, arm) for arm in ARMS]
        if any(req['questions'] != requests[0]['questions'] for req in requests):
            raise ValueError('Selection comparison changed the questions.')
    return manifest
