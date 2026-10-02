"""Record a new architecture comparison and separate report/policy diagnostics."""
import json,math
from pathlib import Path
from triage_bench.dataset import ROOT,read_jsonl,write_jsonl
from triage_bench.evaluate import evaluate
from triage_bench.runner import baseline as legacy_rules
from triage_bench.policy import OPTIONS
from .interpretation_data import DIRECTORY,validate
from .interpretation_model import ReportClassifier,report_inputs,rule_reading,apply_policy,pipeline_input,PARAMETERS
from .structured_ml import StructuredClassifier,SOURCES as FROZEN_SOURCES,PARAMETERS as PACKET_PARAMETERS
from .structured_features import input_bundle
from .structured_data import DIRECTORY as BRIDGE
from .transforms import sha

ARMS={'baseline':'Frozen packet candidate','packet':'Matched packet ML','reading':'Report ML → policy','reading_rules':'Report rules → policy'}
SOURCES=FROZEN_SOURCES+['triage_bench/experiment3/'+n for n in ['selection.py','interpretation_data.py','interpretation_model.py','interpretation_trial.py']]


def matched_changes(rows,keys,control='packet'):
    out={}
    for arm in ARMS:
        changes={'packets_fixed':[],'packets_lost':[],'newly_wrong_fields':{f:[] for f in OPTIONS}}
        for identifier,key in keys.items():
            accepted=key['accepted_answers'];before=rows[control][identifier]['predictions'];after=rows[arm][identifier]['predictions']
            b=all(before[f] in accepted[f] for f in OPTIONS);a=all(after[f] in accepted[f] for f in OPTIONS)
            if a and not b:changes['packets_fixed'].append(identifier)
            if b and not a:changes['packets_lost'].append(identifier)
            for f in OPTIONS:
                if before[f] in accepted[f] and after[f] not in accepted[f]:changes['newly_wrong_fields'][f].append(identifier)
        out[arm]=changes
    return out


def report_metrics(rows,annotations,keys):
    target={(a['id'],a['observation_index']):a for a in annotations};result={}
    for arm in ['reading','reading_rules']:
        fields={f:{'correct':0,'reports':len(annotations)} for f in ['domain','reading','both']};attribution={k:[] for k in ['readings_correct_triage_correct','readings_correct_triage_wrong','readings_wrong_triage_correct','readings_wrong_triage_wrong']}
        for identifier,row in rows[arm].items():
            all_correct=True
            for r in row['readings']:
                t=target[identifier,r['observation_index']];d=r['domain']==t['domain'];s=r['reading']==t['reading'];all_correct &= d and s
                fields['domain']['correct']+=int(d);fields['reading']['correct']+=int(s);fields['both']['correct']+=int(d and s)
            triage=all(row['predictions'][f] in keys[identifier]['accepted_answers'][f] for f in OPTIONS)
            attribution['readings_'+('correct' if all_correct else 'wrong')+'_triage_'+('correct' if triage else 'wrong')].append(identifier)
        result[arm]={'fields':fields,'attribution':attribution}
    return result


def inputs(record,arm):return input_bundle(record,'combined') if arm in {'baseline','packet'} else pipeline_input(record)


def run(output,directory=DIRECTORY):
    directory=Path(directory);output=Path(output);validate(directory)
    if output.exists():raise ValueError('Interpretation runs are immutable.')
    output.mkdir(parents=True);records=read_jsonl(directory/'development.inputs.jsonl');keys=read_jsonl(directory/'development.labels.jsonl')
    plan={'schema':'experiment-3-interpretation-1','arms':ARMS,'split':'development','reference_status':'draft_not_specialist_reviewed','jev_status':'not_run',
          'data_sha256':json.loads((directory/'manifest.json').read_text())['sha256'],'bridge_data_sha256':json.loads((BRIDGE/'manifest.json').read_text())['sha256'],
          'source_sha256':{n:sha((ROOT/n).read_bytes()) for n in SOURCES},'report_parameters':PARAMETERS,'packet_parameters':PACKET_PARAMETERS,
          'training_packets':186,'training_reports':210,'development_packets':108,'development_reports':124,
          'primary_comparison':'Matched packet ML versus report interpretations feeding fixed policy. Same packets; report pipeline adds authored observation supervision and explicit asset grouping. This is an architecture/supervision comparison, not a feature-only ablation.',
          'diagnostic':'Reference readings feed policy only after model predictions. This checks policy against draft references; it is not a model score or attainable accuracy claim.',
          'execution':'One fit per model; train-only vocabularies. Report rules and policy frozen before measuring. No development tuning or hosted calls.'}
    (output/'protocol.json').write_text(json.dumps(plan,indent=2)+'\n')
    write_jsonl(output/'inputs.jsonl',records);write_jsonl(output/'labels.jsonl',keys)
    summary={**plan,'approaches':{}};rows={}
    for arm,data in [('baseline',BRIDGE),('packet',directory)]:
        model=StructuredClassifier('combined',data);pred=[model.predict(r) for r in records];write_jsonl(output/(arm+'.jsonl'),pred);rows[arm]={r['id']:r for r in pred}
        summary['approaches'][arm]={'training':model.metadata,'metrics':evaluate(output/'labels.jsonl',output/(arm+'.jsonl'),inputs_path=output/'inputs.jsonl')}
        write_jsonl(output/(arm+'.features.jsonl'),[{'id':r['id'],'vector':model.vector(r)} for r in records])
        write_jsonl(output/(arm+'.explanations.jsonl'),[{'id':r['id'],'fields':{f:model.explain(r,f) for f in OPTIONS}} for r in records])
    reader=ReportClassifier(directory)
    for arm in ['reading','reading_rules']:
        pred=[];inspections=[]
        for record in records:
            readings=reader.predict(record) if arm=='reading' else [rule_reading(r['text'],r['observation_index']) for r in report_inputs(record)]
            result=apply_policy(record,readings);pred.append({'id':record['id'],'status':'ok',**result,'readings':readings,'input_sha256':sha(json.dumps(inputs(record,arm),sort_keys=True).encode())})
            if arm=='reading':inspections.append({'id':record['id'],'reports':[{'observation_index':r['observation_index'],**reader.inspect(r['text'])} for r in report_inputs(record)]})
        write_jsonl(output/(arm+'.jsonl'),pred);rows[arm]={r['id']:r for r in pred}
        summary['approaches'][arm]={'training':reader.metadata if arm=='reading' else {'method':'Explicit report regexes; no fit, no probabilities.'},'metrics':evaluate(output/'labels.jsonl',output/(arm+'.jsonl'),inputs_path=output/'inputs.jsonl')}
        if arm=='reading':write_jsonl(output/'reading.inspections.jsonl',inspections)
    write_jsonl(output/'rules.jsonl',[{'id':r['id'],'status':'ok','predictions':legacy_rules(r['input'])} for r in records])
    summary['approaches']['rules']={'metrics':evaluate(output/'labels.jsonl',output/'rules.jsonl',inputs_path=output/'inputs.jsonl')}
    # Evaluation-only annotations are read after actual pipeline predictions.
    annotations=read_jsonl(directory/'development.observations.jsonl');write_jsonl(output/'observation-references.jsonl',annotations);by_id={}
    for a in annotations:by_id.setdefault(a['id'],[]).append(a)
    diagnostic=[{'id':r['id'],'status':'ok',**apply_policy(r,by_id[r['id']])} for r in records];write_jsonl(output/'reference-policy-diagnostic.jsonl',diagnostic)
    summary['reference_policy_diagnostic']={'label':'Evaluation diagnostic using draft reference readings; not model performance.','metrics':evaluate(output/'labels.jsonl',output/'reference-policy-diagnostic.jsonl',inputs_path=output/'inputs.jsonl')}
    summary['report_metrics']=report_metrics(rows,annotations,{k['id']:k for k in keys});summary['changes']=matched_changes(rows,{k['id']:k for k in keys})
    summary['evidence_sha256']={p.name:sha(p.read_bytes()) for p in sorted(output.glob('*.jsonl'))};(output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');return summary


def verify(path,root=ROOT,directory=DIRECTORY):
    path=Path(path);root=Path(root);directory=Path(directory);validate(directory)
    saved=json.loads(path.read_text());plan=json.loads((path.parent/'protocol.json').read_text())
    if saved['schema']!='experiment-3-interpretation-1' or any(saved.get(k)!=v for k,v in plan.items()):raise ValueError('Interpretation plan differs.')
    if saved['data_sha256']!=json.loads((directory/'manifest.json').read_text())['sha256'] or saved['bridge_data_sha256']!=json.loads((BRIDGE/'manifest.json').read_text())['sha256']:raise ValueError('Interpretation data differs.')
    if saved['report_parameters']!=PARAMETERS or saved['packet_parameters']!=PACKET_PARAMETERS or any(sha((root/n).read_bytes())!=d for n,d in saved['source_sha256'].items()):raise ValueError('Recorded interpretation source or settings differ.')
    expected={'inputs.jsonl','labels.jsonl','observation-references.jsonl','reference-policy-diagnostic.jsonl','reading.inspections.jsonl','rules.jsonl'}|{a+'.jsonl' for a in ARMS}|{a+s for a in ['baseline','packet'] for s in ['.features.jsonl','.explanations.jsonl']}
    if set(saved['evidence_sha256'])!=expected:raise ValueError('Interpretation evidence files differ.')
    for name,digest in saved['evidence_sha256'].items():
        if Path(name).name!=name or sha((path.parent/name).read_bytes())!=digest:raise ValueError('Interpretation evidence differs.')
    for name,source in [('inputs.jsonl','development.inputs.jsonl'),('labels.jsonl','development.labels.jsonl'),('observation-references.jsonl','development.observations.jsonl')]:
        if sha((path.parent/name).read_bytes())!=saved['data_sha256'][source]:raise ValueError('Recorded evaluation data differs.')
    if set(saved['approaches'])!={*ARMS,'rules'}:raise ValueError('Interpretation approaches differ.')
    records={r['id']:r for r in read_jsonl(path.parent/'inputs.jsonl')};keys={k['id']:k for k in read_jsonl(path.parent/'labels.jsonl')};rows={}
    for arm,result in saved['approaches'].items():
        if evaluate(path.parent/'labels.jsonl',path.parent/(arm+'.jsonl'),inputs_path=path.parent/'inputs.jsonl')!=result['metrics']:raise ValueError('Interpretation score differs.')
        rows[arm]={r['id']:r for r in read_jsonl(path.parent/(arm+'.jsonl'))}
        if set(rows[arm])!=set(records):raise ValueError('Incomplete interpretation predictions.')
        if arm=='rules':continue
        meta=result['training']
        if arm in {'baseline','packet'}:
            hashes=saved['bridge_data_sha256'] if arm=='baseline' else saved['data_sha256']
            if meta['parameters']!=PACKET_PARAMETERS or any(meta['training_'+k+'_sha256']!=hashes['train.'+k+'.jsonl'] for k in ['inputs','labels']):raise ValueError('Packet training differs.')
        elif arm=='reading':
            if meta['parameters']!=PARAMETERS or meta['training_inputs_sha256']!=saved['data_sha256']['train.inputs.jsonl'] or meta['training_annotations_sha256']!=saved['data_sha256']['train.observations.jsonl']:raise ValueError('Report training differs.')
        for identifier,row in rows[arm].items():
            if row['input_sha256']!=sha(json.dumps(inputs(records[identifier],arm),sort_keys=True).encode()):raise ValueError('Interpretation input differs.')
            if arm in {'reading','reading_rules'}:
                recomputed=apply_policy(records[identifier],row['readings'])
                if recomputed['predictions']!=row['predictions'] or recomputed['trace']!=row['trace']:raise ValueError('Policy trace differs.')
    annotations=read_jsonl(path.parent/'observation-references.jsonl')
    if saved['report_metrics']!=report_metrics(rows,annotations,keys) or saved['changes']!=matched_changes(rows,keys):raise ValueError('Interpretation attribution differs.')
    by_id={}
    for a in annotations:by_id.setdefault(a['id'],[]).append(a)
    for row in read_jsonl(path.parent/'reference-policy-diagnostic.jsonl'):
        expected=apply_policy(records[row['id']],by_id[row['id']])
        if row['predictions']!=expected['predictions'] or row['trace']!=expected['trace']:raise ValueError('Reference-fed policy trace differs.')
    if evaluate(path.parent/'labels.jsonl',path.parent/'reference-policy-diagnostic.jsonl',inputs_path=path.parent/'inputs.jsonl')!=saved['reference_policy_diagnostic']['metrics']:raise ValueError('Reference-fed diagnostic differs.')
    for item in read_jsonl(path.parent/'reading.inspections.jsonl'):
        for report in item['reports']:
            for field,e in report['fields'].items():
                row=rows['reading'][item['id']]['readings'][report['observation_index']];p=row['probabilities'][field]
                margin=e['intercept_difference']+sum(v['contribution'] for v in e['top_contributions'])+e['remaining_contribution']
                if p!=e['probabilities'] or not math.isclose(margin,math.log(p[e['selected']]/p[e['compared_with']]),abs_tol=1e-8):raise ValueError('Report score margin differs.')
    return saved,rows
