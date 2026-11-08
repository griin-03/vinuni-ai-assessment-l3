# Hỗ trợ và tiếp nhận lỗi

Trạng thái: quy trình hỗ trợ pilot **đề xuất**, chưa có tổng đài, SLA hay chatbot đang vận hành. Tùng là đầu mối nhận lỗi kỹ thuật; giáo viên giải đáp nội dung/điểm bài; Lý tổng hợp phản hồi đã ẩn danh để chọn vấn đề cần sửa.

## Báo lỗi đủ để tái hiện

Ghi phiên bản/commit nếu biết, vai trò, màn hình, thời điểm và múi giờ, thiết bị/trình duyệt, các bước ngắn, kết quả mong đợi và thực tế. Thêm thông báo lỗi/request ID **nếu giao diện có**; không bịa ID. Chỉ đính kèm ảnh đã che thông tin riêng. Thành viên có repo dùng template Bug; người thử gửi riêng cho đầu mối được thông báo khi tham gia pilot, không phải tự tạo tài khoản GitHub.

Không gửi token/cookie/mật khẩu, URL DB, tài liệu chưa được phép, tên/email học sinh, đáp án hoặc toàn bộ bài làm. Lỗi lộ quyền/bí mật báo riêng theo [SECURITY](../../SECURITY.md), không đăng chi tiết khai thác vào kênh chung.

| Mức xử lý | Ví dụ | Người nhận và cách làm |
|---|---|---|
| Khẩn | Lộ đề/đáp án/quyền, mất bài, điểm sai diện rộng | Tùng xác minh, tạm dừng phần bị ảnh hưởng; giữ log tối thiểu, khôi phục theo bản sao được kiểm tra; ưu tiên trước feature |
| Cản trở | Không đăng nhập, không chốt/giao/nộp đúng điều kiện | Tùng triage; Tùng tái hiện/sửa và viết regression; Ân/Tuấn nhận phần liên quan AI |
| Cải thiện | Hướng dẫn khó hiểu, nhãn chủ đề, thao tác thừa | Lý gom bằng chứng/tần suất; Tùng ưu tiên, Ân kiểm tra chuyên môn khi cần |

Chỉ hứa thời gian xử lý sau khi có người nhận và biết ảnh hưởng. Theo dõi: mới → đã tái hiện → đang sửa → chờ xác minh → đóng; đóng sau khi người báo hoặc người review kiểm tra bản sửa. Một phản hồi có thể dẫn đến sửa hướng dẫn thay vì thêm chức năng.

## Một số tình huống thường gặp

- **Connection refused**: kiểm tra terminal server và đúng cổng trong [README](../../README.md).
- **Phòng mẫu hết hạn**: tạo phòng mới; không sửa lịch sử thi để kéo dài demo.
- **Tài khoản khác trong cùng trình duyệt**: cookie dùng chung; dùng cửa sổ ẩn danh/trình duyệt khác để thử giáo viên và học sinh.
- **Đề đã chốt không sửa được**: nhân bản thành nháp mới để giữ nội dung của bài đã giao.
- **Chưa có lời giải**: xem lịch công bố; điểm và lời giải có thể xuất hiện khác thời điểm.
- **Baseline không sinh được câu**: bổ sung nguồn/chủ đề hoặc soạn thủ công; không coi câu thiếu căn cứ là kết quả AI hợp lệ.

Ghi số liệu hỗ trợ theo [kế hoạch đo lường](../data/measurement-plan.md); chỉ dùng dữ liệu được phép, tách phản hồi thực khỏi dữ liệu thử.
