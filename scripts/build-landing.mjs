import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {parse} from 'acorn';
import {oceanColors} from './ocean-palette.mjs';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const original=path.join(root,'vendor/landing-baseline');
const content=JSON.parse(fs.readFileSync(path.join(root,'content/vinassess.vi.json'),'utf8'));
const assets={
  '/_next/static/media/fervid-logo-white-brand.2j1fe5p7zmdh0.png':'/assets/brand/vinassess-logo-light.svg',
  '/_next/static/media/fervid-logo.3qd6lfl9j27yy.png':'/assets/brand/vinassess-logo.svg',
  '/_next/static/media/logo.34vzqlxdoycah.png':'/assets/brand/vinassess-logo.svg',
  '/images/home/fervid-logo.png':'/assets/brand/vinassess-logo.svg',
  '/images/auth-logo.png':'/assets/brand/vinassess-logo.svg',
  '/_next/static/media/tvc-cover.2cc6ju8k-hvfy.webp':'/assets/illustrations/training-overview.svg',
  '/images/landing-feedback/x-project-desktop.webp':'/assets/illustrations/workspace.svg',
  '/images/common/bct-notified.webp':'/assets/brand/learning-badge.svg',
  '/images/covers/banners/thpt.webp':'/assets/illustrations/onboarding.svg',
  '/images/covers/banners/dgnl.webp':'/assets/illustrations/assessment.svg',
  '/images/covers/banners/ielts.webp':'/assets/illustrations/skills.svg',
  '/images/covers/banners/sat.webp':'/assets/illustrations/compliance.svg',
  '/uploads/website_ui/5fd605aec997078639ad3d790edf30c1.mp4':'#solutions',
  'https://fervid.vn/og-home.png':'http://127.0.0.1:4173/assets/illustrations/training-overview.svg',
};
const blogImages=['1792435805_2566d3a0','1792435719_83dff24a','1792435639_4776ffc4','1792435559_23cd95f5','1792435293_429ebc97','1792435216_bbee0761'];
blogImages.forEach((id,i)=>{
  assets[`https://fervid.vn/uploads/fervid/blogs/blog_${id}.webp`]=`/assets/illustrations/article-${i+1}.svg`;
});
const replacements={...content,...assets};
for(const [old,value] of Object.entries(assets)){
  if(old.startsWith('/'))replacements['https://fervid.vn'+old]=value;
}
const entries=Object.entries(replacements).sort((a,b)=>b[0].length-a[0].length);
const escapeRE=s=>s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
const forms=new Map();
for(const [old,value] of entries){
  forms.set(old,value);
  forms.set(encodeURIComponent(old),encodeURIComponent(value));
  let a=old,b=value;
  for(let level=0;level<3;level++){
    a=JSON.stringify(a).slice(1,-1);b=JSON.stringify(b).slice(1,-1);
    forms.set(a,b);
  }
}
const translationRE=new RegExp([...forms.keys()].sort((a,b)=>b.length-a.length).map(escapeRE).join('|'),'g');
function translate(value){
  if(/^[0-9a-f]+:/i.test(value))return rewriteFlight(value);
  if(value.includes('window.gtag')&&value.includes('G-W4R0HG4YH9'))return '';
  if(value.startsWith('/icon.svg'))return '/assets/brand/vinassess-icon.svg';
  let result=value.replace(translationRE,old=>forms.get(old));
  result=result.replace(/\b\d[\d.,]*\+? (?:câu|đề) trong kho/g,'Nội dung minh họa');
  result=result.replace(/DIGITAL SAT|Digital SAT/g,'Luyện tập THPT');
  if(result==='mailto:admin@fervid.vn'||result==='mailto:Trao đổi về nhu cầu kiểm tra')return '#home-cta-title';
  if(result==='https://fervid.vn'||result==='https://fervid.vn/')return 'http://127.0.0.1:4173/';
  if(/^(?:https?:\/\/)?(?:www\.)?(?:facebook\.com|tiktok\.com|zalo\.me|online\.gov\.vn|giaoduc\.net\.vn|pmc\.ncbi\.nlm\.nih\.gov|tuoitre\.vn)/.test(result))return '#home-cta-title';
  const routes={
    '/login':'/login','/register':'/workspace','/high-school-exams':'#solutions','/high-school-exams/practice':'#solutions',
    '/competency-assessment':'#solutions','/ielts':'#solutions','/sat':'#solutions','/exams':'#solutions',
    '/cslt':'#ferd-loop-heading','/sotay':'#home-latest-posts-title','/dichvu':'#home-cta-title',
    '/blogs':'#home-latest-posts-title',
  };
  if(Object.hasOwn(routes,result))return routes[result];
  if(result.startsWith('/pages/'))return '#home-cta-title';
  if(result.startsWith('/blogs/'))return '#home-latest-posts-title';
  return result;
}

function translateData(value){
  if(typeof value==='string'){
    if(value.includes('"@context"')){
      try{return JSON.stringify(translateData(JSON.parse(value)));}catch{}
    }
    return translate(value);
  }
  if(Array.isArray(value))return value.map(translateData);
  if(value?.['@type']==='Organization')return {'@context':'https://schema.org','@type':'Organization',name:'VinAssess',description:'Nền tảng kiểm tra & ôn tập dành cho học sinh THCS, THPT.'};
  if(value?.['@type']==='WebSite')return {'@context':'https://schema.org','@type':'WebSite',name:'VinAssess',url:'http://127.0.0.1:4173/'};
  if(value&&typeof value==='object')return Object.fromEntries(Object.entries(value).map(([key,item])=>[key,translateData(item)]));
  return value;
}
function rewriteFlight(value){
  return value.split('\n').map(line=>{
    const match=line.match(/^([0-9a-f]+:)([A-Z]*)([\s\S]*)$/i);
    if(!match)return line;
    try{return match[1]+match[2]+JSON.stringify(translateData(JSON.parse(match[3])));}
    catch{return line.replace(translationRE,old=>forms.get(old));}
  }).join('\n');
}

function rewriteJS(source, transform=translate){
  const tree=parse(source,{ecmaVersion:'latest',sourceType:'script',allowReturnOutsideFunction:true});
  const edits=[];
  function visit(node){
    if(!node||typeof node!=='object')return;
    if(node.type==='TemplateLiteral'&&/^\/blogs\//.test(node.quasis[0]?.value?.cooked??'')){
      edits.push({start:node.start,end:node.end,text:JSON.stringify('#home-latest-posts-title')});
      return;
    }
    if(node.type==='Literal'&&typeof node.value==='string'){
      const value=transform(node.value);
      if(value!==node.value)edits.push({start:node.start,end:node.end,text:JSON.stringify(value)});
    }
    if(node.type==='TemplateElement'&&transform===oceanColors){
      const value=transform(node.value.raw);
      if(value!==node.value.raw)edits.push({start:node.start,end:node.end,text:value});
    }
    for(const [key,value] of Object.entries(node)){
      if(key==='start'||key==='end')continue;
      if(Array.isArray(value))value.forEach(visit);
      else if(value&&typeof value==='object')visit(value);
    }
  }
  visit(tree);
  for(const edit of edits.sort((a,b)=>b.start-a.start))source=source.slice(0,edit.start)+edit.text+source.slice(edit.end);
  return source;
}

const unescapeHTML=s=>s.replace(/&amp;/g,'&').replace(/&quot;/g,'"').replace(/&#x27;|&#39;/g,"'").replace(/&lt;/g,'<').replace(/&gt;/g,'>');
const escapeHTML=s=>s.replace(/&/g,'&amp;').replace(/"/g,'&quot;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
function markup(source){
  return source.replace(/<[^>]*>|[^<]+/g,part=>{
    if(part.startsWith('<'))return part.replace(/\b(href|src|srcset|imageSrcSet|alt|title|aria-label|content)=("[^"]*"|'[^']*')/gi,(match,name,quoted)=>{
      const value=unescapeHTML(quoted.slice(1,-1));
      const changed=translate(value);
      return changed===value?match:`${name}="${escapeHTML(changed)}"`;
    });
    const decoded=unescapeHTML(part),value=translate(decoded);
    return value===decoded?part:escapeHTML(value);
  });
}
function rewriteHTML(source){
  // Give the existing catalogue a stable destination for the landing page CTAs.
  source=source.replace(/<h2([^>]*)>Chọn kỳ thi và/, '<h2$1 id="solutions">Chọn kỳ thi và');
  source=source.replace(/<a([^>]*?)href="\/cdn-cgi\/l\/email-protection#[^"]*"([^>]*)>[\s\S]*?<\/a>/g,'<a$1href="#home-cta-title"$2>Trao đổi về nhu cầu học tập</a>');
  source=source.replace(/<script[^>]*src="\/cdn-cgi\/scripts[^>]*><\/script>/g,'');
  let cursor=0,result='';
  const protectedTags=/<(script|style)\b[^>]*>[\s\S]*?<\/\1>/gi;
  for(const match of source.matchAll(protectedTags)){
    result+=markup(source.slice(cursor,match.index));
    const block=match[0];
    if(match[1].toLowerCase()==='style')result+=block;
    else{
      const start=block.indexOf('>')+1,end=block.lastIndexOf('</');
      const code=block.slice(start,end);
      let rewritten=code;
      if(code.trim())rewritten=block.slice(0,start).includes('application/ld+json')?JSON.stringify(translateData(JSON.parse(code))):rewriteJS(code);
      result+=markup(block.slice(0,start))+rewritten+block.slice(end);
    }
    cursor=match.index+block.length;
  }
  result+=markup(source.slice(cursor));
  result=result.replace(/<link rel="icon"[^>]*>/g,'<link rel="icon" href="/assets/brand/vinassess-icon.svg" type="image/svg+xml"/>');
  result=result.replace(/<meta name="description"[^>]*>/g,'<meta name="description" content="VinAssess – Nền tảng kiểm tra và ôn tập THCS, THPT. Giáo viên soạn đề, giao phòng thi và xem nội dung học sinh cần ôn lại."/>');
  result=result.replace('</head>','<link rel="stylesheet" href="/assets/css/vinassess.css"/></head>');
  return result;
}

let files=0;
const uiBundles=new Set([
  '0x_9qyomipz9i.js','2-8tgfv7419gp.js','3d-0yqad75t4q.js',
  '0n7484kbibtsn.js','1_57ciyb90ngr.js','23dl1xcfos8g2.js',
  '2b6kvtx8nahfz.js','29lql5mpzx_ps.js','0kaea-j6pqlfz.js',
]);
for(const name of fs.readdirSync(path.join(original,'_next/static/chunks'))){
  if(name.endsWith('.css')){
    const css=fs.readFileSync(path.join(original,'_next/static/chunks',name),'utf8');
    fs.writeFileSync(path.join(root,'_next/static/chunks',name),oceanColors(css));
    continue;
  }
  if(!name.endsWith('.js'))continue;
  let source=fs.readFileSync(path.join(original,'_next/static/chunks',name),'utf8');
  if(uiBundles.has(name))source=rewriteJS(source);
  if(name==='2-8tgfv7419gp.js'){
    source=source.replace('countUp:{to:1e5,suffix:"+",grouping:!0}','countUp:{to:4,suffix:"",grouping:!0}');
    source=source.replace('countUp:{to:1e3,suffix:"+",grouping:!0}','countUp:{to:11,suffix:"",grouping:!0}');
    source=source.replace('to:62.7,decimals:1,suffix:"%"','to:0,format:()=>"Có nguồn",suffix:""');
    source=source.replace('to:76.9,decimals:1,suffix:"%"','to:0,format:()=>"Giáo viên",suffix:""');
    source=source.replace('to:90,prefix:"≈",suffix:"%"','to:0,format:()=>"Ôn tập",prefix:"",suffix:""');
    source=source.replace('variant:"h4",component:"h2",sx:{color:"neutral.700",maxWidth:617','id:"solutions",variant:"h4",component:"h2",sx:{color:"neutral.700",maxWidth:617');
    source=source.replace('onClick:()=>{g(!1),x(!0)}','onClick:()=>document.getElementById("solutions")?.scrollIntoView({behavior:"smooth"})');
    source=source.replace('className:"fv-3d",color:"primary",size:"medium",children:','className:"fv-3d",color:"primary",size:"medium",onClick:()=>document.getElementById("home-tvc")?.scrollIntoView({behavior:"smooth"}),children:');
  }
  // The lazy-loaded loop renderer has its own WebGL and canvas colors.
  if(uiBundles.has(name)||name==='1czneu6kcshpn.js')source=rewriteJS(source,oceanColors);
  fs.writeFileSync(path.join(root,'_next/static/chunks',name),source);files++;
}
fs.writeFileSync(path.join(root,'index.html'),oceanColors(rewriteHTML(fs.readFileSync(path.join(original,'index.html'),'utf8'))));
console.log(`Built VinAssess content: ${files} JavaScript bundles + landing HTML. Reproducible baseline: vendor/landing-baseline/.`);
