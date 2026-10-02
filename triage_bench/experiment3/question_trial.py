"""Separate development trial of explicit evidence precedence; historical files stay frozen."""
import copy
from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path
import time
import urllib.error
import urllib.parse
import urllib.request

from triage_bench.dataset import ROOT, read_jsonl, stamp, write_jsonl
from triage_bench.evaluate import evaluate
from triage_bench.experiments import focused_questions
from triage_bench.policy import OPTIONS, VERSION as POLICY_VERSION, priority
from triage_bench.runner import NoRedirect, clean_api_key, normalize
from .data import changed_paths
from .hosted import encoded, redact
from .transforms import MODEL, request_body, dependency_facts, measurement_facts, sha

DIRECTORY = ROOT / 'data/experiment-3-question-draft'
ARMS = {'original': 'Original questions', 'precedence': 'Explicit evidence precedence'}
DECISION = 'Keep NOC until current evidence links the fault to the affected service.'
# New written families; no reference is selected from a provider response.
SPECS = [
    ('regional queue isolation', 'dependency', 'transport', 'degraded',
     'An independent packet test at {asset} locates persistent receive-queue drops. End-to-end service probes confirm degradation; radio and supply tests pass.'),
    ('timing register expiry', 'age', 'ran', 'degraded',
     'Radio timing diagnostics at {asset} show a failed clock-lock register during independently verified degradation. No other domain malfunction is observed.'),
    ('battery distribution inventory', 'missing_topology', 'power', 'outage',
     'An independent meter at {asset} reports zero voltage at its equipment DC distribution output. Current service probes confirm an outage; the supply fault must be related to those services.'),
    ('session registry timestamp', 'missing_time', 'core', 'degraded',
     'Shared mobile-core registration traces at {asset} show rejected registrations across independent access paths. Service checks confirm degradation; the trace measurement time is supplied separately.'),
    ('comparable bus samples', 'conflict', 'power', 'outage',
     'An independent calibrated meter at {asset} reports zero voltage on the same equipment bus and under the same operating conditions as the second meter. Service probes confirm an outage.'),
    ('spare rack inventory', 'irrelevant', 'transport', 'outage',
     'A hardware optical test at {asset} confirms a failed required-service interface. End-to-end service probes fail; supply and radio checks pass.'),
    ('partial branch evidence', 'partial_path', 'transport', 'degraded',
     'Independent transport instrumentation at {asset} records sustained forwarding failures. Current end-to-end service checks confirm degradation; no other domain fault is observed.'),
    ('receiver report transit', 'arrival', 'ran', 'degraded',
     'An independent radio receiver diagnostic at {asset} reports failed receive processing. Current service probes confirm degradation; the measurement time is independent of delivery time.'),
]


def candidate_questions():
    result = copy.deepcopy(focused_questions())
    common = ('Apply these evidence rules before assigning a domain. Join observations and both calculated fact blocks by observation_index. '
              'An observation supports a domain only if it reports that domain\'s malfunction, its measurement_facts freshness_status is current, '
              'and dependency_facts supplies at least one supporting path from a listed affected site to that observed asset. '
              'Use the declared valid_for_minutes window for this synthetic exercise. Report age does not replace measurement age. '
              'Stale or unknown freshness, a missing relationship, or an excluded relationship cannot justify domain assignment. '
              'A partial map can support a visible path but cannot prove absence. A path alone does not prove a fault or root cause. '
              'Two current independent measurements of the same quantity on the same asset under comparable conditions that disagree leave the domain unresolved. '
              'A stale report cannot contradict a current measurement. If no unique domain remains supported, retain noc, gather_evidence and insufficient_evidence=yes. '
              'Missing telemetry from other domains alone does not invalidate a current supported malfunction. '
              'Verified recovery, fully explained maintenance and relevant unexplained change scope retain their existing dispositions. ')
    result['initial_owner']['instructions'] = common + 'Select the first investigating team, not confirmed root cause. Apply currentness and incident relationship before the domain malfunction rule.'
    result['next_check']['instructions'] = common + 'Choose the supported domain diagnostic: ran => inspect_radio; transport => inspect_transport; power => inspect_power; core => inspect_core. Otherwise gather_evidence, except verify_change for relevant unexplained change scope or monitor for verified recovery/fully explained maintenance.'
    result['insufficient_evidence']['instructions'] = common + 'Choose yes when those rules leave no unique investigating domain. Choose no for a supported domain or the explicit monitor disposition. Unknown exact root cause alone does not require yes.'
    return result


def body(record, arm):
    if arm not in ARMS: raise ValueError('Unknown question arm.')
    result = request_body(record, 'combined')
    if arm == 'precedence': result['questions'] = candidate_questions()
    return result


def label(owner, impact, uncertain=False):
    return {'initial_owner': owner, 'priority': priority(impact),
            'next_check': 'gather_evidence' if owner == 'noc' else 'inspect_radio' if owner == 'ran' else 'inspect_' + owner,
            'insufficient_evidence': 'yes' if uncertain else 'no'}


def build(directory=DIRECTORY):
    directory = Path(directory)
    if directory.exists(): raise ValueError('Choose a new question-trial data directory.')
    records, keys = [], []
    for index, (family, intervention, owner, status, text) in enumerate(SPECS):
        opaque = sha(('question-trial-v1:' + family).encode())[:12]
        prefix = opaque[:5]; pair = 'NSQ-' + opaque
        sites = [prefix + '-s' + str(i) for i in range(2 if index % 2 else 3)]
        asset, bypass, tier, relay, spare = [prefix + '-' + suffix for suffix in ['x','z','d','r','u']]
        edges = [[site,tier] for site in sites] + [[tier,relay],[relay,asset],[spare,bypass]]
        nodes = sorted({*sites,asset,bypass,tier,relay,spare,prefix+'-archive'})
        now = datetime(2026,7,14,12,tzinfo=timezone.utc) + timedelta(hours=index)
        impact = {'status':status,'affected_sites':len(sites),'affected_site_ids':sites,'basis':'Independent current end-to-end service probes'}
        observation = {'asset_id':asset,'detail':text.format(asset=asset),'observed_at':stamp(now-timedelta(minutes=1)),
                       'measured_at':stamp(now-timedelta(minutes=4)),'valid_for_minutes':15,'source':'Synthetic independent diagnostic'}
        packet = {'operator':'Northstar Telecom','decision_timestamp':stamp(now),
                  'ticket':{'title':'Service diagnostic packet','description':'Review independent service checks and the supplied measurements.'},
                  'service_impact':impact,'observations':[observation],
                  'topology':{'nodes':nodes,'edges':edges,'edge_semantics':'depends_on','scope':'required_service_dependencies',
                              'coverage':'partial' if intervention=='partial_path' else 'complete',
                              'note':'Required directed service dependencies; no protection, capacity or root-cause inference.'},
                  'change_record':{'status':'none_reported','detail':'No relevant change is reported.'}}
        a={'id':pair+'-a','policy_version':POLICY_VERSION,'input':packet}; b=copy.deepcopy(a);b['id']=pair+'-b'
        answer_a=answer_b=label(owner,impact); path=''; rationale=''
        if intervention in {'dependency','partial_path'}:
            b['input']['topology']['edges']=[[u,bypass if v==asset else v] for u,v in edges]
            answer_b=label('noc',impact,True);path='input.topology.edges'
            rationale='A visible supported fault becomes excluded in a complete map or unsupported in a partial map. Retain NOC without an incident relationship.'
        elif intervention=='missing_topology':
            b['input']['topology']={};answer_b=label('noc',impact,True);path='input.topology'
            rationale='The fault is current, but missing inventory leaves its relationship to the affected service unknown. The user-selected teaching rule retains NOC.'
        elif intervention in {'age','missing_time'}:
            b['input']['observations'][0]['measured_at']=None if intervention=='missing_time' else stamp(now-timedelta(minutes=73))
            answer_b=label('noc',impact,True);path='input.observations[0].measured_at'
            rationale='The same fault report loses a current measurement basis. Report arrival does not establish freshness.'
        elif intervention=='conflict':
            second=copy.deepcopy(observation);second['detail']='A second independent calibrated meter at '+asset+' reports nominal voltage on the same equipment bus under the same operating conditions as the first meter.'
            a['input']['observations'].append(second);b['input']['observations'].append(copy.deepcopy(second))
            b['input']['observations'][1]['measured_at']=stamp(now-timedelta(minutes=73))
            answer_a=label('noc',impact,True);path='input.observations[1].measured_at'
            rationale='Comparable current measurements conflict. A stale nominal reading does not contradict the current zero-voltage reading; this conflict rule remains a draft assumption.'
        elif intervention=='irrelevant':
            b['input']['topology']['edges'].append([spare,prefix+'-archive']);path='input.topology.edges'
            rationale='An inventory edge outside the affected-service path leaves the supported fault and all decisions unchanged.'
        else:
            b['input']['observations'][0]['observed_at']=stamp(now-timedelta(minutes=2));path='input.observations[0].observed_at'
            rationale='Delivery time changes while the same measurement stays current and related; all decisions should remain stable.'
        records += [a,b]
        for record,answer in [(a,answer_a),(b,answer_b)]:
            keys.append({'id':record['id'],'split':'development','incident_family_id':family,'pair_id':pair,
                         'pair_kind':'invariance' if answer_a==answer_b else 'decision_change','changed_path':path,
                         'labels':answer,'accepted_answers':{f:[v] for f,v in answer.items()},'label_rationale':rationale,
                         'review_status':'draft_not_specialist_reviewed'})
    directory.mkdir(parents=True)
    write_jsonl(directory/'development.inputs.jsonl',records);write_jsonl(directory/'development.labels.jsonl',keys)
    manifest={'version':'experiment-3-question-draft-1','synthetic':True,'operator':'Northstar Telecom',
              'reference_status':'draft_not_specialist_reviewed','evaluation_status':'development_only_no_held_out_set',
              'human_decision':{'date':'2026-10-02','scope':'Synthetic teaching decision; not network-specialist signoff','decision':DECISION},
              'records':len(records),'pairs':len(keys)//2,'families':len(SPECS),
              'telemetry_assumption':'15-minute declared window and same-bus conflict disposition remain provisional.',
              'sha256':{p.name:sha(p.read_bytes()) for p in sorted(directory.glob('*.jsonl'))}}
    (directory/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');validate(directory)
    return manifest


def validate(directory=DIRECTORY):
    directory=Path(directory);manifest=json.loads((directory/'manifest.json').read_text())
    if manifest.get('reference_status')!='draft_not_specialist_reviewed' or manifest.get('human_decision',{}).get('decision')!=DECISION:raise ValueError('Trial decision or draft status differs.')
    if set(manifest['sha256'])!={'development.inputs.jsonl','development.labels.jsonl'}:raise ValueError('Unexpected manifest paths.')
    for name,digest in manifest['sha256'].items():
        if sha((directory/name).read_bytes())!=digest:raise ValueError('Question-trial checksum differs.')
    records=read_jsonl(directory/'development.inputs.jsonl');keys=read_jsonl(directory/'development.labels.jsonl');answers={k['id']:k for k in keys}
    if len(answers)!=len(keys) or len({r['id'] for r in records})!=len(records) or set(answers)!={r['id'] for r in records}:raise ValueError('Trial IDs differ or repeat.')
    old_families=set();old_ids=set()
    for path in (ROOT/'data/experiment-3-draft').glob('*.labels.jsonl'):
        for k in read_jsonl(path):old_families.add(k['incident_family_id']);old_ids.add(k['id'])
    pairs={}
    for r in records:
        k=answers[r['id']];p=r['input']
        if r['id'] in old_ids or k['incident_family_id'] in old_families:raise ValueError('Old development family reused.')
        if set(r)!={'id','policy_version','input'} or r['policy_version']!=POLICY_VERSION or p['operator']!='Northstar Telecom' or k['split']!='development' or k['review_status']!='draft_not_specialist_reviewed':raise ValueError('Invalid draft record.')
        impact=p['service_impact'];sites=impact['affected_site_ids'];count=impact['affected_sites']
        if isinstance(count,bool) or not isinstance(count,int) or count<=0 or count!=len(set(sites)) or len(sites)!=count or impact['status'] not in {'outage','degraded'}:raise ValueError('Invalid trial impact.')
        measurement_facts(p);dependency_facts(p)
        if k['labels']['priority']!=priority(impact):raise ValueError('Priority changed.')
        for f,options in OPTIONS.items():
            if k['labels'][f] not in options or k['accepted_answers'][f]!=[k['labels'][f]]:raise ValueError('Invalid trial choices.')
        original,changed=body(r,'original'),body(r,'precedence')
        if original['state']!=changed['state'] or original['questions']['priority']!=changed['questions']['priority']:raise ValueError('More than question precedence changed.')
        pairs.setdefault(k['pair_id'],[]).append((r,k))
    for pair in pairs.values():
        if len(pair)!=2:raise ValueError('Incomplete pair.')
        (a,ka),(b,kb)=pair
        if ka['incident_family_id']!=kb['incident_family_id'] or changed_paths(a['input'],b['input'])!=[ka['changed_path']] or ka['changed_path']!=kb['changed_path']:raise ValueError('Uncontrolled intervention.')
        kind='invariance' if ka['labels']==kb['labels'] else 'decision_change'
        if ka['pair_kind']!=kind or kb['pair_kind']!=kind:raise ValueError('Pair reference type differs.')
    if (len(records),len(pairs),len({k['incident_family_id'] for k in keys}))!=(manifest['records'],manifest['pairs'],manifest['families']):raise ValueError('Trial counts differ.')
    return manifest


def prepare(profile,directory=DIRECTORY):
    manifest=validate(directory);directory=Path(directory)
    if profile['model']!=MODEL:raise ValueError('Keep the Jev checkpoint fixed.')
    u=urllib.parse.urlparse(profile['endpoint'])
    if not u.hostname or u.username or u.password or u.query or u.fragment or (u.scheme!='https' and not(u.scheme=='http' and u.hostname in {'127.0.0.1','localhost','::1'})):raise ValueError('Unsafe provider endpoint.')
    capacity=profile['context_tokens']
    if isinstance(capacity,bool) or not isinstance(capacity,int) or not 512<=capacity<=1000000:raise ValueError('Invalid declared capacity.')
    records=read_jsonl(directory/'development.inputs.jsonl');keys=read_jsonl(directory/'development.labels.jsonl');requests=[]
    for index,r in enumerate(records):
        for arm in (list(ARMS) if index%2==0 else list(reversed(ARMS))):
            request=body(r,arm);wire=encoded(request)
            if len(wire)+512>capacity:raise ValueError('Context preflight failed.')
            requests.append({'id':r['id'],'variant':arm,'body':request,'request_sha256':sha(wire),'state_sha256':sha(request['state'].encode())})
    sources=['experiment3/question_trial.py','experiment3/transforms.py','experiment3/hosted.py','experiments.py','policy.py','runner.py','evaluate.py']
    protocol={'schema':'experiment-3-question-trial-1','kind':'jev_question_development','requested_model':MODEL,
              'endpoint':profile['endpoint'],'declared_context_tokens':capacity,'records':len(records),'maximum_requests':len(requests),
              'input_variant':'combined','reference_status':manifest['reference_status'],'network_specialist_review':'pending',
              'human_decision':manifest['human_decision'],'data_sha256':manifest['sha256'],
              'question_sha256':{a:sha(encoded(body(records[0],a)['questions'])) for a in ARMS},
              'source_sha256':{'triage_bench/'+name:sha((ROOT/'triage_bench'/name).read_bytes()) for name in sources},
              'execution':'Serial, alternating arm order by packet; no warmup or retries.',
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
    for arm in ARMS:summary['approaches'][arm]={'metrics':evaluate(output/'labels.jsonl',output/(arm+'.jsonl'),output/(arm+'.metrics.json'),output/'inputs.jsonl')}
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');return summary


def verify(path,root=ROOT,directory=DIRECTORY):
    path=Path(path);root=Path(root);manifest=validate(directory);summary=json.loads(path.read_text());protocol=json.loads((path.parent/'protocol.json').read_text())
    if any(summary.get(k)!=v for k,v in protocol.items()) or protocol['kind']!='jev_question_development' or protocol['data_sha256']!=manifest['sha256'] or protocol['human_decision']!=manifest['human_decision'] or set(summary['approaches'])!=set(ARMS):raise ValueError('Trial protocol differs.')
    if any(sha((root/name).read_bytes())!=digest for name,digest in protocol['source_sha256'].items()):raise ValueError('Trial source differs.')
    for saved,source in [('inputs.jsonl','development.inputs.jsonl'),('labels.jsonl','development.labels.jsonl')]:
        if sha((path.parent/saved).read_bytes())!=manifest['sha256'][source]:raise ValueError('Trial data differ.')
    requests=read_jsonl(path.parent/'requests.jsonl');records={r['id']:r for r in read_jsonl(path.parent/'inputs.jsonl')}
    if sha((path.parent/'requests.jsonl').read_bytes())!=protocol['requests_sha256'] or len(requests)!=len(records)*len(ARMS) or protocol['maximum_requests']!=len(requests) or protocol['records']!=len(records) or {(r['id'],r['variant']) for r in requests}!={(identifier,a) for identifier in records for a in ARMS}:raise ValueError('Trial request coverage differs.')
    request_map={}
    for req in requests:
        expected=body(records[req['id']],req['variant'])
        if req['body']!=expected or req['request_sha256']!=sha(encoded(expected)) or req['state_sha256']!=sha(expected['state'].encode()):raise ValueError('Trial request differs.')
        request_map[(req['id'],req['variant'])]=req
    rows={};attempted=failed=0
    for arm,result in summary['approaches'].items():
        output=path.parent/(arm+'.jsonl')
        if evaluate(path.parent/'labels.jsonl',output,inputs_path=path.parent/'inputs.jsonl')!=result['metrics']:raise ValueError('Trial metrics differ.')
        rows[arm]={r['id']:r for r in read_jsonl(output)}
        for identifier,row in rows[arm].items():
            req=request_map[(identifier,arm)]
            if any(row.get(k)!=req[k] for k in ['state_sha256','request_sha256']):raise ValueError('Trial response request differs.')
            attempted+=1;failed+=row['status']!='ok'
    if (attempted,failed,len(requests)-attempted)!=(summary['attempted_requests'],summary['failed_requests'],summary['unattempted_requests']):raise ValueError('Trial attempt counts differ.')
    if summary['status']!=('completed' if attempted==len(requests) and not failed else 'completed_with_errors'):raise ValueError('Trial status differs.')
    return summary,rows,request_map
