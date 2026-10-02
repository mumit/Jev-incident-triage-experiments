"""Matched logistic classifiers with observation-bound structured feature blocks."""
import json
from pathlib import Path
import time
import numpy as np
import sklearn
from scipy.sparse import hstack,csr_matrix
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from triage_bench.dataset import ROOT,read_jsonl,write_jsonl
from triage_bench.evaluate import evaluate
from triage_bench.experiments import structured_features as impact_features
from triage_bench.policy import OPTIONS
from triage_bench.runner import baseline as rules
from .structured_data import DIRECTORY,validate
from .structured_features import ARMS,descriptors,buckets,input_bundle
from .transforms import sha

PARAMETERS={'C':2.0,'max_iter':2000,'random_state':17,'class_weight':'balanced','word_ngrams':[1,2],'character_ngrams':[3,5],'min_df':2,'sublinear_tf':True,'character_analyzer':'char_wb','priority_features':'impact_only'}
SOURCES=['triage_bench/experiment3/'+name for name in ['structured_data.py','structured_features.py','structured_ml.py','data.py','transforms.py']]+['triage_bench/'+name for name in ['policy.py','experiments.py','runner.py','evaluate.py']]


class FeatureSpace:
    def __init__(self,records):
        states=[descriptors(r,'baseline')['state'] for r in records]
        texts=[row['text'] for r in records for row in descriptors(r,'baseline')['observations']]
        def words():return TfidfVectorizer(ngram_range=(1,2),min_df=2,sublinear_tf=True)
        def chars():return TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5),min_df=2,sublinear_tf=True)
        self.words,self.chars,self.obs_words,self.obs_chars=words(),chars(),words(),chars()
        self.words.fit(states);self.chars.fit(states);self.obs_words.fit(texts);self.obs_chars.fit(texts)
        self.impact=DictVectorizer();self.impact.fit([impact_features(r['input']) for r in records])
        self.counts={}
        for arm in ARMS:
            if arm!='baseline':
                vectorizer=DictVectorizer();vectorizer.fit([descriptors(r,arm)['counts'] for r in records]);self.counts[arm]=vectorizer

    def impact_matrix(self,records):return self.impact.transform([impact_features(r['input']) for r in records])

    def matrix(self,records,arm):
        info=[descriptors(r,arm) for r in records];states=[d['state'] for d in info]
        parts=[self.words.transform(states),self.chars.transform(states),self.impact_matrix(records)]
        if arm!='baseline':
            parts.append(self.counts[arm].transform([d['counts'] for d in info]))
            width=len(self.obs_words.get_feature_names_out())+len(self.obs_chars.get_feature_names_out())
            for bucket in buckets(arm):
                rows=[]
                for d in info:
                    texts=[o['text'] for o in d['observations'] if o['bucket']==bucket]
                    block=hstack([self.obs_words.transform(texts),self.obs_chars.transform(texts)],format='csr').sum(axis=0) if texts else np.zeros((1,width))
                    rows.append(csr_matrix(block))
                from scipy.sparse import vstack
                parts.append(vstack(rows,format='csr'))
        return hstack(parts,format='csr')

    def names(self,arm,priority=False):
        impact=['impact/'+str(s) for s in self.impact.get_feature_names_out()]
        if priority:return impact
        names=['text/word/'+s for s in self.words.get_feature_names_out()]+['text/char/'+s for s in self.chars.get_feature_names_out()]+impact
        if arm!='baseline':
            names+=['facts/'+str(s) for s in self.counts[arm].get_feature_names_out()]
            observation=['word/'+s for s in self.obs_words.get_feature_names_out()]+['char/'+s for s in self.obs_chars.get_feature_names_out()]
            names += [f'observation/{bucket}/{name}' for bucket in buckets(arm) for name in observation]
        return names


class StructuredClassifier:
    def __init__(self,arm,directory=DIRECTORY,space=None):
        if arm not in ARMS:raise ValueError('Unknown ML arm.')
        self.arm=arm;directory=Path(directory);records=read_jsonl(directory/'train.inputs.jsonl');keys={k['id']:k for k in read_jsonl(directory/'train.labels.jsonl')}
        if set(keys)!={r['id'] for r in records}:raise ValueError('Training IDs differ.')
        start=time.perf_counter();self.space=space or FeatureSpace(records);semantic=self.space.matrix(records,arm);impact=self.space.impact_matrix(records);self.heads={}
        for field,choices in OPTIONS.items():
            targets=[keys[r['id']]['labels'][field] for r in records]
            if set(targets)!=set(choices):raise ValueError('Missing training class: '+field)
            head=LogisticRegression(C=2.0,max_iter=2000,random_state=17,class_weight='balanced');head.fit(impact if field=='priority' else semantic,targets);self.heads[field]=head
        self.metadata={'arm':arm,'parameters':PARAMETERS,'training_records':len(records),'training_families':len({k['incident_family_id'] for k in keys.values()}),
                       'training_inputs_sha256':sha((directory/'train.inputs.jsonl').read_bytes()),'training_labels_sha256':sha((directory/'train.labels.jsonl').read_bytes()),
                       'sklearn_version':sklearn.__version__,'training_seconds':time.perf_counter()-start,'semantic_feature_count':semantic.shape[1],
                       'calibration':'Uncalibrated fitted probabilities; provisional references.'}

    def predict(self,record):
        matrix=self.space.matrix([record],self.arm);impact=self.space.impact_matrix([record]);predictions={};probabilities={}
        for field,head in self.heads.items():
            dist={str(c):float(p) for c,p in zip(head.classes_,head.predict_proba(impact if field=='priority' else matrix)[0])}
            predictions[field]=max(dist,key=dist.get);probabilities[field]=dist
        return {'id':record['id'],'status':'ok','predictions':predictions,'probabilities':probabilities,
                'input_sha256':sha(json.dumps(input_bundle(record,self.arm),sort_keys=True).encode())}

    def vector(self,record):
        def named(matrix,names):
            x=matrix.tocsr();return {'dimensions':x.shape[1],'nonzero': [{'feature':names[int(i)],'value':float(v)} for i,v in zip(x.indices,x.data) if v]}
        return {'semantic':named(self.space.matrix([record],self.arm),self.space.names(self.arm)),
                'priority':named(self.space.impact_matrix([record]),self.space.names(self.arm,True))}

    def explain(self,record,field='initial_owner',limit=20):
        if field not in OPTIONS:raise ValueError('Unknown decision field.')
        x=self.space.impact_matrix([record]) if field=='priority' else self.space.matrix([record],self.arm)
        head=self.heads[field];prob=head.predict_proba(x)[0];order=np.argsort(prob)[::-1];winner,other=map(int,order[:2])
        coefs=head.coef_;intercept=head.intercept_
        if len(head.classes_)==2:coefs=np.vstack([-coefs[0]/2,coefs[0]/2]);intercept=np.array([-intercept[0]/2,intercept[0]/2])
        delta=coefs[winner]-coefs[other];contrib=x.multiply(delta).tocsr();names=self.space.names(self.arm,field=='priority')
        values=[{'feature':names[int(i)],'value':float(x[0,i]),'coefficient_difference':float(delta[i]),'contribution':float(v)} for i,v in zip(contrib.indices,contrib.data) if v]
        values.sort(key=lambda v:abs(v['contribution']),reverse=True)
        offset=float(intercept[winner]-intercept[other]);margin=offset+sum(v['contribution'] for v in values)
        return {'field':field,'selected':str(head.classes_[winner]),'compared_with':str(head.classes_[other]),'probabilities':{str(c):float(p) for c,p in zip(head.classes_,prob)},
                'intercept_difference':offset,'log_odds_margin':margin,'top_contributions':values[:limit],
                'remaining_contribution':sum(v['contribution'] for v in values[limit:]),
                'interpretation':'Feature contributions explain the fitted score against the runner-up, not physical causation. Log-odds include all features and the intercept.'}


def run(output,directory=DIRECTORY):
    directory=Path(directory);output=Path(output);validate(directory)
    if output.exists():raise ValueError('Local runs are immutable; choose a new directory.')
    output.mkdir(parents=True);records=read_jsonl(directory/'development.inputs.jsonl');train=read_jsonl(directory/'train.inputs.jsonl')
    write_jsonl(output/'inputs.jsonl',records);write_jsonl(output/'labels.jsonl',read_jsonl(directory/'development.labels.jsonl'))
    plan={'schema':'experiment-3-structured-ml-1','reference_status':'draft_not_specialist_reviewed','split':'development','jev_status':'not_run',
          'training_records':len(train),'development_records':len(records),'data_sha256':json.loads((directory/'manifest.json').read_text())['sha256'],
          'parameters':PARAMETERS,'arms':list(ARMS),'source_sha256':{name:sha((ROOT/name).read_bytes()) for name in SOURCES},
          'execution':'One matched fit per arm; train-only vocabulary and classifiers; no development tuning, filtering or hosted calls.'}
    (output/'protocol.json').write_text(json.dumps(plan,indent=2)+'\n');summary={**plan,'approaches':{}};space=FeatureSpace(train)
    for arm in ARMS:
        model=StructuredClassifier(arm,directory,space);rows=[model.predict(r) for r in records];write_jsonl(output/(arm+'.jsonl'),rows)
        summary['approaches'][arm]={'training':model.metadata,'metrics':evaluate(output/'labels.jsonl',output/(arm+'.jsonl'),inputs_path=output/'inputs.jsonl')}
        write_jsonl(output/(arm+'.features.jsonl'),[{'id':r['id'],'vector':model.vector(r)} for r in records])
        write_jsonl(output/(arm+'.explanations.jsonl'),[{'id':r['id'],'fields':{f:model.explain(r,f) for f in OPTIONS}} for r in records])
    write_jsonl(output/'rules.jsonl',[{'id':r['id'],'status':'ok','predictions':rules(r['input'])} for r in records])
    summary['approaches']['rules']={'metrics':evaluate(output/'labels.jsonl',output/'rules.jsonl',inputs_path=output/'inputs.jsonl')}
    summary['evidence_sha256']={p.name:sha(p.read_bytes()) for p in sorted(output.glob('*.jsonl'))}
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');return summary


def verify(path,root=ROOT,directory=DIRECTORY):
    path=Path(path);root=Path(root);directory=Path(directory);validate(directory);saved=json.loads(path.read_text());plan=json.loads((path.parent/'protocol.json').read_text())
    if saved['schema']!='experiment-3-structured-ml-1' or saved['data_sha256']!=json.loads((directory/'manifest.json').read_text())['sha256']:raise ValueError('Local protocol or data differ.')
    if any(saved.get(k)!=v for k,v in plan.items()):raise ValueError('Local plan differs.')
    if any(sha((root/name).read_bytes())!=digest for name,digest in saved['source_sha256'].items()):raise ValueError('Recorded source differs.')
    if set(saved['approaches'])!={*ARMS,'rules'}:raise ValueError('Unexpected approaches.')
    for name,digest in saved['evidence_sha256'].items():
        if Path(name).name!=name or sha((path.parent/name).read_bytes())!=digest:raise ValueError('Recorded evidence differs.')
    for name,source in [('inputs.jsonl','development.inputs.jsonl'),('labels.jsonl','development.labels.jsonl')]:
        if sha((path.parent/name).read_bytes())!=saved['data_sha256'][source]:raise ValueError('Evaluation data differ.')
    rows={};explanations={}
    for arm,result in saved['approaches'].items():
        if evaluate(path.parent/'labels.jsonl',path.parent/(arm+'.jsonl'),inputs_path=path.parent/'inputs.jsonl')!=result['metrics']:raise ValueError('Scores differ from evidence.')
        if arm!='rules':
            meta=result['training']
            if meta['parameters']!=PARAMETERS or any(meta['training_'+k+'_sha256']!=saved['data_sha256']['train.'+k+'.jsonl'] for k in ['inputs','labels']):raise ValueError('Training recipe differs.')
            explanations[arm]={r['id']:r['fields'] for r in read_jsonl(path.parent/(arm+'.explanations.jsonl'))}
            expected={r['id']:r for r in read_jsonl(directory/'development.inputs.jsonl')}
            for r in read_jsonl(path.parent/(arm+'.jsonl')):
                if r['input_sha256']!=sha(json.dumps(input_bundle(expected[r['id']],arm),sort_keys=True).encode()):raise ValueError('Input construction differs.')
        rows[arm]={r['id']:r for r in read_jsonl(path.parent/(arm+'.jsonl'))}
    return saved,rows,explanations
