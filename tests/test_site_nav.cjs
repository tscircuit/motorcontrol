const fs=require('node:fs'),assert=require('node:assert/strict');
const read=file=>fs.readFileSync(__dirname+'/../dist/'+file,'utf8');
const dashboards=['bench.html','single-motor.html','gantry.html','three-axis-gantry.html','bldc.html'];
const pages=['index.html',...dashboards,'firmware.html','assets.html'];
const links=html=>Array.from(html.matchAll(/<a\b[^>]*>/g),m=>({href:/href="([^"]*)"/.exec(m[0])[1],current:/aria-current="([^"]*)"/.exec(m[0])?.[1]}));
const section=(html,name)=>new RegExp(`<nav class="${name}"[^>]*>(.*?)</nav>`,'s').exec(html)?.[1];
const primary=['/','/','/#dashboards','firmware.html','assets.html','manual/NEMA17-Kit-Booklet.pdf','https://github.com/tscircuit/motorcontrol'];
const current={'index.html':'/','firmware.html':'firmware.html','assets.html':'assets.html'};
for(const page of pages){
 const html=read(page),site=links(section(html,'siteNav'));
 assert.ok(html.includes('href="nav.css"'),page);
 assert.deepEqual(site.map(a=>a.href),primary,page);
 for(const a of site)if(a.href.endsWith('.html')||a.href.endsWith('.pdf'))assert.ok(fs.existsSync(__dirname+'/../dist/'+a.href),a.href);
 const marked=site.filter(a=>a.current);
 if(dashboards.includes(page)){
  assert.deepEqual(marked,[{href:'/#dashboards',current:'true'}],page);
  const strip=links(section(html,'dashboardNav'));
  assert.deepEqual(strip.map(a=>a.href),dashboards,page);
  assert.deepEqual(strip.filter(a=>a.current),[{href:page,current:'page'}],page);
 }else{
  assert.deepEqual(marked,[{href:current[page],current:'page'}],page);
  assert.equal(section(html,'dashboardNav'),undefined,page);
 }
}
console.log('PASS every page shares the site header and dashboard pages list every dashboard');

const home=read('index.html');
assert.match(home,/id="dashboards"/);assert.match(home,/id="first-move"/);
const listed=links(/<ul class="dashboards">(.*?)<\/ul>/s.exec(home)[1]).map(a=>a.href);
assert.deepEqual(listed,dashboards);
assert.match(read('bench.html'),/href="\/#first-move"/);
console.log('PASS get started page links to every dashboard and the bench links back to the quick start');

const note={textContent:'',classList:{add(name){this.name=name;}}};
const run=navigator=>{note.textContent='';note.classList.name='';new Function('navigator','document',read('home.js'))(navigator,{getElementById:()=>note});};
run({serial:{}});assert.equal(note.textContent,'');
run({});assert.match(note.textContent,/Chrome or Edge/);assert.equal(note.classList.name,'unsupported');
console.log('PASS get started page warns only when the browser lacks Web Serial');
