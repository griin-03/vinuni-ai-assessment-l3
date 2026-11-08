# Demo giao diện trên VPS

Cập nhật 08/11/2026, UTC+07. URL: **https://vinas.sunstudy.app/**; đăng nhập: **https://vinas.sunstudy.app/login**. Đây là môi trường demo với dữ liệu tổng hợp, chưa phải pilot dùng dữ liệu học sinh thật hoặc LLM đã kết nối.

## Phạm vi triển khai

- VPS ARM 24 GB do Tùng chỉ định; DNS đi qua Cloudflare. Đường ACME đã xác minh tới đúng origin. Không đổi DNS/cấu hình của tên miền khác.
- Service `vinassess-demo.service`, tài khoản hệ thống `vinassess`, chỉ nghe `127.0.0.1:4175`; Nginx proxy riêng cho `vinas.sunstudy.app`.
- Code bất biến theo release trong `/opt/vinassess/releases/`, symlink `/opt/vinassess/current`; DB demo riêng tại `/var/lib/vinassess/demo.sqlite3`.
- Không chuyển `.env.local`, GitHub/Discord/API key, database máy cá nhân, tài liệu team hoặc kết nối TiDB lên runtime. Gói chỉ chứa mã/tài nguyên cần chạy; không clone repo bằng PAT trên VPS.
- Systemd tự khởi động khi reboot, restart khi lỗi, user không có shell đăng nhập, filesystem readonly ngoài state/tmp, giới hạn RAM 512 MiB và CPU tương đương một core. Không coi giới hạn này là kết quả benchmark tải.
- HTTPS Let's Encrypt riêng, auto-renew bằng lịch Certbot hiện có và hook chỉ reload Nginx khi đúng lineage VinAssess. Chứng chỉ cấp lần đầu hết hạn 06/02/2027. Cookie session có Secure; demo có `noindex` và `Cache-Control: no-store`.

## Chạy lại/build

```sh
npm ci --ignore-scripts
VINASSESS_SITE_URL=https://vinas.sunstudy.app npm run content
```

`VINASSESS_SITE_URL` chỉ dùng khi build canonical/metadata/link landing, mặc định vẫn localhost cho dev. Phải build trước khi đóng gói; không chỉnh chuỗi trực tiếp trên bundle đang phục vụ.

Các file mẫu tại `deploy/`: unit, bootstrap HTTP vhost, HTTPS vhost và hook renew. Không có script tự ghi đè hệ thống từ CI. Đợt triển khai đầu dùng base commit `bb1cf8d` cùng thay đổi cấu hình URL build trong nhánh triển khai; package được đối chiếu SHA256 trước giải nén. Ghi nguồn/commit và checksum gói cho mỗi lần phát hành mới.

## Kiểm tra vận hành

Các lệnh dưới đây do Tùng chạy trên VPS, không phải quyền mặc định của thành viên.

```sh
sudo systemctl status vinassess-demo --no-pager
sudo journalctl -u vinassess-demo -n 80 --no-pager
curl -H 'Host: vinas.sunstudy.app' http://127.0.0.1:4175/login
sudo nginx -t
```

Nếu kiểm tra public bằng công cụ, Cloudflare có thể chặn một số user-agent/IP; xác minh bằng trình duyệt và so sánh origin trước khi kết luận app hỏng. Không tắt bảo vệ toàn zone để sửa lỗi demo. Header Host phải giữ domain khi proxy vì API kiểm Origin/CSRF.

## Cập nhật, lùi bản và dữ liệu

1. Làm nhánh/PR, Tùng duyệt; build và kiểm gói không secret ở máy phát triển/runner cách ly. Không build chung repo sản phẩm khác.
2. Backup DB bằng SQLite backup API; giữ bản ngoài public webroot, quyền chỉ user vận hành. Không sao chép riêng file SQLite chính khi WAL đang hoạt động.
3. Upload release mới vào thư mục riêng, kiểm checksum và dependency; không mang thư mục dữ liệu demo theo code.
4. Chuyển symlink `current`, restart **chỉ** `vinassess-demo`; kiểm landing/login/source/thi và log. Nếu có migration, phải thử trên bản sao và có phương án lùi dữ liệu trước khi chuyển.
5. Khi lỗi, trỏ về release trước và restart VinAssess; restore backup chỉ theo kế hoạch đã kiểm tra. Không đổi symlink ngược tùy tiện sau migration không tương thích.

Không restart StudyStream, SunStudy, CogniAssess, MariaDB hoặc bot vì cập nhật VinAssess. Chỉ cần graceful reload Nginx khi thay đúng vhost/cert VinAssess và sau `nginx -t`; không sửa default/server block của web khác. [Tài liệu Nginx](https://nginx.org/en/docs/control.html) · [Certbot webroot/renew](https://eff-certbot.readthedocs.io/en/stable/using.html).

Tắt demo bằng `sudo systemctl stop vinassess-demo`; không xóa DB hoặc service khác. Muốn ngừng public route phải xử lý riêng đúng vhost VinAssess, test rồi reload Nginx. Việc reset tài khoản/dữ liệu demo cần Tùng quyết định trước vì mọi người dùng chung dữ liệu mẫu.

## Trạng thái kiểm tra lần đầu

- Service hoạt động với user riêng; thử đăng nhập teacher trả 200, cookie Secure; runtime khoảng 17 MiB RAM lúc kiểm tra ban đầu.
- `/README.md`, `.env.local`, `.git/config`, tài liệu team và mã backend thử đều trả 404 qua app.
- Ứng dụng/DB cũ và Nginx master giữ PID/start time; hash các cấu hình cũ không đổi. Chỉ thêm vhost VinAssess, reload Nginx; status endpoint cũ giữ như baseline (một số trả 403 theo host/IP có sẵn, không nhận là mọi endpoint đều 200).
- Public HTTPS trả 200 cho landing, login, workspace shell và logo. Chrome qua domain đã chạy tạo/chốt/giao đề, học sinh autosave, reload giữ đáp án, nộp và xem điểm; hướng dẫn đúng ngữ cảnh, không có page error. Hai màn soạn/phòng ở 390×844 không tràn ngang. Dữ liệu QA được gắn nhãn demo. Không dùng smoke test thay eval mô hình hoặc đo user thật.
