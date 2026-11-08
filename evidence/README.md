# Hồ sơ bằng chứng thật

Các CSV hiện chỉ có header. Chưa có người tham gia, phát biểu, impact hay kết quả thử nghiệm nào được ghi nhận. Không đếm số dòng mẫu hoặc tài liệu minh họa thành người dùng thật.

- `pain-ledger.csv`: dùng mã người tham gia được ẩn danh; lưu trích đoạn **nguyên văn**, nguồn truy nguyên, phạm vi cho phép sử dụng, thông tin ngoài nhóm và người kiểm tra. `origin=real` chỉ khi thực sự thu thập, không phải do AI dựng. Không đưa hồ sơ cá nhân hoặc tài liệu bí mật vào repo; giữ bản gốc ở nơi được đơn vị cho phép và chỉ ghi tham chiếu phù hợp.
- `impact-candidates.csv`: ghi số liệu có nguồn cho các ứng viên được chọn và không chọn. `basis_source` tham chiếu bằng chứng thật, không phải nhận xét của nhóm. Công cụ chỉ tính giờ/tháng; không xác minh nguồn thay con người.
- `benchmarks.csv`: `method` là `manual` hoặc `assisted`; ghép bằng `task_id` trên các tác vụ tương đương. Đo thời gian tổng đến câu được chấp nhận, bao gồm review. Không dùng một ví dụ đơn lẻ để suy rộng mức cải thiện.

Rubric người dùng đưa yêu cầu khảo sát ít nhất 20 người ngoài nhóm **hoặc** khai thác dữ liệu thật có dẫn chứng. Không tự kết luận vài bản ghi khai thác tương đương 20 người; trường hợp khai thác cần người đánh giá xem tính đủ và đại diện.
