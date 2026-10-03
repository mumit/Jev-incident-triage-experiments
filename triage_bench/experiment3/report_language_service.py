"""Read-only inspection of matched wording and hosted report-policy evidence."""
import json
from pathlib import Path
from triage_bench.dataset import ROOT,read_jsonl
from .report_language_data import validate,ARMS as TRAINING_ARMS
from .report_language_trial import verify,ARMS
from .report_language_hosted import verify as verify_hosted,ARMS as HOSTED,report_body
from .interpretation_model import report_inputs,pipeline_input
from .selection import body as direct_body
from .structured_features import input_bundle
from .transforms import dependency_facts,measurement_facts
from .data import changed_paths

class ReportLanguageStudy:
    def __init__(self,root=ROOT):
        self.root=Path(root);self.directory=self.root/'data/report-language-draft';validate(self.directory)
        self.manifest=json.loads((self.directory/'manifest.json').read_text());self.records={};self.keys={};self.annotations={}
        for split in ['train','development']:
            self.records[split]={r['id']:r for r in read_jsonl(self.directory/'narrow'/(split+'.inputs.jsonl'))};self.keys[split]={r['id']:r for r in read_jsonl(self.directory/'narrow'/(split+'.labels.jsonl'))};self.annotations[split]={}
            for a in read_jsonl(self.directory/'narrow'/(split+'.observations.jsonl')):self.annotations[split].setdefault(a['id'],[]).append(a)
        self.training={a:{r['id']:r for r in read_jsonl(self.directory/a/'train.inputs.jsonl')} for a in TRAINING_ARMS}
        self.local=None;self.hosted=None;self.replay=None;self.rows={};self.inspections={};self.bridge_explanations={};self.bridge_vectors={};self.requests=[];self.responses=[];self.status=[]
        for kind,folder in [('local','report-language'),('hosted','report-language-jev')]:
            paths=sorted((self.root/'runs'/folder).glob('*/summary.json'),key=lambda p:p.stat().st_mtime,reverse=True)
            for p in paths:
                try:
                    if kind=='local':
                        s,rows=verify(p,self.directory,self.root);self.local={**s,'run_id':p.parent.name};self.rows.update(rows)
                        self.inspections={a:{r['id']:r['reports'] for r in read_jsonl(p.parent/(a+'.inspections.jsonl'))} for a in TRAINING_ARMS}
                        self.bridge_explanations={r['id']:r['fields'] for r in read_jsonl(p.parent/'bridge.explanations.jsonl')};self.bridge_vectors={r['id']:r['vector'] for r in read_jsonl(p.parent/'bridge.features.jsonl')}
                    else:
                        s,rows,requests,responses=verify_hosted(p,self.directory,self.root);self.hosted={**s,'run_id':p.parent.name};self.rows.update(rows);self.requests=requests;self.responses=responses
                    break
                except (OSError,ValueError,KeyError,TypeError):self.status.append('Saved '+kind+' evidence differs; predictions unavailable.')
        if not self.local:self.status.append('No saved local predictions. Inputs and references remain available.')
        if not self.hosted:self.status.append('Jev has no saved responses on this pack.')

        paths=sorted((self.root/'runs/report-language-replay').glob('*/summary.json'),key=lambda p:p.stat().st_mtime,reverse=True)
        for p in paths:
            try:
                from .report_language_repeat import verify as verify_replay
                summary=verify_replay(p,self.root/'runs/report-language-jev/development-2026-10-02-v1')
                requests=read_jsonl(p.parent/'requests.jsonl')
                self.replay={**summary,'run_id':p.parent.name,'texts':[{'id':q['id'],'observation_index':q['observation_index'],'text':q['body']['state'].removeprefix('Report text only:\n')} for q in requests if q['repetition']==1]}
                break
            except (OSError,ValueError,KeyError,TypeError):self.status.append('Saved diagnostic replay differs; repeat results unavailable.')

    def catalog(self):
        return {'manifest':self.manifest,'arms':{**ARMS,**HOSTED},'local':self.local,'hosted':self.hosted,'replay':self.replay,'status':' '.join(self.status) or 'Saved local and hosted evidence verifies.',
                'cases':{s:[{'id':r['id'],'family':self.keys[s][r['id']]['incident_family_id'],'pair_id':self.keys[s][r['id']]['pair_id'],'control':self.keys[s][r['id']].get('control','training')} for r in records.values()] for s,records in self.records.items()}}

    def case(self,identifier,split='development',arm='broad',report_index=0):
        if split not in self.records or identifier not in self.records[split] or arm not in {**ARMS,**HOSTED}:raise ValueError('Unknown report-language packet or arm.')
        r=self.training[arm][identifier] if split=='train' and arm in TRAINING_ARMS else self.records[split][identifier];key=self.keys[split][identifier]
        partner=next(x for x in self.records[split].values() if x['id']!=identifier and self.keys[split][x['id']]['pair_id']==key['pair_id'])
        reports=report_inputs(r)
        if isinstance(report_index,bool) or not isinstance(report_index,int) or not 0<=report_index<len(reports):raise ValueError('Unknown report index.')
        if arm=='jev_direct':request=direct_body(r,'selected')
        elif arm=='jev_reading':request=report_body(reports[report_index]['text'])
        elif arm=='bridge':request=input_bundle(r,'combined')
        else:request=pipeline_input(r)
        outputs={a:rows.get(identifier) for a,rows in self.rows.items()} if split=='development' else {}
        saved_req=next((q for q in self.requests if q['id']==identifier and q['arm']==arm and q['observation_index']==(report_index if arm=='jev_reading' else None)),None) if split=='development' else None
        response=next((q for q in self.responses if q['id']==identifier and q['arm']==arm and q['observation_index']==(report_index if arm=='jev_reading' else None)),None) if split=='development' else None
        if saved_req and saved_req['body']!=request:raise ValueError('Prepared and recorded request differ.')
        return {'record':r,'paired':partner,'changed_paths':changed_paths(self.records[split][identifier]['input'],partner['input']),'draft_reference':key,'report_references':self.annotations[split][identifier],
                'reports':reports,'training_reports':{a:report_inputs(self.training[a][identifier]) for a in TRAINING_ARMS} if split=='train' else None,
                'dependency_facts':dependency_facts(r['input']),'measurement_facts':measurement_facts(r['input']),
                'outputs':outputs,'request':request,'saved_request':saved_req,'saved_response':response,
                'report_inspections':self.inspections.get(arm,{}).get(identifier) if split=='development' else None,
                'packet_explanation':self.bridge_explanations.get(identifier) if split=='development' and arm=='bridge' else None,
                'packet_vector':self.bridge_vectors.get(identifier) if split=='development' and arm=='bridge' else None}
