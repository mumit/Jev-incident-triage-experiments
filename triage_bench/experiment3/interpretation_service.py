"""Inspect report inputs, predicted meanings, policy traces and separate references."""
import json,threading,uuid
from pathlib import Path
from triage_bench.dataset import ROOT,read_jsonl
from .interpretation_data import validate
from .interpretation_trial import ARMS,run,verify,inputs
from .interpretation_model import pipeline_input
from .structured_features import input_bundle
from .transforms import dependency_facts,measurement_facts,sha
from .data import changed_paths

class InterpretationStudy:
    def __init__(self,root=ROOT):
        self.root=Path(root);self.directory=self.root/'data/experiment-3-interpretation-draft';validate(self.directory)
        self.manifest=json.loads((self.directory/'manifest.json').read_text());self.records={};self.keys={};self.annotations={}
        for split in ['train','development']:
            self.records[split]={r['id']:r for r in read_jsonl(self.directory/(split+'.inputs.jsonl'))};self.keys[split]={k['id']:k for k in read_jsonl(self.directory/(split+'.labels.jsonl'))};self.annotations[split]={}
            for a in read_jsonl(self.directory/(split+'.observations.jsonl')):self.annotations[split].setdefault(a['id'],[]).append(a)
        self.lock=threading.Lock();self.summary=None;self.rows={};self.vectors={};self.explanations={};self.inspections={};self.status='Prepared interpretation comparison; no saved predictions.'
        for path in sorted((self.root/'runs/experiment-3-interpretation').glob('*/summary.json'),key=lambda p:p.stat().st_mtime,reverse=True):
            try:self.load(path);break
            except (OSError,ValueError,KeyError,TypeError):self.status='Saved interpretation evidence differs; predictions unavailable.'

    def load(self,path):
        summary,rows=verify(path,self.root,self.directory);self.summary={**summary,'run_id':path.parent.name};self.rows=rows
        self.vectors={a:{r['id']:r['vector'] for r in read_jsonl(path.parent/(a+'.features.jsonl'))} for a in ['baseline','packet']}
        self.explanations={a:{r['id']:r['fields'] for r in read_jsonl(path.parent/(a+'.explanations.jsonl'))} for a in ['baseline','packet']}
        self.inspections={r['id']:r['reports'] for r in read_jsonl(path.parent/'reading.inspections.jsonl')};self.status='Saved report/policy comparison; draft references.'

    def catalog(self):
        return {'comparison':'interpretation','manifest':self.manifest,'variants':ARMS,'model_labels':{'baseline':'ML · frozen candidate','packet':'ML · matched packet','reading':'Report ML → policy','reading_rules':'Report rules → policy'},
                'pilot':self.summary,'status':self.status,'changes':self.summary['changes'] if self.summary else None,'hosted_pilot':None,'jev_status':'not_run','hosted_status':'No Jev calls. Report classification is a learned or explicit semantic step, separate from input-only fact calculation.',
                'cases':{s:[{'id':r['id'],'family':self.keys[s][r['id']]['incident_family_id'],'pair_id':self.keys[s][r['id']]['pair_id'],'pair_kind':self.keys[s][r['id']]['pair_kind']} for r in records.values()] for s,records in self.records.items()}}

    def case(self,identifier,variant='packet',split='development'):
        if variant not in ARMS or split not in self.records or identifier not in self.records[split]:raise ValueError('Unknown interpretation packet or arm.')
        record=self.records[split][identifier];key=self.keys[split][identifier];partner=next(r for r in self.records[split].values() if r['id']!=identifier and self.keys[split][r['id']]['pair_id']==key['pair_id'])
        bundle=inputs(record,variant);vector=self.vectors.get(variant,{}).get(identifier) if split=='development' else None
        output={a:r.get(identifier) if split=='development' else None for a,r in self.rows.items()}
        return {'record':record,'paired':partner,'draft_reference':key,'changed_paths':changed_paths(record['input'],partner['input']),
                'dependency_facts':dependency_facts(record['input']),'measurement_facts':measurement_facts(record['input']),
                'packets':{a:inputs(record,a) for a in ARMS},'request':{**bundle,'inference_arm':variant,'fitted_vector':vector,'fitted_report_vectors':[{'observation_index':o['observation_index'],'vector':o['vector']} for o in self.inspections.get(identifier,[])] if split=='development' and variant=='reading' else None},
                'state_sha256':sha(json.dumps(bundle,sort_keys=True).encode()),'input_sha256':sha(json.dumps(bundle,sort_keys=True).encode()),'outputs':output,'hosted_outputs':{},'hosted_saved_requests':{},'jev_status':'not_run',
                'explanation':self.explanations.get(variant,{}).get(identifier) if split=='development' else None,
                'report_inputs':pipeline_input(record)['reports'],'report_inspections':self.inspections.get(identifier) if split=='development' and variant=='reading' else None,
                'report_references':self.annotations[split][identifier],'pipeline':output.get(variant) if variant in {'reading','reading_rules'} else None}

    def run_local(self):
        if not self.lock.acquire(blocking=False):raise ValueError('An interpretation comparison is already running.')
        try:
            out=self.root/'runs/experiment-3-interpretation'/('development-'+uuid.uuid4().hex[:12]);run(out,self.directory);self.load(out/'summary.json');return self.catalog()
        finally:self.lock.release()
