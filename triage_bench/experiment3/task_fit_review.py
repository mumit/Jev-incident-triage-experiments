"""Supplementary routing diagnostic; never changes frozen predictions or scores."""
import json
from pathlib import Path
from triage_bench.dataset import read_jsonl
from .task_fit_trial import packet, verify
from .transforms import sha

def routing_review(output):
    output=Path(output); verify(output)
    summary=json.loads((output/'summary.json').read_text())
    if summary['repeat_diagnostic']: raise ValueError('Use primary or calibration evidence.')
    records=read_jsonl(output/'inputs.jsonl')
    keys={k['id']:k['labels'] for k in read_jsonl(output/'labels.jsonl')}
    rows=read_jsonl(output/'responses.jsonl'); result={}
    for arm in summary['arms']:
        actual={r['id']:r for r in rows if r['arm']==arm and r['status']=='ok'}
        points=[]
        for threshold in (0,.5,.6,.7,.8,.9,.95,.99,1):
            readings=routes=errors=0
            for record in records:
                row=actual.get(record['id'])
                if not row or row['reading']=='unknown' or not row.get('probabilities') or row['probabilities'][row['reading']]<threshold: continue
                readings+=1; decision=packet(record,row['reading'])['predictions']
                if decision['initial_owner']!='noc' and decision['insufficient_evidence']=='no':
                    routes+=1; errors+=decision['initial_owner']!=keys[record['id']]['initial_owner']
            points.append({'threshold':threshold,'accepted_report_readings':readings,
                           'domain_recommendations':routes,'domain_coverage':routes/len(records),
                           'wrong_domain_recommendations':errors,'noc_or_review':len(records)-routes})
        result[arm]=points
    return {'schema':'task-fit-routing-review-1','summary_sha256':sha((output/'summary.json').read_bytes()),
            'boundary':'Supplementary calculation from actual readings and frozen policy. Accepted report readings differ from actionable domain ownership. NOC retention and failures remain outside domain coverage. No operational threshold is selected; no saved prediction changes.',
            'source_sha256':sha(Path(__file__).read_bytes()),'arms':result}
