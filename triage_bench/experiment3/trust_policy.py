"""Check explicit declaration consistency without classifying operation outcomes."""
import copy,re
from .declared_data import declaration_fact
from .metadata_policy import apply_metadata_policy
DOMAINS={'core','transport','ran','power'}
VERSION='northstar-declaration-consistency-1'

def header_fact(text):
    # A declaration is a schema header, not a technical vocabulary match.
    values=re.findall(r'(?<!\w)Instrument domain\s*:\s*([^\.\n]+)(?:\.|\n|$)',text,re.IGNORECASE)
    if not values:return {'state':'missing','domain':'none'}
    if len(values)!=1:return {'state':'ambiguous','domain':'none'}
    value=values[0].strip().lower()
    if value in DOMAINS:return {'state':'declared','domain':value}
    if value in {'unavailable','missing','unknown'}:return {'state':'missing','domain':'none'}
    return {'state':'ambiguous','domain':'none'}

def effective_readings(record,readings):
    result=copy.deepcopy(readings)
    for row in result:
        row['raw_interpreter_domain']=row['domain']
        row['domain']=declaration_fact(record['input']['observations'][row['observation_index']])['domain']
        row.get('probabilities',{}).pop('domain',None)
        row.get('provider_confidence',{}).pop('domain',None)
        row['domain_source']='supplied structured declaration; no classification'
    return result

def apply_trust_policy(record,readings,guarded=True):
    result=apply_metadata_policy(record,readings)
    rows=result['trace']['observations']
    fault_assets={r['asset_id'] for r in rows if r['eligible'] and r['reading']=='fault'}
    facts=[];blocks=[]
    for row,observation in zip(rows,record['input']['observations']):
        structured=declaration_fact(observation);prose=header_fact(observation['detail'])
        conflict=structured['state']=='declared' and prose['state']=='declared' and structured['domain']!=prose['domain']
        relevant=row['eligible'] and row['asset_id'] in fault_assets
        fact={'observation_index':row['observation_index'],'structured':structured,'prose_header':prose,'conflict':conflict,'eligible':row['eligible'],'fault_bearing_asset':row['asset_id'] in fault_assets,'blocks_ownership':guarded and conflict and relevant,'exclusion':None if relevant else 'Ineligible report or no eligible fault on this asset.'}
        facts.append(fact)
        if fact['blocks_ownership']:blocks.append(row['observation_index'])
    result['trace']['declaration_guard']={'version':VERSION,'enabled':guarded,'facts':facts,'blocked_observations':blocks,'before':copy.deepcopy(result['predictions']),'boundary':'Compare valid explicit enum declarations on eligible fault-bearing assets. Do not infer domain or operation reading from technical vocabulary. Missing/ambiguous structured domains remain none under the frozen base policy.'}
    if blocks:
        result['predictions'].update(initial_owner='noc',next_check='gather_evidence',insufficient_evidence='yes')
        result['trace']['reason']='Current linked evidence contains conflicting structured and prose domain declarations on a fault-bearing asset; retain NOC until resolved.'
    return result
