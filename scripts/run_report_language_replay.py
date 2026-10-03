"""Replay inspected Jev report texts without changing their requests."""
import argparse,json
from pathlib import Path
from triage_bench.app import load_env,profiles
from triage_bench.dataset import ROOT
from triage_bench.experiment3.report_language_repeat import prepare,run,verify

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['preflight','run','verify']);p.add_argument('--output',type=Path);a=p.parse_args();load_env(ROOT/'.env');profile=profiles()['jev']
    if a.action=='preflight':result=prepare(profile)[0]
    else:
        if not a.output:p.error('run/verify needs a new output directory')
        result=run(a.output,profile) if a.action=='run' else verify(a.output/'summary.json')
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
