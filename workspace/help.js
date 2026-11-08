import {esc,link,notice} from './core.js';

const guides={
  paper:{title:'Soạn một đề ngắn, kiểm tra trước khi giao',steps:[['Lưu nháp','Đặt tên, chọn môn/khối, thêm từng câu. Nháp có thể chưa hoàn chỉnh; nhớ lưu trước khi rời trang.'],['Đáp án và lời giải','Nhập bốn lựa chọn khác nhau, chọn một đáp án đúng và giải thích để học sinh xem sau lịch công bố.'],['Chủ đề cần ôn','Gắn một nhãn cụ thể như “Tính biệt thức delta” để bảng kết quả chỉ ra phần cần ôn.'],['Kiểm tra & chốt','Đối chiếu nội dung rồi chốt. Đề đã chốt giữ nguyên; nhân bản thành nháp mới nếu cần sửa.']]},
  rooms:{title:'Giao đề và theo dõi một phòng thi',steps:[['Chọn đề đã chốt','Mỗi phòng dùng một phiên bản đề và danh sách học sinh riêng.'],['Lịch và thời lượng','Hạn mỗi lượt là thời điểm sớm hơn giữa hết thời lượng và giờ đóng phòng.'],['Công bố đáp án','Mặc định đáp án/lời giải mở sau hạn phòng; chọn thời điểm phù hợp trước khi giao.'],['Đọc kết quả','Bảng chính tính lượt nộp gần nhất mỗi em. Chưa nộp không bị tính thành điểm 0; xem cả cỡ mẫu và câu nhiều em sai.']]},
  authoring:{title:'Soạn có dẫn chứng: nguồn rõ, giáo viên quyết định',steps:[['Nguồn được phép','Chọn học liệu đúng quyền, đúng phiên bản và có hiệu lực.'],['Chủ đề cụ thể','Nêu kiến thức cần kiểm tra, đối tượng và số câu; không gửi dữ liệu nhận diện học sinh.'],['Mở dẫn chứng','Trích dẫn khớp chưa chứng minh câu hỏi đúng ý nghĩa. Đọc nguồn và kiểm tra đáp án/phương án nhiễu.'],['Sửa, từ chối hoặc duyệt','Chỉ câu đã được giáo viên duyệt mới vào ngân hàng. Chế độ hiện tại trích xuất theo mẫu, chưa dùng LLM.']]},
  assessments:{title:'Làm bài và xem lại phần cần ôn',steps:[['Trước khi bắt đầu','Kiểm tra lịch, thời lượng và số lượt; đọc hướng dẫn giáo viên đã đặt.'],['Trong khi làm','Chọn đáp án để tự lưu. Tải lại trang giữ câu đã lưu và không đặt lại đồng hồ.'],['Khi lỗi lưu','Đọc trạng thái lưu. Nếu có tab khác thay đổi, tải bài mới nhất; báo giáo viên nếu chưa xử lý được.'],['Sau khi nộp','Xem điểm và mở lại lời giải theo lịch công bố. Không gửi mật khẩu hay toàn bộ bài làm khi báo lỗi.']]}
};

export function helpFor(route,role){
  const learner=!['training','admin'].includes(role);
  const key=['paper','paper-new','papers'].includes(route)?'paper':['room','rooms'].includes(route)?'rooms':['knowledge','draft','authoring'].includes(route)?'authoring':route==='assessments'||learner?'assessments':'paper';
  const guide=guides[key];
  const body=`<div class="stack">${guide.steps.map(([title,copy],i)=>`<section><h3 class="small">${i+1}. ${esc(title)}</h3><p class="small muted" style="line-height:1.9;margin-top:7px">${esc(copy)}</p></section>`).join('')}<div class="row" style="flex-wrap:wrap">${learner?link('/workspace/assessments','Bài kiểm tra của tôi','checkSquare','secondary'):link('/workspace/papers','Đề thi của tôi','file','secondary')+link('/workspace/rooms','Phòng thi & kết quả','chart','secondary')}</div>${notice('Cần hỗ trợ: ghi màn hình đang dùng, bước tái hiện, thời điểm và thông báo lỗi; gửi riêng cho giáo viên hoặc người phụ trách triển khai. Che tên/email, token và câu trả lời khi chia sẻ ảnh.','help')}</div>`;
  return {title:guide.title,body};
}
