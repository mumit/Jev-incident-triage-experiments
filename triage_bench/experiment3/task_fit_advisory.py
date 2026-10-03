"""Versioned analyst-facing boundary and one frozen held-out evaluation.

Historical inference modules remain unchanged. All outputs require analyst
review; qualifying readings never authorize a ticket assignment or action.
"""
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from triage_bench.dataset import ROOT, read_jsonl, write_jsonl
from triage_bench.runner import NoRedirect, clean_api_key
from .task_fit_data import DIRECTORY
from .task_fit_trial import check_freeze, prepare, normalize, finish, verify, packet
from .hosted import encoded, redact
from .transforms import MODEL, sha

SCHEMA = 'task-fit-analyst-boundary-1'
EVALUATION_OUTPUT = 'runs/task-fit/evaluation-2026-10-03-v1'
EXTRA_SOURCES = ['triage_bench/experiment3/task_fit_advisory.py', 'scripts/run_task_fit_advisory.py']
CRITERIA = {'maximum_wrong_domain_recommendations': 0,
            'maximum_qualifying_reading_errors': 0,
            'maximum_qualifying_fault_misses': 0,
            'minimum_reading_coverage': .5,
            'minimum_domain_coverage': .25,
            'maximum_failed_or_missing': 0}


def decision(record, row, threshold):
    valid = bool(row and row.get('status') == 'ok')
    qualifies = bool(valid and row['reading'] in {'fault', 'normal'} and
                     row.get('probabilities', {}).get(row['reading'], -1) >= threshold)
    result = packet(record, row['reading']) if valid else None
    domain = result['predictions']['initial_owner'] if result else None
    recommend = bool(qualifies and domain != 'noc' and
                     result['predictions']['insufficient_evidence'] == 'no')
    reason = 'failed_or_missing' if not valid else 'unknown_reading' if row['reading'] == 'unknown' else 'below_advisory_threshold' if not qualifies else 'domain_recommendation' if recommend else 'policy_retains_noc'
    return {'qualifying_reading': qualifies, 'domain_recommendation': domain if recommend else None,
            'disposition': reason, 'policy_result': result,
            'analyst_review_required': True, 'automatic_assignment': False}


def assess(output, boundary, directory=DIRECTORY):
    output = Path(output); verify(output, directory)
    summary = json.loads((output / 'summary.json').read_text())
    arm = boundary['arm']; threshold = boundary['advisory_threshold']
    if summary['split'] not in {'calibration', 'evaluation'} or list(summary['arms']) != [arm]:
        raise ValueError('Assess only the frozen calibration or evaluation reader.')
    records = read_jsonl(output / 'inputs.jsonl')
    refs = {r['id']: r['reading'] for r in read_jsonl(output / 'observations.jsonl')}
    keys = {r['id']: r['labels'] for r in read_jsonl(output / 'labels.jsonl')}
    rows = {r['id']: r for r in read_jsonl(output / 'responses.jsonl') if r['arm'] == arm}
    scored = []; readings = routes = errors = misses = wrong_domains = failed = 0
    for record in records:
        identifier = record['id']; row = rows.get(identifier)
        d = decision(record, row, threshold); failed += not row or row.get('status') != 'ok'
        if d['qualifying_reading']:
            readings += 1; errors += row['reading'] != refs[identifier]
            misses += refs[identifier] == 'fault' and row['reading'] != 'fault'
        if d['domain_recommendation']:
            routes += 1; wrong_domains += d['domain_recommendation'] != keys[identifier]['initial_owner']
        scored.append({'id': identifier, **d})
    n = len(records)
    values = {'wrong_domain_recommendations': wrong_domains, 'qualifying_reading_errors': errors,
              'qualifying_fault_misses': misses, 'reading_coverage': readings / n if n else 0,
              'domain_coverage': routes / n if n else 0, 'failed_or_missing': failed}
    checks = {name: values[name.removeprefix('maximum_').removeprefix('minimum_')] >= limit if name.startswith('minimum_')
              else values[name.removeprefix('maximum_')] <= limit for name, limit in boundary['research_criteria'].items()}
    return {'schema': 'task-fit-analyst-assessment-1', 'split': summary['split'],
            'summary_sha256': sha((output / 'summary.json').read_bytes()),
            'boundary_sha256': sha(encoded(boundary)), 'reports': n, 'qualifying_readings': readings,
            'domain_recommendations': routes, 'noc_or_clarification': n - routes,
            'analyst_review_required': n, 'advisory_threshold': threshold, **values,
            'research_checks': checks, 'meets_research_criteria': all(checks.values()),
            'interpretation': 'Synthetic research criteria only. All reports require analyst review. No operational error budget, automatic assignment or live workload benefit is established.',
            'cases': scored}


def freeze_boundary(candidate, calibration, output, directory=DIRECTORY):
    candidate = Path(candidate); calibration = Path(calibration); output = Path(output)
    if output.exists(): raise ValueError('Analyst boundary checkpoints are immutable.')
    arm = json.loads(candidate.read_text())['arm']
    check_freeze(candidate, arm, directory); verify(calibration, directory)
    summary = json.loads((calibration / 'summary.json').read_text())
    if summary['split'] != 'calibration' or summary['status'] != 'completed' or list(summary['arms']) != [arm]:
        raise ValueError('Complete frozen-reader calibration before selecting an advisory boundary.')
    # No evaluation labels or responses enter selection. Maximize qualifying
    # reading coverage with zero observed reading errors and fault misses;
    # ties choose the lowest threshold. Unknown always needs clarification.
    points = [p for p in summary['review_curves'][arm]['points']
              if p['reading_errors'] == 0 and p['accepted_fault_misses'] == 0 and p['eligible_recommendations']]
    if not points: raise ValueError('Calibration supplies no error-free advisory boundary.')
    selected = min(points, key=lambda p: (-p['eligible_recommendations'], p['threshold']))
    result = {'schema': SCHEMA, 'mode': 'analyst_facing', 'user_decision': 'Analyst-facing recommendations first, October 3, 2026.',
              'arm': arm, 'model': MODEL, 'advisory_threshold': selected['threshold'],
              'selection_rule': 'Maximum calibration reading coverage with zero observed reading errors and qualifying fault misses; lowest threshold breaks ties. Evaluation plays no part.',
              'analyst_review': 'Required for every report, including high-probability fault and normal readings. The analyst owns initial-team assignment.',
              'display_rule': 'Show a domain suggestion only for qualifying fault/normal readings when the frozen policy has sufficient evidence for a domain. Otherwise show NOC retention or request clarification, with the underlying reading and raw reply inspectable.',
              'research_criteria': CRITERIA,
              'criteria_status': 'Author-set provisional synthetic study criteria, not user-approved operating limits. Half the reports must yield qualifying readings and a quarter domain suggestions to exercise the assisted workflow; zero observed errors are a research gate, not a statistical safety claim.',
              'candidate_sha256': sha(candidate.read_bytes()),
              'calibration_summary_sha256': sha((calibration / 'summary.json').read_bytes()),
              'source_sha256': {name: sha((ROOT / name).read_bytes()) for name in EXTRA_SOURCES},
              'evaluation_output': EVALUATION_OUTPUT,
              'evaluation_rule': 'One 24-call evaluation with reader, policy, threshold and criteria frozen beforehand. Failures stay in denominators. No automatic retry, retuning or replacement run.',
              'status': 'analyst_boundary_frozen_evaluation_unrun'}
    calibration_result = assess(calibration, result, directory)
    if not calibration_result['meets_research_criteria']:
        raise ValueError('The frozen boundary fails the provisional calibration criteria.')
    output.write_text(json.dumps(result, indent=2) + '\n')
    return result


def check_boundary(path, candidate, calibration, directory=DIRECTORY):
    boundary = json.loads(Path(path).read_text())
    if (boundary.get('schema') != SCHEMA or boundary.get('mode') != 'analyst_facing' or
        boundary.get('research_criteria') != CRITERIA or boundary.get('evaluation_output') != EVALUATION_OUTPUT or
        set(boundary.get('source_sha256', {})) != set(EXTRA_SOURCES)):
        raise ValueError('Invalid analyst boundary.')
    if boundary['candidate_sha256'] != sha(Path(candidate).read_bytes()): raise ValueError('Candidate checkpoint changed.')
    check_freeze(candidate, boundary['arm'], directory); verify(calibration, directory)
    if boundary['calibration_summary_sha256'] != sha((Path(calibration) / 'summary.json').read_bytes()): raise ValueError('Calibration evidence changed.')
    if any(sha((ROOT / name).read_bytes()) != value for name, value in boundary['source_sha256'].items()): raise ValueError('Analyst evaluation source changed.')
    summary = json.loads((Path(calibration) / 'summary.json').read_text())
    eligible = [p for p in summary['review_curves'][boundary['arm']]['points'] if p['reading_errors'] == 0 and p['accepted_fault_misses'] == 0 and p['eligible_recommendations']]
    expected = min(eligible, key=lambda p: (-p['eligible_recommendations'], p['threshold']))['threshold']
    if boundary.get('advisory_threshold') != expected: raise ValueError('Advisory threshold changed.')
    return boundary


def run_evaluation(profile, boundary_path, candidate, calibration, directory=DIRECTORY):
    boundary = check_boundary(boundary_path, candidate, calibration, directory)
    plan, records, requests = prepare(profile, 'evaluation', [boundary['arm']], directory)
    key = clean_api_key(profile.get('api_key', ''))
    if not key: raise ValueError('A server-side Jev key is required.')
    output = ROOT / boundary['evaluation_output']
    if output.exists(): raise ValueError('The preregistered evaluation already exists; do not rerun or replace it.')
    plan.update(analyst_boundary=boundary, analyst_boundary_file_sha256=sha(Path(boundary_path).read_bytes()))
    plan['source_sha256'].update(boundary['source_sha256'])
    output.mkdir(parents=True)
    write_jsonl(output / 'inputs.jsonl', records); write_jsonl(output / 'requests.jsonl', requests)
    for kind in ('labels', 'observations'):
        write_jsonl(output / f'{kind}.jsonl', read_jsonl(Path(directory) / f'evaluation.{kind}.jsonl'))
    plan['started_at'] = datetime.now(timezone.utc).isoformat()
    (output / 'protocol.json').write_text(json.dumps(plan, indent=2) + '\n')
    opener = urllib.request.build_opener(NoRedirect()); rows = []; reason = None; consecutive = 0
    with (output / 'responses.jsonl').open('x') as stream:
        for req in requests:
            row = {k: req[k] for k in ('id', 'arm', 'repetition', 'request_sha256')}; row['status'] = 'ok'
            start = time.perf_counter()
            try:
                wire = urllib.request.Request(profile['endpoint'], data=encoded(req['body']), headers={'Content-Type': 'application/json', 'Authorization': 'Bearer ' + key}, method='POST')
                with opener.open(wire, timeout=30) as response: raw_text = response.read(1048577).decode()
                if len(raw_text) > 1048576: raise ValueError('Oversized response.')
                raw = json.loads(raw_text)
                if not isinstance(raw, dict): raise ValueError('Response must be an object.')
                row.update(raw_response=redact(raw, key), raw_response_text=redact(raw_text, key), usage=redact(raw.get('usage'), key))
                if raw.get('model') != MODEL: reason = 'checkpoint_mismatch'
                row['reading'], row['probabilities'], row['provider_confidence'] = normalize(raw)
            except urllib.error.HTTPError as exc:
                row.update(status='error', http_status=exc.code, error='Provider HTTP ' + str(exc.code))
                if exc.code in {400, 401, 403, 404, 422, 429, 529}: reason = 'provider_http_' + str(exc.code)
            except (ValueError, KeyError, TypeError, OSError) as exc:
                row.update(status='error', error='Request or response validation failed: ' + type(exc).__name__)
                if isinstance(exc, OSError): reason = 'network_error'
            row = redact(row, key); row['latency_ms'] = (time.perf_counter() - start) * 1000
            rows.append(row); stream.write(json.dumps(row) + '\n'); stream.flush()
            consecutive = consecutive + 1 if row['status'] != 'ok' else 0
            if consecutive >= 3 and not reason: reason = 'three_consecutive_failures'
            print(f"{len(rows)}/{len(requests)} {req['arm']} {row['status']}", flush=True)
            if reason: break
    finish(output, plan, records, rows, reason, directory)
    result = assess(output, boundary, directory)
    (output / 'analyst-assessment.json').write_text(json.dumps(result, indent=2) + '\n')
    return result
