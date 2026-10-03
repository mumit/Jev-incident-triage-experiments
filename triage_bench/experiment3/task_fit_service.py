"""Read-only evidence workbench. Final evaluation is excluded from every route."""
import json
from pathlib import Path
from triage_bench.dataset import ROOT, read_jsonl
from .task_fit_data import validate, SPECS
from .task_fit_trial import ARMS, body, examples, packet, verify, check_freeze
from .task_fit_review import routing_review

class TaskFitStudy:
    def __init__(self,root=ROOT):
        self.root=Path(root); self.directory=self.root/'data/task-fit-draft'
        self.counts=validate(self.directory); self.records={}; self.keys={}; self.references={}
        for split in ('development','calibration'):
            self.records[split]={r['id']:r for r in read_jsonl(self.directory/f'{split}.inputs.jsonl')}
            self.keys[split]={r['id']:r for r in read_jsonl(self.directory/f'{split}.labels.jsonl')}
            self.references[split]={r['id']:r for r in read_jsonl(self.directory/f'{split}.observations.jsonl')}
        self.saved={}; self.status=[]
        for kind in ('local','development','repeat','calibration'):
            path=self.root/f'runs/task-fit/{kind}-2026-10-03-v1'
            if not (path/'summary.json').exists():
                self.status.append(kind+': no saved predictions'); continue
            try:
                verify(path,self.directory)
                self.saved[kind]={'summary':json.loads((path/'summary.json').read_text()),'responses':read_jsonl(path/'responses.jsonl'),
                                  'requests':read_jsonl(path/'requests.jsonl') if (path/'requests.jsonl').exists() else []}
            except (ValueError,KeyError,OSError,TypeError):
                self.status.append(kind+': verification failed; predictions unavailable')
        freeze=self.root/'checkpoints/task-fit-candidate-2026-10-03.json'; self.candidate=None
        if freeze.exists():
            try:
                candidate=json.loads(freeze.read_text()); self.candidate=check_freeze(freeze,candidate['arm'],self.directory)
            except (ValueError,KeyError,OSError,TypeError): self.status.append('Candidate freeze does not verify.')

    def catalog(self):
        summaries={}
        for kind,data in self.saved.items():
            s=data['summary']
            summaries[kind]={k:s.get(k) for k in ('status','attempted_requests','failed_requests','unattempted_requests','request_accounting','review_curves','repeatability')}
            summaries[kind]['metrics']={a:[{k:v for k,v in m.items() if k!='packets'} for m in metrics] for a,metrics in s['metrics'].items()}
            if kind in {'development','calibration'}:
                summaries[kind]['routing_review']=routing_review(self.root/f'runs/task-fit/{kind}-2026-10-03-v1')
        cases={}
        for split,rows in self.records.items():
            names={k['incident_family_id']:spec[0] for k,spec in zip(list(self.keys[split].values())[::2],SPECS[split])}
            cases[split]=[{'id':r['id'],'family':names[self.keys[split][r['id']]['incident_family_id']],
                           'pair_id':self.keys[split][r['id']]['pair_id'],'domain':r['input']['observations'][0]['instrument_domain']['domain']} for r in rows.values()]
        return {'counts':self.counts,'cases':cases,'arms':ARMS,'summaries':summaries,
                'candidate':self.candidate,'status':self.status,'evaluation':'Sealed: no inputs, labels, requests or predictions exposed.',
                'boundary':'Synthetic draft references. Inspecting this page makes no model calls. No operating threshold is selected.'}

    def case(self,identifier,split='development',arm='structured'):
        if split not in self.records or identifier not in self.records[split] or arm not in ARMS:
            raise ValueError('Unknown task-fit case, arm or accessible split.')
        r=self.records[split][identifier]; key=self.keys[split][identifier]
        partner=next(v for i,v in self.records[split].items() if i!=identifier and self.keys[split][i]['pair_id']==key['pair_id'])
        source=self.saved.get(split,{}); actual=next((x for x in source.get('responses',[]) if x['id']==identifier and x['arm']==arm),None)
        request=body(r,arm,examples(self.directory))
        saved=next((x for x in source.get('requests',[]) if x['id']==identifier and x['arm']==arm),None)
        if saved and saved['body']!=request: raise ValueError('Saved and prepared request differ.')
        local={x['arm']:x for x in self.saved.get('local',{}).get('responses',[]) if x['id']==identifier}
        repeats=[x for x in self.saved.get('repeat',{}).get('responses',[]) if x['id']==identifier and x['arm']==arm]
        return {'record':r,'partner_id':partner['id'],'request':request,'saved_request':saved,'response':actual,
                'trace':packet(r,actual['reading']) if actual and actual['status']=='ok' else None,
                'reference':self.references[split][identifier],'packet_reference':key['labels'],
                'local_controls':local,'repeats':repeats,'split':split,'arm':arm}
