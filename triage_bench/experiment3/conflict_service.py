"""Read-only per-repetition inspection; repeated incidents remain distinct from responses."""
import copy,json
from pathlib import Path
from triage_bench.dataset import ROOT,read_jsonl
from .conflict_trial import validate,verify,REPEATS
from .question_trial import verify as verify_questions
from .question_service import QuestionStudy

class ConflictStudy(QuestionStudy):
    def __init__(self,root=ROOT):
        self.root=Path(root);self.directory=self.root/'data/experiment-3-conflict-draft';self.manifest=validate(self.directory)
        self.records={r['id']:r for r in read_jsonl(self.directory/'development.inputs.jsonl')}
        self.keys={k['id']:k for k in read_jsonl(self.directory/'development.labels.jsonl')}
        self.summary=None;self.rows={};self.requests={};self.master=None;self.repeats={};self.status='No saved repeated conflict comparison.'
        for path in sorted((self.root/'runs/experiment-3-conflicts').glob('*/summary.json'),key=lambda p:p.stat().st_mtime,reverse=True):
            try:
                master=verify(path,self.root,self.directory);repeats={}
                for item in master['runs']:
                    n=item['repetition'];s,rows,requests=verify_questions(path.parent/f'repetition-{n}'/'summary.json',self.root,self.directory)
                    s['run_id']=path.parent.name+f'/repetition-{n}';repeats[n]=(s,rows,requests)
                self.master,self.repeats=master,repeats;self.status='Saved repeated conflict comparison: '+master['status']+'; draft references.';break
            except (OSError,ValueError,KeyError,TypeError):self.status='Saved repeat evidence differs or is incomplete; scores are unavailable.'

    def snapshot(self,repetition):
        if isinstance(repetition,bool) or not isinstance(repetition,int) or not 1<=repetition<=REPEATS:raise ValueError('Unknown repetition.')
        view=copy.copy(self);view.summary,view.rows,view.requests=self.repeats.get(repetition,(None,{},{}));return view

    def catalog(self,repetition=1):
        result=QuestionStudy.catalog(self.snapshot(repetition));result.update(comparison='conflicts',repetition=repetition,
              repetitions=REPEATS,repeat_summary=self.master,hosted_status=self.status)
        return result

    def case(self,identifier,variant='original',split='development',repetition=1):
        result=QuestionStudy.case(self.snapshot(repetition),identifier,variant,split)
        result['repeated_outputs']={str(n):{a:rows.get(a,{}).get(identifier) for a in ['original','precedence']}
                                   for n,(_,rows,_) in self.repeats.items()}
        return result
