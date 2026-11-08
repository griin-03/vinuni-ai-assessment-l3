# Soạn câu hỏi có dẫn chứng cho giáo viên

Bối cảnh: giáo viên/học sinh THCS, THPT; [MVP](assessment-mvp.md). Rubric Level 3 được chủ dự án cung cấp, không phải chứng nhận đã đạt hoặc đã đối chiếu độc lập với chương trình.

## Một quyết định AI trong luồng chính

**Giáo viên chọn học liệu được phép và mục tiêu kiến thức; hệ thống đề xuất câu có đủ căn cứ hoặc yêu cầu bổ sung, để giáo viên quyết định có đưa câu vào ngân hàng/đề hay không.**

Giả thuyết cần kiểm chứng: giáo viên tốn thời gian soạn và kiểm tra nguồn/độ đúng, sau đó còn phải ghép điểm để chọn nội dung ôn. Chưa có dữ liệu về tần suất, thời gian hay số người bị ảnh hưởng. Không dùng cơ sở doanh nghiệp cũ hoặc dữ liệu tự tạo làm bằng chứng nỗi đau phổ thông.

Hiện dùng `ExtractiveBaseline` **trích xuất theo mẫu tại máy**, không LLM, không gửi học liệu ra ngoài. LLM/gateway nằm trong kế hoạch tuần 1–2; kết quả phần mềm hiện tại chỉ chứng minh một số cơ chế.

## Đường dữ liệu đã có

1. Nhập TXT/Markdown hoặc dán văn bản; người nhập xác nhận quyền dùng, phạm vi nhóm và ngày hiệu lực.
2. Phiên bản/hash, đoạn nguồn và vị trí dòng/ký tự được giữ; không tự bịa trang PDF. Tìm bằng SQLite FTS5, lọc quyền/trạng thái/hiệu lực trước truy xuất; chưa semantic/vector search.
3. Yêu cầu cần nguồn, chủ đề, đối tượng. Thiếu hoặc vượt phạm vi trả quyết định làm rõ/từ chối, không bù câu tùy ý.
4. Job có lease, request key ràng buộc payload; xử lý provider ngoài transaction ghi. Output bị kiểm schema, citation thuộc các đoạn đã lấy, quote nguyên văn và đáp án có trong quote.
5. Giáo viên mở đúng nguồn, kiểm ý nghĩa/đáp án/phương án nhiễu, sửa/từ chối/duyệt. Revision và transaction chặn duyệt tab cũ/duyệt lặp. Nguồn cũ/thu hồi bị chặn dùng mới.
6. Câu được duyệt giữ provenance và phạm vi; đề/phòng phải giữ giới hạn nguồn. Payload học sinh không lộ provenance/đáp án trước thời điểm cho phép.

**Quote khớp không chứng minh kết luận đúng.** Với câu tính Toán, đáp án có thể cần phép suy luận không nằm nguyên văn trong nguồn. MVP AI ưu tiên nhận biết/đọc hiểu học liệu; câu suy luận cần người có chuyên môn hoặc bộ kiểm chứng phép giải độc lập. Không bỏ guard đáp án-trong-quote để nhận output tính toán chưa kiểm chứng.

## Bốn lớp khó và cách kiểm tra

| Lớp | Cơ chế/đường đi tiếp | Việc còn phải làm |
|---|---|---|
| Nguồn sự thật | Version/hash/quote mở được; nguồn đổi phải review lại | Ân + giáo viên kiểm semantic support trên học liệu phổ thông |
| Input mơ hồ | Chủ đề/đối tượng/nguồn bắt buộc, có làm rõ/từ chối | Golden ca thiếu/mâu thuẫn, false abstention |
| Ngoài phạm vi/vượt quyền | ACL ngoài provider, lọc trước retrieval; AI không tự giao bài/đổi điểm | Red-team adapter LLM thật; kiểm egress trước API |
| Sai chuyên môn gây hại | Draft-only, giáo viên duyệt, trace người/nguồn | Kiểm độ phù hợp khối/mục tiêu, đáp án duy nhất, distractor và phép giải |

Hướng dẫn trong UI nêu năng lực/giới hạn, cho sửa/từ chối, mở nguồn và xác nhận trước tác động. Đây là các áp dụng cụ thể từ HAX/PAIR; [memo nguồn](../research/grounded-assessment-ai.md). Lọc chuỗi injection chỉ hỗ trợ, không bảo đảm chặn mọi injection; nguồn được xem là dữ liệu không tin cậy.

## Đánh giá và bằng chứng

`npm run evaluate:rag` chạy **38 ca synthetic trên corpus đào tạo cũ**, development suite đã dùng khi sửa lỗi, không holdout. Kết quả có model status `not_run`, real cases 0. Không trích pass rate này thành độ đúng của đề phổ thông hoặc điểm rubric AI.

Ân chuẩn bị golden phổ thông ≥20 ca có nguồn/nhãn, gồm ca thiếu căn cứ, mơ hồ, sai quyền/injection, đúng chủ đề và sai chuyên môn; tách real/synthetic, dev/holdout. Ghi corpus/prompt/model/policy version, thời gian, chi phí, refusal và lỗi provider. Bar đề xuất trước pilot: 100% chặn lỗi quyền/lộ đáp án critical, ≥90% citation đúng theo giáo viên; báo riêng correctness và false abstention, không hạ bar sau khi xem kết quả chỉ để đạt.

Lý chuẩn bị discovery, ứng viên bị loại, baseline thủ công và assisted trên tác vụ tương đương; đo tổng thời gian đến câu **được chấp nhận**, gồm review/sửa. Lưu bản đã ẩn danh vào [evidence](../../evidence/README.md), bản gốc ở nơi được phép; không bịa quote/impact. [Measurement plan](../data/measurement-plan.md) định nghĩa mẫu số và dữ liệu còn thiếu.

## Non-goals

Chưa chatbot chung, tự xuất bản, tự quyết định điểm/năng lực, OCR/PDF, chấm tự luận, fine-tuning, multi-school hoặc model self-host. Không đưa dữ liệu nhận diện học sinh vào API bên ngoài; chính sách phải được duyệt trước tích hợp theo [gateway dự kiến](../architecture/ai-gateway.md).
