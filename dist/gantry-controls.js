(function(root){
'use strict';
// Require neutral after a stop, focus loss, or controller change.
class JoystickInput {
 constructor(jog){this.jog=jog;this.reset();}
 reset(){this.armed=false;this.source=null;}
 sample(x,y,source){
  if(!Number.isFinite(x)||!Number.isFinite(y)){this.reset();this.jog.analog={};return;}
  const length=Math.hypot(x,y),deadzone=.15;
  if(source!==this.source){this.armed=false;this.source=source;this.jog.analog={};}
  if(length<=deadzone){this.armed=true;this.jog.analog={};return;}
  if(!this.armed)return;
  const scale=(Math.min(1,length)-deadzone)/(1-deadzone)/length;
  // Quantize to avoid filling USB queues with imperceptible stick noise.
  if(!this.jog.setAnalog(Math.round(x*scale*20)/20,Math.round(y*scale*20)/20)){this.reset();this.jog.analog={};}
 }
}
function mount(axes,jog,report){
 const doc=root.document,$=id=>doc.getElementById(id),pad=$('joystick'),knob=$('joystickKnob'),input=new JoystickInput(jog);
 let pointer=null,point=[0,0],gamepad=null;
 const center=()=>{pointer=null;point=[0,0];knob.style.transform='translate(0px,0px)';};
 jog.resetInput=()=>{input.reset();center();};
 const move=e=>{const r=pad.getBoundingClientRect(),radius=r.width/2;let x=(e.clientX-r.left-radius)/radius,y=-(e.clientY-r.top-r.height/2)/radius;const n=Math.max(1,Math.hypot(x,y));point=[x/n,y/n];knob.style.transform=`translate(${point[0]*60}px,${-point[1]*60}px)`;};
 pad.addEventListener('pointerdown',e=>{if(pointer!==null||!jog.ready()||jog.returning||jog.stopsPending)return;e.preventDefault();pointer=e.pointerId;pad.setPointerCapture(pointer);input.sample(0,0,'pointer');move(e);});
 pad.addEventListener('pointermove',e=>{if(pointer===e.pointerId)move(e);});
 pad.addEventListener('pointerup',e=>{if(pointer===e.pointerId){center();input.sample(0,0,'pointer');}});
 for(const event of ['pointercancel','lostpointercapture'])pad.addEventListener(event,()=>{if(pointer!==null)void jog.stop();});
 $('useGamepad').addEventListener('change',()=>{gamepad=null;void jog.stop();});
 root.setInterval(()=>{
  pad.disabled=!jog.ready()||jog.returning||!!jog.stopsPending;
  if(doc.hidden||!doc.hasFocus())return;
  if(pointer!==null){input.sample(...point,'pointer');return;}
  if(!$('useGamepad').checked)return;
  let pads=[];try{pads=Array.from(root.navigator.getGamepads?.()||[]).filter(p=>p?.connected);}catch{}
  const p=pads.find(p=>p.index===gamepad)||pads[0];
  if(!p){if(gamepad!==null){gamepad=null;void jog.stop('Gamepad disconnected.');}$('gamepadStatus').textContent='Connect a gamepad and press a button to detect it.';return;}
  if(gamepad!==null&&p.index!==gamepad){void jog.stop();gamepad=p.index;return;}
  gamepad=p.index;$('gamepadStatus').textContent=p.id+' · center stick, then hold button 1 to jog';
  const editing=['INPUT','SELECT','TEXTAREA'].includes(doc.activeElement?.tagName)||doc.activeElement?.isContentEditable;
  if(editing||!p.buttons[0]?.pressed){jog.analog={};input.reset();return;}
  input.sample(p.axes[0]??0,-(p.axes[1]??0),'gamepad-'+p.index);
 },50);
 for(const axis of Object.keys(axes)){
  $('applyLimits'+axis).onclick=async()=>{
   const a=axes[axis],enabled=$('enableLimits'+axis).checked;
   const min=$('minLimit'+axis).value,max=$('maxLimit'+axis).value;
   if(enabled&&(!min.trim()||!max.trim()||![Number(min),Number(max)].every(Number.isFinite)||Number(min)>=Number(max))){report(axis+': enter a minimum smaller than the maximum.');return;}
   if(jog.key||jog.active||jog.returning||jog.stopsPending||Object.values(axes).some(a=>a.last?.motor_enabled)){report('Stop both axes before applying limits.');return;}
   try{await a.send('set_soft_limits',{enabled,min_full_steps:Number(min),max_full_steps:Number(max)});await a.send('status');report(axis+': soft limits updated.');}catch(e){report(e.message);}
  };
 }
 root.setInterval(()=>{for(const [axis,a] of Object.entries(axes)){
  const live=a.port&&Date.now()-a.seen<1000,supported=a.last?.capabilities?.soft_limits_supported;
  $('applyLimits'+axis).disabled=!live||!supported||!!jog.key||!!jog.active||jog.returning||!!jog.stopsPending||Object.values(axes).some(a=>a.last?.motor_enabled);
  $('limitStatus'+axis).textContent=!live?'Connect for live limits.':!supported?'Requires updated DRV8825 / DRV8452 firmware.':a.last.soft_limits_enabled?`Active: ${a.last.soft_limit_min_full_steps} to ${a.last.soft_limit_max_full_steps} full steps`:'Custom limits disabled.';
 }},200);
}
const api={JoystickInput,mount};if(typeof module!=='undefined')module.exports=api;root.GantryControls=api;
})(typeof window==='undefined'?globalThis:window);
