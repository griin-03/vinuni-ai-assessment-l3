# Xác minh bản khởi tạo repo

Ngày 08/11/2026; macOS, Python/SQLite và Chrome headless. Đây là kiểm tra prototype/đóng gói, không phải chứng nhận production hoặc điểm rubric Level 3.

| Kiểm tra | Kết quả và phạm vi |
|---|---|
| HTTP/SQLite integration | **30/30 test pass**: quyền, CSRF/session, source/citation/review, release bất biến, owner/roster/schedule, revision/autosave, submit/timeout, payload học sinh và CSV |
| Development suite RAG | **38/38 ca synthetic pass**, LLM `NOT_RUN`, real cases 0; corpus đào tạo cũ, không phải eval phổ thông/holdout |
| Checkout chỉ từ Git index | Chạy server từ thư mục tạm, không có `.env.local`, `reference/`, `backups/` hay DB riêng của chủ dự án |
| Cài/dựng lại | `npm ci --ignore-scripts`, `npm run content` thành công trong checkout sạch; npm audit báo 0 vulnerability tại thời điểm cài |
| Prisma | Validate và generate 6.19.3 bằng URL placeholder thành công, không kết nối DB thật/không migrate |
| JavaScript | Syntax check 7 workspace modules đạt |
| Chrome end-to-end | Giáo viên soạn/chốt/giao → học sinh chọn đáp án, reload giữ câu, nộp → xem kết quả; không có page error |
| Hướng dẫn | Mở đúng hướng dẫn soạn đề và học sinh làm bài trong trình duyệt |
| Responsive | Màn 390×844: trang soạn/phòng không tràn ngang; landing không còn copy Smart Corporate/doanh nghiệp/nhân sự/L&D trong phần text kiểm tra |
| Git index | 591 file, khoảng 14 MB, guard không phát hiện secret hoặc runtime asset thiếu; đối chiếu riêng token GitHub và mật khẩu DB thật không có trong index |
| Liên kết Markdown nội bộ | Không thấy đích file bị thiếu trong README, CONTRIBUTING và tài liệu đưa lên |
| Tài nguyên/đường dẫn riêng | 448/448 URL tài nguyên trả 200; `.env.local`, `.git`, DB, vendor, workflow và mã backend thử đều trả 404 qua HTTP |

Chưa đánh giá LLM, chưa đo user thật/impact, chưa kiểm tải đồng thời hoặc độ bền production. Luồng pilot cần gate riêng ở [kế hoạch](../team/six-week-plan.md). Audit nghiệp vụ chưa thay analytics pipeline.

## GitHub và quy trình review

Đang xác minh lần push đầu, CI và API bảo vệ nhánh; phần này sẽ ghi trạng thái thực tế sau khi repo có `main`. `.github/CODEOWNERS` chỉ định `@griin-03`; không coi riêng file đó là bảo vệ nhánh đã được cưỡng chế.
