"""Use supplied instrument scope for comparability without interpreting report text."""
import copy
from .interpretation_model import apply_policy

FUNCTIONS={'request_intake','registration_completion','frame_forwarding','egress_delivery','radio_decoding','timing_alignment','regulated_output','battery_runtime'}
VERSION='northstar-metadata-grouping-1'

def scope_fact(observation):
    value=observation.get('measurement_scope')
    if value is None:return {'state':'missing','function':None,'comparison_context':None}
    if not isinstance(value,dict):return {'state':'malformed','function':None,'comparison_context':None}
    if value.get('status')!='declared':return {'state':'ambiguous','function':None,'comparison_context':None}
    function=value.get('function');context=value.get('comparison_context')
    if not isinstance(function,str) or function not in FUNCTIONS or not isinstance(context,str) or not context.strip():return {'state':'incomplete','function':None,'comparison_context':None}
    return {'state':'declared','function':function,'comparison_context':context}

def apply_metadata_policy(record,readings):
    result=copy.deepcopy(apply_policy(record,readings));trace=result['trace'];rows=trace['observations'];groups={}
    for row,observation in zip(rows,record['input']['observations']):
        row['measurement_scope']=scope_fact(observation)
        if row['eligible'] and row['domain']!='none' and row['measurement_scope']['state']=='declared':
            s=row['measurement_scope'];groups.setdefault((row['domain'],row['asset_id'],s['function'],s['comparison_context']),set()).add(row['reading'])
    fault_assets={(r['domain'],r['asset_id']) for r in rows if r['eligible'] and r['domain']!='none' and r['reading']=='fault'}
    unresolved=[r['observation_index'] for r in rows if r['eligible'] and (r['domain'],r['asset_id']) in fault_assets and r['measurement_scope']['state']!='declared']
    conflicts=[dict(domain=d,asset_id=a,function=f,comparison_context=c) for (d,a,f,c),states in groups.items() if {'fault','normal'}<=states]
    trace.update(policy_version=VERSION,current_conflicts=conflicts,unresolved_scope_reports=unresolved,
                 grouping=[dict(domain=d,asset_id=a,function=f,comparison_context=c,readings=sorted(v)) for (d,a,f,c),v in groups.items()],
                 assumption='Scope and condition identifiers are supplied by a synthetic instrumentation schema. Same identifiers mean comparable measurement conditions; distinct declared identifiers mean distinct conditions. Metadata trust and comparability need operational validation.')
    # With no eligible fault, preserve recovery, change checks and other baseline behavior.
    if not fault_assets:return result
    p=result['predictions'];p.update(initial_owner='noc',next_check='gather_evidence',insufficient_evidence='yes')
    if unresolved:trace['reason']='An eligible report on a fault-bearing asset/domain has missing, ambiguous or incomplete measurement scope; retain NOC.'
    elif conflicts:trace['reason']='Current fault and normal readings disagree on the same asset, domain, function and declared comparison context.'
    elif len(trace['supported_fault_domains'])==1:
        owner=trace['supported_fault_domains'][0];p.update(initial_owner=owner,next_check='inspect_radio' if owner=='ran' else 'inspect_'+owner,insufficient_evidence='no');trace['reason']='One current linked fault domain remains; supplied function/context metadata shows no comparable normal contradiction.'
    else:trace['reason']='Multiple current supported fault domains remain; a unique investigating domain is not established.'
    return result
