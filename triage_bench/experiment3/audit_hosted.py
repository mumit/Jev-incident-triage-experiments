"""Verify saved hosted evidence before exposing predictions or scores."""
import json
from pathlib import Path
from triage_bench.dataset import read_jsonl
from triage_bench.evaluate import evaluate
from .hosted import encoded
from .transforms import VARIANTS,request_body,sha


def verify(path,root,manifest,records,keys):
    path,root=Path(path),Path(root);summary=json.loads(path.read_text());directory=path.parent
    protocol=json.loads((directory/'protocol.json').read_text())
    if any(summary.get(k)!=v for k,v in protocol.items()):raise ValueError('Hosted summary differs from its saved protocol.')
    if summary.get('kind')!='jev_development' or set(summary['approaches'])!=set(VARIANTS):raise ValueError('Unexpected hosted approaches.')
    if summary['draft_pack_sha256']!=manifest['sha256']:raise ValueError('Hosted draft pack differs.')
    if not summary['source_sha256'] or any(not (root/name).is_file() or sha((root/name).read_bytes())!=digest for name,digest in summary['source_sha256'].items()):raise ValueError('Hosted source fingerprint differs.')
    for name,field in [('inputs.jsonl','input_sha256'),('labels.jsonl','label_sha256'),('requests.jsonl','requests_sha256')]:
        if sha((directory/name).read_bytes())!=summary[field]:raise ValueError('Hosted evidence fingerprint differs.')
    inputs=read_jsonl(directory/'inputs.jsonl');labels=read_jsonl(directory/'labels.jsonl');requests=read_jsonl(directory/'requests.jsonl')
    ids={r['id'] for r in inputs}
    if len(ids)!=len(inputs) or ids!={k['id'] for k in labels} or len(labels)!=len(ids) or summary['records']!=len(ids):raise ValueError('Hosted scoring IDs differ.')
    if any(r!=records.get(r['id']) for r in inputs) or any(k!=keys.get(k['id']) for k in labels):raise ValueError('Hosted inputs or references differ from this pack.')
    pairs={keys[identifier]['pair_id'] for identifier in ids}
    if any(sum(keys[identifier]['pair_id']==pair for identifier in ids)!=2 for pair in pairs):raise ValueError('Hosted controlled pair is incomplete.')
    if len(requests)!=len(ids)*len(VARIANTS) or summary['maximum_requests']!=len(requests) or {(r['id'],r['variant']) for r in requests}!={(identifier,v) for identifier in ids for v in VARIANTS}:raise ValueError('Hosted request coverage differs.')
    requests_by_id={}
    for r in requests:
        body=request_body(records[r['id']],r['variant'])
        if r['body']!=body or r['request_sha256']!=sha(encoded(body)) or r['state_sha256']!=sha(body['state'].encode()):raise ValueError('Hosted request does not match exact prepared input.')
        requests_by_id[(r['id'],r['variant'])]=r
    rows={};attempted=failures=0
    for variant,result in summary['approaches'].items():
        output=directory/(variant+'.jsonl')
        if evaluate(directory/'labels.jsonl',output,inputs_path=directory/'inputs.jsonl')!=result['metrics']:raise ValueError('Hosted scores differ from recomputed results.')
        rows[variant]={r['id']:r for r in read_jsonl(output)}
        for identifier,row in rows[variant].items():
            req=requests_by_id[(identifier,variant)]
            if any(row[k]!=req[k] for k in ['request_sha256','state_sha256']):raise ValueError('Hosted response request fingerprint differs.')
            attempted+=1;failures+=row['status']!='ok'
    if attempted!=summary['attempted_requests'] or failures!=summary['failed_requests'] or summary['unattempted_requests']!=len(requests)-attempted:raise ValueError('Hosted attempt counts differ.')
    expected_status='completed' if attempted==len(requests) and not failures else 'completed_with_errors'
    if summary['status']!=expected_status:raise ValueError('Hosted completion status differs.')
    return summary,rows,requests_by_id
