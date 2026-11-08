# Secrets, dữ liệu và báo lỗi

Không commit token GitHub/Discord/AI, SSH key, URL database có mật khẩu, `.env.local`, file SQLite, log thô hoặc dữ liệu nhận diện học sinh. Cấu hình cá nhân dùng `.env.local` và kho bí mật riêng; chỉ chia sẻ `.env.example` đã thay bằng placeholder. Tùng quản lý credential cho staging/production; thành viên dùng dữ liệu giả lập hoặc quyền tối thiểu được cấp riêng.

`npm run check:repo` kiểm tra **Git index** sau `git add`: credential phổ biến, thư mục riêng, database, file lớn và asset runtime bị thiếu. Công cụ không in giá trị phát hiện. Đây là guard hẹp; người review vẫn phải xem staged diff và trạng thái GitHub secret scanning nếu có.

Nếu lỡ lộ credential: báo riêng Tùng, thu hồi/đổi credential ngay, bỏ khỏi commit/history phù hợp. Xóa một dòng ở commit sau không làm credential cũ an toàn trở lại. Không dán token hay screenshot có key vào issue/Discord/PR.

Khi báo lỗi: mô tả phiên bản, bước tái hiện, mong đợi/thực tế và request ID. Gửi dữ liệu giả lập đủ tái hiện; bỏ tên/email, mật khẩu, câu trả lời học sinh và nội dung tài liệu riêng. Lỗi quyền truy cập hoặc mất bài làm là ưu tiên cao và báo riêng người phụ trách trước khi mở rộng pilot.

Thu thập dữ liệu từ người dùng thật theo [kế hoạch đo lường](docs/data/measurement-plan.md). Không đặt nguyên văn phỏng vấn hoặc log nhận diện vào repo, kể cả private. Nguồn thật lưu ngoài Git với quyền phù hợp; repo chỉ chứa dữ liệu đã ẩn danh và được phép chia sẻ.
