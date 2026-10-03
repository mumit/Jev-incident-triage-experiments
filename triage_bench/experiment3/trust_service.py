"""Read-only inspection of shared interpreter responses and declaration policy joins."""
import json
from pathlib import Path
from triage_bench.dataset import ROOT,read_jsonl
from .trust_trial import context,verify,HOSTED,LOCAL,body,arm_labels,POLICIES
from .trust_evaluation import evaluate_run
from .trust_policy import effective_readings,apply_trust_policy,header_fact
from .declared_data import declaration_fact
from .metadata_policy import scope_fact
from .interpretation_model import report_inputs,policy_inputs
from .transforms import dependency_facts,measurement_facts
from .data import changed_paths

class TrustStudy:
 def __init__(self,root=ROOT):
  self.root=Path(root);self.directory=self.root/'data/declaration-trust-draft';m,records,keys,ann,texts=context(self.directory);self.manifest=m;self.records={r['id']:r for r in records};self.keys={k['id']:k for k in keys};self.annotations={};self.texts={t['text_id']:t for t in texts};self.text_for={(o['id'],o['observation_index']):t['text_id'] for t in texts for o in t['occurrences']}
  for a in ann:self.annotations.setdefault(a['id'],[]).append(a)
  self.local=None;self.hosted=None;self.rows={};self.inspections={};self.requests=[];self.responses=[];self.status=[]
  for kind,folder in [('local','declaration-trust'),('hosted','declaration-trust-jev')]:
   for p in sorted((self.root/'runs'/folder).glob('*/summary.json'),key=lambda p:p.stat().st_mtime,reverse=True):
    try:
     s,rows,_,requests,responses=verify(p,self.directory)
     corrected=evaluate_run(p);s={**s,'attribution':corrected['attribution'],'attribution_correction':corrected['correction']}
     if kind=='local':self.local={**s,'run_id':p.parent.name};self.inspections={a:{r['text_id']:r for r in read_jsonl(p.parent/(a+'.inspections.jsonl'))} for a in ['narrow','broad']}
     else:self.hosted={**s,'run_id':p.parent.name};self.requests=requests
     self.responses+=responses;self.rows.update(rows);break
    except (OSError,ValueError,KeyError,TypeError):self.status.append('Saved '+kind+' evidence differs; predictions unavailable.')
  if not self.local:self.status.append('No saved local controls. Inputs and references remain available.')
  if not self.hosted:self.status.append('Jev has no saved responses on this pack.')
 def catalog(self):
  readers={**HOSTED,**LOCAL}
  return {'manifest':self.manifest,'readers':readers,'policies':POLICIES,'arms':arm_labels(readers),'local':self.local,'hosted':self.hosted,'status':' '.join(self.status) or 'Saved shared readings and declaration policy joins verify. Draft synthetic references.',
          'cases':{'development':[{'id':r['id'],'family':self.keys[r['id']]['incident_family_id'],'pair_id':self.keys[r['id']]['pair_id'],'control':self.keys[r['id']]['control']} for r in self.records.values()]}}
 def case(self,identifier,split='development',arm='jev_declared__guarded',report_index=0):
  if split!='development' or identifier not in self.records or arm not in self.catalog()['arms']:raise ValueError('Unknown declaration-trust packet or inference path.')
  reader,policy=arm.split('__');r=self.records[identifier];key=self.keys[identifier];reports=report_inputs(r);partner=next(x for x in self.records.values() if x['id']!=identifier and self.keys[x['id']]['pair_id']==key['pair_id'])
  if isinstance(report_index,bool) or not isinstance(report_index,int) or not 0<=report_index<len(reports):raise ValueError('Unknown report index.')
  t=self.texts[self.text_for[identifier,report_index]];facts={**policy_inputs(r),'measurement_scope':[scope_fact(o) for o in r['input']['observations']],'instrument_domain':[declaration_fact(o) for o in r['input']['observations']],'prose_header':[header_fact(o['detail']) for o in r['input']['observations']]}
  request=body(t['text'],reader) if reader in HOSTED else {'schema':'declaration-trust-input-1','reports':reports,'policy_inputs':facts,'boundary':'Only normalized text enters the frozen local interpreter. Both policies copy occurrence-specific structured domains and retain identical actual operation readings. References never enter inference.'}
  saved=next((q for q in self.requests if q['reader']==reader and q['text_id']==t['text_id']),None);response=next((q for q in self.responses if q['reader']==reader and q['text_id']==t['text_id']),None)
  if saved and saved['body']!=request:raise ValueError('Prepared and saved trust request differ.')
  inspections=[{'observation_index':i,**self.inspections[reader][self.text_for[identifier,i]]} for i in range(len(reports))] if reader in self.inspections else None
  return {'record':r,'paired':partner,'changed_paths':changed_paths(r['input'],partner['input']),'draft_reference':key,'report_references':self.annotations[identifier],'reports':reports,'training_reports':None,'dependency_facts':dependency_facts(r['input']),'measurement_facts':measurement_facts(r['input']),
          'outputs':{a:rows.get(identifier) for a,rows in self.rows.items()},'reading_outputs':{a:self.rows.get(a,{}).get(identifier) for a in self.catalog()['arms']},'request':request,'saved_request':saved,'saved_response':response,'report_inspections':inspections,'packet_explanation':None,'packet_vector':None,'reading_instructions':{a:body('',a)['questions']['reading'] for a in HOSTED},'reference_policy_diagnostic':apply_trust_policy(r,effective_readings(r,self.annotations[identifier]),policy=='guarded'),'policy_facts':facts,'shared_report':t,'selected_reader':reader,'selected_policy':policy}
