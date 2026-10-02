"""One-shot training wording study using the frozen combined feature recipe."""
import json
from pathlib import Path
import math
from triage_bench.dataset import ROOT,read_jsonl,write_jsonl
from triage_bench.evaluate import evaluate
from triage_bench.runner import baseline as rules
from triage_bench.policy import OPTIONS
from .wording_data import DIRECTORY,ARMS,validate
from .structured_ml import StructuredClassifier,PARAMETERS,SOURCES as FROZEN_SOURCES
from .structured_features import input_bundle
from .transforms import sha

SOURCES=FROZEN_SOURCES+['triage_bench/experiment3/wording_data.py','triage_bench/experiment3/wording_ml.py']


def changes(rows,keys,control):
    result={}
    for arm in ARMS:
        fixed=[];lost=[];new_fields={f:[] for f in OPTIONS}
        for identifier,key in keys.items():
            before=rows[control][identifier]['predictions'];after=rows[arm][identifier]['predictions'];accepted=key['accepted_answers']
            b=all(before[f] in accepted[f] for f in accepted);a=all(after[f] in accepted[f] for f in accepted)
            if a and not b:fixed.append(identifier)
            if b and not a:lost.append(identifier)
            for field in new_fields:
                if before[field] in accepted[field] and after[field] not in accepted[field]:new_fields[field].append(identifier)
        result[arm]={'packets_fixed':fixed,'packets_lost':lost,'newly_wrong_fields':new_fields}
    return result


def method_weights(model):
    head=model.heads['initial_owner'];names=model.space.names('combined');classes=list(head.classes_);out={}
    for word in ['tests','diagnostics','test','diagnostic']:
        name='observation/supported/current/word/'+word
        if name not in names:out[word]={'in_vocabulary':False};continue
        column=names.index(name)
        out[word]={'in_vocabulary':True,'noc_minus_domain':{d:float(head.coef_[classes.index('noc'),column]-head.coef_[classes.index(d),column]) for d in ['transport','ran','power','core']}}
    return out


def run(output,directory=DIRECTORY):
    directory=Path(directory);output=Path(output);validate(directory)
    if output.exists():raise ValueError('Wording runs are immutable; choose a new directory.')
    output.mkdir(parents=True);records=read_jsonl(directory/'baseline/development.inputs.jsonl');keys=read_jsonl(directory/'baseline/development.labels.jsonl')
    for name,rows in [('inputs',records),('labels',keys)]:write_jsonl(output/(name+'.jsonl'),rows)
    plan={'schema':'experiment-3-wording-ml-1','reference_status':'draft_not_specialist_reviewed','split':'development','jev_status':'not_run',
          'arms':ARMS,'feature_arm':'combined','parameters':PARAMETERS,'training_records_per_arm':96,'development_records':80,
          'data_sha256':json.loads((directory/'manifest.json').read_text())['sha256'],'source_sha256':{name:sha((ROOT/name).read_bytes()) for name in SOURCES},
          'execution':'One fit per arm; original wording bridge and matched coupled versus counterbalanced nouns. Training-only vocabularies refit per arm. Features and settings frozen. No development tuning or hosted calls.',
          'primary_comparison':'balanced versus coupled; baseline is the unchanged original training bridge',
          'next_decision':'Inspect matched packet and field regressions, synonym invariance and freshness/dependency controls. Do not revise this pack after observing scores.'}
    (output/'protocol.json').write_text(json.dumps(plan,indent=2)+'\n');summary={**plan,'approaches':{}};all_rows={}
    for arm in ARMS:
        model=StructuredClassifier('combined',directory/arm);rows=[model.predict(r) for r in records];write_jsonl(output/(arm+'.jsonl'),rows);all_rows[arm]={r['id']:r for r in rows}
        write_jsonl(output/(arm+'.weights.jsonl'),[{'word':w,**v} for w,v in method_weights(model).items()])
        summary['approaches'][arm]={'training':model.metadata,'method_weights':method_weights(model),'metrics':evaluate(output/'labels.jsonl',output/(arm+'.jsonl'),inputs_path=output/'inputs.jsonl')}
        write_jsonl(output/(arm+'.features.jsonl'),[{'id':r['id'],'vector':model.vector(r)} for r in records])
        write_jsonl(output/(arm+'.explanations.jsonl'),[{'id':r['id'],'fields':{f:model.explain(r,f) for f in OPTIONS}} for r in records])
    write_jsonl(output/'rules.jsonl',[{'id':r['id'],'status':'ok','predictions':rules(r['input'])} for r in records])
    summary['approaches']['rules']={'metrics':evaluate(output/'labels.jsonl',output/'rules.jsonl',inputs_path=output/'inputs.jsonl')}
    summary['changes']={c:changes(all_rows,{k['id']:k for k in keys},c) for c in ['baseline','coupled']}
    summary['evidence_sha256']={p.name:sha(p.read_bytes()) for p in sorted(output.glob('*.jsonl'))}
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');return summary


def verify(path,root=ROOT,directory=DIRECTORY):
    path=Path(path);directory=Path(directory);root=Path(root);validate(directory)
    saved=json.loads(path.read_text());plan=json.loads((path.parent/'protocol.json').read_text())
    if saved['schema']!='experiment-3-wording-ml-1' or any(saved.get(k)!=v for k,v in plan.items()):raise ValueError('Wording protocol differs.')
    if saved['parameters']!=PARAMETERS or saved['data_sha256']!=json.loads((directory/'manifest.json').read_text())['sha256']:raise ValueError('Wording recipe or data differ.')
    if any(sha((root/name).read_bytes())!=digest for name,digest in saved['source_sha256'].items()):raise ValueError('Recorded wording source differs.')
    expected={'inputs.jsonl','labels.jsonl','rules.jsonl'}|{a+s for a in ARMS for s in ['.jsonl','.features.jsonl','.explanations.jsonl','.weights.jsonl']}
    if set(saved['evidence_sha256'])!=expected:raise ValueError('Missing wording evidence.')
    for name,digest in saved['evidence_sha256'].items():
        if Path(name).name!=name or sha((path.parent/name).read_bytes())!=digest:raise ValueError('Wording evidence differs.')
    for name,kind in [('inputs','inputs'),('labels','labels')]:
        if sha((path.parent/(name+'.jsonl')).read_bytes())!=saved['data_sha256']['baseline/development.'+kind+'.jsonl']:raise ValueError('Development evidence differs.')
    if set(saved['approaches'])!={*ARMS,'rules'}:raise ValueError('Unexpected wording arms.')
    records={r['id']:r for r in read_jsonl(path.parent/'inputs.jsonl')};rows={};explanations={}
    for arm,result in saved['approaches'].items():
        if evaluate(path.parent/'labels.jsonl',path.parent/(arm+'.jsonl'),inputs_path=path.parent/'inputs.jsonl')!=result['metrics']:raise ValueError('Wording scores differ.')
        rows[arm]={r['id']:r for r in read_jsonl(path.parent/(arm+'.jsonl'))}
        if set(rows[arm])!=set(records):raise ValueError('Incomplete wording prediction coverage.')
        if arm=='rules':continue
        weights={r['word']:{k:v for k,v in r.items() if k!='word'} for r in read_jsonl(path.parent/(arm+'.weights.jsonl'))}
        if weights!=result['method_weights']:raise ValueError('Method weights differ.')
        meta=result['training']
        if meta['parameters']!=PARAMETERS or any(meta['training_'+kind+'_sha256']!=saved['data_sha256'][arm+'/train.'+kind+'.jsonl'] for kind in ['inputs','labels']):raise ValueError('Training metadata differs.')
        if any(r['input_sha256']!=sha(json.dumps(input_bundle(records[r['id']],'combined'),sort_keys=True).encode()) for r in rows[arm].values()):raise ValueError('Evaluation features differ.')
        explanations[arm]={r['id']:r['fields'] for r in read_jsonl(path.parent/(arm+'.explanations.jsonl'))}
        if set(explanations[arm])!=set(records):raise ValueError('Incomplete wording explanations.')
        for identifier,fields in explanations[arm].items():
            for field,e in fields.items():
                p=rows[arm][identifier]['probabilities'][field]
                margin=e['intercept_difference']+sum(v['contribution'] for v in e['top_contributions'])+e['remaining_contribution']
                if e['probabilities']!=p or not math.isclose(margin,math.log(p[e['selected']]/p[e['compared_with']]),abs_tol=1e-8):raise ValueError('Fitted score margin differs.')
    keys={k['id']:k for k in read_jsonl(path.parent/'labels.jsonl')}
    if saved['changes']!={c:changes(rows,keys,c) for c in ['baseline','coupled']}:raise ValueError('Matched wording changes differ.')
    return saved,rows,explanations
