# Chỗ nối mô hình và gateway được phê duyệt

## Quyết định hiện tại

Runtime chỉ có `ExtractiveBaseline`; không có HTTP client, endpoint, API key hay cơ chế fallback ra ngoài trong bộ soạn. `rag_worker` gọi interface `generate(request, sources)` sau khi đóng connection truy xuất và trước transaction lưu kết quả. Việc thay adapter sau này không được bỏ qua cổng quyền, kiểm tra dẫn chứng hoặc bước duyệt.

## Khi chủ sở hữu học liệu và đơn vị thử nghiệm cho phép API qua gateway

Gateway tập trung kết nối, quyền, chính sách và quan sát; mô hình backend vẫn xử lý payload được chuyển tiếp. Hạ tầng nội bộ của gateway không đồng nghĩa backend cũng ở nội bộ. [Microsoft AI Gateway concepts](https://learn.microsoft.com/en-us/azure/ai-gateway/concepts)

Thiết kế tương lai cần tách **phạm vi người đọc** khỏi **quyền xuất dữ liệu ra mô hình**. Nhãn lớp/nhóm (lưu trữ tương thích là phòng ban) chỉ là ACL, không phải phê duyệt gửi bên ngoài. Không gửi hồ sơ/đáp án có nhận diện học sinh; với trẻ vị thành niên cần quy trình cho phép của đơn vị thử nghiệm trước khi thu thập. OWASP khuyến nghị kiểm soát quyền ở retrieval/integration thay vì giao phán đoán bí mật cho mô hình. [OWASP Sensitive Data Exposure](https://genai.owasp.org/glossary/sensitive-data-exposure/)

Interface triển khai gateway phải bổ sung một cổng egress trước `generate`:

1. Xác nhận loại dữ liệu, mục đích, chủ sở hữu và chính sách cho phép xử lý.
2. Chặn mặc định tài liệu chưa phân loại/nhạy cảm; chỉ cho endpoint và model alias trong allowlist quản trị. Người dùng không được nhập URL tùy ý.
3. Lọc PII/bí mật theo chính sách có kiểm thử; chỉ gửi các đoạn cần thiết. Nếu redaction làm mất căn cứ cần thiết, từ chối thay vì âm thầm gửi bản gốc.
4. Dùng danh tính ứng dụng/secret phía máy chủ; giới hạn token, thời gian, số lượt và ngân sách. Không giữ transaction DB trong lúc gọi mô hình.
5. Thỏa thuận lưu giữ, vùng xử lý, dùng dữ liệu cho huấn luyện, bên xử lý phụ và xóa dữ liệu phải được người có thẩm quyền xem xét theo nhà cung cấp cụ thể. Không suy luận các điều khoản này từ việc có gateway.
6. Log mặc định chỉ metadata cần thiết: request ID, policy version, định danh/hash nguồn, model, token, thời gian, trạng thái. Không ghi nguyên prompt/tài liệu/khóa vào log quan sát.
7. Output là dữ liệu không tin cậy: schema, nguồn, quote và quyền kiểm tra lại; không cấp tool để mô hình tự ghi ngân hàng/giao bài. Người dùng vẫn duyệt riêng.
8. Khi gateway không khả dụng hoặc từ chối, báo lỗi/không chạy. Không tự chuyển sang dịch vụ công khai khác.

Đây là hợp đồng thiết kế cho giai đoạn sau, **chưa phải gateway đã được xây hoặc chính sách egress đã được kiểm thử**. Provider hiện tại không tạo lưu lượng ra ngoài. Việc có phù hợp quy định của đơn vị/pháp luật hay không cần xem trên dữ liệu, thỏa thuận và cấu hình thực tế. Tùng chốt nhà cung cấp/chính sách/ngân sách; Ân/Tuấn cùng AI/ML: Ân nguồn/prompt/citation, Tuấn adapter/eval/error handling; Tùng tích hợp.
