"""Evidence eligibility and selection, without domain inference or reference access."""
import copy
import json
from triage_bench.policy import TEXT
from .transforms import transformed_packet, dependency_facts, measurement_facts, MODEL
from .question_trial import candidate_questions

ARMS = {'baseline': 'Combined facts', 'eligibility': 'Eligibility facts', 'selected': 'Eligible observations only'}


def eligibility(packet):
    dependencies = dependency_facts(packet)
    measurements = measurement_facts(packet)
    result = []
    for d, m in zip(dependencies, measurements):
        reasons = []
        if m['freshness_status'] != 'current':
            reasons.append('measurement_' + m['freshness_status'])
        if not d['supported_site_count']:
            reasons.append('relationship_unknown' if d['relation'] == 'unknown' else 'relationship_excluded')
        result.append({'observation_index': m['observation_index'], 'eligible': not reasons,
                       'reasons': reasons, 'freshness_status': m['freshness_status'],
                       'supported_site_count': d['supported_site_count'], 'relation': d['relation']})
    return result


def packet(record, arm):
    if arm not in ARMS:
        raise ValueError('Unknown evidence-selection arm.')
    result = transformed_packet(record, 'combined')
    if arm == 'baseline':
        return result
    rows = eligibility(record['input'])
    result['evidence_eligibility'] = {
        'rule': 'Eligible means current within the declared window and at least one visible required-service path from a listed affected site. Unknown freshness or an unsupported relationship cannot justify a domain. Eligibility does not classify a malfunction, resolve conflicts or prove root cause.',
        'input_observation_count': len(rows), 'eligible_observation_count': sum(r['eligible'] for r in rows),
        'observations': rows}
    if arm == 'selected':
        keep = [r['observation_index'] for r in rows if r['eligible']]
        # Every index referenced by the fixed questions refers to the new list.
        # Preserve source indices for the separate, inspectable raw packet.
        for name in ['observations', 'measurement_facts', 'dependency_facts']:
            result[name] = [copy.deepcopy(result[name][i]) for i in keep]
            for index, (source, row) in enumerate(zip(keep, result[name])):
                row.update(observation_index=index, source_observation_index=source)
        result['evidence_eligibility']['observations'] = [
            {**rows[source], 'observation_index': index, 'source_observation_index': source}
            for index, source in enumerate(keep)]
    return result


def body(record, arm):
    return {'model': MODEL, 'state': TEXT + '\nCurrent incident evidence:\n' + json.dumps(packet(record, arm), ensure_ascii=False, sort_keys=True),
            'questions': candidate_questions()}
