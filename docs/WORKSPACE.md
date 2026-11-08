# Runtime, quyền và không gian làm việc

Định hướng hiện tại: **THCS/THPT**, không còn L&D doanh nghiệp. Thuật ngữ ở [CONTEXT](../CONTEXT.md), phạm vi ở [MVP](product/assessment-mvp.md), hướng dẫn thao tác ở [guide](guide/README.md).

## Vai trò ở máy chủ

| Giá trị lưu trữ | Nhãn sử dụng | Quyền chính |
|---|---|---|
| `learner` | Học sinh | Học/làm bài được giao, kết quả bản thân |
| `training` | Giáo viên | Nguồn được phép, soạn/review; đề/phòng do mình quản lý |
| `manager` | Giáo viên chủ nhiệm/quản lý nhóm | Theo dõi nhóm được giao; tự nó không cấp quyền soạn đề |
| `admin` | Quản trị trường | Tài khoản/cấu hình/nội dung của một trường, nhật ký |

Một tài khoản giữ một vai trò chính. API kiểm quyền và ownership trước dữ liệu/thao tác; sửa menu/URL không mở quyền. `departments` là mô hình nhóm tương thích, chưa phải phân công môn/lớp hoàn chỉnh. Không tự khóa/hạ vai trò bản thân hoặc xóa quản trị hoạt động cuối cùng; đổi role/trạng thái thu hồi phiên đích.

## Backend và trạng thái bài thi

Python stdlib HTTP + SQLite (FTS5); dùng ES modules/CSS phía trình duyệt. `scripts/serve.py` phục vụ workspace, landing và tài nguyên trong `content/landing-assets.json`. Các module `workspace_*` xử lý auth/API/store; `assessment_*` xử lý đề, release, phòng, lượt và worker hết giờ; `education_store.py` thêm demo phổ thông. `rag_*` xử lý nguồn/draft/citation/review, **chưa có LLM**.

Đề nháp có revision; chốt tạo snapshot/hash bất biến. Phòng giữ release, danh sách nhận, lịch, thời lượng, lượt và chính sách công bố; retry tạo phòng bị ràng buộc request key/payload. Lượt thi giữ snapshot riêng, đồng hồ ở máy chủ, autosave có revision, submit idempotent. Worker chấm câu đã lưu khi quá hạn và rà lại khi khởi động. Đóng nhận lượt mới không tự hủy lượt đang làm; hạn riêng của lượt vẫn được giữ.

Payload học sinh dùng allowlist; ghi chú giáo viên/provenance không đi theo câu làm bài. Correct/explanation tuân chính sách công bố; điểm có thể hiện trước lời giải. Kết quả chính dùng lượt nộp gần nhất mỗi học sinh, có cỡ mẫu, không quy chưa nộp thành 0. CSV kiểm tra cùng quyền phòng và tránh công thức ô tính.

Phần khóa học/khảo thí doanh nghiệp cũ vẫn còn để tương thích và có test. Không dùng số học viên/phòng ban mẫu cũ làm số liệu pilot phổ thông.

## Đăng nhập và dữ liệu

Cookie HttpOnly/SameSite=Lax, phiên 8 giờ, lưu token dạng hash; thao tác ghi kiểm Origin/CSRF. Mật khẩu PBKDF2-SHA256 + salt, giới hạn thử đăng nhập. Phân quyền/điểm không tin dữ liệu client.

Mặc định `127.0.0.1:4173`, dữ liệu `.vinassess/workspace.sqlite3`; `.env*`, mã backend, DB, docs, vendor và private directories bị chặn HTTP. File trong Git không mặc nhiên được web server phục vụ. Không sao chép riêng file SQLite chính khi đang có WAL; backup dùng cơ chế SQLite phù hợp và kiểm tra restore trên môi trường riêng.

Để khởi tạo dữ liệu riêng: dùng **DB mới**, đặt biến process `VINASSESS_DEMO=0`, `VINASSESS_ADMIN_EMAIL`, `VINASSESS_ADMIN_PASSWORD` (≥12 ký tự), `VINASSESS_DB`. Không tự đọc `.env.local`. Cờ chỉ áp dụng lúc DB chưa khởi tạo; không làm sạch DB demo cũ. `VINASSESS_COOKIE_SECURE=1` khi đặt sau HTTPS; cần kế hoạch session/backup/secret và kiểm thử trước pilot.

## Kiểm tra và giới hạn

`npm test` chạy HTTP và DB tạm; `npm run evaluate:rag` là 38 ca tổng hợp cơ chế cũ, không phải eval LLM phổ thông. [Báo cáo](testing/verification.md) mô tả kiểm tra thực tế. Hướng [gateway](architecture/ai-gateway.md), [Prisma/TiDB](architecture/tidb.md) và [scale](architecture/scale-scenarios.md) chưa đồng nghĩa runtime đã chuyển đổi/đạt tải.

Chưa SSO/email mời/khôi phục, nhiều trường, OCR/tự luận, chống gian lận bằng camera, event analytics hoàn chỉnh hoặc vận hành production được chứng minh. Không tự thao tác sản phẩm/VPS/bot đang chạy khi đóng góp code; Tùng quản lý release riêng.
