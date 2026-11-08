# MVP: từ đề kiểm tra đến quyết định ôn tập

Cập nhật 08/11/2026 theo đối tượng mới: THCS/THPT. Tài liệu này thay thế lựa chọn L&D/đào tạo doanh nghiệp trước đây. Rubric Level 3 do chủ sản phẩm cung cấp; chưa tự xác nhận đã đạt.

## Khoanh vùng một ca sử dụng

**Một giáo viên Toán lớp 9 chuẩn bị bài kiểm tra trắc nghiệm ngắn, giao cho một nhóm học sinh, rồi quyết định chủ đề nào cần ôn/dạy lại từ bài nộp.**

Giao diện hỗ trợ chọn môn và khối 6–12; ca demo hẹp là phương trình bậc hai, Toán 9. Bốn câu và học liệu mẫu do dự án tự soạn, chưa là bộ đề chuẩn hay nguồn chính thức.

Giả thuyết nỗi đau: giáo viên đang phải ghép công cụ soạn đề, giao bài, thu điểm và đếm lỗi; điểm tổng chưa giúp biết phải ôn phần nào. Đây **chưa phải phát hiện từ khảo sát**. Giá trị cần kiểm chứng: giảm thời gian từ chuẩn bị đề đến chọn nội dung ôn, có căn cứ về câu hỏi và bài nộp.

## Luồng đã làm

1. **Soạn**: môn, khối, mục tiêu; lưu nháp chưa hoàn chỉnh; thêm câu MCQ hoặc lấy ngân hàng; sửa, nhân bản câu thủ công, đổi thứ tự, xóa, xem trước. Câu ngân hàng giữ nguyên nội dung để bảo toàn nguồn. Revision chặn tab cũ ghi đè.
2. **Chốt**: kiểm tra bốn lựa chọn khác nhau, đáp án, lời giải, nguồn và xác nhận giáo viên; tạo nội dung/hash bất biến. Muốn sửa thì nhân bản thành nháp mới. Chưa có duyệt độc lập nhiều cấp.
3. **Giao phòng**: một phiên bản đề, lịch mở/đóng, thời lượng, mốc điểm /100, 1–3 lượt, danh sách học sinh đang hoạt động. Request key ràng buộc payload chống retry giao trùng. Mặc định công bố đáp án sau hạn phòng; quyền chủ phòng kiểm tra tại máy chủ.
4. **Thi**: đúng người/đúng lịch; bắt đầu đồng thời tái sử dụng một lượt; giữ nội dung và mốc điểm riêng; tự lưu có revision, tiếp tục sau tải lại. Đóng nhận lượt mới vẫn cho lượt đang làm nộp tới hạn riêng. Worker chấm đáp án đã lưu khi hết giờ dù trình duyệt đã đóng; quét lại lượt quá hạn sau restart.
5. **Kết quả → ôn tập**: trạng thái từng học sinh, lịch sử lượt, điểm, chủ đề sai, tỷ lệ sai/bỏ trống, phương án từng câu và CSV đúng phòng. Bảng chính tính lượt nộp gần nhất mỗi học sinh; không tính chưa nộp thành 0. Hiện cỡ mẫu và cách tính; giáo viên tự chọn cách hỗ trợ.

Payload học sinh dùng allowlist, không có ghi chú riêng giáo viên/provenance; đáp án và lời giải chỉ xuất hiện theo chính sách công bố. Không chỉ ẩn bằng CSS.

## Port có chọn lọc từ EduTech AI / CogniAssess

Đối chiếu bản nguồn EduTech AI do chủ dự án cung cấp, commit `dcdf949a104d6c3869fe99f9f5ee6e5853f7b625` cùng file làm việc lúc port; không sửa nguồn, không sao chép secrets, dữ liệu người dùng hoặc uploads. Hash file đã đọc: [manifest](edutech-port.json).

| Nguồn | Được chuyển/adapt |
|---|---|
| `teacher/courses/create/page.tsx` | Trình soạn từng câu, thêm/nhân bản/sắp xếp, nháp và xem trước → `workspace/assessment.js` |
| `teacher/courses/create/actions.ts`, `teacher/courses/actions.ts` | Nháp khác nội dung đã chốt; quyền người soạn; nhân bản thay sửa đề đã dùng → `assessment_service.py` |
| `src/lib/question-teacher-support.ts` | Port hàm chuẩn hóa/giới hạn hint/solution/teachingNotes sang Python, giữ riêng giáo viên |
| `src/lib/public-exam-data.ts`, `src/lib/teacher-exam-scope.ts` | Nguyên tắc payload học sinh và kết quả theo quyền; thích nghi thành room-owner/assignment |
| `src/app/api/courses/route.ts`, `actions/classroom.ts` | Danh sách nhận đề, lịch, lượt, thời lượng, chấm tại máy chủ |
| `src/components/exam/exam-room.css` | Bố cục câu hỏi/navigator thích ứng; giữ Onest/xanh đại dương VinAssess |

Đây là port/thích nghi, không chép nguyên component Next/Prisma vào ES modules/Python. Phần đào sâu thêm: release bất biến, mốc điểm snapshot, autosave revision, expiry worker, thời điểm công bố đáp án, request binding và phân tích chủ đề. Không chuyển ví, gói, thanh toán, social, chatbot tổng quát, camera hay cả cây quyền khoa/bộ môn.

## Bằng chứng và số đo còn thiếu

| Cần đo thật | Cách so sánh | Hiện tại |
|---|---|---|
| Thời gian chuẩn bị đề cùng số câu/chủ đề | Cách cũ và VinAssess; giáo viên đối chiếu chất lượng | Chưa đo |
| Thời gian chọn hai chủ đề cần ôn | Cùng bộ bài nộp, bảng điểm thường và bảng phân tích | Chưa đo |
| Độ phù hợp của quyết định ôn | Giáo viên kiểm tra câu, nhãn chủ đề và lý do | Chưa đánh giá |
| Chất lượng sinh câu có nguồn | Golden ≥20 ca phổ thông, nguồn hợp lệ, nhãn ngữ nghĩa của giáo viên | Chưa chạy LLM |

Thu thập quan sát/phỏng vấn ngoài nhóm theo rubric người dùng (ví dụ ≥20 người), lưu câu nói đã ẩn danh, tần suất, thời gian, ứng viên bị loại và lý do bằng số. Dùng `evidence/`; không bịa số. Ưu tiên giáo viên bộ môn xác nhận pain. Hoạt động với học sinh vị thành niên cần theo quy trình cho phép của nhà trường và chỉ thu dữ liệu cần thiết.

## Giới hạn thực tế

- Chỉ MCQ bốn lựa chọn/một đáp án, điểm đều /100. Chưa có nhiều phần, thang điểm THPT riêng, đúng-sai cụm, tự luận, LaTeX renderer, OCR/Word/Excel. Có công thức Unicode/văn bản; chưa gọi là trình soạn toán chuyên sâu.
- Soạn có nguồn là trích xuất theo mẫu, không LLM. Bộ 38 ca cũ kiểm tra cơ chế trên corpus đào tạo, không chứng minh chất lượng câu phổ thông.
- Một trường/database, một vai trò chính/tài khoản. Giáo viên chọn học sinh hoạt động trong trường; chưa có phân công môn–lớp đầy đủ. Nhóm lưu ở `departments`, chưa là hệ thống quản lý trường đầy đủ.
- Chưa cổng tự đăng ký học sinh/phụ huynh, email mời/khôi phục, camera, xếp hạng, chứng chỉ, kiểm thử tải hay chứng nhận production.
- Phòng mẫu tạo một lần, hết hạn sau bảy ngày. Tạo phòng mới để demo lần sau; không tự đổi hạn bài đã giao.
- Runtime vẫn Python/SQLite. Prisma/TiDB cấu hình và kiểm tra riêng, chưa áp dụng schema/chuyển dữ liệu/thay runtime. Xem [TiDB](../architecture/tidb.md).

## Chạy thử

`npm start` → `/login` → **Giáo viên** → **Đề thi của tôi** → **Soạn đề mới** → **Kiểm tra & chốt** → **Giao vào phòng thi**. Mở cửa sổ đăng nhập riêng vai trò **Học sinh** để làm bài; quay giáo viên → **Phòng thi & kết quả**.

`npm test` kiểm tra cả luồng cũ/mới trên HTTP và SQLite tạm. [Báo cáo xác minh](../testing/verification.md) ghi phạm vi kiểm tra. Test pass là bằng chứng cơ chế, chưa là pain/impact hay đánh giá mô hình.
