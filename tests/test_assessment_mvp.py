"""End-to-end HTTP/SQLite checks of the transferred school assessment workflow."""
import concurrent.futures
import json
import sqlite3
import time
import unittest
import uuid
from datetime import datetime, timedelta, timezone

import test_workspace as common
import workspace_store as store
from assessment_runtime import start_expiry_worker
from education_store import prepare_school_demo


class SchoolAssessmentHTTP(unittest.TestCase):
    client = common.WorkspaceIntegration.client
    request = common.WorkspaceIntegration.request

    @classmethod
    def setUpClass(cls):
        common.WorkspaceIntegration.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        common.WorkspaceIntegration.tearDownClass.__func__(cls)

    def setUp(self):
        self.teacher, self.token = self.client('training')

    def paper(self, items=None):
        data = {'title': 'Toán 9 · Kiểm tra phương trình', 'description': 'Kiểm tra kiến thức nền tảng.', 'subject': 'Toán', 'grade': 9, 'items': items if items is not None else [{'id': 'q1', 'prompt': 'Hai cộng hai bằng bao nhiêu?', 'options': ['Một', 'Hai', 'Ba', 'Bốn'], 'correct': 3, 'explanation': 'Hai cộng hai bằng bốn.', 'category': 'Toán', 'objective': 'Phép cộng', 'teacherSupport': {'hint': 'PRIVATE-HINT', 'solution': 'PRIVATE-SOLUTION', 'teachingNotes': 'PRIVATE-NOTES'}}]}
        status, p = self.request(self.teacher, 'assessment/papers', data, self.token)
        self.assertEqual(status, 200, p)
        return p

    def release(self, p):
        status, p = self.request(self.teacher, 'assessment/papers/' + str(p['id']) + '/release', {'expected_revision': p['revision'], 'content_checked': True}, self.token)
        self.assertEqual(status, 200, p)
        return p

    def room(self, p=None, **overrides):
        p = p or self.release(self.paper())
        now = datetime.now(timezone.utc)
        data = {'request_key': uuid.uuid4().hex, 'release_id': p['release']['id'], 'title': 'Toán 9 · Phòng kiểm thử', 'starts_at': (now - timedelta(minutes=1)).isoformat(), 'ends_at': (now + timedelta(hours=1)).isoformat(), 'duration': 15, 'pass_score': 70, 'max_attempts': 2, 'result_policy': 'after_close', 'user_ids': [4]}
        data.update(overrides)
        status, room = self.request(self.teacher, 'assessment/rooms', data, self.token)
        self.assertEqual(status, 200, room)
        return room['id'], data

    def start(self, rid, role='learner'):
        client, token = self.client(role)
        status, attempt = self.request(client, 'exams/' + str(rid) + '/start', {}, token)
        self.assertEqual(status, 200, attempt)
        return client, token, attempt

    def test_draft_can_be_incomplete_but_release_requires_valid_content(self):
        p = self.paper([])
        route = 'assessment/papers/' + str(p['id']) + '/release'
        self.assertEqual(self.request(self.teacher, route, {'expected_revision': p['revision'], 'content_checked': True}, self.token)[0], 400)
        p = self.paper()
        self.assertEqual(self.request(self.teacher, 'assessment/papers/' + str(p['id']) + '/release', {'expected_revision': p['revision']}, self.token)[0], 400)
        invalid = {**p, 'expected_revision': p['revision']}
        invalid['items'][0]['options'] = ['Trùng', 'Trùng', 'Ba', 'Bốn']
        _, saved = self.request(self.teacher, 'assessment/papers/' + str(p['id']), invalid, self.token)
        self.assertEqual(self.request(self.teacher, 'assessment/papers/' + str(p['id']) + '/release', {'expected_revision': saved['revision'], 'content_checked': True}, self.token)[0], 400)

    def test_learner_and_other_teacher_cannot_read_or_edit_papers_and_results(self):
        p = self.release(self.paper()); rid, _ = self.room(p)
        student, token = self.client()
        for route in ['assessment/papers', 'assessment/papers/' + str(p['id']), 'assessment/rooms/' + str(rid), 'assessment/rooms/' + str(rid) + '/export']:
            self.assertEqual(self.request(student, route)[0], 403, route)
        with store.connection() as db:
            uid = db.execute('INSERT INTO users(name,email,password,role,department_id,title,created_at) VALUES(?,?,?,?,?,?,?)', ('Giáo viên khác', uuid.uuid4().hex+'@vinassess.local', store.password_hash('VinAssess@2026'), 'training', 1, 'Giáo viên', store.now_iso())).lastrowid
            email = db.execute('SELECT email FROM users WHERE id=?', (uid,)).fetchone()[0].split('@')[0]
        other, token = self.client(email)
        self.assertEqual(self.request(other, 'assessment/papers/' + str(p['id']))[0], 404)
        self.assertEqual(self.request(other, 'assessment/rooms/' + str(rid))[0], 404)
        self.assertEqual(self.request(other, 'exams/' + str(rid) + '/status', {'status': 'closed'}, token)[0], 404)

    def test_revision_conflict_release_immutability_and_clone(self):
        p = self.paper(); route = 'assessment/papers/' + str(p['id'])
        data = {**p, 'expected_revision': p['revision']}
        _, changed = self.request(self.teacher, route, data, self.token)
        self.assertEqual(self.request(self.teacher, route, data, self.token)[0], 409)
        ready = self.release(changed)
        self.assertEqual(self.request(self.teacher, route, {**ready, 'expected_revision': ready['revision']}, self.token)[0], 409)
        with store.connection() as db:
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute('UPDATE assessment_releases SET items="[]" WHERE id=?', (ready['release']['id'],))
        status, copy = self.request(self.teacher, route + '/clone', {}, self.token)
        self.assertEqual(status, 200); self.assertEqual(copy['status'], 'draft'); self.assertEqual(copy['items'], ready['items'])

    def test_room_replay_binding_and_roster_validation(self):
        rid, body = self.room()
        self.assertEqual(self.request(self.teacher, 'assessment/rooms', body, self.token)[1]['id'], rid)
        self.assertEqual(self.request(self.teacher, 'assessment/rooms', {**body, 'title': 'Nội dung khác'}, self.token)[0], 409)
        for ids in [[4,4], [1], [999999], [True]]:
            self.assertEqual(self.request(self.teacher, 'assessment/rooms', {**body, 'request_key': uuid.uuid4().hex, 'user_ids': ids}, self.token)[0], 400)

    def test_schedule_and_assignment_are_server_enforced(self):
        rid, _ = self.room(starts_at=(datetime.now(timezone.utc)+timedelta(minutes=10)).isoformat())
        client, token = self.client()
        self.assertEqual(self.request(client, 'exams/' + str(rid) + '/start', {}, token)[0], 403)
        rid, _ = self.room()
        other, token = self.client('tuananh')
        self.assertEqual(self.request(other, 'exams/' + str(rid) + '/start', {}, token)[0], 403)

    def test_no_answer_or_teacher_support_leak_and_delayed_review(self):
        rid, _ = self.room()
        client, token, a = self.start(rid)
        raw = json.dumps(a)
        self.assertNotIn('PRIVATE', raw); self.assertNotIn('correct', a['questions'][0]); self.assertNotIn('explanation', a['questions'][0])
        _, result = self.request(client, 'attempts/' + str(a['id']) + '/submit', {'expected_revision': a['revision'], 'answers': {'q1': 3}}, token)
        self.assertEqual(result['score'], 100);self.assertFalse(result['results_visible']);self.assertNotIn('correct', result['questions'][0])
        with store.connection() as db: db.execute('UPDATE exams SET due=? WHERE id=?', (store.now_iso(-1), rid))
        _, result = self.request(client, 'attempts/' + str(a['id']))
        self.assertTrue(result['results_visible']);self.assertEqual(result['questions'][0]['correct'], 3);self.assertNotIn('PRIVATE', json.dumps(result))

    def test_concurrent_start_reuses_attempt_and_stale_answers_cannot_overwrite(self):
        rid, _ = self.room()
        student, token = self.client()
        with concurrent.futures.ThreadPoolExecutor() as pool:
            starts = list(pool.map(lambda _: self.request(student, 'exams/' + str(rid) + '/start', {}, token), range(2)))
        self.assertTrue(all(status==200 for status,_ in starts));self.assertEqual(starts[0][1]['id'], starts[1][1]['id'])
        a = starts[0][1]; route = 'attempts/' + str(a['id']) + '/answers'
        status, updated = self.request(student, route, {'expected_revision': 0, 'answers': {'q1': 3}}, token)
        self.assertEqual(status, 200);self.assertEqual(updated['revision'], 1)
        self.assertEqual(self.request(student, route, {'expected_revision': 0, 'answers': {}}, token)[0], 409)
        _, resumed = self.request(student, 'attempts/' + str(a['id']))
        self.assertEqual(resumed['answers'], {'q1':3});self.assertEqual(resumed['deadline'], a['deadline'])

    def test_snapshot_scoring_and_idempotent_submission(self):
        rid, _ = self.room(pass_score=100,result_policy='immediate')
        student, token, a = self.start(rid)
        with store.connection() as db: db.execute('UPDATE exams SET pass_score=1,title="Renamed" WHERE id=?', (rid,))
        _, result = self.request(student, 'attempts/' + str(a['id']) + '/submit', {'expected_revision': 0, 'answers': {'q1': 0}}, token)
        self.assertFalse(result['passed']);self.assertEqual(result['pass_score'], 100);self.assertEqual(result['title'], a['title'])
        _, replay = self.request(student, 'attempts/' + str(a['id']) + '/submit', {'expected_revision': 0, 'answers': {'q1': 3}}, token)
        self.assertEqual(result, {**replay, 'server_time':result['server_time']})

    def test_timeout_worker_grades_without_browser_and_ignores_late_answers(self):
        rid, _ = self.room(); student, token, a = self.start(rid)
        with store.connection() as db: db.execute('UPDATE attempts SET deadline=0,answers=? WHERE id=?', (json.dumps({'q1':0}),a['id']))
        stop, worker = start_expiry_worker()
        try:
            for _ in range(30):
                time.sleep(.05)
                with store.connection() as db:
                    stored = db.execute('SELECT * FROM attempts WHERE id=?', (a['id'],)).fetchone()
                if stored['submitted_at']: break
            self.assertEqual(stored['submission_reason'], 'timeout')
        finally:
            stop.set();worker.join(2)
        _, result = self.request(student, 'attempts/' + str(a['id']) + '/submit', {'expected_revision':0,'answers':{'q1':3}}, token)
        self.assertEqual(result['score'], 0);self.assertEqual(result['answers'], {'q1':0})

    def test_close_room_preserves_active_attempt_and_results_use_latest_submission(self):
        rid, _ = self.room(); student, token, a = self.start(rid)
        self.assertEqual(self.request(self.teacher, 'assessment/rooms/'+str(rid)+'/status', {'status':'closed'}, self.token)[0], 200)
        self.assertEqual(self.request(student,'attempts/'+str(a['id'])+'/answers', {'expected_revision':0,'answers':{'q1':0}},token)[0],200)
        _, r = self.request(student,'attempts/'+str(a['id'])+'/submit', {'expected_revision':1,'answers':{'q1':0}},token)
        self.assertEqual(r['score'],0)
        self.request(self.teacher,'assessment/rooms/'+str(rid)+'/status', {'status':'published'},self.token)
        _, _, a = self.start(rid)
        self.request(student,'attempts/'+str(a['id'])+'/submit', {'expected_revision':0,'answers':{'q1':3}},token)
        _, report = self.request(self.teacher,'assessment/rooms/'+str(rid))
        self.assertEqual(report['summary']['submitted'],1);self.assertEqual(report['summary']['average'],100);self.assertEqual(report['analysis'][0]['wrong_rate'],0);self.assertEqual(len(report['roster'][0]['attempts']),2)

    def test_school_seed_is_labelled_and_idempotent_preserves_legacy(self):
        with store.connection() as db: before = db.execute('SELECT COUNT(*) FROM questions').fetchone()[0]
        prepare_school_demo();prepare_school_demo()
        with store.connection() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM questions').fetchone()[0], before+4)
            self.assertEqual(db.execute('SELECT COUNT(*) FROM knowledge_documents WHERE sample_key="school-quadratic"').fetchone()[0],1)
            self.assertEqual(db.execute('SELECT prompt FROM questions WHERE id=1').fetchone()[0][:3],'Bạn')
            self.assertEqual(db.execute('SELECT COUNT(*) FROM users WHERE email="learner@vinassess.local"').fetchone()[0],1)

    def test_bank_scope_and_changed_content_block_new_rooms_and_starts(self):
        with store.connection() as db:
            qid = db.execute('INSERT INTO questions(prompt,options,correct,explanation,category,created_at,provenance) VALUES(?,?,?,?,?,?,?)', ('Câu hỏi phạm vi riêng cho kiểm thử',json.dumps(['Một','Hai','Ba','Bốn']),0,'Lời giải dành cho kiểm thử.','Toán',store.now_iso(),json.dumps({'department_id':1,'citations':[]}))).lastrowid
        p = self.release(self.paper([{'id':'source','source_question_id':qid,'objective':'Phạm vi nguồn'}]))
        now = datetime.now(timezone.utc)
        body = {'request_key':uuid.uuid4().hex,'release_id':p['release']['id'],'title':'Phòng bị giới hạn nguồn','starts_at':(now-timedelta(minutes=1)).isoformat(),'ends_at':(now+timedelta(hours=1)).isoformat(),'duration':15,'pass_score':70,'max_attempts':1,'result_policy':'after_close','user_ids':[4]}
        self.assertEqual(self.request(self.teacher,'assessment/rooms',body,self.token)[0],403)
        # A fresh public bank question is available initially, then changes after release.
        with store.connection() as db:
            qid = db.execute('INSERT INTO questions(prompt,options,correct,explanation,category,created_at) VALUES(?,?,?,?,?,?)', ('Một câu hỏi công khai đủ dài',json.dumps(['Một','Hai','Ba','Bốn']),0,'Lời giải cho câu hỏi công khai.','Toán',store.now_iso())).lastrowid
        p = self.release(self.paper([{'id':'source','source_question_id':qid,'objective':'Nguồn hiện hành'}]));rid,_=self.room(p)
        with store.connection() as db: db.execute('UPDATE questions SET correct=1 WHERE id=?',(qid,))
        student,token=self.client()
        self.assertEqual(self.request(student,'exams/'+str(rid)+'/start',{},token)[0],409)

    def test_result_csv_is_owner_scoped_and_formula_safe(self):
        rid,_=self.room()
        with store.connection() as db:
            original=db.execute('SELECT name FROM users WHERE id=4').fetchone()[0]
            db.execute('UPDATE users SET name="=UNTRUSTED()" WHERE id=4')
        try:
            status,data=self.request(self.teacher,'assessment/rooms/'+str(rid)+'/export')
            self.assertEqual(status,200);self.assertIn("'=UNTRUSTED()",data);self.assertNotIn('quocbao@',data)
        finally:
            with store.connection() as db:db.execute('UPDATE users SET name=? WHERE id=4',(original,))


if __name__ == '__main__': unittest.main()
