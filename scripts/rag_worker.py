"""Durable leased jobs; model work stays outside SQLite write transactions."""
import json
import logging
import secrets
import threading
import time

from rag_domain import canonical
from rag_provider import ExtractiveBaseline
from rag_service import GroundedAuthoring, utc
from workspace_errors import APIError
from workspace_store import connection


def process_one(connection_factory=connection, provider=None, clock=time.time):
    provider = provider or ExtractiveBaseline()
    token, job_id = secrets.token_urlsafe(24), None
    with connection_factory() as db:
        db.execute('BEGIN IMMEDIATE')
        db.execute('UPDATE ai_jobs SET status="failed",message="Tiến trình trước bị gián đoạn nhiều lần. Tạo yêu cầu mới.",finished_at=? WHERE status="running" AND lease_until<=? AND run_count>=2', (utc(clock()), clock()))
        job = db.execute('SELECT * FROM ai_jobs WHERE status="queued" OR (status="running" AND lease_until<=? AND run_count<2) ORDER BY id LIMIT 1', (clock(),)).fetchone()
        if not job: return False
        job_id = job['id']
        db.execute('UPDATE ai_jobs SET status="running",lease_token=?,lease_until=?,run_count=run_count+1 WHERE id=?', (token, clock() + 60, job_id))
    try:
        with connection_factory() as db:
            actor = db.execute('SELECT * FROM users WHERE id=? AND status="active"', (job['user_id'],)).fetchone()
            if actor is None: raise APIError(403, 'Tài khoản không còn hoạt động.')
            service = GroundedAuthoring(db, actor, clock)
            request = json.loads(job['request'])
            sources = service.retrieve(request)
            db.execute('UPDATE ai_jobs SET sources=? WHERE id=? AND lease_token=?', (canonical(sources), job_id, token))
        # No DB connection or lock is held while an adapter executes.
        output = provider.generate(request, sources) if sources else {'decision': 'insufficient_evidence', 'items': [], 'message': 'Không tìm thấy đoạn phù hợp trong nguồn hiện hành. Thử chủ đề cụ thể hơn hoặc bổ sung tài liệu.'}
        with connection_factory() as db:
            db.execute('BEGIN IMMEDIATE')
            actor = db.execute('SELECT * FROM users WHERE id=? AND status="active"', (job['user_id'],)).fetchone()
            if actor is None: raise APIError(403, 'Tài khoản không còn hoạt động.')
            GroundedAuthoring(db, actor, clock).save_output(job_id, output, token, {'provider': provider.name, 'is_llm': provider.is_llm})
    except Exception as error:
        message = error.message if isinstance(error, APIError) else 'Không thể hoàn thành yêu cầu. Nguồn hoặc bộ soạn có lỗi; chưa tạo câu hỏi vào ngân hàng.'
        with connection_factory() as db:
            db.execute('UPDATE ai_jobs SET status="failed",message=?,finished_at=?,lease_token=NULL,lease_until=NULL WHERE id=? AND lease_token=?', (message, utc(clock()), job_id, token))
        if not isinstance(error, APIError): logging.error('Authoring job %s failed (%s)', job_id, type(error).__name__)
    return True


def start_worker():
    stop = threading.Event()
    def run():
        while not stop.is_set():
            try:
                if process_one(): continue
            except Exception: logging.exception('Authoring worker unavailable')
            stop.wait(1)
    thread = threading.Thread(target=run, name='vinassess-authoring', daemon=True)
    thread.start()
    return stop, thread
