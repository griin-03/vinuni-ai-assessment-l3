"""One authoring workflow: authorized sources -> checked draft -> human approval."""
import json
import re
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path

from rag_domain import CATEGORIES, PROMPT_VERSION, canonical, compact, digest, folded, request_gate, terms, verify_item
from rag_store import add_version
from workspace_errors import APIError, require


def utc(timestamp=None):
    return datetime.fromtimestamp(time.time() if timestamp is None else timestamp, timezone.utc).isoformat(timespec='seconds')


def event(db, actor, action, detail):
    db.execute('INSERT INTO audit(actor,action,detail,created_at) VALUES(?,?,?,?)', (actor, action, detail, utc()))


def can_read_document(actor, document):
    return actor['role'] in ('training', 'admin') and (actor['role'] == 'admin' or document['department_id'] is None or document['department_id'] == actor['department_id'])


def question_scope_allowed(actor, question):
    provenance = json.loads(question['provenance']) if 'provenance' in question.keys() else {}
    department = provenance.get('department_id')
    return department is None or actor['role'] == 'admin' or actor['department_id'] == department


def ensure_question_usable(db, actor, question):
    require(question_scope_allowed(actor, question), 'Câu hỏi nằm ngoài phạm vi tài liệu được phép sử dụng.', 403)
    provenance = json.loads(question['provenance']) if 'provenance' in question.keys() else {}
    for citation in provenance.get('citations', []):
        doc = db.execute('SELECT * FROM knowledge_documents WHERE id=?', (citation['document_id'],)).fetchone()
        require(doc and doc['status'] == 'active' and doc['current_version_id'] == citation['version_id'], 'Nguồn của câu hỏi đã thay đổi hoặc bị thu hồi. Cần kiểm tra lại trước khi sử dụng cho đợt mới.', 409)


class GroundedAuthoring:
    def __init__(self, db, actor, clock=time.time):
        self.db, self.actor, self.clock = db, actor, clock

    def _staff(self):
        require(self.actor['role'] in ('training', 'admin'), 'Chức năng soạn nội dung chỉ dành cho giáo viên và quản trị.', 403)

    def _document(self, document_id):
        self._staff()
        doc = self.db.execute('SELECT * FROM knowledge_documents WHERE id=?', (document_id,)).fetchone()
        require(doc and can_read_document(self.actor, doc), 'Tài liệu không tồn tại trong phạm vi truy cập của bạn.', 404)
        return doc

    def documents(self):
        self._staff()
        return [dict(r) for r in self.db.execute('SELECT d.*,v.version,v.content_hash,v.effective_from,length(v.content) characters,(SELECT COUNT(*) FROM knowledge_chunks c WHERE c.version_id=v.id) chunks FROM knowledge_documents d JOIN knowledge_versions v ON v.id=d.current_version_id WHERE (?="admin" OR d.department_id IS NULL OR d.department_id=?) ORDER BY d.id DESC', (self.actor['role'], self.actor['department_id']))]

    def document_detail(self, document_id, version_id=None):
        doc = self._document(document_id)
        version = self.db.execute('SELECT * FROM knowledge_versions WHERE document_id=? AND id=?', (doc['id'], version_id or doc['current_version_id'])).fetchone()
        require(version, 'Không tìm thấy phiên bản tài liệu.', 404)
        chunks = [{**dict(r), 'risk_flags': json.loads(r['risk_flags'])} for r in self.db.execute('SELECT * FROM knowledge_chunks WHERE version_id=? ORDER BY start', (version['id'],))]
        return {'document': dict(doc), 'version': dict(version), 'versions': [dict(r) for r in self.db.execute('SELECT id,version,content_hash,effective_from,created_at FROM knowledge_versions WHERE document_id=? ORDER BY version DESC', (doc['id'],))], 'chunks': chunks}

    def save_document(self, data, document_id=None):
        self._staff()
        require(data.get('source_confirmed') is True, 'Xác nhận tài liệu được phép sử dụng và đã được kiểm tra trước khi nhập.')
        title, content, category = data.get('title', ''), data.get('content', ''), data.get('category')
        require(isinstance(title, str) and 5 <= len(title.strip()) <= 160, 'Tên tài liệu cần từ 5 đến 160 ký tự.')
        require(isinstance(content, str) and 80 <= len(content.strip()) <= 100000, 'Nhập nội dung văn bản từ 80 đến 100.000 ký tự. Hiện hỗ trợ TXT và Markdown.')
        require(category in CATEGORIES, 'Nhóm tài liệu chưa hợp lệ.')
        effective = data.get('effective_from', utc(self.clock())[:10])
        try: datetime.strptime(effective, '%Y-%m-%d')
        except (ValueError, TypeError): raise APIError(400, 'Ngày hiệu lực chưa hợp lệ.')
        if document_id:
            doc = self._document(document_id)
            require(data.get('expected_version_id') == doc['current_version_id'], 'Tài liệu đã có phiên bản mới. Tải lại trước khi cập nhật.', 409)
            department = doc['department_id']
        else:
            department = data.get('department_id')
            require(department is None or isinstance(department, int) and not isinstance(department, bool), 'Phạm vi tài liệu chưa hợp lệ.')
            require(department is None or self.db.execute('SELECT 1 FROM departments WHERE id=?', (department,)).fetchone(), 'Phòng ban không tồn tại.')
            require(self.actor['role'] == 'admin' or department in (None, self.actor['department_id']), 'Bạn chỉ được nhập tài liệu chung hoặc thuộc nhóm được phân công.', 403)
            row = self.db.execute('INSERT INTO knowledge_documents(title,category,department_id,owner_id,created_at) VALUES(?,?,?,?,?)', (title.strip(), category, department, self.actor['id'], utc(self.clock())))
            document_id = row.lastrowid
        version_id = add_version(self.db, document_id, content.strip(), effective, self.actor['id'], utc(self.clock()))
        self.db.execute('UPDATE knowledge_documents SET title=?,category=? WHERE id=?', (title.strip(), category, document_id))
        event(self.db, self.actor['id'], 'knowledge.version_created', 'Tạo phiên bản nguồn KB-' + str(document_id) + ' / V-' + str(version_id))
        return {'id': document_id, 'version_id': version_id}

    def archive(self, document_id, expected_version_id):
        doc = self._document(document_id)
        require(expected_version_id == doc['current_version_id'], 'Nguồn đã thay đổi. Tải lại trước khi thu hồi.', 409)
        self.db.execute('UPDATE knowledge_documents SET status="archived" WHERE id=?', (doc['id'],))
        event(self.db, self.actor['id'], 'knowledge.archived', 'Thu hồi nguồn KB-' + str(doc['id']))
        return {'ok': True}

    def retrieve(self, request, limit=6):
        self._staff()
        ids = request.get('document_ids', [])
        require(isinstance(ids, list) and 1 <= len(ids) <= 12 and all(isinstance(i, int) and not isinstance(i, bool) for i in ids), 'Chọn từ 1 đến 12 tài liệu.')
        for document_id in ids:
            doc = self._document(document_id)
            version = self.db.execute('SELECT effective_from FROM knowledge_versions WHERE id=?', (doc['current_version_id'],)).fetchone()
            require(doc['status'] == 'active' and version['effective_from'] <= utc(self.clock())[:10], 'Một tài liệu đã thu hồi hoặc chưa có hiệu lực. Chọn lại nguồn hiện hành.', 409)
        keywords = terms(request.get('topic', ''))
        if not keywords: return []
        expression = ' OR '.join('"' + t.replace('"', '""') + '"' for t in keywords)
        sql = '''SELECT c.*,v.document_id,v.version,v.content_hash,d.title,d.category,d.department_id,bm25(knowledge_fts) rank
                 FROM knowledge_fts JOIN knowledge_chunks c ON c.id=knowledge_fts.rowid
                 JOIN knowledge_versions v ON v.id=c.version_id JOIN knowledge_documents d ON d.id=v.document_id
                 WHERE knowledge_fts MATCH ? AND d.status='active' AND d.current_version_id=v.id AND v.effective_from<=?
                 AND (?='admin' OR d.department_id IS NULL OR d.department_id=?)
                 AND d.id IN (''' + ','.join('?' for _ in ids) + ') ORDER BY rank,c.id LIMIT 30'
        rows = self.db.execute(sql, [expression, utc(self.clock())[:10], self.actor['role'], self.actor['department_id'], *ids]).fetchall()
        results = []
        topic_words = re.findall(r'[\w]+', folded(request.get('topic', '')))
        phrases = [' '.join(topic_words[i:i + 2]) for i in range(len(topic_words) - 1)]
        for row in rows:
            flags = json.loads(row['risk_flags'])
            normalized = re.findall(r'[\w]+', folded(row['text']))
            overlap = len(set(keywords) & set(normalized))
            phrase_supported = len(keywords) < 2 or any(phrase in ' '.join(normalized) for phrase in phrases)
            if flags or overlap < min(2, len(keywords)) or not phrase_supported: continue
            results.append({**dict(row), 'chunk_id': row['id'], 'risk_flags': flags, 'matched_terms': overlap})
        return results[:limit]

    def create_job(self, data):
        self._staff()
        key = data.get('request_key', '')
        require(isinstance(key, str) and re.fullmatch(r'[a-zA-Z0-9_-]{8,80}', key), 'Mã yêu cầu chưa hợp lệ.')
        topic, audience, count = data.get('topic', ''), data.get('audience', ''), data.get('count', 3)
        require(isinstance(topic, str) and len(topic) <= 500 and isinstance(audience, str) and len(audience) <= 120, 'Chủ đề hoặc đối tượng vượt giới hạn.')
        require(isinstance(count, int) and not isinstance(count, bool) and 1 <= count <= 5, 'Mỗi lượt soạn từ 1 đến 5 câu hỏi.')
        require(data.get('category') in CATEGORIES, 'Chọn nhóm câu hỏi.')
        require(data.get('provider', 'extractive') == 'extractive', 'Chưa kết nối mô hình. Hiện chỉ có chế độ trích xuất cục bộ, không phải LLM.', 409)
        ids = data.get('document_ids', [])
        require(isinstance(ids, list) and len(ids) <= 12 and all(isinstance(i, int) and not isinstance(i, bool) for i in ids), 'Danh sách tài liệu chưa hợp lệ.')
        for i in ids: self._document(i)
        request = {'topic': topic.strip(), 'audience': audience.strip(), 'count': count, 'category': data['category'], 'document_ids': sorted(set(ids))}
        request_hash = digest(canonical(request))
        existing = self.db.execute('SELECT * FROM ai_jobs WHERE user_id=? AND request_key=?', (self.actor['id'], key)).fetchone()
        if existing:
            require(existing['request_hash'] == request_hash, 'Mã yêu cầu đã dùng cho nội dung khác. Tạo yêu cầu mới.', 409)
            return {'id': existing['id'], 'status': existing['status'], 'reused': True}
        count_active = self.db.execute('SELECT COUNT(*) FROM ai_jobs WHERE user_id=? AND status IN ("queued","running")', (self.actor['id'],)).fetchone()[0]
        require(count_active < 3, 'Bạn đang có 3 yêu cầu chờ xử lý. Hoàn tất trước khi tạo thêm.', 429)
        decision, message = request_gate(request)
        status = 'queued' if decision == 'ready' else 'completed'
        cur = self.db.execute('INSERT INTO ai_jobs(user_id,request_key,request_hash,request,status,decision,message,provider,prompt_version,created_at,finished_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)', (self.actor['id'], key, request_hash, canonical(request), status, decision, message, 'extractive', PROMPT_VERSION, utc(self.clock()), utc(self.clock()) if status == 'completed' else None))
        event(self.db, self.actor['id'], 'authoring.requested', 'Tạo yêu cầu soạn có nguồn DR-' + str(cur.lastrowid) + ' · trích xuất cục bộ')
        return {'id': cur.lastrowid, 'status': status, 'decision': decision}

    def _job(self, job_id):
        self._staff()
        row = self.db.execute('SELECT * FROM ai_jobs WHERE id=? AND user_id=?', (job_id, self.actor['id'])).fetchone()
        require(row, 'Không tìm thấy yêu cầu trong không gian của bạn.', 404)
        return row

    def _check_sources(self, sources, current=True):
        for source in sources:
            doc = self._document(source['document_id'])
            require(not current or doc['status'] == 'active' and doc['current_version_id'] == source['version_id'], 'Nguồn đã thay đổi hoặc bị thu hồi. Tạo bản nháp mới từ phiên bản hiện hành.', 409)
            version = self.db.execute('SELECT content_hash,effective_from FROM knowledge_versions WHERE id=? AND document_id=?', (source['version_id'], doc['id'])).fetchone()
            require(version and version['content_hash'] == source['content_hash'], 'Không xác minh được phiên bản nguồn.', 409)
            require(not current or version['effective_from'] <= utc(self.clock())[:10], 'Nguồn chưa có hiệu lực.', 409)

    def jobs(self):
        self._staff()
        return [{**dict(r), 'request': json.loads(r['request'])} for r in self.db.execute('SELECT id,request,status,decision,message,provider,created_at,finished_at FROM ai_jobs WHERE user_id=? ORDER BY id DESC LIMIT 50', (self.actor['id'],))]

    def job_detail(self, job_id):
        job = self._job(job_id)
        sources = json.loads(job['sources']); self._check_sources(sources, current=False)
        current = True
        try: self._check_sources(sources)
        except APIError: current = False
        result = {**dict(job), 'request': json.loads(job['request']), 'sources': sources, 'usage': json.loads(job['usage']), 'sources_current': current}
        result.pop('lease_token', None); result.pop('request_hash', None)
        result['items'] = [{**dict(r), 'options': json.loads(r['options']), 'citations': json.loads(r['citations']), 'validation': json.loads(r['validation'])} for r in self.db.execute('SELECT * FROM ai_items WHERE job_id=? ORDER BY ordinal', (job_id,))]
        return result

    def save_output(self, job_id, output, lease_token, metadata=None):
        job = self._job(job_id)
        require(job['status'] == 'running' and job['lease_token'] == lease_token, 'Yêu cầu đã được xử lý bởi tiến trình khác.', 409)
        sources = json.loads(job['sources']); self._check_sources(sources)
        require(isinstance(output, dict), 'Bộ soạn trả về nội dung không hợp lệ.')
        decision = output.get('decision')
        require(decision in ('draft', 'insufficient_evidence', 'needs_clarification', 'out_of_scope'), 'Trạng thái đầu ra không hợp lệ.')
        items = output.get('items', [])
        request = json.loads(job['request'])
        require(isinstance(items, list) and len(items) <= request['count'], 'Đầu ra vượt số câu hỏi được yêu cầu.')
        require(decision != 'draft' or len(items) > 0, 'Bộ soạn trả về bản nháp rỗng; cần kiểm tra adapter.')
        if decision != 'draft': items = []
        for ordinal, item in enumerate(items, 1):
            validation = verify_item(item, sources)
            candidate = item if isinstance(item, dict) else {}
            options = candidate.get('options', [])
            if not isinstance(options, list) or not all(isinstance(o, str) for o in options): options = []
            citations = candidate.get('citations', [])
            if not isinstance(citations, list): citations = []
            self.db.execute('INSERT INTO ai_items(job_id,ordinal,question,options,correct,category,citations,validation,status) VALUES(?,?,?,?,?,?,?,?,?)', (job_id, ordinal, str(candidate.get('question', ''))[:800], canonical(options), candidate.get('correct') if isinstance(candidate.get('correct'), int) and not isinstance(candidate.get('correct'), bool) else None, request['category'], canonical(citations), canonical(validation), 'needs_review' if validation['valid'] else 'blocked'))
        self.db.execute('UPDATE ai_jobs SET status="completed",decision=?,message=?,usage=?,finished_at=?,lease_token=NULL,lease_until=NULL WHERE id=?', (decision, str(output.get('message', ''))[:600], canonical(metadata or {}), utc(self.clock()), job_id))
        event(self.db, self.actor['id'], 'authoring.checked', 'Kiểm tra trích dẫn cho DR-' + str(job_id) + ' · ' + str(len(items)) + ' bản nháp')

    def edit_item(self, item_id, data):
        row = self.db.execute('SELECT * FROM ai_items WHERE id=?', (item_id,)).fetchone()
        require(row, 'Không tìm thấy bản nháp.', 404)
        job = self._job(row['job_id'])
        require(row['status'] not in ('approved', 'rejected'), 'Bản nháp đã được xử lý, không thể sửa.', 409)
        require(data.get('expected_revision') == row['revision'], 'Bản nháp đã thay đổi. Tải lại trước khi sửa.', 409)
        sources = json.loads(job['sources']); self._check_sources(sources)
        item = {'question': data.get('question'), 'options': data.get('options'), 'correct': data.get('correct'), 'citations': json.loads(row['citations'])}
        validation = verify_item(item, sources)
        require(not any(e in validation['errors'] for e in ('invalid_question', 'invalid_options', 'invalid_correct')), 'Nội dung câu hỏi, bốn phương án hoặc đáp án đúng chưa hợp lệ.')
        self.db.execute('UPDATE ai_items SET question=?,options=?,correct=?,validation=?,status=?,revision=revision+1 WHERE id=?', (item['question'].strip(), canonical(item['options']), item['correct'], canonical(validation), 'needs_review' if validation['valid'] else 'blocked', item_id))
        event(self.db, self.actor['id'], 'authoring.edited', 'Sửa bản nháp IT-' + str(item_id))
        return {'ok': True}

    def review(self, item_id, data):
        row = self.db.execute('SELECT * FROM ai_items WHERE id=?', (item_id,)).fetchone()
        require(row, 'Không tìm thấy bản nháp.', 404)
        job = self._job(row['job_id'])
        decision = data.get('decision')
        require(decision in ('approve', 'reject'), 'Chọn duyệt hoặc từ chối.')
        if row['status'] == 'approved' and decision == 'approve':
            return {'ok': True, 'question_id': row['question_id'], 'reused': True}
        require(row['status'] not in ('approved', 'rejected'), 'Bản nháp đã có quyết định, không thể thay đổi.', 409)
        require(data.get('expected_revision') == row['revision'], 'Bản nháp đã thay đổi. Kiểm tra lại trước khi duyệt.', 409)
        comment = data.get('comment', '')
        require(isinstance(comment, str) and 5 <= len(comment.strip()) <= 1000, 'Ghi lý do hoặc kết quả đối chiếu, tối thiểu 5 ký tự.')
        question_id = None
        if decision == 'approve':
            require(data.get('grounding_checked') is True and data.get('options_checked') is True, 'Cần xác nhận đã kiểm tra ý nghĩa trích dẫn và bốn phương án trả lời.')
            sources = json.loads(job['sources']); self._check_sources(sources)
            item = {'question': row['question'], 'options': json.loads(row['options']), 'correct': row['correct'], 'citations': json.loads(row['citations'])}
            validation = verify_item(item, sources)
            require(validation['valid'], 'Trích dẫn hoặc đáp án không vượt kiểm tra. Sửa bản nháp trước khi duyệt.', 409)
            departments = {s['department_id'] for s in sources if s['chunk_id'] in {e['chunk_id'] for e in validation['evidence']} and s['department_id'] is not None}
            require(len(departments) <= 1, 'Nguồn thuộc các phạm vi riêng khác nhau; không thể tạo một câu hỏi chung.')
            provenance = {'job_id': job['id'], 'item_id': item_id, 'provider': job['provider'], 'prompt_version': job['prompt_version'], 'guard_version': validation['guard_version'], 'citations': validation['evidence'], 'reviewer_id': self.actor['id'], 'reviewed_at': utc(self.clock()), 'review_comment': comment.strip(), 'department_id': next(iter(departments)) if departments else None}
            explanation = '\n'.join('Theo ' + e['title'] + ' (v' + str(e['version']) + ', dòng ' + str(e['line_start']) + '): ' + e['quote'] for e in validation['evidence'])
            cur = self.db.execute('INSERT INTO questions(prompt,options,correct,explanation,category,created_at,source_ai_item_id,provenance) VALUES(?,?,?,?,?,?,?,?)', (row['question'], row['options'], row['correct'], explanation, row['category'], utc(self.clock()), item_id, canonical(provenance)))
            question_id = cur.lastrowid
        self.db.execute('UPDATE ai_items SET status=?,revision=revision+1,reviewer_id=?,review_comment=?,question_id=?,reviewed_at=? WHERE id=?', ('approved' if decision == 'approve' else 'rejected', self.actor['id'], comment.strip(), question_id, utc(self.clock()), item_id))
        event(self.db, self.actor['id'], 'authoring.approved' if decision == 'approve' else 'authoring.rejected', 'Duyệt bản nháp IT-' + str(item_id) + (' → CH-' + str(question_id) if question_id else ' · từ chối'))
        return {'ok': True, 'question_id': question_id}
