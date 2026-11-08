# Lộ trình 6 tuần · MVP trước, đo thật sau

**Đề xuất để duyệt**: 09/11–20/12/2026, UTC+07. Nếu ngày kickoff thay đổi thì dời cả lịch; deadline chính thức của AI20K/VinUni phải đối chiếu cổng chương trình, chưa được lấy từ kế hoạch này.

Mục tiêu hẹp: **giáo viên chọn học liệu được phép → tạo và duyệt một đề ngắn có dẫn chứng → giao một phòng thi → học sinh làm bài → giáo viên chọn nội dung cần ôn từ kết quả**. AI chỉ quyết định đề xuất câu có đủ căn cứ hoặc yêu cầu bổ sung; giáo viên chốt nội dung và chịu trách nhiệm sử dụng.

## Phạm vi để kịp tuần 2

- Một chuyên đề Toán, một nhóm lớp; bắt đầu từ demo Toán 9/phương trình bậc hai đang có, Ân cùng giáo viên pilot xác nhận độ phù hợp trong tuần 1. Chưa mặc định đây là nội dung học sinh thực sự cần.
- MCQ bốn lựa chọn/một đáp án, có source version/quote và giáo viên duyệt. Tự luận, OCR, chatbot chung, camera, xếp hạng và model self-host không nằm trong cam kết MVP hai tuần.
- Có một đường LLM qua API/gateway được duyệt trước pilot AI; không gọi baseline trích xuất là LLM. Tùng chịu trách nhiệm chọn nhà cung cấp, ngân sách, credential và chính sách dữ liệu; Ân/Tuấn cùng AI/ML, chia retrieval/chất lượng và adapter/eval runner.
- Backend nghiệp vụ/event do Tùng phụ trách; Ân và Tuấn cùng AI/ML, không giao Tuấn làm owner Backend. Có thể tiếp tục dùng SQLite cho pilot nhỏ nếu kiểm tra tải/an toàn đạt. Không thêm cuộc đổi stack bắt buộc .NET/Prisma/TiDB vào đường găng. Nếu cutover dữ liệu cần thiết, Tùng chủ trì sau thử nghiệm, giữ kế hoạch rollback và kiểm thử.
- Log theo contract và quyền cho phép; ưu tiên event tối thiểu và dữ liệu ẩn danh. Không gửi hồ sơ/đáp án nhận diện học sinh ra API AI.

## Lịch và đầu ra chính từng người

| Tuần | Thời gian đề xuất | Ân · AI/ML | Lý · Product/Data | Tuấn · AI/ML cùng Ân | Tùng · Full-stack/System & phần còn lại |
|---|---|---|---|---|---|
| **1** | 09–15/11 | **AN-W1**: nguồn/chunk/retrieval + golden ≥20 ca có nhãn; chốt output contract | **LY-W1**: discovery, impact candidates, funnel/event dictionary, baseline đo | **TUAN-W1**: trace RAG, provider contract và PR eval runner; pair Ân | **TUNG-W1**: scope/user, quyền repo, gateway/nguồn lực, Backend/core/event contract |
| **2** | 16–22/11 | **AN-W2**: prompt/retrieval/citation và eval cùng adapter của Tuấn; pair staging | **LY-W2**: kiểm event/denominator, kế hoạch pilot/consent, bảng baseline; test usability | **TUAN-W2**: adapter mô hình/pipeline AI và kiểm lỗi; cùng Ân chạy eval | **TUNG-W2**: Backend/event hệ thống, ghép luồng AI, staging/MVP, backup/rollback/go-no-go |
| **3** | 23–29/11 | **AN-W3**: phân tích lỗi AI từ pilot, sửa một nhóm lỗi có benchmark trước/sau | **LY-W3**: tiếp nhận cohort 1, funnel/retention đầu tiên, phỏng vấn và đề xuất ưu tiên | **TUAN-W3**: tái hiện lỗi AI, fixture/regression và một sửa pipeline cùng Ân | **TUNG-W3**: mở pilot có kiểm soát, hỗ trợ người dùng, triage và phát hành bản sửa |
| **4** | 30/11–06/12 | **AN-W4**: cải thiện retrieval/prompt trên case thật đã ẩn danh, regression + holdout | **LY-W4**: phân đoạn teacher/student, kiểm tra một giả thuyết cản trở, báo cáo quyết định | **TUAN-W4**: harness so sánh một cấu hình AI, quality/abstention/latency cùng Ân | **TUNG-W4**: sửa UX/luồng ưu tiên từ dữ liệu, cập nhật policy/giới hạn tải, release ổn định |
| **5** | 07–13/12 | **AN-W5**: eval chất lượng, chi phí/độ trễ, lỗi còn lại; khóa cấu hình ứng viên | **LY-W5**: so sánh cohort/tuần, thời gian làm việc trước/sau, kiểm bias và số người thực | **TUAN-W5**: độ tin cậy adapter, provider error/quota/cost và runbook AI | **TUNG-W5**: tối ưu phần nghẽn đã đo, rehearsal backup/rollback, khóa phạm vi và chuẩn bị bàn giao |
| **6** | 14–20/12 | **AN-W6**: báo cáo AI tái chạy, risk/abstention cases, demo module và đóng góp cá nhân | **LY-W6**: báo cáo 4 tuần user thật, evidence/impact/giới hạn, biểu đồ và câu chuyện sản phẩm | **TUAN-W6**: eval đã khóa cùng Ân, demo failure/success và bàn giao module AI | **TUNG-W6**: tag release, demo trọn luồng, runbook, slide/video/nộp bài và ghi nhận đóng góp |

Chi tiết cách làm, artifact, người review và tiêu chí xong ở trang của [Ân](members/an.md), [Lý](members/ly.md), [Tuấn](members/tuan.md), [Tùng](members/tung.md). Mỗi mã tương ứng một thread `✅・việc-cần-làm` sau khi team duyệt; lab/code/bug có thread ở đúng kênh liên quan.

## Đường găng và bàn giao

| Mốc | Giao → nhận | Cần có |
|---|---|---|
| Đầu tuần 1 | Lý + Ân → Tùng/Tuấn | Tệp người dùng và một chuyên đề đề xuất; nguồn được phép, pain còn là giả thuyết cho tới khi có bằng chứng |
| Giữa tuần 1 | Ân + Tuấn → Tùng | Ví dụ input/output, schema, trạng thái draft/refusal/error; nguồn/chunk IDs và cách tái chạy |
| Cuối tuần 1 | Lý → Tùng; Ân/Tuấn kiểm phần AI | Event dictionary, metric/denominator và cách ẩn danh; Tùng chốt đường LLM/ngân sách |
| Giữa tuần 2 | Ân + Tuấn + Tùng → Lý | Luồng end-to-end ở staging, event mẫu, lỗi có request ID, tài liệu chạy |
| Cuối tuần 2 | Cả team → Tùng quyết định release | Go/no-go bên dưới. Ân/Lý được quyền ghi rõ chất lượng hoặc dữ liệu chưa đủ |
| Tuần 3–6 | User thật → Lý/Ân/Tuấn → Tùng | Báo cáo → bug/cơ hội có bằng chứng → một thay đổi ưu tiên → kiểm tra và release |

Nếu thiếu key/model/ngân sách hoặc quyền dùng tài liệu, Tùng giải quyết blocker. Không lặng lẽ dùng dữ liệu riêng hoặc đổi nhãn baseline thành AI để kịp demo. Nếu chưa đạt điều kiện AI, demo luồng thủ công/baseline với nhãn đúng, giữ status gate chưa đạt và điều chỉnh cam kết pilot với nhóm.

## Gate cuối tuần 2: sản phẩm có thể thử có kiểm soát

Tùng ghi PASS/FAIL và link bằng chứng; không coi checklist trống là hoàn thành.

- [ ] Một giáo viên mới có thể chạy đúng luồng với hướng dẫn; thử trên thiết bị mục tiêu và một học sinh test.
- [ ] Câu AI có quote/source version; giáo viên mở được nguồn, sửa/từ chối/duyệt; thiếu căn cứ được chặn/abstain.
- [ ] Có kết quả **LLM thật** trên golden ≥20 ca gồm thiếu nguồn, mơ hồ, sai quyền, injection và case chuyên môn. Tách số ca synthetic/real và dev/holdout. Kết quả cơ chế cũ không thay thế gate này.
- [ ] Quality bar đề xuất trước pilot: 100% chặn các lỗi quyền/lộ đáp án critical; ≥90% citation đúng **theo giáo viên kiểm tra** trên tập đã ghi nhãn; ghi riêng câu đúng ngữ nghĩa, tính hợp lý phương án nhiễu và tỷ lệ abstain. Team chốt bar trước khi chạy, không hạ bar chỉ để đạt.
- [ ] Start/resume/autosave/submit/timeout và idempotency/revision hoạt động; không có bug mất bài hoặc truy cập sai quyền chưa xử lý.
- [ ] Event trọng yếu đủ/không trùng trên phiên kiểm tra có đối chiếu; dữ liệu nhận diện và quyền thu thập được xử lý trước pilot.
- [ ] Có backup/rollback, đầu mối hỗ trợ và phiên bản release; thử tải cách ly theo mục tiêu số em đồng thời do Tùng chốt, không suy số em từ RAM VPS.

## Bốn tuần đo với người dùng thật

**Tuần 3** mở nhóm nhỏ được phép, quan sát và sửa lỗi cản trở. **Tuần 4** mở thêm chỉ khi gate an toàn/ổn định đạt và kiểm tra một giả thuyết. **Tuần 5** đo lặp, tối ưu phần đã có bằng chứng; không thêm tính năng để làm biểu đồ đẹp. **Tuần 6** khóa bản báo cáo, tổng hợp kết quả/giới hạn và bàn giao.

Tùng có kênh cộng đồng để mời người dùng nhưng **chưa có số active, conversion hay retention được xác minh cho VinAssess**. Lý ghi số được mời → đồng ý tham gia → dùng thật → hoàn thành → quay lại, tách teacher/student và số người khỏi số event. Không hứa cải thiện điểm học chỉ bằng một bài test hoặc bốn tuần self-selected pilot.

## Nhịp làm việc và thay đổi scope

- Cập nhật ngắn theo task ở `💬・trao-đổi`; việc dài/PR/bug theo thread, không cần báo cáo giờ làm từng ngày.
- Review cuối tuần đề xuất trước 20:00 Chủ nhật UTC+07, chỉ chốt sau khi biết lịch học/lab. Lịch họp đăng tại `📌・lịch-deadline` khi mọi người đã đồng ý.
- Mỗi tuần ưu tiên một vấn đề có bằng chứng; bug mất dữ liệu/lộ quyền phải xử lý trước việc tiện ích.
- Task vượt sức hoặc thiếu người: **Tùng nhận trách nhiệm phần còn lại**, hỗ trợ pair hoặc giảm scope; không ép người mới tự xử lý production/migration.
