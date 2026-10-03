"""Replay inspected report requests unchanged; diagnostic repetition, not new evaluation."""
import json,math,time,urllib.error,urllib.request
from datetime import datetime,timezone
from pathlib import Path
from triage_bench.dataset import ROOT,read_jsonl,write_jsonl
from triage_bench.runner import NoRedirect,clean_api_key
from .hosted import encoded,redact
from .transforms import MODEL,sha
from .report_language_hosted import prepare as preflight,normalize_report,verify as verify_original

ORIGINAL=ROOT/'runs/report-language-jev/development-2026-10-02-v1'
CASES=[('NSL-a8d5a7d47a26-b',1),('NSL-a8d5a7d47a26-b',0),('NSL-c9841c3176a5-a',0),('NSL-c9841c3176a5-a',1)]
REPEATS=3


def prepare(profile,original=ORIGINAL):
    preflight(profile)
    source,_,requests,responses=verify_original(Path(original)/'summary.json')
    selected=[next(q for q in requests if (q['id'],q['observation_index'])==case and q['arm']=='jev_reading') for case in CASES]
    annotations=read_jsonl(Path(original)/'observation-references.jsonl');refs=[next(a for a in annotations if (a['id'],a['observation_index'])==case) for case in CASES]
    actual=[next(r for r in responses if (r['id'],r['observation_index'])==case and r['arm']=='jev_reading') for case in CASES]
    plan=[{**q,'repetition':repeat} for repeat in range(1,REPEATS+1) for q in (selected if repeat%2 else list(reversed(selected)))]
    sources={**source['source_sha256'],'triage_bench/experiment3/report_language_repeat.py':sha((ROOT/'triage_bench/experiment3/report_language_repeat.py').read_bytes())}
    protocol={'schema':'report-language-repeat-1','model':MODEL,'endpoint':profile['endpoint'],'context_tokens':profile['context_tokens'],'source_sha256':sources,'original_summary_sha256':sha((Path(original)/'summary.json').read_bytes()),'maximum_requests':len(plan),'distinct_requests':len(selected),'repetitions':REPEATS,'selection':'Two distinct misread acceptance reports and their matched refusal reports, selected after inspecting development failures. No new families or changed questions. This is a diagnostic repetition, not an independent accuracy estimate.','reference_status':'draft_not_specialist_reviewed','policy_change':False}
    return protocol,plan,refs,actual


def summarize(plan,responses,refs,original):
    keys={(a['id'],a['observation_index']):a for a in refs};actual={(r['repetition'],r['id'],r['observation_index']):r for r in responses};by=[];counts=[]
    for repeat in range(1,REPEATS+1):
        expected=[q for q in plan if q['repetition']==repeat];correct=sum(actual.get((repeat,q['id'],q['observation_index']),{}).get('status')=='ok' and all(actual[repeat,q['id'],q['observation_index']]['predictions'][f]==keys[q['id'],q['observation_index']][f] for f in ['domain','reading']) for q in expected)
        counts.append({'repetition':repeat,'correct_both':correct,'planned_reports':len(expected),'attempted':sum(k[0]==repeat for k in actual)})
    for key,reference in keys.items():
        rows=[actual.get((repeat,*key)) for repeat in range(1,REPEATS+1)];valid=[r for r in rows if r and r['status']=='ok'];choices=[r['predictions'] for r in valid];original_row=next(r for r in original if (r['id'],r['observation_index'])==key)
        by.append({'id':key[0],'observation_index':key[1],'draft_meaning':{f:reference[f] for f in ['domain','reading']},'original_meaning':original_row['predictions'],'repeated_meanings':choices,'attempted':sum(r is not None for r in rows),'failed_or_missing':REPEATS-len(valid),'all_repeats_agree':len(valid)==REPEATS and all(c==choices[0] for c in choices),'correct_repeats':sum(all(c[f]==reference[f] for f in ['domain','reading']) for c in choices)})
    return {'per_repetition':counts,'reports':by,'attempted_requests':len(responses),'failed_requests':sum(r['status']!='ok' for r in responses),'unattempted_requests':len(plan)-len(responses)}


def run(output,profile,original=ORIGINAL):
    protocol,plan,refs,original_rows=prepare(profile,original);key=clean_api_key(profile.get('api_key',''))
    if not key:raise ValueError('Configure a server-side Jev key.')
    output=Path(output)
    if output.exists():raise ValueError('Diagnostic replay is immutable.')
    output.mkdir(parents=True)
    for name,rows in [('requests',plan),('references',refs),('original-responses',original_rows)]:write_jsonl(output/(name+'.jsonl'),rows)
    protocol['started_at']=datetime.now(timezone.utc).isoformat();(output/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    opener=urllib.request.build_opener(NoRedirect());rows=[];reason=None;consecutive=0
    with (output/'responses.jsonl').open('x') as stream:
        for q in plan:
            r={k:q[k] for k in ['id','observation_index','repetition','request_sha256']};r.update(status='ok',predictions={},probabilities={});began=time.perf_counter()
            try:
                req=urllib.request.Request(profile['endpoint'],data=encoded(q['body']),headers={'Content-Type':'application/json','Authorization':'Bearer '+key},method='POST')
                with opener.open(req,timeout=60) as reply:text=reply.read().decode('utf-8')
                def number(v):
                    n=float(v)
                    if not math.isfinite(n):raise ValueError('Non-finite response.')
                    return n
                raw=json.loads(text,parse_float=number,parse_constant=number);r.update(raw_response=redact(raw,key),raw_response_text=redact(text,key))
                if raw.get('model') and raw['model']!=MODEL:reason='checkpoint_mismatch';raise ValueError('Checkpoint changed.')
                r['predictions'],r['probabilities'],r['provider_confidence']=normalize_report(raw)
                r['usage']=redact(raw.get('usage'),key)
            except urllib.error.HTTPError as e:
                r.update(status='error',http_status=e.code,error='Provider HTTP '+str(e.code))
                if e.code in {400,401,403,404,422,429,529}:reason='provider_http_'+str(e.code)
            except (ValueError,KeyError,TypeError,AttributeError,OSError) as e:
                r.update(status='error',error='Request/response validation failed ('+type(e).__name__+').')
                if isinstance(e,OSError):reason='network_error'
            r=redact(r,key);r['latency_ms']=(time.perf_counter()-began)*1000;rows.append(r);stream.write(json.dumps(r)+'\n');stream.flush();consecutive=consecutive+1 if r['status']!='ok' else 0
            if consecutive>=3 and not reason:reason='three_consecutive_failures'
            if reason:break
    summary={**protocol,**summarize(plan,rows,refs,original_rows),'stopped_reason':reason,'status':'completed' if len(rows)==len(plan) and all(r['status']=='ok' for r in rows) else 'completed_with_errors','evidence_sha256':{p.name:sha(p.read_bytes()) for p in sorted(output.glob('*.jsonl'))}}
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');return summary


def verify(path,original=ORIGINAL):
    path=Path(path);s=json.loads(path.read_text());protocol,requests,refs,original_rows=prepare({'model':s['model'],'endpoint':s['endpoint'],'context_tokens':s['context_tokens']},original)
    if any(s.get(k)!=v for k,v in protocol.items()) or json.loads((path.parent/'protocol.json').read_text())!={**protocol,'started_at':s['started_at']}:raise ValueError('Replay protocol/source differ.')
    if set(s['evidence_sha256'])!={'requests.jsonl','responses.jsonl','references.jsonl','original-responses.jsonl'}:raise ValueError('Replay evidence paths differ.')
    if any(sha((path.parent/n).read_bytes())!=h for n,h in s['evidence_sha256'].items()):raise ValueError('Replay evidence differs.')
    if read_jsonl(path.parent/'requests.jsonl')!=requests or read_jsonl(path.parent/'references.jsonl')!=refs or read_jsonl(path.parent/'original-responses.jsonl')!=original_rows:raise ValueError('Replay original joins differ.')
    rows=read_jsonl(path.parent/'responses.jsonl')
    for r,q in zip(rows,requests):
        if any(r.get(k)!=q[k] for k in ['id','observation_index','repetition','request_sha256']):raise ValueError('Replay response join differs.')
        if r['status']=='ok':
            p,probs,c=normalize_report(r['raw_response'])
            if p!=r['predictions'] or probs!=r['probabilities'] or c!=r['provider_confidence'] or r['raw_response'].get('model') not in {None,MODEL}:raise ValueError('Replay normalized response differs.')
    if len(rows)>len(requests) or any(s.get(k)!=v for k,v in summarize(requests,rows,refs,original_rows).items()):raise ValueError('Replay counts differ.')
    if s['status']!=('completed' if len(rows)==len(requests) and all(r['status']=='ok' for r in rows) else 'completed_with_errors'):raise ValueError('Replay status differs.')
    return s
