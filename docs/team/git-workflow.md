# Nhánh đóng góp và Tùng duyệt trước khi vào main

Theo yêu cầu của Tùng: Ân, Lý và Tuấn làm trên nhánh riêng, mở Pull Request (PR), nhận góp ý và sửa trên chính nhánh đó. **Tùng (`@griin-03`) là người review cuối và quyết định merge.** Không push trực tiếp vào `main`, không dùng chung token/tài khoản GitHub.

## Một PR từ đầu đến cuối

Mỗi người cần tài khoản GitHub riêng và quyền Write do Tùng cấp riêng sau khi xác nhận đúng username. Bản phân công không tự cấp quyền repo. Token của Tùng không được gửi cho thành viên.

```sh
git switch main
git pull --ff-only origin main
git switch -c feat/tuan-w1-eval-runner
# Sửa một lát cắt, kiểm tra rồi stage file cụ thể
git diff
git add tests/ten_file.py
npm run check:repo
git commit -m "test: cover AI output contract"
git push -u origin HEAD
```

Trên GitHub, mở **Pull requests → New pull request**, base `main`, compare nhánh vừa push. Điền template, link task `TUAN-W1`/`AN-W1`/`LY-W1` hoặc mã tương ứng, ghi bằng chứng thử và phần cần góp ý. Nhờ `griin-03` review. Tên nhánh gợi ý `feat/an-w2-citation-adapter`, `docs/ly-w1-event-dictionary`, `fix/tuan-w3-provider-parsing`; tránh gom nhiều người sửa cùng một nhánh.

Khi Tùng **Request changes**, sửa tại nhánh hiện tại, commit rồi push tiếp; PR tự cập nhật. Trả lời từng comment, ghi lý do khi không đồng ý; không mở PR mới chỉ để tránh review. Tùng xem lại, xác nhận kiểm tra và **Approve**, sau đó merge (ưu tiên Squash). CI xanh không tự chứng minh nghiệp vụ đúng hay thay thế duyệt nguồn của giáo viên.

Sau merge, xóa nhánh đã xong nếu không dùng tiếp, cập nhật main và tạo nhánh mới. Nếu phát sinh xung đột, nhờ pair; không force-push main. Có thể merge `origin/main` vào nhánh riêng để cập nhật, xử lý xung đột và chạy lại kiểm tra.

## Tùng review những gì

| Phần | Câu hỏi cần trả lời |
|---|---|
| Bài toán/phạm vi | Task nào, hành vi trước/sau, có nằm trong MVP không? |
| Độ đúng | Quyền, nguồn/citation, snapshot, autosave/timeout/retry, lỗi và dữ liệu có đúng không? |
| Bằng chứng | Có cách chạy, test phù hợp, kết quả AI tách khỏi test phần mềm, metric có mẫu số không? |
| Rủi ro | Có secret, PII, đáp án bị lộ, migration/deploy ngoài phạm vi không? |
| Hỗ trợ học | Thành viên hiểu thay đổi, giải thích được trade-off, cần pair hoặc chia task nhỏ hơn không? |

Góp ý cụ thể trên dòng/đoạn liên quan, phân biệt lỗi bắt buộc sửa với gợi ý. Không chấm năng lực bằng số commit/dòng code; ghi đóng góp thật và phần học được vào tài liệu cá nhân tuần 6. Ân/Lý/Tuấn có thể review chéo chuyên môn; Tùng vẫn là người duyệt cuối.

## Cấu hình GitHub và giới hạn

`.github/CODEOWNERS` đề nghị review từ `@griin-03` cho mọi file. Workflow **Quality / verify** chạy kiểm tra trên GitHub-hosted runner, không deploy và không dùng secret VPS/DB/model. Trạng thái bảo vệ nhánh thực tế được ghi trong [báo cáo xác minh](../testing/verification.md), không suy từ việc có file CODEOWNERS.

Cấu hình mong muốn: PR bắt buộc, một approval từ code owner, thu hồi approval khi có commit mới, giải quyết thảo luận, CI `verify` đạt, cấm force-push/xóa main. Tùng là admin và giữ ngoại lệ cho khởi tạo/khắc phục khẩn cấp; mọi lần dùng ngoại lệ phải có lý do và review sau đó. Thành viên chỉ cần quyền Write, không cần Admin/Maintain.

GitHub có thể yêu cầu gói trả phí cho bảo vệ nhánh ở repo private. Nếu API không cho cấu hình, quy trình PR và CI vẫn dùng được nhưng **quy tắc không push main chỉ là quy ước**; cần Tùng chọn gói hỗ trợ hoặc mô hình fork/quyền truy cập phù hợp để cưỡng chế. Không tự đổi repo thành public, mua gói hoặc mời tài khoản khi chưa có username được xác nhận.
