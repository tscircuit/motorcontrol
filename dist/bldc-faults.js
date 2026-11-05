(function(root){
'use strict';
const gateBits=[[28,'VDS overcurrent'],[27,'Sense overcurrent'],[26,'Bootstrap undervoltage'],[25,'Gate-supply undervoltage']];
const controllerBits=[[29,'Initial-position frequency fault'],[28,'Initial-position timeout'],[23,'Abnormal speed'],[22,'Loss of synchronization'],[21,'Motor not detected'],[20,'Motor lock'],[19,'Phase CBC current limit'],[18,'Lock-current limit'],[17,'Motor undervoltage'],[16,'Motor overvoltage']];
const word=v=>Number.isInteger(v)&&v>=0&&v<0xffffffff;
const hex=v=>word(v)?'0x'+v.toString(16).padStart(8,'0'):'unavailable';
const value=(v,unit)=>Number.isFinite(v)?`${Number(v.toFixed(3))} ${unit}`:'unavailable';
function describeFault(e){
 const flags=[];
 if(word(e.gate))for(const [bit,label]of gateBits)if(e.gate&(2**bit))flags.push(label);
 if(word(e.controller))for(const [bit,label]of controllerBits)if(e.controller&(2**bit))flags.push(label);
 let title=e.reason||'Unidentified fault';
 if(e.reason==='Motor-feed current limit')title='Input-current cutoff triggered';
 else if(e.reason==='Motor voltage out of range')title='Motor voltage limit triggered';
 else if(e.reason==='Driver nFAULT asserted'||e.reason==='Driver current limiting')title=flags.length?flags.join(' · '):'Driver fault — cause unavailable';
 const details=[e.stopped?'Motor stopped':'Driver reported limiting; no stop commanded',`Input ${value(e.current_a,'A')} · Motor ${value(e.voltage_v,'V')}`];
 if(e.reason==='Motor-feed current limit')details.push(`Input cutoff ${value(e.input_a,'A')}`);
 if(word(e.controller)&&(e.controller&0x80000))details.push(`Phase thresholds: align ${value(e.align_a,'A')}, run ${value(e.phase_a,'A')}`);
 if(word(e.controller)&&(e.controller&0x40000))details.push(`Lock threshold ${value(e.lock_a,'A')}`);
 if(word(e.gate)&&(e.gate&0x10000000))details.push(`VDS threshold ${value(e.vds_v,'V')}`);
 if(flags.length&&e.reason!=='Driver nFAULT asserted'&&e.reason!=='Driver current limiting')details.push('Driver also reported: '+flags.join(' · '));
 if(e.reason==='Motor voltage out of range')details.push('Source not identified: no hardware input-clamp diagnostic is wired.');
 details.push(`Gate ${hex(e.gate)} · Controller ${hex(e.controller)}`);
 return {title,details,stopped:!!e.stopped,id:e.id,at_ms:e.at_ms};
}
class FaultMonitor{
 constructor(notify){this.notify=notify;this.reset();}
 reset(){this.id=0;this.uptime=0;}
 receive(d){
  if(Number.isFinite(d.uptime_ms)&&d.uptime_ms<this.uptime)this.id=0;
  this.uptime=d.uptime_ms??this.uptime;
  const e=d.fault_event;
  if(!e||!Number.isInteger(e.id)||e.id<=0||e.id===this.id)return;
  const previous=this.id;this.id=e.id;
  const event=describeFault(e);event.missed=previous&&e.id>previous+1?e.id-previous-1:0;
  this.notify(event);
 }
}
function mountFaultUI(document){
 const stack=document.getElementById('faultToasts'),history=document.getElementById('faultHistory'),summary=document.getElementById('faultSummary'),panel=document.getElementById('faultEvents');let total=0;
 return event=>{
  total++;panel.hidden=false;summary.textContent=`Limit & fault events (${total})`;
  const detail=event.details.join('\n')+(event.missed?`\n${event.missed} earlier events occurred between received updates.`:'');
  const item=document.createElement('li'),stamp=new Date().toLocaleTimeString();
  const label=document.createElement('strong');label.textContent=`${stamp} · ${event.title}`;
  const body=document.createElement('div');body.textContent=detail;item.append(label,body);history.prepend(item);while(history.children.length>20)history.lastElementChild.remove();
  const toast=document.createElement('div');toast.className='faultToast'+(event.stopped?' stopped':'');toast.setAttribute('role','alert');
  const title=document.createElement('strong');title.textContent=event.title;
  const text=document.createElement('div');text.textContent=detail;
  const close=document.createElement('button');close.type='button';close.textContent='×';close.setAttribute('aria-label','Dismiss '+event.title);close.onclick=()=>toast.remove();
  toast.append(close,title,text);stack.prepend(toast);while(stack.children.length>4)stack.lastElementChild.remove();
  setTimeout(()=>toast.remove(),12000);
 };
}
const api={describeFault,FaultMonitor,mountFaultUI};if(typeof module!=='undefined')module.exports=api;root.BldcFaults=api;
})(typeof globalThis!=='undefined'?globalThis:this);
