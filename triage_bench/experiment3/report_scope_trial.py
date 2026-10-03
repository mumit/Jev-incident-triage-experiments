"""Matched reading-instruction trial with frozen report-model and policy controls."""
import json,math,time,urllib.error,urllib.request
from datetime import datetime,timezone
from pathlib import Path
from triage_bench.dataset import ROOT,read_jsonl,write_jsonl
from triage_bench.evaluate import evaluate
from triage_bench.runner import NoRedirect,clean_api_key
from .report_scope_data import DIRECTORY,validate
from .report_language_data import DIRECTORY as TRAINING
from .report_language_trial import SOURCES as PREVIOUS,changes,method_weights
from .report_language_hosted import prepare as check_profile,report_body,normalize_report,interpretation_score
from .interpretation_model import ReportClassifier,PARAMETERS,report_inputs,pipeline_input,apply_policy,rule_reading
from .hosted import encoded,redact
from .transforms import MODEL,sha

LOCAL={'narrow':'Report ML · original phrases','broad':'Report ML · broader phrases','report_rules':'Report rules → policy'}
HOSTED={'jev_original':'Jev · original report question','jev_focal':'Jev · measured-function question'}
SOURCES=list(dict.fromkeys(PREVIOUS+['triage_bench/experiment3/report_language_hosted.py','triage_bench/experiment3/report_scope_data.py','triage_bench/experiment3/report_scope_trial.py']))
FOCAL_INSTRUCTION=' Judge the operation of the specific function this report explicitly measures, not the health of the whole component or wider service. Verified successful request intake or handler operation is normal for that measured function even if later registration or end-to-end completion is unmeasured. If the report instead measures completion, request acceptance alone leaves completion unknown. Success of a different function does not cancel an explicit malfunction of the measured function. Keep expected behavior, explicit malfunction and uncertainty distinct.'


def body(text,arm):
    if arm not in HOSTED:raise ValueError('Unknown report-scope arm.')
    result=report_body(text)
    if arm=='jev_focal':result['questions']['reading']['instructions']+=FOCAL_INSTRUCTION
    return result


def context(directory):
    directory=Path(directory);validate(directory);m=json.loads((directory/'manifest.json').read_text());records=read_jsonl(directory/'development.inputs.jsonl');keys=read_jsonl(directory/'development.labels.jsonl');ann=read_jsonl(directory/'development.observations.jsonl')
    return m,records,keys,ann


def diagnostic(records,annotations,keys):
    refs={}
    for a in annotations:refs.setdefault(a['id'],[]).append(a)
    rows=[{'id':r['id'],'status':'ok',**apply_policy(r,refs[r['id']])} for r in records];by={k['id']:k for k in keys}
    wrong=[r['id'] for r in rows if r['predictions']!=by[r['id']]['labels']]
    return rows,{'label':'Reference readings fed to unchanged policy. Evaluation diagnostic, not model performance or an accuracy ceiling. Incorrect readings can mask this policy gap.','mismatched_packets':wrong}


def prepare(profile,directory=DIRECTORY):
    check_profile(profile)
    m,records,keys,ann=context(directory);requests=[];ordinal=0
    for r in records:
        for report in report_inputs(r):
            for arm in (list(HOSTED) if ordinal%2==0 else list(reversed(HOSTED))):
                payload=body(report['text'],arm);wire=encoded(payload)
                if len(wire)+512>profile['context_tokens']:raise ValueError('Context preflight failed.')
                requests.append({'id':r['id'],'arm':arm,'observation_index':report['observation_index'],'body':payload,'request_sha256':sha(wire),'state_sha256':sha(payload['state'].encode())})
            ordinal+=1
    _,diag=diagnostic(records,ann,keys)
    if diag['mismatched_packets']!=m['known_policy_gaps']:raise ValueError('Predeclared policy gap differs.')
    plan={'schema':'report-scope-hosted-1','model':MODEL,'endpoint':profile['endpoint'],'context_tokens':profile['context_tokens'],'arms':HOSTED,'data_sha256':m['sha256'],'source_sha256':{n:sha((ROOT/n).read_bytes()) for n in SOURCES},'records':len(records),'reports':len(ann),'pairs':m['pairs'],'maximum_requests':len(requests),'human_decision':m['human_decision'],'reference_status':m['reference_status'],'primary_comparison':'Identical normalized report texts, model, domain questions, choice criteria and frozen policy. Only reading-question instructions differ. The added paragraph contains several related scope clarifications; effects of individual sentences are not isolated.','execution':'Serial; arm order alternates by report. One response per planned request; no warmup or automatic retries.','failure_stop':'Immediate stop on configuration/access/rate-limit/checkpoint/network errors; otherwise stop after three consecutive malformed responses. Failed or missing report replies invalidate packet predictions.','reference_policy_diagnostic':diag,'context_bound':'UTF-8 request bytes plus 512; not the provider tokenizer.','questions':{a:body('',a)['questions'] for a in HOSTED}}
    return plan,records,keys,ann,requests


def aggregate(records,responses):
    actual={(r['id'],r['arm'],r['observation_index']):r for r in responses};result={}
    for arm in HOSTED:
        rows=[]
        for r in records:
            replies=[actual.get((r['id'],arm,o['observation_index'])) for o in report_inputs(r)]
            if all(x and x['status']=='ok' for x in replies):
                readings=[{'observation_index':x['observation_index'],**x['predictions'],'probabilities':x['probabilities'],'provider_confidence':x.get('provider_confidence',{})} for x in replies];rows.append({'id':r['id'],'status':'ok','readings':readings,**apply_policy(r,readings)})
            elif any(replies):rows.append({'id':r['id'],'status':'error','predictions':{},'readings':[],'error':'Report responses failed or are incomplete.'})
        result[arm]=rows
    return result


def report_scores(responses,annotations,keys,packets):
    scores={}
    for arm in packets:
        replies=[{**r,'arm':'jev_reading'} for r in responses if r['arm']==arm]
        scores[arm]=interpretation_score(replies,annotations,keys,{'jev_reading':packets[arm]})
    return scores


def report_changes(responses,annotations):
    actual={(r['id'],r['arm'],r['observation_index']):r for r in responses};result={'reports_fixed':[],'reports_lost':[],'newly_wrong_domain':[],'newly_wrong_reading':[]}
    for a in annotations:
        b=actual.get((a['id'],'jev_original',a['observation_index']),{});n=actual.get((a['id'],'jev_focal',a['observation_index']),{});b=b.get('predictions',{}) if b.get('status')=='ok' else {};n=n.get('predictions',{}) if n.get('status')=='ok' else {};item={'id':a['id'],'observation_index':a['observation_index']};before=all(b.get(f)==a[f] for f in ['domain','reading']);after=all(n.get(f)==a[f] for f in ['domain','reading'])
        if after and not before:result['reports_fixed'].append(item)
        if before and not after:result['reports_lost'].append(item)
        for f in ['domain','reading']:
            if b.get(f)==a[f] and n.get(f)!=a[f]:result['newly_wrong_'+f].append(item)
    return result


def run_hosted(output,profile,directory=DIRECTORY):
    plan,records,keys,ann,requests=prepare(profile,directory);key=clean_api_key(profile.get('api_key',''));output=Path(output)
    if not key:raise ValueError('Configure a server-side Jev key.')
    if output.exists():raise ValueError('Report-scope runs are immutable.')
    output.mkdir(parents=True)
    for n,rows in [('inputs',records),('labels',keys),('observation-references',ann),('requests',requests)]:write_jsonl(output/(n+'.jsonl'),rows)
    plan.update(started_at=datetime.now(timezone.utc).isoformat(),requests_sha256=sha((output/'requests.jsonl').read_bytes()));(output/'protocol.json').write_text(json.dumps(plan,indent=2)+'\n');responses=[];reason=None;consecutive=0;opener=urllib.request.build_opener(NoRedirect())
    with (output/'responses.jsonl').open('x') as stream:
        for q in requests:
            row={k:q[k] for k in ['id','arm','observation_index','request_sha256','state_sha256']};row.update(status='ok',predictions={},probabilities={});began=time.perf_counter()
            try:
                req=urllib.request.Request(profile['endpoint'],data=encoded(q['body']),headers={'Content-Type':'application/json','Authorization':'Bearer '+key},method='POST')
                with opener.open(req,timeout=60) as reply:text=reply.read().decode('utf-8')
                def number(v):
                    n=float(v)
                    if not math.isfinite(n):raise ValueError('Non-finite response.')
                    return n
                raw=json.loads(text,parse_float=number,parse_constant=number)
                if not isinstance(raw,dict):raise ValueError('Response must be an object.')
                row.update(raw_response=redact(raw,key),raw_response_text=redact(text,key),resolved_model=raw.get('model'),usage=redact(raw.get('usage'),key))
                if raw.get('model') and raw['model']!=MODEL:reason='checkpoint_mismatch';raise ValueError('Checkpoint changed.')
                row['predictions'],row['probabilities'],row['provider_confidence']=normalize_report(raw)
            except urllib.error.HTTPError as e:
                row.update(status='error',http_status=e.code,error='Provider HTTP '+str(e.code))
                if e.code in {400,401,403,404,422,429,529}:reason='provider_http_'+str(e.code)
            except (ValueError,KeyError,TypeError,OSError) as e:
                row.update(status='error',error='Request/response validation failed ('+type(e).__name__+').')
                if isinstance(e,OSError):reason='network_error'
            row=redact(row,key);row['latency_ms']=(time.perf_counter()-began)*1000;responses.append(row);stream.write(json.dumps(row)+'\n');stream.flush();consecutive=consecutive+1 if row['status']!='ok' else 0
            if consecutive>=3 and not reason:reason='three_consecutive_failures'
            if reason:break
    packets=aggregate(records,responses);summary={**plan,'attempted_requests':len(responses),'failed_requests':sum(r['status']!='ok' for r in responses),'unattempted_requests':len(requests)-len(responses),'stopped_reason':reason,'status':'completed' if len(responses)==len(requests) and all(r['status']=='ok' for r in responses) else 'completed_with_errors','approaches':{}}
    for a,rows in packets.items():write_jsonl(output/(a+'.jsonl'),rows);summary['approaches'][a]={'metrics':evaluate(output/'labels.jsonl',output/(a+'.jsonl'),inputs_path=output/'inputs.jsonl')}
    summary.update(report_metrics=report_scores(responses,ann,{k['id']:k for k in keys},packets),changes=changes({a:{r['id']:r for r in rows} for a,rows in packets.items()},{k['id']:k for k in keys},'jev_original'),report_changes=report_changes(responses,ann),evidence_sha256={p.name:sha(p.read_bytes()) for p in sorted(output.glob('*.jsonl'))});(output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');return summary


def run_local(output,directory=DIRECTORY):
    m,records,keys,ann=context(directory);output=Path(output)
    if output.exists():raise ValueError('Report-scope runs are immutable.')
    output.mkdir(parents=True);plan={'schema':'report-scope-local-1','source_sha256':{n:sha((ROOT/n).read_bytes()) for n in SOURCES},'data_sha256':m['sha256'],'training_sha256':{str(p.relative_to(TRAINING)):sha(p.read_bytes()) for a in ['narrow','broad'] for p in (TRAINING/a).glob('train.*.jsonl')},'arms':LOCAL,'parameters':PARAMETERS,'records':len(records),'reports':len(ann),'reference_status':m['reference_status'],'execution':'Reuse both frozen report training recipes as controls; fit training only, with no new training labels or development tuning.'};(output/'protocol.json').write_text(json.dumps(plan,indent=2)+'\n')
    for n,rows in [('inputs',records),('labels',keys),('observation-references',ann)]:write_jsonl(output/(n+'.jsonl'),rows)
    summary={**plan,'approaches':{}};packets={};responses=[]
    for arm in LOCAL:
        reader=ReportClassifier(TRAINING/arm) if arm!='report_rules' else None;predictions=[];inspections=[]
        for r in records:
            meanings=reader.predict(r) if reader else [rule_reading(o['text'],o['observation_index']) for o in report_inputs(r)];predictions.append({'id':r['id'],'status':'ok','readings':meanings,**apply_policy(r,meanings)})
            if reader:inspections.append({'id':r['id'],'reports':[{'observation_index':o['observation_index'],**reader.inspect(o['text'])} for o in report_inputs(r)]})
            responses.extend({'id':r['id'],'arm':arm,'observation_index':o['observation_index'],'status':'ok','predictions':{f:o[f] for f in ['domain','reading']}} for o in meanings)
        write_jsonl(output/(arm+'.jsonl'),predictions);packets[arm]=predictions
        if reader:write_jsonl(output/(arm+'.inspections.jsonl'),inspections)
        summary['approaches'][arm]={'metrics':evaluate(output/'labels.jsonl',output/(arm+'.jsonl'),inputs_path=output/'inputs.jsonl')}
        if reader:summary['approaches'][arm].update(training=reader.metadata,method_weights_normal_minus_fault=method_weights(reader))
    diagnostic_rows,diag=diagnostic(records,ann,keys);write_jsonl(output/'reference-policy-diagnostic.jsonl',diagnostic_rows);diag['metrics']=evaluate(output/'labels.jsonl',output/'reference-policy-diagnostic.jsonl',inputs_path=output/'inputs.jsonl');summary.update(reference_policy_diagnostic=diag,report_metrics=report_scores(responses,ann,{k['id']:k for k in keys},packets),changes=changes({a:{r['id']:r for r in v} for a,v in packets.items()},{k['id']:k for k in keys}),evidence_sha256={p.name:sha(p.read_bytes()) for p in sorted(output.glob('*.jsonl'))});(output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');return summary


def verify(path,directory=DIRECTORY):
    path=Path(path);s=json.loads(path.read_text());plan=json.loads((path.parent/'protocol.json').read_text());m,records,keys,ann=context(directory)
    if s.get('schema') not in {'report-scope-hosted-1','report-scope-local-1'} or set(s['source_sha256'])!=set(SOURCES) or any(s.get(k)!=v for k,v in plan.items()) or s['data_sha256']!=m['sha256'] or any(sha((ROOT/n).read_bytes())!=h for n,h in s['source_sha256'].items()):raise ValueError('Report-scope protocol/source differ.')
    hosted=s['schema']=='report-scope-hosted-1'
    expected={'inputs.jsonl','labels.jsonl','observation-references.jsonl'}|{a+'.jsonl' for a in (HOSTED if hosted else LOCAL)}|({'requests.jsonl','responses.jsonl'} if hosted else {'narrow.inspections.jsonl','broad.inspections.jsonl','reference-policy-diagnostic.jsonl'})
    if set(s['evidence_sha256'])!=expected or any(sha((path.parent/n).read_bytes())!=h for n,h in s['evidence_sha256'].items()):raise ValueError('Report-scope evidence differs.')
    for n,v in [('inputs',records),('labels',keys),('observation-references',ann)]:
        if read_jsonl(path.parent/(n+'.jsonl'))!=v:raise ValueError('Report-scope evaluation data differ.')
    packets={a:read_jsonl(path.parent/(a+'.jsonl')) for a in (HOSTED if hosted else LOCAL)};keymap={k['id']:k for k in keys};responses=[]
    if set(s['approaches'])!=set(packets):raise ValueError('Report-scope arm coverage differs.')
    if hosted:
        prepared,*_,requests=prepare({'model':s['model'],'endpoint':s['endpoint'],'context_tokens':s['context_tokens']},directory)
        if any(s.get(k)!=v for k,v in prepared.items()) or read_jsonl(path.parent/'requests.jsonl')!=requests or sha((path.parent/'requests.jsonl').read_bytes())!=s['requests_sha256']:raise ValueError('Matched hosted requests differ.')
        responses=read_jsonl(path.parent/'responses.jsonl')
        if len(responses)>len(requests):raise ValueError('Extra hosted responses.')
        for r,q in zip(responses,requests):
            if any(r.get(k)!=q[k] for k in ['id','arm','observation_index','request_sha256','state_sha256']):raise ValueError('Hosted response join differs.')
            if r['status']=='ok':
                p,probs,c=normalize_report(r['raw_response'])
                if p!=r['predictions'] or probs!=r['probabilities'] or c!=r['provider_confidence'] or r['raw_response'].get('model') not in {None,MODEL}:raise ValueError('Hosted normalization differs.')
        if packets!=aggregate(records,responses) or s['attempted_requests']!=len(responses) or s['failed_requests']!=sum(r['status']!='ok' for r in responses) or s['unattempted_requests']!=len(requests)-len(responses) or s['status']!=('completed' if len(responses)==len(requests) and not s['failed_requests'] else 'completed_with_errors'):raise ValueError('Hosted aggregation/counts differ.')
        if s['report_changes']!=report_changes(responses,ann):raise ValueError('Report regressions differ.')
    else:
        if s['parameters']!=PARAMETERS or any(sha((TRAINING/n).read_bytes())!=h for n,h in s['training_sha256'].items()):raise ValueError('Frozen report training differs.')
        for arm,rows in packets.items():
            if {r['id'] for r in rows}!=set(keymap) or len(rows)!=len(keymap):raise ValueError('Local packet coverage differs.')
            for r in rows:
                source=next(x for x in records if x['id']==r['id']);result=apply_policy(source,r['readings'])
                if any(result[k]!=r[k] for k in result):raise ValueError('Policy trace differs.')
                responses.extend({'id':r['id'],'arm':arm,'observation_index':o['observation_index'],'status':'ok','predictions':{f:o[f] for f in ['domain','reading']}} for o in r['readings'])
            if arm=='report_rules':continue
            meta=s['approaches'][arm]['training']
            if meta['parameters']!=PARAMETERS or meta['training_inputs_sha256']!=s['training_sha256'][arm+'/train.inputs.jsonl'] or meta['training_annotations_sha256']!=s['training_sha256'][arm+'/train.observations.jsonl']:raise ValueError('Training metadata differs.')
            inspections=read_jsonl(path.parent/(arm+'.inspections.jsonl'));rowmap={r['id']:r for r in rows}
            if len(inspections)!=len(records) or {r['id'] for r in inspections}!=set(keymap):raise ValueError('Inspection coverage differs.')
            for item in inspections:
                if [o['observation_index'] for o in item['reports']]!=list(range(len(rowmap[item['id']]['readings']))):raise ValueError('Report inspection join differs.')
                for o in item['reports']:
                    values={v['feature']:v['value'] for v in o['vector']['nonzero']}
                    if o['vector']['dimensions']!=meta['feature_count'] or set(o['fields'])!={'domain','reading'}:raise ValueError('Report dimensions differ.')
                    for f,e in o['fields'].items():
                        probs=rowmap[item['id']]['readings'][o['observation_index']]['probabilities'][f];margin=e['intercept_difference']+sum(c['contribution'] for c in e['top_contributions'])+e['remaining_contribution']
                        if probs!=e['probabilities'] or not math.isclose(margin,math.log(probs[e['selected']]/probs[e['compared_with']]),abs_tol=1e-8):raise ValueError('Report margin differs.')
                        for c in e['top_contributions']:
                            if c['value']!=values[c['feature']] or not math.isclose(c['contribution'],c['value']*c['coefficient_difference'],abs_tol=1e-10):raise ValueError('Report contribution differs.')
        rows,diag=diagnostic(records,ann,keys);diag['metrics']=evaluate(path.parent/'labels.jsonl',path.parent/'reference-policy-diagnostic.jsonl',inputs_path=path.parent/'inputs.jsonl')
        if rows!=read_jsonl(path.parent/'reference-policy-diagnostic.jsonl') or diag!=s['reference_policy_diagnostic']:raise ValueError('Reference-reading diagnostic differs.')
    for arm,result in s['approaches'].items():
        if set(s['approaches'])!=set(packets) or result['metrics']!=evaluate(path.parent/'labels.jsonl',path.parent/(arm+'.jsonl'),inputs_path=path.parent/'inputs.jsonl'):raise ValueError('Packet scores differ.')
    if s['report_metrics']!=report_scores(responses,ann,keymap,packets) or s['changes']!=changes({a:{r['id']:r for r in v} for a,v in packets.items()},keymap,'jev_original' if hosted else 'narrow'):raise ValueError('Report/policy diagnostics differ.')
    return s,{a:{r['id']:r for r in v} for a,v in packets.items()},read_jsonl(path.parent/'requests.jsonl') if hosted else [],responses
