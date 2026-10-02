"""Written report interpretations and packet decisions in separate draft keys."""
import copy,json
from pathlib import Path
from datetime import timedelta
from triage_bench.dataset import ROOT,read_jsonl,write_jsonl,stamp
from .data import make_pair,decisions,validate as validate_pairs
from .transforms import timestamp,sha

DIRECTORY=ROOT/'data/experiment-3-interpretation-draft'
DOMAIN_NAMES={'transport':('forwarding buffer','optical frame stream'),'ran':('antenna decode monitor','radio symbol receiver'),'power':('equipment feed circuit','cabinet voltage probe'),'core':('subscriber session engine','registration request handler')}
# These tuples are authored observation meanings, not packet decision labels.
TRAIN_TEXT={
 'transport':('packet forwarding is failing','packet forwarding is not failing; independent checks pass','packet forwarding might be failing; the diagnosis is unconfirmed'),
 'ran':('radio decoding is failing','radio decoding is not failing; independent checks pass','radio decoding might be failing; the diagnosis is unconfirmed'),
 'power':('equipment supply is failing','equipment supply is not failing; independent checks pass','equipment supply might be failing; the diagnosis is unconfirmed'),
 'core':('subscriber session processing is failing','subscriber session processing is not failing; independent checks pass','subscriber session processing might be failing; the diagnosis is unconfirmed')}
DEV_TEXT={
 'transport':('packet loss is present; independent service probes confirm interruption','packet loss was not observed; independent delivery probes pass','packet loss is suspected; the measurement is inconclusive'),
 'ran':('receive decoding failures are present; independent service probes confirm degradation','receive decoding failures were not observed; independent receive checks pass','receive decoding failures are suspected; the measurement is inconclusive'),
 'power':('equipment voltage is absent; independent service probes confirm interruption','equipment voltage is normal; the proposed supply fault was not observed','equipment voltage loss is suspected; the measurement is inconclusive'),
 'core':('subscriber requests are rejected across independently checked access paths','subscriber requests are not rejected; independent transaction checks pass','subscriber request rejection is suspected; the measurement is inconclusive')}
READINGS=['fault','normal','unknown'];DOMAINS=[*DOMAIN_NAMES,'none']


def specifications(split):
    out=[]
    for domain,names in DOMAIN_NAMES.items():
        name=names[0 if split=='train' else 1]
        if split=='train':
            for state in READINGS:
                for kind in ['dependency','age']:out.append((name+' '+state+' '+kind,domain,state,kind))
        else:
            for kind in ['dependency','age','conflict','negation','uncertainty','missing_topology']:out.append((name+' '+kind,domain,'fault',kind))
        if split=='train':out.append((name+' comparable instruments',domain,'fault','conflict'))
    out += [('probe recovery interval' if split=='train' else 'customer recovery confirmation','none','normal','recovery'),
            ('unexplained cabinet work' if split=='train' else 'work footprint discrepancy','none','unknown','maintenance'),
            ('unclassified instrument notice' if split=='train' else 'unclassified sensor assessment','none','unknown','arrival')]
    return out


def report_text(domain,state,split,index):
    if domain=='none':return 'Independent service probes pass throughout the recovery interval.' if state=='normal' else 'An unclassified instrument reading is unconfirmed. No domain diagnosis is available.'
    phrase=(TRAIN_TEXT if split=='train' else DEV_TEXT)[domain][READINGS.index(state)]
    return 'Independent '+domain+(' tests' if index%2==0 else ' diagnostics')+' at {asset} report that '+phrase+'.'


def build(directory=DIRECTORY):
    directory=Path(directory)
    if directory.exists():raise ValueError('Choose a new interpretation data directory.')
    manifest={'schema':'experiment-3-interpretation-data-1','operator':'Northstar Telecom','synthetic':True,'reference_status':'draft_not_specialist_reviewed',
              'evaluation_status':'development_only_no_held_out_set','annotation_construction':'Domain and reading are written report meanings. They are not inferred from triage keys; stale or disconnected faults retain fault annotations.',
              'policy_assumptions':'15-minute inclusive validity; current same-asset/domain reports are comparable in these written cases. Recovery requires no impact and current normal service probes. No operational claims.',
              'splits':{}}
    for split,count in [('train',3),('development',2)]:
        records,keys,annotations=[],[],[]
        for family,domain,state,kind in specifications(split):
            for index in range(count):
                text=report_text(domain,state,split,index)
                if kind=='maintenance':text='Current impact extends beyond the documented work footprint. No domain diagnosis has been established.'
                status='none' if kind=='recovery' else 'degraded' if domain in {'ran','core'} else 'outage'
                actual_kind='arrival' if kind in {'negation','uncertainty'} else kind
                owner=domain if state=='fault' and domain!='none' else 'noc'
                pair,answers=make_pair((family,actual_kind,owner,text,'chain' if split=='train' else 'mesh' if index==0 else 'split',status),split,index)
                meanings=[[{'domain':domain,'reading':state}],[{'domain':domain,'reading':state}]]
                if kind=='age':pair[1]['input']['observations'][0]['measured_at']=None if index%2 else stamp(timestamp(pair[1]['input']['decision_timestamp'])-timedelta(minutes=15,seconds=1))
                if state!='fault' and kind in {'dependency','age'}:
                    for key in answers:key['labels']=decisions('noc',pair[0]['input']['service_impact'],True)
                if kind=='conflict':
                    for record in pair:record['input']['observations'][1]['detail']=report_text(domain,'normal',split,index+1).format(asset=record['input']['observations'][1]['asset_id'])
                    meanings=[m+[{'domain':domain,'reading':'normal'}] for m in meanings]
                    answers[1]['labels']=decisions(domain,pair[1]['input']['service_impact'])
                    if index%2:
                        for record in pair:record['input']['observations'].reverse()
                        meanings=[list(reversed(m)) for m in meanings]
                        for key in answers:key['changed_path']='input.observations[0].measured_at'
                if kind in {'negation','uncertainty'}:
                    other='normal' if kind=='negation' else 'unknown'
                    pair[1]['input']['observations'][0]['observed_at']=pair[0]['input']['observations'][0]['observed_at']
                    pair[1]['input']['observations'][0]['detail']=report_text(domain,other,split,index).format(asset=pair[1]['input']['observations'][0]['asset_id'])
                    meanings[1][0]['reading']=other;answers[1]['labels']=decisions('noc',pair[1]['input']['service_impact'],True)
                    for key in answers:key['changed_path']='input.observations[0].detail'
                for record,key,meaning in zip(pair,answers,meanings):
                    record['id']=record['id'].replace('NS3-','NSI-');key['id']=record['id'];key['pair_id']=key['pair_id'].replace('NS3-','NSI-')
                    key['accepted_answers']={f:[v] for f,v in key['labels'].items()}
                    key['pair_kind']='decision_change' if answers[0]['labels']!=answers[1]['labels'] else 'invariance'
                    key['label_rationale']='The selected packet reference is a prewritten synthetic teaching decision. The pair changes '+key['changed_path']+'. Current supported faults justify their domain; normal, unknown, stale, unlinked or conflicting readings retain NOC. Recovery monitors; unexplained work checks its scope.'
                    for oi,m in enumerate(meaning):annotations.append({'id':record['id'],'observation_index':oi,**m,'review_status':'draft_not_specialist_reviewed','rationale':'Written report meaning, independent of service relationship and measurement age.'})
                records+=pair;keys+=answers
        for name,rows in [('inputs',records),('labels',keys),('observations',annotations)]:write_jsonl(directory/(split+'.'+name+'.jsonl'),rows)
        manifest['splits'][split]={'records':len(records),'families':len(specifications(split)),'pairs':len(records)//2}
        manifest.setdefault('observation_counts',{})[split]=len(annotations)
    manifest['sha256']={p.name:sha(p.read_bytes()) for p in sorted(directory.glob('*.jsonl'))}
    (directory/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');validate(directory);return manifest


def validate(directory=DIRECTORY):
    directory=Path(directory);manifest=json.loads((directory/'manifest.json').read_text())
    # Reuse the frozen single-field-pair validator without changing its schema.
    base=copy.deepcopy(manifest);base['sha256']={k:v for k,v in manifest['sha256'].items() if not k.endswith('.observations.jsonl')}
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        tmp=Path(tmp)
        for name in base['sha256']:(tmp/name).write_bytes((directory/name).read_bytes())
        (tmp/'manifest.json').write_text(json.dumps(base));validate_pairs(tmp)
    expected={s+'.'+k+'.jsonl' for s in ['train','development'] for k in ['inputs','labels','observations']}
    if set(manifest['sha256'])!=expected:raise ValueError('Unexpected interpretation data files.')
    for name,digest in manifest['sha256'].items():
        if sha((directory/name).read_bytes())!=digest:raise ValueError('Interpretation checksum differs.')
    new_ids=set();new_families=set()
    for split in ['train','development']:
        records=read_jsonl(directory/(split+'.inputs.jsonl'));annotations=read_jsonl(directory/(split+'.observations.jsonl'))
        identities={(r['id'],i) for r in records for i in range(len(r['input']['observations']))}
        if len(annotations)!=len(identities) or {(a['id'],a['observation_index']) for a in annotations}!=identities:raise ValueError('Annotation coverage differs.')
        if any(set(a)!={'id','observation_index','domain','reading','review_status','rationale'} or a['domain'] not in DOMAINS or a['reading'] not in READINGS or a['review_status']!='draft_not_specialist_reviewed' for a in annotations):raise ValueError('Invalid observation interpretation.')
        if manifest['observation_counts'][split]!=len(annotations):raise ValueError('Annotation counts differ.')
        new_ids|={r['id'] for r in records};new_families|={k['incident_family_id'] for k in read_jsonl(directory/(split+'.labels.jsonl'))}
    for folder in (ROOT/'data').glob('experiment-3*'):
        if folder.resolve() in {directory.resolve(),DIRECTORY.resolve()}:continue
        for p in folder.rglob('*.labels.jsonl'):
            old=read_jsonl(p)
            if new_ids & {k['id'] for k in old} or new_families & {k['incident_family_id'] for k in old}:raise ValueError('Earlier interpretation family reused.')
    return {**{s:manifest['splits'][s]['records'] for s in ['train','development']},'observations':manifest['observation_counts']}
