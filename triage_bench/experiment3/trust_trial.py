"""Matched declaration guard comparison using frozen readers and occurrence joins."""
import copy,json,math,time,urllib.error,urllib.request
from datetime import datetime,timezone
from pathlib import Path
from triage_bench.dataset import ROOT,read_jsonl,write_jsonl
from triage_bench.evaluate import evaluate
from triage_bench.runner import NoRedirect,clean_api_key
from .trust_data import DIRECTORY,validate
from .trust_policy import effective_readings,apply_trust_policy
from .declared_trial import SOURCES as PREVIOUS,body as frozen_declared_body
from .metadata_trial import report_metrics,attribution
from .metadata_policy import apply_metadata_policy
from .report_scope_trial import body as frozen_body,LOCAL
from .report_language_hosted import prepare as check_profile,normalize_report
from .report_language_data import DIRECTORY as TRAINING
from .report_language_trial import changes
from .interpretation_model import ReportClassifier,PARAMETERS,report_inputs,rule_reading
from .hosted import encoded,redact
from .transforms import MODEL,sha
HOSTED={'jev_declared':'Jev · declared-domain question'}
POLICIES={'unguarded':'Structured domain · base policy','guarded':'Structured domain · declaration guard'}
def arm_labels(readers):return {r+'__'+p:label+' · '+name for r,label in readers.items() for p,name in POLICIES.items()}
SOURCES=list(dict.fromkeys(PREVIOUS+['triage_bench/experiment3/trust_data.py','triage_bench/experiment3/trust_policy.py','triage_bench/experiment3/trust_trial.py']))

def body(text,reader):
 if reader not in HOSTED:raise ValueError('Unknown trust reader.')
 return frozen_declared_body(text,reader)

def context(directory=DIRECTORY):
 directory=Path(directory);validate(directory);m=json.loads((directory/'manifest.json').read_text());records=read_jsonl(directory/'development.inputs.jsonl');keys=read_jsonl(directory/'development.labels.jsonl');ann=read_jsonl(directory/'development.observations.jsonl');texts={};by={r['id']:r for r in records};refs={(a['id'],a['observation_index']):a for a in ann}
 for r in records:
  for o in report_inputs(r):
   identifier=sha(o['text'].encode());texts.setdefault(identifier,{'text_id':identifier,'text':o['text'],'occurrences':[]})['occurrences'].append({'id':r['id'],'observation_index':o['observation_index']})
 for t in texts.values():
  meanings={(refs[o['id'],o['observation_index']]['domain'],refs[o['id'],o['observation_index']]['reading']) for o in t['occurrences']}
  if len(meanings)!=1:raise ValueError('Shared report meanings differ.')
 return m,records,keys,ann,list(texts.values())

def aggregate(records,texts,responses,readers):
 actual={(r['reader'],r['text_id']):r for r in responses};text_for={(o['id'],o['observation_index']):t['text_id'] for t in texts for o in t['occurrences']};rows={}
 for reader in readers:
  for policy in POLICIES:
   arm=reader+'__'+policy;rows[arm]=[]
   for r in records:
    replies=[actual.get((reader,text_for[r['id'],i])) for i in range(len(r['input']['observations']))]
    if all(x and x['status']=='ok' for x in replies):
     raw=[{'observation_index':i,'text_id':text_for[r['id'],i],**x['predictions'],'probabilities':x.get('probabilities',{}),'provider_confidence':x.get('provider_confidence',{})} for i,x in enumerate(replies)]
     readings=effective_readings(r,raw);result=apply_trust_policy(r,readings,policy=='guarded');rows[arm].append({'id':r['id'],'status':'ok','readings':readings,'raw_readings':raw,**result})
    elif any(replies):rows[arm].append({'id':r['id'],'status':'error','readings':[],'raw_readings':[],'predictions':{},'error':'A shared report response failed or is missing.'})
 return rows

def diagnostic(records,ann,guarded=True):
 refs={}
 for a in ann:refs.setdefault(a['id'],[]).append(a)
 return [{'id':r['id'],'status':'ok',**apply_trust_policy(r,effective_readings(r,refs[r['id']]),guarded)} for r in records]

def matched_changes(packets,keys,readers):
 return {r:changes({a:{x['id']:x for x in rows} for a,rows in packets.items() if a.startswith(r+'__')},keys,r+'__unguarded') for r in readers}

def plan_base(schema,directory):
 m,records,keys,ann,texts=context(directory);keymap={k['id']:k for k in keys};diag=diagnostic(records,ann);control='matched_base_policy_per_reader'
 return {'schema':schema,'data_sha256':m['sha256'],'source_sha256':{n:sha((ROOT/n).read_bytes()) for n in SOURCES},'records':len(records),'report_occurrences':len(ann),'distinct_report_texts':len(texts),'pairs':m['pairs'],'human_decision':m['human_decision'],'reference_status':m['reference_status'],'control':control,'prepared_reference_diagnostic':{'reference_matches':sum(r['predictions']==keymap[r['id']]['labels'] for r in diag),'records':len(records),'mismatched_packets':[r['id'] for r in diag if r['predictions']!=keymap[r['id']]['labels']]},'comparison':'Both policies use occurrence-specific structured domains and identical frozen interpreter readings. The candidate alone checks explicit structured/prose enum disagreement on eligible fault-bearing assets. No questions or training change.','response_reuse':'One actual response per distinct text/reader, reused across correlated occurrences and paired packets. Software-domain paths make no model calls.','software_assumption':'Structured and prose declarations can disagree. Their authority and actual reliability are unvalidated. An explicit enum parser checks consistency, not correctness or root cause.'},records,keys,ann,texts

def prepare(profile,directory=DIRECTORY):
 check_profile(profile);plan,records,keys,ann,texts=plan_base('declaration-trust-hosted-1',directory);requests=[]
 for i,t in enumerate(texts):
  for reader in (list(HOSTED) if i%2==0 else list(reversed(HOSTED))):
   payload=body(t['text'],reader);wire=encoded(payload)
   if len(wire)+512>profile['context_tokens']:raise ValueError('Context preflight failed.')
   requests.append({'text_id':t['text_id'],'reader':reader,'body':payload,'request_sha256':sha(wire)})
 plan.update(model=MODEL,endpoint=profile['endpoint'],context_tokens=profile['context_tokens'],readers=HOSTED,maximum_requests=len(requests),execution='Serial, one frozen reader per distinct text. No warmup or automatic retries.',failure_stop='Stop on access/configuration/rate-limit/checkpoint/network errors, or three consecutive malformed responses. Every dependent packet, including software-domain controls, remains invalid when a shared reading fails.',questions={a:body('',a)['questions'] for a in HOSTED})
 return plan,records,keys,ann,texts,requests

def write_setup(output,plan,records,keys,ann,texts,requests=None):
 output=Path(output)
 if output.exists():raise ValueError('Trust-domain runs are immutable.')
 output.mkdir(parents=True)
 for n,v in [('inputs',records),('labels',keys),('observation-references',ann),('report-inputs',texts)]:write_jsonl(output/(n+'.jsonl'),v)
 if requests is not None:write_jsonl(output/'requests.jsonl',requests)
 plan.update(started_at=datetime.now(timezone.utc).isoformat());(output/'protocol.json').write_text(json.dumps(plan,indent=2)+'\n');return output

def finish(output,plan,records,keys,ann,texts,responses,reason=None,inspections=None):
 packets=aggregate(records,texts,responses,plan['readers']);arms=arm_labels(plan['readers']);keymap={k['id']:k for k in keys};summary={**plan,'arms':arms,'approaches':{}}
 for arm,rows in packets.items():
  write_jsonl(output/(arm+'.jsonl'),rows);summary['approaches'][arm]={'metrics':evaluate(output/'labels.jsonl',output/(arm+'.jsonl'),inputs_path=output/'inputs.jsonl')}
 summary.update(report_metrics=report_metrics(texts,responses,ann,plan['readers']),attribution=attribution(texts,responses,ann,keymap,packets),changes=matched_changes(packets,keymap,plan['readers']))
 summary['reference_policy_diagnostic']={}
 for policy in POLICIES:
  name='reference-policy-'+policy+'.jsonl';write_jsonl(output/name,diagnostic(records,ann,policy=='guarded'));summary['reference_policy_diagnostic'][policy]={'label':'Prewritten report meanings plus supplied metadata fed to policy; evaluation diagnostic, not a model score or accuracy ceiling.','metrics':evaluate(output/'labels.jsonl',output/name,inputs_path=output/'inputs.jsonl')}
 if inspections:
  for reader,rows in inspections.items():write_jsonl(output/(reader+'.inspections.jsonl'),rows)
 summary.update(attempted_predictions=len(responses),failed_predictions=sum(r['status']!='ok' for r in responses),unattempted_predictions=len(texts)*len(plan['readers'])-len(responses),stopped_reason=reason,status='completed' if len(responses)==len(texts)*len(plan['readers']) and all(r['status']=='ok' for r in responses) else 'completed_with_errors',evidence_sha256={p.name:sha(p.read_bytes()) for p in sorted(output.glob('*.jsonl'))});(output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');return summary

def run_local(output,directory=DIRECTORY):
    plan,records,keys,ann,texts=plan_base('declaration-trust-local-1',directory);plan.update(readers=LOCAL,parameters=PARAMETERS,training_sha256={str(p.relative_to(TRAINING)):sha(p.read_bytes()) for a in ['narrow','broad'] for p in (TRAINING/a).glob('train.*.jsonl')});output=write_setup(output,plan,records,keys,ann,texts);by={r['id']:r for r in records};responses=[];inspections={};metadata={}
    for reader in LOCAL:
        model=ReportClassifier(TRAINING/reader) if reader!='report_rules' else None
        if model:metadata[reader]=model.metadata;inspections[reader]=[]
        for t in texts:
            o=t['occurrences'][0];r=model.predict(by[o['id']])[o['observation_index']] if model else rule_reading(t['text'],o['observation_index']);responses.append({'text_id':t['text_id'],'reader':reader,'status':'ok','predictions':{f:r[f] for f in ['domain','reading']},'probabilities':r.get('probabilities',{}),'rule':r.get('rule')})
            if model:inspections[reader].append({'text_id':t['text_id'],'text':t['text'],**model.inspect(t['text'])})
    plan['training_metadata']=metadata;(output/'protocol.json').write_text(json.dumps(plan,indent=2)+'\n');write_jsonl(output/'responses.jsonl',responses);return finish(output,plan,records,keys,ann,texts,responses,inspections=inspections)

def run_hosted(output,profile,directory=DIRECTORY):
    plan,records,keys,ann,texts,requests=prepare(profile,directory);key=clean_api_key(profile.get('api_key',''))
    if not key:raise ValueError('Configure a server-side Jev key.')
    output=write_setup(output,plan,records,keys,ann,texts,requests);opener=urllib.request.build_opener(NoRedirect());responses=[];reason=None;consecutive=0
    with (output/'responses.jsonl').open('x') as stream:
        for q in requests:
            row={k:q[k] for k in ['text_id','reader','request_sha256']};row.update(status='ok',predictions={},probabilities={});started=time.perf_counter()
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
            row=redact(row,key);row['latency_ms']=(time.perf_counter()-started)*1000;responses.append(row);stream.write(json.dumps(row)+'\n');stream.flush();consecutive=consecutive+1 if row['status']!='ok' else 0
            if consecutive>=3 and not reason:reason='three_consecutive_failures'
            if reason:break
    return finish(output,plan,records,keys,ann,texts,responses,reason)

def verify(path,directory=DIRECTORY):
 path=Path(path);s=json.loads(path.read_text());protocol=json.loads((path.parent/'protocol.json').read_text());m,records,keys,ann,texts=context(directory)
 if s.get('schema') not in {'declaration-trust-local-1','declaration-trust-hosted-1'} or set(s['source_sha256'])!=set(SOURCES) or any(s.get(k)!=v for k,v in protocol.items()) or s['data_sha256']!=m['sha256'] or any(sha((ROOT/n).read_bytes())!=h for n,h in s['source_sha256'].items()):raise ValueError('Trust protocol/source differ.')
 hosted=s['schema']=='declaration-trust-hosted-1';readers=HOSTED if hosted else LOCAL;arms=arm_labels(readers);expected={'inputs.jsonl','labels.jsonl','observation-references.jsonl','report-inputs.jsonl','responses.jsonl','reference-policy-unguarded.jsonl','reference-policy-guarded.jsonl'}|{a+'.jsonl' for a in arms}|({'requests.jsonl'} if hosted else {'narrow.inspections.jsonl','broad.inspections.jsonl'})
 if set(s['evidence_sha256'])!=expected or any(sha((path.parent/n).read_bytes())!=h for n,h in s['evidence_sha256'].items()):raise ValueError('Trust evidence differs.')
 for name,rows in [('inputs',records),('labels',keys),('observation-references',ann),('report-inputs',texts)]:
  if read_jsonl(path.parent/(name+'.jsonl'))!=rows:raise ValueError('Trust data joins differ.')
 responses=read_jsonl(path.parent/'responses.jsonl');expected_pairs={(r,t['text_id']) for r in readers for t in texts}
 if len({(r['reader'],r['text_id']) for r in responses})!=len(responses) or any((r['reader'],r['text_id']) not in expected_pairs or r['status'] not in {'ok','error'} for r in responses):raise ValueError('Shared declared response joins differ.')
 if hosted:
  prepared,*_,requests=prepare({'model':s['model'],'endpoint':s['endpoint'],'context_tokens':s['context_tokens']},directory)
  if any(s.get(k)!=v for k,v in prepared.items()) or read_jsonl(path.parent/'requests.jsonl')!=requests or len(responses)>len(requests):raise ValueError('Frozen declared requests differ.')
  for r,q in zip(responses,requests):
   if any(r.get(k)!=q[k] for k in ['text_id','reader','request_sha256']):raise ValueError('Trust response order differs.')
   if r['status']=='ok':
    p,probs,c=normalize_report(r['raw_response'])
    if r['raw_response'].get('model') not in {None,MODEL} or p!=r['predictions'] or probs!=r['probabilities'] or c!=r['provider_confidence']:raise ValueError('Trust response normalization differs.')
 else:
  prepared,*_=plan_base('declaration-trust-local-1',directory)
  if any(s.get(k)!=v for k,v in prepared.items()) or s['readers']!=LOCAL or s['parameters']!=PARAMETERS or set(s['training_sha256'])!={str(p.relative_to(TRAINING)) for a in ['narrow','broad'] for p in (TRAINING/a).glob('train.*.jsonl')} or any(sha((TRAINING/n).read_bytes())!=h for n,h in s['training_sha256'].items()) or len(responses)!=len(expected_pairs):raise ValueError('Frozen declared training differs.')
  for reader in ['narrow','broad']:
   meta=s['training_metadata'][reader];inspections=read_jsonl(path.parent/(reader+'.inspections.jsonl'));actual={r['text_id']:r for r in responses if r['reader']==reader}
   if meta['parameters']!=PARAMETERS or meta['training_inputs_sha256']!=s['training_sha256'][reader+'/train.inputs.jsonl'] or meta['training_annotations_sha256']!=s['training_sha256'][reader+'/train.observations.jsonl'] or len(inspections)!=len(texts) or {r['text_id'] for r in inspections}!={t['text_id'] for t in texts}:raise ValueError('Trust training/inspection metadata differ.')
   for o in inspections:
    if sha(o['text'].encode())!=o['text_id'] or o['vector']['dimensions']!=meta['feature_count'] or set(o['fields'])!={'domain','reading'}:raise ValueError('Trust inspection differs.')
    values={v['feature']:v['value'] for v in o['vector']['nonzero']}
    for f,e in o['fields'].items():
     p=actual[o['text_id']]['probabilities'][f];margin=e['intercept_difference']+sum(c['contribution'] for c in e['top_contributions'])+e['remaining_contribution']
     if p!=e['probabilities'] or e['selected']!=actual[o['text_id']]['predictions'][f] or not math.isclose(margin,math.log(p[e['selected']]/p[e['compared_with']]),abs_tol=1e-8):raise ValueError('Trust fitted margin differs.')
     if any(c['value']!=values[c['feature']] or not math.isclose(c['value']*c['coefficient_difference'],c['contribution'],abs_tol=1e-10) for c in e['top_contributions']):raise ValueError('Trust fitted contribution differs.')
 packets=aggregate(records,texts,responses,readers);keymap={k['id']:k for k in keys}
 if s['arms']!=arms or set(s['approaches'])!=set(packets):raise ValueError('Trust arm coverage differs.')
 for arm,rows in packets.items():
  if read_jsonl(path.parent/(arm+'.jsonl'))!=rows or s['approaches'][arm]['metrics']!=evaluate(path.parent/'labels.jsonl',path.parent/(arm+'.jsonl'),inputs_path=path.parent/'inputs.jsonl'):raise ValueError('Trust predictions/scores differ.')
 for reader in readers:
  for a,b in zip(packets[reader+'__unguarded'],packets[reader+'__guarded']):
   if a['status']!=b['status'] or a['readings']!=b['readings'] or a['raw_readings']!=b['raw_readings'] or any('domain' in r['probabilities'] for r in b['readings']):raise ValueError('Guard changed meanings or fabricated probabilities.')
 for policy in POLICIES:
  name='reference-policy-'+policy+'.jsonl'
  if read_jsonl(path.parent/name)!=diagnostic(records,ann,policy=='guarded') or s['reference_policy_diagnostic'][policy]['metrics']!=evaluate(path.parent/'labels.jsonl',path.parent/name,inputs_path=path.parent/'inputs.jsonl'):raise ValueError('Trust diagnostic differs.')
 if s['report_metrics']!=report_metrics(texts,responses,ann,readers) or s['attribution']!=attribution(texts,responses,ann,keymap,packets) or s['changes']!=matched_changes(packets,keymap,readers):raise ValueError('Trust metrics/changes differ.')
 if s['attempted_predictions']!=len(responses) or s['failed_predictions']!=sum(r['status']!='ok' for r in responses) or s['unattempted_predictions']!=len(expected_pairs)-len(responses) or s['status']!=('completed' if len(responses)==len(expected_pairs) and not s['failed_predictions'] else 'completed_with_errors'):raise ValueError('Trust failure counts differ.')
 return s,{a:{r['id']:r for r in rows} for a,rows in packets.items()},texts,read_jsonl(path.parent/'requests.jsonl') if hosted else [],responses
