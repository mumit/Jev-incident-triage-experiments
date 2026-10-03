"""Build, validate, preflight, run or verify the measured-function trial."""
import argparse,json
from pathlib import Path
from triage_bench.app import load_env,profiles
from triage_bench.dataset import ROOT
from triage_bench.experiment3.report_scope_data import build,validate
from triage_bench.experiment3.report_scope_trial import prepare,run_hosted,run_local,verify

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['build','validate','preflight','local','hosted','verify']);p.add_argument('--output',type=Path);a=p.parse_args()
 if a.action=='build':s=build()
 elif a.action=='validate':s=validate()
 else:
  load_env(ROOT/'.env');profile=profiles()['jev']
  if a.action=='preflight':s=prepare(profile)[0]
  else:
   if not a.output:p.error('local/hosted/verify needs an output directory')
   s=run_local(a.output) if a.action=='local' else run_hosted(a.output,profile) if a.action=='hosted' else verify(a.output/'summary.json')[0]
 print(json.dumps(s,indent=2))
if __name__=='__main__':main()
