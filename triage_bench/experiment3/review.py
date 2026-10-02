"""Computational reference review and input-information audit; no specialist signoff."""
from collections import Counter, defaultdict
import json
from .data import DIRECTORY, validate
from .transforms import VARIANTS, request_body, sha
from triage_bench.dataset import read_jsonl


def review(directory=DIRECTORY):
    validate(directory)
    records=read_jsonl(directory/'development.inputs.jsonl')
    keys={k['id']:k for k in read_jsonl(directory/'development.labels.jsonl')}
    pairs=defaultdict(list)
    for r in records: pairs[keys[r['id']]['pair_id']].append(r)
    variants={}
    for variant in VARIANTS:
        identical=[]
        for pair_id, rows in pairs.items():
            if request_body(rows[0],variant)==request_body(rows[1],variant) and keys[rows[0]['id']]['labels']!=keys[rows[1]['id']]['labels']:
                identical.append({'pair_id':pair_id,'family':keys[rows[0]['id']]['incident_family_id']})
        variants[variant]={'indistinguishable_pairs_with_different_references':identical,
                           'max_request_bytes':max(len(json.dumps(request_body(r,variant),ensure_ascii=False,sort_keys=True).encode()) for r in records)}
    return {'review_status':'computational_checks_only','network_specialist_review':'pending',
            'references':'draft_not_specialist_reviewed','records':len(records),'pairs':len(pairs),
            'pair_types':dict(Counter(keys[rows[0]['id']]['pair_kind'] for rows in pairs.values())),
            'sha256':{name:sha((directory/name).read_bytes()) for name in ['development.inputs.jsonl','development.labels.jsonl']},
            'variants':variants}
