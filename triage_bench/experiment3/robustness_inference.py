"""Bounded robustness inference; unchanged filter and explicit questions."""
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import time
import urllib.error
import urllib.parse
import urllib.request

from triage_bench.dataset import ROOT, read_jsonl, write_jsonl
from triage_bench.evaluate import evaluate
from triage_bench.runner import NoRedirect, clean_api_key, normalize
from .hosted import encoded, redact
from .transforms import MODEL, sha

from .robustness_data import DIRECTORY, validate
from .selection import body
ARMS = {'baseline': 'Combined facts', 'selected': 'Eligible observations only'}


def prepare(profile,directory=DIRECTORY):
    manifest=validate(directory);directory=Path(directory)
    if profile['model']!=MODEL:raise ValueError('Keep the Jev checkpoint fixed.')
    u=urllib.parse.urlparse(profile['endpoint'])
    if not u.hostname or u.username or u.password or u.query or u.fragment or (u.scheme!='https' and not(u.scheme=='http' and u.hostname in {'127.0.0.1','localhost','::1'})):raise ValueError('Unsafe provider endpoint.')
    capacity=profile['context_tokens']
    if isinstance(capacity,bool) or not isinstance(capacity,int) or not 512<=capacity<=1000000:raise ValueError('Invalid declared capacity.')
    records=read_jsonl(directory/'development.inputs.jsonl');keys=read_jsonl(directory/'development.labels.jsonl');requests=[]
    for index,r in enumerate(records):
        for arm in (list(ARMS)[index % len(ARMS):] + list(ARMS)[:index % len(ARMS)]):
            request=body(r,arm);wire=encoded(request)
            if len(wire)+512>capacity:raise ValueError('Context preflight failed.')
            requests.append({'id':r['id'],'variant':arm,'body':request,'request_sha256':sha(wire),'state_sha256':sha(request['state'].encode())})
    sources=['experiment3/robustness_inference.py','experiment3/robustness_data.py','experiment3/selection_data.py','experiment3/selection.py','experiment3/question_trial.py','experiment3/transforms.py','experiment3/hosted.py','experiments.py','policy.py','runner.py','evaluate.py']
    protocol={'schema':'experiment-3-robustness-trial-1','kind':'jev_robustness_development','requested_model':MODEL,
              'endpoint':profile['endpoint'],'declared_context_tokens':capacity,'records':len(records),'maximum_requests':len(requests),
              'input_variants':list(ARMS),'reference_status':manifest['reference_status'],'network_specialist_review':'pending',
              'human_decision':manifest['human_decision'],'data_sha256':manifest['sha256'],
              'question_sha256':{a:sha(encoded(body(records[0],a)['questions'])) for a in ARMS},
              'source_sha256':{'triage_bench/'+name:sha((ROOT/'triage_bench'/name).read_bytes()) for name in sources},
              'execution':'Serial, rotating arm order by packet; one call per packet and arm; no warmup or retries.',
              'timeout_seconds':60,'context_preflight':'UTF-8 request bytes plus 512 <= declared capacity; not a tokenizer.'}
    return protocol,records,keys,requests


def run(output,profile,directory=DIRECTORY,progress=None):
    protocol,records,keys,requests=prepare(profile,directory);key=clean_api_key(profile.get('api_key',''))
    if not key:raise ValueError('A server-side Jev key is required.')
    output=Path(output)
    if output.exists():raise ValueError('Runs are immutable; choose a new directory.')
    output.mkdir(parents=True)
    write_jsonl(output/'inputs.jsonl',records);write_jsonl(output/'labels.jsonl',keys);write_jsonl(output/'requests.jsonl',requests)
    protocol.update(started_at=datetime.now(timezone.utc).isoformat(),requests_sha256=sha((output/'requests.jsonl').read_bytes()))
    (output/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    streams={a:(output/(a+'.jsonl')).open('x') for a in ARMS};opener=urllib.request.build_opener(NoRedirect())
    attempted=failed=consecutive=0;reason=None;started=time.perf_counter()
    try:
        for req in requests:
            row={k:req[k] for k in ['id','request_sha256','state_sha256']};row.update(status='ok',predictions={},probabilities={});began=time.perf_counter();attempted+=1
            try:
                wire=urllib.request.Request(profile['endpoint'],data=encoded(req['body']),headers={'Content-Type':'application/json','Authorization':'Bearer '+key},method='POST')
                with opener.open(wire,timeout=60) as response:text=response.read().decode('utf-8')
                row['raw_response_text']=redact(text,key)
                def number(value):
                    result=float(value)
                    if not math.isfinite(result):raise ValueError('Nonfinite response value.')
                    return result
                raw=json.loads(text,parse_float=number,parse_constant=number)
                if not isinstance(raw,dict):raise ValueError('Response is not an object.')
                row['raw_response']=redact(raw,key);row['resolved_model']=raw.get('model');row['usage']=redact(raw.get('usage'),key)
                if raw.get('model') and raw['model']!=MODEL:reason='checkpoint_mismatch';raise ValueError('Reported checkpoint changed.')
                row['predictions'],row['probabilities'],row['provider_confidence']=normalize(raw)
            except urllib.error.HTTPError as exc:
                row.update(status='error',http_status=exc.code,error='Provider HTTP '+str(exc.code))
                if exc.code in {400,401,403,404,422,429,529}:reason='provider_http_'+str(exc.code)
            except (ValueError,KeyError,TypeError,OSError) as exc:
                row.update(status='error',error='Request/response validation failed ('+type(exc).__name__+').')
                if isinstance(exc,OSError):reason='network_error'
            row=redact(row,key);row['latency_ms']=(time.perf_counter()-began)*1000
            stream=streams[req['variant']];stream.write(json.dumps(row)+'\n');stream.flush()
            failed+=row['status']!='ok';consecutive=consecutive+1 if row['status']!='ok' else 0
            if consecutive>=3 and not reason:reason='three_consecutive_failures'
            if progress:progress(attempted,len(requests),req['variant'],row['status'])
            if reason:break
    finally:
        for stream in streams.values():stream.close()
    summary={**protocol,'attempted_requests':attempted,'failed_requests':failed,'unattempted_requests':len(requests)-attempted,
             'stopped_reason':reason,'status':'completed' if attempted==len(requests) and not failed else 'completed_with_errors',
             'wall_seconds':time.perf_counter()-started,'approaches':{}}
    for arm in ARMS:summary['approaches'][arm]={'metrics':evaluate(output/'labels.jsonl',output/(arm+'.jsonl'),output/(arm+'.metrics.json'),output/'inputs.jsonl'), 'predictions_sha256':sha((output/(arm+'.jsonl')).read_bytes())}
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');return summary


def verify(path,root=ROOT,directory=DIRECTORY):
    path=Path(path);root=Path(root);manifest=validate(directory);summary=json.loads(path.read_text());protocol=json.loads((path.parent/'protocol.json').read_text())
    if any(summary.get(k)!=v for k,v in protocol.items()) or protocol['kind']!='jev_robustness_development' or protocol['data_sha256']!=manifest['sha256'] or protocol['human_decision']!=manifest['human_decision'] or set(summary['approaches'])!=set(ARMS):raise ValueError('Trial protocol differs.')
    if any(sha((root/name).read_bytes())!=digest for name,digest in protocol['source_sha256'].items()):raise ValueError('Trial source differs.')
    for saved,source in [('inputs.jsonl','development.inputs.jsonl'),('labels.jsonl','development.labels.jsonl')]:
        if sha((path.parent/saved).read_bytes())!=manifest['sha256'][source]:raise ValueError('Trial data differ.')
    requests=read_jsonl(path.parent/'requests.jsonl');records={r['id']:r for r in read_jsonl(path.parent/'inputs.jsonl')}
    if sha((path.parent/'requests.jsonl').read_bytes())!=protocol['requests_sha256'] or len(requests)!=len(records)*len(ARMS) or protocol['maximum_requests']!=len(requests) or protocol['records']!=len(records) or {(r['id'],r['variant']) for r in requests}!={(identifier,a) for identifier in records for a in ARMS}:raise ValueError('Trial request coverage differs.')
    if protocol['question_sha256']!={a:sha(encoded(body(next(iter(records.values())),a)['questions'])) for a in ARMS}:raise ValueError('Frozen questions differ.')
    request_map={}
    for req in requests:
        expected=body(records[req['id']],req['variant'])
        if req['body']!=expected or req['request_sha256']!=sha(encoded(expected)) or req['state_sha256']!=sha(expected['state'].encode()):raise ValueError('Trial request differs.')
        request_map[(req['id'],req['variant'])]=req
    rows={};attempted=failed=0
    for arm,result in summary['approaches'].items():
        output=path.parent/(arm+'.jsonl')
        if sha(output.read_bytes())!=result['predictions_sha256'] or evaluate(path.parent/'labels.jsonl',output,inputs_path=path.parent/'inputs.jsonl')!=result['metrics']:raise ValueError('Trial metrics differ.')
        rows[arm]={r['id']:r for r in read_jsonl(output)}
        for identifier,row in rows[arm].items():
            req=request_map[(identifier,arm)]
            if any(row.get(k)!=req[k] for k in ['state_sha256','request_sha256']):raise ValueError('Trial response request differs.')
            attempted+=1;failed+=row['status']!='ok'
    if (attempted,failed,len(requests)-attempted)!=(summary['attempted_requests'],summary['failed_requests'],summary['unattempted_requests']):raise ValueError('Trial attempt counts differ.')
    if summary['status']!=('completed' if attempted==len(requests) and not failed else 'completed_with_errors'):raise ValueError('Trial status differs.')
    return summary,rows,request_map
