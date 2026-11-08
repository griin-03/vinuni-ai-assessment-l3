import concurrent.futures
import json
from pathlib import Path
import sqlite3
import tempfile
import time
import unittest
from unittest.mock import patch
import uuid

import test_workspace as common
import workspace_store as store
from rag_worker import process_one


class GroundedAuthoringHTTP(unittest.TestCase):
    client = common.WorkspaceIntegration.client
    request = common.WorkspaceIntegration.request

    @classmethod
    def setUpClass(cls):
        common.WorkspaceIntegration.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        common.WorkspaceIntegration.tearDownClass.__func__(cls)

    def doc_id(self, key):
        with store.connection() as db:
            return db.execute('SELECT id FROM knowledge_documents WHERE sample_key=?', (key,)).fetchone()[0]

    def create_draft(self, client, token, did=None, topic='báo cáo sự cố bảo mật'):
        data = {'request_key': uuid.uuid4().hex, 'topic': topic, 'audience': 'Nhân viên mới', 'count': 1, 'category': 'Tuân thủ', 'document_ids': [did or self.doc_id('security')], 'provider': 'extractive'}
        status, result = self.request(client, 'ai/drafts', data, token)
        self.assertEqual(status, 200, result)
        for _ in range(20):
            process_one()
            status, detail = self.request(client, 'ai/drafts/' + str(result['id']))
            if detail['status'] not in ('queued', 'running'): break
        self.assertEqual(detail['status'], 'completed', detail)
        self.assertTrue(detail['items'], detail)
        return detail

    def approve(self, client, token, item):
        return self.request(client, 'ai/items/' + str(item['id']) + '/review', {'decision': 'approve', 'expected_revision': item['revision'], 'grounding_checked': True, 'options_checked': True, 'comment': 'Đã đối chiếu ý nghĩa, nguồn và phương án nhiễu trong bản mẫu.'}, token)

    def test_acl_and_no_external_provider(self):
        learner, token = self.client()
        self.assertEqual(self.request(learner, 'knowledge/documents')[0], 403)
        self.assertEqual(self.request(learner, 'ai/overview')[0], 403)
        training, token = self.client('training')
        self.assertEqual(self.request(training, 'knowledge/documents/' + str(self.doc_id('ops-private')))[0], 404)
        _, overview = self.request(training, 'ai/overview')
        self.assertFalse(overview['capabilities']['external_egress'])
        self.assertFalse(overview['capabilities']['is_llm'])
        self.assertEqual(self.request(training, 'ai/drafts', {'request_key': uuid.uuid4().hex, 'topic': 'bảo mật tài khoản', 'audience': 'Nhân viên', 'category': 'Tuân thủ', 'count': 1, 'document_ids': [self.doc_id('security')], 'provider': 'openai'}, token)[0], 409)

    def test_job_ownership_and_approval_requires_human(self):
        client, csrf = self.client('training')
        job = self.create_draft(client, csrf)
        admin, _ = self.client('admin')
        self.assertEqual(self.request(admin, 'ai/drafts/' + str(job['id']))[0], 404)
        item = job['items'][0]
        payload = {'decision': 'approve', 'expected_revision': item['revision'], 'comment': 'Chưa có xác nhận ngữ nghĩa.'}
        self.assertEqual(self.request(client, 'ai/items/' + str(item['id']) + '/review', payload, csrf)[0], 400)
        self.assertEqual(self.approve(client, csrf, item)[0], 200)
        _, repeated = self.approve(client, csrf, item)
        self.assertTrue(repeated['reused'])
        with store.connection() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM questions WHERE source_ai_item_id=?', (item['id'],)).fetchone()[0], 1)

    def test_concurrent_review_and_stale_edit(self):
        client, csrf = self.client('training')
        job = self.create_draft(client, csrf); item = job['items'][0]
        payload = {'expected_revision': item['revision'], 'question': item['question'], 'options': item['options'], 'correct': item['correct']}
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(self.request, client, 'ai/items/' + str(item['id']) + '/edit', payload, csrf) for _ in range(2)]
            statuses = sorted(f.result()[0] for f in futures)
        self.assertEqual(statuses, [200, 409])
        _, fresh = self.request(client, 'ai/drafts/' + str(job['id'])); item = fresh['items'][0]
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: self.approve(client, csrf, item), range(2)))
        self.assertEqual([r[0] for r in results], [200, 200])
        self.assertEqual(results[0][1]['question_id'], results[1][1]['question_id'])

    def test_new_source_version_blocks_old_review(self):
        client, csrf = self.client('training')
        body = {'title': 'Nguồn kiểm thử có phiên bản', 'content': '# Bảo mật nội bộ\n\nNhân viên phải báo cáo sự cố bảo mật cho quản lý trực tiếp trong vòng 30 phút sau khi phát hiện.', 'category': 'Tuân thủ', 'department_id': None, 'effective_from': store.now_iso()[:10], 'source_confirmed': True}
        _, source = self.request(client, 'knowledge/documents', body, csrf)
        job = self.create_draft(client, csrf, source['id'])
        _, detail = self.request(client, 'knowledge/documents/' + str(source['id']))
        body.update({'expected_version_id': detail['version']['id'], 'content': body['content'].replace('30 phút', '15 phút')})
        self.assertEqual(self.request(client, 'knowledge/documents/' + str(source['id']) + '/versions', body, csrf)[0], 200)
        self.assertEqual(self.approve(client, csrf, job['items'][0])[0], 409)
        _, historical = self.request(client, 'knowledge/documents/' + str(source['id']) + '/versions/' + str(detail['version']['id']))
        self.assertIn('30 phút', historical['version']['content'])

    def test_private_source_cannot_escape_through_quiz(self):
        training, csrf = self.client('training')
        job = self.create_draft(training, csrf, self.doc_id('hr-private'), 'phân quyền hồ sơ nhân sự')
        _, approved = self.approve(training, csrf, job['items'][0])
        _, exam = self.request(training, 'exams', {'title': 'Khảo thí nguồn riêng HR', 'description': 'Chỉ nhân sự đúng phạm vi nguồn được giao bài.', 'question_ids': [approved['question_id']], 'duration': 5, 'pass_score': 100, 'max_attempts': 1, 'due': store.now_iso(7)}, csrf)
        self.assertEqual(self.request(training, 'exams/' + str(exam['id']) + '/status', {'status': 'published'}, csrf)[0], 200)
        self.assertEqual(self.request(training, 'exams/' + str(exam['id']) + '/assign', {'user_ids': [4]}, csrf)[0], 403)
        self.assertEqual(self.request(training, 'exams/' + str(exam['id']) + '/assign', {'user_ids': [2]}, csrf)[0], 200)
        _, attempt = self.request(training, 'exams/' + str(exam['id']) + '/start', {}, csrf)
        self.assertNotIn('provenance', attempt['questions'][0])
        self.assertNotIn('explanation', attempt['questions'][0])
        self.assertNotIn('correct', attempt['questions'][0])
        learner, token = self.client('learner')
        self.assertEqual(self.request(learner, 'exams/' + str(exam['id']) + '/start', {}, token)[0], 403)

    def test_request_replay_is_bound_to_payload(self):
        client, csrf = self.client('training')
        data = {'request_key': uuid.uuid4().hex, 'topic': 'báo cáo sự cố bảo mật', 'audience': 'Nhân viên', 'category': 'Tuân thủ', 'count': 1, 'document_ids': [self.doc_id('security')]}
        _, first = self.request(client, 'ai/drafts', data, csrf)
        _, second = self.request(client, 'ai/drafts', data, csrf)
        self.assertEqual(first['id'], second['id'])
        data['topic'] = 'khóa màn hình khi rời bàn'
        self.assertEqual(self.request(client, 'ai/drafts', data, csrf)[0], 409)

    def test_migration_preserves_existing_records(self):
        original = store.DB_PATH
        try:
            with tempfile.TemporaryDirectory() as temp:
                store.DB_PATH = Path(temp) / 'legacy.sqlite3'
                with patch.object(store, 'migrate_rag', lambda db, now: None): store.init_store()
                with store.connection() as db:
                    users = [tuple(r) for r in db.execute('SELECT * FROM users ORDER BY id')]
                    attempts = [tuple(r) for r in db.execute('SELECT * FROM attempts ORDER BY id')]
                    questions = [tuple(r) for r in db.execute('SELECT * FROM questions ORDER BY id')]
                store.init_store(); store.init_store()
                with store.connection() as db:
                    self.assertEqual(users, [tuple(r) for r in db.execute('SELECT * FROM users ORDER BY id')])
                    self.assertEqual(attempts, [tuple(r) for r in db.execute('SELECT * FROM attempts ORDER BY id')])
                    self.assertEqual(questions, [tuple(r) for r in db.execute('SELECT id,prompt,options,correct,explanation,category,created_at FROM questions ORDER BY id')])
                    self.assertEqual(db.execute('SELECT COUNT(*) FROM schema_migrations WHERE version=1').fetchone()[0], 1)
        finally: store.DB_PATH = original

    def test_worker_recovers_expired_lease_without_duplicate_items(self):
        client, csrf = self.client('training')
        while process_one(): pass
        data = {'request_key': uuid.uuid4().hex, 'topic': 'báo cáo sự cố bảo mật', 'audience': 'Nhân viên', 'category': 'Tuân thủ', 'count': 1, 'document_ids': [self.doc_id('security')]}
        _, created = self.request(client, 'ai/drafts', data, csrf)
        with store.connection() as db:
            db.execute('UPDATE ai_jobs SET status="running",lease_token="interrupted",lease_until=0,run_count=1 WHERE id=?', (created['id'],))
        self.assertTrue(process_one())
        self.assertFalse(process_one())
        _, job = self.request(client, 'ai/drafts/' + str(created['id']))
        self.assertEqual(job['status'], 'completed')
        self.assertEqual(len(job['items']), 1)
        self.assertEqual(job['run_count'], 2)

    def test_malformed_adapter_output_is_blocked_not_published(self):
        class Malformed:
            name, is_llm = 'test-fixture', False
            def generate(self, request, sources):
                return {'decision': 'draft', 'items': [{'question': 'Câu hỏi kiểm tra đầu ra không đáng tin cậy?', 'options': {'bad': 'schema'}, 'correct': 0, 'citations': [{'chunk_id': [], 'quote': 'Không phải một trích dẫn hợp lệ trong tài liệu.'}]}]}
        while process_one(): pass
        client, csrf = self.client('training')
        _, created = self.request(client, 'ai/drafts', {'request_key': uuid.uuid4().hex, 'topic': 'báo cáo sự cố bảo mật', 'audience': 'Nhân viên', 'category': 'Tuân thủ', 'count': 1, 'document_ids': [self.doc_id('security')]}, csrf)
        self.assertTrue(process_one(provider=Malformed()))
        _, job = self.request(client, 'ai/drafts/' + str(created['id']))
        self.assertEqual(job['items'][0]['status'], 'blocked')
        self.assertEqual(job['items'][0]['options'], [])
        self.assertEqual(self.approve(client, csrf, job['items'][0])[0], 409)

    def test_adapter_failure_does_not_silently_fallback(self):
        class Failure:
            name, is_llm = 'test-fixture', False
            def generate(self, request, sources): raise RuntimeError('fixture failure')
        while process_one(): pass
        client, csrf = self.client('training')
        _, created = self.request(client, 'ai/drafts', {'request_key': uuid.uuid4().hex, 'topic': 'báo cáo sự cố bảo mật', 'audience': 'Nhân viên', 'category': 'Tuân thủ', 'count': 1, 'document_ids': [self.doc_id('security')]}, csrf)
        with self.assertLogs(level='ERROR'): self.assertTrue(process_one(provider=Failure()))
        _, job = self.request(client, 'ai/drafts/' + str(created['id']))
        self.assertEqual(job['status'], 'failed')
        self.assertEqual(job['items'], [])


if __name__ == '__main__': unittest.main()
