import copy
import json
from pathlib import Path
import tempfile, threading, unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from triage_bench.dataset import read_jsonl
from triage_bench.policy import OPTIONS
from triage_bench.experiment3.selection import ARMS, body, packet, eligibility
from triage_bench.experiment3.selection_data import DIRECTORY, build, validate
from triage_bench.experiment3.selection_trial import prepare, run, verify
from triage_bench.experiment3.transforms import MODEL


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.records = read_jsonl(DIRECTORY / 'development.inputs.jsonl')

    def profile(self, endpoint='https://api.typesafe.ai/v1/systemone'):
        return {'model': MODEL, 'endpoint': endpoint, 'context_tokens': 32768, 'api_key': 'selection-fixture-secret'}

    def test_new_reproducible_pairs_and_disjoint_families(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(build(Path(folder) / 'data'), validate())
        self.assertEqual(len(self.records), 12)
        self.assertEqual(validate()['pairs'], 6)

    def test_eligibility_handles_unknown_excluded_partial_and_invalid_times(self):
        p = copy.deepcopy(self.records[-1]['input'])
        self.assertTrue(eligibility(p)[0]['eligible'])
        p['topology']['coverage'] = 'partial'
        self.assertTrue(eligibility(p)[0]['eligible'])
        p['topology']['edges'] = []
        self.assertEqual(eligibility(p)[0]['reasons'], ['relationship_unknown'])
        p['topology']['coverage'] = 'complete'
        self.assertEqual(eligibility(p)[0]['reasons'], ['relationship_excluded'])
        p['topology'] = {}
        p['observations'][0]['measured_at'] = None
        self.assertEqual(eligibility(p)[0]['reasons'], ['measurement_unknown', 'relationship_unknown'])
        p['observations'][0]['measured_at'] = p['decision_timestamp']
        with self.assertRaises(ValueError): eligibility(p)

    def test_filter_reindexes_every_join_and_keeps_raw_packet_intact(self):
        r = self.records[5]  # The nominal observation is first in the radio pair.
        before = copy.deepcopy(r)
        filtered = packet(r, 'selected')
        self.assertEqual(r, before)
        for name in ['observations', 'measurement_facts', 'dependency_facts']:
            self.assertEqual(len(filtered[name]), 1)
            self.assertEqual(filtered[name][0]['observation_index'], 0)
            self.assertEqual(filtered[name][0]['source_observation_index'], 1)
        self.assertNotIn(r['input']['observations'][0]['detail'], body(r, 'selected')['state'])
        self.assertEqual(len(packet(r, 'eligibility')['observations']), 2)

    def test_current_conflict_controls_remain_and_empty_evidence_is_explicit(self):
        for r in self.records[:6:2]:
            filtered = packet(r, 'selected')
            self.assertEqual(len(filtered['observations']), 2)
            self.assertTrue(all(x['eligible'] for x in filtered['evidence_eligibility']['observations']))
        for r in self.records[6::2]:
            filtered = packet(r, 'selected')
            self.assertEqual(filtered['observations'], [])
            self.assertEqual(filtered['measurement_facts'], [])
            self.assertEqual(filtered['dependency_facts'], [])
        p = copy.deepcopy(self.records[-1]['input'])
        p['observations'][0]['valid_for_minutes'] = 5
        self.assertTrue(eligibility(p)[0]['eligible'])
        p['observations'][0]['valid_for_minutes'] = 4.999
        self.assertEqual(eligibility(p)[0]['reasons'], ['measurement_stale'])

    def test_fixed_questions_historical_baseline_and_allowlist(self):
        from triage_bench.experiment3.question_trial import body as historical
        for r in self.records:
            requests = [body(r, a) for a in ARMS]
            self.assertTrue(all(x['questions'] == historical(r, 'precedence')['questions'] for x in requests))
            self.assertEqual(requests[0], historical(r, 'precedence'))
        r = copy.deepcopy(self.records[1])
        r['labels'] = {'initial_owner': 'LEAK_SENTINEL'}
        r['input']['observations'][0]['reference'] = 'LEAK_SENTINEL'
        r['input']['reference'] = 'LEAK_SENTINEL'
        for a in ARMS: self.assertEqual(body(r, a), body(self.records[1], a))
        protocol, _, _, requests = prepare(self.profile())
        self.assertEqual(protocol['maximum_requests'], 36)
        self.assertEqual(len(set(protocol['question_sha256'].values())), 1)
        self.assertEqual([r['variant'] for r in requests[:9]], ['baseline', 'eligibility', 'selected', 'eligibility', 'selected', 'baseline', 'selected', 'baseline', 'eligibility'])
        self.assertNotIn('selection-fixture-secret', json.dumps(protocol))

    def fixture(self, out, status=200):
        captured = []
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                assert len(read_jsonl(out / 'requests.jsonl')) == 36
                captured.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
                self.send_response(status); self.end_headers()
                predictions = {'initial_owner':'noc', 'priority':'P2', 'next_check':'gather_evidence', 'insufficient_evidence':'yes'}
                raw = {'model': MODEL, 'note': 'selection-fixture-secret', 'answers': {f: {'choice': predictions[f], 'probabilities': {k:1/len(c) for k in c}} for f,c in OPTIONS.items()}}
                self.wfile.write(json.dumps(raw).encode())
            def log_message(self, *args): pass
        server = HTTPServer(('127.0.0.1', 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try: result = run(out, self.profile(f'http://127.0.0.1:{server.server_port}/v1/systemone'))
        finally: server.shutdown(); server.server_close(); thread.join()
        return result, captured

    def test_wire_plan_redaction_immutable_run_and_tamper_rejection(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / 'run'
            result, captured = self.fixture(out)
            self.assertEqual(result['attempted_requests'], 36)
            self.assertEqual(captured, [r['body'] for r in read_jsonl(out / 'requests.jsonl')])
            verify(out / 'summary.json')
            with self.assertRaisesRegex(ValueError, 'immutable'): run(out, self.profile())
            for path in out.iterdir(): self.assertNotIn('selection-fixture-secret', path.read_text())
            path = out / 'selected.jsonl'
            rows = read_jsonl(path); rows[0]['probabilities']['priority']['P2'] = .99
            path.write_text('\n'.join(json.dumps(x) for x in rows) + '\n')
            with self.assertRaisesRegex(ValueError, 'metrics'): verify(out / 'summary.json')

    def test_rate_limit_stops_and_missing_responses_stay_in_denominator(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / 'run'
            result, captured = self.fixture(out, 429)
            self.assertEqual(len(captured), 1)
            self.assertEqual(result['unattempted_requests'], 35)
            self.assertEqual(result['approaches']['selected']['metrics']['records'], 12)
            self.assertEqual(result['approaches']['selected']['metrics']['missing_records'], 12)
            verify(out / 'summary.json')

    def test_service_and_http_export_do_not_invent_missing_results(self):
        from triage_bench.experiment3.selection_service import SelectionStudy
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); build(root / 'data/experiment-3-selection-draft')
            study = SelectionStudy(root)
            self.assertIsNone(study.catalog()['hosted_pilot'])
            case = study.case(self.records[1]['id'], 'selected')
            self.assertEqual(case['request'], body(self.records[1], 'selected'))
            self.assertTrue(all(x is None for x in case['hosted_outputs'].values()))
            with self.assertRaises(ValueError): study.case(self.records[0]['id'], split='train')
        import urllib.request
        from http.server import ThreadingHTTPServer
        from triage_bench.app import App, handler_for
        server = ThreadingHTTPServer(('127.0.0.1',0), handler_for(App()))
        thread = threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            url = f'http://127.0.0.1:{server.server_port}'
            with urllib.request.urlopen(url + '/api/experiment3/catalog?trial=selection') as res: catalog = json.load(res)
            self.assertEqual(catalog['comparison'], 'selection')
            with urllib.request.urlopen(url + '/api/experiment3/export?trial=selection&variant=selected&id=' + self.records[1]['id']) as res: request = json.load(res)
            self.assertEqual(request, body(self.records[1], 'selected'))
        finally: server.shutdown();server.server_close();thread.join()
