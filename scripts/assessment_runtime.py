"""Authoritative attempt scoring, answer serialization and timeout recovery."""
import json
import threading
import time
from datetime import datetime, timezone

from workspace_store import connection, audit, now_iso


def grade_attempt(db, attempt, answers=None, reason='submitted'):
    if attempt['submitted_at']:
        return
    questions = json.loads(attempt['questions'])
    answers = answers if answers is not None else json.loads(attempt['answers'])
    correct = sum(answers.get(str(q['id'])) == q['correct'] for q in questions)
    score = round(correct * 100 / max(1, len(questions)))
    passing = attempt['pass_score_snapshot']
    if passing is None:
        passing = db.execute('SELECT pass_score FROM exams WHERE id=?', (attempt['exam_id'],)).fetchone()[0]
    submitted_at = datetime.fromtimestamp(min(time.time(), attempt['deadline']), timezone.utc).isoformat(timespec='seconds')
    changed = db.execute('UPDATE attempts SET answers=?,submitted_at=?,score=?,passed=?,submission_reason=?,revision=revision+1 WHERE id=? AND submitted_at IS NULL', (json.dumps(answers), submitted_at, score, int(score >= passing), reason, attempt['id']))
    if changed.rowcount:
        audit(db, attempt['user_id'], 'exam.submitted', ('Hết giờ' if reason == 'timeout' else 'Nộp bài') + ' · ' + str(score) + '/100 điểm')


def settle_expired(db, clock=None):
    clock = time.time() if clock is None else clock
    for attempt in db.execute('SELECT * FROM attempts WHERE submitted_at IS NULL AND deadline<=?', (clock,)).fetchall():
        grade_attempt(db, attempt, reason='timeout')


def attempt_data(db, attempt):
    data = dict(db.execute('SELECT * FROM attempts WHERE id=?', (attempt['id'],)).fetchone())
    exam = db.execute('SELECT * FROM exams WHERE id=?', (data['exam_id'],)).fetchone()
    data['title'] = data['title_snapshot'] or exam['title']
    data['pass_score'] = data['pass_score_snapshot'] if data['pass_score_snapshot'] is not None else exam['pass_score']
    data['results_visible'] = bool(data['submitted_at']) and (exam['result_policy'] == 'immediate' or datetime.fromisoformat(exam['due']).timestamp() <= time.time())
    data['review_available_at'] = exam['due'] if exam['result_policy'] == 'after_close' else None
    data['room_id'] = exam['id'] if exam['release_id'] else None
    data['answers'] = json.loads(data['answers'])
    # Allowlist: teacherSupport, provenance and future private fields never leak.
    public = []
    for original in json.loads(data['questions']):
        q = {key: original[key] for key in ('id', 'prompt', 'options', 'category', 'objective') if key in original}
        if isinstance(q['options'], str):
            q['options'] = json.loads(q['options'])
        if data['results_visible']:
            q.update(correct=original['correct'], explanation=original['explanation'])
        public.append(q)
    data['questions'] = public
    data['server_time'] = time.time()
    return data


def start_expiry_worker():
    stop = threading.Event()

    def run():
        while not stop.wait(1):
            try:
                with connection() as db:
                    db.execute('BEGIN IMMEDIATE')
                    settle_expired(db)
            except Exception as error:
                print('Attempt expiry retry: ' + type(error).__name__, flush=True)

    thread = threading.Thread(target=run, name='assessment-expiry', daemon=True)
    thread.start()
    return stop, thread
