"""Freeze the analyst boundary, evaluate once, or inspect recorded evidence."""
import argparse
import json
from pathlib import Path
from triage_bench.app import load_env, profiles
from triage_bench.dataset import ROOT
from triage_bench.experiment3.task_fit_advisory import freeze_boundary, check_boundary, run_evaluation, assess

CANDIDATE = ROOT/'checkpoints/task-fit-candidate-2026-10-03.json'
CALIBRATION = ROOT/'runs/task-fit/calibration-2026-10-03-v1'
BOUNDARY = ROOT/'checkpoints/task-fit-analyst-boundary-2026-10-03.json'


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=['freeze', 'preflight', 'evaluate', 'assess'])
    p.add_argument('--output', type=Path)
    a = p.parse_args()
    if a.action == 'freeze': result = freeze_boundary(CANDIDATE, CALIBRATION, BOUNDARY)
    elif a.action == 'preflight': result = check_boundary(BOUNDARY, CANDIDATE, CALIBRATION)
    elif a.action == 'evaluate':
        load_env(ROOT/'.env')
        result = run_evaluation(profiles()['jev'], BOUNDARY, CANDIDATE, CALIBRATION)
    else:
        if not a.output: p.error('assess requires --output containing a saved calibration or evaluation run')
        result = assess(a.output, check_boundary(BOUNDARY, CANDIDATE, CALIBRATION))
    print(json.dumps(result, indent=2))


if __name__ == '__main__': main()
