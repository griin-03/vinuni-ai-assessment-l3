import {state,api,esc,icon,action,link,badge,notice,empty,dateTime,date,categories,field,area,selectField,toast} from './core.js';
import {head} from './views.js';

let hooks={},overview=null,job=null,report=null,poll=null;
export const authoringRoutes=['knowledge','authoring','draft','evaluation'];
export function configureAuthoring(value){hooks=value;}
export function stopAuthoringPoll(){clearTimeout(poll);poll=null;}
export async function loadAuthoring(){
 stopAuthoringPoll();
 if(state.route==='draft')job=await api('ai/drafts/'+state.id);
 else if(state.route==='evaluation')report=await api('ai/evaluation');
 else overview=await api('ai/overview');
}
const status=j=>j.status==='failed'?badge('Xử lý thất bại','red'):j.status==='queued'?badge('Đang chờ','gray'):j.status==='running'?badge('Đang soạn','amber'):j.decision==='draft'?badge('Chờ đối chiếu','blue'):badge(({needs_clarification:'Cần làm rõ',insufficient_evidence:'Thiếu căn cứ',out_of_scope:'Ngoài phạm vi'})[j.decision]||j.decision,'amber');
const kind=j=>j.provider==='extractive'?'Trích xuất theo mẫu':'Mô hình đã cấu hình';
const modeNote=()=>notice('<strong>Xử lý cục bộ · Chưa dùng LLM.</strong> Tìm đoạn bằng từ khóa, trích xuất câu hỏi theo mẫu và kiểm tra nguồn. Đây là baseline để thử quy trình; chưa đại diện cho chất lượng AI.','shield');
const department=d=>d.department_id?state.data.departments.find(p=>p.id===d.department_id)?.name||'Giới hạn lớp / nhóm':'Toàn trường';

export function renderAuthoring(){
 if(state.route==='knowledge')return knowledgeView();
 if(state.route==='authoring')return authoringView();
 if(state.route==='draft')return draftView();
 if(state.route==='evaluation')return evaluationView();
 return '';
}

function knowledgeView(){
 const docs=(overview?.documents||[]).filter(d=>!state.data.settings.education_mvp||categories.includes(d.category));
 return head('Kho học liệu','Nguồn sự thật được quản lý phiên bản và phạm vi trước khi dùng để soạn nội dung.',action('grounded-new-document','Nhập tài liệu','plus'),'NGUỒN & DẪN CHỨNG')+modeNote()+`<div class="grounded-summary mt mb"><div><b>${docs.filter(d=>d.status==='active').length}</b><span>Tài liệu hiện hành</span></div><div><b>TXT · MD</b><span>Định dạng đang hỗ trợ</span></div><div><b>Phiên bản cố định</b><span>Giữ nguyên nội dung để đối chiếu</span></div></div>`+(docs.length?`<div class="panel"><div class="table-wrap"><table><thead><tr><th>Tài liệu</th><th>Phiên bản</th><th>Phạm vi</th><th>Trạng thái</th><th></th></tr></thead><tbody>${docs.map(d=>`<tr><td><strong>${esc(d.title)}</strong><small>${esc(d.category)} · ${d.characters.toLocaleString('vi-VN')} ký tự · ${d.chunks} đoạn ${d.sample_key?'· Dữ liệu mẫu':''}</small></td><td><strong>v${d.version}</strong><small>${esc(d.content_hash.slice(0,12))}</small></td><td>${esc(department(d))}</td><td>${d.status==='archived'?badge('Đã thu hồi','gray'):d.effective_from>new Date().toISOString().slice(0,10)?badge('Chưa hiệu lực','amber'):badge('Được dùng','green',true)}<small>Từ ${date(d.effective_from)}</small></td><td class="table-actions"><div class="row" style="justify-content:flex-end">${action('grounded-source','Đọc nguồn','eye','ghost sm',`data-id="${d.id}"`)}${action('grounded-version','Bản mới','upload','secondary sm',`data-id="${d.id}"`)}${d.status==='active'?action('grounded-archive','Thu hồi','','ghost sm',`data-id="${d.id}" data-version="${d.current_version_id}"`):''}</div></td></tr>`).join('')}</tbody></table></div></div>`:empty('Chưa có học liệu','Nhập tài liệu đã được phép sử dụng. Hệ thống sẽ không tạo thêm thông tin khi thiếu nguồn.',action('grounded-new-document','Nhập tài liệu đầu tiên','plus')));
}

function authoringView(){
 const docs=(overview?.documents||[]).filter(d=>d.status==='active'&&d.effective_from<=new Date().toISOString().slice(0,10)&&(!state.data.settings.education_mvp||categories.includes(d.category)));
 return head('Soạn câu hỏi có dẫn chứng','Một tác vụ: từ tài liệu được phép sử dụng đến câu hỏi đã được giáo viên đối chiếu.',link('/workspace/knowledge','Quản lý nguồn','book','secondary'),'KHÔNG GIAN SOẠN NỘI DUNG')+modeNote()+`<div class="grounded-layout mt"><section class="panel"><div class="panel-head"><div><h2>Tạo bản nháp để kiểm tra</h2><p>Chọn nguồn rõ ràng, không điền đủ số lượng bằng nội dung phỏng đoán</p></div></div><form data-form="grounded-create" class="panel-body"><div data-form-error></div>${field('topic','Chủ đề / kiến thức cần kiểm tra','text','phương trình bậc hai','required maxlength="500" placeholder="Ví dụ: phương trình bậc hai"')}${field('audience','Đối tượng học sinh','text','Học sinh lớp 9','required maxlength="120"')}<div class="form-grid">${selectField('category','Nhóm câu hỏi',categories.map(c=>[c,c]),'Toán')}${field('count','Số câu tối đa','number',3,'required min="1" max="5"')}</div><div class="form-section">Nguồn được phép sử dụng</div><div class="selection-list">${docs.map(d=>`<label class="selection-row"><input type="checkbox" name="document_ids" value="${d.id}" ${d.sample_key==='school-quadratic'?'checked':''}/><span><strong>${esc(d.title)}</strong><small>v${d.version} · ${esc(department(d))}</small></span></label>`).join('')||'<p class="small muted" style="padding:16px">Cần nhập tài liệu trước khi soạn câu hỏi.</p>'}</div><div class="grounded-form-footer"><span class="tiny muted">Tối đa 5 câu / lượt · Không tự xuất bản</span><button class="btn" type="submit" ${docs.length?'':'disabled'}>${icon('file')}Soạn bản nháp</button></div></form></section><aside class="stack"><div class="panel side-details"><h2>Từ nguồn đến câu hỏi</h2><ol class="grounded-steps"><li><b>1</b><div><strong>Giới hạn nguồn</strong><p>Kiểm tra quyền, phiên bản và ngày hiệu lực trước khi tìm đoạn.</p></div></li><li><b>2</b><div><strong>Truy xuất & trích xuất</strong><p>Tìm theo từ khóa; trả ít câu hơn nếu nguồn chưa đủ.</p></div></li><li><b>3</b><div><strong>Kiểm tra dẫn chứng</strong><p>Đối chiếu đoạn trích và đáp án với văn bản gốc.</p></div></li><li><b>4</b><div><strong>Người phụ trách duyệt</strong><p>Kiểm tra ý nghĩa, câu hỏi và phương án nhiễu trước khi lưu ngân hàng.</p></div></li></ol></div>${notice('<strong>Trích dẫn khớp chưa có nghĩa câu hỏi đúng.</strong> Người duyệt cần xác nhận ý nghĩa và chỉ có một đáp án phù hợp.','info')}</aside></div><div class="panel mt"><div class="panel-head"><div><h2>Lịch sử soạn của bạn</h2><p>Truy vết nguồn, trạng thái và quyết định duyệt</p></div></div><div class="table-wrap mt"><table><thead><tr><th>Chủ đề</th><th>Trạng thái</th><th>Thời điểm</th><th></th></tr></thead><tbody>${(overview?.jobs||[]).map(j=>`<tr><td><strong>${esc(j.request.topic||'Chưa có chủ đề cụ thể')}</strong><small>${esc(j.request.audience)} · ${esc(kind(j))}</small></td><td>${status(j)}</td><td>${dateTime(j.created_at)}</td><td class="table-actions">${link('/workspace/draft/'+j.id,'Xem kết quả','chevron','ghost sm')}</td></tr>`).join('')||'<tr><td colspan="4">Chưa có yêu cầu soạn nội dung.</td></tr>'}</tbody></table></div></div>`;
}

function schedulePoll(){
 if(poll||!job||!['queued','running'].includes(job.status))return;
 const id=job.id;
 poll=setTimeout(async()=>{poll=null;if(state.route!=='draft'||state.id!==id)return;try{job=await api('ai/drafts/'+id);hooks.render();schedulePoll();}catch(error){toast(error.message,true);}},900);
}

function draftView(){
 if(!job)return empty('Đang mở bản nháp','Vui lòng chờ.');
 schedulePoll();
 const approved=job.items.filter(i=>i.status==='approved').length;
 return head('Đối chiếu & duyệt câu hỏi',`DR-${String(job.id).padStart(4,'0')} · ${job.request.topic}`,link('/workspace/authoring','Về soạn nội dung','arrowLeft','secondary'),'BẢN NHÁP CẦN NGƯỜI KIỂM TRA')+`<div class="panel grounded-job-head"><div class="between"><div class="row">${status(job)}${badge('Trích xuất cục bộ · Không phải LLM','gray')}</div><span class="small muted">${approved}/${job.items.length} câu đã duyệt</span></div><p>${esc(job.message||'Yêu cầu đã được lưu; có thể rời trang và mở lại để xem kết quả.')}</p>${!job.sources_current?notice('Nguồn đã thay đổi hoặc thu hồi. Các bản nháp chưa duyệt cần được tạo lại từ nguồn hiện hành.','info'):''}</div>`+(['queued','running'].includes(job.status)?`<div class="empty mt"><span class="spinner" style="display:inline-block"></span><h3 style="margin-top:15px">Đang tìm nguồn và kiểm tra trích dẫn</h3><p>Không ghi câu hỏi vào ngân hàng trong bước này.</p></div>`:!job.items.length?`<div class="mt">${empty(job.status==='failed'?'Chưa xử lý được yêu cầu':job.decision==='needs_clarification'?'Cần làm rõ yêu cầu':job.decision==='out_of_scope'?'Yêu cầu nằm ngoài tác vụ':'Chưa đủ căn cứ',job.message,link('/workspace/authoring','Bổ sung yêu cầu hoặc nguồn','arrowLeft'))}</div>`:job.items.map(item=>{
  const check=item.validation,final=['approved','rejected'].includes(item.status);
  return `<article class="panel grounded-item mt"><div class="panel-head"><div class="row">${badge('CÂU '+item.ordinal,'gray')}${item.status==='approved'?badge('Đã vào ngân hàng','green'):item.status==='rejected'?badge('Đã từ chối','gray'):check.valid?badge('Trích dẫn khớp · Chưa duyệt','blue'):badge('Bị chặn kiểm tra','red')}</div><span class="tiny muted">IT-${item.id} · revision ${item.revision}</span></div><div class="grounded-review-grid"><section class="grounded-question"><h3>${esc(item.question)}</h3><div class="grounded-options">${item.options.map((o,i)=>`<div class="${i===item.correct?'proposed':''}"><b>${String.fromCharCode(65+i)}</b><span>${esc(o)}</span>${i===item.correct?icon('check'):''}</div>`).join('')}</div><p class="tiny muted">Màu xanh đánh dấu đáp án đề xuất; người duyệt cần kiểm tra lại.</p>${check.errors.length?`<div class="field-error mt">${check.errors.map(e=>esc(errorLabel(e))).join('<br/>')}</div>`:''}</section><aside class="grounded-evidence"><div class="between"><strong class="small">${icon('book')} Dẫn chứng để đối chiếu</strong><span class="tiny muted">${check.evidence.length} nguồn</span></div>${check.evidence.map(e=>`<div class="evidence-quote"><div class="between"><b>${esc(e.title)}</b>${badge('v'+e.version,'gray')}</div><blockquote>${esc(e.quote)}</blockquote><div class="between"><span class="tiny muted">Dòng ${e.line_start}–${e.line_end} · ${esc(e.content_hash.slice(0,8))}</span>${action('grounded-source','Mở nguồn','eye','ghost sm',`data-id="${e.document_id}" data-version="${e.version_id}" data-quote="${esc(e.quote)}"`)}</div></div>`).join('')||'<p class="small muted mt">Chưa có trích dẫn vượt kiểm tra; không được duyệt câu này.</p>'}<p class="tiny muted" style="line-height:1.8;margin-top:15px">Kiểm tra tự động xác nhận nguồn và chuỗi trích dẫn. Ý nghĩa, mức độ phù hợp và chất lượng phương án nhiễu do người duyệt xác nhận.</p></aside></div><div class="grounded-item-footer"><span class="tiny muted">${final?'Quyết định: '+esc(item.review_comment):'Chưa có câu hỏi nào được xuất bản tự động.'}</span><div class="row">${!final?action('grounded-edit-item','Sửa nháp','edit','secondary sm',`data-id="${item.id}"`)+action('grounded-reject','Từ chối','','ghost sm',`data-id="${item.id}"`)+action('grounded-approve','Đối chiếu & duyệt','check','sm',`data-id="${item.id}" ${!check.valid||!job.sources_current?'disabled':''}`):item.status==='approved'?link('/workspace/questions','Mở ngân hàng','arrow','ghost sm'):''}</div></div></article>`;
 }).join(''));
}

function errorLabel(code){return ({quote_mismatch:'Đoạn trích không khớp nguồn.',citation_not_retrieved:'Trích dẫn nằm ngoài tập đoạn đã truy xuất.',missing_citation:'Chưa có dẫn chứng.',correct_answer_not_grounded:'Đáp án đúng chưa được trích dẫn hỗ trợ bằng văn bản.',duplicate_options:'Các phương án bị trùng nội dung.',unsafe_source:'Nguồn có dấu hiệu chứa chỉ dẫn cho mô hình.',unsafe_output:'Câu hỏi chứa chỉ dẫn ngoài tác vụ.',invalid_options:'Cần bốn phương án hợp lệ.',invalid_correct:'Chưa xác định đúng một đáp án.',invalid_question:'Nội dung câu hỏi chưa hợp lệ.'})[code]||code;}

function evaluationView(){
 const r=report||{status:'not_run'};
 return head('Đánh giá & bằng chứng sản phẩm','Tách kết quả kiểm thử hệ thống, chất lượng mô hình và bằng chứng nhu cầu thật.',link('/workspace/authoring','Về soạn nội dung','arrowLeft','secondary'),'ĐO LƯỜNG CÓ NGUỒN GỐC')+notice('<strong>Chưa có đánh giá LLM thực.</strong> Bộ 38 ca cơ chế được xây trước khi chuyển sang THCS/THPT; chưa kiểm định chất lượng câu hỏi phổ thông. Bộ ca hiện tại là dữ liệu tổng hợp do dự án tự soạn. Không thay thế ca thật, khảo sát người dùng hoặc xác nhận chuyên môn.','info')+`<div class="grounded-summary mt mb"><div><b>${r.total_cases??'—'}</b><span>Ca kiểm tra tổng hợp</span></div><div><b>${r.passed_cases??'—'}/${r.total_cases??'—'}</b><span>Vượt kiểm tra cơ chế</span></div><div><b>Chưa chạy</b><span>Chất lượng sinh bằng LLM</span></div><div><b>Chưa thu thập</b><span>Bằng chứng người dùng thật</span></div></div><div class="panel mb"><div class="panel-head"><div><h2>Kết quả kiểm tra truy xuất, trích dẫn và kiểm soát rủi ro</h2><p>${r.generated_at?'Chạy lúc '+dateTime(r.generated_at):'Chạy npm run evaluate:rag để sinh báo cáo'}</p></div>${badge(r.status==='passed'?'Vượt quality bar cơ chế':r.status==='not_run'?'Chưa chạy':'Có lỗi cần xử lý',r.status==='passed'?'green':'amber')}</div><div class="table-wrap mt"><table><thead><tr><th>Nhóm kiểm tra</th><th>Đạt / Tổng</th><th>Tỷ lệ</th><th>Mục tiêu</th></tr></thead><tbody>${(r.metrics||[]).map(m=>`<tr><td><strong>${esc(m.label)}</strong></td><td>${m.passed}/${m.total}</td><td>${m.rate}%</td><td>≥ ${m.target}%</td></tr>`).join('')||'<tr><td colspan="4">Chưa có kết quả được ghi nhận.</td></tr>'}</tbody></table></div></div><div class="grounded-layout"><div class="panel side-details"><h2>Những phần chưa được chứng minh</h2><div class="kv"><span>Ca từ công việc thật</span><b>0 ca đã xác nhận</b></div><div class="kv"><span>Phỏng vấn / khảo sát</span><b>Chưa có</b></div><div class="kv"><span>Giảm thời gian soạn đề</span><b>Chưa đo</b></div><div class="kv"><span>Độ đúng ngữ nghĩa của LLM</span><b>Chưa chạy</b></div><p class="small muted mt" style="line-height:1.9">Chỉ đánh dấu hoàn tất khi có nguồn truy nguyên và dữ liệu đo. Không dùng tỷ lệ vượt test phần mềm để kết luận chất lượng AI hay mức độ đáp ứng rubric.</p></div><div class="panel side-details"><h2>Quality bar trước khi đưa nội dung vào sử dụng</h2><ul class="grounded-quality"><li>${icon('check')}Trích dẫn thuộc nguồn đúng quyền và đúng phiên bản.</li><li>${icon('check')}Không có câu hỏi vào ngân hàng khi chưa có người duyệt.</li><li>${icon('check')}Từ chối khi không đủ nguồn; không tự bù để đủ số lượng.</li><li>${icon('check')}Đo riêng chất lượng ngữ nghĩa bằng ca thật và người có chuyên môn.</li></ul></div></div>`;
}

async function sourceDialog(id,version,quote=''){
 const result=await api(version?`knowledge/documents/${id}/versions/${version}`:`knowledge/documents/${id}`);
 let content=esc(result.version.content);if(quote)content=content.replace(esc(quote),'<mark>'+esc(quote)+'</mark>');
 hooks.modal(result.document.title,`Phiên bản ${result.version.version} · hiệu lực ${date(result.version.effective_from)} · ${department(result.document)}`,`<div class="between mb"><span class="tiny muted">SHA-256 ${esc(result.version.content_hash.slice(0,20))}</span>${result.document.current_version_id!==result.version.id?badge('Phiên bản lịch sử','amber'):badge('Phiên bản hiện tại','green')}</div>${result.chunks.some(c=>c.risk_flags.length)?notice('Một số đoạn có dấu hiệu chứa chỉ dẫn cho mô hình. Các đoạn được đánh dấu không được dùng trong truy xuất tự động. Đây là kiểm tra hỗ trợ, không phải bảo đảm phát hiện mọi injection.','info'):''}<pre class="source-reader">${content}</pre><div class="form-section">Các phiên bản đã lưu</div><div class="row" style="flex-wrap:wrap">${result.versions.map(v=>action('grounded-source','v'+v.version+' · '+date(v.created_at),'file','secondary sm',`data-id="${id}" data-version="${v.id}"`)).join('')}</div>`,'',true);
}

async function documentForm(id){
 const existing=id?await api('knowledge/documents/'+id):null;
 const scopes=[['','Toàn trường'],...state.data.departments.filter(d=>state.data.user.role==='admin'||d.id===state.data.user.department_id).map(d=>[d.id,d.name])];
 hooks.modal(existing?'Tạo phiên bản tài liệu mới':'Nhập học liệu','Nội dung nằm tại máy đang chạy dự án; chưa có kết nối dịch vụ mô hình bên ngoài.',`<input type="hidden" name="id" value="${id||''}"/><input type="hidden" name="expected_version_id" value="${existing?.version.id||''}"/>${field('title','Tên tài liệu','text',existing?.document.title||'','required minlength="5" maxlength="160"')}<div class="form-grid">${selectField('category','Nhóm nội dung',categories.map(c=>[c,c]),existing?.document.category||'Toán')}${selectField('department_id','Phạm vi được phép sử dụng',scopes,existing?.document.department_id||'')}${field('effective_from','Ngày hiệu lực','date',existing?.version.effective_from||new Date().toISOString().slice(0,10),'required')}<div class="form-field"><label for="grounded-file">Đọc nội dung từ TXT / Markdown</label><input class="input" id="grounded-file" type="file" accept=".txt,.md,text/plain,text/markdown" data-grounded-file/><small>Tối đa 100 KB. Không tự đọc PDF hoặc gửi tệp ra ngoài.</small></div></div>${area('content','Nội dung văn bản',existing?.version.content||'','required minlength="80" maxlength="100000" style="min-height:230px" placeholder="Dán nội dung học liệu, giữ đề mục và công thức cần đối chiếu…"')}<label class="check-row"><input type="checkbox" name="source_confirmed" required/>Tôi xác nhận có quyền sử dụng và đã kiểm tra nội dung, phạm vi, ngày hiệu lực.</label><div class="mt">${notice('Phiên bản cũ được giữ nguyên để truy vết. Bản nháp chưa duyệt dựa trên phiên bản cũ sẽ cần tạo lại.','file')}</div>`,'grounded-document',true,'Lưu nguồn đã xác nhận');
 if(existing)document.querySelector('#overlay-root [name="department_id"]').disabled=true;
}

export async function authoringAction(button){
 const name=button.dataset.action,id=Number(button.dataset.id);
 if(!name?.startsWith('grounded-'))return false;
 if(name==='grounded-new-document')await documentForm();
 else if(name==='grounded-version')await documentForm(id);
 else if(name==='grounded-source')await sourceDialog(id,Number(button.dataset.version)||null,button.dataset.quote||'');
 else if(name==='grounded-archive')hooks.modal('Thu hồi nguồn tài liệu?','Nguồn sẽ dừng được dùng cho yêu cầu soạn mới.',`<input type="hidden" name="id" value="${id}"/><input type="hidden" name="version" value="${button.dataset.version}"/>${notice('Lịch sử và trích dẫn được giữ lại. Các bản nháp chưa duyệt và đợt khảo thí mới có sử dụng nguồn này sẽ bị chặn để kiểm tra lại.','info')}`,'grounded-archive',false,'Xác nhận thu hồi');
 else if(name==='grounded-approve'||name==='grounded-reject'){
  const item=job.items.find(i=>i.id===id),approve=name==='grounded-approve';
  hooks.modal(approve?'Đối chiếu trước khi lưu ngân hàng':'Từ chối bản nháp',`IT-${id} · ${job.request.topic}`,`<input type="hidden" name="id" value="${id}"/><input type="hidden" name="revision" value="${item.revision}"/><input type="hidden" name="decision" value="${approve?'approve':'reject'}"/>${approve?`<div class="stack mb"><label class="check-row"><input type="checkbox" name="grounding_checked" required/>Tôi đã đọc nguồn và xác nhận ý nghĩa của câu hỏi, đáp án đúng được hỗ trợ.</label><label class="check-row"><input type="checkbox" name="options_checked" required/>Tôi đã kiểm tra bốn phương án khác nhau, chỉ có một đáp án phù hợp và nội dung đúng đối tượng.</label></div>`:''}${area('comment',approve?'Ghi nhận kết quả kiểm tra':'Lý do từ chối','','required minlength="5" maxlength="1000"')}<div class="mt">${notice(approve?'Thao tác này chỉ thêm câu hỏi vào ngân hàng. Không tự tạo, mở đợt hoặc giao bài cho học sinh.':'Bản nháp đã từ chối được giữ lại để truy vết.','shield')}</div>`,'grounded-review',false,approve?'Duyệt vào ngân hàng':'Ghi nhận từ chối');
 }else if(name==='grounded-edit-item'){
  const item=job.items.find(i=>i.id===id);
  hooks.modal('Sửa bản nháp & kiểm tra lại','Dẫn chứng được giữ nguyên; đáp án đúng vẫn phải có trong đoạn nguồn.',`<input type="hidden" name="id" value="${id}"/><input type="hidden" name="revision" value="${item.revision}"/>${area('question','Câu hỏi',item.question,'required minlength="12" maxlength="800"')}${item.options.map((o,i)=>field('option_'+i,'Phương án '+String.fromCharCode(65+i),'text',o,'required minlength="2" maxlength="1000"')).join('')}${selectField('correct','Đáp án đúng',[0,1,2,3].map(i=>[i,String.fromCharCode(65+i)]),item.correct)}`,'grounded-edit',true,'Lưu & kiểm tra lại');
 }
 return true;
}

export async function authoringSubmit(form){
 const kind=form.dataset.form;if(!kind?.startsWith('grounded-'))return false;
 const fd=new FormData(form),v=Object.fromEntries(fd),button=form.querySelector('[type="submit"]');button.disabled=true;
 try{
  if(kind==='grounded-document'){
   await api(v.id?`knowledge/documents/${v.id}/versions`:'knowledge/documents',{title:v.title,content:v.content,category:v.category,department_id:v.department_id?Number(v.department_id):null,expected_version_id:Number(v.expected_version_id)||null,effective_from:v.effective_from,source_confirmed:fd.has('source_confirmed')});
   hooks.closeModal();await loadAuthoring();hooks.render();toast('Đã lưu phiên bản nguồn có thể đối chiếu.');
  }else if(kind==='grounded-create'){
   const result=await api('ai/drafts',{request_key:crypto.randomUUID(),topic:v.topic,audience:v.audience,count:Number(v.count),category:v.category,document_ids:fd.getAll('document_ids').map(Number),provider:'extractive'});hooks.navigate('/workspace/draft/'+result.id);
  }else if(kind==='grounded-archive'){
   await api(`knowledge/documents/${v.id}/archive`,{expected_version_id:Number(v.version)});hooks.closeModal();await loadAuthoring();hooks.render();toast('Đã thu hồi nguồn khỏi truy xuất mới.');
  }else if(kind==='grounded-review'){
   const result=await api(`ai/items/${v.id}/review`,{decision:v.decision,expected_revision:Number(v.revision),comment:v.comment,grounding_checked:fd.has('grounding_checked'),options_checked:fd.has('options_checked')});hooks.closeModal();await hooks.refresh();await loadAuthoring();hooks.render();toast(result.question_id?'Đã duyệt vào ngân hàng câu hỏi.':'Đã ghi nhận từ chối.');
  }else if(kind==='grounded-edit'){
   await api(`ai/items/${v.id}/edit`,{expected_revision:Number(v.revision),question:v.question,options:[0,1,2,3].map(i=>v['option_'+i]),correct:Number(v.correct)});hooks.closeModal();await loadAuthoring();hooks.render();toast('Đã lưu và kiểm tra lại bản nháp.');
  }
 }catch(error){const target=form.querySelector('[data-form-error]');if(target){target.className='field-error';target.textContent=error.message;}else toast(error.message,true);}
 finally{if(button.isConnected)button.disabled=false;}
 return true;
}

export async function authoringChange(event){
 if(!event.target.matches('[data-grounded-file]'))return;
 const file=event.target.files?.[0];if(!file)return;
 if(file.size>100000||!(/\.(txt|md)$/i).test(file.name)){toast('Chọn TXT hoặc Markdown tối đa 100 KB.',true);return;}
 const content=await file.text();if(content.includes('\0')){toast('Không đọc được tệp như văn bản.',true);return;}
 document.querySelector('#overlay-root [name="content"]').value=content;
}
