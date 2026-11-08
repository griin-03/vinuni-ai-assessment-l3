import {state,api,esc,icon,avatar,date,dateTime,can,staff,action,link,badge,progress,percent,empty,notice,categories,field,area,selectField,toast,searched} from './core.js';
import {shell,view,auditPage,pendingItems,titles} from './views.js';
import {authoringRoutes,configureAuthoring,loadAuthoring,renderAuthoring,stopAuthoringPoll,authoringAction,authoringSubmit,authoringChange} from './authoring.js';
import {assessmentRoutes,configureAssessment,loadAssessment,renderAssessment,assessmentAction,assessmentSubmit,assessmentInput,canLeaveAssessment} from './assessment.js';
import {helpFor} from './help.js';

const root=document.getElementById('app'),overlays=document.getElementById('overlay-root');
let timer=null,auditRows=[],saveQueue=Promise.resolve(),saveError=false,lastFocus=null;
let currentPath=location.pathname;
const roleIcons={learner:'book',manager:'users',training:'layers',admin:'shield'};
const todayPlus=days=>{const d=new Date();d.setDate(d.getDate()+days);return d.toISOString().slice(0,10);};
const dueISO=value=>new Date(value+'T23:59:00+07:00').toISOString();

function routeInfo(){
 const [,base,page,id]=location.pathname.split('/');
 state.route=base==='workspace'?(page||'overview'):'login';state.id=Number(id)||null;
}
function navigate(path,replace=false){
 if(!canLeaveAssessment())return;
 closeModal();if(state.attempt&&!state.attempt.submitted_at&&!path.includes('/attempt/'))state.attempt=null;
 history[replace?'replaceState':'pushState']({},'',path);state.search='';state.filter='all';state.category='all';state.mobile=false;routeInfo();loadRoute();window.scrollTo(0,0);
 currentPath=path;
}
async function refresh(){state.data=await api('bootstrap');state.csrf=state.data.csrf;}
async function loadRoute(){
 stopAuthoringPoll();
 clearInterval(timer);
 if(!state.data){await loginPage();return;}
 if(state.route==='login'){navigate('/workspace/overview',true);return;}
 try{
  if(authoringRoutes.includes(state.route)&&can('authoring.draft'))await loadAuthoring();
  if(assessmentRoutes.includes(state.route))await loadAssessment();
  if(state.route==='attempt'){
   state.attempt=await api('attempts/'+state.id);state.clockOffset=Date.now()/1000-state.attempt.server_time;state.question=0;renderExam();return;
  }
  if(state.route==='audit'&&can('audit.read'))auditRows=await api('audit');
  render();
 }catch(error){handleError(error);}
}
function render(){
 clearInterval(timer);document.title=(titles[state.route]||'Không gian làm việc')+' · VinAssess';
 root.innerHTML=shell(assessmentRoutes.includes(state.route)?renderAssessment():authoringRoutes.includes(state.route)&&can('authoring.draft')?renderAuthoring():state.route==='audit'&&can('audit.read')?auditPage(auditRows):view());
}
function handleError(error){
 if(error.status===401){state.data=null;state.csrf='';history.replaceState({},'','/login');loginPage();}
 toast(error.message,true);
}
async function loginPage(){
 clearInterval(timer);state.attempt=null;
 if(!state.public)try{state.public=await api('public');}catch(error){root.innerHTML=empty('Chưa kết nối được hệ thống',error.message,action('reload','Thử kết nối lại','arrow'));return;}
 document.title='Đăng nhập · VinAssess';
 root.innerHTML=`<main class="login-page"><section class="login-story"><a href="/" class="brand"><img src="/assets/brand/vinassess-icon.svg" alt=""/>VinAssess</a><div><div class="uppercase" style="color:#8cbcd7">ASSESS · UNDERSTAND · IMPROVE</div><h1>Học đúng trọng tâm.<br/><span>Hiểu bài từ lỗi sai.</span></h1><p>Một không gian thống nhất để học tập, đánh giá năng lực và phát triển lớp học của bạn.</p><div class="login-art" aria-hidden="true"><div class="login-art-top"><span>Hành trình học tập</span>${icon('trend')}</div><div class="login-art-row">${icon('book')}Ôn tập gắn với bài học</div><div class="login-art-line"><i style="width:76%"></i></div><div class="login-art-row">${icon('checkSquare')}Đánh giá theo tiêu chí rõ ràng</div><div class="login-art-line"><i style="width:57%;background:#a8d9ee"></i></div><div class="login-art-row">${icon('chart')}Theo dõi tiến bộ của từng học sinh</div><div class="login-art-line"><i style="width:88%;background:#c3e5f5"></i></div></div><div class="login-steps"><span><b>F</b>Focus</span><span><b>E</b>Evaluate</span><span><b>R</b>Reinforce</span><span><b>D</b>Develop</span></div></div><div class="login-story-foot">${icon('shield')}Truy cập đúng vai trò · Dữ liệu đúng phạm vi</div></section><section class="login-main"><div class="login-content"><a href="/" class="login-back">${icon('arrowLeft')}Về trang giới thiệu</a><h2>Chào mừng trở lại</h2><p class="login-subtitle">Đăng nhập để tiếp tục hành trình học tập và làm việc tại <strong>${esc(state.public.company)}</strong>.</p><form class="login-form" data-form="login"><div data-form-error></div>${field('email','Email tài khoản','email','','required autocomplete="username" placeholder="hocsinh@example.edu"') }<div class="form-field"><label for="login-password">Mật khẩu</label><div class="password-wrap"><input class="input" id="login-password" type="password" name="password" required autocomplete="current-password" placeholder="Nhập mật khẩu của bạn"/><button type="button" class="icon-btn" data-action="toggle-password" aria-label="Hiện hoặc ẩn mật khẩu">${icon('eye')}</button></div></div><div class="between mb"><span class="tiny muted">Tài khoản được cấp bởi nhà trường</span><button type="button" class="btn ghost small" data-action="login-help">Cần hỗ trợ?</button></div><button class="btn" type="submit">Đăng nhập ${icon('arrow')}</button><p class="login-security">${icon('lock')}Phiên đăng nhập được quản lý an toàn tại máy chủ</p></form>${state.public.demo==='1'?`<section class="login-demo"><div class="login-demo-head"><span>Khám phá không gian VinAssess</span>${badge('Môi trường trải nghiệm','amber')}</div><p>Dùng tài khoản mẫu theo vai trò để trải nghiệm. Dữ liệu được lưu riêng trên máy đang chạy dự án.</p><div class="demo-roles">${Object.entries(state.public.roles).map(([role,name])=>`<button class="demo-role" data-action="demo-login" data-role="${role}">${icon(roleIcons[role])}<span>${esc(name)}</span></button>`).join('')}</div></section>`:''}</div></section></main>`;
}
function closeModal(){
 overlays.innerHTML='';document.body.style.overflow='';if(lastFocus?.isConnected)lastFocus.focus();lastFocus=null;
}
function modal(title,subtitle,body,form='',wide=false,submit='Lưu thay đổi'){
 lastFocus=document.activeElement;
 overlays.innerHTML=`<div class="overlay" data-overlay><section class="modal ${wide?'wide':''}" role="dialog" aria-modal="true" aria-labelledby="modal-title"><div class="modal-header"><div><h2 id="modal-title">${esc(title)}</h2>${subtitle?`<p>${esc(subtitle)}</p>`:''}</div><button type="button" class="icon-btn" data-action="close" aria-label="Đóng">${icon('close')}</button></div>${form?`<form data-form="${form}" style="display:contents">`:''}<div class="modal-body"><div data-form-error></div>${body}</div><div class="modal-footer">${action('close',form?'Hủy':'Đóng','','secondary')}${form?`<button class="btn" type="submit">${icon('check')}${esc(submit)}</button>`:''}</div>${form?'</form>':''}</section></div>`;
 document.body.style.overflow='hidden';setTimeout(()=>overlays.querySelector('input,select,textarea,button')?.focus(),30);
}
function formError(form,message){const el=form.querySelector('[data-form-error]');if(el){el.className='field-error';el.textContent=message;el.scrollIntoView({block:'nearest'});}else toast(message,true);}
async function mutate(path,body,message){await api(path,body);closeModal();await refresh();render();toast(message);}
function courseForm(id){
 modal('Tạo chuyên đề ôn tập','Bắt đầu với mục tiêu rõ ràng và nội dung có thể áp dụng.',`${field('title','Tên chương trình','text','','required minlength="3" maxlength="160" placeholder="Ví dụ: Hội nhập học sinh khối Kinh doanh"')}${selectField('category','Nhóm chương trình',categories.map(c=>[c,c]))}${area('description','Mục tiêu & mô tả','','required minlength="10" maxlength="1500" placeholder="Sau chương trình, người học có thể…"')}<div class="form-section between"><span>Nội dung bài học</span>${action('add-lesson','Thêm bài học','plus','ghost sm')}</div><div id="lesson-fields">${lessonForm(1)}</div>${notice('Chương trình được lưu ở trạng thái bản nháp. Kiểm tra nội dung, sau đó xuất bản trước khi giao cho học sinh.','file')}`,'course',true,'Lưu bản nháp');
 if(id){
  const course=state.data.courses.find(c=>c.id===id);if(!course)return;
  const form=overlays.querySelector('form');form.dataset.form='edit-course';form.insertAdjacentHTML('beforeend',`<input type="hidden" name="id" value="${id}"/>`);
  document.getElementById('modal-title').textContent='Chỉnh sửa bản nháp';
  for(const key of ['title','category','description'])form.elements[key].value=course[key];
  const fields=overlays.querySelector('#lesson-fields');fields.innerHTML=course.lessons.map((l,i)=>lessonForm(i+1)).join('');
  [...fields.children].forEach((node,i)=>{const lesson=course.lessons[i];node.querySelector('[name="lesson_title"]').value=lesson.title;node.querySelector('[name="lesson_body"]').value=lesson.body+(lesson.points.length?'\n\n'+lesson.points.map(p=>'• '+p).join('\n'):'');node.querySelector('[name="lesson_minutes"]').value=lesson.minutes;});
 }
}
function lessonForm(index){return `<section class="lesson-form"><div class="between"><strong>Bài học ${index}</strong>${index>1?'<button class="icon-btn" type="button" data-action="remove-lesson" aria-label="Xóa bài học">'+icon('close')+'</button>':''}</div><div class="form-grid"><div class="form-field"><label>Tên bài học</label><input class="input" name="lesson_title" required minlength="3" maxlength="160" placeholder="Chủ đề bài học"/></div><div class="form-field"><label>Thời lượng (phút)</label><input class="input" name="lesson_minutes" type="number" value="15" min="1" max="240" required/></div></div><div class="form-field mt"><label>Nội dung bài đọc</label><textarea name="lesson_body" minlength="30" maxlength="10000" required placeholder="Viết nội dung hướng dẫn, ví dụ và tình huống áp dụng…" style="min-height:110px"></textarea></div></section>`;}
function assignmentForm(kind,id){
 const item=state.data[kind==='course'?'courses':'exams'].find(c=>c.id===id);if(!item)return;
 modal(kind==='course'?'Giao chương trình học':'Giao đợt khảo thí',item.title,`<input type="hidden" name="id" value="${id}"/>${kind==='course'?field('due','Hạn hoàn thành','date',todayPlus(14),`required min="${todayPlus(0)}"`):notice('Hạn nộp: <strong>'+dateTime(item.due)+'</strong>. Người dùng sẽ có quyền làm bài sau khi được giao.','calendar')}<div class="form-section">Chọn học sinh</div><div class="filter-row mb"><label class="input-wrap">${icon('search')}<input class="input" data-selection-search placeholder="Tìm tên hoặc lớp / nhóm…" aria-label="Tìm người nhận"/></label><select data-selection-department aria-label="Lọc theo lớp / nhóm"><option value="all">Tất cả lớp / nhóm</option>${state.data.departments.map(d=>`<option value="${d.id}">${esc(d.name)}</option>`).join('')}</select></div><div class="between mb"><label class="check-row"><input type="checkbox" data-select-all/>Chọn tất cả đang hiển thị</label><span class="tiny muted" data-selection-count>0 học sinh đã chọn</span></div><div class="selection-list">${state.data.people.filter(p=>p.status==='active').map(p=>`<label class="selection-row" data-selection-person="${esc(p.name+' '+p.department)}" data-department="${p.department_id}"><input type="checkbox" name="user_ids" value="${p.id}"/>${avatar(p.name,p.id)}<span class="grow">${esc(p.name)}<small>${esc(p.department)} · ${esc(p.email)}</small></span>${item.members?.includes(p.id)?badge('Đã giao','gray'):''}</label>`).join('')}</div><div class="mt">${notice('Giao lại chương trình không xóa tiến độ hiện có. Tài khoản đã khóa không nằm trong danh sách nhận.','info')}</div>`,'assign-'+kind,true,'Xác nhận giao');
}
function questionForm(){
 modal('Thêm câu hỏi','Câu hỏi trắc nghiệm với một phương án đúng.',`${selectField('category','Nhóm nội dung',categories.map(c=>[c,c]))}${area('prompt','Nội dung câu hỏi','','required minlength="10" maxlength="2000" placeholder="Mô tả tình huống và câu hỏi rõ ràng…"')}<div class="form-section">Phương án trả lời</div>${[0,1,2,3].map(i=>`<div class="form-field"><label for="answer-${i}">Phương án ${String.fromCharCode(65+i)}</label><div class="row"><label class="check-row" title="Chọn làm đáp án đúng"><input type="radio" name="correct" value="${i}" ${i===0?'checked':''} required aria-label="Đáp án ${String.fromCharCode(65+i)} là đúng"/></label><input class="input" id="answer-${i}" name="option_${i}" required maxlength="500" placeholder="Nội dung phương án ${String.fromCharCode(65+i)}"/></div></div>`).join('')}<p class="tiny muted mb">Chọn nút tròn bên cạnh phương án đúng.</p>${area('explanation','Giải thích đáp án','','required minlength="5" maxlength="2000" placeholder="Giúp người học hiểu lý do và cách áp dụng…"')}`,'question',false,'Thêm câu hỏi');
}
function examForm(){
 if(!state.data.questions.length){toast('Thêm ít nhất một câu hỏi trước khi tạo đợt khảo thí.',true);return;}
 modal('Tạo đợt khảo thí','Thiết lập thời gian và tiêu chí trước khi giao bài.',`${field('title','Tên đợt khảo thí','text','','required minlength="3" maxlength="160" placeholder="Ví dụ: An toàn thông tin · Tháng 11"')}${area('description','Mục tiêu đánh giá','','required minlength="10" maxlength="1500" placeholder="Nội dung và mục tiêu của đợt đánh giá…"')}<div class="form-grid">${field('duration','Thời gian làm bài (phút)','number',20,'required min="1" max="180"')}${field('pass_score','Điểm đạt / 100','number',75,'required min="1" max="100"')}${field('max_attempts','Số lượt làm tối đa','number',2,'required min="1" max="5"')}${field('due','Hạn nộp','date',todayPlus(14),`required min="${todayPlus(0)}"`)}</div><div class="form-section between"><span>Chọn câu hỏi</span><span class="tiny muted" data-selection-count>0 câu hỏi đã chọn</span></div><label class="input-wrap mb">${icon('search')}<input class="input" data-selection-search placeholder="Tìm trong ngân hàng câu hỏi…" aria-label="Tìm câu hỏi"/></label><div class="selection-list">${state.data.questions.map(q=>`<label class="selection-row" data-selection-person="${esc(q.prompt+' '+q.category)}"><input type="checkbox" name="question_ids" value="${q.id}"/><span>${esc(q.prompt)}<small>${esc(q.category)} · CH-${String(q.id).padStart(4,'0')}</small></span></label>`).join('')}</div><div class="mt">${notice('Bản nháp chưa hiển thị với học sinh. Mở đợt và giao học sinh sau khi kiểm tra các thiết lập. Thời gian làm bài được tính tại máy chủ.','clock')}</div>`,'exam',true,'Tạo bản nháp');
}
function userForm(id){
 const u=state.data.people.find(p=>p.id===id);
 if(u){modal('Quản lý tài khoản',u.name,`<input type="hidden" name="id" value="${u.id}"/><div class="row mb">${avatar(u.name,u.id,'lg')}<div><h3>${esc(u.name)}</h3><p class="small muted">${esc(u.email)}</p></div></div>${selectField('role','Vai trò truy cập',Object.entries(state.data.roles),u.role)}${selectField('status','Trạng thái',[['active','Hoạt động'],['inactive','Khóa tài khoản']],u.status)}${notice('Thay đổi quyền hoặc trạng thái sẽ kết thúc các phiên đăng nhập của tài khoản này.','shield')}`,'edit-user',false,'Cập nhật tài khoản');return;}
 modal('Thêm học sinh','Tạo tài khoản nội bộ và xác định đúng phạm vi giảng dạy.',`${field('name','Họ và tên','text','','required minlength="2" maxlength="100"')}${field('email','Email tài khoản','email','','required maxlength="200" autocomplete="off"')}<div class="form-grid">${selectField('department_id','Lớp / nhóm',state.data.departments.map(d=>[d.id,d.name]))}${selectField('role','Vai trò truy cập',Object.entries(state.data.roles),'learner')}</div><div class="mt">${field('title','Chức danh','text','','maxlength="100"')}${field('password','Mật khẩu khởi tạo','password','','required minlength="12" maxlength="200" autocomplete="new-password"')}</div>${notice('Mật khẩu cần ít nhất 12 ký tự, gồm chữ hoa, chữ thường và số. Cung cấp tài khoản qua kênh nội bộ an toàn; hệ thống chưa gửi thư mời qua email.','lock')}`,'user',false,'Tạo tài khoản');
}
function personDetail(id){
 const p=state.data.people.find(p=>p.id===id);if(!p)return;
 modal('Hồ sơ học tập',p.department,`<div class="row mb">${avatar(p.name,p.id,'lg')}<div><h2>${esc(p.name)}</h2><p class="small muted">${esc(p.title)}</p><p class="tiny muted">${esc(p.email)}</p></div></div><div class="side-details" style="padding:0"><div class="kv"><span>Vai trò</span>${badge(state.data.roles[p.role])}</div><div class="kv"><span>Chương trình đã giao</span><b>${p.assigned}</b></div><div class="kv"><span>Chương trình hoàn thành</span><b>${p.completed}</b></div><div class="kv"><span>Lượt học quá hạn</span><b>${p.overdue}</b></div><div class="kv"><span>Điểm khảo thí trung bình</span><b>${p.score===null?'Chưa có kết quả':p.score+'/100'}</b></div></div><div class="mt mb">${progress(p.progress)}<p class="small muted" style="margin-top:7px">Tiến độ học tập trung bình: ${p.progress}%</p></div>${notice('Hồ sơ này chỉ hiển thị trong phạm vi học sinh bạn được phép quản lý.','shield')}`);
}
function help(){
 const guide=helpFor(state.route,state.data.user.role);
 modal(guide.title,'Hướng dẫn đúng bước đang dùng; không cần đi hết mọi menu.',guide.body);
}

function showSearch(value=''){
 modal('Tìm kiếm trong không gian làm việc','Chỉ hiển thị dữ liệu thuộc phạm vi truy cập của bạn.',`<label class="input-wrap mb">${icon('search')}<input class="input" id="workspace-search" value="${esc(value)}" placeholder="Chương trình, khảo thí hoặc học sinh…" aria-label="Tìm kiếm nhanh" style="width:100%"/></label><div id="search-results"></div>`);
 searchResults(value);setTimeout(()=>document.getElementById('workspace-search')?.focus(),30);
}
function searchResults(value){
 const target=document.getElementById('search-results');if(!target)return;
 if(value.trim().length<2){target.innerHTML='<p class="small muted">Nhập ít nhất 2 ký tự để bắt đầu tìm kiếm.</p>';return;}
 const d=state.data;const matches=[...d.courses.filter(c=>searched(c.title,value)).map(c=>({title:c.title,sub:'Chương trình · '+c.category,ico:'book',href:'/workspace/course/'+c.id})),...d.exams.filter(x=>searched(x.title,value)).map(x=>({title:x.title,sub:'Đợt khảo thí',ico:'checkSquare',href:staff()?'/workspace/exams':'/workspace/assessments'})),...(d.user.role!=='learner'?d.people.filter(p=>searched(p.name+' '+p.email,value)).map(p=>({title:p.name,sub:p.department,ico:'users',id:p.id})):[])].slice(0,12);
 target.innerHTML=matches.map(m=>m.href?`<a href="${m.href}" class="search-result">${icon(m.ico)}<div><strong>${esc(m.title)}</strong><small>${esc(m.sub)}</small></div></a>`:`<button type="button" class="search-result" style="width:100%;text-align:left;background:white;border:0;border-bottom:1px solid var(--line)" data-action="person" data-id="${m.id}">${icon(m.ico)}<span><strong>${esc(m.title)}</strong><small>${esc(m.sub)}</small></span></button>`).join('')||'<p class="small muted">Không tìm thấy kết quả phù hợp. Thử từ khóa khác.</p>';
}
function notifications(){
 lastFocus=document.activeElement;
 overlays.innerHTML=`<div class="overlay drawer-overlay" data-overlay><aside class="drawer" role="dialog" aria-modal="true" aria-labelledby="modal-title"><div class="modal-header"><div><h2 id="modal-title">Việc cần hoàn thành</h2><p>Chương trình và khảo thí được giao cho bạn</p></div><button class="icon-btn" data-action="close" aria-label="Đóng">${icon('close')}</button></div>${pendingItems().map(n=>`<a class="notification-item" href="${n.href}"><div class="row"><span class="activity-symbol">${icon(n.icon)}</span><h3>${esc(n.title)}</h3></div><p>${esc(n.copy)}</p></a>`).join('')||'<div class="panel-body"><p class="small muted">Bạn đã hoàn thành các nhiệm vụ hiện tại.</p></div>'}</aside></div>`;document.body.style.overflow='hidden';overlays.querySelector('button')?.focus();
}
async function exportReport(){
 const response=await fetch('/api/workspace/report.csv',{credentials:'same-origin'});
 if(!response.ok){const result=await response.json();throw new Error(result.error);}
 const url=URL.createObjectURL(await response.blob());const a=document.createElement('a');a.href=url;a.download='VinAssess-Bao-cao-dao-tao-'+todayPlus(0)+'.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);toast('Đã xuất báo cáo theo phạm vi được phân quyền.');
}
function startExam(id){
 const x=state.data.exams.find(x=>x.id===id);if(!x)return;
 modal('Sẵn sàng làm bài?',x.title,`<div class="exam-specs" style="margin-top:0"><div><span>Thời gian</span><b>${x.duration} phút</b></div><div><span>Số câu hỏi</span><b>${x.question_count} câu</b></div><div><span>Điểm đạt</span><b>${x.pass_score}/100</b></div></div><input type="hidden" name="id" value="${id}"/><div class="stack"><p class="small muted" style="line-height:1.9">Bạn có tối đa ${x.max_attempts} lượt làm bài. Câu trả lời được lưu khi chọn. Sau khi nộp, em xem điểm; đáp án và lời giải xuất hiện theo lịch giáo viên đã chọn.</p>${notice('Đồng hồ bắt đầu khi bạn xác nhận. Thời gian vẫn tiếp tục nếu rời trang hoặc tải lại. Khi hết giờ, hệ thống chấm các câu đã lưu.','clock')}<label class="check-row"><input type="checkbox" required/>Tôi đã đọc và hiểu hướng dẫn làm bài.</label></div>`,'start-exam',false,'Bắt đầu làm bài');
}
function renderExam(){
 clearInterval(timer);closeModal();const a=state.attempt;
 if(a.submitted_at){renderResult(a);return;}
 const q=a.questions[state.question];const answered=Object.keys(a.answers).length;
 document.title='Đang làm bài · VinAssess';
 root.innerHTML=`<main class="exam-mode"><header class="exam-top"><div class="row"><img src="/assets/brand/vinassess-logo.svg" alt="VinAssess"/><span class="exam-top-title">${esc(a.title)}</span></div><div class="row"><div class="exam-time" id="exam-timer">${icon('clock')}<span>--:--</span></div>${action('leave-exam','Lưu & thoát','','secondary')}${action('submit-exam','Nộp bài','check')}</div></header><div class="exam-layout"><section class="panel"><div class="exam-question"><div class="between">${badge('CÂU '+String(state.question+1).padStart(2,'0')+' / '+a.questions.length)}<button class="btn ghost sm" data-action="flag">${icon('flag')}${state.flags.has(q.id)?'Đã đánh dấu':'Đánh dấu xem lại'}</button></div><h2>${esc(q.prompt)}</h2><form>${q.options.map((o,i)=>`<label class="answer-option"><input type="radio" name="exam-answer" value="${i}" data-question="${q.id}" ${a.answers[q.id]===i?'checked':''}/><b>${String.fromCharCode(65+i)}</b><span>${esc(o)}</span></label>`).join('')}</form></div><div class="exam-nav">${action('prev-question','Câu trước','arrowLeft','secondary',state.question===0?'disabled':'')}<span class="exam-save" id="save-status">${icon('check')}${saveError?'Có lỗi lưu. Giữ trang mở để thử lại.':'Câu trả lời được lưu tự động'}</span>${action('next-question',state.question===a.questions.length-1?'Kiểm tra & nộp':'Câu tiếp theo','arrow','secondary')}</div></section><aside><div class="panel"><div class="panel-body"><div class="between"><h2 class="small">Danh sách câu hỏi</h2><span class="tiny muted" id="answered-count">${answered}/${a.questions.length} đã trả lời</span></div><div class="question-grid">${a.questions.map((q,i)=>`<button class="question-number ${a.answers[q.id]!==undefined?'answered':''} ${i===state.question?'current':''} ${state.flags.has(q.id)?'flagged':''}" data-action="go-question" data-index="${i}" aria-label="Câu ${i+1}">${i+1}</button>`).join('')}</div><div class="hint-box">${icon('info')}<span>Chọn số câu để di chuyển. Bạn có thể thay đổi câu trả lời trước khi nộp bài.</span></div></div></div></aside></div></main>`;
 const offset=state.clockOffset||0;
 const tick=()=>{if(!state.attempt||state.attempt.submitted_at)return;const remain=Math.max(0,Math.ceil(a.deadline-(Date.now()/1000-offset)));const el=document.getElementById('exam-timer');if(el){el.classList.toggle('urgent',remain<60);el.querySelector('span').textContent=String(Math.floor(remain/60)).padStart(2,'0')+':'+String(remain%60).padStart(2,'0');}if(remain===0){clearInterval(timer);finishExam(true);}};
 tick();timer=setInterval(tick,1000);
}
async function finishExam(auto=false){
 if(!state.attempt||state.attempt.submitted_at)return;
 try{await saveQueue;if(saveError&&!auto)throw new Error('Bài chưa lưu đầy đủ. Hãy thử chọn lại đáp án hoặc tải lại trước khi nộp.');state.attempt=await api('attempts/'+state.attempt.id+'/submit',{answers:state.attempt.answers,expected_revision:state.attempt.revision});clearInterval(timer);closeModal();await refresh();renderResult(state.attempt);if(auto)toast('Đã hết giờ. Hệ thống đã ghi nhận bài làm của bạn.');}catch(error){handleError(error);}
}
function submitExamDialog(){
 const a=state.attempt,remaining=a.questions.length-Object.keys(a.answers).length;
 modal('Xác nhận nộp bài',a.title,`<p class="small muted mb">Đã trả lời <strong>${Object.keys(a.answers).length}/${a.questions.length}</strong> câu hỏi.</p>${remaining?notice('Còn <strong>'+remaining+' câu chưa trả lời</strong>. Những câu này sẽ không được tính điểm.','info'):notice('Bạn đã trả lời tất cả câu hỏi. Sau khi nộp, câu trả lời không thể thay đổi.','check')}<p class="small muted mt">Bạn có thể quay lại kiểm tra trước khi xác nhận.</p>`,'submit-exam',false,'Xác nhận nộp bài');
}
function renderResult(a){
 clearInterval(timer);document.title='Kết quả bài kiểm tra · VinAssess';
 const visible=a.results_visible!==false;
 const detail=visible?a.questions.map((q,i)=>`<section class="review-item"><div class="between">${badge('CÂU '+(i+1),'gray')}${a.answers[q.id]===q.correct?badge('Chính xác','green'):badge(a.answers[q.id]===undefined?'Chưa trả lời':'Cần ôn lại','amber')}</div><h3>${esc(q.prompt)}</h3><div class="review-answer">Đáp án đúng: <strong>${String.fromCharCode(65+q.correct)}. ${esc(q.options[q.correct])}</strong></div>${a.answers[q.id]!==undefined&&a.answers[q.id]!==q.correct?`<p>Bạn đã chọn: ${String.fromCharCode(65+a.answers[q.id])}. ${esc(q.options[a.answers[q.id]])}</p>`:''}<p style="margin-top:10px">${esc(q.explanation)}</p></section>`).join(''):`<div class="panel-body">${notice('Đáp án và lời giải được công bố sau '+dateTime(a.review_available_at)+'. Em có thể mở lại kết quả sau thời điểm này.','lock')}</div>`;
 root.innerHTML=shell(`<div class="page-head"><div><div class="eyebrow">KẾT QUẢ BÀI KIỂM TRA</div><h1>${esc(a.title)}</h1><p>Nộp lúc ${dateTime(a.submitted_at)}${a.submission_reason==='timeout'?' · Hệ thống nộp khi hết giờ':''}</p></div>${link('/workspace/assessments','Về bài kiểm tra của tôi','arrowLeft','secondary')}</div><div class="panel"><div class="result-header"><div class="result-ring ${a.passed?'':'failed'}"><strong>${a.score}</strong><small>/100 điểm</small></div><h2>${a.passed?'Em đã đạt mốc điểm.':'Cùng xem lại những phần cần ôn nhé.'}</h2><p>Mốc đạt: ${a.pass_score}/100${visible?' · Đúng '+a.questions.filter(q=>a.answers[q.id]===q.correct).length+'/'+a.questions.length+' câu':''}</p><p class="tiny muted mt">Kết quả của một bài kiểm tra giúp chọn nội dung ôn tập, chưa phản ánh toàn bộ năng lực của em.</p></div>${detail}</div>`);
}

function selectionFilter(){
 const search=overlays.querySelector('[data-selection-search]')?.value||'',dept=overlays.querySelector('[data-selection-department]')?.value||'all';
 for(const row of overlays.querySelectorAll('[data-selection-person]'))row.hidden=!searched(row.dataset.selectionPerson,search)||(dept!=='all'&&row.dataset.department!==dept);
}
function selectionCount(){const checks=overlays.querySelectorAll('.selection-row input:checked');const el=overlays.querySelector('[data-selection-count]');if(el)el.textContent=checks.length+(overlays.querySelector('input[name="question_ids"]')?' câu hỏi đã chọn':' học sinh đã chọn');}

document.addEventListener('submit',async event=>{
 const form=event.target.closest('[data-form]');if(!form)return;event.preventDefault();
 if(await assessmentSubmit(form))return;
 if(await authoringSubmit(form))return;
 const kind=form.dataset.form,fd=new FormData(form),values=Object.fromEntries(fd),button=form.querySelector('[type="submit"]');
 if(kind==='search'){showSearch(values.search||'');return;}
 if(button)button.disabled=true;
 try{
  if(kind==='login'){
   await api('login',{email:values.email,password:values.password});await refresh();navigate('/workspace/overview',true);
  }else if(kind==='course'||kind==='edit-course'){
   const titles=fd.getAll('lesson_title'),bodies=fd.getAll('lesson_body'),times=fd.getAll('lesson_minutes');
   const result=await api('courses'+(kind==='edit-course'?'/'+values.id:''),{title:values.title,category:values.category,description:values.description,lessons:titles.map((title,i)=>({title,body:bodies[i],minutes:Number(times[i])}))});closeModal();await refresh();navigate('/workspace/course/'+result.id);toast('Đã lưu chương trình ở trạng thái bản nháp.');
  }else if(kind==='assign-course'||kind==='assign-exam'){
   const user_ids=fd.getAll('user_ids').map(Number);if(!user_ids.length)throw new Error('Chọn ít nhất một học sinh để giao.');
   await mutate((kind==='assign-course'?'courses/':'exams/')+values.id+'/assign',{user_ids,...(kind==='assign-course'?{due:dueISO(values.due)}:{})},'Đã giao cho '+user_ids.length+' học sinh.');
  }else if(kind==='question')await mutate('questions',{prompt:values.prompt,category:values.category,options:[0,1,2,3].map(i=>values['option_'+i]),correct:Number(values.correct),explanation:values.explanation},'Đã thêm câu hỏi vào ngân hàng.');
  else if(kind==='exam'){
   const question_ids=fd.getAll('question_ids').map(Number);if(!question_ids.length)throw new Error('Chọn ít nhất một câu hỏi.');
   await mutate('exams',{title:values.title,description:values.description,duration:Number(values.duration),pass_score:Number(values.pass_score),max_attempts:Number(values.max_attempts),due:dueISO(values.due),question_ids},'Đã tạo đợt khảo thí ở trạng thái bản nháp.');
  }else if(kind==='user')await mutate('users',{...values,department_id:Number(values.department_id)},'Đã tạo tài khoản nội bộ.');
  else if(kind==='edit-user')await mutate('users/'+values.id,{role:values.role,status:values.status},'Đã cập nhật tài khoản và kết thúc các phiên cũ.');
  else if(kind==='settings')await mutate('settings',values,'Đã lưu thông tin nhà trường.');
  else if(kind==='password'){
   if(values.new_password!==values.confirm_password)throw new Error('Mật khẩu xác nhận chưa khớp.');
   await api('profile/password',values);closeModal();state.data=null;state.csrf='';navigate('/login',true);toast('Đã đổi mật khẩu. Vui lòng đăng nhập lại.');
  }else if(kind==='start-exam'){
   state.attempt=await api('exams/'+values.id+'/start',{});state.flags=new Set();closeModal();navigate('/workspace/attempt/'+state.attempt.id);
  }else if(kind==='submit-exam')await finishExam();
 }catch(error){if(error.status===401&&kind!=='login')handleError(error);else formError(form,error.message);}
 finally{if(button?.isConnected)button.disabled=false;}
});

document.addEventListener('click',async event=>{
 if(state.mobile&&event.clientX>246){state.mobile=false;root.querySelector('.sidebar')?.classList.remove('open');return;}
 const anchor=event.target.closest('a[href]');
 if(anchor&&anchor.origin===location.origin&&/^\/(workspace(?:\/|$)|login$)/.test(anchor.pathname)&&!event.metaKey&&!event.ctrlKey&&!event.shiftKey){event.preventDefault();navigate(anchor.pathname);return;}
 if(event.target.matches('[data-overlay]')){closeModal();return;}
 const button=event.target.closest('[data-action]');if(!button||button.disabled)return;
 const name=button.dataset.action,id=Number(button.dataset.id);
 try{
  if(await authoringAction(button))return;
  if(await assessmentAction(button))return;
  if(name==='close')closeModal();
  else if(name==='menu'){state.mobile=!state.mobile;root.querySelector('.sidebar')?.classList.toggle('open',state.mobile);}
  else if(name==='logout'){if(!canLeaveAssessment())return;await api('logout',{});state.data=null;state.csrf='';navigate('/login',true);}
  else if(name==='demo-login'){
   const form=root.querySelector('[data-form="login"]');form.elements.email.value=button.dataset.role+'@vinassess.local';form.elements.password.value='VinAssess@2026';form.requestSubmit();
  }else if(name==='toggle-password'){const input=root.querySelector('[name="password"]');input.type=input.type==='password'?'text':'password';}
  else if(name==='login-help')modal('Hỗ trợ đăng nhập','Tài khoản nội bộ do nhà trường cấp.',notice('Liên hệ quản trị hệ thống hoặc đầu mối đào tạo của nhà trường để được cấp tài khoản, cập nhật email hoặc đặt lại mật khẩu.','mail')+(state.public.demo==='1'?'<p class="small muted mt">Môi trường trải nghiệm: chọn một trong bốn vai trò bên dưới biểu mẫu. Tài khoản mẫu có mật khẩu <strong>VinAssess@2026</strong>.</p>':''));
  else if(name==='reload'){state.public=null;loginPage();}
  else if(name==='help')help();
  else if(name==='search')showSearch();
  else if(name==='notifications')notifications();
  else if(name==='chart'){state.chart=button.dataset.mode;render();}
  else if(name==='filter'){state.filter=button.dataset.value;render();}
  else if(name==='new-course')courseForm();
  else if(name==='edit-course')courseForm(id);
  else if(name==='preview-lesson'){
   const c=state.data.courses.find(c=>c.id===id),l=c?.lessons.find(l=>l.id===Number(button.dataset.lesson));if(l)modal(l.title,c.title,`<article class="reader" style="padding:0;min-height:0"><p>${esc(l.body)}</p><ul>${l.points.map(p=>`<li>${icon('check')}<span>${esc(p)}</span></li>`).join('')}</ul></article>`);
  }else if(name==='preview-exam'){
   const x=state.data.exams.find(x=>x.id===id);if(x)modal(x.title,'Xem lại nội dung và tiêu chí trước khi mở đợt.',`<p class="small muted mb">${esc(x.description)}</p><div class="exam-specs"><div><span>Thời gian</span><b>${x.duration} phút</b></div><div><span>Điểm đạt</span><b>${x.pass_score}/100</b></div><div><span>Hạn nộp</span><b>${date(x.due)}</b></div></div>${(x.question_ids||[]).map(qid=>state.data.questions.find(q=>q.id===qid)).filter(Boolean).map((q,i)=>`<section class="question-item"><span class="tiny muted">CÂU ${i+1} · ${esc(q.category)}</span><h3>${esc(q.prompt)}</h3><div class="answers-preview">${q.options.map((o,n)=>`<span class="${n===q.correct?'correct':''}">${String.fromCharCode(65+n)}. ${esc(o)}</span>`).join('')}</div></section>`).join('')}`, '',true);
  }
  else if(name==='add-lesson'){const container=overlays.querySelector('#lesson-fields');if(container.children.length>=30)throw new Error('Tối đa 30 bài học mỗi chương trình.');container.insertAdjacentHTML('beforeend',lessonForm(container.children.length+1));}
  else if(name==='remove-lesson')button.closest('.lesson-form').remove();
  else if(name==='publish-course'){
   modal('Xuất bản chương trình','Nội dung sẽ sẵn sàng để giao cho học sinh.',`<p class="small muted">Bạn đã kiểm tra tên, mục tiêu và các bài học của chương trình?</p><div class="mt">${action('confirm-publish-course','Xác nhận xuất bản','upload','',`data-id="${id}"`)}</div>`);
  }else if(name==='confirm-publish-course')await mutate('courses/'+id+'/publish',{},'Đã xuất bản chương trình. Bạn có thể giao học cho học sinh.');
  else if(name==='assign-course')assignmentForm('course',id);
  else if(name==='assign-exam')assignmentForm('exam',id);
  else if(name==='new-question')questionForm();
  else if(name==='new-exam')examForm();
  else if(name==='exam-status'){
   modal(button.dataset.status==='closed'?'Đóng đợt khảo thí?':'Mở đợt khảo thí?','Xác nhận thay đổi trạng thái.',notice(button.dataset.status==='closed'?'Các lượt đang làm vẫn có thể nộp bài; hệ thống ngừng tiếp nhận lượt làm mới.':'Đợt khảo thí sẽ sẵn sàng để giao cho học sinh. Chỉ người đã được giao mới được phép làm bài.','info')+`<div class="mt">${action('confirm-exam-status','Xác nhận','check','',`data-id="${id}" data-status="${button.dataset.status}"`)}</div>`);
  }else if(name==='confirm-exam-status')await mutate('exams/'+id+'/status',{status:button.dataset.status},'Đã cập nhật trạng thái đợt khảo thí.');
  else if(name==='new-user')userForm();
  else if(name==='edit-user')userForm(id);
  else if(name==='person')personDetail(id);
  else if(name==='export')await exportReport();
  else if(name==='complete-lesson'){
   button.disabled=true;await api('courses/'+id+'/progress',{lesson_id:Number(button.dataset.lesson)});await refresh();render();toast('Đã ghi nhận hoàn thành bài học.');
  }else if(name==='password')modal('Đổi mật khẩu','Sau khi đổi, bạn sẽ cần đăng nhập lại.',`${field('current_password','Mật khẩu hiện tại','password','','required autocomplete="current-password"')}${field('new_password','Mật khẩu mới','password','','required minlength="12" maxlength="200" autocomplete="new-password"')}${field('confirm_password','Xác nhận mật khẩu mới','password','','required minlength="12" maxlength="200" autocomplete="new-password"')}${notice('Mật khẩu mới cần có ít nhất 12 ký tự, gồm chữ hoa, chữ thường và số.','lock')}`,'password',false,'Đổi mật khẩu');
  else if(name==='start-exam')startExam(id);
  else if(name==='resume-exam'||name==='result')navigate('/workspace/attempt/'+id);
  else if(name==='reload-attempt'){await saveQueue;state.attempt=await api('attempts/'+state.attempt.id);saveError=false;state.question=Math.min(state.question,state.attempt.questions.length-1);renderExam();}
  else if(name==='go-question'){state.question=Number(button.dataset.index);renderExam();}
  else if(name==='prev-question'){state.question=Math.max(0,state.question-1);renderExam();}
  else if(name==='next-question'){if(state.question===state.attempt.questions.length-1)submitExamDialog();else{state.question++;renderExam();}}
  else if(name==='flag'){const q=state.attempt.questions[state.question];if(state.flags.has(q.id))state.flags.delete(q.id);else state.flags.add(q.id);renderExam();}
  else if(name==='submit-exam')submitExamDialog();
  else if(name==='leave-exam'){
   await saveQueue;if(saveError)throw new Error('Câu trả lời chưa được lưu. Kiểm tra kết nối trước khi thoát.');
   modal('Rời không gian làm bài?','Thời gian làm bài vẫn tiếp tục.',notice('Các câu trả lời đã được lưu. Bạn có thể mở lại từ Bài kiểm tra của tôi; đồng hồ không dừng khi rời trang.','clock')+`<div class="mt">${action('confirm-leave-exam','Về danh sách','arrowLeft','secondary')}</div>`);
  }else if(name==='confirm-leave-exam'){navigate('/workspace/assessments');await refresh();render();}
 }catch(error){handleError(error);if(button.isConnected)button.disabled=false;}
});

document.addEventListener('input',event=>{
 assessmentInput(event);
 const target=event.target;
 if(target.matches('[data-filter-search]')){
  const pos=target.selectionStart;state.search=target.value;render();const input=root.querySelector('[data-filter-search]');input?.focus();if(input&&pos!==null)input.setSelectionRange(pos,pos);
 }else if(target.id==='workspace-search')searchResults(target.value);
 else if(target.matches('[data-selection-search]'))selectionFilter();
});
document.addEventListener('change',event=>{
 assessmentInput(event);
 authoringChange(event).catch(error=>toast(error.message,true));
 const target=event.target;
 if(target.matches('[data-category-filter],[data-department-filter]')){state.category=target.value;render();}
 else if(target.matches('[data-selection-department]'))selectionFilter();
 else if(target.matches('[data-select-all]')){for(const row of overlays.querySelectorAll('.selection-row:not([hidden])'))row.querySelector('input').checked=target.checked;selectionCount();}
 else if(target.closest('.selection-row'))selectionCount();
 else if(target.name==='exam-answer'){
  const a=state.attempt;a.answers[target.dataset.question]=Number(target.value);const snapshot={...a.answers};
  const status=document.getElementById('save-status');if(status)status.innerHTML=icon('clock')+'Đang lưu…';
  saveQueue=saveQueue.then(()=>api('attempts/'+a.id+'/answers',{answers:snapshot,expected_revision:a.revision})).then(result=>{
   a.revision=result.revision;
   saveError=false;if(state.attempt?.id!==a.id)return;if(result.submitted_at){state.attempt=result;renderResult(result);return;}
   const el=document.getElementById('save-status');if(el)el.innerHTML=icon('check')+'Đã lưu câu trả lời';
   root.querySelectorAll('.question-number').forEach((el,i)=>el.classList.toggle('answered',a.answers[a.questions[i]?.id]!==undefined));const counter=document.getElementById('answered-count');if(counter)counter.textContent=Object.keys(a.answers).length+'/'+a.questions.length+' đã trả lời';
  }).catch(error=>{saveError=true;toast('Chưa lưu được câu trả lời: '+error.message,true);const el=document.getElementById('save-status');if(el)el.innerHTML=error.status===409?'Bài đã thay đổi ở tab khác. '+action('reload-attempt','Tải bài mới nhất','refresh','ghost sm'):'Chưa lưu được · Thử chọn lại đáp án';});
 }
});
document.addEventListener('keydown',event=>{
 if((event.metaKey||event.ctrlKey)&&event.key.toLowerCase()==='k'&&state.data){event.preventDefault();showSearch();}
 if(event.key==='Escape'){closeModal();state.mobile=false;root.querySelector('.sidebar')?.classList.remove('open');}
 if(event.key==='Tab'&&overlays.children.length){const focus=[...overlays.querySelectorAll('button,input,select,textarea,a[href]')].filter(e=>!e.disabled&&e.getBoundingClientRect().width);const first=focus[0],last=focus[focus.length-1];if(event.shiftKey&&document.activeElement===first){event.preventDefault();last?.focus();}else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first?.focus();}}
});
window.addEventListener('popstate',()=>{if(!canLeaveAssessment()){history.pushState({},'',currentPath);return;}currentPath=location.pathname;closeModal();state.search='';state.filter='all';state.category='all';routeInfo();loadRoute();});
window.addEventListener('beforeunload',event=>{if(state.attempt&&!state.attempt.submitted_at&&saveError){event.preventDefault();event.returnValue='';}});

configureAuthoring({modal,closeModal,refresh,render,navigate});
configureAssessment({modal,closeModal,refresh,render,navigate,replaceRoute:path=>{history.replaceState({},'',path);currentPath=path;routeInfo();}});
try{await refresh();routeInfo();await loadRoute();}catch(error){if(error.status!==401)toast(error.message,true);state.data=null;await loginPage();}
