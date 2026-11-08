"""Local baseline and a small seam for a future approved model/gateway adapter.

No HTTP client, external endpoint, API key or outbound fallback is used here.
Baseline drafts are extraction templates, not LLM-generated content.
"""
import re
from rag_domain import folded, terms


class ExtractiveBaseline:
    name = 'extractive'
    is_llm = False

    def generate(self, request, sources):
        candidates = []
        numeric_claims = {}
        keywords = set(terms(request['topic']))
        for source in sources:
            if source.get('risk_flags'): continue
            for sentence in re.split(r'(?<=[.!?])\s+|\n+', source['text']):
                sentence = sentence.strip()
                if not 35 <= len(sentence) <= 650 or sentence.startswith('#'): continue
                if not any(k in folded(sentence) for k in ('phai ', 'can ', 'khong duoc ', 'chi ', 'co trach nhiem ')): continue
                overlap = len(keywords & set(terms(sentence)))
                if overlap:
                    candidates.append((overlap, source, sentence))
                    values = re.findall(r'\d+', sentence)
                    if values:
                        skeleton = re.sub(r'\d+', '#', folded(sentence))
                        numeric_claims.setdefault(skeleton, set()).add(tuple(values))
        if any(len(values) > 1 for values in numeric_claims.values()):
            return {'decision': 'needs_clarification', 'items': [], 'message': 'Có các đoạn quy định gần trùng nhưng khác con số trong nguồn đã chọn. Xác nhận tài liệu có thẩm quyền hoặc giới hạn lại nguồn trước khi soạn.'}
        candidates.sort(key=lambda c: -c[0])
        items, used = [], set()
        for _, source, sentence in candidates:
            if sentence in used: continue
            used.add(sentence)
            stem = ' '.join(sentence.split()[:9]).rstrip('.,')
            items.append({'question': 'Theo tài liệu, với nội dung “' + stem + '…”, quy định nào sau đây được nêu đúng?', 'options': [sentence, 'Có thể bỏ qua yêu cầu này khi công việc đang gấp.', 'Chỉ cần thực hiện yêu cầu này khi có người nhắc nhở.', 'Mỗi người được tự thay đổi yêu cầu này mà không cần xác nhận.'], 'correct': 0, 'citations': [{'chunk_id': source['chunk_id'], 'quote': sentence}]})
            if len(items) >= request['count']: break
        return {'decision': 'draft' if items else 'insufficient_evidence', 'items': items, 'message': ('Đã trích xuất ' + str(len(items)) + '/' + str(request['count']) + ' câu. Đây là bản nháp theo mẫu, không dùng LLM; cần kiểm tra ý nghĩa và phương án nhiễu.' if items else 'Chưa tìm thấy quy định đủ cụ thể trong nguồn đã chọn. Bổ sung tài liệu hoặc làm rõ chủ đề.')}


def capabilities():
    return {'mode': 'local_only', 'llm_status': 'not_configured', 'external_egress': False, 'provider': 'extractive', 'is_llm': False, 'message': 'Xử lý tại máy. Chế độ trích xuất theo mẫu không phải đánh giá chất lượng LLM. Chưa có kết nối mô hình hoặc gateway.'}
