"""Pinned Jev direct triage versus report meaning followed by frozen policy."""
import json,math,time,urllib.error,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path
from triage_bench.dataset import ROOT,read_jsonl,write_jsonl
from triage_bench.evaluate import evaluate
from triage_bench.runner import NoRedirect,clean_api_key,normalize
from .report_language_data import DIRECTORY,validate
from .report_language_trial import SOURCES as LOCAL_SOURCES,changes
from .interpretation_model import report_inputs,apply_policy
from .interpretation_trial import report_metrics
from .selection import body as direct_body
from .hosted import encoded,redact
from .transforms import MODEL,sha

ARMS={'jev_direct':'Jev · direct triage','jev_reading':'Jev · report → policy'}
SOURCES=LOCAL_SOURCES+['triage_bench/experiment3/report_language_hosted.py','triage_bench/experiment3/hosted.py','triage_bench/runner.py','triage_bench/evaluate.py','triage_bench/experiment3/question_trial.py']
REPORT_CHOICES={
 'domain':{'transport':'The focal measurement concerns packet forwarding, routing, links or optical transport.','ran':'The focal measurement concerns radio processing, decoding, timing or radio equipment.','power':'The focal measurement concerns electrical supply, voltage or equipment power.','core':'The focal measurement concerns subscriber registration, sessions or shared core services.','none':'No specific fault domain is described; general service recovery or an unclassified observation.'},
 'reading':{'fault':'An explicit observation establishes failure or impairment of the focal component. A passing auxiliary check or an unconfirmed earlier alarm does not cancel an independent current fault observation.','normal':'The focal component measurement establishes normal operation or explicitly rules out the stated fault. Fault-related words under negation do not establish a fault. Verified general service recovery is normal.','unknown':'The focal reading is uncertain, suspected, inconclusive or not established. Distinguish uncertainty about the focal measurement from uncertainty about an unrelated check or earlier alarm.'}}


def report_body(text):
    return {'model':MODEL,'state':'Report text only:\n'+text,'questions':{f:{'type':'choice','instructions':'Interpret the focal component evidence in this report. Select '+('the described domain.' if f=='domain' else 'fault, normal or unknown according to the report, respecting clause scope. Do not infer an incident disposition, freshness or service relationship.'),'criteria':c} for f,c in REPORT_CHOICES.items()}}


def normalize_report(raw):
    if not isinstance(raw,dict) or not isinstance(raw.get('answers'),dict):raise ValueError('Missing report answers.')
    meanings={};probabilities={};confidence={}
    for f,choices in REPORT_CHOICES.items():
        a=raw['answers'][f];choice=a['choice']
        if choice not in choices:raise ValueError('Invalid report choice.')
        meanings[f]=choice;dist=a.get('probabilities')
        if dist is not None:
            if not isinstance(dist,dict) or set(dist)!=set(choices) or any(isinstance(p,bool) or not isinstance(p,(int,float)) or not math.isfinite(p) or not 0<=p<=1 for p in dist.values()):raise ValueError('Invalid report probabilities.')
            total=sum(dist.values())
            if abs(total-1)>.001:
                if total>0 and all(abs(p-round(p,2))<1e-10 for p in dist.values()) and abs(total-1)<=.005*len(dist)+1e-10:dist={c:p/total for c,p in dist.items()}
                else:raise ValueError('Report probabilities do not sum to one.')
            probabilities[f]=dist
        if 'confidence' in a:confidence[f]=a['confidence']
    return meanings,probabilities,confidence


def prepare(profile,directory=DIRECTORY):
    directory=Path(directory);validate(directory);m=json.loads((directory/'manifest.json').read_text())
    if profile['model']!=MODEL:raise ValueError('Keep the Jev checkpoint fixed.')
    u=urllib.parse.urlparse(profile['endpoint']);capacity=profile['context_tokens']
    if not u.hostname or u.username or u.password or u.query or u.fragment or (u.scheme!='https' and not(u.scheme=='http' and u.hostname in {'127.0.0.1','localhost','::1'})):raise ValueError('Unsafe provider endpoint.')
    if isinstance(capacity,bool) or not isinstance(capacity,int) or not 512<=capacity<=1000000:raise ValueError('Invalid declared context capacity.')
    records=read_jsonl(directory/'narrow/development.inputs.jsonl');keys=read_jsonl(directory/'narrow/development.labels.jsonl');requests=[]
    for index,r in enumerate(records):
        direct=[{'id':r['id'],'arm':'jev_direct','observation_index':None,'body':direct_body(r,'selected')}]
        reader=[{'id':r['id'],'arm':'jev_reading','observation_index':o['observation_index'],'body':report_body(o['text'])} for o in report_inputs(r)]
        for req in (direct+reader if index%2==0 else reader+direct):
            wire=encoded(req['body'])
            if len(wire)+512>capacity:raise ValueError('Context preflight failed; no hosted requests sent.')
            req.update(request_sha256=sha(wire),state_sha256=sha(req['body']['state'].encode()));requests.append(req)
    plan={'schema':'report-language-hosted-1','requested_model':MODEL,'endpoint':profile['endpoint'],'declared_context_tokens':capacity,'arms':ARMS,
          'data_sha256':m['sha256'],'source_sha256':{n:sha((ROOT/n).read_bytes()) for n in SOURCES},'records':len(records),'report_count':m['observation_counts']['development'],'maximum_requests':len(requests),
          'reference_status':'draft_not_specialist_reviewed','execution':'Serial, alternating direct/report block order by packet; one response per request, no warmup or automatic retries.',
          'comparison':'Frozen selected-evidence direct triage versus text-only report interpretation feeding frozen ML report policy. Task boundary, context, evidence retention, questions and software execution differ; this is an architecture comparison.',
          'failure_stop':'Stop immediately for access/configuration/rate-limit/overload/checkpoint/network failures; otherwise stop after three consecutive malformed responses. Missing and failed report requests invalidate packet triage.',
          'timeout_seconds':60,'context_preflight':'UTF-8 request bytes plus 512 <= declared capacity; not a tokenizer.',
          'report_questions_sha256':sha(encoded(report_body('')['questions'])),'direct_questions_sha256':sha(encoded(direct_body(records[0],'selected')['questions']))}
    return plan,records,keys,requests


def aggregate(records,responses):
    by={(r['id'],r['arm'],r['observation_index']):r for r in responses};direct=[];reading=[]
    for r in records:
        d=by.get((r['id'],'jev_direct',None))
        if d:direct.append({'id':r['id'],'status':d['status'],'predictions':d.get('predictions',{}),'probabilities':d.get('probabilities',{})})
        replies=[by.get((r['id'],'jev_reading',o['observation_index'])) for o in report_inputs(r)]
        if all(x and x['status']=='ok' for x in replies):
            meanings=[{'observation_index':x['observation_index'],**x['predictions'],'probabilities':x['probabilities'],'provider_confidence':x.get('provider_confidence',{})} for x in replies]
            reading.append({'id':r['id'],'status':'ok','readings':meanings,**apply_policy(r,meanings)})
        elif any(replies):reading.append({'id':r['id'],'status':'error','predictions':{},'readings':[],'error':'Report responses failed or are incomplete.'})
    return {'jev_direct':direct,'jev_reading':reading}


def interpretation_score(responses,annotations,keys,packets):
    actual={(r['id'],r['observation_index']):r for r in responses if r['arm']=='jev_reading'};fields={f:{'correct':0,'reports':len(annotations)} for f in ['domain','reading','both']};wrong=[]
    for a in annotations:
        r=actual.get((a['id'],a['observation_index']));p=r.get('predictions',{}) if r and r['status']=='ok' else {};d=p.get('domain')==a['domain'];state=p.get('reading')==a['reading']
        fields['domain']['correct']+=int(d);fields['reading']['correct']+=int(state);fields['both']['correct']+=int(d and state)
        if not(d and state):wrong.append({'id':a['id'],'observation_index':a['observation_index']})
    valid={r['id']:r for r in packets['jev_reading'] if r['status']=='ok'}
    attribution=report_metrics({'reading':valid,'reading_rules':valid},[a for a in annotations if a['id'] in valid],keys)['reading']['attribution']
    return {'fields':fields,'incorrect_or_missing':wrong,'attribution':attribution,'valid_packets':len(valid),'failed_or_missing_packets':len(keys)-len(valid)}


def run(output,profile,directory=DIRECTORY,progress=None):
    plan,records,keys,requests=prepare(profile,directory);key=clean_api_key(profile.get('api_key',''))
    if not key:raise ValueError('Configure a Jev key on the server or in the environment.')
    output=Path(output)
    if output.exists():raise ValueError('Hosted report-language runs are immutable.')
    output.mkdir(parents=True)
    for name,data in [('inputs',records),('labels',keys),('requests',requests),('observation-references',read_jsonl(Path(directory)/'narrow/development.observations.jsonl'))]:write_jsonl(output/(name+'.jsonl'),data)
    plan.update(started_at=datetime.now(timezone.utc).isoformat(),requests_sha256=sha((output/'requests.jsonl').read_bytes()))
    (output/'protocol.json').write_text(json.dumps(plan,indent=2)+'\n');rows=[];reason=None;consecutive=0;started=time.perf_counter();opener=urllib.request.build_opener(NoRedirect())
    with (output/'responses.jsonl').open('x') as stream:
        for req in requests:
            row={k:req[k] for k in ['id','arm','observation_index','request_sha256','state_sha256']};row.update(status='ok',predictions={},probabilities={});began=time.perf_counter()
            try:
                wire=urllib.request.Request(profile['endpoint'],data=encoded(req['body']),headers={'Content-Type':'application/json','Authorization':'Bearer '+key},method='POST')
                with opener.open(wire,timeout=60) as response:response_text=response.read().decode('utf-8')
                row['raw_response_text']=redact(response_text,key)
                def number(v):
                    result=float(v)
                    if not math.isfinite(result):raise ValueError('Non-finite response.')
                    return result
                raw=json.loads(response_text,parse_float=number,parse_constant=number)
                if not isinstance(raw,dict):raise ValueError('Response must be an object.')
                row.update(raw_response=redact(raw,key),resolved_model=raw.get('model'),usage=redact(raw.get('usage'),key))
                if raw.get('model') and raw['model']!=MODEL:reason='checkpoint_mismatch';raise ValueError('Checkpoint changed.')
                row['predictions'],row['probabilities'],row['provider_confidence']=normalize(raw) if req['arm']=='jev_direct' else normalize_report(raw)
            except urllib.error.HTTPError as e:
                row.update(status='error',http_status=e.code,error='Provider HTTP '+str(e.code))
                if e.code in {400,401,403,404,422,429,529}:reason='provider_http_'+str(e.code)
            except (ValueError,KeyError,TypeError,OSError) as e:
                row.update(status='error',error='Request/response validation failed ('+type(e).__name__+').')
                if isinstance(e,OSError):reason='network_error'
            row=redact(row,key);row['latency_ms']=(time.perf_counter()-began)*1000;rows.append(row);stream.write(json.dumps(row)+'\n');stream.flush()
            consecutive=consecutive+1 if row['status']!='ok' else 0
            if consecutive>=3 and not reason:reason='three_consecutive_failures'
            if progress:progress(len(rows),len(requests),req['arm'],row['status'])
            if reason:break
    packets=aggregate(records,rows);summary={**plan,'attempted_requests':len(rows),'failed_requests':sum(r['status']!='ok' for r in rows),'unattempted_requests':len(requests)-len(rows),'stopped_reason':reason,
        'status':'completed' if len(rows)==len(requests) and all(r['status']=='ok' for r in rows) else 'completed_with_errors','wall_seconds':time.perf_counter()-started,'approaches':{}}
    for a,pred in packets.items():
        write_jsonl(output/(a+'.jsonl'),pred);summary['approaches'][a]={'metrics':evaluate(output/'labels.jsonl',output/(a+'.jsonl'),inputs_path=output/'inputs.jsonl')}
    annotations=read_jsonl(output/'observation-references.jsonl');keymap={k['id']:k for k in keys};summary['report_metrics']=interpretation_score(rows,annotations,keymap,packets)
    summary['changes']=changes({a:{r['id']:r for r in p} for a,p in packets.items()},keymap,'jev_direct')
    summary['evidence_sha256']={p.name:sha(p.read_bytes()) for p in sorted(output.glob('*.jsonl'))};(output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');return summary


def verify(path,directory=DIRECTORY,root=ROOT):
    path=Path(path);root=Path(root);directory=Path(directory);validate(directory);s=json.loads(path.read_text());plan=json.loads((path.parent/'protocol.json').read_text());m=json.loads((directory/'manifest.json').read_text())
    if s['schema']!='report-language-hosted-1' or any(s.get(k)!=v for k,v in plan.items()) or s['data_sha256']!=m['sha256'] or any(sha((root/n).read_bytes())!=h for n,h in s['source_sha256'].items()):raise ValueError('Hosted report-language protocol/source differ.')
    expected={'inputs.jsonl','labels.jsonl','requests.jsonl','responses.jsonl','observation-references.jsonl','jev_direct.jsonl','jev_reading.jsonl'}
    if set(s['evidence_sha256'])!=expected:raise ValueError('Hosted evidence paths differ.')
    for n,h in s['evidence_sha256'].items():
        if sha((path.parent/n).read_bytes())!=h:raise ValueError('Hosted evidence differs.')
    for n,k in [('inputs','inputs'),('labels','labels'),('observation-references','observations')]:
        if sha((path.parent/(n+'.jsonl')).read_bytes())!=m['sha256']['narrow/development.'+k+'.jsonl']:raise ValueError('Hosted evaluation data differ.')
    requests=read_jsonl(path.parent/'requests.jsonl');records=read_jsonl(path.parent/'inputs.jsonl');keys={k['id']:k for k in read_jsonl(path.parent/'labels.jsonl')}
    _,_,_,expected_requests=prepare({'model':s['requested_model'],'endpoint':s['endpoint'],'context_tokens':s['declared_context_tokens']},directory)
    if requests!=expected_requests or sha((path.parent/'requests.jsonl').read_bytes())!=s['requests_sha256'] or s['maximum_requests']!=len(requests):raise ValueError('Hosted requests differ.')
    responses=read_jsonl(path.parent/'responses.jsonl')
    if len(responses)!=s['attempted_requests'] or s['failed_requests']!=sum(r['status']!='ok' for r in responses) or s['unattempted_requests']!=len(requests)-len(responses):raise ValueError('Hosted attempt counts differ.')
    for r,q in zip(responses,requests):
        if any(r.get(k)!=q[k] for k in ['id','arm','observation_index','request_sha256','state_sha256']):raise ValueError('Hosted response/request join differs.')
        if r['status']=='ok':
            p,probs,c=normalize(r['raw_response']) if r['arm']=='jev_direct' else normalize_report(r['raw_response'])
            if p!=r['predictions'] or probs!=r['probabilities'] or c!=r['provider_confidence'] or r.get('resolved_model')!=r['raw_response'].get('model') or r.get('resolved_model') not in {None,MODEL}:raise ValueError('Hosted normalized response differs.')
    packets=aggregate(records,responses)
    for a,pred in packets.items():
        if pred!=read_jsonl(path.parent/(a+'.jsonl')) or s['approaches'][a]['metrics']!=evaluate(path.parent/'labels.jsonl',path.parent/(a+'.jsonl'),inputs_path=path.parent/'inputs.jsonl'):raise ValueError('Hosted packet aggregation differs.')
    if s['report_metrics']!=interpretation_score(responses,read_jsonl(path.parent/'observation-references.jsonl'),keys,packets) or s['changes']!=changes({a:{r['id']:r for r in p} for a,p in packets.items()},keys,'jev_direct'):raise ValueError('Hosted diagnostic scores differ.')
    if s['status']!=('completed' if len(responses)==len(requests) and not s['failed_requests'] else 'completed_with_errors'):raise ValueError('Hosted status differs.')
    return s,{a:{r['id']:r for r in p} for a,p in packets.items()},requests,responses
