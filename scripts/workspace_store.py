"""SQLite persistence and development fixtures for the VinAssess workspace."""
import hashlib
import json
import os
import secrets
import sqlite3
import time
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from rag_store import migrate as migrate_rag
from assessment_store import migrate as migrate_assessment

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = Path(os.environ.get('VINASSESS_DB', str(ROOT / '.vinassess/workspace.sqlite3')))
ROLES = {'learner': 'Học sinh', 'manager': 'Giáo viên chủ nhiệm', 'training': 'Giáo viên', 'admin': 'Quản trị nhà trường'}
PERMISSIONS = {
    'learner': ['learning.self', 'assessment.self', 'profile.self'],
    'manager': ['learning.self', 'assessment.self', 'profile.self', 'people.team', 'reports.team'],
    'training': ['learning.self', 'assessment.self', 'profile.self', 'people.all', 'reports.all', 'courses.manage', 'exams.manage', 'questions.manage'],
    'admin': ['learning.self', 'assessment.self', 'profile.self', 'people.all', 'reports.all', 'courses.manage', 'exams.manage', 'questions.manage', 'users.manage', 'settings.manage', 'audit.read'],
}
for _role in ('training', 'admin'):
    PERMISSIONS[_role] += ['knowledge.manage', 'authoring.draft', 'authoring.review']


def now_iso(days=0):
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat(timespec='seconds')


def password_hash(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), 310000).hex()
    return 'pbkdf2_sha256$310000$' + salt + '$' + digest


def password_valid(password, stored):
    try:
        _, rounds, salt, digest = stored.split('$')
        actual = hashlib.pbkdf2_hmac('sha256', password.encode(), bytes.fromhex(salt), int(rounds)).hex()
        return secrets.compare_digest(actual, digest)
    except (ValueError, TypeError):
        return False


@contextmanager
def connection():
    db = sqlite3.connect(str(DB_PATH), timeout=15)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def audit(db, user_id, action, detail):
    db.execute('INSERT INTO audit(actor,action,detail,created_at) VALUES(?,?,?,?)', (user_id, action, detail, now_iso()))


def init_store():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    DB_PATH.touch(mode=0o600, exist_ok=True)
    DB_PATH.chmod(0o600)
    with connection() as db:
        db.executescript('''
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS departments(id INTEGER PRIMARY KEY,name TEXT NOT NULL UNIQUE);
        CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY,name TEXT NOT NULL,email TEXT UNIQUE COLLATE NOCASE NOT NULL,password TEXT NOT NULL,role TEXT NOT NULL,department_id INTEGER REFERENCES departments(id),title TEXT NOT NULL DEFAULT '',status TEXT NOT NULL DEFAULT 'active',created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS sessions(token TEXT PRIMARY KEY,user_id INTEGER REFERENCES users(id),csrf TEXT NOT NULL,expires REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS login_failures(key TEXT PRIMARY KEY,count INTEGER NOT NULL,until REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS courses(id INTEGER PRIMARY KEY,title TEXT NOT NULL,category TEXT NOT NULL,description TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'draft',duration INTEGER NOT NULL,lessons TEXT NOT NULL,owner_id INTEGER REFERENCES users(id),created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS enrollments(course_id INTEGER REFERENCES courses(id),user_id INTEGER REFERENCES users(id),due TEXT NOT NULL,completed TEXT NOT NULL DEFAULT '[]',completed_at TEXT,PRIMARY KEY(course_id,user_id));
        CREATE TABLE IF NOT EXISTS questions(id INTEGER PRIMARY KEY,prompt TEXT NOT NULL,options TEXT NOT NULL,correct INTEGER NOT NULL,explanation TEXT NOT NULL,category TEXT NOT NULL,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS exams(id INTEGER PRIMARY KEY,title TEXT NOT NULL,description TEXT NOT NULL,question_ids TEXT NOT NULL,duration INTEGER NOT NULL,pass_score INTEGER NOT NULL,max_attempts INTEGER NOT NULL DEFAULT 2,due TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'draft',created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS exam_assignments(exam_id INTEGER REFERENCES exams(id),user_id INTEGER REFERENCES users(id),PRIMARY KEY(exam_id,user_id));
        CREATE TABLE IF NOT EXISTS attempts(id INTEGER PRIMARY KEY,exam_id INTEGER REFERENCES exams(id),user_id INTEGER REFERENCES users(id),started REAL NOT NULL,deadline REAL NOT NULL,answers TEXT NOT NULL DEFAULT '{}',questions TEXT NOT NULL,submitted_at TEXT,score INTEGER,passed INTEGER);
        CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY,actor INTEGER REFERENCES users(id),action TEXT NOT NULL,detail TEXT NOT NULL,created_at TEXT NOT NULL);
        ''')
        if db.execute('SELECT 1 FROM settings WHERE key="initialized"').fetchone():
            migrate_rag(db, now_iso())
            migrate_assessment(db, now_iso())
            return
        demo = os.environ.get('VINASSESS_DEMO', '1') != '0'
        if not demo and len(os.environ.get('VINASSESS_ADMIN_PASSWORD', '')) < 12:
            raise RuntimeError('Đặt VINASSESS_ADMIN_PASSWORD ít nhất 12 ký tự khi VINASSESS_DEMO=0.')
        for i, name in enumerate(['Nhân sự & Đào tạo', 'Kinh doanh', 'Công nghệ', 'Vận hành'], 1):
            db.execute('INSERT INTO departments VALUES(?,?)', (i, name))
        settings = {'initialized': '1', 'demo': '1' if demo else '0', 'company': 'VinAssess Company', 'company_email': 'hr@vinassess.local', 'timezone': 'Asia/Ho_Chi_Minh'}
        db.executemany('INSERT INTO settings VALUES(?,?)', settings.items())
        if not demo:
            db.execute('INSERT INTO users(name,email,password,role,department_id,title,created_at) VALUES(?,?,?,?,?,?,?)', ('Quản trị hệ thống', os.environ.get('VINASSESS_ADMIN_EMAIL', 'admin@vinassess.local'), password_hash(os.environ['VINASSESS_ADMIN_PASSWORD']), 'admin', 1, 'Quản trị hệ thống', now_iso()))
            migrate_rag(db, now_iso())
            migrate_assessment(db, now_iso())
            return
        seed_demo(db)
        migrate_rag(db, now_iso())
        migrate_assessment(db, now_iso())
    try:
        DB_PATH.chmod(0o600)
    except OSError:
        pass


def seed_demo(db):
    password = password_hash('VinAssess@2026')
    people = [
        ('Nguyễn Minh Anh', 'admin', 'admin', 1, 'Quản trị hệ thống'),
        ('Trần Hoài An', 'training', 'training', 1, 'Chuyên viên đào tạo'),
        ('Lê Minh Quân', 'manager', 'manager', 2, 'Trưởng phòng Kinh doanh'),
        ('Nguyễn Hà Linh', 'learner', 'learner', 2, 'Chuyên viên kinh doanh'),
        ('Phạm Tuấn Anh', 'tuananh', 'learner', 2, 'Chuyên viên kinh doanh'),
        ('Vũ Ngọc Mai', 'ngocmai', 'learner', 2, 'Chuyên viên khách hàng'),
        ('Đỗ Đức Huy', 'duchuy', 'learner', 2, 'Chuyên viên kinh doanh'),
        ('Bùi Phương Thảo', 'phuongthao', 'learner', 2, 'Chuyên viên khách hàng'),
        ('Trần Quốc Bảo', 'quocbao', 'learner', 3, 'Kỹ sư phần mềm'),
        ('Nguyễn Khánh Vy', 'khanhvy', 'learner', 3, 'Chuyên viên phân tích'),
        ('Lê Hải Đăng', 'haidang', 'learner', 3, 'Kỹ sư hệ thống'),
        ('Phan Thu Hà', 'thuha', 'manager', 3, 'Trưởng phòng Công nghệ'),
        ('Hoàng Gia Hân', 'giahan', 'learner', 4, 'Chuyên viên vận hành'),
        ('Đặng Minh Khoa', 'minhkhoa', 'learner', 4, 'Điều phối vận hành'),
        ('Ngô Thanh Tâm', 'thanhtam', 'manager', 4, 'Trưởng phòng Vận hành'),
        ('Lý Bảo Ngọc', 'baongoc', 'learner', 1, 'Chuyên viên nhân sự'),
        ('Mai Hoàng Nam', 'hoangnam', 'learner', 4, 'Chuyên viên vận hành'),
        ('Phạm Hồng Nhung', 'hongnhung', 'learner', 1, 'Chuyên viên tuyển dụng'),
    ]
    for name, email, role, department, title in people:
        db.execute('INSERT INTO users(name,email,password,role,department_id,title,created_at) VALUES(?,?,?,?,?,?,?)', (name, email + '@vinassess.local', password, role, department, title, now_iso(-35)))
    curricula = [
        ('Hội nhập & văn hóa doanh nghiệp', 'Hội nhập', 'Bắt đầu hành trình mới với sự thấu hiểu về văn hóa, con người và cách chúng ta làm việc cùng nhau.', 90, [
            ('Chào mừng đến với đội ngũ', 'Một khởi đầu rõ ràng giúp bạn tự tin hơn trong công việc. Trong tuần đầu tiên, hãy xác nhận vai trò, mục tiêu và các đầu mối hỗ trợ cùng quản lý trực tiếp.', ['Trao đổi với quản lý về mục tiêu trong 30 ngày đầu.', 'Hoàn thành thông tin nhân sự và kiểm tra các quyền truy cập được cấp.', 'Lên lịch gặp đồng nghiệp và người hướng dẫn trong nhóm.']),
            ('Giá trị cốt lõi trong công việc', 'Văn hóa được thể hiện qua các quyết định mỗi ngày: giữ cam kết, trao đổi minh bạch và cùng chịu trách nhiệm về kết quả.', ['Làm rõ kỳ vọng và thời hạn trước khi nhận việc.', 'Phản hồi vào hành vi và kết quả, tôn trọng con người.', 'Chủ động báo sớm khi có rủi ro ảnh hưởng tới cam kết.']),
            ('Cộng tác giữa các phòng ban', 'Mỗi yêu cầu phối hợp cần có mục tiêu, người chịu trách nhiệm và tiêu chí hoàn thành. Trao đổi đầy đủ bối cảnh giúp giảm hiểu nhầm và tránh làm lại.', ['Ghi rõ mục tiêu, đầu ra và thời hạn trong yêu cầu phối hợp.', 'Chọn kênh trao đổi phù hợp với tính khẩn cấp.', 'Tóm tắt quyết định và xác nhận lại người thực hiện.']),
            ('Kế hoạch 30–60–90 ngày', 'Cùng quản lý biến kỳ vọng thành những cột mốc cụ thể. Kế hoạch cần phản ánh công việc thực tế và được cập nhật qua các buổi trao đổi định kỳ.', ['30 ngày: nắm quy trình, công cụ và các đầu mối.', '60 ngày: tự thực hiện các nhiệm vụ thuộc phạm vi vai trò.', '90 ngày: nhìn lại kết quả và thống nhất mục tiêu tiếp theo.'])]),
        ('An toàn thông tin cho mọi nhân viên', 'Tuân thủ', 'Nhận diện rủi ro, bảo vệ tài khoản và xử lý đúng khi gặp sự cố trong công việc.', 60, [
            ('Bảo vệ tài khoản làm việc', 'Tài khoản doanh nghiệp là danh tính của bạn trong hệ thống. Không chia sẻ mật khẩu hoặc mã xác thực với bất kỳ ai, kể cả người tự nhận là bộ phận hỗ trợ.', ['Dùng mật khẩu riêng cho từng dịch vụ và bật xác thực đa yếu tố khi có.', 'Khóa màn hình khi rời khỏi bàn làm việc.', 'Chỉ sử dụng thiết bị và phần mềm theo chính sách doanh nghiệp.']),
            ('Nhận diện thư và đường dẫn giả mạo', 'Thư giả mạo thường tạo cảm giác khẩn cấp, yêu cầu cung cấp thông tin hoặc mở tệp bất thường. Hãy kiểm tra người gửi và xác minh bằng một kênh độc lập.', ['Kiểm tra tên miền người gửi và địa chỉ liên kết.', 'Không nhập mật khẩu vào trang mở từ thư không rõ nguồn gốc.', 'Báo cáo thư đáng ngờ cho bộ phận phụ trách an toàn thông tin.']),
            ('Chia sẻ dữ liệu đúng phạm vi', 'Chỉ chia sẻ dữ liệu cho người có nhu cầu công việc và quyền truy cập phù hợp. Khi phát hiện sự cố, ghi lại thông tin cần thiết và báo ngay theo quy trình nội bộ.', ['Kiểm tra người nhận và quyền xem trước khi gửi tài liệu.', 'Không tải dữ liệu nội bộ lên công cụ công khai chưa được phê duyệt.', 'Báo sớm sự cố; không tự ý xóa bằng chứng hoặc che giấu thông tin.'])]),
        ('Kỹ năng tư vấn & chăm sóc khách hàng', 'Nghiệp vụ', 'Lắng nghe có cấu trúc, xác định nhu cầu và xây dựng cuộc trao đổi hướng tới giá trị cho khách hàng.', 120, [
            ('Lắng nghe và làm rõ nhu cầu', 'Bắt đầu bằng câu hỏi mở về bối cảnh và mục tiêu. Tóm tắt điều bạn hiểu trước khi đề xuất giải pháp để bảo đảm hai bên đang nói về cùng một vấn đề.', ['Hỏi về mục tiêu, khó khăn và tiêu chí thành công.', 'Không ngắt lời hoặc đưa giải pháp quá sớm.', 'Xác nhận các nhu cầu ưu tiên bằng ngôn ngữ của khách hàng.']),
            ('Tư vấn dựa trên giá trị', 'Liên hệ giải pháp với nhu cầu đã xác nhận. Trình bày rõ phạm vi đáp ứng, điều kiện triển khai và những giới hạn cần trao đổi thêm.', ['Dùng ví dụ phù hợp với bối cảnh của khách hàng.', 'Không cam kết tính năng hoặc thời hạn khi chưa xác minh.', 'Thống nhất bước tiếp theo và người chịu trách nhiệm.']),
            ('Xử lý phản hồi và khiếu nại', 'Giữ bình tĩnh, ghi nhận trải nghiệm và tập trung vào sự việc. Một phản hồi tốt cần có đầu mối xử lý, thời gian cập nhật và bước xác nhận kết quả.', ['Lắng nghe, xác nhận vấn đề và ghi nhận thông tin.', 'Chuyển đúng đầu mối thay vì hứa vượt thẩm quyền.', 'Theo dõi đến khi khách hàng nhận được phản hồi rõ ràng.'])]),
        ('Phản hồi hiệu quả cho quản lý', 'Năng lực', 'Tổ chức trao đổi một-một và đưa phản hồi dựa trên hành vi, tác động và kế hoạch cải thiện.', 75, [
            ('Chuẩn bị buổi trao đổi một-một', 'Thu thập ví dụ cụ thể và xác định điều cần hiểu thêm. Buổi trao đổi một-một là cơ hội tháo gỡ khó khăn và định hướng phát triển.', ['Gửi trước các chủ đề cần trao đổi.', 'Dành thời gian để nhân viên chia sẻ.', 'Ghi lại hành động và thời điểm theo dõi.']),
            ('Phản hồi theo tình huống và hành vi', 'Mô tả bối cảnh, hành vi quan sát được và tác động; tránh suy đoán ý định hoặc đánh giá tính cách.', ['Dùng ví dụ cụ thể và ngôn ngữ trung tính.', 'Hỏi góc nhìn của người nhận phản hồi.', 'Cùng thống nhất hành vi cần duy trì hoặc thay đổi.'])]),
        ('Quy trình vận hành & cải tiến liên tục', 'Nghiệp vụ', 'Xác định điểm nghẽn, chuẩn hóa bàn giao và theo dõi chất lượng công việc theo chu trình cải tiến.', 90, [
            ('Bàn giao công việc có tiêu chí', 'Một lần bàn giao hoàn chỉnh cần có kết quả, tài liệu và tiêu chí chấp nhận để người nhận tiếp tục thực hiện.', ['Ghi rõ đầu vào và đầu ra.', 'Xác nhận người nhận và thời điểm bàn giao.', 'Theo dõi các vấn đề phát sinh đến khi được xử lý.']),
            ('Cải tiến từ dữ liệu thực tế', 'Chọn vấn đề có tác động rõ ràng, tìm nguyên nhân và thử nghiệm thay đổi trong phạm vi nhỏ trước khi mở rộng.', ['Xác định số đo trước khi thay đổi.', 'Thử nghiệm và so sánh kết quả.', 'Ghi nhận cách làm hiệu quả vào quy trình.'])]),
        ('Ứng dụng AI có trách nhiệm', 'Năng lực', 'Lựa chọn công việc phù hợp, bảo vệ dữ liệu và kiểm tra chất lượng đầu ra khi sử dụng công cụ AI.', 45, [
            ('Kiểm tra trước khi sử dụng đầu ra AI', 'Đầu ra AI có thể sai hoặc thiếu bối cảnh. Người sử dụng chịu trách nhiệm kiểm tra tính chính xác và mức phù hợp trước khi đưa vào công việc.', ['Không gửi thông tin mật vào công cụ chưa được phê duyệt.', 'Đối chiếu các dữ kiện quan trọng với nguồn đáng tin cậy.', 'Giữ bước kiểm tra của con người với quyết định có ảnh hưởng.'])]),
    ]
    for i, (title, category, description, duration, lessons) in enumerate(curricula, 1):
        items = [{'id': n + 1, 'title': t, 'body': body, 'points': points, 'minutes': max(8, duration // len(lessons))} for n, (t, body, points) in enumerate(lessons)]
        db.execute('INSERT INTO courses VALUES(?,?,?,?,?,?,?,?,?)', (i, title, category, description, 'draft' if i == 6 else 'published', duration, json.dumps(items, ensure_ascii=False), 2, now_iso(-20 + i)))
    for uid in range(1, len(people) + 1):
        for cid in [1, 2, 3 if people[uid - 1][3] == 2 else 5]:
            length = len(curricula[cid - 1][4]); done = min(length, (uid + cid) % (length + 1))
            if uid == 4: done = 2 if cid == 1 else 0
            db.execute('INSERT INTO enrollments VALUES(?,?,?,?,?)', (cid, uid, now_iso(6 if cid == 1 else 12), json.dumps(list(range(1, done + 1))), now_iso(-2) if done == length else None))
    question_data = [
        ('Bạn nhận được thư yêu cầu cung cấp mã xác thực để “khắc phục tài khoản”. Bạn nên làm gì?', ['Gửi mã để không gián đoạn công việc', 'Không cung cấp mã, xác minh qua kênh hỗ trợ chính thức', 'Chuyển mã cho đồng nghiệp kiểm tra', 'Trả lời và yêu cầu giữ bí mật'], 1, 'Mã xác thực không được chia sẻ. Xác minh yêu cầu qua kênh chính thức và báo cáo thư đáng ngờ.', 'Tuân thủ'),
        ('Trước khi chia sẻ tài liệu nội bộ, bước nào là phù hợp nhất?', ['Bật liên kết công khai để thuận tiện', 'Chỉ kiểm tra tên tệp', 'Kiểm tra người nhận và quyền truy cập theo nhu cầu công việc', 'Gửi bản sao tới email cá nhân'], 2, 'Nguyên tắc tối thiểu quyền yêu cầu giới hạn người nhận và quyền truy cập đúng phạm vi.', 'Tuân thủ'),
        ('Khi phát hiện nghi ngờ rò rỉ dữ liệu, bạn nên làm gì trước?', ['Xóa toàn bộ thông tin liên quan', 'Đợi đến cuối tuần', 'Tự công bố trên mạng xã hội', 'Báo ngay đầu mối phụ trách theo quy trình và giữ thông tin cần thiết'], 3, 'Báo sớm giúp giảm tác động và bảo toàn thông tin phục vụ xử lý sự cố.', 'Tuân thủ'),
        ('Lựa chọn nào giúp bảo vệ tài khoản tốt hơn?', ['Dùng cùng mật khẩu cho mọi dịch vụ', 'Dùng mật khẩu riêng và bật xác thực đa yếu tố', 'Ghi mật khẩu lên bàn làm việc', 'Chia sẻ tài khoản trong nhóm'], 1, 'Mật khẩu riêng và xác thực đa yếu tố giảm rủi ro khi một dịch vụ bị lộ thông tin.', 'Tuân thủ'),
        ('Một yêu cầu phối hợp rõ ràng cần có những thông tin nào?', ['Chỉ cần tên người gửi', 'Càng nhiều người nhận càng tốt', 'Mục tiêu, đầu ra, người phụ trách và thời hạn', 'Chỉ cần đánh dấu khẩn cấp'], 2, 'Yêu cầu đầy đủ giúp các bên thống nhất kỳ vọng và trách nhiệm.', 'Hội nhập'),
        ('Khi có rủi ro trễ hạn, cách xử lý phù hợp là gì?', ['Báo sớm, nêu tác động và đề xuất hướng xử lý', 'Chờ đến hạn mới thông báo', 'Không cập nhật để tránh gây lo lắng', 'Tự thay đổi kỳ vọng của người nhận'], 0, 'Minh bạch sớm tạo điều kiện để nhóm phối hợp điều chỉnh kế hoạch.', 'Hội nhập'),
        ('Mục tiêu của kế hoạch 30–60–90 ngày là gì?', ['Xếp hạng mọi nhân viên', 'Thống nhất các cột mốc hội nhập và phát triển theo vai trò', 'Thay thế toàn bộ trao đổi với quản lý', 'Giảm mọi hoạt động hướng dẫn'], 1, 'Kế hoạch cụ thể hóa kỳ vọng và được cập nhật thông qua trao đổi với quản lý.', 'Hội nhập'),
        ('Bạn nên làm gì trước khi đề xuất giải pháp cho khách hàng?', ['Giới thiệu ngay toàn bộ tính năng', 'Đưa ra mức giảm giá', 'Xác nhận bối cảnh và nhu cầu ưu tiên', 'Cam kết mọi yêu cầu'], 2, 'Tư vấn hiệu quả bắt đầu từ việc hiểu đúng nhu cầu.', 'Nghiệp vụ'),
        ('Khách hàng yêu cầu cam kết vượt thẩm quyền của bạn. Bạn nên làm gì?', ['Đồng ý trước rồi xử lý sau', 'Từ chối trao đổi tiếp', 'Chuyển cho người bất kỳ', 'Ghi nhận và xác minh với đầu mối có thẩm quyền'], 3, 'Không cam kết khi chưa xác minh giúp bảo vệ kỳ vọng và uy tín doanh nghiệp.', 'Nghiệp vụ'),
        ('Phản hồi hiệu quả nên tập trung vào điều gì?', ['Hành vi quan sát được và tác động cụ thể', 'Tính cách của người nhận', 'So sánh với mọi đồng nghiệp', 'Suy đoán ý định'], 0, 'Phản hồi dựa trên hành vi và tác động giúp người nhận hiểu cách cải thiện.', 'Năng lực'),
        ('Khi dùng đầu ra từ AI trong công việc, bạn cần làm gì?', ['Dùng ngay vì AI luôn đúng', 'Kiểm tra dữ kiện, bối cảnh và phạm vi sử dụng', 'Gửi toàn bộ dữ liệu mật để tăng độ chính xác', 'Bỏ qua mọi nguồn tham khảo'], 1, 'Con người cần kiểm tra chất lượng và bảo vệ dữ liệu khi sử dụng AI.', 'Năng lực'),
        ('Trước khi mở rộng một thay đổi quy trình, nên làm gì?', ['Triển khai cho mọi phòng ban ngay', 'Chỉ dựa vào cảm giác', 'Thử nghiệm phạm vi nhỏ và so sánh số đo', 'Bỏ qua tác động với người thực hiện'], 2, 'Thử nghiệm có đo lường giúp xác định tác động thực tế trước khi mở rộng.', 'Nghiệp vụ'),
    ]
    for prompt, options, correct, explanation, category in question_data:
        db.execute('INSERT INTO questions(prompt,options,correct,explanation,category,created_at) VALUES(?,?,?,?,?,?)', (prompt, json.dumps(options, ensure_ascii=False), correct, explanation, category, now_iso(-15)))
    for i, (title, desc, ids, duration, passing, due) in enumerate([
        ('An toàn thông tin · Đánh giá định kỳ', 'Kiểm tra khả năng nhận diện và xử lý các rủi ro thông tin thường gặp.', [1, 2, 3, 4], 15, 75, 7),
        ('Hội nhập · Sẵn sàng cho hành trình mới', 'Xác nhận kiến thức nền tảng về cộng tác và văn hóa làm việc.', [5, 6, 7, 11], 20, 75, 10),
        ('Tư vấn khách hàng · Kiến thức nghiệp vụ', 'Đánh giá cách xác định nhu cầu và phối hợp xử lý yêu cầu khách hàng.', [8, 9, 6, 12], 15, 75, 14),
    ], 1):
        db.execute('INSERT INTO exams VALUES(?,?,?,?,?,?,?,?,?,?)', (i, title, desc, json.dumps(ids), duration, passing, 2, now_iso(due), 'published', now_iso(-8)))
        for uid in range(1, len(people) + 1):
            if i < 3 or people[uid - 1][3] == 2:
                db.execute('INSERT INTO exam_assignments VALUES(?,?)', (i, uid))
                if uid not in (1, 2, 3, 4) and (uid + i) % 3 != 0:
                    qs = [dict(db.execute('SELECT * FROM questions WHERE id=?', (qid,)).fetchone()) for qid in ids]
                    score = 100 if uid % 4 else 50
                    db.execute('INSERT INTO attempts(exam_id,user_id,started,deadline,answers,questions,submitted_at,score,passed) VALUES(?,?,?,?,?,?,?,?,?)', (i, uid, time.time() - 90000, time.time() - 89000, '{}', json.dumps(qs), now_iso(-1), score, int(score >= passing)))
    audit(db, 2, 'course.published', 'Xuất bản chương trình Hội nhập & văn hóa doanh nghiệp')
    audit(db, 2, 'exam.published', 'Mở đợt khảo thí An toàn thông tin · Đánh giá định kỳ')
    audit(db, 1, 'workspace.created', 'Khởi tạo không gian trải nghiệm với dữ liệu mẫu')
