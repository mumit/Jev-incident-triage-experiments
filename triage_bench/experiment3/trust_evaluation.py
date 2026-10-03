"""Separate corrected attribution for frozen declaration-trust runs.

The recorded generic attribution compared effective structured domains with prose
references. This evaluation uses raw interpreter heads and separately scores the
operation reading consumed by policy. It never rewrites recorded run files.
"""
import json
from pathlib import Path
from triage_bench.dataset import ROOT,read_jsonl
from .trust_trial import verify
from .transforms import sha
SOURCE='triage_bench/experiment3/trust_evaluation.py'

def corrected_attribution(rows,annotations,keys):
 refs={(a['id'],a['observation_index']):a for a in annotations};result={}
 for arm,packets in rows.items():
  result[arm]={}
  for boundary,fields in [('raw_interpreter',['domain','reading']),('operation_reading',['reading'])]:
   categories={k:[] for k in ['readings_correct_triage_correct','readings_correct_triage_wrong','readings_wrong_triage_correct','readings_wrong_triage_wrong','failed_or_missing_packets']}
   for identifier,key in keys.items():
    row=packets.get(identifier)
    if not row or row['status']!='ok':categories['failed_or_missing_packets'].append(identifier);continue
    raw=row['raw_readings'];correct=len(raw)==sum(a['id']==identifier for a in annotations) and all(all(o[f]==refs[identifier,o['observation_index']][f] for f in fields) for o in raw)
    triage=row['predictions']==key['labels'];categories['readings_'+('correct' if correct else 'wrong')+'_triage_'+('correct' if triage else 'wrong')].append(identifier)
   result[arm][boundary]=categories
 return result

def evaluate_run(path):
 path=Path(path);summary,rows,*_=verify(path);ann=read_jsonl(path.parent/'observation-references.jsonl');keys={k['id']:k for k in read_jsonl(path.parent/'labels.jsonl')}
 return {'schema':'declaration-trust-evaluation-1','run_summary_sha256':sha(path.read_bytes()),'evaluation_source_sha256':{SOURCE:sha((ROOT/SOURCE).read_bytes())},'recorded_source_sha256':summary['source_sha256'],'approaches':summary['approaches'],'report_metrics':summary['report_metrics'],'changes':summary['changes'],'attribution':corrected_attribution(rows,ann,keys),'correction':'Recorded generic attribution compares effective structured domains with prose annotations. This separate evaluation uses raw interpreter domains and separately scores operation readings. Packet and distinct-text scores were unaffected. Original run evidence is unchanged.'}

def verify_evaluation(path,run):
 saved=json.loads(Path(path).read_text());expected=evaluate_run(run)
 if saved!=expected:raise ValueError('Corrected trust evaluation differs.')
 return saved
