"""Inspect saved local inputs, sparse feature vectors and fitted score margins."""
import json,threading,uuid
from pathlib import Path
from triage_bench.dataset import ROOT,read_jsonl
from .structured_data import validate
from .structured_features import ARMS,input_bundle
from .structured_ml import run,verify
from .transforms import dependency_facts,measurement_facts,sha
from .data import changed_paths


def compare_to_baseline(rows,keys):
    if not rows:return None
    baseline=rows['baseline'];result={}
    for arm in ARMS:
        fixed=[];lost=[];new_fields={f:[] for f in ['initial_owner','next_check','insufficient_evidence']}
        for identifier,key in keys.items():
            if identifier not in baseline or identifier not in rows[arm]:raise ValueError('Incomplete matched prediction coverage.')
            before=baseline[identifier]['predictions'];after=rows[arm][identifier]['predictions'];accepted=key['accepted_answers']
            b=all(before[f] in accepted[f] for f in accepted);a=all(after[f] in accepted[f] for f in accepted)
            if a and not b:fixed.append(identifier)
            if b and not a:lost.append(identifier)
            for field in new_fields:
                if before[field] in accepted[field] and after[field] not in accepted[field]:new_fields[field].append(identifier)
        result[arm]={'packets_fixed':fixed,'packets_lost':lost,'newly_wrong_fields':new_fields}
    return result

class StructuredStudy:
    def __init__(self,root=ROOT):
        self.root=Path(root);self.directory=self.root/'data/experiment-3-structured-ml-draft';validate(self.directory)
        self.manifest=json.loads((self.directory/'manifest.json').read_text());self.records={};self.keys={}
        for split in ['train','development']:
            self.records[split]={r['id']:r for r in read_jsonl(self.directory/(split+'.inputs.jsonl'))}
            self.keys[split]={k['id']:k for k in read_jsonl(self.directory/(split+'.labels.jsonl'))}
        self.lock=threading.Lock();self.summary=None;self.rows={};self.explanations={};self.vectors={};self.status='No saved structured ML comparison. Prepared inputs remain inspectable.'
        for path in sorted((self.root/'runs/experiment-3-structured-ml').glob('*/summary.json'),key=lambda p:p.stat().st_mtime,reverse=True):
            try:self.load(path);break
            except (OSError,ValueError,KeyError,TypeError):self.status='Saved local evidence differs or is incomplete; scores are unavailable.'

    def load(self,path):
        summary,rows,explanations=verify(path,self.root,self.directory)
        vectors={arm:{r['id']:r['vector'] for r in read_jsonl(path.parent/(arm+'.features.jsonl'))} for arm in ARMS}
        self.summary={**summary,'run_id':path.parent.name};self.rows=rows;self.explanations=explanations;self.vectors=vectors
        self.status='Saved matched structured ML comparison; draft references.'

    def catalog(self):
        return {'comparison':'structured','manifest':self.manifest,'variants':ARMS,'model':'Logistic regression','pilot':self.summary,'status':self.status,
                'changes':compare_to_baseline(self.rows,self.keys['development']),'hosted_pilot':None,'jev_status':'not_run','hosted_status':'Jev stays frozen; this comparison makes no hosted calls.',
                'cases':{s:[{'id':r['id'],'family':self.keys[s][r['id']]['incident_family_id'],'pair_id':self.keys[s][r['id']]['pair_id'],'pair_kind':self.keys[s][r['id']]['pair_kind']} for r in records.values()] for s,records in self.records.items()}}

    def case(self,identifier,variant='baseline',split='development'):
        if variant not in ARMS or split not in self.records or identifier not in self.records[split]:raise ValueError('Unknown ML case or arm.')
        record=self.records[split][identifier];key=self.keys[split][identifier];partner=next(r for r in self.records[split].values() if r['id']!=identifier and self.keys[split][r['id']]['pair_id']==key['pair_id'])
        bundle=input_bundle(record,variant);outputs={a:rows.get(identifier) if split=='development' else None for a,rows in self.rows.items()}
        vector=self.vectors.get(variant,{}).get(identifier) if split=='development' else None
        return {'record':record,'paired':partner,'draft_reference':key,'changed_paths':changed_paths(record['input'],partner['input']),
                'dependency_facts':dependency_facts(record['input']),'measurement_facts':measurement_facts(record['input']),
                'packets':{a:input_bundle(record,a) for a in ARMS},'request':{**bundle,'fitted_vector':vector},'state_sha256':sha(bundle['text_state'].encode()),
                'input_sha256':sha(json.dumps(bundle,sort_keys=True).encode()),'outputs':outputs,'hosted_outputs':{},'hosted_saved_requests':{},'jev_status':'not_run',
                'explanation':self.explanations.get(variant,{}).get(identifier) if split=='development' else None}

    def run_local(self):
        if not self.lock.acquire(blocking=False):raise ValueError('A local feature comparison is already running.')
        try:
            dest=self.root/'runs/experiment-3-structured-ml'/('development-'+uuid.uuid4().hex[:12]);run(dest,self.directory);self.load(dest/'summary.json');return self.catalog()
        finally:self.lock.release()
