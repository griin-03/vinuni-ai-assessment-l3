# Đo lường bốn tuần người dùng thật

Owner đề xuất: Lý; Ân/Tuấn cung cấp dữ liệu/evaluation AI; Tùng triển khai event hệ thống, tích hợp, tuyển user và xử lý support; Ân kiểm nhãn chất lượng AI. **Đây là thiết kế cần triển khai/kiểm tra ở tuần 1–2. Runtime hiện có audit nghiệp vụ, chưa có analytics pipeline này.**

## Câu hỏi sản phẩm

1. Giáo viên có chuẩn bị được một đề phù hợp từ học liệu và kiểm tra căn cứ trong thời gian hợp lý không?
2. Bao nhiêu câu được giữ, sửa hoặc từ chối sau đối chiếu; lý do là gì?
3. Học sinh có bắt đầu, lưu và nộp bài được không; bước nào cần hỗ trợ?
4. Giáo viên có dùng phân tích lỗi để chọn nội dung ôn tập không, và quay lại dùng ở lần tiếp theo không?

Lượt bấm từng nút, giờ cao điểm và tính năng được mở giúp chẩn đoán luồng/tải. Chúng không tự chứng minh giá trị, chất lượng học tập hoặc tác động kinh doanh.

## Funnel và công thức

| Metric | Tử số / mẫu số hoặc phép tính | Ghi chú |
|---|---|---|
| Adoption teacher | Giáo viên hoàn tất nhiệm vụ / giáo viên đồng ý thử và có cơ hội dùng | Ghi cả invited, consented, active, task-complete, không trộn tổng thành viên cộng đồng |
| Tạo đề được chốt | Số phiên mục tiêu dẫn tới `paper_released` / phiên tạo đề mục tiêu hợp lệ | Nối session/job/paper, không đếm lại retry; báo cả bị chặn/abstain |
| Thời gian soạn/duyệt | Thời điểm bắt đầu nhiệm vụ đến chốt, báo median/range/cỡ mẫu | Đo cùng chủ đề/cỡ đề; tách thời gian người thao tác, chờ AI và nghỉ nếu có quan sát |
| Giữ/sửa/từ chối câu | Số câu mỗi quyết định / tổng câu đã được review | Mẫu số không phải tổng câu sinh ra; nhiều câu chưa review phải báo riêng |
| Citation đúng | Số câu có citation đúng theo nhãn giáo viên / câu được kiểm | Tách quote/source cơ chế và semantic support; không coi exact match là entailment |
| Hoàn thành làm bài | Số lượt nộp thành công / lượt đã bắt đầu hợp lệ | Tách timeout, lỗi kỹ thuật, bỏ dở; một người có thể nhiều lượt |
| Save error | Số yêu cầu lưu lỗi / tổng yêu cầu lưu trong khoảng quan sát | So request ID và phiên bản; không chỉ đo event frontend có thể mất |
| Quay lại | Người quay lại có hành động mục tiêu / cohort có đủ cửa sổ theo dõi | Định nghĩa 7 ngày/cửa sổ trước phân tích; loại cohort chưa đủ thời gian khỏi denominator |
| Support/bug | Số case theo severity, thời gian xác nhận→sửa, số được mở lại | Ghi version, không dùng số case ít để kết luận ít lỗi khi ít user |

Giờ cao điểm theo **Asia/Ho_Chi_Minh** từ timestamp UTC; báo unique users, sessions, event và request riêng. Không suy số học sinh đồng thời từ tổng người đăng ký. “User active lớn” của nền tảng khác chưa là số liệu VinAssess.

## Event contract đề xuất v1

Trường chung: `event_id`, `schema_version`, `event_name`, `occurred_at_utc`, `received_at_utc`, `actor_pseudonym`, `actor_role`, `session_id`, `request_id`, `release_version`, `environment` và IDs nghiệp vụ cần thiết. Actor/role/received time lấy từ máy chủ; không tin role client gửi. Quyết định nghiệp vụ dùng event server; event frontend chỉ hỗ trợ quan sát UI.

| Event | Phát khi nào | Thuộc tính tối thiểu được phép |
|---|---|---|
| `authoring_task_started` | Bắt đầu nhiệm vụ có mục tiêu, không phải mỗi lần reload | subject/grade dạng danh mục, task/session ID |
| `draft_requested` | Request hợp lệ đã được ghi job | job ID, count, provider mode, source version IDs |
| `draft_completed` | Job hoàn tất có draft | job ID, output count, duration, model/prompt version |
| `draft_abstained` | Thiếu căn cứ/làm rõ/ngoài phạm vi | job ID, decision code, không ghi raw prompt |
| `draft_failed` | Lỗi kỹ thuật sau retry hợp lệ | job/request ID, error code, attempt count |
| `question_reviewed` | Một quyết định review đã commit | item ID, approve/edit/reject, reason code; comment tự do lưu riêng nếu cần |
| `paper_released` | Release đề được ghi thành công | paper/release ID, item count, subject/grade |
| `room_created` | Phòng và danh sách đã commit | room/release ID, assigned count, duration; không log roster tên/email |
| `attempt_started` | Lượt mới được ghi | attempt/room ID; không phát mới khi resume/retry |
| `answer_save_failed` | Một lần lưu thất bại xác định được | request/attempt ID, error code, expected/current revision nếu phù hợp |
| `attempt_submitted` | Chỉ một transition sang đã nộp | attempt/room ID, submitted/timeout reason; không log raw answers |
| `result_viewed` | Người dùng được phép mở kết quả | attempt ID, review-visible boolean |
| `help_opened` | Mở hướng dẫn theo bước | route/task key trong allowlist, role |
| `feedback_recorded` | Đã nhận feedback theo quyền cho phép | pseudonymous case ID, category/rating; nội dung riêng không nằm trong log event |

Tên event là contract **dự kiến**, chưa nhận là đã được phát đầy đủ trong code. `help_opened` cũng chưa được gửi chỉ vì UI có hướng dẫn. Tùng cùng Lý chọn subset tối thiểu cần đo, implement rồi Lý đối chiếu trước pilot; thay đổi phải cập nhật version.

## Chất lượng dữ liệu và quyền

- Dedupe theo event ID và khóa nghiệp vụ của transition; không coi gửi lặp/đa tab là nhiều người hay nhiều lần chốt.
- Check missing ID, sai role, timestamp ngoài cửa sổ, event không theo thứ tự và khác timezone. Reconcile một số phiên với server receipts/log đã lọc.
- Không log tên/email, mật khẩu, token, IP, prompt đầy đủ, đoạn tài liệu, câu trả lời thô hoặc ảnh camera. Thu thêm trường phải có lý do, quyền và thời hạn giữ.
- Dữ liệu học sinh vị thành niên: Tùng/Lý làm theo quy trình được nhà trường/người có thẩm quyền cho phép, thông báo cách sử dụng và hỗ trợ rút dữ liệu. Chưa xác nhận được quyền thì thử bằng dữ liệu giả/lượt quan sát phù hợp, không mở thu thập rộng.
- Raw interview, mapping pseudonym→người và log nhạy cảm nằm ngoài Git, quyền riêng. Repo chỉ có cấu trúc, sample ghi `synthetic`, query và aggregate được phép.

## Báo cáo mỗi tuần 3–6

1. Khoảng thời gian, release, nguồn dữ liệu và cohort; dữ liệu chưa có ghi “chưa có”.
2. Số được mời/đồng ý/dùng/hoàn thành/quay lại; cỡ mẫu teacher/student.
3. Funnel, thời gian nhiệm vụ, review quality và lỗi/support; missing/duplicate checks.
4. Tối đa ba phát hiện có bằng chứng, một thay đổi ưu tiên, tiêu chí kiểm tra sau thay đổi.
5. Giới hạn: small sample, self-selection, người bỏ dở, thay đổi chủ đề/cỡ đề, thời gian theo dõi chưa đủ.

Cuối kỳ dùng `evidence/` để tổng hợp pain/impact/benchmark đã ẩn danh. Chưa khẳng định cải thiện kết quả học tập chỉ dựa vào điểm quiz, click hoặc bốn tuần pilot.
