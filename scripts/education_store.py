"""Create a labelled school demo without replacing existing corporate records.

Only the runnable app calls this. Legacy regression fixtures stay independent.
"""
import hashlib
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from workspace_store import connection, now_iso, audit
from rag_store import add_version


def prepare_school_demo():
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        if db.execute('SELECT value FROM settings WHERE key="education_mvp"').fetchone(): return
        demo = db.execute('SELECT value FROM settings WHERE key="demo"').fetchone()
        db.execute('INSERT INTO settings VALUES("education_mvp","1")')
        if not demo or demo[0] != '1': return
        teacher = db.execute('SELECT id FROM users WHERE email="training@vinassess.local" AND role="training"').fetchone()
        learner = db.execute('SELECT id FROM users WHERE email="learner@vinassess.local" AND role="learner"').fetchone()
        if not teacher or not learner: return
        data = json.loads((Path(__file__).resolve().parents[1] / 'content/school-demo.json').read_text())
        now = now_iso()
        # Rename only known demo group labels; retain IDs, rosters and all past work.
        for old, new in [('Nhân sự & Đào tạo', 'Tổ giáo viên'), ('Kinh doanh', 'Lớp 9A'), ('Công nghệ', 'Lớp 12A'), ('Vận hành', 'Lớp 10A')]:
            db.execute('UPDATE departments SET name=? WHERE name=?', (new, old))
        db.execute('UPDATE settings SET value="Trường học VinAssess · Mẫu" WHERE key="company" AND value="VinAssess Company"')
        db.execute('UPDATE users SET title=CASE role WHEN "learner" THEN "Học sinh · Tài khoản mẫu" WHEN "manager" THEN "Giáo viên chủ nhiệm · Mẫu" WHEN "training" THEN "Giáo viên Toán · Mẫu" ELSE "Quản trị · Mẫu" END WHERE email LIKE "%@vinassess.local"')
        for item in data['items']:
            db.execute('INSERT INTO questions(prompt,options,correct,explanation,category,created_at) VALUES(?,?,?,?,?,?)', (item['prompt'], json.dumps(item['options'], ensure_ascii=False), item['correct'], item['explanation'], 'Toán', now))
        payload = json.dumps(data['items'], ensure_ascii=False, sort_keys=True, separators=(',', ':'))
        paper = db.execute('INSERT INTO assessment_papers(owner_id,title,description,subject,grade,items,status,created_at,updated_at) VALUES(?,?,?,?,?,?,"released",?,?)', (teacher['id'], data['title']+' · Mẫu', data['description'], data['subject'], data['grade'], payload, now, now)).lastrowid
        release = db.execute('INSERT INTO assessment_releases(paper_id,owner_id,title,description,subject,grade,items,content_hash,created_at) VALUES(?,?,?,?,?,?,?,?,?)', (paper, teacher['id'], data['title']+' · Mẫu', data['description'], data['subject'], data['grade'], payload, hashlib.sha256(payload.encode()).hexdigest(), now)).lastrowid
        due = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(timespec='seconds')
        room = db.execute('INSERT INTO exams(title,description,question_ids,duration,pass_score,max_attempts,due,status,created_at,release_id,owner_id,starts_at,result_policy) VALUES(?,?,"[]",15,70,2,?,"published",?,?,?, ?,"after_close")', ('Toán 9 · Kiểm tra ngắn · Phòng mẫu', data['description'], due, now, release, teacher['id'], time.time()-60)).lastrowid
        students = db.execute('SELECT id FROM users WHERE role="learner" AND department_id=2 AND email LIKE "%@vinassess.local"').fetchall()
        for student in students:
            db.execute('INSERT INTO exam_assignments VALUES(?,?)', (room, student['id']))
            if student['id'] == learner['id']: continue
            answers = {item['id']: item['correct'] if (student['id']+i)%3 else (item['correct']+1)%4 for i,item in enumerate(data['items'])}
            score = round(sum(answers[i['id']]==i['correct'] for i in data['items'])*100/len(data['items']))
            db.execute('INSERT INTO attempts(exam_id,user_id,started,deadline,answers,questions,submitted_at,score,passed,pass_score_snapshot,title_snapshot,submission_reason) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)', (room,student['id'],time.time()-1000,time.time()-100,json.dumps(answers),payload,now,score,int(score>=70),70,'Toán 9 · Kiểm tra ngắn · Phòng mẫu','submitted'))
        doc = db.execute('INSERT INTO knowledge_documents(title,category,owner_id,sample_key,created_at) VALUES(?,"Toán",?,"school-quadratic",?)', (data['source']['title'], teacher['id'], now)).lastrowid
        add_version(db, doc, data['source']['content'], now[:10], teacher['id'], now)
        audit(db, teacher['id'], 'school.demo_created', 'Thêm đề, phòng và kết quả minh họa THCS; giữ lịch sử trước đó')
