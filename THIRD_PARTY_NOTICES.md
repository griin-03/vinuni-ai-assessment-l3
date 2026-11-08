# Nguồn và thành phần bên thứ ba

| Thành phần | Nguồn / ghi nhận |
|---|---|
| Baseline landing và tài nguyên đã tải | Giao diện công khai Fervid, snapshot ngày 02/11/2026. `vendor/landing-baseline/` giữ đầu vào build; `index.html`/`_next` là bản chuyển nội dung VinAssess. Đây là giao diện kế thừa, không nhận là được viết mới hoàn toàn. |
| Luồng đề/phòng thi | Port/thích nghi có chọn lọc từ dự án EduTech AI / CogniAssess do chủ dự án cung cấp. Chi tiết và hash tại `docs/product/edutech-port.json`. |
| Onest | Font Onest, điều kiện theo SIL Open Font License trong `fonts/OFL.txt`. |
| React/Next và thư viện nằm trong bundle landing | Giữ các notice có sẵn trong bundle. Nguồn runtime và package cài qua npm có điều kiện riêng của tác giả. |
| Acorn, Prisma | Phụ thuộc npm được ghi và ghim/khóa trong package files; giữ license của từng package trong phân phối tương ứng. |

Repo này đang private cho team. Chưa cấp một giấy phép chung cho việc tái phân phối toàn bộ mã/tài nguyên bên thứ ba. Trước khi chuyển public hoặc tái phân phối, Tùng cần kiểm tra điều kiện của các tài nguyên kế thừa và thay thế phần chưa có quyền phù hợp. Không gắn MIT cho toàn bộ snapshot chỉ vì một số thư viện dùng MIT.
