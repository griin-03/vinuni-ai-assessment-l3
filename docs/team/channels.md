# Công việc theo đúng kênh Discord

Đã đối chiếu tên/ID kênh live ngày 08/11/2026. **Đây là bản tổ chức công việc trong repo để duyệt; chưa đăng hoặc tạo thread trên Discord.** Không cần tạo thêm kênh cho từng người hay từng công nghệ.

| Kênh hiện có | Dùng cho việc gì | Ai chuẩn bị / cập nhật | Bản nháp |
|---|---|---|---|
| [📌・lịch-deadline](https://discord.com/channels/1568869307109081148/1568871262347075706) | Mốc đã được team chốt, lịch họp, hạn chương trình đã xác minh | Tùng đăng sau khi thống nhất; không dùng ngày đề xuất thành deadline chính thức | [01](discord-drafts/01-lich-deadline.md) |
| [💬・trao-đổi](https://discord.com/channels/1568869307109081148/1568871272606212106) | Xác nhận vai trò/quỹ giờ, cập nhật ngắn, blocker và quyết định | Mỗi người cập nhật phần mình; Tùng tổng hợp | [02](discord-drafts/02-trao-doi.md) |
| [✅・việc-cần-làm](https://discord.com/channels/1568869307109081148/1568871275001155705) | Một task một thread: owner, reviewer, đầu ra, tiêu chí, hạn/trạng thái | Bốn người theo mã AN/LY/TUAN/TUNG-W1…W6; Tùng nhận việc chưa phân | [03](discord-drafts/03-viec-can-lam.md) |
| [🧪・mini-lab](https://discord.com/channels/1568869307109081148/1568871292273164320) | Pair/tự luyện RAG, API, eval, data và staging, có cách chạy/đầu ra | Ân↔Tuấn, Tùng↔Ân/Tuấn, Lý↔Tuấn theo từng tuần | [04](discord-drafts/04-mini-lab.md) |
| [📚・tài-liệu-link](https://discord.com/channels/1568869307109081148/1568871304126537828) | Repo, hướng dẫn chạy, nguồn được phép, data dictionary và report | Tùng giữ mục lục, mỗi owner thêm link và quyền cần có | [05](discord-drafts/05-tai-lieu-link.md) |
| [🚀・dự-án-demo](https://discord.com/channels/1568869307109081148/1568871322119966755) | Thread PR/review, bug, phiên bản demo và kết quả tuần | Tùng release; Ân/Lý/Tuấn góp bằng chứng phần mình | [06](discord-drafts/06-du-an-demo.md) |

Voice: [🎙️・Họp team](https://discord.com/channels/1568869307109081148/1568871314826072115) và [💻・Cùng làm việc](https://discord.com/channels/1568869307109081148/1568871317438992384). Chọn giờ sau khi đối chiếu lịch lớp/lab/office hour/workshop; không yêu cầu camera hoặc báo giờ làm.

## Mẫu task để chủ nhóm copy sau khi duyệt

```text
[Cần làm][TUAN-W2] Adapter mô hình và pipeline AI — Tuấn
Mục tiêu: ...
Đầu ra / link dự kiến: ...
Owner: Tuấn | Pair/review AI: Ân | Duyệt cuối: Tùng
Hạn: ngày/giờ UTC+07 đã chốt, hoặc Chưa chốt
Cách làm: ...
Tiêu chí xong: ...
Trạng thái: Cần làm → Đang làm → Chờ review → Xong
Blocker / cần ai hỗ trợ: ...
PR / kết quả / cách chạy: ...
```

Thread công việc là nơi giữ trạng thái; thread `[Lỗi]` giữ repro và kiểm tra; thread lab giữ bài học. Link qua lại thay vì sao chép nhiều bản trạng thái. Không tag mọi người mặc định; chỉ nhờ đúng reviewer. Chưa có GitHub username của ba thành viên nên không tự gán account hoặc mời collaborator.
