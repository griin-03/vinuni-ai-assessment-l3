# Nguyễn Hoàng Ân · AI/ML cùng Tuấn, RAG và chất lượng chuyên môn

Vai trò đề xuất để duyệt. Ân từng dạy Toán THPT, muốn phát triển AI/ML/Data và học cách đưa sản phẩm lên hệ thống. Đầu ra cần có code/module chạy lại được, eval và một lần pair triển khai; không giới hạn ở nghiên cứu hoặc notebook.

**Bắt đầu đọc:** `scripts/rag_domain.py`, `rag_service.py`, `rag_provider.py`, `rag_worker.py`, `evaluations/` và [phạm vi MVP](../../product/assessment-mvp.md). Fixture/corpus đào tạo cũ là kiểm tra cơ chế; bộ ca phổ thông phải chuẩn bị mới.

## AN-W1 · Nguồn, nhiệm vụ AI và tập đánh giá

- Làm: cùng Lý/Tùng chốt một chuyên đề, đối tượng và mục tiêu; xác nhận quyền dùng nguồn. Ưu tiên câu nhận biết/đọc hiểu học liệu cho MVP AI; bài tính toán cần verifier riêng.
- Hướng làm: lập source manifest có phiên bản, thử chunk/retrieval trên ví dụ thật được phép, ghi đầu ra `draft / needs_clarification / insufficient_evidence / out_of_scope / failed`. Đọc kỹ guard hiện buộc đáp án có trong quote; không bỏ guard chỉ để sinh được bài tính toán.
- Đầu ra: PR/doc source pipeline, contract provider + ví dụ và **≥20 case có nhãn** (kể cả thiếu nguồn, mơ hồ, sai quyền, injection, sai chuyên môn). Tách dev/holdout, synthetic/real; chưa có case thật thì ghi 0.
- Xong khi: Tuấn chạy lại được ví dụ, Tùng hiểu interface, mỗi nhãn có lý do/source; chưa báo tỷ lệ LLM nếu chưa gọi model. Review Tùng + Lý, trao đổi kỹ thuật ở `🧪・mini-lab`, task ở `✅・việc-cần-làm`.

## AN-W2 · Prompt/retrieval/citation, cùng Tuấn tích hợp LLM

- Làm: prompt/retrieval/citation và quy tắc từ chối có version; cùng Tuấn chốt output contract. Tuấn chủ trì adapter transport/error, Ân kiểm đầu ra và chuyên môn, Tùng chốt gateway/tích hợp.
- Hướng làm: pair với Tuấn từ job tới output validation; kiểm tra source/quote riêng với kiểm tra ý nghĩa. Kiểm distractor, độ tuổi, chủ đề và không tự chốt câu.
- Đầu ra: PR prompt/guard/retrieval cùng adapter của Tuấn, bảng eval chạy model thật, cost/latency theo cấu hình đã dùng, demo source → draft → giáo viên duyệt. Pair Tùng deploy **staging riêng** và đọc log an toàn.
- Xong khi: người khác tái chạy eval/hiểu giới hạn; gate AI cuối tuần 2 có bằng chứng. Review Tùng, Tuấn chạy lại; demo ở `🚀・dự-án-demo`.

## AN-W3 · Học từ lỗi người dùng thật

- Làm: xem các câu giáo viên giữ/sửa/từ chối từ cohort 1, gom một nhóm lỗi ưu tiên.
- Hướng làm: chỉ dùng nội dung đã được phép/ẩn danh; phân biệt retrieval miss, thiếu căn cứ, suy luận sai, distractor yếu và diễn đạt không hợp lứa tuổi.
- Đầu ra: error taxonomy, case regression mới có nguồn, một thay đổi có before/after trên cùng tập.
- Xong khi: Lý nối được lý do lỗi với metric, Tuấn chạy regression, Tùng quyết định release. Không đưa raw tài liệu/log học sinh vào Git.

## AN-W4 · Một cải thiện có kiểm chứng

- Làm: tối ưu chunk/retrieval hoặc prompt theo lỗi có bằng chứng; review tiêu chí khớp chủ đề và luận cứ.
- Hướng làm: đổi từng biến, giữ holdout không dùng để tune; ghi phiên bản nguồn/model/prompt và nguyên nhân đánh đổi.
- Đầu ra: PR nhỏ, bảng so sánh đã ghi nhãn, các case abstain đúng/sai và phần chưa giải quyết.
- Xong khi: không làm hỏng quyền/citation đã có; review Tuấn tái chạy, Tùng tích hợp; Lý xác nhận mẫu/phân đoạn không bị trộn.

## AN-W5 · Khóa cấu hình ứng viên

- Làm: đo lại chất lượng, chi phí và độ trễ; chốt cấu hình phù hợp ngân sách pilot.
- Hướng làm: chạy cùng bộ ca với cấu hình ứng viên, ghi lỗi nghiêm trọng và điều kiện dừng/hỏi lại. Không bắt đầu fine-tune ngoài scope.
- Đầu ra: model/prompt card, risk log, bảng eval có tử số/mẫu số và cấu hình tái chạy.
- Xong khi: Tùng có cấu hình để release/rollback, Lý dùng được số liệu đúng ngữ nghĩa; review Tùng.

## AN-W6 · Báo cáo và bàn giao AI

- Làm: chạy lại tập eval đã khóa, trình bày demo và rủi ro; hướng dẫn Tuấn/người khác chạy module.
- Đầu ra: báo cáo chất lượng có provenance, tài liệu cách chạy và đóng góp gắn PR; chọn case thành công/thất bại trung thực cho demo.
- Xong khi: người khác tái chạy được; có phân biệt rõ test cơ chế, đánh giá LLM và đánh giá chuyên môn. Review Lý + Tùng.

## Hỗ trợ và portfolio

Tùng nhận deploy/secret/gateway/hạ tầng và blocker ngoài chuyên môn; Ân được pair triển khai để đạt mục tiêu học. Ân và Tuấn là cặp AI/ML cùng xây, chạy eval và review chéo mỗi tuần; không xem Tuấn chỉ là người hỗ trợ Backend hoặc chạy việc lặt vặt.

Portfolio dự kiến: một module RAG có citation/refusal, một bộ eval có nhãn, error analysis và bằng chứng tích hợp/triển khai. Chỉ ghi số liệu/đóng góp đã hoàn thành, không chuyển task được giao thành thành tích.
