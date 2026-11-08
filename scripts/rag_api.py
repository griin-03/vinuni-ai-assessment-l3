import json
from pathlib import Path
from rag_provider import capabilities
from rag_service import GroundedAuthoring
from workspace_errors import APIError, require


def dispatch_rag(db, actor, method, route, data):
    service = GroundedAuthoring(db, actor)
    service._staff()
    p = route.split('/')
    if route == 'ai/overview' and method == 'GET':
        return {'capabilities': capabilities(), 'documents': service.documents(), 'jobs': service.jobs()}
    if route == 'ai/evaluation' and method == 'GET':
        file = Path(__file__).resolve().parents[1] / 'evaluations/reports/grounding.json'
        return json.loads(file.read_text()) if file.exists() else {'status': 'not_run', 'model_evaluation': {'status': 'not_run', 'reason': 'Chưa kết nối LLM hoặc chưa chạy đánh giá.'}}
    if route == 'knowledge/documents':
        if method == 'GET': return service.documents()
        if method == 'POST': return service.save_document(data)
    if len(p) >= 3 and p[:2] == ['knowledge', 'documents'] and p[2].isdigit():
        document_id = int(p[2])
        if len(p) == 3 and method == 'GET': return service.document_detail(document_id)
        if len(p) == 5 and p[3] == 'versions' and p[4].isdigit() and method == 'GET': return service.document_detail(document_id, int(p[4]))
        if len(p) == 4 and p[3] == 'versions' and method == 'POST': return service.save_document(data, document_id)
        if len(p) == 4 and p[3] == 'archive' and method == 'POST': return service.archive(document_id, data.get('expected_version_id'))
    if route == 'ai/drafts':
        if method == 'POST': return service.create_job(data)
        if method == 'GET': return service.jobs()
    if len(p) == 3 and p[:2] == ['ai', 'drafts'] and p[2].isdigit() and method == 'GET': return service.job_detail(int(p[2]))
    if len(p) == 4 and p[:2] == ['ai', 'items'] and p[2].isdigit() and method == 'POST':
        if p[3] == 'edit': return service.edit_item(int(p[2]), data)
        if p[3] == 'review': return service.review(int(p[2]), data)
    raise APIError(404, 'Không tìm thấy chức năng soạn có dẫn chứng.')
