"""Fresh declared-domain families with independent report and packet references."""
import copy,json
from pathlib import Path
from datetime import datetime,timedelta
from triage_bench.dataset import ROOT,read_jsonl,write_jsonl,stamp
from triage_bench.policy import VERSION,OPTIONS,priority
from .data import make_pair,decisions,changed_paths
from .interpretation_model import report_inputs
from .metadata_data import DOMAINS
from .metadata_policy import scope_fact
from .transforms import sha
DIRECTORY=ROOT/'data/declared-domain-draft'
DECISION={'date':'2026-10-02','source':'user_selected_declared_domain','definition':'Identify the declared instrument domain. Policy separately checks current affected-service relevance. Missing or ambiguous declarations establish no domain.','status':'synthetic_teaching_definition_not_specialist_reviewed'}

def declaration_fact(observation):
 value=observation.get('instrument_domain')
 if value is None:return {'state':'missing','domain':'none'}
 if not isinstance(value,dict):return {'state':'malformed','domain':'none'}
 if value.get('status')!='declared':return {'state':'ambiguous','domain':'none'}
 domain=value.get('domain')
 if not isinstance(domain,str) or domain not in DOMAINS:return {'state':'invalid','domain':'none'}
 return {'state':'declared','domain':domain}

def build_rows():
 specs=[(d+' generic','function',d) for d in DOMAINS]+[(d+' technical distraction','distraction',d) for d in DOMAINS]+[('ran missing declaration','missing','ran'),('power missing declaration','missing','power'),('core unresolved declaration','ambiguous','core'),('transport unresolved declaration','ambiguous','transport')]+[(d+' eligibility','stale' if i%2==0 else 'unlinked',d) for i,d in enumerate(DOMAINS)]
 records,keys,ann=[],[],[]
 distract={'core':'radio decoding','transport':'subscriber registration','ran':'electrical supply','power':'optical transport'}
 for family,kind,domain in specs:
  for variant in [0,2]:
   marker='Instrument domain: '+domain+'.'
   declaration={'status':'declared','domain':domain};reference_domain=domain
   if kind=='missing':marker='Instrument domain: unavailable.';declaration=None;reference_domain='none'
   elif kind=='ambiguous':marker='Instrument domain: unresolved between core and transport.';declaration={'status':'ambiguous','candidates':['core','transport']};reference_domain='none'
   prefix={'function':'Commissioned instrument observation.','distraction':'Cross-system instrument observation.','missing':'Unattributed instrument observation.','ambiguous':'Provisional instrument observation.','stale':'Timestamp-controlled instrument observation.','unlinked':'Path-controlled instrument observation.'}[kind]
   tail=''
   if kind=='distraction':tail=' Context only: the incident ticket also mentions '+distract[domain]+'. That separate function is not measured in this report.'
   elif kind=='missing':tail=' The measured equipment handles '+('radio decoding' if domain=='ran' else 'electrical supply')+'. No instrument domain declaration is available.'
   texts=[f'{prefix} {marker} The focal monitored operation records an internal component failure; the measured operation cannot execute correctly.{tail}',f'{prefix} {marker} The focal monitored operation records normal execution; the measured operation succeeds as specified.{tail}']
   pair,targets=make_pair(('declared '+family,'arrival',domain,texts[0],'mesh' if variant else 'split','degraded'),'development',variant);a,b=pair
   for r in pair:
    o=r['input']['observations'][0];o['instrument_domain']=copy.deepcopy(declaration);o['measurement_scope']={'status':'declared','function':DOMAINS[domain][0],'comparison_context':'condition-A'}
    n=copy.deepcopy(o);n['detail']=texts[1];n['measurement_scope']['function']=DOMAINS[domain][1];r['input']['observations'].append(n)
   b['input']['observations'][0]['observed_at']=a['input']['observations'][0]['observed_at'];b['input']['observations'][1]['observed_at']=a['input']['observations'][1]['observed_at']
   path='input.observations[1].measurement_scope.function';owners=[domain,'noc']
   if kind in {'function','distraction'}:b['input']['observations'][1]['measurement_scope']['function']=DOMAINS[domain][0]
   elif kind in {'missing','ambiguous'}:
    b['input']['observations'][0]['observed_at']=stamp(datetime.fromisoformat(b['input']['decision_timestamp'].replace('Z','+00:00'))-timedelta(minutes=3));path='input.observations[0].observed_at';owners=['noc','noc']
   elif kind=='stale':
    b['input']['observations'][0]['measured_at']=stamp(datetime.fromisoformat(b['input']['decision_timestamp'].replace('Z','+00:00'))-timedelta(minutes=20));path='input.observations[0].measured_at'
   elif kind=='unlinked':b['input']['observations'][0]['asset_id']=b['input']['observations'][0]['asset_id'].split('-')[0]+'-z';path='input.observations[0].asset_id'
   for r,k,owner in zip(pair,targets,owners):
    r['id']=r['id'].replace('NS3-','NDD-');answer=decisions(owner,r['input']['service_impact'],owner=='noc');k.update(id=r['id'],pair_id=k['pair_id'].replace('NS3-','NDD-'),labels=answer,accepted_answers={f:[v] for f,v in answer.items()},control=kind,changed_path=path,pair_kind='invariant' if kind in {'missing','ambiguous'} else 'decision_change',label_rationale='Prewritten declared-domain reference: a current linked fault assigns its declared domain when measurement scope is resolved and no comparable normal contradicts it. No single declaration, stale faults, disconnected faults and comparable contradictions retain NOC. Domain references identify the instrument declaration, not a root cause inferred from technical words.')
    for i,reading in enumerate(['fault','normal']):ann.append({'id':r['id'],'observation_index':i,'domain':reference_domain,'reading':reading,'review_status':'draft_not_specialist_reviewed','rationale':'Domain follows the explicit single instrument declaration; missing or ambiguous declarations mean none. Reading follows the independently written focal operation outcome. Neither timestamp, path nor packet target determines report meaning.'})
   records+=pair;keys+=targets
 return records,keys,ann

def build(directory=DIRECTORY):
 directory=Path(directory)
 if directory.exists():raise ValueError('Choose a new declared-domain data directory.')
 rows,keys,ann=build_rows()
 for n,v in [('inputs',rows),('labels',keys),('observations',ann)]:write_jsonl(directory/('development.'+n+'.jsonl'),v)
 m={'schema':'declared-domain-data-1','operator':'Northstar Telecom','synthetic':True,'reference_status':'draft_not_specialist_reviewed','evaluation_status':'development_only_no_held_out_set','human_decision':DECISION,'records':len(rows),'reports':len(ann),'families':len({k['incident_family_id'] for k in keys}),'pairs':len(rows)//2,'distinct_report_texts':len({o['text'] for r in rows for o in report_inputs(r)}),'construction':'Fresh generic, technical-distraction, missing/ambiguous declaration and eligibility pairs. Instrument declaration is an input fact supplied consistently in prose and structured metadata. Trust, contradictory declarations and incorrect metadata are not tested. Two graph/impact variants share texts; one prediction per distinct text is reused across occurrences.','sha256':{p.name:sha(p.read_bytes()) for p in sorted(directory.glob('*.jsonl'))}}
 (directory/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');validate(directory);return m

def validate(directory=DIRECTORY):
 directory=Path(directory);m=json.loads((directory/'manifest.json').read_text());expected={'development.'+k+'.jsonl' for k in ['inputs','labels','observations']}
 if set(m['sha256'])!=expected or any(sha((directory/n).read_bytes())!=h for n,h in m['sha256'].items()):raise ValueError('Declared data fingerprints differ.')
 rows=read_jsonl(directory/'development.inputs.jsonl');keys=read_jsonl(directory/'development.labels.jsonl');ann=read_jsonl(directory/'development.observations.jsonl');by={k['id']:k for k in keys};refs={(a['id'],a['observation_index']):a for a in ann};pairs={}
 if len(rows)!=len(by) or len(keys)!=len(by) or {r['id'] for r in rows}!=set(by) or len(ann)!=len(refs) or set(refs)!={(r['id'],i) for r in rows for i in range(2)}:raise ValueError('Declared data joins differ.')
 for r in rows:
  k=by[r['id']];p=r['input'];impact=p['service_impact']
  if set(r)!={'id','input','policy_version'} or r['policy_version']!=VERSION or set(p)!={'operator','ticket','service_impact','change_record','decision_timestamp','observations','topology'} or p['operator']!='Northstar Telecom' or len(p['observations'])!=2 or k['split']!='development' or k['review_status']!='draft_not_specialist_reviewed':raise ValueError('Invalid public declared packet.')
  if set(k['labels'])!=set(OPTIONS) or any(v not in OPTIONS[f] for f,v in k['labels'].items()) or k['labels']['priority']!=priority(impact) or impact['affected_sites']!=len(set(impact['affected_site_ids'])) or any(k['accepted_answers'][f]!=[v] for f,v in k['labels'].items()):raise ValueError('Invalid declared impact/reference.')
  for i,o in enumerate(p['observations']):
   a=refs[r['id'],i];d=o['instrument_domain'];fact=declaration_fact(o)
   if set(o)-{'asset_id','detail','measured_at','observed_at','source','valid_for_minutes','measurement_scope','instrument_domain'} or o['asset_id'] not in p['topology']['nodes'] or scope_fact(o)['state']!='declared':raise ValueError('Declared observation boundary differs.')
   marker='Instrument domain: unavailable.' if d is None else 'Instrument domain: unresolved between core and transport.' if d.get('status')=='ambiguous' else 'Instrument domain: '+d['domain']+'.'
   if (d is not None and not (d=={'status':'declared','domain':fact['domain']} or d=={'status':'ambiguous','candidates':['core','transport']})) or marker not in o['detail'] or a['domain']!=fact['domain'] or a['reading']!=['fault','normal'][i] or a['review_status']!='draft_not_specialist_reviewed':raise ValueError('Declaration/prose/reference boundary differs.')
  pairs.setdefault(k['pair_id'],[]).append(r)
 for pair in pairs.values():
  if len(pair)!=2:raise ValueError('Incomplete declared pair.')
  ka,kb=[by[r['id']] for r in pair]
  if ka['incident_family_id']!=kb['incident_family_id'] or ka['changed_path']!=kb['changed_path'] or changed_paths(pair[0]['input'],pair[1]['input'])!=[ka['changed_path']] or report_inputs(pair[0])!=report_inputs(pair[1]) or any(refs[pair[0]['id'],i][f]!=refs[pair[1]['id'],i][f] for i in range(2) for f in ['domain','reading']):raise ValueError('Declared pair intervention differs.')
 families={k['incident_family_id'] for k in keys};texts={o['text'] for r in rows for o in report_inputs(r)}
 for old in (ROOT/'data').rglob('*.labels.jsonl'):
  if old.parent in {directory,DIRECTORY}:continue
  prior=read_jsonl(old)
  if set(by)&{k['id'] for k in prior} or families&{k['incident_family_id'] for k in prior}:raise ValueError('Earlier family or packet reused.')
 for old in (ROOT/'data').rglob('*.inputs.jsonl'):
  if old.parent in {directory,DIRECTORY}:continue
  if texts&{o['text'] for r in read_jsonl(old) for o in report_inputs(r) if 'policy_version' in r}:raise ValueError('Earlier report text reused.')
 if any(m[k]!=v for k,v in {'records':len(rows),'reports':len(ann),'families':len(families),'pairs':len(pairs),'distinct_report_texts':len(texts),'human_decision':DECISION}.items()):raise ValueError('Declared manifest differs.')
 return {k:m[k] for k in ['records','reports','families','pairs','distinct_report_texts']}
