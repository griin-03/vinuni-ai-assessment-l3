# Lê Thanh Tùng · Product lead, Full-stack, System và phần còn lại

Theo yêu cầu của Tùng: giao đúng thế mạnh/mong muốn của từng người; **Tùng chịu trách nhiệm phần chưa phân, phát sinh và vượt phạm vi người khác**. Điều này gồm tích hợp, UX, bảo mật, hạ tầng, hỗ trợ user và quyết định giảm scope khi cần.

## TUNG-W1 · Chốt bài toán, nguồn lực và đường găng

- Cùng Lý/Ân chọn pain, chuyên đề và user; tách thông tin đã kiểm chứng/giả thuyết. Xin tên GitHub để cấp collaborator, chốt quỹ giờ/kênh làm việc sau khi team đọc kế hoạch.
- Chuẩn bị môi trường dev/staging riêng, cách giữ secret và demo; xác định API model, ngân sách, dữ liệu được phép gửi. Không gọi API bằng key đặt trong frontend hoặc dùng key chung truyền trong Discord.
- Ghép code hiện có, hướng dẫn Tuấn PR AI đầu; nhận Backend nghiệp vụ và event hệ thống; pair Ân hiểu runtime/provider; hỗ trợ Lý nhận dữ liệu synthetic.
- Đầu ra: backlog có owner/reviewer, product spec, API/gateway quyết định, kiến trúc hiện tại và giả định scale. Xong khi mỗi người biết bước đầu/cách chạy, blocker có người nhận; cả team review.

## TUNG-W2 · Ghép MVP và phát hành cách ly

- Hoàn thiện Web/UX, hướng dẫn theo ngữ cảnh, auth/session/nguồn, API AI, queue/error và data instrumentation. Tùng nhận các phần tích hợp chưa có owner.
- Pair Ân/Tuấn module AI và triển khai, cho Lý kiểm task completion/event; fix blocker và chuẩn bị backup/rollback/support.
- Đầu ra: staging/release MVP, smoke/load-test theo mục tiêu được chốt, gate cuối tuần 2 có bằng chứng; chưa đạt mục nào phải nói rõ. Xong khi đủ điều kiện thử có kiểm soát, chưa gọi là production cho mọi quy mô.

## TUNG-W3 · Mời người dùng và vận hành pilot

- Mời user từ kênh cộng đồng theo quy trình được phép; không tự coi toàn bộ cộng đồng là user VinAssess. Cung cấp hướng dẫn, giải thích giới hạn và nhận hỗ trợ.
- Theo dõi lỗi quan trọng, triage với Lý, nhận sửa Backend/release, pair Ân/Tuấn khi lỗi đường AI; nhận mọi sự cố vận hành và bảo mật.
- Đầu ra: cohort 1, nhật ký release/support đã ẩn danh, một bản sửa ưu tiên. Xong khi có dữ liệu sử dụng thật theo định nghĩa và không để lỗi critical mở rộng pilot.

## TUNG-W4 · Tối ưu luồng có bằng chứng

- Chọn thay đổi từ report của Lý và lỗi AI của Ân/Tuấn, không mở scope theo ý thích. Sửa onboarding/menu/hướng dẫn/luồng core; nhận regression core, phối hợp Ân/Tuấn regression AI.
- Rà tải, quota API, policy nguồn và đường backup; không dùng server sản phẩm cũ làm nơi thử tải.
- Đầu ra: release cải thiện + trước/sau/giới hạn; reviewer phù hợp kiểm luồng và dữ liệu.

## TUNG-W5 · Ổn định, phục hồi và khóa scope

- Tối ưu phần nghẽn đã đo, pair restore/rollback staging, rà secret và quyền; quyết định có cần thay data layer hay chỉ sửa query/transaction.
- Chốt candidate, runbook, UX/support và outline slide/demo; giữ ai cũng có phần giải thích được trong portfolio.
- Đầu ra: checklist vận hành, rehearsal phục hồi, release candidate và phân công bàn giao. Xong khi có kế hoạch lùi bản và không chặn bốn tuần đo chỉ vì đổi stack.

## TUNG-W6 · Bàn giao và nộp bài

- Tag release, chuẩn bị demo/video/slides theo yêu cầu chương trình đã đối chiếu; ghép báo cáo AI và report user 4 tuần, kiểm quote/số liệu/nguồn.
- Ghi rõ phần kế thừa, phần đã làm, giới hạn và đóng góp từng thành viên. Giữ bản báo cáo user đã ẩn danh, không đưa dữ liệu riêng vào repo.
- Đầu ra: bản release có hướng dẫn tái chạy, tài liệu bàn giao, demo và bằng chứng nộp bài khi thực sự đã nộp. Cả team kiểm chéo; chưa có deadline chương trình thì không bịa.

## Nguyên tắc bảo vệ hệ thống có sẵn

Các lần deploy/reload/migration/cấp quyền là việc riêng, không xảy ra chỉ vì PR hoặc GitHub Actions chạy. Không cài self-hosted runner vào VPS đang có sản phẩm. Thiết kế tương lai ở [scale scenarios](../../architecture/scale-scenarios.md) là tài liệu giả định; chỉ quyết định đầu tư khi tải/ngân sách được đo và chốt.

Tùng chịu trách nhiệm tổng thể nhưng nên giảm scope và pair thay vì che blocker hoặc ghi đóng góp thay đồng đội. Kết quả “chưa chứng minh giá trị” vẫn được báo trung thực.
