"""Pure grounding rules: no model/network/database privileges live here."""
import hashlib
import json
import re
import unicodedata

PROMPT_VERSION = 'grounded-mcq-v1'
GUARD_VERSION = 'exact-evidence-v1'
CATEGORIES = ('Toán', 'Ngữ văn', 'Tiếng Anh', 'Vật lý', 'Hóa học', 'Sinh học', 'Lịch sử', 'Địa lý', 'Tin học', 'Khoa học tự nhiên', 'Giáo dục công dân', 'Hội nhập', 'Tuân thủ', 'Nghiệp vụ', 'Năng lực')


def compact(value):
    return re.sub(r'\s+', ' ', str(value)).strip()


def folded(value):
    return ''.join(c for c in unicodedata.normalize('NFD', value.lower()) if not unicodedata.combining(c)).replace('đ', 'd')


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


STOP = set('tao de cau hoi kiem tra trac nghiem giup toi ve theo tai lieu noi bo quy trinh chinh sach nhan vien cong ty mot cac va cua la cho duoc can nhung voi khi trong bao nhieu nao hay phu hop'.split())


def terms(value):
    return list(dict.fromkeys(t for t in re.findall(r'[\w]+', folded(value)) if len(t) > 1 and t not in STOP))[:24]


def injection_flags(value):
    plain = folded(value)
    patterns = [r'ignore.{0,40}(?:previous|system|instructions)', r'bo qua.{0,35}(?:huong dan|chi dan|lenh truoc)', r'(?:system|assistant)\s*:', r'(?:reveal|print|show).{0,25}(?:system prompt|api.key)', r'tiet lo.{0,25}(?:system prompt|khoa api)']
    return ['instruction_in_source'] if any(re.search(p, plain) for p in patterns) else []


def request_gate(request):
    topic = request.get('topic', '')
    audience = request.get('audience', '')
    if not isinstance(topic, str) or not isinstance(audience, str):
        return 'needs_clarification', 'Nhập chủ đề và đối tượng học sinh bằng văn bản.'
    if len(topic.strip()) < 5 or not terms(topic) or len(audience.strip()) < 3:
        return 'needs_clarification', 'Cần chủ đề cụ thể và đối tượng học sinh. Ví dụ: phương trình bậc hai cho học sinh lớp 9.'
    if injection_flags(topic) or re.search(r'(?:xoa|cap|thay doi).{0,25}(?:tai khoan|quyen admin|diem thi)|(?:doc|lay|tiet lo).{0,25}(?:mat khau|khoa api)', folded(topic)):
        return 'out_of_scope', 'Trợ lý chỉ soạn bản nháp câu hỏi từ nguồn được phép; không thay đổi quyền, điểm hay tiết lộ bí mật.'
    if not request.get('document_ids'):
        return 'needs_clarification', 'Chọn ít nhất một tài liệu đã được xác nhận để giới hạn nguồn sự thật.'
    return 'ready', ''


def chunk_text(content, maximum=1100):
    """Offsets refer to stored text, not invented PDF page numbers."""
    chunks, start, heading = [], 0, ''
    while start < len(content):
        end = min(len(content), start + maximum)
        if end < len(content):
            boundary = content.rfind('\n\n', start + maximum // 2, end)
            if boundary > start: end = boundary
        while start < end and content[start].isspace(): start += 1
        text = content[start:end].rstrip()
        if text:
            first = text.splitlines()[0]
            if first.startswith('#'): heading = first.lstrip('# ').strip()
            chunks.append({'start': start, 'end': start + len(text), 'text': text, 'heading': heading, 'line_start': content.count('\n', 0, start) + 1, 'line_end': content.count('\n', 0, start + len(text)) + 1, 'risk_flags': injection_flags(text)})
        start = end
        while start < len(content) and content[start].isspace(): start += 1
    return chunks


def verify_item(item, sources):
    """Checks provenance and answer extraction, not semantic entailment."""
    errors, evidence = [], []
    if not isinstance(item, dict):
        return {'valid': False, 'errors': ['invalid_schema'], 'evidence': []}
    question, options, correct = item.get('question'), item.get('options'), item.get('correct')
    if not isinstance(question, str) or not 12 <= len(question.strip()) <= 800:
        errors.append('invalid_question')
    if not isinstance(options, list) or len(options) != 4 or not all(isinstance(o, str) and 2 <= len(o.strip()) <= 1000 for o in options):
        errors.append('invalid_options')
    elif len({folded(compact(o)) for o in options}) != 4:
        errors.append('duplicate_options')
    if not isinstance(correct, int) or isinstance(correct, bool) or not 0 <= correct < 4:
        errors.append('invalid_correct')
    citations = item.get('citations', [])
    if not isinstance(citations, list) or not 1 <= len(citations) <= 3:
        errors.append('missing_citation')
        citations = []
    allowed = {s['chunk_id']: s for s in sources}
    for citation in citations:
        if not isinstance(citation, dict):
            errors.append('invalid_citation'); continue
        if not isinstance(citation.get('chunk_id'), int) or isinstance(citation.get('chunk_id'), bool):
            errors.append('invalid_citation'); continue
        source = allowed.get(citation.get('chunk_id'))
        quote = citation.get('quote', '')
        if source is None:
            errors.append('citation_not_retrieved'); continue
        if source.get('risk_flags'):
            errors.append('unsafe_source'); continue
        if not isinstance(quote, str) or not 25 <= len(quote) <= 1000 or quote not in source['text']:
            errors.append('quote_mismatch'); continue
        relative = source['text'].index(quote)
        evidence.append({'chunk_id': source['chunk_id'], 'document_id': source['document_id'], 'version_id': source['version_id'], 'version': source['version'], 'title': source['title'], 'content_hash': source['content_hash'], 'quote': quote, 'start': source['start'] + relative, 'end': source['start'] + relative + len(quote), 'line_start': source['line_start'] + source['text'][:relative].count('\n'), 'line_end': source['line_start'] + source['text'][:relative + len(quote)].count('\n')})
    if evidence and 'invalid_options' not in errors and 'invalid_correct' not in errors:
        answer = compact(options[correct])
        if not any(len(answer) >= 12 and answer in compact(e['quote']) for e in evidence):
            errors.append('correct_answer_not_grounded')
    if isinstance(question, str) and injection_flags(question): errors.append('unsafe_output')
    return {'valid': not errors, 'errors': sorted(set(errors)), 'evidence': evidence, 'semantic_support': 'human_review_required', 'guard_version': GUARD_VERSION}
