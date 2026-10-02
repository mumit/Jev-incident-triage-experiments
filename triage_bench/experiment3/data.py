"""Manually specified draft scenario families with separate provisional reference decisions."""
import copy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path

from triage_bench.dataset import ROOT, read_jsonl, stamp, write_jsonl
from triage_bench.policy import VERSION as POLICY_VERSION, priority, OPTIONS
from .transforms import dependency_facts, measurement_facts, transformed_packet, VARIANTS, VERSION

DIRECTORY = ROOT / 'data/experiment-3-draft'
# Each tuple is a separately written teaching family; variations inside a family
# are correlated. No final evaluation families are generated during preparation.
TRAIN = [
 ('distribution splice', 'dependency', 'transport', 'Independent optical telemetry reports loss of signal at {asset}. Power readings are normal; no other domain diagnostic is available.', 'chain', 'outage'),
 ('return path queue', 'dependency', 'transport', 'Backhaul diagnostics locate packet loss on the return interface {asset}. Outbound probes pass. No radio diagnostic is available.', 'fork', 'degraded'),
 ('receiver calibration', 'age', 'ran', 'Radio receiver diagnostics at {asset} report low receive sensitivity during verified service degradation. Other domain diagnostics are unavailable.', 'fan', 'degraded'),
 ('equipment breaker', 'age', 'power', 'An independent meter at {asset} reports zero voltage after the DC breaker. Utility input is healthy. Service probes confirm an outage.', 'chain', 'outage'),
 ('subscriber control', 'age', 'core', 'Shared core policy-control telemetry at {asset} reports rejected subscriber sessions across independently checked access paths.', 'fork', 'degraded'),
 ('sector time feed', 'missing', 'ran', 'Sector radio timing diagnostics at {asset} report loss of synchronization. No corroborating domain telemetry is available.', 'fan', 'degraded'),
 ('truncated inventory', 'partial', 'noc', 'Optical diagnostics report a faulty transmitter at {asset}. Affected-site diagnostics are unavailable; the incident relationship needs checking.', 'fork', 'outage'),
 ('verified service recovery', 'recovery', 'noc', 'Independent service probes confirm recovery throughout the observation interval. No active fault evidence remains.', 'fan', 'none'),
 ('maintenance footprint', 'maintenance', 'noc', 'Current service impact extends beyond the maintenance footprint. The change scope does not explain all observations; no domain fault has been diagnosed.', 'chain', 'outage'),
 ('unrelated inventory append', 'inventory', 'transport', 'Independent optical diagnostics identify a failed required-service uplink {asset}. Other domain telemetry is unavailable.', 'fork', 'outage'),
 ('report delivery delay', 'arrival', 'ran', 'Radio scheduler diagnostics at {asset} show stalled task processing under low occupancy. Independent service probes confirm degradation.', 'chain', 'degraded'),
 ('bus meter disagreement', 'conflict', 'power', 'An independent DC meter at {asset} reads zero supply voltage on the equipment bus. Service probes confirm an outage.', 'fan', 'outage'),
]
DEVELOPMENT = [
 ('relay detour', 'dependency', 'transport', 'Microwave backhaul counters at {asset} show sustained receive failures. Independent affected-site service probes fail. Other domain diagnostics are unavailable.', 'split', 'outage'),
 ('exchange uplink map', 'dependency', 'transport', 'A hardware optical test confirms loss of signal at {asset}. Impacted service probes fail while site supply checks pass.', 'mesh', 'degraded'),
 ('roof supply display', 'age', 'power', 'A rectifier output measurement at {asset} reads below the equipment operating range. Independent service checks confirm an outage.', 'split', 'outage'),
 ('resolver trace delay', 'age', 'core', 'Shared core resolver traces at {asset} show failed lookups across independently checked access paths.', 'mesh', 'degraded'),
 ('sector sample without time', 'missing', 'ran', 'A radio timing monitor at {asset} records repeated synchronization faults. Independent service probes confirm degradation.', 'split', 'degraded'),
 ('feeder excerpt', 'partial', 'noc', 'An optical terminal at {asset} reports a hardware fault. The affected service has no other usable domain telemetry.', 'mesh', 'outage'),
 ('archive edge append', 'inventory', 'transport', 'An independent optical diagnostic records a malfunction on required service span {asset}. Affected-site service checks fail.', 'split', 'outage'),
 ('inventory not delivered', 'missing_topology', 'transport', 'A backhaul optical diagnostic confirms a malfunction at {asset}. Impacted service checks fail; no alternative domain evidence is available.', 'split', 'outage'),
 ('supply feed disagreement', 'conflict', 'power', 'A calibrated DC supply sensor at {asset} reports zero equipment-bus voltage during a verified service outage.', 'mesh', 'outage'),
]


def decisions(owner, impact, uncertain=False, check=None):
    return {'initial_owner': owner, 'priority': priority(impact),
            'next_check': check or ('inspect_radio' if owner == 'ran' else 'inspect_' + owner if owner != 'noc' else 'gather_evidence'),
            'insufficient_evidence': 'yes' if uncertain else 'no'}


def make_pair(spec, split, variant):
    family, kind, owner, detail, layout, status = spec
    opaque = hashlib.sha256(f'exp3:{split}:{family}:{variant}'.encode()).hexdigest()[:12]
    identifier = 'NS3-' + opaque
    n = 0 if status == 'none' else [1, 9, 12][variant % 3]
    sites = [opaque[:5] + '-s' + str(i) for i in range(n)]
    asset, first, second, other = [opaque[:5] + '-' + x for x in ['x', 'm', 'q', 'z']]
    if layout in {'chain', 'split'}:
        edges = [[s, first] for s in sites] + [[first, second], [second, asset]]
    elif layout in {'fork', 'mesh'}:
        edges = [[s, first if i % 2 else second] for i, s in enumerate(sites)] + [[first, asset], [second, asset]]
    else:
        edges = [[s, asset] for s in sites]
    if layout == 'split':
        gateways = [opaque[:5] + '-g' + str(i) for i in range(n)]
        edges = [[s, gateway] for s, gateway in zip(sites, gateways)] + [[gateway, first if i % 2 else second] for i, gateway in enumerate(gateways)] + [[first, second], [second, asset]]
    # Independent development layouts have a second tier rather than renamed training graphs.
    if layout == 'mesh':
        pivot = opaque[:5] + '-v'
        edges = [e if e[1] != asset else [e[0], pivot] for e in edges] + [[pivot, asset]]
    nodes = sorted({asset, other, first, second, *sites, *(node for e in edges for node in e)})
    now = datetime(2026, 6, 10, 12, tzinfo=timezone.utc) + timedelta(days=variant, minutes=int(opaque[:2], 16))
    obs = {'observed_at': stamp(now - timedelta(minutes=1)), 'measured_at': stamp(now - timedelta(minutes=5)),
           'valid_for_minutes': 15, 'asset_id': asset, 'source': 'Synthetic independent telemetry', 'detail': detail.format(asset=asset)}
    impact = {'status': status, 'affected_sites': n, 'affected_site_ids': sites, 'basis': 'Independent current service probes'}
    packet = {'operator': 'Northstar Telecom', 'decision_timestamp': stamp(now),
              'ticket': {'title': 'Network service observation', 'description': 'Inspect the supplied telemetry and dependencies.'},
              'observations': [obs], 'service_impact': impact,
              'topology': {'nodes': nodes, 'edges': edges, 'edge_semantics': 'depends_on',
                           'scope': 'required_service_dependencies', 'coverage': 'complete',
                           'note': 'Directed service dependencies for listed affected sites; no protection or capacity inference.'},
              'change_record': {'status': 'none_reported', 'detail': 'No relevant change record is supplied.'}}
    record = {'id': identifier + '-a', 'policy_version': POLICY_VERSION, 'input': packet}
    other_record = copy.deepcopy(record); other_record['id'] = identifier + '-b'
    a, b = decisions(owner, impact, owner == 'noc'), decisions(owner, impact, owner == 'noc')
    path = ''
    explanation = ''
    if kind == 'missing_topology':
        other_record['input']['topology'] = {}
        b = decisions('noc', impact, True)
        path = 'input.topology'
        explanation = 'The dependency inventory is unavailable; the observed component cannot be connected to the affected service.'
    elif kind in {'dependency', 'partial'}:
        # Remove every incoming link to the observed faulty asset, retaining the
        # node in the complete inventory. Only edges change in a dependency pair.
        disconnected = [[u, other if v == asset else v] for u, v in edges]
        if kind == 'dependency':
            other_record['input']['topology']['edges'] = disconnected
            b = decisions('noc', impact, True)
            path = 'input.topology.edges'
            explanation = 'The faulty component stops being a dependency of the affected sites; other domain evidence is unavailable.'
        else:
            record['input']['topology']['edges'] = disconnected
            other_record['input']['topology']['edges'] = disconnected
            other_record['input']['topology']['coverage'] = 'partial'
            a = b = decisions('noc', impact, True)
            path = 'input.topology.coverage'
            explanation = 'Complete absence becomes an unknown relationship; neither packet supports an investigating domain.'
    elif kind in {'age', 'missing'}:
        other_record['input']['observations'][0]['measured_at'] = None if kind == 'missing' else stamp(now - timedelta(minutes=95))
        b = decisions('noc', impact, True)
        path = 'input.observations[0].measured_at'
        explanation = 'The domain-specific measurement becomes stale or lacks a measurement time, despite a recent report.'
    elif kind == 'inventory':
        # Predeclare unrelated nodes to keep this intervention to the edge list.
        record['input']['topology']['nodes'] += [opaque[:5] + '-e', opaque[:5] + '-f']
        other_record['input']['topology']['nodes'] = copy.deepcopy(record['input']['topology']['nodes'])
        other_record['input']['topology']['edges'].append([opaque[:5] + '-e', opaque[:5] + '-f'])
        path = 'input.topology.edges'; explanation = 'An unrelated inventory edge leaves supported dependencies and decisions unchanged.'
    elif kind in {'arrival', 'recovery'}:
        other_record['input']['observations'][0]['observed_at'] = stamp(now - timedelta(minutes=3))
        if kind == 'recovery':
            a = b = decisions('noc', impact, False, 'monitor')
        path = 'input.observations[0].observed_at'; explanation = 'Report arrival changes while the same current measurement and disposition remain valid.'
    elif kind == 'maintenance':
        record['input']['change_record'] = {'status': 'scope_unexplained', 'detail': 'Maintenance affects one cabinet; impact extends beyond it.'}
        other_record['input']['change_record'] = copy.deepcopy(record['input']['change_record'])
        other_record['input']['observations'][0]['observed_at'] = stamp(now - timedelta(minutes=3))
        a = b = decisions('noc', impact, True, 'verify_change')
        path = 'input.observations[0].observed_at'; explanation = 'A small delivery-time change does not resolve the unexplained maintenance scope.'
    elif kind == 'conflict':
        normal = copy.deepcopy(obs)
        normal['detail'] = 'A second independent DC meter at ' + asset + ' reports nominal equipment-bus voltage. Its measurement timestamp is supplied separately.'
        record['input']['observations'].append(normal)
        other_record['input']['observations'].append(copy.deepcopy(normal))
        other_record['input']['observations'][1]['measured_at'] = stamp(now - timedelta(minutes=95))
        a, b = decisions('noc', impact, True), decisions('power', impact)
        path = 'input.observations[1].measured_at'
        explanation = 'Two current voltage reports conflict. An old nominal-voltage measurement does not contradict the current zero-voltage measurement.'
    keys = []
    for item, label in [(record, a), (other_record, b)]:
        keys.append({'id': item['id'], 'split': split, 'incident_family_id': family, 'pair_id': identifier,
                     'pair_kind': 'decision_change' if a != b else 'invariance', 'changed_path': path,
                     'labels': copy.deepcopy(label), 'accepted_answers': {f: [v] for f, v in label.items()},
                     'label_rationale': explanation, 'review_status': 'draft_not_specialist_reviewed'})
    return [record, other_record], keys


def build(output=DIRECTORY):
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError('Draft pack already exists; choose a new version directory.')
    manifest = {'version': VERSION, 'operator': 'Northstar Telecom', 'synthetic': True,
                'reference_status': 'draft_not_specialist_reviewed', 'evaluation_status': 'development_only_no_held_out_set',
                'telemetry_assumption': 'Each observation declares a 15-minute validity window; this teaching assumption needs specialist review.',
                'splits': {}}
    for split, specs, count in [('train', TRAIN, 3), ('development', DEVELOPMENT, 2)]:
        records, keys = [], []
        for spec in specs:
            for index in range(count):
                pair, answers = make_pair(spec, split, index)
                records.extend(pair); keys.extend(answers)
        write_jsonl(output / (split + '.inputs.jsonl'), records)
        write_jsonl(output / (split + '.labels.jsonl'), keys)
        manifest['splits'][split] = {'records': len(records), 'families': len(specs), 'pairs': len(keys) // 2}
    manifest['sha256'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output.glob('*.jsonl'))}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    validate(output)
    return manifest


def changed_paths(a, b, prefix='input'):
    if a == b:
        return []
    if isinstance(a, dict) and isinstance(b, dict) and set(a) == set(b):
        return [p for key in a for p in changed_paths(a[key], b[key], prefix + '.' + key)]
    # Edges and arbitrary topology arrays are treated as a single intervention;
    # observation arrays are expanded to permit exact measurement-time changes.
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b) and prefix == 'input.observations':
        return [p for i, (x, y) in enumerate(zip(a, b)) for p in changed_paths(x, y, prefix + '[' + str(i) + ']')]
    return [prefix]


def validate(directory=DIRECTORY):
    directory = Path(directory)
    manifest = json.loads((directory / 'manifest.json').read_text())
    if set(manifest['sha256']) != {split + '.' + kind + '.jsonl' for split in ['train', 'development'] for kind in ['inputs', 'labels']}:
        raise ValueError('Unexpected draft manifest paths.')
    seen_ids, seen_families, seen_packets = set(), set(), set()
    counts = {}
    for split in ['train', 'development']:
        records = read_jsonl(directory / (split + '.inputs.jsonl'))
        keys = read_jsonl(directory / (split + '.labels.jsonl'))
        by_id = {k['id']: k for k in keys}
        if len(by_id) != len(keys) or len({r['id'] for r in records}) != len(records) or set(by_id) != {r['id'] for r in records}:
            raise ValueError('Draft packet/reference IDs differ or repeat.')
        families = {k['incident_family_id'] for k in keys}
        if seen_families & families:
            raise ValueError('Family leakage between training and development.')
        seen_families |= families
        pairs = {}
        for record in records:
            if set(record) != {'id', 'policy_version', 'input'} or record['id'] in seen_ids or record['policy_version'] != POLICY_VERSION:
                raise ValueError('Invalid public packet or duplicate ID.')
            seen_ids.add(record['id']); packet = record['input']; key = by_id[record['id']]
            encoded = json.dumps(packet, sort_keys=True)
            if encoded in seen_packets:
                raise ValueError('Duplicate packet across draft splits.')
            seen_packets.add(encoded)
            if packet['operator'] != 'Northstar Telecom' or key['review_status'] != 'draft_not_specialist_reviewed' or key['split'] != split:
                raise ValueError('Invalid operator or reference status.')
            impact = packet['service_impact']
            count, sites = impact['affected_sites'], impact['affected_site_ids']
            if isinstance(count, bool) or not isinstance(count, int) or count < 0 or not isinstance(sites, list) or any(not isinstance(s, str) for s in sites) or len(set(sites)) != len(sites) or len(sites) != count:
                raise ValueError('Affected-site identities must match the declared count.')
            if impact['status'] not in {'outage', 'degraded', 'none', 'unknown'} or impact['status'] == 'none' and count != 0:
                raise ValueError('Invalid service impact.')
            if key['labels']['priority'] != priority(packet['service_impact']):
                raise ValueError('Priority differs from the unchanged policy.')
            for f, choices in OPTIONS.items():
                if key['labels'][f] not in choices or key['labels'][f] not in key['accepted_answers'][f] or not set(key['accepted_answers'][f]) <= set(choices):
                    raise ValueError('Invalid draft decision.')
            measurement_facts(packet); dependency_facts(packet)
            for variant in VARIANTS:
                transformed_packet(record, variant)
            pairs.setdefault(key['pair_id'], []).append((record, key))
        for pair in pairs.values():
            if len(pair) != 2 or len({k['incident_family_id'] for _, k in pair}) != 1:
                raise ValueError('Incomplete controlled pair.')
            (a, ka), (b, kb) = pair
            if changed_paths(a['input'], b['input']) != [ka['changed_path']] or ka['changed_path'] != kb['changed_path']:
                raise ValueError('Pair changes more than the declared field.')
            changed = ka['labels'] != kb['labels']
            if changed != (ka['pair_kind'] == 'decision_change') or ka['pair_kind'] != kb['pair_kind']:
                raise ValueError('Pair reference changes differ from its purpose.')
        counts[split] = len(records)
        if manifest['splits'][split] != {'records': len(records), 'families': len(families), 'pairs': len(pairs)}:
            raise ValueError('Draft manifest counts differ.')
    for filename, expected in manifest['sha256'].items():
        if hashlib.sha256((directory / filename).read_bytes()).hexdigest() != expected:
            raise ValueError('Draft checksum mismatch.')
    return counts
