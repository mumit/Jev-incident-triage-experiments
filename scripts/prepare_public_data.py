"""Download or prepare the fixed three-case public-data feasibility sample."""
import argparse
import json
from triage_bench.public_data import download, prepare, verify


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('download', 'prepare', 'verify'))
    parser.add_argument('--folder', default='runs/public-data/audit-2026-10-03')
    args = parser.parse_args()
    result = {'download': download, 'prepare': prepare, 'verify': verify}[args.action](args.folder)
    print(json.dumps({'action': args.action, 'revision': result['revision'],
                      'files': len(result['files']), 'cases': len(result.get('cases', []))}))


if __name__ == '__main__':
    main()
