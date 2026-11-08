# Trần Thị Lý · Product discovery và phân tích dữ liệu

**Cần Lý xác nhận** vai trò và quỹ giờ. Ảnh hồ sơ ghi Data Analysis/Data Engineering/ML; Tùng cung cấp nền tảng tài chính và muốn Lý tập trung Data/metric. Chưa có phần Lý tự giới thiệu đầy đủ trong nội dung được cung cấp. Không mặc định Lý phải tự viết backend hoặc trở thành người ra đề Toán.

**Bắt đầu đọc:** [measurement plan](../../data/measurement-plan.md), `evidence/`, [MVP](../../product/assessment-mvp.md) và demo. Tùng cung cấp event/data hệ thống, Ân/Tuấn cung cấp dữ liệu AI đúng contract; Ân hỗ trợ nội dung chuyên môn.

## LY-W1 · Pain, số đo và dữ liệu nền

- Làm: cùng Tùng tiếp cận giáo viên/người học mục tiêu, ghi hiện trạng và so sánh vài ứng viên pain bằng tần suất/thời gian thực. Tùng chịu trách nhiệm mở kênh tuyển người và hỗ trợ quan sát/phỏng vấn.
- Hướng làm: câu hỏi trung tính, mã người tham gia, nguồn và quyền lưu; không biến lượt thích/ý kiến team thành bằng chứng ngoài nhóm. Tổng bằng chứng cuối kỳ hướng tới rubric ≥20 người ngoài nhóm hoặc mining đủ nguồn, không tự chia đều/quota nếu chưa có nguồn lực.
- Đầu ra: research note đã ẩn danh, impact table, data dictionary + funnel/event/denominator được chốt với Tuấn/Tùng.
- Xong khi: mỗi số có nguồn, phần thiếu ghi thiếu; review Ân về chuyên môn và Tùng về quyết định scope. Task ở `✅・việc-cần-làm`, tài liệu ở `📚・tài-liệu-link`.

## LY-W2 · Kiểm thử đo lường trước pilot

- Làm: quan sát người mới dùng hướng dẫn, kiểm event bằng một phiên đi đúng/sai luồng và lập kế hoạch cohort thử thật.
- Hướng làm: đối chiếu event log với thao tác thực, kiểm trùng/mất, timezone, khoảng thời gian và ID ẩn danh; soạn mẫu feedback/baseline trước khi mời user.
- Đầu ra: notebook/script/bảng phân tích chạy lại được trên dữ liệu synthetic đã gắn nhãn; checklist dữ liệu và kế hoạch pilot có quyền cho phép.
- Xong khi: một người khác chạy được; không trộn mẫu giả với thật; Tùng sửa UX/support theo quan sát. Review Tuấn + Tùng, Ân kiểm nhãn AI.

## LY-W3 · Cohort 1 và funnel đầu tiên

- Làm: ghi số được mời/đồng ý/dùng/hoàn thành/quay lại; phân teacher/student; gom phản hồi và lỗi cản trở.
- Hướng làm: dashboard nhỏ bằng công cụ quen thuộc, lưu query/công thức; báo số người và cỡ mẫu trước tỷ lệ. So sánh với observation/support, không chọn tính năng chỉ vì nhiều click.
- Đầu ra: báo cáo tuần có bảng chất lượng dữ liệu, ba phát hiện ưu tiên tối đa và link bug/task bằng chứng.
- Xong khi: Tùng chọn được một ưu tiên có lý do; Tuấn tái hiện được bug; Ân biết nhóm lỗi câu hỏi cần xem. Review Tùng.

## LY-W4 · Một giả thuyết sản phẩm

- Làm: kiểm tra một điểm rơi trong funnel, chẳng hạn người dùng không hiểu chốt đề hoặc dẫn chứng khó kiểm tra.
- Hướng làm: chốt giả thuyết, metric và cách so sánh trước thay đổi; nếu mẫu nhỏ dùng observation/mô tả và ghi giới hạn, không gọi là A/B chứng minh hiệu quả.
- Đầu ra: phân tích theo cohort/bản release, đề xuất một thay đổi và cách kiểm tra sau release.
- Xong khi: định nghĩa denominator/nhóm so sánh rõ, nhận diện self-selection/small sample; review Tùng + Ân.

## LY-W5 · Đo lặp giá trị và dữ liệu

- Làm: đo thời gian soạn/duyệt, mức giữ/sửa câu, hoàn thành/returning và yêu cầu hỗ trợ; rà completeness của bằng chứng.
- Hướng làm: đối chiếu cùng nhiệm vụ/cỡ đề khi đo trước-sau, báo median/range/cỡ mẫu; nêu thay đổi nguồn/cách chọn user có thể ảnh hưởng kết quả.
- Đầu ra: bảng so sánh tuần/cohort, danh sách thiếu dữ liệu và câu chuyện giá trị có/không được xác nhận.
- Xong khi: số liệu trace được tới nguồn ẩn danh, không suy tăng điểm học từ điểm quiz demo; review Tuấn về data và Ân về ý nghĩa.

## LY-W6 · Báo cáo bốn tuần người dùng thật

- Làm: tổng hợp insight, impact, failure/risk, biểu đồ và bài học cho báo cáo/demo.
- Đầu ra: report 4 tuần, notebook/query tái chạy, evidence ledger sạch, định nghĩa metric và phần đóng góp cá nhân.
- Xong khi: người khác kiểm tra được tử số/mẫu số và phân synthetic/real; báo cả kết quả không đạt, khoảng trống và giới hạn. Review Tùng + Ân.

## Hỗ trợ và portfolio

Tùng lo tuyển user, hạ tầng, hỗ trợ sản phẩm và việc phát sinh; Tùng làm đường event/data hệ thống; Tuấn pair dữ liệu/evaluation AI; Ân kiểm nội dung và nhãn. Có thể bắt đầu bằng CSV/SQL/công cụ phân tích quen thuộc, chưa yêu cầu data platform nặng.

Portfolio dự kiến: discovery có bằng chứng, định nghĩa metric, kiểm tra data quality, funnel/cohort và quyết định sản phẩm từ user thật. Chỉ công bố dữ liệu đã được phép, ẩn danh và thực sự thu được.
