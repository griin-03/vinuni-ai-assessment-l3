# Trần Văn Tuấn · AI/ML cùng Ân, trọng tâm AI engineering

Theo cập nhật của Tùng: **Tuấn và Ân cùng phụ trách AI/ML**. Tuấn từng làm web ở trường, quen .NET, muốn học AI/ML/Data; bắt đầu bằng module nhỏ, có pair và PR review. Backend nghiệp vụ, event hệ thống, database và vận hành thuộc Tùng; không dùng nền Backend của Tuấn để đẩy Tuấn khỏi hướng AI mong muốn.

Phân chia trong cặp: Ân dẫn nguồn/retrieval/prompt/rubric và chuyên môn; Tuấn dẫn adapter/pipeline chạy AI, công cụ evaluation và kiểm lỗi provider. Hai bạn cùng thiết kế, chạy thử, phân tích lỗi và review chéo; Tùng duyệt cuối và tích hợp. Không mặc định RAG phải huấn luyện model hoặc đổi stack sang .NET.

**Bắt đầu:** chạy demo; đọc `rag_provider.py`, `rag_worker.py`, `rag_domain.py`, `evaluate_rag.py` với Ân. Tùng hướng dẫn Python, cấu trúc job và PR đầu; không yêu cầu tự thiết kế toàn bộ AI service.

## TUAN-W1 · Hiểu RAG và dựng bộ chạy evaluation

- Làm: pair Ân lần theo một source → chunk → retrieval → provider → citation guard → draft. Cùng chốt input/output/status và cách ghi phiên bản.
- Hướng làm: chạy baseline hiện có, phân biệt retrieval với generation và quote match với semantic support. Nhận một PR nhỏ cho eval runner/fixture/provider contract, chưa cần key thật.
- Đầu ra: PR tái chạy được, một trace có giải thích, file kết quả ca AI đúng/sai/abstain theo contract; dùng golden có nhãn do Ân chủ trì.
- Xong khi: tự giải thích được kết quả, không nhầm 38 ca cũ với eval LLM phổ thông; Ân review kỹ thuật, Tùng duyệt. Task `✅・việc-cần-làm`, pair `🧪・mini-lab`.

## TUAN-W2 · Adapter mô hình và pipeline có kiểm lỗi

- Làm: cùng Ân nối một adapter API/gateway đã được Tùng duyệt vào interface provider. Tuấn tập trung transport/parse/status/timeout; Ân tập trung prompt/retrieval/citation/chuyên môn.
- Hướng làm: secret chỉ ở máy chủ, endpoint allowlist, output có schema; không tự fallback dịch vụ khác. Kiểm timeout, 429, output sai schema, thiếu citation và dữ liệu không được phép gửi; Tùng xử lý auth/job persistence/egress và staging.
- Đầu ra: PR adapter + fixture lỗi không gọi API thật, lệnh chạy eval LLM khi có key riêng, trace source → draft → review. Cùng Ân báo latency/token/cost nếu provider thực có số liệu.
- Xong khi: lỗi có trạng thái rõ, không tự chốt câu, không log học liệu/secret; Ân tái chạy, Tùng tích hợp và duyệt. Gate chưa có model thật vẫn ghi chưa đạt.

## TUAN-W3 · Phân tích lỗi AI từ pilot

- Làm: cùng Ân phân loại câu bị sửa/từ chối: retrieval miss, thiếu căn cứ, sai suy luận, phương án nhiễu hoặc provider failure.
- Hướng làm: chỉ nhận case được phép và đã ẩn danh; xây repro/fixture nhỏ, thêm vào tập dev đúng nhãn. Nhận một sửa lỗi trong pipeline/eval, không tune trên holdout.
- Đầu ra: PR sửa lỗi AI, bảng case trước/sau, báo tỷ lệ lỗi provider riêng với tỷ lệ chất lượng câu. Lý hỗ trợ mẫu số và nối phản hồi người dùng.
- Xong khi: đồng đội tái hiện được, nguồn truy nguyên rõ; Ân review ý nghĩa, Tùng duyệt/release.

## TUAN-W4 · Một thử nghiệm AI có kiểm soát

- Làm: cùng Ân chọn một biến retrieval/prompt/model configuration từ lỗi đã đo. Tuấn chuẩn bị harness chạy so sánh và bảng kết quả; Ân kiểm rubric/chuyên môn.
- Hướng làm: giữ nguồn/dataset và cấu hình còn lại cố định, version từng run, tách dev/holdout; không tự đổi provider hoặc gửi nguồn chưa được phép.
- Đầu ra: công cụ chạy A/B offline hoặc benchmark paired, kết quả chất lượng/abstention/latency có tử số và mẫu số, khuyến nghị có giới hạn.
- Xong khi: có thể lặp lại; Lý kiểm cách tổng hợp, Ân kiểm nhãn, Tùng quyết định áp dụng. Không gọi thử nghiệm offline là A/B người dùng thật.

## TUAN-W5 · Độ tin cậy và chi phí đường AI

- Làm: kiểm schema/error handling/quota/cost của adapter và hỗ trợ Ân khóa cấu hình ứng viên.
- Hướng làm: thử lỗi provider bằng fixture, đo timeout và retry có giới hạn nếu được duyệt; tránh gọi tính phí trùng khi retry. Tùng chịu queue/idempotency/budget/rollback ở hệ thống; Tuấn cung cấp contract và test module AI.
- Đầu ra: test adapter, runbook lỗi AI, bảng latency/cost trên run đã ghi cấu hình; liệt kê giới hạn và điều kiện dừng.
- Xong khi: không fallback ra ngoài, không bỏ guard/duyệt để tăng completion; Ân review, Tùng duyệt.

## TUAN-W6 · Báo cáo AI và bàn giao module

- Làm: cùng Ân chạy bộ eval đã khóa, demo một ca thành công, một ca thiếu nguồn và một ca lỗi provider; hướng dẫn đồng đội chạy module.
- Đầu ra: PR/commit của mình, tài liệu adapter/eval runner, bảng kết quả có provenance và phần portfolio AI engineering đã thực hiện.
- Xong khi: phân biệt code tự viết/pair/kế thừa, fixture và model thật; người khác chạy lại được. Ân/Lý kiểm nội dung và số liệu, Tùng duyệt release.

## Hỗ trợ và giới hạn trách nhiệm

Ân pair AI/ML mỗi tuần; Tùng hỗ trợ Python/integration/secret/infra và nhận phần còn lại. Khi quá tải, chia nhỏ hoặc giảm scope, không chuyển Tuấn thành owner Backend/production. Portfolio dự kiến là adapter/pipeline AI, eval harness, error analysis và kết quả pilot có nguồn; chưa ghi thành tích đã xong từ task được giao.
