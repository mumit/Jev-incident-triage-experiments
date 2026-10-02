"""Bind each observation's text to input-only dependency/freshness categories."""
import re
from .transforms import dependency_facts,measurement_facts,request_body

ARMS={'baseline':'Text baseline','dependency':'Structured dependency','measurement':'Structured freshness','combined':'Both structured features'}
RELATIONS=['supported','excluded','unknown']
FRESHNESS=['current','stale','unknown']


def descriptors(record,arm):
    if arm not in ARMS:raise ValueError('Unknown structured ML arm.')
    packet=record['input'];deps=dependency_facts(packet);ages=measurement_facts(packet)
    nodes=set((packet.get('topology') or {}).get('nodes',[]))|{o.get('asset_id') for o in packet['observations']}
    identifiers=sorted((n for n in nodes if isinstance(n,str) and n),key=len,reverse=True)
    rows=[]
    for index,(obs,dep,age) in enumerate(zip(packet['observations'],deps,ages)):
        assert dep['observation_index']==age['observation_index']==index
        relation='supported' if dep['supported_site_count']>0 else 'excluded' if dep['relation']=='no_listed_sites_depend' else 'unknown'
        freshness=age['freshness_status']
        # Asset identity supports the graph calculation, not a learned category.
        text=obs['detail']
        for identifier in identifiers:text=re.sub(r'(?<!\w)'+re.escape(identifier)+r'(?!\w)','asset',text)
        bucket=relation if arm=='dependency' else freshness if arm=='measurement' else relation+'/'+freshness if arm=='combined' else None
        rows.append({'observation_index':index,'text':text,'relationship':relation,'freshness':freshness,'bucket':bucket})
    counts={}
    if arm!='baseline':
        for row in rows:counts['observation_count/'+row['bucket']]=counts.get('observation_count/'+row['bucket'],0)+1
    return {'arm':arm,'state':request_body(record,'baseline')['state'],'counts':counts,'observations':rows,
            'method':'All observations retained. Input-only categories bind each observation text to a channel; no malfunction classification or reference decision is calculated.'}


def buckets(arm):
    return RELATIONS if arm=='dependency' else FRESHNESS if arm=='measurement' else [r+'/'+a for r in RELATIONS for a in FRESHNESS] if arm=='combined' else []


def input_bundle(record,arm):
    from triage_bench.experiments import structured_features as impact_features
    d=descriptors(record,arm)
    return {'schema':'experiment-3-ml-input-1','arm':arm,'text_state':d['state'],
            'impact_features':impact_features(record['input']),'structured_counts':d['counts'],
            'observation_channels':[{'observation_index':o['observation_index'],'text':o['text'],'channel':o['bucket']} for o in d['observations']] if arm!='baseline' else [],
            'feature_construction':'Shared training-only text vocabulary plus impact; selected arm adds counts and observation text channels. All observations stay available. Priority uses impact only.'}
