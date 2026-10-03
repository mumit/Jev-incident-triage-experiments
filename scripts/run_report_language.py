"""Build, validate, replay or verify the matched report-language study."""
import argparse,json
from pathlib import Path
from triage_bench.experiment3.report_language_data import DIRECTORY,build,validate
from triage_bench.experiment3.report_language_trial import run,verify

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['build','validate','run','verify']);p.add_argument('--output',type=Path);p.add_argument('--data',type=Path,default=DIRECTORY);a=p.parse_args()
    if a.action=='build':result=build(a.data)
    elif a.action=='validate':result=validate(a.data)
    else:
        if not a.output:p.error('run/verify needs an output directory')
        s=run(a.output,a.data) if a.action=='run' else verify(a.output/'summary.json',a.data)[0]
        result={arm:{'packets':v['metrics']['records'],'all_four':v['metrics']['all_fields_accuracy'],'pairs':v['metrics']['pair_all_fields_accuracy']} for arm,v in s['approaches'].items()}
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
