"""New written training/development families for a matched local feature study."""
import copy
import json
from pathlib import Path
from triage_bench.dataset import ROOT, read_jsonl, write_jsonl
from .data import make_pair, validate as validate_base
from .question_trial import DECISION
from .transforms import sha

DIRECTORY = ROOT/'data/experiment-3-structured-ml-draft'
# Family names and prose are independent of earlier packs. Mechanisms and templates
# remain shared teaching constructs; family separation does not imply realism.
DOMAINS = {
 'transport': ('packet fabric', 'forwarding fabric trace',
  'Independent transport diagnostics at {asset} detect persistent packet forwarding drops. Current service checks confirm impact.',
  'A transport receive-channel test at {asset} records interrupted delivery. Independently tested service requests fail.',
  'An independent transport test at {asset} reports normal packet delivery under the same conditions.'),
 'ran': ('baseband decode', 'sector receive chain',
  'Independent radio diagnostics at {asset} report failed baseband decoding. Current service checks confirm impact.',
  'A radio receive-chain diagnostic at {asset} detects repeated decode failures during independently verified degradation.',
  'An independent radio test at {asset} reports normal receive processing under the same conditions.'),
 'power': ('equipment supply branch', 'cabinet output circuit',
  'Independent power diagnostics at {asset} record failed equipment supply. Current service checks confirm impact.',
  'A power output-circuit meter at {asset} records absent DC supply during independently verified service loss.',
  'An independent power test at {asset} reports normal equipment supply under the same conditions.'),
 'core': ('session control worker', 'shared subscriber transaction',
  'Independent core diagnostics at {asset} record rejected session-control requests across separately checked access paths.',
  'A shared core transaction trace at {asset} detects failed subscriber requests across independently checked access paths.',
  'An independent core test at {asset} reports normal subscriber request processing under the same conditions.')}


def specs(split):
    result=[]
    for domain,(train_name,dev_name,train_text,dev_text,_) in DOMAINS.items():
        name,text=(train_name,train_text) if split=='train' else (dev_name,dev_text)
        for kind,suffix in [('dependency','service association'),('age','measurement validity'),('conflict','instrument disagreement')]:
            result.append((name+' '+suffix,kind,domain,text,'chain' if split=='train' else 'mesh','degraded' if domain in {'ran','core'} else 'outage'))
    result += ([
      ('unmapped amplifier inventory','partial','noc','A transport amplifier diagnostic at {asset} reports a hardware failure. Independent service checks confirm impact.','fork','outage'),
      ('access restoration interval','recovery','noc','Independent service probes confirm complete recovery throughout the observation interval. No current domain fault remains.','fan','none'),
      ('partial work order scope','maintenance','noc','A maintenance record describes limited cabinet work while current impact extends beyond its declared scope. No domain fault has been diagnosed.','chain','outage'),
      ('decode monitor delivery interval','arrival','ran','A radio receive diagnostic at {asset} reports failed decoding. Independent service probes confirm degradation.','fan','degraded')
    ] if split=='train' else [
      ('incomplete decoder service map','visible_partial','ran','A radio decoder diagnostic at {asset} reports failed decoding during independently verified degradation.','mesh','degraded'),
      ('unavailable supply service map','missing_topology','power','A power feeder diagnostic at {asset} records failed supply during independently verified service loss.','split','outage'),
      ('verified customer probe recovery','recovery','noc','Independent customer service probes pass throughout the recovery observation interval. No active domain malfunction is reported.','mesh','none'),
      ('cabinet work footprint mismatch','maintenance','noc','Current service loss extends beyond a cabinet work footprint. No independent domain diagnosis explains the full impact.','split','outage')])
    return result


def build(directory=DIRECTORY):
    directory=Path(directory)
    if directory.exists(): raise ValueError('Choose a new structured ML data directory.')
    manifest={'version':'experiment-3-structured-ml-draft-1','operator':'Northstar Telecom','synthetic':True,
              'reference_status':'draft_not_specialist_reviewed','evaluation_status':'development_only_no_held_out_set',
              'human_decision':{'decision':DECISION,'scope':'Synthetic teaching rule; not specialist signoff'},
              'construction':'New family prose; shared pair templates and four repeated domain mechanisms. Correlated variations are not independent incidents.',
              'telemetry_assumption':'15-minute inclusive validity; comparable-instrument conflict disposition remains provisional.','splits':{}}
    for split,count in [('train',3),('development',2)]:
        records,keys=[],[]
        for spec in specs(split):
            family,kind,owner,text,layout,status=spec
            for index in range(count):
                actual=(family,'dependency' if kind=='visible_partial' else kind,owner,text,layout,status)
                pair,labels=make_pair(actual,split,index)
                if kind=='age':
                    # Training includes stale and unknown times. The development
                    # stale condition is just beyond the same declared boundary.
                    pair[1]['input']['observations'][0]['measured_at']=None if index==1 else pair[1]['input']['observations'][0]['measured_at']
                    if split=='development' and index==0:
                        from datetime import timedelta
                        from triage_bench.dataset import stamp
                        from .transforms import timestamp
                        pair[1]['input']['observations'][0]['measured_at']=stamp(timestamp(pair[1]['input']['decision_timestamp'])-timedelta(minutes=15,seconds=1))
                if kind=='conflict':
                    for r in pair:
                        asset=r['input']['observations'][0]['asset_id']
                        r['input']['observations'][1]['detail']=DOMAINS[owner][4].format(asset=asset)
                    labels[1]['labels']['initial_owner']=owner
                    labels[1]['labels']['next_check']='inspect_radio' if owner=='ran' else 'inspect_'+owner
                    labels[1]['accepted_answers']={f:[v] for f,v in labels[1]['labels'].items()}
                    for label in labels:label['label_rationale']='Two current independent reports of the same domain disagree. A stale nominal report cannot contradict a current supported fault; retain NOC on the current conflict.'
                    # Keep pair intervention unchanged while varying report order.
                    if index%2:
                        for r in pair:r['input']['observations'].reverse()
                        for label in labels:label['changed_path']='input.observations[0].measured_at'
                if kind=='visible_partial':
                    for r in pair:
                        t=r['input']['topology'];first_site=r['input']['service_impact']['affected_site_ids'][0]
                        # Keep only one affected-service branch in both maps.
                        original=copy.deepcopy(pair[0]['input']['topology']) if r is pair[1] else copy.deepcopy(t)
                        t.update(original);t['edges']=[e for e in original['edges'] if e[0] not in r['input']['service_impact']['affected_site_ids'] or e[0]==first_site]
                    pair[0]['input']['topology']['coverage']='partial';pair[1]['input']['topology']['coverage']='complete'
                    labels[1]['labels']=copy.deepcopy(labels[0]['labels'])
                    for label in labels:
                        label['accepted_answers']={f:[v] for f,v in label['labels'].items()};label['changed_path']='input.topology.coverage';label['pair_kind']='invariance'
                        label['label_rationale']='One affected site has a visible path in both maps. Partial coverage leaves other relationships unknown; one supported path meets the synthetic teaching rule.'
                for r,k in zip(pair,labels):
                    r['id']=r['id'].replace('NS3-','NSM-');k['id']=r['id'];k['pair_id']=k['pair_id'].replace('NS3-','NSM-')
                records+=pair;keys+=labels
        write_jsonl(directory/(split+'.inputs.jsonl'),records);write_jsonl(directory/(split+'.labels.jsonl'),keys)
        manifest['splits'][split]={'records':len(records),'families':len(specs(split)),'pairs':len(records)//2}
    manifest['sha256']={p.name:sha(p.read_bytes()) for p in sorted(directory.glob('*.jsonl'))}
    (directory/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');validate(directory);return manifest


def validate(directory=DIRECTORY):
    counts=validate_base(directory)
    keys=[k for s in ['train','development'] for k in read_jsonl(Path(directory)/(s+'.labels.jsonl'))]
    old=[]
    for folder in ['experiment-3-draft','experiment-3-question-draft','experiment-3-conflict-draft','experiment-3-selection-draft','experiment-3-robustness-draft']:
        for p in (ROOT/'data'/folder).glob('*.labels.jsonl'):old+=read_jsonl(p)
    if {k['id'] for k in keys}&{k['id'] for k in old} or {k['incident_family_id'] for k in keys}&{k['incident_family_id'] for k in old}:
        raise ValueError('Earlier family or packet reused.')
    return counts
