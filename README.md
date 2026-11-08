# VinAssess

Nền tảng kiểm tra và ôn tập cho THCS, THPT. Lát cắt hiện tại: **giáo viên chuẩn bị đề có căn cứ → duyệt/chốt → giao phòng thi → học sinh làm bài → giáo viên chọn nội dung cần ôn từ kết quả**.

Dự án của **EdTech AI Builders L3B**. Mục tiêu đề xuất: 2 tuần MVP, 4 tuần thử với người dùng thật. [Kế hoạch 6 tuần](docs/team/six-week-plan.md) là bản để team duyệt, không phải deadline chính thức của chương trình.

| Hạng mục | Trạng thái thực tế |
|---|---|
| Landing, đăng nhập và workspace theo vai trò | Đã có; giao diện xanh đại dương |
| Đề nháp, phiên bản chốt, phòng thi, làm bài và kết quả theo chủ đề | Đã có, dùng dữ liệu minh họa |
| Nguồn/phiên bản, truy xuất, citation, giáo viên duyệt | Đã có baseline trích xuất tại máy |
| LLM qua API/gateway, đánh giá câu phổ thông bằng chuyên gia | Chưa kết nối/chưa chạy |
| Backend ứng dụng | Python + SQLite; chưa chuyển API sang TiDB |
| Prisma/TiDB | Schema/client và công cụ cấu hình riêng; không tự áp dụng schema |
| Funnel/cohort, pain và impact người dùng thật | Có kế hoạch/biểu mẫu; chưa có số liệu xác minh |

**Demo giao diện:** https://vinas.sunstudy.app/ · [Đăng nhập demo](https://vinas.sunstudy.app/login). Dữ liệu tổng hợp, chưa kết nối LLM. [Cấu hình và vận hành demo](docs/operations/vinassess-demo.md).

## Chạy trong vài phút

Cần **Python ≥3.9 có SQLite FTS5** (khuyến nghị 3.12). Chạy demo không cần cài thư viện Python hoặc cấu hình AI/DB ngoài.

```sh
git clone https://github.com/griin-03/vinuni-ai-assessment-l3.git
cd vinuni-ai-assessment-l3
python3 scripts/serve.py
```

Mở **http://127.0.0.1:4173/login**. Giữ terminal đang chạy; `Ctrl+C` để dừng. Đổi cổng khi cần: `python3 scripts/serve.py --port 4174`. Trên Windows có thể dùng `py -3 -X utf8 scripts/serve.py`.

`ERR_CONNECTION_REFUSED` thường nghĩa là server chưa chạy/đã dừng hoặc trình duyệt đang mở sai cổng. Xem thông báo terminal trước khi tải lại. Nếu máy không có `python3`, cài Python rồi chạy lại.

### Demo luồng chính

1. Chọn **Giáo viên** → **Đề thi của tôi** → **Soạn đề mới**. Thêm câu, đáp án, lời giải và nhãn chủ đề; lưu nháp.
2. **Kiểm tra & chốt** → **Giao vào phòng thi**; chọn học sinh, lịch, thời lượng và thời điểm công bố đáp án.
3. Mở cửa sổ ẩn danh, chọn **Học sinh** → làm bài, thử tải lại để kiểm tra tự lưu → nộp.
4. Quay lại giáo viên → **Phòng thi & kết quả** → xem câu/chủ đề sai và xuất CSV.
5. **Kho tài liệu / Soạn có dẫn chứng** thử đường baseline; mở nguồn và duyệt trước khi lấy câu từ ngân hàng. Nút **Hướng dẫn** giải thích theo màn hình đang dùng.

Demo Toán 9/phương trình bậc hai là nội dung tự soạn; không phải đề chính thức hay kết quả của học sinh thật. Phòng mẫu hết hạn sau 7 ngày kể từ khi tạo; hãy tạo phòng mới nếu cần.

| Tài khoản demo | Vai trò giao diện |
|---|---|
| `training@vinassess.local` | Giáo viên |
| `learner@vinassess.local` | Học sinh |
| `admin@vinassess.local` | Quản trị |
| `manager@vinassess.local` | Quản lý nhóm, tương thích phần nền cũ |

Mật khẩu demo: `VinAssess@2026`. Đây là credential mẫu công khai, chỉ dùng cho dữ liệu demo. [Hướng dẫn người dùng](docs/guide/README.md) · [Báo lỗi/hỗ trợ](docs/guide/support.md).

## Bắt đầu theo vai trò trong team

| Thành viên | Phần chính | Hướng dẫn đủ 6 tuần |
|---|---|---|
| **Ân** | RAG/citation/evaluation, góc nhìn giáo viên Toán; pair triển khai | [Việc và cách làm](docs/team/members/an.md) |
| **Lý** | Discovery, dữ liệu và metric sản phẩm; đề xuất cần Lý xác nhận | [Việc và cách làm](docs/team/members/ly.md) |
| **Tuấn** | AI/ML cùng Ân: adapter, pipeline và công cụ evaluation | [Việc và cách làm](docs/team/members/tuan.md) |
| **Tùng** | Product, Full-stack/System, tích hợp và mọi phần còn lại | [Việc và cách làm](docs/team/members/tung.md) |

Đọc [quy ước đóng góp/nhánh/PR](CONTRIBUTING.md), [team và nguồn background](docs/team/README.md), [mốc nghiệm thu 6 tuần](docs/team/six-week-plan.md), [làm việc theo kênh Discord](docs/team/channels.md). Phân công được **lưu trong repo để duyệt**, chưa đăng lên Discord. Ngày kickoff đề xuất 09/11/2026; điều chỉnh theo lịch thật của team.

Mỗi thành viên push nhánh riêng và mở PR vào `main`; **Tùng review và quyết định merge**. Có [quy trình review chi tiết](docs/team/git-workflow.md), template PR và kiểm tra CI. Không commit thay người khác hoặc ghi việc được giao thành việc đã hoàn thành.

## Phát triển và kiểm tra

Cần **Node ≥22** cho công cụ nội dung/Prisma. Python vẫn là runtime chính.

```sh
npm ci
npm test
npm run evaluate:rag
npm run product:readiness
npm run content
```

- `npm test`: HTTP + SQLite tạm, kiểm quyền, citation/review, đề/phòng/timeout/autosave/chấm điểm. Không dùng database đang chạy.
- `evaluate:rag`: **38 ca tổng hợp cũ trên corpus đào tạo**, kiểm tra cơ chế; không phải điểm chất lượng LLM hay golden phổ thông. Kết quả sinh ở `evaluations/reports/`, không commit.
- `product:readiness`: chỉ ra bằng chứng/mô hình còn thiếu; không chứng nhận đạt Level 3.
- `content`: dựng lại landing từ `vendor/landing-baseline/`, dữ liệu `content/` và theme. Không cần snapshot riêng hay truy cập web gốc. Đọc [thông báo nguồn bên thứ ba](THIRD_PARTY_NOTICES.md) trước khi phát hành.
- Sau khi `git add` đúng các file cần đưa lên, chạy `npm run check:repo`: quét **Git index**, kiểm secret/private data và tài nguyên runtime. Kiểm tra này không thay thế review bảo mật.

[Kết quả xác minh](docs/testing/verification.md) ghi rõ phạm vi, điều đã chạy và giới hạn.

## Cấu hình và dữ liệu

Chạy demo tạo SQLite tại `.vinassess/workspace.sqlite3` (Git bỏ qua, HTTP chặn). Không xóa DB đang có để khắc phục lỗi tùy tiện. Muốn thử dữ liệu mới, dùng `VINASSESS_DB` trỏ đến file khác.

Python đọc biến môi trường của process, **không tự nạp `.env.local`**. `VINASSESS_DEMO=0`, `VINASSESS_ADMIN_EMAIL`, `VINASSESS_ADMIN_PASSWORD` chỉ khởi tạo dữ liệu riêng khi DB mới; không biến demo DB hiện hữu thành DB thật. Mật khẩu quản trị tối thiểu 12 ký tự. Xem [runtime và phân quyền](docs/WORKSPACE.md), [SECURITY](SECURITY.md).

Prisma đọc `.env.local` qua công cụ trong repo. Sao chép `.env.example`, điền thông tin riêng, rồi dùng `npm run db:validate` / `npm run db:generate`. `npm run db:check` kết nối DB chỉ đọc, **chỉ chạy khi bạn đã được cấp quyền và cấu hình đúng**. Không commit `.env.local`, không chạy `db push`/migration trên database dùng chung. [Chi tiết TiDB và kế hoạch chuyển đổi](docs/architecture/tidb.md).

## Tìm mã và tài liệu

| Đường dẫn | Nội dung |
|---|---|
| `workspace/` | ES modules/CSS: đăng nhập, soạn đề, phòng thi, nguồn, review, hướng dẫn |
| `scripts/workspace_*`, `assessment_*`, `education_store.py` | HTTP/auth, SQLite, nghiệp vụ đề/phòng/thi |
| `scripts/rag_*` | Ingestion, FTS5 retrieval, draft worker, guard và bước duyệt |
| `prisma/` | Schema MySQL cho bước tích hợp sau |
| `content/`, `vendor/`, `_mirror/`, `_next/` | Nội dung, baseline landing và tài nguyên giao diện cần chạy |
| `tests/`, `evaluations/`, `evidence/` | Kiểm thử, development suite và mẫu thu bằng chứng thật |
| `docs/team/`, `docs/data/` | Phân công, nhánh/PR, kế hoạch đo lường |

Đọc tiếp: [MVP và non-goals](docs/product/assessment-mvp.md) · [Soạn có dẫn chứng](docs/product/grounded-authoring.md) · [Gateway AI dự kiến](docs/architecture/ai-gateway.md) · [Chọn lọc note workshop](docs/product/workshop-notes.md) · [Kịch bản mở rộng giả định](docs/architecture/scale-scenarios.md).

Chưa có OCR, chấm tự luận, chatbot chung, SSO, event analytics hoàn chỉnh hoặc kiểm thử tải production. Chưa có bằng chứng giảm thời gian/tăng điểm học; phải đo trên người dùng thật. Giữ phạm vi hẹp và đào sâu độ đúng, quyền truy cập, lưu bài, citation và review.
