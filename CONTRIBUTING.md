# Làm việc cùng VinAssess

Đọc [README](README.md), [vai trò team](docs/team/README.md) và [kế hoạch 6 tuần](docs/team/six-week-plan.md) trước khi nhận việc. Mỗi PR gắn một task có owner, reviewer, đầu ra và tiêu chí hoàn thành.

## Luồng một công việc

1. Chọn task trong kế hoạch; ghi nhận tại kênh `✅・việc-cần-làm` khi team đã duyệt. Không coi các bản nháp trong repo là task đã được Discord giao.
2. Tạo branch từ `main`: `feat/<task-id>-ten-ngan`, `fix/<task-id>-ten-ngan`, `docs/<task-id>-ten-ngan`.
3. Làm một lát cắt nhỏ có thể review. Trước khi đổi interface/provider/schema, thống nhất với owner để không làm đứt việc người khác.
4. Chạy kiểm tra phù hợp; xem diff, stage file cụ thể rồi chạy `npm run check:repo`.
5. Push branch, mở PR theo template; ghi cái gì thay đổi, lý do, cách chạy/thử, bằng chứng và giới hạn.
6. Nhờ người hỗ trợ chuyên môn và **Tùng (`@griin-03`) review cuối**. Sửa trên cùng nhánh theo góp ý, chờ Tùng duyệt/merge; không push thẳng main. Xem [quy trình nhánh và review](docs/team/git-workflow.md). Không tự thao tác VPS, database cloud hoặc bot đang chạy.

```sh
git switch main
git pull --ff-only
git switch -c feat/tuan-w1-eval-runner
# Sửa file theo task, rồi:
npm test
git diff
git add tests/ten_file.py docs/ten_file.md
npm run check:repo
git commit -m "test: cover AI provider output contract"
git push -u origin HEAD
```

## Ai sửa vùng nào

| Vùng | Owner chính | Review / hỗ trợ |
|---|---|---|
| `scripts/rag_*`, evaluation AI | Ân + Tuấn cùng AI/ML; chia retrieval/chất lượng và adapter/eval runner | Review chéo; Tùng duyệt cuối và tích hợp |
| Core đề/phòng/lượt thi, event hệ thống và kiểm thử | Tùng | Ân/Tuấn kiểm interface AI, Lý kiểm dữ liệu |
| `docs/data/`, bằng chứng, phân tích metric | Lý — chờ xác nhận phần việc | Ân/Tuấn hỗ trợ dữ liệu AI; Tùng triển khai event |
| `workspace/`, landing, hệ thống, bảo mật, phát hành | Tùng | Một thành viên kiểm tra lại luồng theo task |
| Việc phát sinh/chưa phân/cross-module | Tùng | Nhờ đồng đội hỗ trợ theo thế mạnh, không tự đổi owner |

Tuấn quen .NET nhưng MVP hiện dùng Python/JS. Chưa thêm microservice .NET hoặc đổi stack chỉ để phân việc; task đầu có hướng dẫn chạy, fixture và buổi pair. Ân vẫn có phần thực hành triển khai với Tùng. Lý tập trung Data/metric; chưa mặc định phải làm giáo viên Toán hoặc viết backend.

## Quy ước và kiểm tra

- Frontend ES modules, dùng `esc` cho văn bản không tin cậy. Không thêm framework hoặc thiết kế lại landing ngoài task.
- Backend kiểm tra quyền tại máy chủ; không tin điểm/role/reviewer từ trình duyệt. Không đưa correct/explanation/provenance/ghi chú giáo viên vào payload làm bài trước chính sách công bố.
- Schema SQLite và Prisma hiện là hai trạng thái khác nhau: runtime dùng SQLite, Prisma là cấu hình/target schema chưa cutover. Mọi migration phải có backup/test dữ liệu; không `db push` lên `sys`.
- Provider baseline cục bộ không được ghi nhãn LLM. Kết quả test phần mềm, kết quả AI và bằng chứng người dùng phải báo riêng.
- Test cho logic quan trọng: dùng fixture/database tạm; không viết test chỉ lặp lại triển khai. Chỉnh tài liệu/nhãn đơn giản chỉ cần kiểm tra liên kết/nội dung phù hợp.
- Dữ liệu/phỏng vấn mới phải ghi nguồn và quyền sử dụng. Không bịa quote, người tham gia, số active, impact hoặc tỷ lệ chất lượng.

```sh
npm test
npm run evaluate:rag
npm run content
npm run check:repo
```

CI chạy trên GitHub-hosted Ubuntu, không dùng self-hosted runner hoặc credential VPS. Thay đổi nhỏ chỉ cần chạy phần kiểm tra liên quan; CI sẽ kiểm tra nhánh được push/PR.

## Khi chưa biết bắt đầu

Chạy demo vai trò Giáo viên và Học sinh, đọc đầu việc tuần 1 của mình, mở một PR nhỏ đầu tiên và nhờ pair. Gặp blocker thì cập nhật trong thread: đã thử gì → lỗi nào → cần ai hỗ trợ. Không cần tự gánh phần ngoài thế mạnh; Tùng chịu trách nhiệm phần còn lại theo phân công.
