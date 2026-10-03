"""Matched report-wording intervention and fresh development families."""
import copy,json,tempfile
from collections import Counter
from datetime import timedelta
from pathlib import Path
from triage_bench.dataset import ROOT,read_jsonl,write_jsonl,stamp
from .data import make_pair,decisions,changed_paths,validate as validate_pairs
from .interpretation_data import DIRECTORY as ORIGINAL,DOMAINS,READINGS
from .transforms import sha,timestamp

DIRECTORY=ROOT/'data/report-language-draft'
ARMS={'narrow':'Original report phrases','broad':'Broader report phrases'}
NAMES={'transport':'forwarding integrity sample','ran':'receiver decoding survey','power':'distribution voltage sample','core':'subscriber admission trace'}
TRAIN_CLAIMS={
 'transport':{'fault':['packet forwarding is failing','packet delivery is interrupted','packet loss is present','the required transport path fails','traffic cannot traverse the forwarding interface','packet transmission has failed'],
              'normal':['packet forwarding is not failing','packet delivery is uninterrupted','packet loss was not observed','the required transport path operates normally','traffic traverses the forwarding interface without failure','packet transmission has not failed'],
              'unknown':['packet forwarding might be failing','packet delivery interruption is suspected','packet loss is unconfirmed','the required transport path may fail','whether traffic can traverse the interface is inconclusive','packet transmission failure cannot be confirmed']},
 'ran':{'fault':['radio decoding is failing','receive processing is interrupted','radio decoding failures are present','the radio receiver fails','radio synchronization is absent','receive processing has failed'],
        'normal':['radio decoding is not failing','receive processing is uninterrupted','radio decoding failures were not observed','the radio receiver operates normally','radio synchronization is stable','receive processing has not failed'],
        'unknown':['radio decoding might be failing','receive processing interruption is suspected','radio decoding failure is unconfirmed','the radio receiver may fail','radio synchronization loss is inconclusive','receive processing failure cannot be confirmed']},
 'power':{'fault':['equipment supply is failing','equipment power delivery is interrupted','equipment voltage is absent','the required supply circuit fails','equipment supply voltage is below its operating range','power delivery has failed'],
          'normal':['equipment supply is not failing','equipment power delivery is uninterrupted','equipment voltage is normal','the required supply circuit operates normally','equipment supply voltage is within its operating range','power delivery has not failed'],
          'unknown':['equipment supply might be failing','equipment power interruption is suspected','equipment voltage loss is unconfirmed','the required supply circuit may fail','whether voltage is within its operating range is inconclusive','power delivery failure cannot be confirmed']},
 'core':{'fault':['subscriber session processing is failing','subscriber request processing is interrupted','subscriber requests are rejected','the core session handler fails','subscriber registration processing is unavailable','session processing has failed'],
         'normal':['subscriber session processing is not failing','subscriber request processing is uninterrupted','subscriber requests are not rejected','the core session handler operates normally','subscriber registration processing is available','session processing has not failed'],
         'unknown':['subscriber session processing might be failing','subscriber request interruption is suspected','subscriber request rejection is unconfirmed','the core session handler may fail','subscriber registration availability is inconclusive','session processing failure cannot be confirmed']}}
# Development sentences are specified independently of fitted weights and responses.
DEV_CLAIMS={
 'transport':{'fault':'the return-path interface drops traffic and delivery is disrupted','normal':'the return-path interface does not drop traffic and delivery is intact','unknown':'return-path drops are possible, but the capture cannot establish whether delivery is disrupted'},
 'ran':{'fault':'the receiver loses timing alignment and decoding stops','normal':'the receiver does not lose timing alignment and decoding continues','unknown':'timing alignment loss is possible, but the capture cannot establish whether decoding stopped'},
 'power':{'fault':'the equipment feed has no usable voltage and cannot energize the load','normal':'the equipment feed has usable voltage and energizes the load without interruption','unknown':'equipment feed loss is possible, but the meter result cannot establish whether the load is energized'},
 'core':{'fault':'the registration handler refuses subscriber requests across independent access routes','normal':'the registration handler accepts subscriber requests across independent access routes','unknown':'registration refusal is possible, but the trace cannot establish whether requests were accepted'}}


def broad_training(records,annotations,keys):
    result=copy.deepcopy(records);meaning={(a['id'],a['observation_index']):a for a in annotations}
    pairs={};by_id={k['id']:k for k in keys}
    for r in result:
        pair=by_id[r['id']]['pair_id'];pairs.setdefault(pair,len(pairs))
        for oi,o in enumerate(r['input']['observations']):
            a=meaning[r['id'],oi]
            if a['domain']=='none':continue
            claim=TRAIN_CLAIMS[a['domain']][a['reading']][(pairs[pair]+oi)%6]
            # The same probe nouns now occur in all three reading classes.
            follow={'fault':'Independent service probes confirm disruption.','normal':'Independent service probes confirm continued service.','unknown':'Independent service probes cannot resolve the uncertainty.'}[a['reading']]
            prefix=o['detail'].split(' report that ',1)[0]
            o['detail']=prefix+' report that '+claim+'. '+follow
    return result


def development_text(domain,state,kind,index):
    if domain=='none':
        return 'Independent service probes confirm restored service throughout the interval.' if state=='normal' else 'The unclassified sensor message does not establish a domain diagnosis.'
    claim=DEV_CLAIMS[domain][state]
    prefix=f'Independent {domain} instrumentation at {{asset}} reports: '
    if kind=='scope_negation':
        return prefix+'a routine availability check passes, but '+claim+'.'
    if kind=='scope_uncertainty':
        return prefix+('an earlier alarm is unconfirmed, but an independent current instrument establishes that '+claim+'.' if state=='fault' else 'an earlier alarm is unconfirmed; whether '+DEV_CLAIMS[domain]['fault']+' is also unconfirmed.')
    if index%2:return prefix+claim+'. Independent end-to-end measurements accompany this report.'
    return prefix+claim+'. This describes the measured component, not its age or service relationship.'


def development():
    records,keys,annotations=[],[],[]
    specs=[(name+' '+kind,d,'fault',kind) for d,name in NAMES.items() for kind in ['dependency','age','conflict','negation','uncertainty','missing_topology','scope_negation','scope_uncertainty']]
    specs += [('restoration observation interval','none','normal','recovery'),('work impact beyond footprint','none','unknown','maintenance'),('unassigned sensor notice','none','unknown','arrival')]
    for family,domain,state,kind in specs:
        for index in range(2):
            detail=development_text(domain,state,kind,index)
            if kind=='maintenance':detail='Current service impact extends beyond the documented work area. A domain diagnosis has not been established.'
            basic='arrival' if kind in {'negation','uncertainty','scope_negation','scope_uncertainty'} else kind
            status='none' if kind=='recovery' else 'degraded' if domain in {'ran','core'} else 'outage'
            pair,answers=make_pair((family,basic,domain if domain!='none' else 'noc',detail,'mesh' if index%2 else 'split',status),'development',index)
            meanings=[[{'domain':domain,'reading':state}],[{'domain':domain,'reading':state}]]
            if kind=='age':pair[1]['input']['observations'][0]['measured_at']=None if index%2 else stamp(timestamp(pair[1]['input']['decision_timestamp'])-timedelta(minutes=15,seconds=1))
            if kind=='conflict':
                for r in pair:r['input']['observations'][1]['detail']=development_text(domain,'normal',kind,index).format(asset=r['input']['observations'][1]['asset_id'])
                meanings=[m+[{'domain':domain,'reading':'normal'}] for m in meanings]
                answers[1]['labels']=decisions(domain,pair[1]['input']['service_impact'])
                if index%2:
                    for r in pair:r['input']['observations'].reverse()
                    meanings=[list(reversed(m)) for m in meanings]
                    for k in answers:k['changed_path']='input.observations[0].measured_at'
            if kind in {'negation','uncertainty','scope_negation','scope_uncertainty'}:
                other='normal' if kind in {'negation','scope_negation'} else 'unknown'
                b=pair[1]['input']['observations'][0];b['observed_at']=pair[0]['input']['observations'][0]['observed_at'];b['detail']=development_text(domain,other,kind,index).format(asset=b['asset_id'])
                meanings[1][0]['reading']=other;answers[1]['labels']=decisions('noc',pair[1]['input']['service_impact'],True)
                for k in answers:k['changed_path']='input.observations[0].detail'
            for r,k,meaning in zip(pair,answers,meanings):
                r['id']=r['id'].replace('NS3-','NSL-');k.update(id=r['id'],pair_id=k['pair_id'].replace('NS3-','NSL-'),control=kind)
                k['accepted_answers']={f:[v] for f,v in k['labels'].items()};k['pair_kind']='decision_change' if answers[0]['labels']!=answers[1]['labels'] else 'invariance'
                k['label_rationale']='Draft reference for this packet. The A-to-B pair changes '+k['changed_path']+'. Only current faults with a visible affected-service path justify their domain. A normal auxiliary check does not cancel an explicit component fault; uncertainty about an earlier alarm does not cancel an independent current fault measurement. Comparable current contradictions retain NOC. Recovery monitors; unexplained work verifies scope.'
                for oi,a in enumerate(meaning):annotations.append({'id':r['id'],'observation_index':oi,**a,'review_status':'draft_not_specialist_reviewed','rationale':'Written focal component reading; clause scope distinguishes the current measurement from auxiliary checks or earlier alarms.'})
            records+=pair;keys+=answers
    return records,keys,annotations


def build(directory=DIRECTORY):
    directory=Path(directory)
    if directory.exists():raise ValueError('Choose a new report-language directory.')
    train=read_jsonl(ORIGINAL/'train.inputs.jsonl');keys=read_jsonl(ORIGINAL/'train.labels.jsonl');annotations=read_jsonl(ORIGINAL/'train.observations.jsonl')
    dev,devkeys,devann=development();broad=broad_training(train,annotations,keys)
    for arm,rows in [('narrow',train),('broad',broad)]:
        for split,pack,targets,obs in [('train',rows,keys,annotations),('development',dev,devkeys,devann)]:
            for name,data in [('inputs',pack),('labels',targets),('observations',obs)]:write_jsonl(directory/arm/(split+'.'+name+'.jsonl'),data)
    manifest={'schema':'report-language-data-1','operator':'Northstar Telecom','synthetic':True,'reference_status':'draft_not_specialist_reviewed','evaluation_status':'development_only_no_held_out_set',
              'arms':ARMS,'intervention':'Only training observation detail changes. Counts, report meanings, packet targets and all non-text evidence stay matched. New development inputs and annotations are identical across arms.',
              'policy_assumptions':'Frozen report policy: 15-minute inclusive window, current visible service support and same-asset/domain comparability. Clause references distinguish focal current evidence from an auxiliary check or earlier alarm; specialist review pending.',
              'training_origin_sha256':{p.name:sha(p.read_bytes()) for p in ORIGINAL.glob('train.*.jsonl')},
              'splits':{'train':{'records':186,'families':31,'pairs':93},'development':{'records':len(dev),'families':len({k['incident_family_id'] for k in devkeys}),'pairs':len(dev)//2}},
              'observation_counts':{'train':len(annotations),'development':len(devann)},'training_class_counts':{d:dict(Counter(a['reading'] for a in annotations if a['domain']==d)) for d in DOMAINS},
              'sha256':{str(p.relative_to(directory)):sha(p.read_bytes()) for p in sorted(directory.rglob('*.jsonl'))}}
    (directory/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');validate(directory);return manifest


def validate(directory=DIRECTORY):
    directory=Path(directory);m=json.loads((directory/'manifest.json').read_text())
    expected={a+'/'+s+'.'+k+'.jsonl' for a in ARMS for s in ['train','development'] for k in ['inputs','labels','observations']}
    if set(m['sha256'])!=expected:raise ValueError('Report-language manifest paths differ.')
    for name,digest in m['sha256'].items():
        if sha((directory/name).read_bytes())!=digest:raise ValueError('Report-language checksum differs.')
    for arm in ARMS:
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder);base={**m,'sha256':{s+'.'+k+'.jsonl':m['sha256'][arm+'/'+s+'.'+k+'.jsonl'] for s in ['train','development'] for k in ['inputs','labels']}}
            for name in base['sha256']:(p/name).write_bytes((directory/arm/name).read_bytes())
            (p/'manifest.json').write_text(json.dumps(base));validate_pairs(p)
        for split in ['train','development']:
            rows=read_jsonl(directory/arm/(split+'.inputs.jsonl'));ann=read_jsonl(directory/arm/(split+'.observations.jsonl'))
            coverage={(r['id'],i) for r in rows for i in range(len(r['input']['observations']))}
            if len(ann)!=len(coverage) or {(a['id'],a['observation_index']) for a in ann}!=coverage:raise ValueError('Report annotation coverage differs.')
            if any(a['domain'] not in DOMAINS or a['reading'] not in READINGS or a['review_status']!='draft_not_specialist_reviewed' for a in ann):raise ValueError('Invalid report annotation.')
            if len(ann)!=m['observation_counts'][split]:raise ValueError('Report count differs.')
    for split,kinds in [('train',['labels','observations']),('development',['inputs','labels','observations'])]:
        for k in kinds:
            if (directory/'narrow'/(split+'.'+k+'.jsonl')).read_bytes()!=(directory/'broad'/(split+'.'+k+'.jsonl')).read_bytes():raise ValueError('Matched non-intervention data differ.')
    for name,digest in m['training_origin_sha256'].items():
        if sha((ORIGINAL/name).read_bytes())!=digest or sha((directory/'narrow'/name).read_bytes())!=digest:raise ValueError('Original training bridge differs.')
    a=read_jsonl(directory/'narrow/train.inputs.jsonl');b=read_jsonl(directory/'broad/train.inputs.jsonl')
    if not any(x!=y for x,y in zip(a,b)):raise ValueError('No training wording intervention.')
    for x,y in zip(a,b):
        if {k:v for k,v in x.items() if k!='input'}!={k:v for k,v in y.items() if k!='input'}:raise ValueError('Record identity changed.')
        for path in changed_paths(x['input'],y['input']):
            if not path.startswith('input.observations[') or not path.endswith('].detail'):raise ValueError('Non-text training intervention.')
    keys=read_jsonl(directory/'narrow/development.labels.jsonl');ids={k['id'] for k in keys};families={k['incident_family_id'] for k in keys}
    for p in (ROOT/'data').glob('experiment-3*/**/*.labels.jsonl'):
        old=read_jsonl(p)
        if ids & {k['id'] for k in old} or families & {k['incident_family_id'] for k in old}:raise ValueError('Earlier development family reused.')
    return {'train_per_arm':len(a),'development':len(keys),'development_families':len(families),'reports':m['observation_counts']}
