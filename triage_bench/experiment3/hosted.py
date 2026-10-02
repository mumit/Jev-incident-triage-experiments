"""Bounded hosted development comparison. No training, reference tuning or retries."""
import json
import math
from pathlib import Path
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from triage_bench.dataset import ROOT, read_jsonl, write_jsonl
from triage_bench.evaluate import evaluate
from triage_bench.runner import NoRedirect, clean_api_key, normalize
from .data import DIRECTORY, validate
from .review import review
from .transforms import MODEL, VARIANTS, request_body, sha


def encoded(body):
    return json.dumps(body,ensure_ascii=False,sort_keys=True).encode()


def redact(value,key):
    if isinstance(value,str):return value.replace(key,'[redacted]') if key else value
    if isinstance(value,list):return [redact(v,key) for v in value]
    if isinstance(value,dict):return {redact(k,key):redact(v,key) for k,v in value.items()}
    return value


def prepare(profile,directory=DIRECTORY,pair_ids=None):
    directory=Path(directory);validate(directory)
    if profile['model']!=MODEL:raise ValueError('Experiment 3 requires the fixed Jev checkpoint.')
    url=urllib.parse.urlparse(profile['endpoint'])
    if not url.hostname or url.username or url.password or url.query or url.fragment or (url.scheme!='https' and not (url.scheme=='http' and url.hostname in {'localhost','127.0.0.1','::1'})):
        raise ValueError('Use HTTPS or a loopback endpoint without credentials or query parameters.')
    capacity=profile['context_tokens']
    if isinstance(capacity,bool) or not isinstance(capacity,int) or not 512<=capacity<=1000000:raise ValueError('Invalid declared context capacity.')
    records=read_jsonl(directory/'development.inputs.jsonl');keys=read_jsonl(directory/'development.labels.jsonl')
    if pair_ids is not None:
        if not pair_ids or len(set(pair_ids))!=len(pair_ids) or not set(pair_ids)<={k['pair_id'] for k in keys}:raise ValueError('Select distinct existing controlled pairs.')
        ids={k['id'] for k in keys if k['pair_id'] in pair_ids};records=[r for r in records if r['id'] in ids]
        keys=[k for k in keys if k['id'] in ids]
    requests=[];variants=list(VARIANTS)
    for index,record in enumerate(records):
        # Rotate the serial order across packets to distribute early/late positions.
        order=variants[index%4:]+variants[:index%4]
        for variant in order:
            body=request_body(record,variant);wire=encoded(body)
            if len(wire)+512>capacity:raise ValueError('Context preflight failed; no hosted request sent.')
            requests.append({'id':record['id'],'variant':variant,'body':body,'request_sha256':sha(wire),'state_sha256':sha(body['state'].encode())})
    files=['experiment3/hosted.py','experiment3/review.py','experiment3/transforms.py','experiment3/data.py','runner.py','evaluate.py','experiments.py','policy.py']
    protocol={'schema':'experiment-3-jev-1','requested_model':MODEL,'endpoint':profile['endpoint'],
              'declared_context_tokens':capacity,'deployment':profile.get('deployment','Hosted Jev API'),
              'reference_status':'draft_not_specialist_reviewed','network_specialist_review':'pending',
              'split':'development','records':len(records),'maximum_requests':len(requests),
              'execution':'Serial, variant order rotates by packet; no warmup or automatic retries.',
              'timeout_seconds':60,'failure_stop':'Immediate for configuration/access/rate-limit failures, checkpoint mismatch or network errors; otherwise stop after three consecutive failed responses.','context_preflight':'UTF-8 request bytes plus 512 <= declared capacity; not a tokenizer.',
              'source_sha256':{'triage_bench/'+name:sha((ROOT/'triage_bench'/name).read_bytes()) for name in files},
              'draft_pack_sha256':json.loads((directory/'manifest.json').read_text())['sha256'],
              'questions_sha256':sha(encoded(requests[0]['body']['questions'])),
              'computational_review':review(directory)}
    return protocol,records,keys,requests


def run(output,profile,directory=DIRECTORY,pair_ids=None,progress=None,stop_event=None):
    protocol,records,keys,requests=prepare(profile,directory,pair_ids)
    key=clean_api_key(profile.get('api_key',''))
    if not key:raise ValueError('Configure a Jev key on the server or in the environment.')
    output=Path(output)
    if output.exists():raise ValueError('Choose a new hosted output directory; runs are immutable.')
    output.mkdir(parents=True)
    write_jsonl(output/'inputs.jsonl',records);write_jsonl(output/'labels.jsonl',keys);write_jsonl(output/'requests.jsonl',requests)
    protocol.update(started_at=datetime.now(timezone.utc).isoformat(),input_sha256=sha((output/'inputs.jsonl').read_bytes()),
                    label_sha256=sha((output/'labels.jsonl').read_bytes()),requests_sha256=sha((output/'requests.jsonl').read_bytes()))
    (output/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    # All requests and scoring data are saved before the first external call.
    streams={v:(output/(v+'.jsonl')).open('x') for v in VARIANTS}
    opener=urllib.request.build_opener(NoRedirect());attempted=failures=consecutive_failures=0;reason=None;started=time.perf_counter()
    try:
        for request in requests:
            if stop_event is not None and stop_event.is_set():reason='cancelled';break
            row={k:request[k] for k in ['id','request_sha256','state_sha256']}
            row.update(status='ok',predictions={},probabilities={})
            began=time.perf_counter();attempted+=1
            try:
                req=urllib.request.Request(profile['endpoint'],data=encoded(request['body']),headers={'Content-Type':'application/json','Authorization':'Bearer '+key},method='POST')
                with opener.open(req,timeout=60) as response:
                    text=response.read().decode('utf-8')
                row['raw_response_text']=redact(text,key)
                def number(value):
                    result=float(value)
                    if not math.isfinite(result):raise ValueError('Non-finite response value.')
                    return result
                raw=json.loads(text,parse_float=number,parse_constant=lambda value: number(value))
                if not isinstance(raw,dict):raise ValueError('Response must be a JSON object.')
                row['raw_response']=redact(raw,key)
                row['resolved_model']=raw.get('model');row['usage']=redact(raw.get('usage'),key)
                if raw.get('model') and raw['model']!=MODEL:
                    reason='checkpoint_mismatch';raise ValueError('Reported checkpoint differs.')
                row['predictions'],row['probabilities'],row['provider_confidence']=normalize(raw)
                row['distribution_sums']={f:sum(a['probabilities'].values()) for f,a in raw.get('answers',{}).items() if isinstance(a,dict) and isinstance(a.get('probabilities'),dict)}
            except urllib.error.HTTPError as exc:
                row.update(status='error',error='Provider request failed (HTTP '+str(exc.code)+').',http_status=exc.code)
                if exc.code in {400,401,403,404,422,429,529}:reason='provider_http_'+str(exc.code)
            except (ValueError,KeyError,TypeError,OSError) as exc:
                row.update(status='error',error='Request or response validation failed ('+type(exc).__name__+').')
                if isinstance(exc,OSError):reason='network_error'
            row=redact(row,key);row['latency_ms']=(time.perf_counter()-began)*1000
            stream=streams[request['variant']];stream.write(json.dumps(row,ensure_ascii=False)+'\n');stream.flush()
            failures+=row['status']!='ok'
            consecutive_failures=consecutive_failures+1 if row['status']!='ok' else 0
            if consecutive_failures>=3 and not reason:reason='three_consecutive_failures'
            if progress:progress(attempted,len(requests),request['variant'],row['status'])
            if reason:break
    finally:
        for stream in streams.values():stream.close()
    summary={**protocol,'kind':'jev_development','attempted_requests':attempted,'failed_requests':failures,
             'unattempted_requests':len(requests)-attempted,'stopped_reason':reason,'wall_seconds':time.perf_counter()-started,
             'status':'completed' if attempted==len(requests) and not failures else 'completed_with_errors','approaches':{}}
    for variant in VARIANTS:
        metrics=evaluate(output/'labels.jsonl',output/(variant+'.jsonl'),output/(variant+'.metrics.json'),output/'inputs.jsonl')
        summary['approaches'][variant]={'metrics':metrics}
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    return summary
