"""New metadata intervention pairs with references written before inference."""
import copy,json
from pathlib import Path
from datetime import datetime,timedelta
from triage_bench.dataset import ROOT,read_jsonl,write_jsonl,stamp
from triage_bench.policy import VERSION,OPTIONS,priority
from .data import make_pair,decisions,changed_paths
from .interpretation_model import report_inputs
from .transforms import sha
from .metadata_policy import FUNCTIONS
DIRECTORY=ROOT/'data/metadata-policy-draft'
DECISION={'date':'2026-10-02','source':'user_selected_explicit_instrument_metadata_first','status':'synthetic_input_assumption_not_operational_validation'}
DOMAINS={'core':('request_intake','registration_completion'),'transport':('frame_forwarding','egress_delivery'),'ran':('radio_decoding','timing_alignment'),'power':('regulated_output','battery_runtime')}

def build_rows():
    specs=[(d+' function comparison','function',d) for d in DOMAINS]+[(d+' condition comparison','context',d) for d in DOMAINS]+[('core missing instrument scope','missing','core'),('core ambiguous instrument scope','ambiguous','core'),('transport stale missing scope','stale','transport'),('ran unlinked missing scope','unlinked','ran')]
    records,keys,annotations=[],[],[]
    for family,kind,domain in specs:
        for variant in [0,2]:
            first,second=DOMAINS[domain]
            fault=f'Independent {domain} observation: The monitored operation fails because of an internal component malfunction; valid operations cannot finish.'
            normal=f'Independent {domain} observation: The monitored operation completes normally as specified; the measured operation succeeds.'
            if kind=='context':
                fault=f'Independent {domain} observation: A current operation trace confirms a component failure during the measured operation.'
                normal=f'Independent {domain} observation: A current operation trace verifies normal execution of the measured operation.'
            pair,targets=make_pair(('metadata '+family,'arrival',domain,fault,'mesh' if variant else 'split','degraded'),'development',variant)
            a,b=pair
            for r in pair:
                o=r['input']['observations'][0];o['measurement_scope']={'status':'declared','function':first,'comparison_context':'condition-A'}
                n=copy.deepcopy(o);n['detail']=normal;n['measurement_scope']['function']=second;r['input']['observations'].append(n)
            b['input']['observations'][0]['observed_at']=a['input']['observations'][0]['observed_at'];b['input']['observations'][1]['observed_at']=a['input']['observations'][1]['observed_at']
            path='input.observations[1].measurement_scope.function';answers=[domain,'noc']
            if kind=='function':b['input']['observations'][1]['measurement_scope']['function']=first
            elif kind=='context':
                for r in pair:r['input']['observations'][1]['measurement_scope']['function']=first
                a['input']['observations'][1]['measurement_scope']['comparison_context']='condition-B';path='input.observations[1].measurement_scope.comparison_context'
            elif kind=='missing':b['input']['observations'][1]['measurement_scope']=None;path='input.observations[1].measurement_scope'
            elif kind=='ambiguous':b['input']['observations'][1]['measurement_scope']['status']='ambiguous';path='input.observations[1].measurement_scope.status'
            elif kind=='stale':
                for r in pair:del r['input']['observations'][1]['measurement_scope']
                now=datetime.fromisoformat(b['input']['decision_timestamp'].replace('Z','+00:00'));b['input']['observations'][1]['measured_at']=stamp(now-timedelta(minutes=20));path='input.observations[1].measured_at';answers=['noc',domain]
            elif kind=='unlinked':
                for r in pair:del r['input']['observations'][1]['measurement_scope']
                a['input']['observations'][1]['asset_id']=a['input']['observations'][1]['asset_id'].split('-')[0]+'-z';path='input.observations[1].asset_id'
            for r,k,owner in zip(pair,targets,answers):
                r['id']=r['id'].replace('NS3-','NMP-');answer=decisions(owner,r['input']['service_impact'],owner=='noc');k.update(id=r['id'],pair_id=k['pair_id'].replace('NS3-','NMP-'),labels=answer,accepted_answers={f:[v] for f,v in answer.items()},control=kind,changed_path=path,pair_kind='decision_change',label_rationale='Draft instrument-metadata policy reference. A current linked fault assigns its domain unless a normal report contradicts the same measured function under the same declared conditions, or a relevant eligible report has unresolved scope. Distinct declared functions or conditions are compatible. Stale and unlinked reports cannot create a scope block.')
                for i,state in enumerate(['fault','normal']):annotations.append({'id':r['id'],'observation_index':i,'domain':domain,'reading':state,'review_status':'draft_not_specialist_reviewed','rationale':'Prewritten meaning of the reported operation. Metadata describes its function and comparison conditions, not whether that operation succeeds.'})
            records+=pair;keys+=targets
    return records,keys,annotations

def build(directory=DIRECTORY):
    directory=Path(directory)
    if directory.exists():raise ValueError('Choose a new metadata data directory.')
    records,keys,ann=build_rows()
    for n,rows in [('inputs',records),('labels',keys),('observations',ann)]:write_jsonl(directory/('development.'+n+'.jsonl'),rows)
    texts={o['text'] for r in records for o in report_inputs(r)}
    manifest={'schema':'metadata-policy-data-1','operator':'Northstar Telecom','synthetic':True,'reference_status':'draft_not_specialist_reviewed','evaluation_status':'development_only_no_held_out_set','human_decision':DECISION,'records':len(records),'reports':len(ann),'families':len({k['incident_family_id'] for k in keys}),'pairs':len(records)//2,'distinct_report_texts':len(texts),'construction':'Pairs change one metadata or eligibility field. Report texts and their meanings match across each pair. Two graph/impact variants share templates; distinct text responses are reused across packet occurrences. Supplied function and condition metadata is a synthetic assumption.','sha256':{p.name:sha(p.read_bytes()) for p in sorted(directory.glob('*.jsonl'))}}
    (directory/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');validate(directory);return manifest

def validate(directory=DIRECTORY):
    directory=Path(directory);m=json.loads((directory/'manifest.json').read_text());expected={'development.'+k+'.jsonl' for k in ['inputs','labels','observations']}
    if set(m['sha256'])!=expected or any(sha((directory/n).read_bytes())!=h for n,h in m['sha256'].items()):raise ValueError('Metadata data fingerprints differ.')
    rows=read_jsonl(directory/'development.inputs.jsonl');keys=read_jsonl(directory/'development.labels.jsonl');ann=read_jsonl(directory/'development.observations.jsonl');by={k['id']:k for k in keys};annotations={(a['id'],a['observation_index']):a for a in ann};pairs={}
    if len(rows)!=len(by) or len(keys)!=len(by) or {r['id'] for r in rows}!=set(by):raise ValueError('Metadata packet joins differ.')
    coverage={(r['id'],i) for r in rows for i in range(len(r['input']['observations']))}
    if set(annotations)!=coverage or len(ann)!=len(coverage) or any(a['domain'] not in DOMAINS or a['reading'] not in {'fault','normal'} or a['review_status']!='draft_not_specialist_reviewed' for a in ann):raise ValueError('Report reference coverage differs.')
    for r in rows:
        k=by[r['id']];p=r['input'];impact=p['service_impact']
        if set(r)!={'id','input','policy_version'} or r['policy_version']!=VERSION or set(p)!={'operator','ticket','service_impact','change_record','decision_timestamp','observations','topology'} or p['operator']!='Northstar Telecom' or k['split']!='development' or k['review_status']!='draft_not_specialist_reviewed':raise ValueError('Invalid public metadata packet.')
        if set(k['labels'])!=set(OPTIONS) or any(v not in OPTIONS[f] for f,v in k['labels'].items()) or k['labels']['priority']!=priority(impact) or impact['affected_sites']!=len(set(impact['affected_site_ids'])) or any(k['accepted_answers'][f]!=[v] for f,v in k['labels'].items()):raise ValueError('Invalid impact/reference.')
        for o in p['observations']:
            if set(o)-{'asset_id','detail','measured_at','observed_at','source','valid_for_minutes','measurement_scope'} or o['asset_id'] not in p['topology']['nodes']:raise ValueError('Observation boundary differs.')
            if o.get('measurement_scope') is not None:
                s=o['measurement_scope']
                if set(s)!={'status','function','comparison_context'} or s['status'] not in {'declared','ambiguous'} or s['function'] not in FUNCTIONS or s['comparison_context'] not in {'condition-A','condition-B'}:raise ValueError('Invalid supplied scope.')
        pairs.setdefault(k['pair_id'],[]).append(r)
    for pair in pairs.values():
        ka,kb=[by[r['id']] for r in pair]
        if len(pair)!=2 or ka['incident_family_id']!=kb['incident_family_id'] or ka['changed_path']!=kb['changed_path'] or changed_paths(pair[0]['input'],pair[1]['input'])!=[ka['changed_path']] or report_inputs(pair[0])!=report_inputs(pair[1]) or [{f:annotations[r['id'],i][f] for f in ['domain','reading']} for i in range(2) for r in pair][::2]!=[{f:annotations[pair[1]['id'],i][f] for f in ['domain','reading']} for i in range(2)]:raise ValueError('Pair intervention or report meanings differ.')
    families={k['incident_family_id'] for k in keys};texts={o['text'] for r in rows for o in report_inputs(r)}
    for old in (ROOT/'data').rglob('*.labels.jsonl'):
        if old.parent in {directory,DIRECTORY}:continue
        prior=read_jsonl(old)
        if set(by)&{k['id'] for k in prior} or families&{k['incident_family_id'] for k in prior}:raise ValueError('Earlier family or packet reused.')
    for old in (ROOT/'data').rglob('*.inputs.jsonl'):
        if old.parent in {directory,DIRECTORY}:continue
        if texts & {o['text'] for r in read_jsonl(old) for o in report_inputs(r) if 'policy_version' in r}:raise ValueError('Earlier report text reused.')
    if any(m[k]!=v for k,v in {'records':len(rows),'reports':len(ann),'families':len(families),'pairs':len(pairs),'distinct_report_texts':len(texts),'human_decision':DECISION}.items()):raise ValueError('Manifest differs.')
    return {k:m[k] for k in ['records','reports','families','pairs','distinct_report_texts']}
