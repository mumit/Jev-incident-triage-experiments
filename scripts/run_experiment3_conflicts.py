"""Build, validate, preflight or run a bounded repeated conflict comparison."""
import argparse,json
from pathlib import Path
from triage_bench.app import load_env,profiles
from triage_bench.dataset import ROOT
from triage_bench.experiment3.conflict_trial import build,validate,prepare,run

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['build','validate','preflight','run']);p.add_argument('--output',type=Path);a=p.parse_args()
    if a.action=='build':result=build()
    elif a.action=='validate':result=validate()
    else:
        load_env(ROOT/'.env');profile=profiles()['jev']
        if a.action=='preflight':
            plan,_=prepare(profile);result={k:plan[k] for k in ['repetitions','maximum_requests','records_per_repetition','pairs_per_repetition']}
        else:
            if not a.output:p.error('run requires a new output directory')
            def progress(n,done,total,arm,status):print(json.dumps({'repetition':n,'completed':done,'total':total,'arm':arm,'status':status}),flush=True)
            s=run(a.output,profile,progress=progress);result={'status':s['status'],'attempted':s['attempted_requests'],'failed':s['failed_requests'],'scores':{a:v['all_fields_accuracy'] for a,v in s['approaches'].items()}}
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
