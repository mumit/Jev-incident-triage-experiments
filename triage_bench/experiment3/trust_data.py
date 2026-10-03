"""Fresh declaration-conflict pairs; report meanings and packet decisions are separate."""
import copy,json
from datetime import datetime,timedelta
from pathlib import Path
from triage_bench.dataset import ROOT,read_jsonl,write_jsonl,stamp
from triage_bench.policy import VERSION,OPTIONS,priority
from .data import make_pair,decisions,changed_paths
from .interpretation_model import report_inputs
from .metadata_data import DOMAINS
from .metadata_policy import scope_fact
from .trust_policy import header_fact
from .transforms import sha
DIRECTORY=ROOT/'data/declaration-trust-draft'
DECISION={'date':'2026-10-02','source':'user_selected_retain_noc_on_declaration_conflict','definition':'Retain NOC until conflicting structured and explicit prose domain declarations are resolved. Preserve operation reading. Only current affected-service evidence on a fault-bearing asset can block ownership.','status':'synthetic_teaching_definition_not_specialist_reviewed'}

def build_rows():
    specs=[(d+' '+kind,kind,d) for kind in ['fault_conflict','normal_conflict','clean_comparability'] for d in DOMAINS]
    specs += [(d+' unresolved','missing' if i%2==0 else 'ambiguous',d) for i,d in enumerate(DOMAINS)]
    specs += [(d+' eligibility','stale' if i%2==0 else 'unlinked',d) for i,d in enumerate(DOMAINS)]
    records,keys,ann=[],[],[];other={'core':'ran','ran':'power','power':'transport','transport':'core'}
    for family,kind,domain in specs:
        for variant in [0,2]:
            prefix=kind.replace('_',' ').capitalize()+' consistency observation.'
            texts=[f'{prefix} Instrument domain: {domain}. The measured operation logs component failure and cannot produce its expected output.',f'{prefix} Instrument domain: {domain}. The measured operation logs normal execution and produces its expected output.']
            pair,targets=make_pair(('declaration consistency '+family,'arrival',domain,texts[0],'mesh' if variant else 'split','degraded'),'development',variant);a,b=pair
            for r in pair:
                o=r['input']['observations'][0];o['instrument_domain']={'status':'declared','domain':domain};o['measurement_scope']={'status':'declared','function':DOMAINS[domain][0],'comparison_context':'condition-A'}
                n=copy.deepcopy(o);n['detail']=texts[1];n['measurement_scope']['function']=DOMAINS[domain][1];r['input']['observations'].append(n)
            for i in range(2):b['input']['observations'][i]['observed_at']=a['input']['observations'][i]['observed_at']
            owners=[domain,'noc'];path='input.observations[1].measurement_scope.function'
            if kind=='clean_comparability':b['input']['observations'][1]['measurement_scope']['function']=DOMAINS[domain][0]
            elif kind in {'fault_conflict','normal_conflict'}:
                index=0 if kind=='fault_conflict' else 1;b['input']['observations'][index]['instrument_domain']['domain']=other[domain];path=f'input.observations[{index}].instrument_domain.domain'
            elif kind=='missing':b['input']['observations'][0]['instrument_domain']=None;path='input.observations[0].instrument_domain'
            elif kind=='ambiguous':b['input']['observations'][0]['instrument_domain']['status']='ambiguous';path='input.observations[0].instrument_domain.status'
            elif kind=='stale':
                for r in pair:r['input']['observations'][1]['instrument_domain']['domain']=other[domain]
                now=datetime.fromisoformat(b['input']['decision_timestamp'].replace('Z','+00:00'));b['input']['observations'][1]['measured_at']=stamp(now-timedelta(minutes=20));path='input.observations[1].measured_at';owners=['noc',domain]
            elif kind=='unlinked':
                for r in pair:r['input']['observations'][1]['instrument_domain']['domain']=other[domain]
                a['input']['observations'][1]['asset_id']=a['input']['observations'][1]['asset_id'].split('-')[0]+'-z';path='input.observations[1].asset_id'
            for r,k,owner in zip(pair,targets,owners):
                r['id']=r['id'].replace('NS3-','NDT-');answer=decisions(owner,r['input']['service_impact'],owner=='noc');k.update(id=r['id'],pair_id=k['pair_id'].replace('NS3-','NDT-'),labels=answer,accepted_answers={f:[v] for f,v in answer.items()},control=kind,changed_path=path,pair_kind='decision_change',label_rationale='Prewritten NOC conflict rule: eligible structured/prose declaration disagreement on an asset bearing a current linked fault retains NOC, including a normal report on another function. Exclude stale and unlinked reports. Missing/ambiguous fault metadata supplies no domain. Agreeing declarations use the frozen function-aware policy; comparable fault/normal contradiction retains NOC.')
                for i,reading in enumerate(['fault','normal']):ann.append({'id':r['id'],'observation_index':i,'domain':domain,'reading':reading,'review_status':'draft_not_specialist_reviewed','rationale':'Domain describes the explicit prose instrument header; reading describes its written operation outcome. Structured metadata and packet decisions are separate. A metadata/prose conflict does not change this report annotation.'})
            records+=pair;keys+=targets
    return records,keys,ann

def build(directory=DIRECTORY):
    directory=Path(directory)
    if directory.exists():raise ValueError('Choose a new declaration-trust data directory.')
    records,keys,ann=build_rows()
    for n,v in [('inputs',records),('labels',keys),('observations',ann)]:write_jsonl(directory/('development.'+n+'.jsonl'),v)
    m={'schema':'declaration-trust-data-1','operator':'Northstar Telecom','synthetic':True,'reference_status':'draft_not_specialist_reviewed','evaluation_status':'development_only_no_held_out_set','human_decision':DECISION,'records':len(records),'reports':len(ann),'families':len({k['incident_family_id'] for k in keys}),'pairs':len(records)//2,'distinct_report_texts':len({o['text'] for r in records for o in report_inputs(r)}),'construction':'Further families with agreeing/conflicting, missing/ambiguous, current/stale and linked/unlinked declarations plus clean comparability controls. Each pair changes one metadata or eligibility field, never report text or annotation. Identical text can have different structured declarations; copy metadata by occurrence, never from the first occurrence. Metadata age and authority are not tested.','sha256':{p.name:sha(p.read_bytes()) for p in sorted(directory.glob('*.jsonl'))}}
    (directory/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');validate(directory);return m

def validate(directory=DIRECTORY):
    directory=Path(directory);m=json.loads((directory/'manifest.json').read_text());expected={'development.'+n+'.jsonl' for n in ['inputs','labels','observations']}
    if set(m['sha256'])!=expected or any(sha((directory/n).read_bytes())!=h for n,h in m['sha256'].items()):raise ValueError('Trust data fingerprints differ.')
    rows=read_jsonl(directory/'development.inputs.jsonl');keys=read_jsonl(directory/'development.labels.jsonl');ann=read_jsonl(directory/'development.observations.jsonl');by={k['id']:k for k in keys};refs={(a['id'],a['observation_index']):a for a in ann};pairs={}
    if len(rows)!=len(by) or len(keys)!=len(by) or {r['id'] for r in rows}!=set(by) or len(ann)!=len(refs) or set(refs)!={(r['id'],i) for r in rows for i in range(2)}:raise ValueError('Trust data joins differ.')
    for r in rows:
        k=by[r['id']];p=r['input'];impact=p['service_impact']
        if set(r)!={'id','input','policy_version'} or r['policy_version']!=VERSION or set(p)!={'operator','ticket','service_impact','change_record','decision_timestamp','observations','topology'} or p['operator']!='Northstar Telecom' or len(p['observations'])!=2 or k['split']!='development' or k['review_status']!='draft_not_specialist_reviewed':raise ValueError('Invalid public trust packet.')
        if set(k['labels'])!=set(OPTIONS) or any(v not in OPTIONS[f] for f,v in k['labels'].items()) or k['labels']['priority']!=priority(impact) or impact['affected_sites']!=len(set(impact['affected_site_ids'])) or any(k['accepted_answers'][f]!=[v] for f,v in k['labels'].items()):raise ValueError('Invalid trust reference.')
        for i,o in enumerate(p['observations']):
            a=refs[r['id'],i];d=o.get('instrument_domain')
            if set(o)-{'asset_id','detail','measured_at','observed_at','source','valid_for_minutes','measurement_scope','instrument_domain'} or o['asset_id'] not in p['topology']['nodes'] or scope_fact(o)['state']!='declared':raise ValueError('Trust observation boundary differs.')
            if d is not None and (not isinstance(d,dict) or set(d)!={'status','domain'} or d['status'] not in {'declared','ambiguous'} or d['domain'] not in DOMAINS):raise ValueError('Invalid trust declaration.')
            if header_fact(o['detail'])!={'state':'declared','domain':a['domain']} or a['reading']!=['fault','normal'][i] or a['review_status']!='draft_not_specialist_reviewed':raise ValueError('Trust prose reference differs.')
        pairs.setdefault(k['pair_id'],[]).append(r)
    for pair in pairs.values():
        if len(pair)!=2:raise ValueError('Incomplete trust pair.')
        ka,kb=[by[r['id']] for r in pair]
        if ka['incident_family_id']!=kb['incident_family_id'] or ka['changed_path']!=kb['changed_path'] or changed_paths(pair[0]['input'],pair[1]['input'])!=[ka['changed_path']] or report_inputs(pair[0])!=report_inputs(pair[1]) or any(refs[pair[0]['id'],i][f]!=refs[pair[1]['id'],i][f] for i in range(2) for f in ['domain','reading']):raise ValueError('Trust pair intervention differs.')
    families={k['incident_family_id'] for k in keys};texts={o['text'] for r in rows for o in report_inputs(r)}
    for old in (ROOT/'data').rglob('*.labels.jsonl'):
        if old.parent in {directory,DIRECTORY}:continue
        prior=read_jsonl(old)
        if set(by)&{k['id'] for k in prior} or families&{k['incident_family_id'] for k in prior}:raise ValueError('Earlier family or packet reused.')
    for old in (ROOT/'data').rglob('*.inputs.jsonl'):
        if old.parent in {directory,DIRECTORY}:continue
        if texts&{o['text'] for r in read_jsonl(old) for o in report_inputs(r) if 'policy_version' in r}:raise ValueError('Earlier report text reused.')
    if any(m[k]!=v for k,v in {'records':len(rows),'reports':len(ann),'families':len(families),'pairs':len(pairs),'distinct_report_texts':len(texts),'human_decision':DECISION}.items()):raise ValueError('Trust manifest differs.')
    return {k:m[k] for k in ['records','reports','families','pairs','distinct_report_texts']}
