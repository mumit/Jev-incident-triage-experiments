"""Record matched report-wording fits without changing the frozen interpreter or policy."""
import json,math
from pathlib import Path
from triage_bench.dataset import ROOT,read_jsonl,write_jsonl
from triage_bench.evaluate import evaluate
from triage_bench.policy import OPTIONS
from triage_bench.runner import baseline
from .report_language_data import DIRECTORY,validate
from .interpretation_model import ReportClassifier,PARAMETERS,pipeline_input,apply_policy,report_inputs,rule_reading
from .interpretation_trial import SOURCES as PREVIOUS_SOURCES,report_metrics
from .structured_data import DIRECTORY as BRIDGE
from .structured_ml import StructuredClassifier
from .transforms import sha

ARMS={'narrow':'Report ML · original phrases','broad':'Report ML · broader phrases','bridge':'ML · frozen packet','report_rules':'Report rules → policy','rules':'Rules'}
SOURCES=PREVIOUS_SOURCES+['triage_bench/experiment3/report_language_data.py','triage_bench/experiment3/report_language_trial.py']


def changes(rows,keys,control='narrow'):
    result={}
    for arm in rows:
        c={'packets_fixed':[],'packets_lost':[],'newly_wrong_fields':{f:[] for f in OPTIONS}}
        for identifier,k in keys.items():
            accepted=k['accepted_answers'];b=rows[control].get(identifier,{}).get('predictions',{});a=rows[arm].get(identifier,{}).get('predictions',{})
            before=all(b.get(f) in accepted[f] for f in OPTIONS);after=all(a.get(f) in accepted[f] for f in OPTIONS)
            if after and not before:c['packets_fixed'].append(identifier)
            if before and not after:c['packets_lost'].append(identifier)
            for f in OPTIONS:
                if b.get(f) in accepted[f] and a.get(f) not in accepted[f]:c['newly_wrong_fields'][f].append(identifier)
        result[arm]=c
    return result


def reports_score(rows,annotations,keys):
    result={}
    for a in ['narrow','broad','report_rules']:
        mapped={'reading':rows[a],'reading_rules':rows[a]}
        result[a]=report_metrics(mapped,annotations,keys)['reading']
    return result


def controls(rows,keys):
    result={}
    for a,pred in rows.items():
        result[a]={}
        for identifier,k in keys.items():
            c=result[a].setdefault(k['control'],{'correct':0,'packets':0});c['packets']+=1
            c['correct']+=all(pred[identifier]['predictions'][f] in k['accepted_answers'][f] for f in OPTIONS)
    return result


def method_weights(reader):
    h=reader.heads['reading'];classes=list(h.classes_);difference=h.coef_[classes.index('normal')]-h.coef_[classes.index('fault')]
    return {w:float(difference[reader.words.vocabulary_[w]]) if w in reader.words.vocabulary_ else None for w in ['service','probes','service probes','failing','suspected','unconfirmed']}


def run(output,directory=DIRECTORY):
    directory=Path(directory);validate(directory);output=Path(output)
    if output.exists():raise ValueError('Report-language runs are immutable.')
    manifest=json.loads((directory/'manifest.json').read_text());records=read_jsonl(directory/'narrow/development.inputs.jsonl');keys=read_jsonl(directory/'narrow/development.labels.jsonl')
    plan={'schema':'report-language-local-1','data_sha256':manifest['sha256'],'bridge_data_sha256':json.loads((BRIDGE/'manifest.json').read_text())['sha256'],
          'source_sha256':{n:sha((ROOT/n).read_bytes()) for n in SOURCES},'parameters':PARAMETERS,'arms':ARMS,'reference_status':'draft_not_specialist_reviewed','jev_status':'not_run',
          'training_packets_per_report_arm':186,'training_reports_per_arm':210,'development_packets':len(records),'development_reports':manifest['observation_counts']['development'],
          'primary_comparison':'Broader versus original training phrases: same counts, annotations, non-text inputs, interpreter and policy. Only training report wording changes. Each arm fits its own train-only vocabulary.',
          'execution':'One fit per arm; no development tuning. Packet bridge and report regexes remain frozen. Clause controls use separately written provisional references.'}
    output.mkdir(parents=True);(output/'protocol.json').write_text(json.dumps(plan,indent=2)+'\n')
    for name,data in [('inputs',records),('labels',keys),('observation-references',read_jsonl(directory/'narrow/development.observations.jsonl'))]:write_jsonl(output/(name+'.jsonl'),data)
    rows={};summary={**plan,'approaches':{}}
    for arm in ['narrow','broad']:
        reader=ReportClassifier(directory/arm);pred=[];inspection=[]
        for r in records:
            reading=reader.predict(r);pred.append({'id':r['id'],'status':'ok','readings':reading,**apply_policy(r,reading),'input_sha256':sha(json.dumps(pipeline_input(r),sort_keys=True).encode())})
            inspection.append({'id':r['id'],'reports':[{'observation_index':o['observation_index'],**reader.inspect(o['text'])} for o in report_inputs(r)]})
        write_jsonl(output/(arm+'.weights.jsonl'),[{'feature':w,'normal_minus_fault':v} for w,v in method_weights(reader).items()]);write_jsonl(output/(arm+'.jsonl'),pred);write_jsonl(output/(arm+'.inspections.jsonl'),inspection);rows[arm]={r['id']:r for r in pred}
        summary['approaches'][arm]={'training':reader.metadata,'method_weights_normal_minus_fault':method_weights(reader),'metrics':evaluate(output/'labels.jsonl',output/(arm+'.jsonl'),inputs_path=output/'inputs.jsonl')}
    bridge=StructuredClassifier('combined',BRIDGE);pred=[bridge.predict(r) for r in records];rows['bridge']={r['id']:r for r in pred};write_jsonl(output/'bridge.jsonl',pred)
    write_jsonl(output/'bridge.features.jsonl',[{'id':r['id'],'vector':bridge.vector(r)} for r in records]);write_jsonl(output/'bridge.explanations.jsonl',[{'id':r['id'],'fields':{f:bridge.explain(r,f) for f in OPTIONS}} for r in records])
    summary['approaches']['bridge']={'training':bridge.metadata,'metrics':evaluate(output/'labels.jsonl',output/'bridge.jsonl',inputs_path=output/'inputs.jsonl')}
    pred=[]
    for r in records:
        reading=[rule_reading(o['text'],o['observation_index']) for o in report_inputs(r)];pred.append({'id':r['id'],'status':'ok','readings':reading,**apply_policy(r,reading)})
    for arm,prediction in [('report_rules',pred),('rules',[{'id':r['id'],'status':'ok','predictions':baseline(r['input'])} for r in records])]:
        write_jsonl(output/(arm+'.jsonl'),prediction);rows[arm]={r['id']:r for r in prediction};summary['approaches'][arm]={'metrics':evaluate(output/'labels.jsonl',output/(arm+'.jsonl'),inputs_path=output/'inputs.jsonl')}
    annotations=read_jsonl(output/'observation-references.jsonl');keymap={k['id']:k for k in keys};by_id={}
    for a in annotations:by_id.setdefault(a['id'],[]).append(a)
    write_jsonl(output/'reference-policy-diagnostic.jsonl',[{'id':r['id'],'status':'ok',**apply_policy(r,by_id[r['id']])} for r in records])
    summary['reference_policy_diagnostic']={'label':'Evaluation-only reference readings fed to policy, not model performance.','metrics':evaluate(output/'labels.jsonl',output/'reference-policy-diagnostic.jsonl',inputs_path=output/'inputs.jsonl')}
    summary.update(report_metrics=reports_score(rows,annotations,keymap),changes=changes(rows,keymap),comparison_to_bridge=changes(rows,keymap,'bridge'),controls=controls(rows,keymap))
    summary['evidence_sha256']={p.name:sha(p.read_bytes()) for p in sorted(output.glob('*.jsonl'))};(output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');return summary


def verify(path,directory=DIRECTORY,root=ROOT):
    path=Path(path);directory=Path(directory);root=Path(root);validate(directory);s=json.loads(path.read_text());plan=json.loads((path.parent/'protocol.json').read_text());m=json.loads((directory/'manifest.json').read_text())
    if s['schema']!='report-language-local-1' or any(s.get(k)!=v for k,v in plan.items()) or s['parameters']!=PARAMETERS or s['data_sha256']!=m['sha256']:raise ValueError('Report-language protocol differs.')
    if any(sha((root/n).read_bytes())!=h for n,h in s['source_sha256'].items()):raise ValueError('Frozen report-language sources differ.')
    if s['bridge_data_sha256']!=json.loads((BRIDGE/'manifest.json').read_text())['sha256']:raise ValueError('Frozen packet bridge differs.')
    expected={'inputs.jsonl','labels.jsonl','observation-references.jsonl','reference-policy-diagnostic.jsonl','bridge.features.jsonl','bridge.explanations.jsonl'}|{a+'.jsonl' for a in ARMS}|{a+s for a in ['narrow','broad'] for s in ['.inspections.jsonl','.weights.jsonl']}
    if set(s['evidence_sha256'])!=expected:raise ValueError('Report-language evidence paths differ.')
    for n,h in s['evidence_sha256'].items():
        if Path(n).name!=n or sha((path.parent/n).read_bytes())!=h:raise ValueError('Report-language evidence differs.')
    for n,k in [('inputs','inputs'),('labels','labels'),('observation-references','observations')]:
        if sha((path.parent/(n+'.jsonl')).read_bytes())!=m['sha256']['narrow/development.'+k+'.jsonl']:raise ValueError('Evaluation data differ.')
    records={r['id']:r for r in read_jsonl(path.parent/'inputs.jsonl')};keys={k['id']:k for k in read_jsonl(path.parent/'labels.jsonl')};rows={}
    if set(s['approaches'])!=set(ARMS):raise ValueError('Local arm coverage differs.')
    for a,result in s['approaches'].items():
        rows[a]={r['id']:r for r in read_jsonl(path.parent/(a+'.jsonl'))}
        if set(rows[a])!=set(records) or result['metrics']!=evaluate(path.parent/'labels.jsonl',path.parent/(a+'.jsonl'),inputs_path=path.parent/'inputs.jsonl'):raise ValueError('Local scores or coverage differ.')
        if a in ['narrow','broad']:
            meta=result['training']
            if meta['parameters']!=PARAMETERS or meta['training_inputs_sha256']!=m['sha256'][a+'/train.inputs.jsonl'] or meta['training_annotations_sha256']!=m['sha256'][a+'/train.observations.jsonl']:raise ValueError('Matched training differs.')
        for identifier,row in rows[a].items():
            if a in ['narrow','broad','report_rules']:
                recomputed=apply_policy(records[identifier],row['readings'])
                if row['predictions']!=recomputed['predictions'] or row['trace']!=recomputed['trace']:raise ValueError('Policy trace differs.')
            if a in ['narrow','broad'] and row['input_sha256']!=sha(json.dumps(pipeline_input(records[identifier]),sort_keys=True).encode()):raise ValueError('Shared inference input differs.')
        if a in ['narrow','broad']:
            weights={r['feature']:r['normal_minus_fault'] for r in read_jsonl(path.parent/(a+'.weights.jsonl'))}
            if weights!=result['method_weights_normal_minus_fault']:raise ValueError('Saved method weights differ.')
            inspected=read_jsonl(path.parent/(a+'.inspections.jsonl'))
            if {r['id'] for r in inspected}!=set(records) or len(inspected)!=len(records):raise ValueError('Inspection coverage differs.')
            for item in inspected:
                if [r['observation_index'] for r in item['reports']]!=list(range(len(records[item['id']]['input']['observations']))):raise ValueError('Report vector coverage differs.')
                for report in item['reports']:
                    if report['vector']['dimensions']!=result['training']['feature_count']:raise ValueError('Report dimensions differ.')
                    values={v['feature']:v['value'] for v in report['vector']['nonzero']}
                    for f,e in report['fields'].items():
                        p=rows[a][item['id']]['readings'][report['observation_index']]['probabilities'][f]
                        margin=e['intercept_difference']+sum(c['contribution'] for c in e['top_contributions'])+e['remaining_contribution']
                        if p!=e['probabilities'] or not math.isclose(margin,math.log(p[e['selected']]/p[e['compared_with']]),abs_tol=1e-8):raise ValueError('Report margin differs.')
                        for c in e['top_contributions']:
                            if c['value']!=values[c['feature']] or not math.isclose(c['contribution'],c['value']*c['coefficient_difference'],abs_tol=1e-10):raise ValueError('Report contribution differs.')
    annotations=read_jsonl(path.parent/'observation-references.jsonl')
    if s['report_metrics']!=reports_score(rows,annotations,keys) or s['changes']!=changes(rows,keys) or s['comparison_to_bridge']!=changes(rows,keys,'bridge') or s['controls']!=controls(rows,keys):raise ValueError('Report-language diagnostics differ.')
    by_id={}
    for a in annotations:by_id.setdefault(a['id'],[]).append(a)
    for row in read_jsonl(path.parent/'reference-policy-diagnostic.jsonl'):
        expected=apply_policy(records[row['id']],by_id[row['id']])
        if row['predictions']!=expected['predictions'] or row['trace']!=expected['trace']:raise ValueError('Reference-fed trace differs.')
    if s['reference_policy_diagnostic']['metrics']!=evaluate(path.parent/'labels.jsonl',path.parent/'reference-policy-diagnostic.jsonl',inputs_path=path.parent/'inputs.jsonl'):raise ValueError('Reference-fed diagnostic differs.')
    return s,rows
