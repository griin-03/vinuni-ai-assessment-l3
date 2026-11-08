# Prisma / TiDB

Prisma Client và CLI ghim `6.19.3`, connector `mysql`. `DATABASE_URL` đọc từ môi trường hoặc `.env.local`, mode 600, bỏ qua Git và bị chặn HTTP. `.env.example` chỉ có placeholder. Không đưa URL có mật khẩu vào frontend, log hay README.

Kết nối dùng `sslaccept=strict`, pool 5, timeout 10 giây theo [hướng dẫn TiDB với Prisma](https://docs.pingcap.com/developer/dev-guide-sample-application-nodejs-prisma/). Schema dùng cách cấu hình Prisma 6; không tự nâng Prisma 7 vì khác cấu hình/adapter.

Đã kiểm tra chỉ đọc tới database `sys`, xác nhận `Ssl_cipher` có giá trị và TLS strict. Không đọc bản ghi học sinh, không tạo/sửa bảng. `sys` là đích người dùng cung cấp; chưa áp dụng target schema lên đó.

```sh
npm run db:validate
npm run db:generate
npm run db:check
```

`db:check` chỉ SELECT thông tin kết nối, SHOW trạng thái TLS và đếm bảng qua information_schema. Lỗi chỉ in mã an toàn, không in URL. Không có db push/migrate chạy ngầm trong npm start/install.

`prisma/schema.prisma` là **target schema lõi khảo thí**: nhóm/tài khoản, câu hỏi, nháp, release, phòng, giao đề, bài làm. Chưa bao gồm toàn bộ học liệu/RAG, audit và tính năng cũ; chưa chuyển các trigger bất biến sang MySQL. Không áp dụng trực tiếp lên database đang dùng trước khi hoàn thiện migration.

**Runtime VinAssess vẫn Python/SQLite** (`.vinassess/workspace.sqlite3` hoặc `VINASSESS_DB`). Kết nối thành công chưa chuyển API hay dữ liệu sang TiDB. Chuyển thật cần database ứng dụng riêng, migration không mất dữ liệu, thay lớp lưu trữ và kiểm thử lại quyền, transaction, concurrency, snapshot, deadline, FTS. Chưa có double-write hoặc tự sao chép dữ liệu học sinh ra cloud.

Override `deepmerge-ts` trong `@prisma/config` lên `8.0.2` xử lý cảnh báo stack exhaustion bản <8. Validate/generate/check được kiểm tra lại sau override.
