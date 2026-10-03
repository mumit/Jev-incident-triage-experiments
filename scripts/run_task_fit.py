"""Prepare, run and verify the task-fit interpretation study."""
import argparse
import json
from pathlib import Path
from triage_bench.app import load_env, profiles
from triage_bench.dataset import ROOT
from triage_bench.experiment3.task_fit_data import build, validate
from triage_bench.experiment3.task_fit_trial import prepare, run_local, run_hosted, verify, freeze_candidate, check_freeze

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['build','validate','preflight','local','hosted','verify','freeze'])
    p.add_argument('--output',type=Path)
    p.add_argument('--split',default='development',choices=['development','calibration','evaluation'])
    p.add_argument('--arm',action='append')
    p.add_argument('--repeat',action='store_true')
    p.add_argument('--freeze',type=Path)
    p.add_argument('--development',type=Path)
    p.add_argument('--repetition',type=Path)
    a=p.parse_args()
    if a.action=='build': result=build()
    elif a.action=='validate': result=validate()
    elif a.action=='freeze':
        if not a.output or not a.development or not a.repetition: p.error('freeze needs --output, --development and --repetition')
        result=freeze_candidate(a.development,a.repetition,a.output)
    else:
        load_env(ROOT/'.env'); profile=profiles()['jev']
        if a.action in {'preflight','hosted'} and a.split!='development':
            if not a.arm or len(a.arm)!=1: p.error('Choose the single frozen arm.')
            check_freeze(a.freeze,a.arm[0])
        if a.action=='hosted' and a.split=='evaluation':
            p.error('Final evaluation remains sealed until its operating-boundary protocol is recorded; use calibration first.')
        if a.action=='preflight': result=prepare(profile,a.split,a.arm,repeat=a.repeat)[0]
        else:
            if not a.output: p.error('An output directory is required.')
            result=run_local(a.output) if a.action=='local' else verify(a.output) if a.action=='verify' else run_hosted(a.output,profile,a.split,a.arm,repeat=a.repeat,candidate=a.freeze)
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
