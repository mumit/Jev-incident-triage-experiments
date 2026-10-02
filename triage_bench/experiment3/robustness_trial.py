"""Three planned repetitions on further controls; no changes to frozen selection."""
import json
from pathlib import Path
from triage_bench.dataset import ROOT, read_jsonl, write_jsonl
from .robustness_data import DIRECTORY, build, validate
from .robustness_inference import ARMS, prepare as prepare_inference, run as run_inference, verify as verify_inference
from .selection import body
from .hosted import encoded
from .transforms import sha
REPEATS = 3


def prepare(profile,directory=DIRECTORY):
    manifest=validate(directory);base,records,keys,requests=prepare_inference(profile,directory)
    plan={'schema':'experiment-3-robustness-repeat-1','kind':'jev_selection_robustness','repetitions':REPEATS,
          'maximum_requests':len(requests)*REPEATS,'records_per_repetition':len(records),'pairs_per_repetition':manifest['pairs'],
          'reference_status':manifest['reference_status'],'network_specialist_review':'pending','input_protocol':base,
          'source_sha256':{'triage_bench/experiment3/robustness_trial.py':sha((ROOT/'triage_bench/experiment3/robustness_trial.py').read_bytes())},
          'execution':'Three planned repeats of fixed requests; serial rotating arm order in each repeat. No tuning, warmup or automatic retry.',
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
            summary,rows,_=verify_inference(path,root,data_directory);runs.append({'repetition':n,'summary':summary});rows_by_repeat[n]=rows
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
        summary=run_inference(output/f'repetition-{n}',profile,directory,progress=report)
        if summary['status']!='completed':break
    result=aggregate(output,plan,data_directory=directory);(output/'summary.json').write_text(json.dumps(result,indent=2)+'\n');return result


def verify(path,root=ROOT,directory=DIRECTORY):
    path=Path(path);plan=json.loads((path.parent/'protocol.json').read_text());saved=json.loads(path.read_text());validate(directory)
    if plan['schema']!='experiment-3-robustness-repeat-1' or plan['repetitions']!=REPEATS:raise ValueError('Unexpected repeated protocol.')
    if any(sha((Path(root)/name).read_bytes())!=digest for name,digest in plan['source_sha256'].items()):raise ValueError('Repeated source differs.')
    requests=read_jsonl(path.parent/'planned_requests.jsonl')
    if sha((path.parent/'planned_requests.jsonl').read_bytes())!=plan['planned_requests_sha256']:raise ValueError('Repeated request fingerprint differs.')
    records=read_jsonl(Path(directory)/'development.inputs.jsonl');expected=[]
    for n in range(1,REPEATS+1):
        for index,r in enumerate(records):
            for arm in (list(ARMS)[index % len(ARMS):] + list(ARMS)[:index % len(ARMS)]):
                request=body(r,arm);expected.append({'id':r['id'],'variant':arm,'body':request,'request_sha256':sha(encoded(request)),
                                                   'state_sha256':sha(request['state'].encode()),'repetition':n})
    if requests!=expected or plan['maximum_requests']!=len(expected):raise ValueError('Repeated requests differ from fixed questions and inputs.')
    result=aggregate(path.parent,plan,root,directory)
    if result!=saved:raise ValueError('Repeated scores differ from recomputed evidence.')
    for item in result['runs']:
        summary=item['summary'];base=plan['input_protocol']
        if any(summary.get(k)!=v for k,v in base.items()):raise ValueError('Repeated child differs from planned protocol.')
    return result
