"""Matched training-word interventions and new provisional development families."""
import copy
import json
import re
from pathlib import Path
from triage_bench.dataset import ROOT, read_jsonl, write_jsonl, stamp
from .data import make_pair, validate as validate_pairs, changed_paths
from .structured_data import DIRECTORY as ORIGINAL, DOMAINS
from .question_trial import DECISION
from .transforms import sha, timestamp
from datetime import timedelta

DIRECTORY = ROOT/'data/experiment-3-wording-draft'
ARMS = {'baseline':'Original training wording', 'coupled':'Matched coupled wording', 'balanced':'Counterbalanced wording'}
FAULTS = {
 'transport': 'Independent transport {method} at {asset} find packet delivery failures on the service path. Current service probes confirm loss.',
 'ran': 'Independent radio {method} at {asset} find receive decoding failures during verified degradation.',
 'power': 'Independent power {method} at {asset} find absent equipment supply during verified service loss.',
 'core': 'Independent core {method} at {asset} find rejected subscriber sessions across separately checked access paths.'}
NORMAL = {
 'transport':'Independent transport {method} at {asset} report normal packet delivery under the same conditions.',
 'ran':'Independent radio {method} at {asset} report normal receive processing under the same conditions.',
 'power':'Independent power {method} at {asset} report normal equipment supply under the same conditions.',
 'core':'Independent core {method} at {asset} report normal subscriber request processing under the same conditions.'}
NAMES={'transport':'aggregation continuity','ran':'receiver equalization','power':'battery distribution','core':'registration controller'}


def training():
    original=read_jsonl(ORIGINAL/'train.inputs.jsonl')
    coupled=copy.deepcopy(original);balanced=copy.deepcopy(original)
    counters={(d,k):0 for d in DOMAINS for k in ['fault','normal']}
    # Explicit authoring map identifies the twelve domain families. This never
    # enters inference features and does not inspect targets to construct words.
    labels={k['id']:k for k in read_jsonl(ORIGINAL/'train.labels.jsonl')}
    families={DOMAINS[d][0]+' '+suffix:d for d in DOMAINS for suffix in ['service association','measurement validity','instrument disagreement']}
    for a,b in zip(coupled,balanced):
        domain=families.get(labels[a['id']]['incident_family_id'])
        if domain is None:continue
        for oa,ob in zip(a['input']['observations'],b['input']['observations']):
            kind='normal' if 'reports normal' in oa['detail'] else 'fault'
            # Coupled keeps the original health/method association while using
            # plural nouns and the same grammatical frame in both matched arms.
            if kind=='normal':
                oa['detail']=NORMAL[domain].format(method='tests',asset=oa['asset_id'])
            method='tests' if kind=='normal' else 'diagnostics'
            alternative=method if (counters[domain,kind]//2+list(DOMAINS).index(domain))%2==0 else ('diagnostics' if method=='tests' else 'tests')
            ob['detail']=oa['detail'].replace(method,alternative)
            counters[domain,kind]+=1
    return {'baseline':original,'coupled':coupled,'balanced':balanced}


def development():
    records,keys=[],[]
    for domain in DOMAINS:
        for kind,suffix in [('dependency','path routing'),('age','sample expiry'),('conflict','comparable reports'),('wording','method synonym')]:
            for index in range(2):
                text=FAULTS[domain].replace('{method}','tests' if index==0 else 'diagnostics')
                spec=(NAMES[domain]+' '+suffix,'arrival' if kind=='wording' else kind,domain,text,'mesh' if index==0 else 'split','degraded' if domain in {'ran','core'} else 'outage')
                pair,answers=make_pair(spec,'development',index)
                if kind=='age':pair[1]['input']['observations'][0]['measured_at']=None if index else stamp(timestamp(pair[1]['input']['decision_timestamp'])-timedelta(minutes=15,seconds=1))
                if kind=='conflict':
                    for record in pair:
                        asset=record['input']['observations'][0]['asset_id']
                        record['input']['observations'][1]['detail']=NORMAL[domain].format(method='diagnostics' if index==0 else 'tests',asset=asset)
                    answers[1]['labels']['initial_owner']=domain;answers[1]['labels']['next_check']='inspect_radio' if domain=='ran' else 'inspect_'+domain
                    for key in answers:
                        key['accepted_answers']={f:[v] for f,v in key['labels'].items()}
                        key['label_rationale']='Comparable current independent fault and nominal reports disagree; retain NOC. A stale nominal reading cannot contradict a supported current fault.'
                    if index:
                        for record in pair:record['input']['observations'].reverse()
                        for key in answers:key['changed_path']='input.observations[0].measured_at'
                if kind=='wording':
                    pair[1]['input']['observations'][0]['observed_at']=pair[0]['input']['observations'][0]['observed_at']
                    pair[1]['input']['observations'][0]['detail']=pair[0]['input']['observations'][0]['detail'].replace('tests','diagnostics') if index==0 else pair[0]['input']['observations'][0]['detail'].replace('diagnostics','tests')
                    for key in answers:key['changed_path']='input.observations[0].detail';key['pair_kind']='invariance';key['label_rationale']='Only the measurement-method noun changes. The same current fault and visible service path support the same decisions.'
                records+=pair;keys+=answers
    extras=[
      ('unmapped cooling service excerpt','partial','noc','An independent transport test at {asset} reports a hardware fault during verified service loss.','mesh','outage'),
      ('supply inventory delivery gap','missing_topology','power','An independent power diagnostic at {asset} reports absent equipment supply during verified service loss.','split','outage'),
      ('service recovery verification cycle','recovery','noc','Independent service tests pass throughout the recovery interval. No active domain fault remains.','mesh','none'),
      ('unexplained work zone extent','maintenance','noc','Service loss extends beyond the documented work zone. No domain fault has been independently diagnosed.','split','outage')]
    for spec in extras:
        for index in range(2):
            pair,answers=make_pair(spec,'development',index);records+=pair;keys+=answers
    for record,key in zip(records,keys):
        record['id']=record['id'].replace('NS3-','NSW-');key['id']=record['id'];key['pair_id']=key['pair_id'].replace('NS3-','NSW-')
    return records,keys


def word_counts(records):
    result={k:{'tests':0,'diagnostics':0} for k in ['fault','normal']}
    for record in records:
        for row in record['input']['observations']:
            text=row['detail'];kind='normal' if 'report normal' in text else 'fault'
            for word in result[kind]:
                if re.search(r'\b'+word+r'\b',text):result[kind][word]+=1
    return result


def build(directory=DIRECTORY):
    directory=Path(directory)
    if directory.exists():raise ValueError('Choose a new wording data directory.')
    train=training();dev,keys=development();train_keys=read_jsonl(ORIGINAL/'train.labels.jsonl')
    for arm in ARMS:
        path=directory/arm
        for split,records,answers in [('train',train[arm],train_keys),('development',dev,keys)]:
            write_jsonl(path/(split+'.inputs.jsonl'),records);write_jsonl(path/(split+'.labels.jsonl'),answers)
        manifest={'version':'experiment-3-wording-draft-1','operator':'Northstar Telecom','synthetic':True,'reference_status':'draft_not_specialist_reviewed',
                  'splits':{'train':{'records':96,'families':16,'pairs':48},'development':{'records':80,'families':20,'pairs':40}},
                  'sha256':{p.name:sha(p.read_bytes()) for p in sorted(path.glob('*.jsonl'))}}
        (path/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    plan={'schema':'experiment-3-wording-data-1','operator':'Northstar Telecom','synthetic':True,'reference_status':'draft_not_specialist_reviewed',
          'evaluation_status':'development_only_no_held_out_set','human_decision':DECISION,'arms':ARMS,
          'splits':manifest['splits'],'training_intervention':'Matched coupled versus balanced differs only in tests/diagnostics nouns in twelve domain families; extra families unchanged. Original wording is a bridge control.',
          'training_word_counts':{a:word_counts(train[a]) for a in ['coupled','balanced']},
          'construction':'Original training mechanisms and references; new development family names and prose, shared templates and simplified vocabulary. Correlated variations are not independent incidents.',
          'sha256':{str(p.relative_to(directory)):sha(p.read_bytes()) for p in sorted(directory.glob('*/*'))}}
    (directory/'manifest.json').write_text(json.dumps(plan,indent=2)+'\n');validate(directory);return plan


def validate(directory=DIRECTORY):
    directory=Path(directory);plan=json.loads((directory/'manifest.json').read_text())
    expected={str(p.relative_to(directory)) for p in directory.glob('*/*')}
    if set(plan['sha256'])!=expected:raise ValueError('Wording manifest paths differ.')
    for name,digest in plan['sha256'].items():
        if Path(name).is_absolute() or '..' in Path(name).parts or sha((directory/name).read_bytes())!=digest:raise ValueError('Wording data checksum differs.')
    trains={};devs={}
    for arm in ARMS:
        validate_pairs(directory/arm);trains[arm]=read_jsonl(directory/arm/'train.inputs.jsonl');devs[arm]=read_jsonl(directory/arm/'development.inputs.jsonl')
        if (directory/arm/'train.labels.jsonl').read_bytes()!=(ORIGINAL/'train.labels.jsonl').read_bytes():raise ValueError('Training targets differ.')
        if (directory/arm/'development.labels.jsonl').read_bytes()!=(directory/'baseline/development.labels.jsonl').read_bytes():raise ValueError('Development targets differ.')
    if trains!=training():raise ValueError('Declared training wording intervention differs.')
    if any(devs[a]!=devs['baseline'] for a in ARMS):raise ValueError('Development inputs differ between arms.')
    for a,b in zip(trains['coupled'],trains['balanced']):
        if a['id']!=b['id']:raise ValueError('Training identity changed.')
        before,after=copy.deepcopy(a),copy.deepcopy(b)
        for record in [before,after]:
            for row in record['input']['observations']:row['detail']=re.sub(r'\b(tests|diagnostics)\b','METHOD',row['detail'])
        if before!=after:raise ValueError('Matched training intervention changes more than the method noun.')
    counts={a:word_counts(trains[a]) for a in ['coupled','balanced']}
    if counts!=plan['training_word_counts'] or counts['balanced']!={'fault':{'tests':36,'diagnostics':36},'normal':{'tests':12,'diagnostics':12}}:raise ValueError('Method words are not balanced within reading outcomes.')
    new_keys=read_jsonl(directory/'baseline/development.labels.jsonl');families={k['incident_family_id'] for k in new_keys};ids={k['id'] for k in new_keys}
    for folder in (ROOT/'data').glob('experiment-3*'):
        if folder.resolve()==directory.resolve():continue
        for p in folder.glob('*.labels.jsonl'):
            old=read_jsonl(p)
            if families & {k['incident_family_id'] for k in old} or ids & {k['id'] for k in old}:raise ValueError('New development families overlap earlier packs.')
    return {'train_per_arm':96,'development_per_arm':80,'development_families':20,'development_pairs':40}
