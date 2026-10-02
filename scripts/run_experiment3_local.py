"""Prepare or run the draft local experiment 3 pilot. Never calls Jev."""
import argparse
import json
from pathlib import Path
from triage_bench.experiment3.data import DIRECTORY, build, validate
from triage_bench.experiment3.local import run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['build', 'validate', 'run'])
    parser.add_argument('--data', type=Path, default=DIRECTORY)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.action == 'build': result = build(args.data)
    elif args.action == 'validate': result = validate(args.data)
    else:
        if not args.output: parser.error('run requires a new --output directory')
        summary = run(args.output, args.data)
        result = {p: {k: s['metrics'].get(k) for k in ['all_fields_accuracy', 'semantic_decisions_accuracy', 'pair_all_fields_accuracy']} for p, s in summary['approaches'].items()}
    print(json.dumps(result, indent=2))


if __name__ == '__main__': main()
