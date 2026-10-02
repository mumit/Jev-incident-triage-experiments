"""Deterministic input facts. No reference labels, model calls or state mutation."""
from collections import deque
from datetime import datetime
import copy
import hashlib
import json
import math

from triage_bench.experiments import compact_packet, focused_questions
from triage_bench.policy import TEXT

VARIANTS = {'baseline': 'Compact baseline', 'dependency': 'Dependency facts',
            'measurement': 'Measurement age', 'combined': 'Both facts'}
MODEL = 'jev-1.13.0'
VERSION = 'experiment-3-draft-1'


def sha(value):
    return hashlib.sha256(value).hexdigest()


def timestamp(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.utcoffset() is None:
        raise ValueError('Evidence timestamps require a timezone.')
    return result


def measurement_facts(packet):
    now = timestamp(packet['decision_timestamp'])
    facts = []
    for index, obs in enumerate(packet['observations']):
        arrived = timestamp(obs['observed_at'])
        if arrived > now:
            raise ValueError('Report arrival is after the decision time.')
        measured = obs.get('measured_at')
        limit = obs.get('valid_for_minutes')
        age = None
        if measured:
            when = timestamp(measured)
            if when > arrived:
                raise ValueError('Measurement must precede report arrival.')
            age = (now - when).total_seconds() / 60
        if limit is not None and (isinstance(limit, bool) or not isinstance(limit, (int, float)) or not math.isfinite(limit) or limit <= 0):
            raise ValueError('Declared validity must be positive finite minutes.')
        status = 'unknown' if age is None or limit is None else 'current' if age <= limit else 'stale'
        facts.append({'observation_index': index, 'reported_at': obs['observed_at'],
                      'measured_at': measured, 'report_age_minutes': (now - arrived).total_seconds() / 60,
                      'measurement_age_minutes': age, 'declared_valid_for_minutes': limit,
                      'freshness_status': status,
                      'basis': 'Declared telemetry validity, not an operationally validated threshold.'})
    return facts


def dependency_facts(packet):
    graph = packet.get('topology') or {}
    edges = graph.get('edges') or []
    raw_nodes = graph.get('nodes') or []
    if not isinstance(raw_nodes, list) or any(not isinstance(n, str) for n in raw_nodes):
        raise ValueError('Topology nodes must be identifiers.')
    nodes = set(raw_nodes)
    if any(not isinstance(n, str) for n in nodes) or len(nodes) > 256 or len(edges) > 512:
        raise ValueError('Invalid or oversized topology.')
    adjacency = {}
    for edge in edges:
        if not isinstance(edge, list) or len(edge) != 2 or any(not isinstance(n, str) for n in edge):
            raise ValueError('Dependencies require pairs of node identifiers.')
        nodes.update(edge)
        adjacency.setdefault(edge[0], []).append(edge[1])
    if len(nodes) > 256:
        raise ValueError('Topology exceeds 256 nodes.')
    valid_semantics = graph.get('edge_semantics') == 'depends_on' and graph.get('scope') == 'required_service_dependencies'
    complete = graph.get('coverage') == 'complete'
    sites = packet['service_impact'].get('affected_site_ids')
    count = packet['service_impact']['affected_sites']
    listed = sites if isinstance(sites, list) and all(isinstance(s, str) for s in sites) else []
    scope_known = isinstance(count, int) and not isinstance(count, bool) and isinstance(sites, list) and len(listed) == len(set(listed)) and count == len(listed)

    def path_to(start, target):
        queue = deque([(start, [start])])
        visited = {start}
        while queue:
            node, path = queue.popleft()
            if node == target:
                return path
            for parent in sorted(adjacency.get(node, [])):
                if parent not in visited:
                    visited.add(parent)
                    queue.append((parent, path + [parent]))
        return None

    def reachable_cycle(start):
        active, visited = set(), set()
        def visit(node):
            if node in active:
                return True
            if node in visited:
                return False
            visited.add(node); active.add(node)
            cycle = any(visit(parent) for parent in adjacency.get(node, []))
            active.remove(node)
            return cycle
        return visit(start)

    facts = []
    for index, obs in enumerate(packet['observations']):
        asset = obs.get('asset_id')
        paths, excluded, unknown = [], [], []
        for site in listed:
            known = valid_semantics and scope_known and site in nodes and asset in nodes
            path = path_to(site, asset) if known else None
            if path:
                paths.append({'site': site, 'path': path})
            elif known and complete and not reachable_cycle(site):
                excluded.append(site)
            else:
                unknown.append(site)
        relation = ('unknown' if not scope_known or not listed or not valid_semantics or unknown else
                    'all_listed_sites_depend' if len(paths) == len(listed) else
                    'no_listed_sites_depend' if not paths else 'some_listed_sites_depend')
        facts.append({'observation_index': index, 'asset_id': asset,
                      'edge_semantics': graph.get('edge_semantics'), 'declared_coverage': graph.get('coverage'),
                      'affected_site_scope_known': scope_known, 'relation': relation,
                      'supported_site_count': len(paths), 'excluded_site_count': len(excluded),
                      'unknown_site_count': len(unknown) if scope_known else None,
                      'supporting_paths': paths, 'excluded_sites': excluded, 'unknown_sites': unknown,
                      'basis': 'Reachability along declared required service dependencies. Supports a relationship, not a root cause.'})
    return facts


def transformed_packet(record, variant):
    if variant not in VARIANTS:
        raise ValueError('Unknown experiment 3 input variant.')
    # Select raw fields explicitly before applying the historical compact transform.
    # New telemetry fields are facts only; reference metadata never enters here.
    source = record['input']
    packet = {'decision_timestamp': source['decision_timestamp'],
              'service_impact': {k: copy.deepcopy(source['service_impact'][k]) for k in ['status', 'affected_sites', 'basis', 'affected_site_ids'] if k in source['service_impact']},
              'observations': [{k: copy.deepcopy(o.get(k)) for k in ['detail', 'observed_at', 'measured_at', 'valid_for_minutes', 'asset_id']} for o in source['observations']],
              'topology': {k: copy.deepcopy((source.get('topology') or {})[k]) for k in ['nodes', 'edges', 'edge_semantics', 'scope', 'coverage', 'note'] if k in (source.get('topology') or {})},
              'change_record': {k: copy.deepcopy(source['change_record'].get(k)) for k in ['status', 'detail']}}
    result = compact_packet(packet)
    if variant in {'dependency', 'combined'}:
        result['dependency_facts'] = dependency_facts(packet)
    if variant in {'measurement', 'combined'}:
        result['measurement_facts'] = measurement_facts(packet)
    return result


def request_body(record, variant):
    return {'model': MODEL, 'state': TEXT + '\nCurrent incident evidence:\n' + json.dumps(transformed_packet(record, variant), ensure_ascii=False, sort_keys=True),
            'questions': focused_questions()}
