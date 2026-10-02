"""Inspect the saved training intervention, common evaluation inputs and margins."""
import json,threading,uuid
from pathlib import Path
from triage_bench.dataset import ROOT,read_jsonl
from .wording_data import ARMS,validate
from .wording_ml import run,verify
from .structured_features import input_bundle
from .transforms import dependency_facts,measurement_facts,sha
from .data import changed_paths

def diagnostic_summary(rows,keys):
    if not rows:return None
    result={}
    groups={'path routing':'Service path','sample expiry':'Measurement time','comparable reports':'Current versus stale nominal report','method synonym':'Method synonym',
            'service excerpt':'Incomplete inventory','delivery gap':'Missing inventory','verification cycle':'Recovery','zone extent':'Maintenance scope'}
    for arm in ARMS:
        scores={}
        for suffix,label in groups.items():
            selected=[k for k in keys.values() if k['incident_family_id'].endswith(suffix)]
            scores[label]={'correct':sum(rows[arm][k['id']]['predictions']==k['labels'] for k in selected),'packets':len(selected)}
        pairs={}
        for key in keys.values():
            if key['incident_family_id'].endswith('method synonym'):pairs.setdefault(key['pair_id'],[]).append(key['id'])
        result[arm]={'controls':scores,'synonym_pairs':len(pairs),'synonym_agreement':sum(rows[arm][a]['predictions']==rows[arm][b]['predictions'] for a,b in pairs.values()),
                     'synonym_pairs_correct':sum(all(rows[arm][i]['predictions']==keys[i]['labels'] for i in pair) for pair in pairs.values())}
    return result

class WordingStudy:
    def __init__(self,root=ROOT):
        self.root=Path(root);self.directory=self.root/'data/experiment-3-wording-draft';validate(self.directory)
        self.manifest=json.loads((self.directory/'manifest.json').read_text());self.records={};self.keys={}
        for split in ['train','development']:
            self.records[split]={a:{r['id']:r for r in read_jsonl(self.directory/a/(split+'.inputs.jsonl'))} for a in ARMS}
            self.keys[split]={k['id']:k for k in read_jsonl(self.directory/'baseline'/(split+'.labels.jsonl'))}
        self.lock=threading.Lock();self.summary=None;self.rows={};self.explanations={};self.vectors={};self.status='Prepared wording study; no saved predictions.'
        for path in sorted((self.root/'runs/experiment-3-wording').glob('*/summary.json'),key=lambda p:p.stat().st_mtime,reverse=True):
            try:self.load(path);break
            except (OSError,ValueError,KeyError,TypeError):self.status='Saved wording evidence differs or is incomplete; scores are unavailable.'

    def load(self,path):
        summary,rows,explanations=verify(path,self.root,self.directory)
        self.summary={**summary,'run_id':path.parent.name};self.rows=rows;self.explanations=explanations
        self.vectors={a:{r['id']:r['vector'] for r in read_jsonl(path.parent/(a+'.features.jsonl'))} for a in ARMS}
        self.status='Saved training-wording comparison; draft references.'

    def catalog(self):
        return {'comparison':'wording','manifest':self.manifest,'variants':ARMS,'model':'Logistic regression','pilot':self.summary,'status':self.status,
                'diagnostics':diagnostic_summary(self.rows,self.keys['development']),'changes':self.summary['changes']['coupled'] if self.summary else None,'hosted_pilot':None,'jev_status':'not_run','hosted_status':'No Jev calls; combined feature construction and classifier settings stay frozen.',
                'cases':{s:[{'id':r['id'],'family':self.keys[s][r['id']]['incident_family_id'],'pair_id':self.keys[s][r['id']]['pair_id'],'pair_kind':self.keys[s][r['id']]['pair_kind']} for r in records['baseline'].values()] for s,records in self.records.items()}}

    def case(self,identifier,variant='baseline',split='development'):
        if variant not in ARMS or split not in self.records or identifier not in self.records[split][variant]:raise ValueError('Unknown wording case or arm.')
        record=self.records[split][variant][identifier];key=self.keys[split][identifier]
        partner=next(r for r in self.records[split][variant].values() if r['id']!=identifier and self.keys[split][r['id']]['pair_id']==key['pair_id'])
        bundle=input_bundle(record,'combined');vector=self.vectors.get(variant,{}).get(identifier) if split=='development' else None
        return {'record':record,'paired':partner,'draft_reference':key,'changed_paths':changed_paths(record['input'],partner['input']),
                'dependency_facts':dependency_facts(record['input']),'measurement_facts':measurement_facts(record['input']),
                'packets':{a:input_bundle(self.records[split][a][identifier],'combined') for a in ARMS},'request':{**bundle,'training_arm':variant,'fitted_vector':vector},
                'state_sha256':sha(bundle['text_state'].encode()),'input_sha256':sha(json.dumps(bundle,sort_keys=True).encode()),
                'outputs':{a:rows.get(identifier) if split=='development' else None for a,rows in self.rows.items()},'hosted_outputs':{},'hosted_saved_requests':{},'jev_status':'not_run',
                'training_wordings':{a:[r['detail'] for r in self.records[split][a][identifier]['input']['observations']] for a in ARMS} if split=='train' else None,
                'explanation':self.explanations.get(variant,{}).get(identifier) if split=='development' else None}

    def run_local(self):
        if not self.lock.acquire(blocking=False):raise ValueError('A local wording comparison is already running.')
        try:
            dest=self.root/'runs/experiment-3-wording'/('development-'+uuid.uuid4().hex[:12]);run(dest,self.directory);self.load(dest/'summary.json');return self.catalog()
        finally:self.lock.release()
