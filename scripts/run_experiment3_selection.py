"""Build, validate, preflight or run the matched evidence-selection comparison."""
import argparse
import json
from pathlib import Path
from triage_bench.app import load_env,profiles
from triage_bench.dataset import ROOT
from triage_bench.experiment3.selection_data import build,validate
from triage_bench.experiment3.selection_trial import prepare,run

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['build','validate','preflight','run']);p.add_argument('--output',type=Path);args=p.parse_args()
    if args.action=='build': result=build()
    elif args.action=='validate':result=validate()
    else:
        load_env(ROOT/'.env');profile=profiles()['jev']
        if args.action=='preflight':
            protocol,_,_,_=prepare(profile);result={'records':protocol['records'],'maximum_requests':protocol['maximum_requests'],'model':protocol['requested_model'],'identical_questions':len(set(protocol['question_sha256'].values()))==1}
        else:
            if not args.output:p.error('run requires a new output directory')
            def progress(n,total,arm,status):print(json.dumps({'completed':n,'total':total,'arm':arm,'status':status}),flush=True)
            summary=run(args.output,profile,progress=progress);result={'status':summary['status'],'attempted':summary['attempted_requests'],'failed':summary['failed_requests'],'scores':{a:v['metrics']['all_fields_accuracy'] for a,v in summary['approaches'].items()}}
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
