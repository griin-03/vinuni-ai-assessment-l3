import {icon} from './icons.js';
export {icon};
export const state={data:null,public:null,route:'overview',id:null,search:'',filter:'all',category:'all',chart:'department',csrf:'',attempt:null,question:0,flags:new Set(),mobile:false};
export const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
export const initials=name=>String(name).trim().split(/\s+/).slice(-2).map(s=>s[0]).join('').toUpperCase();
export const avatar=(name,id=0,size='')=>`<span class="avatar c${id%6} ${size}" aria-hidden="true">${esc(initials(name))}</span>`;
export const date=value=>value?new Intl.DateTimeFormat('vi-VN',{day:'2-digit',month:'2-digit',year:'numeric'}).format(new Date(value)):'—';
export const shortDate=value=>new Intl.DateTimeFormat('vi-VN',{day:'2-digit',month:'2-digit'}).format(new Date(value));
export const dateTime=value=>value?new Intl.DateTimeFormat('vi-VN',{day:'2-digit',month:'2-digit',year:'numeric',hour:'2-digit',minute:'2-digit'}).format(new Date(value)):'—';
export const number=value=>new Intl.NumberFormat('vi-VN').format(value);
export const can=key=>state.data?.permissions.includes(key);
export const staff=()=>can('courses.manage');
export const action=(name,label,ico='',cls='',extra='')=>`<button type="button" class="btn ${cls}" data-action="${esc(name)}" ${extra}>${ico?icon(ico):''}${esc(label)}</button>`;
export const link=(href,label,ico='',cls='')=>`<a class="btn ${cls}" href="${esc(href)}">${ico?icon(ico):''}${esc(label)}</a>`;
export const badge=(label,color='blue',dot=false)=>`<span class="badge ${color}">${dot?'<i class="dot"></i>':''}${esc(label)}</span>`;
export const progress=(value,color='')=>`<div class="progress ${color}" role="progressbar" aria-label="Tiến độ" aria-valuenow="${value}" aria-valuemin="0" aria-valuemax="100"><i style="width:${Math.min(100,Math.max(0,value))}%"></i></div>`;
export const percent=c=>c.enrollment?Math.round(c.enrollment.completed.length/Math.max(1,c.lessons.length)*100):0;
export const notice=(message,ico='info')=>`<div class="notice">${icon(ico)}<span>${message}</span></div>`;
export const empty=(title,message,button='',ico='folder')=>`<div class="empty">${icon(ico)}<h3>${esc(title)}</h3><p>${esc(message)}</p>${button}</div>`;
export const sample=()=>state.data?.settings.demo==='1'?`<span class="sample-note">${icon('info')}Dữ liệu mẫu</span>`:'';
export const categories=['Toán','Ngữ văn','Tiếng Anh','Vật lý','Hóa học','Sinh học','Lịch sử','Địa lý','Tin học','Khoa học tự nhiên','Giáo dục công dân'];
export const categoryIcon=c=>({'Hội nhập':'book','Tuân thủ':'shield','Nghiệp vụ':'layers','Năng lực':'target'}[c]||'book');
export const field=(name,label,type='text',value='',options='')=>`<div class="form-field"><label for="f-${name}">${label}</label><input class="input" id="f-${name}" name="${name}" type="${type}" value="${esc(value)}" ${options}/></div>`;
export const selectField=(name,label,options,selected='')=>`<div class="form-field"><label for="f-${name}">${label}</label><select id="f-${name}" name="${name}">${options.map(([value,title])=>`<option value="${esc(value)}" ${String(value)===String(selected)?'selected':''}>${esc(title)}</option>`).join('')}</select></div>`;
export const area=(name,label,value='',attrs='')=>`<div class="form-field"><label for="f-${name}">${label}</label><textarea id="f-${name}" name="${name}" ${attrs}>${esc(value)}</textarea></div>`;
export const api=async(path,body,method)=>{
 const response=await fetch('/api/workspace/'+path,{method:method||(body===undefined?'GET':'POST'),credentials:'same-origin',headers:{...(body===undefined?{}:{'Content-Type':'application/json'}),...(state.csrf?{'X-CSRF-Token':state.csrf}:{})},...(body===undefined?{}:{body:JSON.stringify(body)})});
 const result=await response.json();
 if(!response.ok){const error=new Error(result.error||'Không thể hoàn thành yêu cầu.');error.status=response.status;throw error;}
 return result;
};
export function toast(message,error=false){
 const node=document.createElement('div');node.className='toast'+(error?' error':'');node.innerHTML=icon(error?'info':'check')+`<span>${esc(message)}</span>`;document.getElementById('toast-root').append(node);setTimeout(()=>node.remove(),4500);
}
export const statusCourse=c=>c.status==='draft'?badge('Bản nháp','gray'):badge('Đã xuất bản','green',true);
export function statusExam(exam){
 if(exam.status==='draft')return badge('Bản nháp','gray');
 if(exam.status==='closed')return badge('Đã đóng','gray');
 if(new Date(exam.due)<new Date())return badge('Đã hết hạn','gray');
 return badge('Đang mở','green',true);
}
export const searched=(value,search=state.search)=>String(value).normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/đ/g,'d').toLowerCase().includes(search.normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/đ/g,'d').toLowerCase());
