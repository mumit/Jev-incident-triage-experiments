"""Fresh conflict pairs and repeated fixed questions; no changes to completed trials."""
import copy
from datetime import datetime,timedelta,timezone
import json
from pathlib import Path

from triage_bench.dataset import ROOT,read_jsonl,stamp,write_jsonl
from triage_bench.policy import VERSION as POLICY_VERSION
from .question_trial import ARMS,DECISION,body,label,prepare as prepare_questions,run as run_questions,validate as validate_questions,verify as verify_questions
from .hosted import encoded
from .transforms import sha

DIRECTORY=ROOT/'data/experiment-3-conflict-draft'
REPEATS=3
SPECS=[
 ('cabinet bus crosscheck','power',False,'outage',
  'An independent calibrated DC meter reads 0 V and reports failed equipment supply.',
  'A second independent calibrated DC meter reads 48 V and reports nominal equipment supply.',
  'the same equipment bus, in volts, at the same load and operating conditions'),
 ('load panel sample order','power',True,'outage',
  'An independent load-panel DC sensor reads 0 V and reports failed equipment supply.',
  'A second independent load-panel DC sensor reads 48 V and reports nominal equipment supply.',
  'the same load-panel output, in volts, at the same load and operating conditions'),
 ('optical receive crosscheck','transport',False,'degraded',
  'An independent optical receiver diagnostic reads -42 dBm and reports loss of receive signal.',
  'A second independent optical receiver diagnostic reads -12 dBm and reports nominal receive signal.',
  'the same optical receive port, in dBm, at the same transmitter state and operating conditions'),
 ('clock offset crosscheck','ran',False,'degraded',
  'An independent radio clock monitor reads 250 microseconds of offset and reports a synchronization malfunction.',
  'A second independent radio clock monitor reads 0 microseconds of offset and reports nominal synchronization.',
  'the same radio clock output, in microseconds, with the same timing reference and operating conditions'),
]


def build(directory=DIRECTORY):
    directory=Path(directory)
    if directory.exists():raise ValueError('Conflict draft already exists; choose a new version.')
    records=[];keys=[]
    for index,(family,owner,normal_first,status,bad,normal,quantity) in enumerate(SPECS):
        opaque=sha(('conflict-repeat-v1:'+family).encode())[:12];pair='NSC-'+opaque;prefix=opaque[:5]
        sites=[prefix+'-site0',prefix+'-site1'];asset=prefix+'-device';gateway=prefix+'-gateway';relay=prefix+'-relay'
        now=datetime(2026,8,18,9,tzinfo=timezone.utc)+timedelta(hours=index)
        impact={'status':status,'affected_sites':2,'affected_site_ids':sites,'basis':'Independent current end-to-end service probes'}
        texts=[normal,bad] if normal_first else [bad,normal];normal_index=0 if normal_first else 1
        observations=[{'asset_id':asset,'source':'Synthetic independent instrument '+str(i+1),
                       'detail':text+' Both instruments measure '+quantity+' at '+asset+'. Independent current service checks confirm '+status+'.',
                       'observed_at':stamp(now-timedelta(minutes=1)),'measured_at':stamp(now-timedelta(minutes=4)),'valid_for_minutes':15}
                      for i,text in enumerate(texts)]
        packet={'operator':'Northstar Telecom','decision_timestamp':stamp(now),
                'ticket':{'title':'Comparable instrument reports','description':'Inspect both measurements and the current affected-service checks.'},
                'service_impact':impact,'observations':observations,
                'topology':{'nodes':[*sites,gateway,relay,asset],'edges':[[s,gateway] for s in sites]+[[gateway,relay],[relay,asset]],
                            'edge_semantics':'depends_on','scope':'required_service_dependencies','coverage':'complete',
                            'note':'Declared required service paths. No protection, redundancy or causal inference.'},
                'change_record':{'status':'none_reported','detail':'No relevant change is reported.'}}
        a={'id':pair+'-a','policy_version':POLICY_VERSION,'input':packet};b=copy.deepcopy(a);b['id']=pair+'-b'
        b['input']['observations'][normal_index]['measured_at']=stamp(now-timedelta(minutes=83))
        for r,answers in [(a,label('noc',impact,True)),(b,label(owner,impact))]:
            records.append(r);keys.append({'id':r['id'],'split':'development','incident_family_id':family,'pair_id':pair,'pair_kind':'decision_change',
             'changed_path':f'input.observations[{normal_index}].measured_at','labels':answers,'accepted_answers':{f:[v] for f,v in answers.items()},
             'label_rationale':'Comparable current instrument reports conflict. Once the nominal report is stale, the current malfunction and supported path justify its domain diagnostic. These are draft teaching dispositions.',
             'review_status':'draft_not_specialist_reviewed'})
    directory.mkdir(parents=True);write_jsonl(directory/'development.inputs.jsonl',records);write_jsonl(directory/'development.labels.jsonl',keys)
    manifest={'version':'experiment-3-conflict-draft-1','operator':'Northstar Telecom','synthetic':True,'reference_status':'draft_not_specialist_reviewed',
              'evaluation_status':'development_only_no_held_out_set','records':8,'pairs':4,'families':4,
              'human_decision':{'date':'2026-10-02','scope':'Synthetic teaching decision; not network-specialist signoff','decision':DECISION},
              'telemetry_assumption':'15-minute validity and comparable-instrument conflict rule remain provisional. Instrument values and classifications are teaching examples, not validated network thresholds.',
              'sha256':{p.name:sha(p.read_bytes()) for p in sorted(directory.glob('*.jsonl'))}}
    (directory/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');validate(directory);return manifest


def validate(directory=DIRECTORY):
    manifest=validate_questions(directory)
    old=read_jsonl(ROOT/'data/experiment-3-question-draft/development.labels.jsonl')
    old_families={k['incident_family_id'] for k in old};old_ids={k['id'] for k in old}
    keys=read_jsonl(Path(directory)/'development.labels.jsonl')
    if any(k['incident_family_id'] in old_families or k['id'] in old_ids for k in keys):raise ValueError('Previous question cases reused.')
    if any(k['pair_kind']!='decision_change' for k in keys):raise ValueError('Expected conflict decision-changing pairs.')
    return manifest


def prepare(profile,directory=DIRECTORY):
    manifest=validate(directory);base,records,keys,requests=prepare_questions(profile,directory)
    plan={'schema':'experiment-3-conflict-repeat-1','kind':'jev_conflict_repetition','repetitions':REPEATS,
          'maximum_requests':len(requests)*REPEATS,'records_per_repetition':len(records),'pairs_per_repetition':manifest['pairs'],
          'reference_status':manifest['reference_status'],'network_specialist_review':'pending','question_protocol':base,
          'source_sha256':{'triage_bench/experiment3/conflict_trial.py':sha((ROOT/'triage_bench/experiment3/conflict_trial.py').read_bytes())},
          'execution':'Three planned repeats of fixed requests; serial alternating arm order in each repeat. No tuning, warmup or automatic retry.',
          'stop':'Stop later repetitions if any repetition is incomplete or has failed responses.',
          'interpretation':'Eight distinct packets and four correlated pairs; repeated responses are not independent incidents.'}
    planned=[{**r,'repetition':n} for n in range(1,REPEATS+1) for r in requests]
    return plan,planned


def aggregate(directory,plan,root=ROOT,data_directory=DIRECTORY):
    directory=Path(directory);keys=read_jsonl(Path(data_directory)/'development.labels.jsonl');by_id={k['id']:k for k in keys}
    runs=[];rows_by_repeat={}
    for n in range(1,REPEATS+1):
        path=directory/f'repetition-{n}'/'summary.json'
        if path.exists():
            summary,rows,_=verify_questions(path,root,data_directory);runs.append({'repetition':n,'summary':summary});rows_by_repeat[n]=rows
    approaches={}
    for arm in ARMS:
        cases=[]
        for identifier,key in by_id.items():
            outputs=[rows_by_repeat.get(n,{}).get(arm,{}).get(identifier) for n in range(1,REPEATS+1)]
            ok=[r for r in outputs if r and r['status']=='ok']
            correct=[bool(r and r['status']=='ok' and all(r['predictions'][f] in key['accepted_answers'][f] for f in key['labels'])) for r in outputs]
            cases.append({'id':identifier,'family':key['incident_family_id'],'correct_by_repetition':correct,
                          'predictions_by_repetition':[r['predictions'] if r and r['status']=='ok' else None for r in outputs],
                          'all_repetitions_correct':all(correct),'complete':len(ok)==REPEATS,
                          'identical_decisions':len(ok)==REPEATS and len({json.dumps(r['predictions'],sort_keys=True) for r in ok})==1})
        denom=len(keys)*REPEATS;good=sum(sum(c['correct_by_repetition']) for c in cases)
        pair_ids={k['pair_id'] for k in keys};pair_good=0
        for n in range(REPEATS):
            correct_by_id={c['id']:c['correct_by_repetition'][n] for c in cases}
            pair_good+=sum(all(correct_by_id[k['id']] for k in keys if k['pair_id']==pair) for pair in pair_ids)
        approaches[arm]={'fully_correct_responses':good,'planned_packet_responses':denom,'all_fields_accuracy':good/denom,
                         'pair_successes':pair_good,'planned_pairs':len(pair_ids)*REPEATS,'pair_all_fields_accuracy':pair_good/(len(pair_ids)*REPEATS),
                         'cases_with_identical_decisions':sum(c['identical_decisions'] for c in cases),'cases_complete':sum(c['complete'] for c in cases),
                         'cases_correct_in_every_repetition':sum(c['all_repetitions_correct'] for c in cases),'distinct_packets':len(keys),'cases':cases}
    attempted=sum(r['summary']['attempted_requests'] for r in runs);failed=sum(r['summary']['failed_requests'] for r in runs)
    return {**plan,'status':'completed' if attempted==plan['maximum_requests'] and not failed else 'completed_with_errors',
            'attempted_requests':attempted,'failed_requests':failed,'unattempted_requests':plan['maximum_requests']-attempted,'runs':runs,'approaches':approaches}


def run(output,profile,directory=DIRECTORY,progress=None):
    plan,requests=prepare(profile,directory);output=Path(output)
    from triage_bench.runner import clean_api_key
    if not clean_api_key(profile.get('api_key','')):raise ValueError('A server-side key is required.')
    if output.exists():raise ValueError('Repeated runs are immutable; choose a new directory.')
    output.mkdir(parents=True);write_jsonl(output/'planned_requests.jsonl',requests)
    plan['planned_requests_sha256']=sha((output/'planned_requests.jsonl').read_bytes())
    (output/'protocol.json').write_text(json.dumps(plan,indent=2)+'\n')
    for n in range(1,REPEATS+1):
        def report(done,total,arm,status):
            if progress:progress(n,done,total,arm,status)
        summary=run_questions(output/f'repetition-{n}',profile,directory,progress=report)
        if summary['status']!='completed':break
    result=aggregate(output,plan,data_directory=directory);(output/'summary.json').write_text(json.dumps(result,indent=2)+'\n');return result


def verify(path,root=ROOT,directory=DIRECTORY):
    path=Path(path);plan=json.loads((path.parent/'protocol.json').read_text());saved=json.loads(path.read_text());validate(directory)
    if plan['schema']!='experiment-3-conflict-repeat-1' or plan['repetitions']!=REPEATS:raise ValueError('Unexpected repeated protocol.')
    if any(sha((Path(root)/name).read_bytes())!=digest for name,digest in plan['source_sha256'].items()):raise ValueError('Repeated source differs.')
    requests=read_jsonl(path.parent/'planned_requests.jsonl')
    if sha((path.parent/'planned_requests.jsonl').read_bytes())!=plan['planned_requests_sha256']:raise ValueError('Repeated request fingerprint differs.')
    records=read_jsonl(Path(directory)/'development.inputs.jsonl');expected=[]
    for n in range(1,REPEATS+1):
        for index,r in enumerate(records):
            for arm in (list(ARMS) if index%2==0 else list(reversed(ARMS))):
                request=body(r,arm);expected.append({'id':r['id'],'variant':arm,'body':request,'request_sha256':sha(encoded(request)),
                                                   'state_sha256':sha(request['state'].encode()),'repetition':n})
    if requests!=expected or plan['maximum_requests']!=len(expected):raise ValueError('Repeated requests differ from fixed questions and inputs.')
    result=aggregate(path.parent,plan,root,directory)
    if result!=saved:raise ValueError('Repeated scores differ from recomputed evidence.')
    for item in result['runs']:
        summary=item['summary'];base=plan['question_protocol']
        if any(summary.get(k)!=v for k,v in base.items()):raise ValueError('Repeated child differs from planned protocol.')
    return result
