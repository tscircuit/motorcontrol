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
 const controller=$('gamepadDevice'),xAxis=$('gamepadXAxis'),yAxis=$('gamepadYAxis'),holdButton=$('gamepadButton');
 let deviceKey='',mappingKey='';
 const stopInput=()=>{input.reset();jog.analog={};void jog.stop();};
 $('useGamepad').addEventListener('change',()=>{stopInput();$('useGamepad').blur();});
 for(const select of [controller,xAxis,yAxis,holdButton])select.addEventListener('change',()=>{stopInput();select.blur();});
 const fill=(select,items,value)=>{
  select.replaceChildren(...items.map(([id,text])=>{const option=doc.createElement('option');option.value=String(id);option.textContent=text;return option;}));
  select.value=String(value);
 };
 const scan=()=>{
  if(typeof root.navigator.getGamepads!=='function')return {pads:[],error:'This browser does not expose the Gamepad API. Open this page in desktop Chrome or Edge.'};
  try{return {pads:Array.from(root.navigator.getGamepads()||[]).filter(p=>p&&p.connected!==false)};}
  catch(e){return {pads:[],error:'Joystick access is blocked by the browser: '+e.message+'. Open the gantry page directly in its own tab.'};}
 };
 function poll(){
  pad.disabled=!jog.ready()||jog.returning||!!jog.stopsPending;
  const {pads,error}=scan(),key=JSON.stringify(pads.map(p=>[p.index,p.id]));
  if(key!==deviceKey){
   const previous=controller.value;deviceKey=key;
   fill(controller,pads.length?pads.map(p=>[p.index,p.id]):[['','No joystick detected']],pads.some(p=>String(p.index)===previous)?previous:pads[0]?.index??'');
  }
  const p=pads.find(p=>String(p.index)===controller.value);
  controller.disabled=!pads.length;
  if(!p){
   if(gamepad!==null){gamepad=null;stopInput();}
   xAxis.disabled=yAxis.disabled=holdButton.disabled=true;
   $('gamepadStatus').textContent=error||'No joystick detected. Click Detect joystick, then press a button on the joystick. Keep this tab focused; reconnect USB or Bluetooth if needed.';
   $('gamepadValues').textContent='';return;
  }
  const nextMapping=JSON.stringify([p.index,p.id,p.axes.length,p.buttons.length]);
  if(mappingKey!==nextMapping){
   mappingKey=nextMapping;
   fill(xAxis,p.axes.map((_,i)=>[i,'Axis '+(i+1)]),0);
   fill(yAxis,p.axes.map((_,i)=>[i,'Axis '+(i+1)]),Math.min(1,p.axes.length-1));
   fill(holdButton,p.buttons.map((_,i)=>[i,'Button '+(i+1)]),0);
  }
  xAxis.disabled=yAxis.disabled=!p.axes.length;holdButton.disabled=!p.buttons.length;
  $('gamepadValues').textContent='Axes: '+p.axes.map((v,i)=>(i+1)+': '+Number(v).toFixed(2)).join(' · ')+' | Pressed buttons: '+(p.buttons.flatMap((b,i)=>b.pressed?[i+1]:[]).join(', ')||'none');
  if(gamepad!==null&&gamepad!==p.index){stopInput();}
  gamepad=p.index;
  const enabled=$('useGamepad').checked;
  $('gamepadStatus').textContent=p.id+' detected'+(enabled?' — center the stick while holding Button '+(Number(holdButton.value)+1)+', then move.':' — enable joystick control to jog.');
  if(pointer!==null){if(!doc.hidden&&doc.hasFocus())input.sample(...point,'pointer');return;}
  if(!enabled||doc.hidden||!doc.hasFocus()){jog.analog={};input.reset();return;}
  const active=doc.activeElement;
  const editing=active?.isContentEditable||['SELECT','TEXTAREA'].includes(active?.tagName)||(active?.tagName==='INPUT'&&!['checkbox','button'].includes(active.type));
  if(editing||!p.buttons[Number(holdButton.value)]?.pressed){jog.analog={};input.reset();return;}
  input.sample(p.axes[Number(xAxis.value)]??0,-(p.axes[Number(yAxis.value)]??0),'gamepad-'+p.index);
 }
 // Poll before enabling motion too: the user must be able to see detection separately.
 root.setInterval(()=>{
  poll();
  if(pointer!==null&&!doc.hidden&&doc.hasFocus())input.sample(...point,'pointer');
 },50);
 $('detectGamepad').addEventListener('click',()=>{$('detectGamepad').blur();poll();});
 root.addEventListener('gamepadconnected',poll);
 root.addEventListener('gamepaddisconnected',poll);
 const canSetLimits=()=>!jog.key&&!jog.active&&!jog.returning&&!jog.stopsPending&&Object.values(axes).every(a=>!a.last?.motor_enabled);
 async function applyLimits(axis,enabled,min,max){
  const a=axes[axis];
  if(!canSetLimits()){report('Stop both axes before setting limits.');return false;}
  try{
   await a.send('set_soft_limits',{enabled,min_full_steps:min,max_full_steps:max});
   await a.send('status');report(axis+': limits set to '+(enabled?min+' … '+max+' full steps.':'disabled.'));return true;
  }catch(e){report(e.message);return false;}
 }
 for(const axis of Object.keys(axes)){
  $('applyLimits'+axis).onclick=async()=>{
   const enabled=$('enableLimits'+axis).checked,min=$('minLimit'+axis).value,max=$('maxLimit'+axis).value;
   if(enabled&&(!min.trim()||!max.trim()||![Number(min),Number(max)].every(Number.isFinite)||Number(min)>=Number(max))){report(axis+': enter a minimum smaller than the maximum.');return;}
   await applyLimits(axis,enabled,Number(min),Number(max));
  };
  for(const side of ['Min','Max'])$('set'+side+'Here'+axis).onclick=async()=>{
   const a=axes[axis],t=a.last,position=t?.position_full_steps;
   if(!a.port||Date.now()-a.seen>=1000||!Number.isFinite(position)||!t.capabilities?.soft_limits_supported){report(axis+': connect updated firmware with a live position to set a limit.');return;}
   // With no custom bounds yet, leave the opposite end open. Preserve an already set end.
   let min=t.soft_limits_enabled?t.soft_limit_min_full_steps:-1000000000;
   let max=t.soft_limits_enabled?t.soft_limit_max_full_steps:1000000000;
   if(side==='Min')min=position;else max=position;
   if(min>=max){report(axis+': minimum and maximum must be different positions.');return;}
   if(await applyLimits(axis,true,min,max)){
    $('enableLimits'+axis).checked=true;$('minLimit'+axis).value=String(min);$('maxLimit'+axis).value=String(max);
   }
  };
 }
 root.setInterval(()=>{for(const [axis,a] of Object.entries(axes)){
  const live=a.port&&Date.now()-a.seen<1000,supported=a.last?.capabilities?.soft_limits_supported;
  const disabled=!live||!supported||!canSetLimits();
  $('applyLimits'+axis).disabled=disabled;
  $('setMinHere'+axis).disabled=$('setMaxHere'+axis).disabled=disabled||!Number.isFinite(a.last?.position_full_steps);
  $('limitPosition'+axis).textContent=live&&Number.isFinite(a.last?.position_full_steps)?'Current position: '+a.last.position_full_steps+' full steps':'Current position unavailable';
  $('limitStatus'+axis).textContent=!live?'Connect for live limits.':!supported?'Requires updated DRV8825 / DRV8452 firmware.':a.last.soft_limits_enabled?`Active: ${a.last.soft_limit_min_full_steps} to ${a.last.soft_limit_max_full_steps} full steps`:'Custom limits disabled.';
 }},200);
}
const api={JoystickInput,mount};if(typeof module!=='undefined')module.exports=api;root.GantryControls=api;
})(typeof window==='undefined'?globalThis:window);
