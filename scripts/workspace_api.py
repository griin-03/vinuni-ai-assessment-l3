"""Same-origin workspace API. All permissions and data scopes are checked here."""
import csv
import hashlib
import io
import json
import os
import re
import secrets
import sqlite3
import time
from datetime import datetime, timezone
from http.cookies import SimpleCookie
from urllib.parse import urlsplit

from workspace_store import connection, audit, now_iso, password_hash, password_valid, PERMISSIONS, ROLES
from workspace_errors import APIError
from rag_domain import CATEGORIES
from rag_api import dispatch_rag
from rag_service import question_scope_allowed, ensure_question_usable
from assessment_service import dispatch_assessment, Assessment
from assessment_runtime import grade_attempt, attempt_data, settle_expired


def require(condition, message, status=400):
    if not condition:
        raise APIError(status, message)


def text(data, key, minimum=1, maximum=200):
    value = data.get(key, '')
    require(isinstance(value, str) and minimum <= len(value.strip()) <= maximum, 'Thông tin “' + key + '” chưa hợp lệ.')
    return value.strip()


def number(data, key, minimum, maximum):
    value = data.get(key)
    require(isinstance(value, int) and not isinstance(value, bool) and minimum <= value <= maximum, 'Giá trị “' + key + '” chưa hợp lệ.')
    return value


def due_date(value):
    require(isinstance(value, str), 'Chọn hạn hoàn thành.')
    try:
        result = datetime.fromisoformat(value.replace('Z', '+00:00'))
        if result.tzinfo is None:
            result = result.replace(tzinfo=timezone.utc)
        require(result.timestamp() > time.time(), 'Hạn hoàn thành phải ở tương lai.')
        return result.astimezone(timezone.utc).isoformat(timespec='seconds')
    except ValueError:
        raise APIError(400, 'Ngày chưa hợp lệ.')


def public_user(row):
    return {k: row[k] for k in ('id', 'name', 'email', 'role', 'department_id', 'department', 'title', 'status')}


def user_query():
    return 'SELECT u.*,d.name department FROM users u LEFT JOIN departments d ON d.id=u.department_id '


def scope_users(db, user):
    if user['role'] in ('admin', 'training'):
        return db.execute(user_query() + 'ORDER BY u.id').fetchall()
    if user['role'] == 'manager':
        return db.execute(user_query() + 'WHERE department_id=? ORDER BY u.id', (user['department_id'],)).fetchall()
    return [user]


def permission(user, key):
    require(key in PERMISSIONS[user['role']], 'Bạn không có quyền thực hiện thao tác này.', 403)


def summarize_people(db, user):
    people = []
    for row in scope_users(db, user):
        p = public_user(row)
        es = db.execute('SELECT e.completed,c.lessons,e.due FROM enrollments e JOIN courses c ON c.id=e.course_id WHERE e.user_id=? AND c.status="published"', (row['id'],)).fetchall()
        p['assigned'] = len(es)
        p['completed'] = sum(len(json.loads(e['completed'])) == len(json.loads(e['lessons'])) for e in es)
        p['overdue'] = sum(e['due'] < now_iso() and len(json.loads(e['completed'])) < len(json.loads(e['lessons'])) for e in es)
        p['progress'] = round(sum(len(json.loads(e['completed'])) / max(1, len(json.loads(e['lessons']))) for e in es) * 100 / len(es)) if es else 0
        grades = db.execute('SELECT score FROM attempts WHERE user_id=? AND submitted_at IS NOT NULL', (row['id'],)).fetchall()
        p['score'] = round(sum(g['score'] for g in grades) / len(grades)) if grades else None
        people.append(p)
    return people


def course_data(db, user, course):
    result = dict(course)
    result['lessons'] = json.loads(result['lessons'])
    own = db.execute('SELECT * FROM enrollments WHERE course_id=? AND user_id=?', (course['id'], user['id'])).fetchone()
    result['enrollment'] = {**dict(own), 'completed': json.loads(own['completed'])} if own else None
    if 'courses.manage' in PERMISSIONS[user['role']]:
        rows = db.execute('SELECT e.*,u.name FROM enrollments e JOIN users u ON u.id=e.user_id WHERE course_id=?', (course['id'],)).fetchall()
        result['assigned'] = len(rows)
        result['finished'] = sum(len(json.loads(r['completed'])) == len(result['lessons']) for r in rows)
        result['members'] = [r['user_id'] for r in rows]
    return result


def exam_data(db, user, exam):
    data = dict(exam)
    data['question_count'] = len(json.loads(data.pop('question_ids')))
    if exam['release_id']:
        release = db.execute('SELECT items,subject,grade FROM assessment_releases WHERE id=?', (exam['release_id'],)).fetchone()
        data.update(question_count=len(json.loads(release['items'])), subject=release['subject'], grade=release['grade'])
    assigned = db.execute('SELECT 1 FROM exam_assignments WHERE exam_id=? AND user_id=?', (exam['id'], user['id'])).fetchone()
    data['assigned_to_me'] = bool(assigned)
    data['attempts'] = [dict(r) for r in db.execute('SELECT id,score,passed,submitted_at,deadline FROM attempts WHERE exam_id=? AND user_id=? ORDER BY id DESC', (exam['id'], user['id'])).fetchall()]
    if 'exams.manage' in PERMISSIONS[user['role']]:
        data['question_ids'] = json.loads(exam['question_ids'])
        data['members'] = [r[0] for r in db.execute('SELECT user_id FROM exam_assignments WHERE exam_id=?', (exam['id'],))]
        data['assigned'] = len(data['members'])
        data['finished'] = db.execute('SELECT COUNT(DISTINCT user_id) FROM attempts WHERE exam_id=? AND submitted_at IS NOT NULL', (exam['id'],)).fetchone()[0]
    return data


def bootstrap(db, user, csrf):
    settle_expired(db)
    staff = user['role'] in ('training', 'admin')
    courses = db.execute('SELECT * FROM courses ORDER BY id DESC').fetchall() if staff else db.execute('SELECT c.* FROM courses c JOIN enrollments e ON e.course_id=c.id WHERE e.user_id=? AND c.status="published" ORDER BY c.id', (user['id'],)).fetchall()
    exams = db.execute('SELECT * FROM exams WHERE release_id IS NULL OR owner_id=? OR ?="admin" ORDER BY due', (user['id'], user['role'])).fetchall() if staff else db.execute('SELECT x.* FROM exams x JOIN exam_assignments a ON a.exam_id=x.id WHERE a.user_id=? AND x.status!="draft" ORDER BY x.due', (user['id'],)).fetchall()
    people = summarize_people(db, user)
    scope = [p['id'] for p in people]
    query = 'SELECT a.*,u.name actor_name FROM audit a LEFT JOIN users u ON u.id=a.actor '
    if not staff:
        query += 'WHERE a.actor IN (' + ','.join('?' for _ in scope) + ') '
    activity = [dict(r) for r in db.execute(query + 'ORDER BY a.id DESC LIMIT 12', () if staff else scope)]
    settings = dict(db.execute('SELECT key,value FROM settings WHERE key IN ("company","company_email","timezone","demo","education_mvp")').fetchall())
    questions = [{**dict(r), 'options': json.loads(r['options']), 'provenance': json.loads(r['provenance'])} for r in db.execute('SELECT * FROM questions ORDER BY id DESC') if question_scope_allowed(user, r)] if staff else []
    if settings.get('education_mvp'):
        questions = [q for q in questions if q['category'] in CATEGORIES[:11]]
    return {'user': public_user(user), 'csrf': csrf, 'permissions': PERMISSIONS[user['role']], 'roles': ROLES, 'settings': settings, 'departments': [dict(r) for r in db.execute('SELECT * FROM departments')], 'people': people, 'courses': [course_data(db, user, c) for c in courses], 'exams': [exam_data(db, user, x) for x in exams], 'questions': questions, 'activity': activity, 'server_time': time.time()}


def assigned_people(db, data):
    ids = data.get('user_ids', [])
    require(isinstance(ids, list) and 0 < len(ids) <= 2000 and all(isinstance(i, int) and not isinstance(i, bool) for i in ids), 'Chọn ít nhất một nhân viên.')
    ids = list(set(ids))
    count = db.execute('SELECT COUNT(*) FROM users WHERE status="active" AND id IN (' + ','.join('?' for _ in ids) + ')', ids).fetchone()[0]
    require(count == len(ids), 'Danh sách có tài khoản không còn hoạt động.')
    return ids


def handle_api(handler, method, path):
    if not path.startswith('/api/workspace/'):
        return False
    cookie_header = None
    try:
        body = {}
        if method != 'GET':
            origin = handler.headers.get('Origin', '')
            require(urlsplit(origin).netloc == handler.headers.get('Host') and urlsplit(origin).scheme in ('http', 'https'), 'Yêu cầu phải xuất phát từ cùng trang VinAssess.', 403)
            require(handler.headers.get('Sec-Fetch-Site') != 'cross-site', 'Yêu cầu không hợp lệ.', 403)
            size = int(handler.headers.get('Content-Length', '0'))
            require(0 <= size <= 200000, 'Nội dung yêu cầu quá lớn.', 413)
            if size:
                require(handler.headers.get('Content-Type', '').startswith('application/json'), 'Chỉ nhận nội dung JSON.', 415)
                body = json.loads(handler.rfile.read(size))
                require(isinstance(body, dict), 'Nội dung yêu cầu chưa hợp lệ.')
        with connection() as db:
            if path == '/api/workspace/public' and method == 'GET':
                result = dict(db.execute('SELECT key,value FROM settings WHERE key IN ("demo","company")'))
                result['roles'] = ROLES
            elif path == '/api/workspace/login' and method == 'POST':
                email = text(body, 'email', 3, 200).lower()
                password = text(body, 'password', 1, 200)
                key = handler.client_address[0] + ':' + email
                failure = db.execute('SELECT * FROM login_failures WHERE key=?', (key,)).fetchone()
                require(not failure or failure['until'] <= time.time() or failure['count'] < 8, 'Bạn đã thử nhiều lần. Vui lòng đợi 5 phút rồi thử lại.', 429)
                user = db.execute(user_query() + 'WHERE u.email=?', (email,)).fetchone()
                if not user or not password_valid(password, user['password']) or user['status'] != 'active':
                    count = failure['count'] + 1 if failure and failure['until'] > time.time() else 1
                    db.execute('INSERT OR REPLACE INTO login_failures VALUES(?,?,?)', (key, count, time.time() + 300))
                    db.commit()
                    raise APIError(401, 'Email hoặc mật khẩu chưa đúng, hoặc tài khoản đã bị khóa.')
                db.execute('DELETE FROM login_failures WHERE key=?', (key,))
                db.execute('DELETE FROM sessions WHERE expires<?', (time.time(),))
                token, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
                db.execute('INSERT INTO sessions VALUES(?,?,?,?)', (hashlib.sha256(token.encode()).hexdigest(), user['id'], csrf, time.time() + 28800))
                secure = '; Secure' if os.environ.get('VINASSESS_COOKIE_SECURE') == '1' else ''
                cookie_header = 'vinassess_session=' + token + '; Path=/; HttpOnly; SameSite=Lax; Max-Age=28800' + secure
                audit(db, user['id'], 'session.login', 'Đăng nhập vào không gian làm việc')
                result = {'ok': True, 'user': public_user(user), 'csrf': csrf}
            else:
                if method != 'GET':
                    db.execute('BEGIN IMMEDIATE')
                cookie = SimpleCookie()
                try: cookie.load(handler.headers.get('Cookie', ''))
                except Exception: pass
                token = cookie.get('vinassess_session')
                session = db.execute('SELECT * FROM sessions WHERE token=? AND expires>?', (hashlib.sha256((token.value if token else '').encode()).hexdigest(), time.time())).fetchone()
                require(session, 'Phiên làm việc đã kết thúc. Vui lòng đăng nhập lại.', 401)
                user = db.execute(user_query() + 'WHERE u.id=? AND u.status="active"', (session['user_id'],)).fetchone()
                require(user, 'Tài khoản không còn hoạt động.', 401)
                if method != 'GET':
                    require(secrets.compare_digest(handler.headers.get('X-CSRF-Token', ''), session['csrf']), 'Phiên làm việc chưa hợp lệ. Vui lòng tải lại trang.', 403)
                if path == '/api/workspace/bootstrap' and method == 'GET':
                    result = bootstrap(db, user, session['csrf'])
                elif path == '/api/workspace/logout' and method == 'POST':
                    db.execute('DELETE FROM sessions WHERE token=?', (session['token'],))
                    cookie_header = 'vinassess_session=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0'
                    result = {'ok': True}
                else:
                    result = dispatch(db, user, method, path, body)
            if isinstance(result, tuple):
                payload, content_type = result
            else:
                payload, content_type = json.dumps(result, ensure_ascii=False).encode(), 'application/json; charset=utf-8'
        handler.send_response(200)
        handler.send_header('Content-Type', content_type)
        handler.send_header('Cache-Control', 'no-store')
        handler.send_header('X-Content-Type-Options', 'nosniff')
        if cookie_header: handler.send_header('Set-Cookie', cookie_header)
        if content_type.startswith('text/csv'): handler.send_header('Content-Disposition', 'attachment; filename="vinassess-report.csv"')
        handler.send_header('Content-Length', str(len(payload)))
        handler.end_headers()
        handler.wfile.write(payload)
    except (APIError, ValueError, json.JSONDecodeError, sqlite3.IntegrityError) as error:
        status = error.status if isinstance(error, APIError) else 400
        message = error.message if isinstance(error, APIError) else 'Dữ liệu chưa hợp lệ hoặc đã tồn tại. Vui lòng kiểm tra lại.'
        payload = json.dumps({'error': message}, ensure_ascii=False).encode()
        handler.send_response(status)
        handler.send_header('Content-Type', 'application/json; charset=utf-8')
        handler.send_header('Cache-Control', 'no-store')
        handler.send_header('Content-Length', str(len(payload)))
        handler.end_headers()
        handler.wfile.write(payload)
    return True


def dispatch(db, user, method, path, body):
    route = path.removeprefix('/api/workspace/')
    parts = route.split('/')
    if parts[0] == 'assessment':
        return dispatch_assessment(db, user, method, route, body)
    if parts[0] in ('knowledge', 'ai'):
        return dispatch_rag(db, user, method, route, body)
    if route == 'report.csv' and method == 'GET':
        require(user['role'] != 'learner', 'Bạn không có quyền xuất báo cáo.', 403)
        out = io.StringIO()
        writer = csv.writer(out)
        writer.writerow(['Họ tên', 'Email', 'Phòng ban', 'Chương trình được giao', 'Đã hoàn thành', 'Tiến độ (%)', 'Quá hạn', 'Điểm trung bình'])
        for p in summarize_people(db, user):
            values = [p['name'], p['email'], p['department'], p['assigned'], p['completed'], p['progress'], p['overdue'], p['score'] if p['score'] is not None else '']
            writer.writerow([("'" + v if isinstance(v, str) and v.startswith(('=', '+', '-', '@', '\t', '\r', '\n')) else v) for v in values])
        audit(db, user['id'], 'report.exported', 'Xuất báo cáo tiến độ trong phạm vi được phân quyền')
        return ('\ufeff' + out.getvalue()).encode('utf-8'), 'text/csv; charset=utf-8'
    if route == 'audit' and method == 'GET':
        permission(user, 'audit.read')
        return [dict(r) for r in db.execute('SELECT a.*,u.name actor_name FROM audit a LEFT JOIN users u ON u.id=a.actor ORDER BY id DESC LIMIT 200')]
    if route == 'profile/password' and method == 'POST':
        require(password_valid(text(body, 'current_password'), user['password']), 'Mật khẩu hiện tại chưa đúng.')
        password = text(body, 'new_password', 12, 200)
        require(any(c.isupper() for c in password) and any(c.islower() for c in password) and any(c.isdigit() for c in password), 'Mật khẩu cần ít nhất 12 ký tự, gồm chữ hoa, chữ thường và số.')
        db.execute('UPDATE users SET password=? WHERE id=?', (password_hash(password), user['id']))
        db.execute('DELETE FROM sessions WHERE user_id=?', (user['id'],))
        audit(db, user['id'], 'account.password_changed', 'Đổi mật khẩu và kết thúc các phiên đăng nhập')
        return {'ok': True}
    if route == 'settings' and method == 'POST':
        permission(user, 'settings.manage')
        for key, value in [('company', text(body, 'company', 2, 80)), ('company_email', text(body, 'company_email', 3, 200))]:
            if key == 'company_email': require(re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', value), 'Email liên hệ chưa hợp lệ.')
            db.execute('UPDATE settings SET value=? WHERE key=?', (value, key))
        audit(db, user['id'], 'settings.updated', 'Cập nhật thông tin doanh nghiệp')
        return {'ok': True}
    if parts[0] == 'users' and method == 'POST':
        permission(user, 'users.manage')
        if len(parts) == 1:
            name, email = text(body, 'name', 2, 100), text(body, 'email', 3, 200).lower()
            require(re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email), 'Email chưa hợp lệ.')
            role = body.get('role')
            require(role in ROLES, 'Vai trò chưa hợp lệ.')
            dept = number(body, 'department_id', 1, 100000)
            require(db.execute('SELECT 1 FROM departments WHERE id=?', (dept,)).fetchone(), 'Phòng ban không tồn tại.')
            password = text(body, 'password', 12, 200)
            require(any(c.isupper() for c in password) and any(c.islower() for c in password) and any(c.isdigit() for c in password), 'Mật khẩu cần chữ hoa, chữ thường và số.')
            cur = db.execute('INSERT INTO users(name,email,password,role,department_id,title,created_at) VALUES(?,?,?,?,?,?,?)', (name, email, password_hash(password), role, dept, text(body, 'title', 0, 100), now_iso()))
            audit(db, user['id'], 'user.created', 'Tạo tài khoản cho ' + name)
            return {'id': cur.lastrowid}
        if len(parts) == 2 and parts[1].isdigit():
            uid = int(parts[1]); target = db.execute('SELECT * FROM users WHERE id=?', (uid,)).fetchone()
            require(target, 'Tài khoản không tồn tại.', 404)
            role, status = body.get('role'), body.get('status')
            require(role in ROLES and status in ('active', 'inactive'), 'Vai trò hoặc trạng thái chưa hợp lệ.')
            require(uid != user['id'] or (role == user['role'] and status == 'active'), 'Bạn không thể tự hạ quyền hoặc khóa tài khoản đang sử dụng.')
            if target['role'] == 'admin' and (role != 'admin' or status != 'active'):
                require(db.execute('SELECT COUNT(*) FROM users WHERE role="admin" AND status="active"').fetchone()[0] > 1, 'Cần giữ ít nhất một quản trị hệ thống hoạt động.')
            db.execute('UPDATE users SET role=?,status=? WHERE id=?', (role, status, uid))
            db.execute('DELETE FROM sessions WHERE user_id=?', (uid,))
            audit(db, user['id'], 'user.updated', 'Cập nhật vai trò/trạng thái của ' + target['name'])
            return {'ok': True}
    if parts[0] == 'courses':
        if len(parts) == 3 and parts[1].isdigit() and parts[2] == 'progress' and method == 'POST':
            cid = int(parts[1])
            row = db.execute('SELECT e.*,c.lessons FROM enrollments e JOIN courses c ON c.id=e.course_id WHERE e.course_id=? AND e.user_id=? AND c.status="published"', (cid, user['id'])).fetchone()
            require(row, 'Bạn chưa được giao chương trình này.', 403)
            lesson_id = number(body, 'lesson_id', 1, 1000)
            lessons = json.loads(row['lessons']); done = set(json.loads(row['completed']))
            require(lesson_id in [l['id'] for l in lessons], 'Bài học không tồn tại.', 404)
            index = next(i for i, l in enumerate(lessons) if l['id'] == lesson_id)
            require(all(l['id'] in done for l in lessons[:index]), 'Hoàn thành bài học trước để tiếp tục.')
            done.add(lesson_id)
            finished = len(done) == len(lessons)
            db.execute('UPDATE enrollments SET completed=?,completed_at=? WHERE course_id=? AND user_id=?', (json.dumps(sorted(done)), now_iso() if finished else None, cid, user['id']))
            if finished and not row['completed_at']: audit(db, user['id'], 'course.completed', 'Hoàn thành một chương trình học')
            return {'ok': True, 'completed': sorted(done)}
        if method == 'POST':
            permission(user, 'courses.manage')
            if len(parts) == 3 and parts[1].isdigit() and parts[2] == 'assign':
                cid = int(parts[1]); course = db.execute('SELECT * FROM courses WHERE id=?', (cid,)).fetchone()
                require(course and course['status'] == 'published', 'Chỉ giao các chương trình đã xuất bản.')
                ids, due = assigned_people(db, body), due_date(body.get('due'))
                for uid in ids:
                    db.execute('INSERT INTO enrollments(course_id,user_id,due) VALUES(?,?,?) ON CONFLICT(course_id,user_id) DO UPDATE SET due=excluded.due', (cid, uid, due))
                audit(db, user['id'], 'course.assigned', 'Giao “' + course['title'] + '” cho ' + str(len(ids)) + ' nhân viên')
                return {'ok': True}
            if len(parts) == 3 and parts[1].isdigit() and parts[2] == 'publish':
                cid = int(parts[1]); course = db.execute('SELECT * FROM courses WHERE id=?', (cid,)).fetchone()
                require(course, 'Không tìm thấy chương trình.', 404)
                require(json.loads(course['lessons']), 'Chương trình cần có ít nhất một bài học.')
                db.execute('UPDATE courses SET status="published" WHERE id=?', (cid,))
                audit(db, user['id'], 'course.published', 'Xuất bản “' + course['title'] + '”')
                return {'ok': True}
            if len(parts) == 1 or len(parts) == 2 and parts[1].isdigit():
                existing = db.execute('SELECT * FROM courses WHERE id=?', (int(parts[1]),)).fetchone() if len(parts) == 2 else None
                if len(parts) == 2:
                    require(existing, 'Không tìm thấy chương trình.', 404)
                    require(existing['status'] == 'draft', 'Chỉ chỉnh sửa nội dung chương trình ở trạng thái bản nháp.')
                lessons = body.get('lessons', [])
                require(isinstance(lessons, list) and 1 <= len(lessons) <= 30, 'Thêm ít nhất một bài học, tối đa 30 bài.')
                clean = []
                for i, lesson in enumerate(lessons):
                    require(isinstance(lesson, dict), 'Bài học chưa hợp lệ.')
                    clean.append({'id': i + 1, 'title': text(lesson, 'title', 3, 160), 'body': text(lesson, 'body', 30, 10000), 'points': [], 'minutes': number(lesson, 'minutes', 1, 240)})
                category = text(body, 'category')
                require(category in CATEGORIES, 'Nhóm chương trình chưa hợp lệ.')
                title = text(body, 'title', 3, 160)
                description = text(body, 'description', 10, 1500)
                if existing:
                    db.execute('UPDATE courses SET title=?,category=?,description=?,duration=?,lessons=? WHERE id=?', (title, category, description, sum(l['minutes'] for l in clean), json.dumps(clean, ensure_ascii=False), existing['id']))
                    audit(db, user['id'], 'course.updated', 'Cập nhật bản nháp “' + title + '”')
                    return {'id': existing['id']}
                cur = db.execute('INSERT INTO courses(title,category,description,duration,lessons,owner_id,created_at) VALUES(?,?,?,?,?,?,?)', (title, category, description, sum(l['minutes'] for l in clean), json.dumps(clean, ensure_ascii=False), user['id'], now_iso()))
                audit(db, user['id'], 'course.created', 'Tạo bản nháp “' + title + '”')
                return {'id': cur.lastrowid}
    if parts[0] == 'questions' and method == 'POST' and len(parts) == 1:
        permission(user, 'questions.manage')
        options = body.get('options', [])
        require(isinstance(options, list) and len(options) == 4 and all(isinstance(o, str) and 1 <= len(o.strip()) <= 500 for o in options), 'Nhập đủ bốn phương án trả lời.')
        require(len(set(o.strip().casefold() for o in options)) == 4, 'Các phương án trả lời phải khác nhau.')
        category = text(body, 'category')
        require(category in CATEGORIES, 'Nhóm câu hỏi chưa hợp lệ.')
        cur = db.execute('INSERT INTO questions(prompt,options,correct,explanation,category,created_at) VALUES(?,?,?,?,?,?)', (text(body, 'prompt', 10, 2000), json.dumps(options, ensure_ascii=False), number(body, 'correct', 0, 3), text(body, 'explanation', 5, 2000), category, now_iso()))
        audit(db, user['id'], 'question.created', 'Thêm câu hỏi vào ngân hàng ' + category)
        return {'id': cur.lastrowid}
    if parts[0] == 'exams' and method == 'POST':
        if len(parts) == 3 and parts[1].isdigit():
            room = db.execute('SELECT release_id FROM exams WHERE id=?', (int(parts[1]),)).fetchone()
            if room and room['release_id']:
                service = Assessment(db, user)
                if parts[2] == 'start': return service.start(int(parts[1]))
                if parts[2] == 'status': return service.room_status(int(parts[1]), body)
                raise APIError(409, 'Danh sách phòng đã chốt khi giao đề. Tạo phòng mới để giao cho nhóm khác.')
        if len(parts) == 3 and parts[1].isdigit() and parts[2] == 'start':
            # Serialize starts so concurrent tabs reuse the same active attempt.
            if not db.in_transaction: db.execute('BEGIN IMMEDIATE')
            xid = int(parts[1]); exam = db.execute('SELECT x.* FROM exams x JOIN exam_assignments a ON a.exam_id=x.id WHERE x.id=? AND a.user_id=? AND x.status="published"', (xid, user['id'])).fetchone()
            require(exam, 'Bạn chưa được giao đợt khảo thí này hoặc đợt đã đóng.', 403)
            active = db.execute('SELECT * FROM attempts WHERE exam_id=? AND user_id=? AND submitted_at IS NULL ORDER BY id DESC LIMIT 1', (xid, user['id'])).fetchone()
            if active:
                if active['deadline'] <= time.time(): grade_attempt(db, active, reason='timeout')
                return attempt_data(db, active)
            for qid in json.loads(exam['question_ids']):
                question = db.execute('SELECT * FROM questions WHERE id=?', (qid,)).fetchone()
                ensure_question_usable(db, user, question)
            require(exam['due'] > now_iso(), 'Đợt khảo thí đã hết hạn.')
            count = db.execute('SELECT COUNT(*) FROM attempts WHERE exam_id=? AND user_id=?', (xid, user['id'])).fetchone()[0]
            require(count < exam['max_attempts'], 'Bạn đã sử dụng hết lượt làm bài.')
            require(not db.execute('SELECT 1 FROM attempts WHERE exam_id=? AND user_id=? AND passed=1', (xid, user['id'])).fetchone(), 'Bạn đã đạt yêu cầu của đợt khảo thí này.')
            questions = [dict(db.execute('SELECT * FROM questions WHERE id=?', (i,)).fetchone()) for i in json.loads(exam['question_ids'])]
            deadline = min(time.time() + exam['duration'] * 60, datetime.fromisoformat(exam['due']).timestamp())
            cur = db.execute('INSERT INTO attempts(exam_id,user_id,started,deadline,questions,pass_score_snapshot,title_snapshot) VALUES(?,?,?,?,?,?,?)', (xid, user['id'], time.time(), deadline, json.dumps(questions, ensure_ascii=False), exam['pass_score'], exam['title']))
            audit(db, user['id'], 'exam.started', 'Bắt đầu “' + exam['title'] + '”')
            return attempt_data(db, {'id': cur.lastrowid})
        permission(user, 'exams.manage')
        if len(parts) == 3 and parts[1].isdigit() and parts[2] == 'status':
            status = body.get('status'); require(status in ('published', 'closed'), 'Trạng thái chưa hợp lệ.')
            exam = db.execute('SELECT * FROM exams WHERE id=?', (int(parts[1]),)).fetchone()
            require(exam, 'Không tìm thấy đợt khảo thí.', 404)
            for qid in json.loads(exam['question_ids']):
                question = db.execute('SELECT * FROM questions WHERE id=?', (qid,)).fetchone()
                if status == 'published': ensure_question_usable(db, user, question)
                else: require(question_scope_allowed(user, question), 'Đợt khảo thí nằm ngoài phạm vi nội dung của bạn.', 403)
            require(status == 'closed' or exam['due'] > now_iso(), 'Không thể mở đợt đã hết hạn.')
            db.execute('UPDATE exams SET status=? WHERE id=?', (status, exam['id']))
            audit(db, user['id'], 'exam.status_changed', ('Mở' if status == 'published' else 'Đóng') + ' đợt “' + exam['title'] + '”')
            return {'ok': True}
        if len(parts) == 3 and parts[1].isdigit() and parts[2] == 'assign':
            exam = db.execute('SELECT * FROM exams WHERE id=?', (int(parts[1]),)).fetchone()
            require(exam and exam['status'] == 'published' and exam['due'] > now_iso(), 'Chỉ giao đợt khảo thí đang mở và còn hạn.')
            ids = assigned_people(db, body)
            targets = db.execute('SELECT * FROM users WHERE id IN (' + ','.join('?' for _ in ids) + ')', ids).fetchall()
            for qid in json.loads(exam['question_ids']):
                question = db.execute('SELECT * FROM questions WHERE id=?', (qid,)).fetchone()
                ensure_question_usable(db, user, question)
                require(all(question_scope_allowed(target, question) for target in targets), 'Phạm vi người nhận không phù hợp với nguồn giới hạn phòng ban của câu hỏi.', 403)
            for uid in ids: db.execute('INSERT OR IGNORE INTO exam_assignments VALUES(?,?)', (exam['id'], uid))
            audit(db, user['id'], 'exam.assigned', 'Giao “' + exam['title'] + '” cho ' + str(len(ids)) + ' nhân viên')
            return {'ok': True}
        if len(parts) == 1:
            ids = body.get('question_ids', [])
            require(isinstance(ids, list) and 1 <= len(ids) <= 100 and all(isinstance(i, int) for i in ids) and len(ids) == len(set(ids)), 'Chọn từ 1 đến 100 câu hỏi khác nhau.')
            require(db.execute('SELECT COUNT(*) FROM questions WHERE id IN (' + ','.join('?' for _ in ids) + ')', ids).fetchone()[0] == len(ids), 'Có câu hỏi không còn tồn tại.')
            for qid in ids:
                ensure_question_usable(db, user, db.execute('SELECT * FROM questions WHERE id=?', (qid,)).fetchone())
            title = text(body, 'title', 3, 160)
            cur = db.execute('INSERT INTO exams(title,description,question_ids,duration,pass_score,max_attempts,due,status,created_at) VALUES(?,?,?,?,?,?,?,?,?)', (title, text(body, 'description', 10, 1500), json.dumps(ids), number(body, 'duration', 1, 180), number(body, 'pass_score', 1, 100), number(body, 'max_attempts', 1, 5), due_date(body.get('due')), 'draft', now_iso()))
            audit(db, user['id'], 'exam.created', 'Tạo bản nháp “' + title + '”')
            return {'id': cur.lastrowid}
    if parts[0] == 'attempts' and len(parts) in (2, 3) and parts[1].isdigit():
        if not db.in_transaction: db.execute('BEGIN IMMEDIATE')
        attempt = db.execute('SELECT * FROM attempts WHERE id=? AND user_id=?', (int(parts[1]), user['id'])).fetchone()
        require(attempt, 'Không tìm thấy lượt làm bài của bạn.', 404)
        if not attempt['submitted_at'] and attempt['deadline'] <= time.time(): grade_attempt(db, attempt, reason='timeout')
        if method == 'GET' and len(parts) == 2: return attempt_data(db, attempt)
        if method == 'POST' and len(parts) == 3 and parts[2] in ('answers', 'submit'):
            current = db.execute('SELECT * FROM attempts WHERE id=?', (attempt['id'],)).fetchone()
            if not current['submitted_at']:
                room = db.execute('SELECT release_id FROM exams WHERE id=?', (current['exam_id'],)).fetchone()
                if room['release_id'] or 'expected_revision' in body:
                    require(type(body.get('expected_revision')) is int and body['expected_revision'] == current['revision'], 'Bài làm đã thay đổi ở tab khác. Tải lại để lấy câu trả lời mới nhất.', 409)
                answers = body.get('answers', {})
                ids = {str(q['id']) for q in json.loads(current['questions'])}
                require(isinstance(answers, dict) and all(k in ids and isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= 3 for k, v in answers.items()), 'Câu trả lời chưa hợp lệ.')
                if parts[2] == 'submit': grade_attempt(db, current, answers)
                else: db.execute('UPDATE attempts SET answers=?,revision=revision+1 WHERE id=?', (json.dumps(answers), attempt['id']))
            return attempt_data(db, attempt)
    raise APIError(404, 'Không tìm thấy chức năng được yêu cầu.')
