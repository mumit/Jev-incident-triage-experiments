import io,json,tempfile,unittest,urllib.error
from pathlib import Path
from unittest.mock import patch
from triage_bench.dataset import read_jsonl,write_jsonl
from triage_bench.experiment3.report_language_data import DIRECTORY
from triage_bench.experiment3.report_language_hosted import prepare as original_prepare
from triage_bench.experiment3.report_language_repeat import CASES,prepare,run,verify,summarize
from triage_bench.experiment3.hosted import encoded

class ReplayTests(unittest.TestCase):
    def setUp(self):
        self.folder=tempfile.TemporaryDirectory();self.addCleanup(self.folder.cleanup);self.root=Path(self.folder.name);self.original=self.root/'original';self.original.mkdir();(self.original/'summary.json').write_text('{}')
        self.profile={'model':'jev-1.13.0','endpoint':'http://127.0.0.1:12345','context_tokens':32768,'api_key':'fixture-key'}
        p,_,_,requests=original_prepare(self.profile);refs=read_jsonl(DIRECTORY/'narrow/development.observations.jsonl');write_jsonl(self.original/'observation-references.jsonl',refs)
        replies=[{**q,'status':'ok','predictions':{'domain':'core','reading':'unknown'}} for q in requests if q['arm']=='jev_reading']
        self.mock=patch('triage_bench.experiment3.report_language_repeat.verify_original',return_value=(p,{},requests,replies));self.mock.start();self.addCleanup(self.mock.stop)

    def test_exact_original_requests_repeated_with_four_distinct_bodies(self):
        p,q,refs,_=prepare(self.profile,self.original);self.assertEqual(len(q),12);self.assertEqual(len({encoded(r['body']) for r in q}),4);self.assertEqual(len(refs),4)
        for c in CASES:
            bodies=[r['body'] for r in q if (r['id'],r['observation_index'])==c];self.assertEqual(bodies,[bodies[0]]*3)
        self.assertNotIn('draft_meaning',q[0]['body']);self.assertEqual([r['repetition'] for r in q],[1]*4+[2]*4+[3]*4)

    def test_recorded_success_verifies_redaction_plan_and_immutability(self):
        out=self.root/'run';calls=[]
        class Provider:
            def open(_,request,timeout):
                self.assertEqual(len(read_jsonl(out/'requests.jsonl')),12);self.assertTrue((out/'protocol.json').is_file());calls.append(json.loads(request.data))
                return io.BytesIO(json.dumps({'model':'jev-1.13.0','note':'fixture-key','answers':{'domain':{'choice':'core'},'reading':{'choice':'fault'}}}).encode())
        with patch('triage_bench.experiment3.report_language_repeat.urllib.request.build_opener',return_value=Provider()):s=run(out,self.profile,self.original)
        self.assertEqual(verify(out/'summary.json',self.original),s);self.assertEqual(len(calls),12);self.assertNotIn('fixture-key',(out/'responses.jsonl').read_text())
        self.assertEqual([r['correct_both'] for r in s['per_repetition']],[2]*3)
        with self.assertRaises(ValueError):run(out,self.profile,self.original)
        (out/'responses.jsonl').write_text((out/'responses.jsonl').read_text()+'\n')
        with self.assertRaisesRegex(ValueError,'evidence'):verify(out/'summary.json',self.original)

    def test_rate_limit_stops_immediately_without_automatic_retry(self):
        class Provider:
            def open(_,request,timeout):raise urllib.error.HTTPError(request.full_url,429,'limited',{},None)
        with patch('triage_bench.experiment3.report_language_repeat.urllib.request.build_opener',return_value=Provider()):s=run(self.root/'limited',self.profile,self.original)
        self.assertEqual(s['attempted_requests'],1);self.assertEqual(s['unattempted_requests'],11);self.assertEqual(s['stopped_reason'],'provider_http_429');self.assertEqual([r['correct_both'] for r in s['per_repetition']],[0]*3)

    def test_missing_and_malformed_replies_stay_in_planned_denominators(self):
        class Provider:
            def open(_,request,timeout):return io.BytesIO(b'[]')
        with patch('triage_bench.experiment3.report_language_repeat.urllib.request.build_opener',return_value=Provider()):s=run(self.root/'malformed',self.profile,self.original)
        self.assertEqual(s['attempted_requests'],3);self.assertEqual(s['stopped_reason'],'three_consecutive_failures');self.assertEqual([r['planned_reports'] for r in s['per_repetition']],[4]*3);self.assertTrue(all(r['failed_or_missing']==3 for r in s['reports']))

    def test_repeated_wrong_agreement_is_not_correctness(self):
        _,plan,refs,old=prepare(self.profile,self.original);rows=[{**q,'status':'ok','predictions':{'domain':'core','reading':'unknown'}} for q in plan]
        s=summarize(plan,rows,refs,old);self.assertTrue(all(r['all_repeats_agree'] for r in s['reports']));self.assertTrue(all(r['correct_repeats']==0 for r in s['reports']))
