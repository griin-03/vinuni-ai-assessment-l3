"""Integration checks against an isolated SQLite database and HTTP server."""
import http.cookiejar
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import workspace_store as store
from serve import MirrorHandler, MirrorServer
from functools import partial


class QuietHandler(MirrorHandler):
    def log_message(self, *args):
        pass


class WorkspaceIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='vinassess-test-')
        cls.previous_db = store.DB_PATH
        cls.previous_demo = os.environ.get('VINASSESS_DEMO')
        os.environ['VINASSESS_DEMO'] = '1'
        store.DB_PATH = Path(cls.temp.name) / 'test.sqlite3'
        store.init_store()
        cls.server = MirrorServer(('127.0.0.1', 0), partial(QuietHandler, manifest={'assets': {}}, routes=set()))
        cls.origin = 'http://127.0.0.1:' + str(cls.server.server_port)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()
        store.DB_PATH = cls.previous_db
        if cls.previous_demo is None:
            os.environ.pop('VINASSESS_DEMO', None)
        else:
            os.environ['VINASSESS_DEMO'] = cls.previous_demo
        cls.temp.cleanup()

    def client(self, role='learner'):
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        _, login = self.request(opener, 'login', {'email': role + '@vinassess.local', 'password': 'VinAssess@2026'})
        self.assertIn('csrf', login)
        return opener, login['csrf']

    def request(self, opener, route, body=None, csrf=None, origin=True):
        headers = {'Content-Type': 'application/json'}
        if origin: headers['Origin'] = self.origin
        if csrf: headers['X-CSRF-Token'] = csrf
        request = urllib.request.Request(self.origin + '/api/workspace/' + route, data=json.dumps(body).encode() if body is not None else None, headers=headers)
        try:
            response = opener.open(request)
        except urllib.error.HTTPError as error:
            response = error
        raw = response.read()
        return response.status, json.loads(raw) if response.headers.get('Content-Type', '').startswith('application/json') else raw.decode('utf-8-sig')

    def test_learner_cannot_manage_or_leak_answers(self):
        client, csrf = self.client()
        status, data = self.request(client, 'bootstrap')
        self.assertEqual(status, 200)
        self.assertEqual([p['id'] for p in data['people']], [4])
        self.assertEqual(data['questions'], [])
        self.assertTrue(all(c['enrollment']['user_id'] == 4 for c in data['courses']))
        for route in ['courses', 'questions', 'exams', 'users', 'settings']:
            self.assertEqual(self.request(client, route, {}, csrf)[0], 403, route)
        self.assertEqual(self.request(client, 'audit')[0], 403)
        self.assertEqual(self.request(client, 'report.csv')[0], 403)
        _, attempt = self.request(client, 'exams/1/start', {}, csrf)
        self.assertNotIn('correct', attempt['questions'][0])
        self.assertNotIn('explanation', attempt['questions'][0])
        self.assertEqual(self.request(client, 'attempts/' + str(attempt['id']) + '/submit', {'answers': {'1': 8}}, csrf)[0], 400)

    def test_manager_scope_and_csv(self):
        client, csrf = self.client('manager')
        _, data = self.request(client, 'bootstrap')
        self.assertEqual({p['department_id'] for p in data['people']}, {2})
        _, csv = self.request(client, 'report.csv')
        self.assertIn('Nguyễn Hà Linh', csv)
        self.assertNotIn('Trần Quốc Bảo', csv)
        self.assertEqual(self.request(client, 'courses', {}, csrf)[0], 403)
        self.assertEqual(self.request(client, 'users/4', {'role': 'admin', 'status': 'active'}, csrf)[0], 403)

    def test_session_origin_and_csrf(self):
        client, csrf = self.client('admin')
        self.assertEqual(self.request(client, 'settings', {'company': 'Demo', 'company_email': 'hr@example.test'})[0], 403)
        self.assertEqual(self.request(client, 'settings', {}, csrf, origin=False)[0], 403)
        self.assertEqual(self.request(client, 'logout', {}, csrf)[0], 200)
        self.assertEqual(self.request(client, 'bootstrap')[0], 401)
        for path in ['/.vinassess/workspace.sqlite3', '/scripts/workspace_store.py', '/backups/before-ocean-blue/index.html', '/content/ocean-palette.json', '/%2e%2e/.vinassess/workspace.sqlite3']:
            with self.assertRaises(urllib.error.HTTPError): client.open(self.origin + path)

    def test_training_can_publish_assign_but_not_grant_roles(self):
        client, csrf = self.client('training')
        self.assertEqual(self.request(client, 'users/4', {'role': 'admin', 'status': 'active'}, csrf)[0], 403)
        status, created = self.request(client, 'courses', {'title': 'Đào tạo kiểm thử nghiệp vụ', 'category': 'Nghiệp vụ', 'description': 'Mục tiêu cụ thể cho chương trình kiểm thử.', 'lessons': [{'title': 'Bài thứ nhất', 'body': 'Nội dung hướng dẫn thực tế đủ dài cho bài học đầu tiên.', 'minutes': 10}, {'title': 'Bài thứ hai', 'body': 'Nội dung thực hành bổ sung đủ dài cho bài học tiếp theo.', 'minutes': 10}]}, csrf)
        self.assertEqual(status, 200)
        cid = created['id']
        update = {'title': 'Bản nháp đã cập nhật', 'category': 'Nghiệp vụ', 'description': 'Nội dung và mục tiêu sau khi chỉnh sửa bản nháp.', 'lessons': [{'title': 'Bài thứ nhất', 'body': 'Nội dung hướng dẫn thực tế đủ dài cho bài học đầu tiên.', 'minutes': 10}, {'title': 'Bài thứ hai', 'body': 'Nội dung thực hành bổ sung đủ dài cho bài học tiếp theo.', 'minutes': 10}]}
        self.assertEqual(self.request(client, 'courses/' + str(cid), update, csrf)[0], 200)
        self.assertEqual(self.request(client, 'courses/' + str(cid) + '/assign', {'user_ids': [4], 'due': store.now_iso(10)}, csrf)[0], 400)
        self.assertEqual(self.request(client, 'courses/' + str(cid) + '/publish', {}, csrf)[0], 200)
        self.assertEqual(self.request(client, 'courses/' + str(cid), update, csrf)[0], 400)
        self.assertEqual(self.request(client, 'courses/' + str(cid) + '/assign', {'user_ids': [4], 'due': store.now_iso(10)}, csrf)[0], 200)
        learner, token = self.client()
        route = 'courses/' + str(cid) + '/progress'
        self.assertEqual(self.request(learner, route, {'lesson_id': 2}, token)[0], 400)
        self.assertEqual(self.request(learner, route, {'lesson_id': 1}, token)[0], 200)
        self.assertEqual(self.request(learner, route, {'lesson_id': 2}, token)[0], 200)

    def test_exam_grade_idor_and_immutable_submission(self):
        client, csrf = self.client('manager')
        _, attempt = self.request(client, 'exams/2/start', {}, csrf)
        _, resumed = self.request(client, 'exams/2/start', {}, csrf)
        self.assertEqual(attempt['id'], resumed['id'])
        other, _ = self.client('learner')
        self.assertEqual(self.request(other, 'attempts/' + str(attempt['id']))[0], 404)
        answers = {'5': 2, '6': 0, '7': 1, '11': 1}
        _, result = self.request(client, 'attempts/' + str(attempt['id']) + '/submit', {'answers': answers}, csrf)
        self.assertEqual(result['score'], 100)
        self.assertTrue(result['passed'])
        self.assertIn('correct', result['questions'][0])
        _, unchanged = self.request(client, 'attempts/' + str(attempt['id']) + '/submit', {'answers': {}}, csrf)
        self.assertEqual(unchanged['score'], 100)
        self.assertEqual(self.request(client, 'exams/2/start', {}, csrf)[0], 400)

    def test_timeout_uses_saved_answers(self):
        client, csrf = self.client('training')
        _, attempt = self.request(client, 'exams/1/start', {}, csrf)
        with store.connection() as db:
            db.execute('UPDATE attempts SET deadline=0,answers=? WHERE id=?', (json.dumps({'1': 1}), attempt['id']))
        _, result = self.request(client, 'attempts/' + str(attempt['id']) + '/submit', {'answers': {'1': 1, '2': 2, '3': 3, '4': 1}}, csrf)
        self.assertEqual(result['score'], 25)
        self.assertTrue(result['submitted_at'])

    def test_admin_protection_and_session_revocation(self):
        client, csrf = self.client('admin')
        self.assertEqual(self.request(client, 'users/1', {'role': 'learner', 'status': 'active'}, csrf)[0], 400)
        target, _ = self.client('tuananh')
        self.assertEqual(self.request(client, 'users/5', {'role': 'manager', 'status': 'active'}, csrf)[0], 200)
        self.assertEqual(self.request(target, 'bootstrap')[0], 401)
        self.assertEqual(self.request(client, 'users/5', {'role': 'learner', 'status': 'active'}, csrf)[0], 200)


if __name__ == '__main__':
    unittest.main()
