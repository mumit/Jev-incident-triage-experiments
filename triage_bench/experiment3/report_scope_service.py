"""Read-only inspection of the measured-function instruction comparison."""
import json
from pathlib import Path
from triage_bench.dataset import ROOT,read_jsonl
from .report_scope_data import validate
from .report_scope_trial import verify,LOCAL,HOSTED,body
from .interpretation_model import report_inputs,pipeline_input,apply_policy
from .transforms import dependency_facts,measurement_facts
from .data import changed_paths

class ReportScopeStudy:
 def __init__(self,root=ROOT):
  self.root=Path(root);self.directory=self.root/'data/report-scope-draft';validate(self.directory)
  self.manifest=json.loads((self.directory/'manifest.json').read_text());self.records={r['id']:r for r in read_jsonl(self.directory/'development.inputs.jsonl')};self.keys={k['id']:k for k in read_jsonl(self.directory/'development.labels.jsonl')};self.annotations={}
  for a in read_jsonl(self.directory/'development.observations.jsonl'):self.annotations.setdefault(a['id'],[]).append(a)
  self.local=None;self.hosted=None;self.rows={};self.inspections={};self.requests=[];self.responses=[];self.status=[]
  for kind,folder in [('local','report-scope'),('hosted','report-scope-jev')]:
   for p in sorted((self.root/'runs'/folder).glob('*/summary.json'),key=lambda p:p.stat().st_mtime,reverse=True):
    try:
     s,rows,requests,responses=verify(p,self.directory)
     if kind=='local':
      self.local={**s,'run_id':p.parent.name};self.inspections={a:{r['id']:r['reports'] for r in read_jsonl(p.parent/(a+'.inspections.jsonl'))} for a in ['narrow','broad']}
     else:self.hosted={**s,'run_id':p.parent.name};self.requests=requests;self.responses=responses
     self.rows.update(rows);break
    except (OSError,ValueError,KeyError,TypeError):self.status.append('Saved '+kind+' evidence differs; predictions unavailable.')
  if not self.local:self.status.append('No saved ML controls. Inputs and references remain available.')
  if not self.hosted:self.status.append('Jev has no saved responses on this pack.')
 def catalog(self):
  return {'manifest':self.manifest,'arms':{**HOSTED,**LOCAL},'local':self.local,'hosted':self.hosted,'status':' '.join(self.status) or 'Saved Jev and ML evidence verifies. Draft synthetic references.',
          'cases':{'development':[{'id':r['id'],'family':self.keys[r['id']]['incident_family_id'],'pair_id':self.keys[r['id']]['pair_id'],'control':self.keys[r['id']]['control']} for r in self.records.values()]}}
 def case(self,identifier,split='development',arm='jev_focal',report_index=0):
  if split!='development' or identifier not in self.records or arm not in {**LOCAL,**HOSTED}:raise ValueError('Unknown measured-function packet or arm.')
  r=self.records[identifier];key=self.keys[identifier];partner=next(x for x in self.records.values() if x['id']!=identifier and self.keys[x['id']]['pair_id']==key['pair_id']);reports=report_inputs(r)
  if isinstance(report_index,bool) or not isinstance(report_index,int) or not 0<=report_index<len(reports):raise ValueError('Unknown report index.')
  request=body(reports[report_index]['text'],arm) if arm in HOSTED else pipeline_input(r)
  saved=next((q for q in self.requests if q['id']==identifier and q['arm']==arm and q['observation_index']==report_index),None)
  response=next((q for q in self.responses if q['id']==identifier and q['arm']==arm and q['observation_index']==report_index),None)
  if saved and saved['body']!=request:raise ValueError('Prepared and recorded request differ.')
  return {'record':r,'paired':partner,'changed_paths':changed_paths(r['input'],partner['input']),'draft_reference':key,'report_references':self.annotations[identifier],'reports':reports,'training_reports':None,
          'dependency_facts':dependency_facts(r['input']),'measurement_facts':measurement_facts(r['input']),'outputs':{a:rows.get(identifier) for a,rows in self.rows.items()},'request':request,'saved_request':saved,'saved_response':response,
          'report_inspections':self.inspections.get(arm,{}).get(identifier),'packet_explanation':None,'packet_vector':None,'reading_instructions':{a:body('',a)['questions']['reading']['instructions'] for a in HOSTED},'reference_policy_diagnostic':apply_policy(r,self.annotations[identifier])}
