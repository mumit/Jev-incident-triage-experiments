"""Read-only inspection of the matched question trial; no inference from the browser."""
import json
from pathlib import Path
from triage_bench.dataset import ROOT,read_jsonl
from .data import changed_paths
from .question_trial import ARMS,body,validate,verify
from .transforms import MODEL,dependency_facts,measurement_facts,transformed_packet,sha

class QuestionStudy:
    def __init__(self,root=ROOT):
        self.root=Path(root);self.directory=self.root/'data/experiment-3-question-draft';self.manifest=validate(self.directory)
        self.records={r['id']:r for r in read_jsonl(self.directory/'development.inputs.jsonl')}
        self.keys={k['id']:k for k in read_jsonl(self.directory/'development.labels.jsonl')}
        self.summary=None;self.rows={};self.requests={};self.status='No saved Jev question comparison.'
        for path in sorted((self.root/'runs/experiment-3-questions').glob('*/summary.json'),key=lambda p:p.stat().st_mtime,reverse=True):
            try:
                self.summary,self.rows,self.requests=verify(path,self.root,self.directory);self.summary['run_id']=path.parent.name
                self.status='Saved Jev question comparison: '+self.summary['status']+'; draft references.';break
            except (OSError,ValueError,KeyError,TypeError):self.status='Saved question evidence differs or is incomplete; scores are unavailable.'

    def catalog(self):
        return {'comparison':'questions','manifest':self.manifest,'variants':ARMS,'status':'This comparison changes Jev questions only; ML is outside its scope.',
                'model':MODEL,'pilot':None,'hosted_pilot':self.summary,'hosted_status':self.status,
                'jev_status':self.summary['status'] if self.summary else 'not_run',
                'cases':{'train':[],'development':[{'id':r['id'],'family':self.keys[r['id']]['incident_family_id'],
                          'pair_id':self.keys[r['id']]['pair_id'],'pair_kind':self.keys[r['id']]['pair_kind']} for r in self.records.values()]}}

    def case(self,identifier,variant='original',split='development'):
        if split!='development' or identifier not in self.records or variant not in ARMS:raise ValueError('Unknown question-trial case or arm.')
        r=self.records[identifier];key=self.keys[identifier];partner=next(other for id,other in self.records.items() if id!=identifier and self.keys[id]['pair_id']==key['pair_id'])
        request=body(r,variant)
        return {'record':r,'draft_reference':key,'paired':partner,'changed_paths':changed_paths(r['input'],partner['input']),
                'dependency_facts':dependency_facts(r['input']),'measurement_facts':measurement_facts(r['input']),
                'packets':{'baseline':transformed_packet(r,'combined'),**{a:transformed_packet(r,'combined') for a in ARMS}},
                'question_sets':{a:body(r,a)['questions'] for a in ARMS},
                'request':request,'state_sha256':sha(request['state'].encode()),'questions_sha256':sha(json.dumps(request['questions'],sort_keys=True).encode()),
                'request_bytes':len(json.dumps(request,ensure_ascii=False).encode()),'outputs':{},
                'hosted_outputs':{a:self.rows.get(a,{}).get(identifier) for a in ARMS},
                'hosted_saved_requests':{a:self.requests.get((identifier,a)) for a in ARMS},
                'jev_status':self.summary['status'] if self.summary else 'not_run'}
