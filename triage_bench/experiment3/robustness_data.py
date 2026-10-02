"""Further development controls for the unchanged evidence-selection filter."""
import copy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
from triage_bench.dataset import ROOT, read_jsonl, stamp, write_jsonl
from triage_bench.policy import VERSION as POLICY_VERSION
from .question_trial import DECISION, label
from .selection_data import validate as validate_selection
from .transforms import sha

DIRECTORY = ROOT / 'data/experiment-3-robustness-draft'
FAMILIES = ['optical validity boundary', 'partial radio branch visibility',
            'missing feeder inventory', 'concurrent supply and forwarding faults']


def build(directory=DIRECTORY):
    directory = Path(directory)
    if directory.exists():
        raise ValueError('Choose a new robustness data directory.')
    records, keys = [], []
    for index, family in enumerate(FAMILIES):
        opaque = sha(('selection-robustness-v1:' + family).encode())[:12]
        pair, prefix = 'NSR-' + opaque, opaque[:5]
        sites = [prefix + '-s0', prefix + '-s1']
        gateway, asset, supply = [prefix + '-' + suffix for suffix in ['gateway', 'device', 'supply']]
        now = datetime(2026, 9, 21, 10, tzinfo=timezone.utc) + timedelta(hours=index)
        status = 'degraded' if index == 1 else 'outage'
        impact = {'status': status, 'affected_sites': 2, 'affected_site_ids': sites,
                  'basis': 'Independent current end-to-end service probes'}
        def observation(component, text, age=4):
            return {'asset_id': component, 'detail': text, 'measured_at': stamp(now - timedelta(minutes=age)),
                    'observed_at': stamp(now - timedelta(minutes=1)), 'valid_for_minutes': 15,
                    'source': 'Synthetic independent instrument'}
        details = [
            'An independent receive probe at '+asset+' reads -44 dBm and reports optical loss of signal, a transport malfunction. It measures the same receive channel under the same operating conditions as the nominal probe.',
            'An independent radio diagnostic at '+asset+' reports failed receive processing, a radio-access malfunction. Independent current end-to-end probes confirm degradation.',
            'An independent load-side meter at '+asset+' reads 0 V and reports failed DC feeder supply, a power malfunction. Independent current service checks confirm an outage.',
            'An independent supply meter at '+supply+' reads 0 V and reports failed equipment supply, a power malfunction. Current service checks confirm an outage.'
        ]
        observations = [observation(supply if index == 3 else asset, details[index])]
        edges = [[s, gateway] for s in sites] + [[gateway, asset]]
        if index == 3:
            edges.append([asset, supply])
            observations.append(observation(asset, 'An independent forwarding test at '+asset+' reports repeated packet forwarding failures, a transport malfunction. Its report does not attribute either malfunction to the other.'))
        if index == 0:
            observations.append(observation(asset, 'A second independent receive probe at '+asset+' reads -10 dBm and reports nominal optical reception. It measures the same receive channel under the same operating conditions as the loss-of-signal probe.', age=15))
        topology = {'nodes': sites + [gateway, asset, supply], 'edges': edges, 'coverage': 'complete',
                    'edge_semantics': 'depends_on', 'scope': 'required_service_dependencies',
                    'note': 'Declared required-service paths, without redundancy or causal inference.'}
        packet = {'operator': 'Northstar Telecom', 'decision_timestamp': stamp(now),
                  'ticket': {'title': 'Current diagnostic evidence', 'description': 'Review current independent service checks and the available measurements.'},
                  'service_impact': impact, 'observations': observations, 'topology': topology,
                  'change_record': {'status': 'none_reported', 'detail': 'No relevant change is reported.'}}
        a = {'id': pair+'-a', 'policy_version': POLICY_VERSION, 'input': packet}
        b = copy.deepcopy(a); b['id'] = pair+'-b'
        if index == 0:
            b['input']['observations'][1]['measured_at'] = stamp(now - timedelta(minutes=15, seconds=1))
            path = 'input.observations[1].measured_at'
            answer_a, answer_b = label('noc', impact, True), label('transport', impact)
            rationale = 'The declared window includes exactly 15 minutes. A retains two current comparable contradictory reports. One second beyond the window excludes the nominal report in B; the current related fault supports transport.'
        elif index == 1:
            # Only one listed site has a visible path. Partial inventory does not
            # establish the other site's absence, but one path supports investigation.
            for r in [a, b]:
                r['input']['topology']['edges'] = [e for e in edges if e[0] != sites[1]]
            a['input']['topology']['coverage'] = 'partial'
            path = 'input.topology.coverage'
            answer_a = answer_b = label('ran', impact)
            rationale = 'One listed affected site has a visible required-service path to the current radio fault in both maps. Partial coverage cannot prove absence for the other site. The frozen questions require at least one supporting path, not support for every site.'
        elif index == 2:
            a['input']['topology'] = {}
            path = 'input.topology'
            answer_a, answer_b = label('noc', impact, True), label('power', impact)
            rationale = 'A has a current fault but no declared relationship to affected services. B supplies the missing visible paths. The user-selected teaching rule retains NOC until that relationship is supported.'
        else:
            b['input']['observations'][1]['measured_at'] = stamp(now - timedelta(minutes=61))
            path = 'input.observations[1].measured_at'
            answer_a, answer_b = label('noc', impact, True), label('power', impact)
            rationale = 'Both distinct domains have current related malfunctions in A. The frozen no-unique-domain clause supplies the provisional NOC disposition; it does not specify investigation sequencing. In B the transport measurement is stale and only the current related supply fault supports a domain. Specialist review of the multi-domain disposition is pending.'
        records += [a, b]
        for r, answer in [(a, answer_a), (b, answer_b)]:
            keys.append({'id': r['id'], 'split': 'development', 'incident_family_id': family, 'pair_id': pair,
                         'pair_kind': 'invariance' if answer_a == answer_b else 'decision_change', 'changed_path': path,
                         'labels': answer, 'accepted_answers': {f:[v] for f,v in answer.items()}, 'label_rationale': rationale,
                         'review_status': 'draft_not_specialist_reviewed'})
    directory.mkdir(parents=True)
    write_jsonl(directory/'development.inputs.jsonl', records); write_jsonl(directory/'development.labels.jsonl', keys)
    manifest = {'version': 'experiment-3-robustness-draft-1', 'operator': 'Northstar Telecom', 'synthetic': True,
                'records': 8, 'pairs': 4, 'families': 4, 'reference_status': 'draft_not_specialist_reviewed',
                'evaluation_status': 'development_only_no_held_out_set',
                'human_decision': {'date': '2026-10-02', 'scope': 'Synthetic teaching decision; not network-specialist signoff', 'decision': DECISION},
                'telemetry_assumption': '15-minute inclusive validity and multi-domain NOC disposition are provisional. Instrument classifications and required-service paths are teaching assumptions.',
                'sha256': {p.name:sha(p.read_bytes()) for p in sorted(directory.glob('*.jsonl'))}}
    (directory/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    validate(directory)
    return manifest


def validate(directory=DIRECTORY):
    manifest = validate_selection(directory)
    old = read_jsonl(ROOT/'data/experiment-3-selection-draft/development.labels.jsonl')
    families, ids = {k['incident_family_id'] for k in old}, {k['id'] for k in old}
    keys = read_jsonl(Path(directory)/'development.labels.jsonl')
    if any(k['incident_family_id'] in families or k['id'] in ids for k in keys):
        raise ValueError('Earlier selection family reused.')
    return manifest
