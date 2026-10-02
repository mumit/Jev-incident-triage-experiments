"""Learn or explicitly classify report meaning, then apply a separate policy."""
import json,re
import numpy as np
import sklearn
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from triage_bench.dataset import read_jsonl
from triage_bench.policy import priority
from .interpretation_data import DIRECTORY,DOMAINS,READINGS
from .structured_features import descriptors
from .selection import eligibility
from .transforms import measurement_facts,sha

PARAMETERS={'C':2.0,'max_iter':2000,'random_state':17,'class_weight':'balanced','word_ngrams':[1,2],'character_ngrams':[3,5],'min_df':2,'sublinear_tf':True,'character_analyzer':'char_wb'}


def report_inputs(record):
    return [{'observation_index':o['observation_index'],'text':o['text']} for o in descriptors(record,'combined')['observations']]


def policy_inputs(record):
    p=record['input']
    return {'eligibility':eligibility(p),'measurement_facts':measurement_facts(p),'asset_ids':[o['asset_id'] for o in p['observations']],
            'service_impact':{k:p['service_impact'][k] for k in ['status','affected_sites']},'change_status':p['change_record']['status']}


def pipeline_input(record):
    return {'schema':'experiment-3-report-policy-input-1','reports':report_inputs(record),'policy_inputs':policy_inputs(record),
            'boundary':'Report interpreters see only the normalized report text. Policy receives predicted meanings, declared impact, change status, currentness, paths and asset grouping. No reference annotations enter inference.'}


def apply_policy(record,readings):
    if len(readings)!=len(record['input']['observations']) or [r['observation_index'] for r in readings]!=list(range(len(readings))):raise ValueError('Report interpretations do not join the packet.')
    if any(r['domain'] not in DOMAINS or r['reading'] not in READINGS for r in readings):raise ValueError('Invalid predicted meaning.')
    inputs=policy_inputs(record);rows=[];groups={}
    for r,e,m,asset in zip(readings,inputs['eligibility'],inputs['measurement_facts'],inputs['asset_ids']):
        row={k:r[k] for k in ['observation_index','domain','reading']};row.update(eligible=e['eligible'],freshness=m['freshness_status'],supported_sites=e['supported_site_count'],asset_id=asset);rows.append(row)
        if e['eligible'] and r['domain']!='none':groups.setdefault((r['domain'],asset),set()).add(r['reading'])
    conflicts=[{'domain':d,'asset_id':asset} for (d,asset),states in groups.items() if {'fault','normal'}<=states]
    faults=sorted({d for (d,_),states in groups.items() if 'fault' in states})
    current_recovery=any(r['domain']=='none' and r['reading']=='normal' and r['freshness']=='current' for r in rows)
    owner='noc';check='gather_evidence';insufficient='yes'
    if conflicts:reason='Comparable current fault and normal readings disagree on the same asset/domain.'
    elif len(faults)==1:
        owner=faults[0];check='inspect_radio' if owner=='ran' else 'inspect_'+owner;insufficient='no';reason='One current fault domain has a visible affected-service path.'
    elif len(faults)>1:reason='Multiple current supported fault domains remain; a unique investigating domain is not established.'
    elif inputs['service_impact']['status']=='none' and current_recovery:
        check='monitor';insufficient='no';reason='No current impact and a current normal service-probe interpretation support recovery monitoring.'
    elif inputs['change_status']=='scope_unexplained':check='verify_change';reason='No unique current fault supports a domain; verify the unexplained change scope.'
    else:reason='No current supported fault domain is established. Normal, unknown, stale or unlinked reports do not assign a team.'
    return {'predictions':{'initial_owner':owner,'priority':priority(inputs['service_impact']),'next_check':check,'insufficient_evidence':insufficient},
            'trace':{'observations':rows,'supported_fault_domains':faults,'current_conflicts':conflicts,'reason':reason,
                     'assumption':'These synthetic same-asset/domain instruments are authored as comparable. A service-probe normal reading with no impact represents recovery; thresholds and grouping need specialist review.'}}


def rule_reading(text,index):
    patterns={'transport':r'\b(transport|optical|backhaul|packet)\b','ran':r'\b(radio|antenna|decoding)\b','power':r'\b(power|voltage|supply)\b','core':r'\b(core|subscriber|session)\b'}
    domains=[d for d,p in patterns.items() if re.search(p,text,re.I)];domain=domains[0] if len(domains)==1 else 'none'
    if re.search(r'\b(might|may|could|unconfirmed|inconclusive|suspected)\b|not.*established|cannot determine',text,re.I):reading='unknown';rule='Uncertainty expression'
    elif re.search(r'\b(normal|nominal|healthy|pass|passes)\b|\bnot (failing|rejected)\b|\bnot observed\b',text,re.I):reading='normal';rule='Normal reading or a recognized negation'
    elif re.search(r'\b(failing|failed|failure|failures|absent|rejected|loss)\b',text,re.I):reading='fault';rule='Fault expression without a recognized uncertainty or normal expression'
    else:reading='unknown';rule='No recognized reading expression'
    return {'observation_index':index,'domain':domain,'reading':reading,'rule':rule,'domain_matches':domains}


class ReportClassifier:
    def __init__(self,directory=DIRECTORY):
        from pathlib import Path
        directory=Path(directory);records=read_jsonl(directory/'train.inputs.jsonl');annotations={(r['id'],r['observation_index']):r for r in read_jsonl(directory/'train.observations.jsonl')}
        reports=[(r['id'],o) for r in records for o in report_inputs(r)];texts=[o['text'] for _,o in reports]
        self.words=TfidfVectorizer(ngram_range=(1,2),min_df=2,sublinear_tf=True);self.chars=TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5),min_df=2,sublinear_tf=True)
        x=hstack([self.words.fit_transform(texts),self.chars.fit_transform(texts)],format='csr');self.heads={}
        for field,choices in [('domain',DOMAINS),('reading',READINGS)]:
            targets=[annotations[identifier,o['observation_index']][field] for identifier,o in reports]
            if set(targets)!=set(choices):raise ValueError('Missing report interpretation class.')
            model=LogisticRegression(C=2.0,max_iter=2000,random_state=17,class_weight='balanced');model.fit(x,targets);self.heads[field]=model
        self.metadata={'sklearn_version':sklearn.__version__,'parameters':PARAMETERS,'training_packets':len(records),'training_reports':len(reports),'feature_count':x.shape[1],
                       'training_inputs_sha256':sha((directory/'train.inputs.jsonl').read_bytes()),'training_annotations_sha256':sha((directory/'train.observations.jsonl').read_bytes()),
                       'input_scope':'Observation detail only; asset identities normalized. No impact, paths, timestamps, policy text or packet target decisions.'}

    def matrix(self,texts):return hstack([self.words.transform(texts),self.chars.transform(texts)],format='csr')
    def names(self):return ['word/'+s for s in self.words.get_feature_names_out()]+['char/'+s for s in self.chars.get_feature_names_out()]

    def predict(self,record):
        reports=report_inputs(record);matrix=self.matrix([o['text'] for o in reports]);result=[]
        for i,report in enumerate(reports):
            row={'observation_index':report['observation_index'],'text':report['text'],'probabilities':{}}
            for field,head in self.heads.items():
                p={str(c):float(v) for c,v in zip(head.classes_,head.predict_proba(matrix[i])[0])};row[field]=max(p,key=p.get);row['probabilities'][field]=p
            result.append(row)
        return result

    def inspect(self,text):
        x=self.matrix([text]);names=self.names();fields={}
        for field,head in self.heads.items():
            p=head.predict_proba(x)[0];winner,other=map(int,np.argsort(p)[::-1][:2]);delta=head.coef_[winner]-head.coef_[other];contrib=x.multiply(delta).tocsr()
            values=[{'feature':names[int(i)],'value':float(x[0,i]),'coefficient_difference':float(delta[i]),'contribution':float(v)} for i,v in zip(contrib.indices,contrib.data) if v];values.sort(key=lambda v:abs(v['contribution']),reverse=True)
            offset=float(head.intercept_[winner]-head.intercept_[other]);fields[field]={'selected':str(head.classes_[winner]),'compared_with':str(head.classes_[other]),'probabilities':{str(c):float(v) for c,v in zip(head.classes_,p)},
                 'intercept_difference':offset,'log_odds_margin':offset+sum(v['contribution'] for v in values),'top_contributions':values[:15],'remaining_contribution':sum(v['contribution'] for v in values[15:])}
        return {'vector':{'dimensions':x.shape[1],'nonzero':[{'feature':names[int(i)],'value':float(v)} for i,v in zip(x.indices,x.data) if v]},'fields':fields}
