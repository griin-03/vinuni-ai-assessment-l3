# Nháp cho 🧪・mini-lab

**Chưa gửi. Đây là gợi ý tự luyện của dự án, không phải bài chính thức AI20K.** Một lab một thread, có input/cách chạy/output/tiêu chí/reviewer. Ghép vào task tuần để không tăng gánh học riêng.

| Lab | Pair | Mục tiêu / đầu ra |
|---|---|---|
| LAB-W1: Theo một RAG trace | Ân–Tuấn; Tùng hỗ trợ Python | Source/chunk/retrieval/provider/guard, Tuấn làm PR eval runner và giải thích output |
| LAB-W2: Từ LLM tới review | Ân–Tuấn; Tùng pair staging | Output đúng/sai/abstain, validation và cách deploy/đọc log an toàn; Lý đối chiếu event |
| LAB-W3: Một lỗi AI thật | Ân–Tuấn; Lý/Tùng review | Tái hiện bằng fixture AI đã ẩn danh → regression → sửa pipeline → kiểm lại |
| LAB-W4: Kiểm một giả thuyết | Lý–Tuấn, Ân kiểm ý nghĩa | Query/metric trước-sau trên cùng định nghĩa, phân biệt sample nhỏ và kết luận chắc chắn |
| LAB-W5: Thử lỗi provider cách ly | Ân–Tuấn; Tùng kiểm hệ thống | Timeout/429/schema sai/cost; Tùng giữ backup/restore staging, không chạm VPS sản phẩm khác |
| LAB-W6: Người khác chạy lại | Bốn người kiểm chéo | Mỗi phần có hướng dẫn/đầu ra và giới hạn, tái chạy được trước demo |

Chưa có key hoặc nguồn thật thì dùng fixture có nhãn synthetic và nói rõ kết quả tương ứng; không biến fixture thành đánh giá LLM.
