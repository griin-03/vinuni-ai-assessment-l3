# Lát cắt AI có căn cứ: soạn câu hỏi từ tài liệu nội bộ

Ngày nghiên cứu: 07/11/2026. Rubric “AI20K Level 3” trong tài liệu này là **yêu cầu người dùng cung cấp**, chưa được đối chiếu với một văn bản công bố chính thức. Memo nghiên cứu ở giai đoạn đầu; định hướng hiện tại là giáo viên/học sinh THCS, THPT ở [MVP](../product/assessment-mvp.md). Ưu tiên một tác vụ AI có bằng chứng trước khi mở rộng.

## Phạm vi sản phẩm được chọn

**Một người dùng:** chuyên viên đào tạo nội bộ (L&D). **Một tác vụ:** từ chính sách/quy trình đã được phép sử dụng, tạo bản nháp câu hỏi trắc nghiệm để người phụ trách kiểm tra. **Một kết quả AI:** câu hỏi, bốn phương án, một đáp án đúng, giải thích và trích dẫn nguồn cho đáp án; hoặc yêu cầu làm rõ/từ chối có lý do.

AI không tự xuất bản câu hỏi, tự giao bài, thay đổi điểm hay kết luận năng lực nhân viên. Nút duyệt mới chuyển bản nháp vào ngân hàng câu hỏi theo quyền người đang đăng nhập. Đây là lựa chọn phạm vi cho VinAssess, không phải điều khoản bắt buộc từ các hướng dẫn dưới đây.

## Nguồn và bài học có thể áp dụng

- HAX nêu các hướng dẫn làm rõ khả năng/giới hạn, hỗ trợ sửa sai, thu hẹp dịch vụ khi chưa chắc chắn, giải thích hành vi và cho biết hệ quả thao tác. [Microsoft HAX Design Library, G1/G2/G9/G10/G11/G16](https://www.microsoft.com/en-us/haxtoolkit/library/)
- PAIR khuyến nghị giải thích khi không đủ dữ liệu để đáp ứng, và cung cấp đường đi tiếp khi hệ thống không thể đưa kết quả. [Google PAIR — Errors + Graceful Failure](https://pair.withgoogle.com/chapter/errors-failing/)
- OWASP yêu cầu xem tài liệu truy hồi và đầu ra mô hình là dữ liệu không đáng tin; quyền và đối số thao tác phải được kiểm tra ngoài mô hình. Tách nhãn/instruction hay lọc từ khóa không tạo ra bảo đảm chống prompt injection. [OWASP — LLM Prompt Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html)
- NIST AI 600-1 khuyến nghị kiểm tra nguồn/trích dẫn (MS-2.5-003), nguồn gốc và căn cứ dữ liệu RAG/đánh giá (MS-2.5-005), so sánh với dữ liệu chuẩn bằng nhiều cách đánh giá (MP-2.3-001), đồng thời không suy rộng từ các thử nghiệm hẹp, giai thoại (MS-2.5-001). [NIST Generative AI Profile](https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.600-1.pdf)

Các kiểm soát và chỉ số tiếp theo là **đề xuất kỹ thuật và nghiệm thu cho VinAssess**, không phải ngưỡng chứng nhận do các tổ chức này quy định.

## Bốn lớp rủi ro đúng theo yêu cầu người dùng

| Lớp | Tình huống lỗi cần xử lý | Tương tác và kiểm soát cụ thể | Cách đo |
|---|---|---|---|
| 1 · Nguồn sự thật; bịa nội dung/trích dẫn | AI viện dẫn đoạn không tồn tại, dùng chính sách cũ hoặc giải thích trái nguồn | Chỉ truy hồi tài liệu được cấp quyền, có phiên bản và hiệu lực; giữ nguyên danh sách đoạn đã gửi cho mô hình. UI mở được đúng tài liệu/phiên bản/đoạn. Máy chủ xác thực citation thuộc tập được truy hồi và quote thực sự có trong đoạn; người duyệt kiểm tra ý nghĩa | Tỷ lệ nguồn truy cập được và quote khớp; citation hỗ trợ đáp án/giải thích theo người gán nhãn; tỷ lệ khẳng định không có căn cứ; đúng phiên bản |
| 2 · Đầu vào mơ hồ/thiếu thông tin | “Tạo đề phù hợp” nhưng không nói chủ đề, số câu hoặc tài liệu; nguồn có hai cách hiểu | Biểu mẫu xác định tài liệu, mục tiêu, chủ đề và số câu. Nếu thiếu dữ kiện quan trọng, trả danh sách thông tin cần bổ sung; nếu tài liệu không đủ thì không bịa để đủ số lượng | Precision/recall cho quyết định hỏi lại; tỷ lệ từ chối nhầm trên ca đủ thông tin; số vòng làm rõ và tỷ lệ hoàn tất sau làm rõ |
| 3 · Ngoài phạm vi/vượt quyền | Yêu cầu đọc phòng ban khác, tiết lộ đề chưa mở, sửa điểm; tài liệu chèn “bỏ qua hướng dẫn” | Cổng quyền chạy trước retrieval và trước approve; mô hình chỉ nhận dữ liệu đã lọc và không có công cụ sửa hệ thống. Tài liệu là dữ liệu, không phải chỉ dẫn. UI giải thích giới hạn và dẫn về tác vụ soạn câu hỏi | Rò dữ liệu trái quyền = 0 trong bộ kiểm thử; tỷ lệ thao tác ghi ngoài tác vụ bị chặn; tỷ lệ bỏ lọt/chặn nhầm injection; thử lách bằng API trực tiếp |
| 4 · Thiệt hại khi sai nghiệp vụ | Đáp án sai được dùng để đào tạo hoặc đánh giá nhân viên; reviewer tin nhãn AI quá mức | Luôn ghi “Bản nháp AI — cần kiểm tra”; hiện đáp án, giải thích và nguồn cạnh nhau. Người có quyền sửa/từ chối/duyệt, xác nhận đã kiểm tra. Chỉ thao tác duyệt của con người ghi ngân hàng câu hỏi; lưu ai duyệt, bản nháp nào, nguồn nào và lúc nào | Đáp án chính xác, chỉ có một đáp án đúng, phù hợp mục tiêu; lỗi nghiêm trọng thoát qua duyệt; tỷ lệ sửa/từ chối; thời gian để tạo một câu hỏi được chấp nhận |

**Điểm cần phân biệt:** quote khớp chuỗi không chứng minh kết luận đúng. Đáp án nhiễu được phép sai có chủ đích; cần kiểm tra đáp án được đánh dấu đúng và lời giải được nguồn hỗ trợ, thay vì cấm mọi con số khác trong bốn lựa chọn. Không trình bày similarity score hoặc “độ tự tin” do mô hình tự báo thành xác suất chính xác đã được hiệu chuẩn.

## Kiến trúc vừa đủ cho lát cắt

1. **Tài liệu phiên bản:** lưu tác giả/chủ sở hữu, phạm vi truy cập, trạng thái được dùng, phiên bản, hash nội dung và thời điểm hiệu lực. Các đoạn có định danh và vị trí ổn định; không tự tạo số trang nếu chưa có parser xác định trang.
2. **Cổng yêu cầu:** kiểm tra quyền, trường bắt buộc, phạm vi tác vụ; trả `needs_clarification`, `out_of_scope`, `insufficient_evidence` hoặc cho chạy. Không gọi mô hình chỉ để xử lý lỗi quyền có thể quyết định chắc chắn bằng mã.
3. **Retrieval:** lọc theo quyền và phiên bản trước khi tìm; chọn đoạn hỗ trợ mục tiêu, ghi lại các đoạn thực tế đã cung cấp. Lexical retrieval là baseline có thể đo, không được tự gọi là semantic retrieval.
4. **Sinh bản nháp:** adapter mô hình chỉ nhận instruction cố định, yêu cầu có cấu trúc và các đoạn dữ liệu. Đầu ra có schema rõ: prompt/options/correct/explanation/evidence IDs/quotes, không có lệnh thao tác database. Lưu model, prompt version, nguồn và thời gian chạy.
5. **Kiểm tra và công bố:** kiểm tra schema/citation/phiên bản/quyền; bản nháp lỗi không được duyệt. Duyệt là giao dịch riêng do người dùng xác nhận, có chống ghi lặp và nhật ký. Nếu nguồn bị thu hồi hoặc phiên bản hiệu lực thay đổi trước lúc duyệt, yêu cầu kiểm tra lại. Câu hỏi đã duyệt giữ được liên kết tới nguồn gốc; lịch sử lượt thi không bị viết lại.

Nếu chưa cấu hình LLM, UI cần nói rõ “chưa kết nối mô hình”, cho xem luồng dữ liệu mẫu có nhãn riêng hoặc không cho sinh. Bộ test dùng mock vẫn hữu ích cho hợp đồng phần mềm, nhưng **không phải đo chất lượng AI thực**. Việc chọn nhà cung cấp cần xét chính sách dữ liệu nội bộ; không tự gửi tài liệu thật tới dịch vụ bên ngoài khi chưa có cấu hình và phạm vi sử dụng phù hợp.

## Golden set và báo cáo đo chất lượng

Theo rubric người dùng: tối thiểu 20 ca, có ca thật và ca khó. Một bộ khởi đầu **đề xuất**: 8 ca có đủ căn cứ; 4 ca thiếu/mơ hồ; 3 ca không có nguồn, nguồn mâu thuẫn hoặc hết hiệu lực; 3 ca trái quyền/ngoài phạm vi; 2 ca injection trong tài liệu. Phải bổ sung ca thật từ công việc L&D; phân bố trên không tự chứng minh tính đại diện.

Mỗi ca cần có: ID, nguồn gốc (`real`/`synthetic`), quyền sử dụng, tài liệu và phiên bản, đầu vào, phạm vi người dùng, quyết định mong đợi, đoạn nguồn chuẩn và tiêu chí chấp nhận. Các đầu ra sinh khác câu chữ vẫn có thể đúng; chấm theo rubric thay vì yêu cầu khớp toàn bộ văn bản. Người chuyên môn gán nhãn trước khi xem kết quả nếu có thể; ghi bất đồng và cách phân xử. Ca được dùng sửa prompt không đồng thời được báo là bộ holdout chưa từng dùng.

Báo cáo cần tách:

- **Kiểm thử hệ thống:** schema/citation hợp lệ, quyền, trạng thái và approve; có thể đo bằng fixture/mock.
- **Chất lượng mô hình thật:** retrieval recall trên đoạn chuẩn; độ đúng đáp án; nguồn có thực sự hỗ trợ; đủ/không mơ hồ; quyết định hỏi lại/từ chối. Ghi numerator/denominator, model/prompt/corpus version, ca lỗi và cách đo. Provider lỗi hoặc chưa cấu hình phải là `not_run`/`failed`, không tính thành “AI từ chối đúng”.
- **Giá trị sử dụng:** so sánh quy trình thủ công với dùng công cụ bằng cùng loại tài liệu và yêu cầu; đo tổng thời gian đến câu hỏi được chấp nhận, số sửa và lỗi, không chỉ thời gian sinh văn bản.

Ngưỡng đạt phải được thỏa thuận trước khi chạy. Các lỗi quyền, phát hành không duyệt và citation giả nên là điều kiện chặn phát hành dù điểm trung bình cao. Hai mươi ca là tối thiểu theo rubric, không đủ để suy ra độ tin cậy rộng trong doanh nghiệp.

## Chứng cứ vấn đề thật: phần không được thay bằng dữ liệu demo

Rubric người dùng yêu cầu bằng chứng từ ít nhất 20 người hoặc khai thác dữ liệu thật có ví dụ nguyên văn. Các hướng dẫn chính thức ở trên **không phải** 20 người dùng L&D, và 20 câu hỏi do AI tự tạo **không phải** 20 bằng chứng vấn đề.

Cần một evidence ledger riêng: người tham gia/bản ghi được ẩn danh, vai trò, ngày và phương pháp thu thập, trích đoạn nguyên văn có quyền sử dụng, nguồn truy nguyên, tác vụ/tần suất, thời gian hoặc lỗi hiện tại, cách giải quyết đang dùng và mức độ ảnh hưởng. Không ghi suy diễn của nhóm thành lời người dùng. Nếu khai thác hội thoại/bài đăng, phải lưu nguồn/ngày/điều kiện sử dụng, phân biệt số bản ghi với số người duy nhất và lọc trùng.

Tại thời điểm viết memo, nghiên cứu này chỉ cung cấp cơ sở thiết kế từ nguồn chính thức; **chưa thu thập 20 người, chưa có bộ ca thật được chuyên gia xác nhận và chưa có kết quả đánh giá LLM của VinAssess**. Các mục đó phải được báo là còn thiếu cho đến khi có dữ liệu thật.
