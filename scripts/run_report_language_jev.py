"""Preflight, run or verify the bounded Jev report-language comparison."""
import argparse,json
from pathlib import Path
from triage_bench.dataset import ROOT
from triage_bench.app import load_env,profiles
from triage_bench.experiment3.report_language_hosted import prepare,run,verify

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['preflight','run','verify']);p.add_argument('--output',type=Path);a=p.parse_args()
    load_env(ROOT/'.env');profile=profiles()['jev']
    if a.action=='preflight':
        plan,_,_,_=prepare(profile);result={k:plan[k] for k in ['records','report_count','maximum_requests','requested_model']}
    else:
        if not a.output:p.error('run/verify needs an output directory')
        s=run(a.output,profile,progress=lambda n,total,arm,status:print(json.dumps({'completed':n,'total':total,'arm':arm,'status':status}),flush=True)) if a.action=='run' else verify(a.output/'summary.json')[0]
        result={k:s[k] for k in ['status','attempted_requests','failed_requests','unattempted_requests','stopped_reason']};result['scores']={k:v['metrics']['all_fields_accuracy'] for k,v in s['approaches'].items()}
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
