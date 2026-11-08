"""Narrow teacher workflow ported from EduTech AI; see docs/product/assessment-mvp.md.

One school per database. Paper and room ownership are checked independently of UI.
"""
import csv
import hashlib
import io
import json
import re
import time
from datetime import datetime, timezone

from workspace_errors import APIError, require
from workspace_store import audit, now_iso
from rag_service import ensure_question_usable, question_scope_allowed
from assessment_runtime import attempt_data, settle_expired

SUBJECTS = ('Toán', 'Ngữ văn', 'Tiếng Anh', 'Vật lý', 'Hóa học', 'Sinh học', 'Lịch sử', 'Địa lý', 'Tin học', 'Khoa học tự nhiên', 'Giáo dục công dân')


def string(data, key, minimum=0, maximum=2000):
    value = data.get(key, '')
    require(isinstance(value, str) and minimum <= len(value.strip()) <= maximum, 'Kiểm tra trường ' + key + '.')
    return value.strip()


def integer(data, key, minimum, maximum):
    value = data.get(key)
    require(type(value) is int and minimum <= value <= maximum, 'Kiểm tra trường ' + key + '.')
    return value


def timestamp(value):
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        require(result.tzinfo is not None, 'Lịch thi cần kèm múi giờ.')
        return result.timestamp()
    except (AttributeError, TypeError, ValueError):
        raise APIError(400, 'Lịch thi chưa hợp lệ.')


def teacher_support(value):
    # Adapted from src/lib/question-teacher-support.ts getQuestionTeacherSupport.
    value = value if isinstance(value, dict) else {}
    return {key: re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', value.get(key, '').replace('[SLASH]', '\\'))[:limit].strip() if isinstance(value.get(key, ''), str) else '' for key, limit in (('hint', 1200), ('solution', 8000), ('teachingNotes', 2400))}


class Assessment:
    def __init__(self, db, actor):
        self.db, self.actor = db, actor

    def staff(self):
        require(self.actor['role'] in ('training', 'admin'), 'Chỉ giáo viên hoặc quản trị được quản lý đề và phòng thi.', 403)

    def owned(self, table, ident):
        self.staff()
        row = self.db.execute('SELECT * FROM ' + table + ' WHERE id=?', (ident,)).fetchone()
        require(row and (row['owner_id'] == self.actor['id'] or self.actor['role'] == 'admin'), 'Không tìm thấy nội dung thuộc quyền quản lý của bạn.', 404)
        return row

    def paper_data(self, paper):
        result = dict(paper)
        result['items'] = json.loads(result['items'])
        release = self.db.execute('SELECT id,content_hash,created_at FROM assessment_releases WHERE paper_id=?', (paper['id'],)).fetchone()
        result['release'] = dict(release) if release else None
        return result

    def papers(self):
        self.staff()
        rows = self.db.execute('SELECT * FROM assessment_papers ' + ('' if self.actor['role'] == 'admin' else 'WHERE owner_id=? ') + 'ORDER BY updated_at DESC', () if self.actor['role'] == 'admin' else (self.actor['id'],))
        return [self.paper_data(row) for row in rows]

    def clean_items(self, items, strict=False):
        require(isinstance(items, list) and len(items) <= 100, 'Mỗi đề có tối đa 100 câu.')
        require(not strict or items, 'Đề cần có ít nhất một câu hỏi.')
        clean, ids, sources = [], set(), set()
        for i, item in enumerate(items):
            require(isinstance(item, dict), 'Câu hỏi chưa hợp lệ.')
            ident = string(item, 'id', 1, 64)
            require(re.fullmatch(r'[a-zA-Z0-9_-]+', ident) and ident not in ids, 'Định danh câu hỏi bị trùng hoặc chưa hợp lệ.')
            ids.add(ident)
            source = item.get('source_question_id')
            if source is not None:
                require(type(source) is int and source > 0 and source not in sources, 'Câu hỏi nguồn bị trùng hoặc chưa hợp lệ.')
                sources.add(source)
                row = self.db.execute('SELECT * FROM questions WHERE id=?', (source,)).fetchone()
                require(row, 'Câu hỏi nguồn không tồn tại.', 404)
                ensure_question_usable(self.db, self.actor, row)
                clean.append({'id': ident, 'source_question_id': source, 'prompt': row['prompt'], 'options': json.loads(row['options']), 'correct': row['correct'], 'explanation': row['explanation'], 'category': row['category'], 'objective': string(item, 'objective', 0, 120), 'provenance': json.loads(row['provenance'])})
                continue
            prompt = string(item, 'prompt', 10 if strict else 0, 2000)
            options = item.get('options', [])
            require(isinstance(options, list) and len(options) == 4 and all(isinstance(o, str) and len(o.strip()) <= 500 for o in options), 'Câu ' + str(i + 1) + ' cần bốn phương án.')
            options = [o.strip() for o in options]
            correct = item.get('correct')
            require(correct is None and not strict or type(correct) is int and 0 <= correct < 4, 'Chọn đáp án đúng cho câu ' + str(i + 1) + '.')
            if strict:
                require(all(options) and len({o.casefold() for o in options}) == 4, 'Câu ' + str(i + 1) + ' cần bốn phương án khác nhau, không để trống.')
            clean.append({'id': ident, 'prompt': prompt, 'options': options, 'correct': correct, 'explanation': string(item, 'explanation', 5 if strict else 0, 2000), 'category': string(item, 'category', 0, 80), 'objective': string(item, 'objective', 0, 120), 'teacherSupport': teacher_support(item.get('teacherSupport'))})
        return clean

    def save_paper(self, body, ident=None):
        self.staff()
        existing = self.owned('assessment_papers', ident) if ident else None
        if existing:
            require(existing['status'] == 'draft', 'Đề đã chốt. Hãy nhân bản để sửa phiên bản mới.', 409)
            require(body.get('expected_revision') == existing['revision'] and type(body.get('expected_revision')) is int, 'Bản nháp đã được sửa ở tab khác. Tải lại trước khi lưu.', 409)
        subject = string(body, 'subject', 2, 80)
        require(subject in SUBJECTS, 'Chọn môn học được hỗ trợ.')
        values = (string(body, 'title', 5, 160), string(body, 'description', 0, 1500), subject, integer(body, 'grade', 6, 12), json.dumps(self.clean_items(body.get('items', [])), ensure_ascii=False))
        if existing:
            self.db.execute('UPDATE assessment_papers SET title=?,description=?,subject=?,grade=?,items=?,revision=revision+1,updated_at=? WHERE id=?', (*values, now_iso(), ident))
        else:
            ident = self.db.execute('INSERT INTO assessment_papers(title,description,subject,grade,items,owner_id,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)', (*values, self.actor['id'], now_iso(), now_iso())).lastrowid
        audit(self.db, self.actor['id'], 'paper.saved', 'Lưu nháp đề DT-' + str(ident))
        return self.paper_data(self.owned('assessment_papers', ident))

    def release(self, ident, body):
        paper = self.owned('assessment_papers', ident)
        if paper['status'] == 'released':
            return self.paper_data(paper)
        require(type(body.get('expected_revision')) is int and body['expected_revision'] == paper['revision'], 'Bản nháp đã thay đổi. Tải lại và kiểm tra trước khi chốt.', 409)
        require(body.get('content_checked') is True, 'Xác nhận đã đối chiếu nội dung, đáp án và lời giải.')
        items = self.clean_items(json.loads(paper['items']), strict=True)
        payload = json.dumps(items, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
        self.db.execute('INSERT INTO assessment_releases(paper_id,owner_id,title,description,subject,grade,items,content_hash,created_at) VALUES(?,?,?,?,?,?,?,?,?)', (ident, paper['owner_id'], paper['title'], paper['description'], paper['subject'], paper['grade'], payload, hashlib.sha256(payload.encode()).hexdigest(), now_iso()))
        self.db.execute('UPDATE assessment_papers SET status="released",revision=revision+1,updated_at=? WHERE id=?', (now_iso(), ident))
        audit(self.db, self.actor['id'], 'paper.released', 'Chốt đề DT-' + str(ident) + ' sau xác nhận của giáo viên')
        return self.paper_data(self.owned('assessment_papers', ident))

    def clone(self, ident):
        paper = self.owned('assessment_papers', ident)
        return self.save_paper({**dict(paper), 'title': (paper['title'][:145] + ' · Bản sao'), 'items': json.loads(paper['items'])})

    def validate_sources(self, release, targets=()):
        for item in json.loads(release['items']):
            source = item.get('source_question_id')
            if source:
                row = self.db.execute('SELECT * FROM questions WHERE id=?', (source,)).fetchone()
                require(row, 'Câu hỏi nguồn không còn khả dụng.', 409)
                ensure_question_usable(self.db, self.actor, row)
                # Prevent a changed bank entry from silently diverging from its release.
                require(row['prompt'] == item['prompt'] and json.loads(row['options']) == item['options'] and row['correct'] == item['correct'] and json.loads(row['provenance']) == item['provenance'], 'Câu hỏi nguồn đã thay đổi. Tạo bản đề mới trước khi giao hoặc bắt đầu lượt mới.', 409)
                require(all(question_scope_allowed(target, row) for target in targets), 'Nguồn câu hỏi không được phép chia sẻ với một số học sinh đã chọn.', 403)

    def create_room(self, body):
        self.staff()
        key = string(body, 'request_key', 16, 80)
        fingerprint = hashlib.sha256(json.dumps({k: v for k, v in body.items() if k != 'request_key'}, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()
        previous = self.db.execute('SELECT id,request_hash FROM exams WHERE owner_id=? AND request_key=?', (self.actor['id'], key)).fetchone()
        if previous:
            require(previous['request_hash'] == fingerprint, 'Mã giao phòng đã dùng cho nội dung khác. Mở lại biểu mẫu để tạo yêu cầu mới.', 409)
            return {'id': previous['id']}
        release = self.owned('assessment_releases', integer(body, 'release_id', 1, 2**31))
        starts, ends = timestamp(body.get('starts_at')), timestamp(body.get('ends_at'))
        require(ends > max(time.time(), starts) and ends - starts <= 366 * 86400, 'Giờ đóng phòng phải sau giờ mở và nằm trong một năm.')
        policy = body.get('result_policy', 'after_close')
        require(policy in ('immediate', 'after_close'), 'Chính sách công bố đáp án chưa hợp lệ.')
        ids = body.get('user_ids', [])
        require(isinstance(ids, list) and 1 <= len(ids) <= 2000 and all(type(i) is int for i in ids) and len(ids) == len(set(ids)), 'Chọn học sinh, không chọn trùng.')
        targets = self.db.execute('SELECT * FROM users WHERE id IN (' + ','.join('?' for _ in ids) + ') AND status="active" AND role="learner"', ids).fetchall()
        require(len(targets) == len(ids), 'Chỉ giao cho tài khoản học sinh đang hoạt động.')
        self.validate_sources(release, targets)
        due = datetime.fromtimestamp(ends, timezone.utc).isoformat(timespec='seconds')
        cur = self.db.execute('INSERT INTO exams(title,description,question_ids,duration,pass_score,max_attempts,due,status,created_at,release_id,owner_id,starts_at,result_policy) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)', (string(body, 'title', 5, 160), release['description'], json.dumps([i['source_question_id'] for i in json.loads(release['items']) if i.get('source_question_id')]), integer(body, 'duration', 1, 180), integer(body, 'pass_score', 1, 100), integer(body, 'max_attempts', 1, 3), due, 'published', now_iso(), release['id'], self.actor['id'], starts, policy))
        self.db.execute('UPDATE exams SET request_key=?,request_hash=? WHERE id=?', (key, fingerprint, cur.lastrowid))
        for uid in ids:
            self.db.execute('INSERT INTO exam_assignments VALUES(?,?)', (cur.lastrowid, uid))
        audit(self.db, self.actor['id'], 'room.created', 'Giao phòng PT-' + str(cur.lastrowid) + ' cho ' + str(len(ids)) + ' học sinh')
        return {'id': cur.lastrowid}

    def room_data(self, row):
        data = dict(row)
        release = self.db.execute('SELECT title,subject,grade,items,content_hash,paper_id FROM assessment_releases WHERE id=?', (row['release_id'],)).fetchone()
        data.update(paper_title=release['title'], subject=release['subject'], grade=release['grade'], paper_id=release['paper_id'], question_count=len(json.loads(release['items'])), content_hash=release['content_hash'])
        data['assigned'] = self.db.execute('SELECT COUNT(*) FROM exam_assignments WHERE exam_id=?', (row['id'],)).fetchone()[0]
        data['finished'] = self.db.execute('SELECT COUNT(DISTINCT user_id) FROM attempts WHERE exam_id=? AND submitted_at IS NOT NULL', (row['id'],)).fetchone()[0]
        return data

    def rooms(self):
        self.staff()
        settle_expired(self.db)
        rows = self.db.execute('SELECT * FROM exams WHERE release_id IS NOT NULL ' + ('' if self.actor['role'] == 'admin' else 'AND owner_id=? ') + 'ORDER BY id DESC', () if self.actor['role'] == 'admin' else (self.actor['id'],))
        return [self.room_data(row) for row in rows]

    def room_status(self, ident, body):
        row = self.owned('exams', ident)
        require(row['release_id'], 'Đây không phải phòng thi từ đề đã chốt.')
        status = body.get('status')
        require(status in ('published', 'closed'), 'Trạng thái phòng chưa hợp lệ.')
        if status == 'published':
            require(timestamp(row['due']) > time.time(), 'Phòng thi đã hết hạn.')
            self.validate_sources(self.db.execute('SELECT * FROM assessment_releases WHERE id=?', (row['release_id'],)).fetchone())
        self.db.execute('UPDATE exams SET status=? WHERE id=?', (status, ident))
        audit(self.db, self.actor['id'], 'room.status_changed', 'Phòng PT-' + str(ident) + ' · ' + status)
        return {'ok': True}

    def start(self, ident):
        row = self.db.execute('SELECT e.* FROM exams e JOIN exam_assignments a ON a.exam_id=e.id WHERE e.id=? AND a.user_id=? AND e.release_id IS NOT NULL', (ident, self.actor['id'])).fetchone()
        require(row, 'Bạn chưa được giao phòng thi này.', 403)
        active = self.db.execute('SELECT * FROM attempts WHERE exam_id=? AND user_id=? AND submitted_at IS NULL ORDER BY id DESC LIMIT 1', (ident, self.actor['id'])).fetchone()
        settle_expired(self.db)
        if active:
            return attempt_data(self.db, active)
        require(row['status'] == 'published' and row['starts_at'] <= time.time() < timestamp(row['due']), 'Phòng thi chưa mở, đã đóng hoặc đã hết hạn.', 403)
        count = self.db.execute('SELECT COUNT(*) FROM attempts WHERE exam_id=? AND user_id=?', (ident, self.actor['id'])).fetchone()[0]
        require(count < row['max_attempts'], 'Bạn đã hết lượt làm bài.')
        require(not self.db.execute('SELECT 1 FROM attempts WHERE exam_id=? AND user_id=? AND passed=1', (ident, self.actor['id'])).fetchone(), 'Bạn đã đạt yêu cầu của phòng thi này.')
        release = self.db.execute('SELECT * FROM assessment_releases WHERE id=?', (row['release_id'],)).fetchone()
        self.validate_sources(release, [self.actor])
        started = time.time()
        cur = self.db.execute('INSERT INTO attempts(exam_id,user_id,started,deadline,questions,pass_score_snapshot,title_snapshot) VALUES(?,?,?,?,?,?,?)', (ident, self.actor['id'], started, min(started + row['duration'] * 60, timestamp(row['due'])), release['items'], row['pass_score'], row['title']))
        audit(self.db, self.actor['id'], 'exam.started', 'Vào phòng PT-' + str(ident))
        return attempt_data(self.db, {'id': cur.lastrowid})

    def results(self, ident):
        row = self.owned('exams', ident)
        require(row['release_id'], 'Phòng thi chưa có phiên bản đề.')
        settle_expired(self.db)
        room = self.room_data(row)
        release = self.db.execute('SELECT * FROM assessment_releases WHERE id=?', (row['release_id'],)).fetchone()
        items = json.loads(release['items'])
        roster, latest = [], []
        for person in self.db.execute('SELECT u.id,u.name,u.email,d.name classroom FROM exam_assignments a JOIN users u ON u.id=a.user_id LEFT JOIN departments d ON d.id=u.department_id WHERE a.exam_id=? ORDER BY u.name', (ident,)).fetchall():
            attempts = self.db.execute('SELECT * FROM attempts WHERE exam_id=? AND user_id=? ORDER BY id DESC', (ident, person['id'])).fetchall()
            submitted = next((a for a in attempts if a['submitted_at']), None)
            active = next((a for a in attempts if not a['submitted_at']), None)
            weak = {}
            if submitted:
                latest.append(submitted)
                answers = json.loads(submitted['answers'])
                for q in json.loads(submitted['questions']):
                    if answers.get(str(q['id'])) != q['correct']:
                        topic = q.get('objective') or q['category'] or release['subject']
                        weak[topic] = weak.get(topic, 0) + 1
            roster.append({**dict(person), 'state': 'in_progress' if active else 'submitted' if submitted else 'not_started', 'score': submitted['score'] if submitted else None, 'passed': submitted['passed'] if submitted else None, 'submitted_at': submitted['submitted_at'] if submitted else None, 'submission_reason': submitted['submission_reason'] if submitted else None, 'attempt_count': len(attempts), 'weak_topics': weak, 'attempts': [{key: a[key] for key in ('id', 'score', 'passed', 'started', 'deadline', 'submitted_at', 'submission_reason')} for a in attempts]})
        analysis = []
        for q in items:
            choices = [0, 0, 0, 0]
            unanswered = 0
            for a in latest:
                answer = json.loads(a['answers']).get(str(q['id']))
                if type(answer) is int and 0 <= answer < 4:
                    choices[answer] += 1
                else:
                    unanswered += 1
            right = choices[q['correct']]
            analysis.append({'id': q['id'], 'prompt': q['prompt'], 'objective': q.get('objective') or q['category'] or release['subject'], 'options': q['options'], 'correct': q['correct'], 'choices': choices, 'unanswered': unanswered, 'sample_size': len(latest), 'correct_count': right, 'wrong_rate': round(100 * (len(latest) - right) / len(latest)) if latest else None})
        return {'room': room, 'roster': roster, 'analysis': analysis, 'summary': {'assigned': len(roster), 'submitted': len(latest), 'passed': sum(bool(a['passed']) for a in latest), 'average': round(sum(a['score'] for a in latest) / len(latest), 1) if latest else None}, 'basis': 'Mỗi học sinh tính lượt nộp gần nhất; câu bỏ trống tính chưa đúng. Đây là tín hiệu để giáo viên xem xét, không phải kết luận năng lực.'}

    def export(self, ident):
        result = self.results(ident)
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['Học sinh', 'Email', 'Lớp / nhóm', 'Trạng thái', 'Điểm /100', 'Đạt', 'Lượt đã làm', 'Nộp lúc', 'Chủ đề cần ôn tập'])
        for p in result['roster']:
            values = [p['name'], p['email'], p['classroom'], p['state'], p['score'] if p['score'] is not None else '', '' if p['passed'] is None else p['passed'], p['attempt_count'], p['submitted_at'] or '', '; '.join(p['weak_topics'])]
            writer.writerow(["'" + v if isinstance(v, str) and v.startswith(('=', '+', '-', '@', '\t', '\r', '\n')) else v for v in values])
        audit(self.db, self.actor['id'], 'room.exported', 'Xuất kết quả PT-' + str(ident))
        return ('\ufeff' + output.getvalue()).encode(), 'text/csv; charset=utf-8'


def dispatch_assessment(db, actor, method, route, body):
    service = Assessment(db, actor)
    parts = route.split('/')[1:]
    if parts == ['papers']:
        return service.papers() if method == 'GET' else service.save_paper(body)
    if len(parts) >= 2 and parts[0] == 'papers' and parts[1].isdigit():
        ident = int(parts[1])
        if len(parts) == 2:
            return service.paper_data(service.owned('assessment_papers', ident)) if method == 'GET' else service.save_paper(body, ident)
        if len(parts) == 3 and method == 'POST':
            if parts[2] == 'release': return service.release(ident, body)
            if parts[2] == 'clone': return service.clone(ident)
    if parts == ['rooms']:
        return service.rooms() if method == 'GET' else service.create_room(body)
    if len(parts) >= 2 and parts[0] == 'rooms' and parts[1].isdigit():
        ident = int(parts[1])
        if len(parts) == 2 and method == 'GET': return service.results(ident)
        if len(parts) == 3:
            if parts[2] == 'status' and method == 'POST': return service.room_status(ident, body)
            if parts[2] == 'export' and method == 'GET': return service.export(ident)
    raise APIError(404, 'Không tìm thấy chức năng đề thi / phòng thi.')
