"""Review/preflight or run a new bounded Jev development comparison."""
import argparse
import json
from pathlib import Path
from triage_bench.app import load_env,profiles
from triage_bench.dataset import ROOT
from triage_bench.experiment3.hosted import prepare,run


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['preflight','run'])
    parser.add_argument('--output',type=Path)
    parser.add_argument('--pair',action='append',help='Optional full controlled pair; repeat for a small pilot.')
    args=parser.parse_args();load_env(ROOT/'.env');profile=profiles()['jev']
    if args.action=='preflight':
        protocol,_,_,_=prepare(profile,pair_ids=args.pair)
        if args.output:
            with args.output.open('x') as stream:stream.write(json.dumps(protocol,indent=2)+'\n')
        print(json.dumps({'model':protocol['requested_model'],'records':protocol['records'],'maximum_requests':protocol['maximum_requests'],
                          'context_preflight_passed':True,'review':'computational_only; specialist review pending'},indent=2))
    else:
        if not args.output:parser.error('run requires a new output directory')
        def progress(done,total,variant,status):print(json.dumps({'completed':done,'total':total,'variant':variant,'status':status}),flush=True)
        summary=run(args.output,profile,pair_ids=args.pair,progress=progress)
        print(json.dumps({'status':summary['status'],'attempted':summary['attempted_requests'],'failed':summary['failed_requests'],
                          'scores':{v:a['metrics']['all_fields_accuracy'] for v,a in summary['approaches'].items()}},indent=2))


if __name__=='__main__':main()
