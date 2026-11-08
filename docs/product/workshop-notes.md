# Chọn lọc note workshop cho VinAssess

Nguồn: note Tùng cung cấp ngày 08/11/2026; đây là quyết định áp dụng của dự án, không phải yêu cầu chính thức của workshop hay chương trình. Cập nhật vào kế hoạch 6 tuần, không thêm tất cả thành tính năng MVP.

| Keyword | Quyết định | Cách áp dụng / owner |
|---|---|---|
| Hướng dẫn, tip, menu hướng dẫn, theo từng key | Áp dụng | Nút Trung tâm hướng dẫn hiện mở đúng ngữ cảnh soạn đề/phòng/nguồn/làm bài. “Key” được hiểu là bước hoặc tác vụ; chưa có yêu cầu phím tắt/keyboard tour. Tùng triển khai, Lý kiểm tra người mới có tự làm được. |
| Tiếp cận sản phẩm đơn giản | Áp dụng vào MVP | Một đường chính có thể hoàn thành; giải thích ngay lúc chọn nguồn/chốt đề/giao phòng. Tùng + Lý đo task completion và thời gian cần hỗ trợ. |
| Customer support | Áp dụng gọn | Hướng dẫn báo lỗi đã bỏ dữ liệu riêng; Tùng là đầu mối, Lý gom phản hồi đã ẩn danh. Bug tái hiện/test ở kênh Dự án/demo sau khi team duyệt cách làm. Chưa có hệ thống ticket ngoài hoặc hỗ trợ 24/7. |
| AI hỗ trợ | Giữ trong lát cắt chính | Ân làm gợi ý câu có nguồn/refusal; giáo viên đối chiếu. Chưa mở chatbot tổng quát, tự sửa điểm hay tự phát hành. Runtime hiện vẫn là baseline, adapter LLM nằm trong công việc tuần 1–2. |
| Huấn luyện | Chưa fine-tune | Ưu tiên nguồn, prompt/version, retrieval và eval có nhãn; ghi lỗi để quyết định sau. Không dùng dữ liệu học sinh để huấn luyện mặc định. |
| Khớp chủ đề | Áp dụng làm rubric | Mỗi câu có mục tiêu/chủ đề, độ phù hợp lứa tuổi và nguồn; Ân kiểm tra chuyên môn, Lý tổng hợp tỷ lệ giữ/sửa/từ chối. Nhãn chủ đề trong UI đã có, kiểm định ngữ nghĩa mới là việc tiếp theo. |
| Luận điểm, luận cứ | Áp dụng vào kiểm chứng | Tách điều câu hỏi/đáp án khẳng định, đoạn nguồn hỗ trợ và bước suy luận. Quote tồn tại không bảo đảm kết luận đúng. Bài tính toán cần kiểm chứng phép giải riêng; MVP AI ưu tiên câu đọc hiểu/nhận biết nguồn trước. |
| GitBook | Để sau | Dùng README + docs có version trước. Nếu user thật cần tài liệu công khai, Tùng/Lý chọn phần đã bỏ dữ liệu riêng để xuất sang GitBook; chưa tạo site hoặc tài khoản mới. |
| “Mình đưa ra kiến trúc” | Áp dụng | Tùng ghi kiến trúc thực tế, quyết định, rủi ro và hướng mở rộng; Ân/Tuấn hiểu interface của phần mình, không cần cùng đổi toàn bộ stack. |
| “1 triệu người dùng” | Bài tập thiết kế, chưa phải cam kết tải | Có kịch bản giả định và công thức tải ở [tài liệu kiến trúc](../architecture/scale-scenarios.md). Không ghi MVP/VPS hiện chịu được một triệu người. |

## Checklist khi review một câu có dẫn chứng

1. Câu này đánh giá mục tiêu kiến thức nào, có thuộc chủ đề đã chọn không?
2. Câu/đáp án đang khẳng định điều gì; nguồn nào hỗ trợ, phiên bản và đoạn nào?
3. Có bước suy luận/tính toán vượt đoạn trích không? Nếu có, ai/công cụ nào kiểm tra độc lập?
4. Có đúng một lựa chọn đúng và phương án nhiễu hợp lý với học sinh mục tiêu không?
5. Nếu nguồn mâu thuẫn/thiếu, hệ thống có dừng hoặc hỏi lại thay vì tự bù không?

Các tiêu chí này là hướng review của giáo viên và việc đánh giá của Ân, không giả vờ đã có một bộ chấm AI ngữ nghĩa hoàn chỉnh trong code.
