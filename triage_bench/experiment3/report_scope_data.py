"""Prewritten measured-function development cases; no changes to earlier evidence."""
import copy,json
from pathlib import Path
from triage_bench.dataset import ROOT,read_jsonl,write_jsonl
from triage_bench.policy import VERSION,OPTIONS,priority
from .data import make_pair,decisions,changed_paths
from .interpretation_data import DOMAINS,READINGS
from .transforms import sha

DIRECTORY=ROOT/'data/report-scope-draft'
DECISION={'date':'2026-10-02','decision':'Normal handler reading: successful acceptance is normal for the focal handler; downstream registration completion remains a separate measurement.','status':'user_selected_synthetic_teaching_rule_not_specialist_signoff'}
# Targets below describe the measured function, independently of packet decisions.
CORE=[
 ('intake receipt versus queue malfunction','text','normal','fault',
  'This instrument measures request intake. The handler acknowledges receipt and accepts correctly formed subscriber requests into its queue. This instrument does not measure later registration completion.',
  'This instrument measures request intake. An internal queue malfunction prevents the handler from accepting correctly formed subscriber requests. This instrument does not measure later registration completion.'),
 ('completed registration versus unmeasured finish','text','normal','unknown',
  'This instrument measures completed registration. The transaction trace verifies that subscriber registration completed successfully for the measured requests.',
  'This instrument measures completed registration. Request intake acknowledgements are visible, but no completion trace exists; whether subscriber registration completed is not established.'),
 ('intake scope versus completion scope','text','normal','unknown',
  'This instrument measures request intake. The handler accepts requests; later registration completion is not observed by this instrument.',
  'This instrument measures registration completion. The handler accepts requests; later registration completion is not observed by this instrument.'),
 ('credential gate expected rejection versus malfunction','text','normal','fault',
  'This instrument measures credential validation. The gate rejects invalid credentials and accepts valid credentials exactly as specified; the measured validation function operates correctly.',
  'This instrument measures credential validation. An internal validator malfunction rejects valid credentials that should be accepted; the measured validation function fails.'),
 ('batch admission partial malfunction','text','normal','fault',
  'This instrument measures batch admission. The handler admits every correctly formed request in the measured batch as specified. Registration completion is outside this measurement.',
  'This instrument measures batch admission. The handler admits some correctly formed requests, but an internal malfunction prevents admission of the remaining valid requests. Registration completion is outside this measurement.'),
 ('receipt trace certainty','text','normal','unknown',
  'This instrument measures request intake. Receipt events verify that the handler accepted the measured requests. Later service completion remains outside this measurement.',
  'This instrument measures request intake. Receipt events are missing; whether the handler accepted the measured requests is unconfirmed. Later service completion remains outside this measurement.'),
 ('comparable intake contradiction','conflict','fault','normal',
  'Two comparable instruments measure the same intake function under the same conditions. This instrument records an internal handler malfunction that prevents acceptance of valid requests.',
  'Two comparable instruments measure the same intake function under the same conditions. This instrument verifies that the handler accepts the valid requests as specified.'),
 ('different function comparison','mixed_scope','fault','normal',
  'This instrument measures registration completion. An internal completion-worker malfunction prevents the valid subscriber registrations from completing.',
  'This instrument measures request intake. The handler accepts valid requests as specified; registration completion is outside this measurement.'),
]
TRANSFER={
 'transport':('egress delivery function','The interface delivers every measured frame to the next hop as specified.','An internal egress malfunction drops the measured frames before the next hop.','whether the interface delivered the measured frames'),
 'ran':('decode acknowledgement function','The decoder produces valid decode acknowledgements for the measured radio blocks as specified.','An internal decoder malfunction prevents acknowledgement of the measured radio blocks.','whether the decoder acknowledged the measured radio blocks'),
 'power':('regulated output function','The regulator maintains its measured output within the declared operating range.','An internal regulator malfunction prevents the measured output from reaching its declared operating range.','whether the regulator maintained the measured output')}


def build_rows():
    specs=[('core '+name,kind,'core',a,b,sa,sb) for name,kind,sa,sb,a,b in CORE]
    for d,(function,normal,fault,uncertain) in TRANSFER.items():
        prefix='This instrument measures '+function+'. '
        suffix=' Wider service completion is outside this measurement.'
        specs += [(d+' component function versus wider transaction','text',d,prefix+normal+suffix,prefix+fault+suffix,'normal','fault'),
                  (d+' component receipt certainty','text',d,prefix+normal+suffix,prefix+'The trace is missing; '+uncertain+' is not established.'+suffix,'normal','unknown'),
                  (d+' same function contradiction','conflict',d,'Two comparable instruments measure the same '+function+' under the same conditions. '+fault,'Two comparable instruments measure the same '+function+' under the same conditions. '+normal,'fault','normal')]
    records,keys,annotations=[],[],[]
    for family,kind,domain,a,b,state_a,state_b in specs:
        for index in range(2):
            prefix='Independent '+domain+' measurement at {asset}: '
            pair,targets=make_pair((family,'conflict' if kind=='conflict' else 'arrival',domain,prefix+a,'mesh' if index else 'split','degraded'),'development',index)
            impact=pair[0]['input']['service_impact'];normal=decisions('noc',impact,True);fault=decisions(domain,impact)
            meanings=[[{'domain':domain,'reading':state_a}],[{'domain':domain,'reading':state_b}]]
            if kind=='conflict':
                for r in pair:r['input']['observations'][1]['detail']=(prefix+b).format(asset=r['input']['observations'][1]['asset_id'])
                meanings=[[{'domain':domain,'reading':'fault'},{'domain':domain,'reading':'normal'}] for _ in pair];answers=[normal,fault]
                if index:
                    for r in pair:r['input']['observations'].reverse()
                    for m in meanings:m.reverse()
                    for k in targets:k['changed_path']='input.observations[0].measured_at'
            elif kind=='mixed_scope':
                for r in pair:
                    second=copy.deepcopy(r['input']['observations'][0]);second['detail']=(prefix+b).format(asset=second['asset_id']);r['input']['observations'].append(second)
                pair[1]['input']['observations'][0]['observed_at']=pair[0]['input']['observations'][0]['observed_at']
                pair[1]['input']['observations'][1]['observed_at']=pair[0]['input']['observations'][1]['observed_at']
                pair[1]['input']['observations'][1]['detail']=(prefix+'This instrument measures registration completion. It verifies that the valid subscriber registrations completed successfully under the same conditions as the other completion instrument.').format(asset=pair[1]['input']['observations'][1]['asset_id'])
                meanings=[[{'domain':'core','reading':'fault'},{'domain':'core','reading':'normal'}] for _ in pair];answers=[fault,normal]
                for k in targets:k['changed_path']='input.observations[1].detail'
            else:
                pair[1]['input']['observations'][0]['observed_at']=pair[0]['input']['observations'][0]['observed_at'];pair[1]['input']['observations'][0]['detail']=(prefix+b).format(asset=pair[1]['input']['observations'][0]['asset_id'])
                answers=[fault if s=='fault' else normal for s in [state_a,state_b]]
                for k in targets:k['changed_path']='input.observations[0].detail'
            for r,k,meanings_for_record,answer in zip(pair,targets,meanings,answers):
                r['id']=r['id'].replace('NS3-','NSS-');k.update(id=r['id'],pair_id=k['pair_id'].replace('NS3-','NSS-'),labels=copy.deepcopy(answer),accepted_answers={f:[v] for f,v in answer.items()},control=kind,known_policy_gap=kind=='mixed_scope' and r['id'].endswith('-a'),pair_kind='decision_change' if answers[0]!=answers[1] else 'invariance')
                k['label_rationale']='Draft measured-function reference. Success of request intake does not establish transaction completion; expected validation behavior is normal, while an explicit internal malfunction is a fault. Only current faults with a visible affected-service path assign their domain. Contradictions require the same measured function; success at intake does not contradict a completion fault. The unchanged policy cannot represent that last distinction.'
                for oi,m in enumerate(meanings_for_record):annotations.append({'id':r['id'],'observation_index':oi,**m,'review_status':'draft_not_specialist_reviewed','rationale':'Prewritten reading of the explicitly stated measured function; service impact and packet disposition remain separate.'})
            records+=pair;keys+=targets
    return records,keys,annotations


def build(directory=DIRECTORY):
    directory=Path(directory)
    if directory.exists():raise ValueError('Choose a new report-scope data directory.')
    records,keys,annotations=build_rows()
    for name,rows in [('inputs',records),('labels',keys),('observations',annotations)]:write_jsonl(directory/('development.'+name+'.jsonl'),rows)
    manifest={'schema':'report-scope-data-1','operator':'Northstar Telecom','synthetic':True,'reference_status':'draft_not_specialist_reviewed','evaluation_status':'development_only_no_held_out_set','human_decision':DECISION,'records':len(records),'reports':len(annotations),'families':len({k['incident_family_id'] for k in keys}),'pairs':len(records)//2,'known_policy_gaps':[k['id'] for k in keys if k['known_policy_gap']],'training':'Reuse frozen original/broader report training only for ML controls; no new training or development tuning.','construction':'New family names and measured-function descriptions; shared packet/pair templates and explicit domain prefixes limit independence and realism.','sha256':{p.name:sha(p.read_bytes()) for p in sorted(directory.glob('*.jsonl'))}}
    (directory/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');validate(directory);return manifest


def validate(directory=DIRECTORY):
    directory=Path(directory);m=json.loads((directory/'manifest.json').read_text());expected={'development.'+k+'.jsonl' for k in ['inputs','labels','observations']}
    if set(m['sha256'])!=expected or any(sha((directory/n).read_bytes())!=h for n,h in m['sha256'].items()):raise ValueError('Report-scope data fingerprints differ.')
    rows=read_jsonl(directory/'development.inputs.jsonl');keys=read_jsonl(directory/'development.labels.jsonl');ann=read_jsonl(directory/'development.observations.jsonl');by_id={k['id']:k for k in keys};pairs={}
    if len(rows)!=len(by_id) or set(by_id)!={r['id'] for r in rows} or len({r['id'] for r in rows})!=len(rows):raise ValueError('Packet/reference IDs differ or repeat.')
    coverage={(r['id'],i) for r in rows for i in range(len(r['input']['observations']))}
    if len(ann)!=len(coverage) or {(a['id'],a['observation_index']) for a in ann}!=coverage or any(a['domain'] not in DOMAINS or a['reading'] not in READINGS or a['review_status']!='draft_not_specialist_reviewed' for a in ann):raise ValueError('Report reference coverage differs.')
    for r in rows:
        k=by_id[r['id']]
        if set(r)!={'id','input','policy_version'} or r['policy_version']!=VERSION or set(r['input'])!={'operator','ticket','service_impact','change_record','decision_timestamp','observations','topology'} or r['input']['operator']!='Northstar Telecom' or k['review_status']!='draft_not_specialist_reviewed' or k['split']!='development':raise ValueError('Invalid public packet/reference.')
        impact=r['input']['service_impact'];topology=r['input']['topology']
        if set(k['labels'])!=set(OPTIONS) or any(v not in OPTIONS[f] for f,v in k['labels'].items()) or k['labels']['priority']!=priority(impact) or impact['affected_sites']!=len(set(impact['affected_site_ids'])) or not set(impact['affected_site_ids'])<=set(topology['nodes']):raise ValueError('Invalid impact or decision keys.')
        if any(set(o)!={'asset_id','detail','measured_at','observed_at','source','valid_for_minutes'} or o['asset_id'] not in topology['nodes'] for o in r['input']['observations']):raise ValueError('Invalid observation boundary.')
        if any(k['accepted_answers'][f]!=[v] for f,v in k['labels'].items()):raise ValueError('Accepted answers differ.')
        pairs.setdefault(k['pair_id'],[]).append(r)
    for pair in pairs.values():
        pairkeys=[by_id[r['id']] for r in pair]
        if len(pair)!=2 or changed_paths(pair[0]['input'],pair[1]['input'])!=[pairkeys[0]['changed_path']] or pairkeys[0]['changed_path']!=pairkeys[1]['changed_path'] or pairkeys[0]['incident_family_id']!=pairkeys[1]['incident_family_id'] or any(k['pair_kind']!=('invariance' if pairkeys[0]['labels']==pairkeys[1]['labels'] else 'decision_change') for k in pairkeys):raise ValueError('Expected one declared pair intervention.')
    ids=set(by_id);families={k['incident_family_id'] for k in keys}
    for p in (ROOT/'data').rglob('*.labels.jsonl'):
        if p.parent in {directory,DIRECTORY}:continue
        old=read_jsonl(p)
        if ids & {k['id'] for k in old} or families & {k['incident_family_id'] for k in old}:raise ValueError('Earlier family or packet reused.')
    if len(rows)!=m['records'] or len(ann)!=m['reports'] or len(pairs)!=m['pairs'] or len(families)!=m['families'] or m['human_decision']!=DECISION or m['known_policy_gaps']!=[k['id'] for k in keys if k['known_policy_gap']]:raise ValueError('Manifest counts or declared policy gaps differ.')
    return {k:m[k] for k in ['records','reports','families','pairs','known_policy_gaps']}
