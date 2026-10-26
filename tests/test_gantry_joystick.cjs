const assert=require('node:assert/strict');
const {Jogger,PositionSlots}=require('../dist/gantry.js');
const {JoystickInput}=require('../dist/gantry-controls.js');
const calls=[],axes={};
for(const axis of ['X','Y'])axes[axis]={port:{},seen:100,last:{protocol:3,temperature_c:25,motor_enabled:false,device_id:axis,position_session:'boot',position_full_steps:0,capabilities:{resolutions:{half:2},fixed_ramp_ms:400,deferred_start_supported:true}},send:async(cmd,fields)=>{calls.push({axis,cmd,fields});}};
const jog=new Jogger(axes,()=>{},()=>100),input=new JoystickInput(jog);
jog.resetInput=()=>input.reset();
(async()=>{
 input.sample(1,0,'pad');assert.equal(jog.key,null);
 input.sample(.1,0,'pad');input.sample(.575,-.575,'pad');
 await jog.tick(100,{},'half');
 const moves=calls.filter(c=>c.cmd==='jog');assert.equal(moves.length,2);assert.equal(moves[0].fields.direction,1);assert.equal(moves[1].fields.direction,-1);assert.ok(moves[0].fields.speed_sps<100);
 input.sample(0,0,'pad');await jog.tick(100,{});assert.equal(calls.filter(c=>c.cmd==='decelerate').length,2);
 await jog.stop();input.sample(1,0,'pad');assert.equal(jog.key,null);
 input.sample(0,0,'pad');input.sample(1,0,'pad');assert.equal(jog.direction('X'),1);
 input.sample(1,0,'other-pad');assert.equal(jog.key,null);
 input.sample(0,0,'other-pad');input.sample(1,0,'other-pad');jog.press('ArrowLeft');await jog.tick(100,{X:true});assert.equal(calls.filter(c=>c.cmd==='jog').at(-1).fields.direction,1);
 await jog.stop();axes.X.last.temperature_c=65;input.sample(0,0,'pad');input.sample(1,0,'pad');assert.equal(jog.key,null);axes.X.last.temperature_c=25;
 input.sample(NaN,1,'pad');assert.equal(jog.key,null);
 const slots=new PositionSlots(axes,jog,()=>{},null);assert.equal(slots.save(0),true);
 axes.X.last.soft_limits_enabled=true;axes.X.last.soft_limit_min_full_steps=1;axes.X.last.soft_limit_max_full_steps=10;
 assert.equal(await slots.goto(0,100),false);assert.equal(calls.filter(c=>c.cmd==='start').length,0);
 console.log('PASS analog diagonal speed, dead zone, release, neutral rearm, source changes, keyboard/inversion, thermal gating, invalid input, GOTO limit rejection');
})().catch(e=>{console.error(e);process.exitCode=1;});

// Exercise mounted pointer/gamepad events without physical controllers.
{
 const vm=require('node:vm'),fs=require('node:fs'),nodes={},timers=[];
 const node=id=>nodes[id]??=( {value:'0',checked:false,style:{},events:{},addEventListener(k,f){this.events[k]=f;},setPointerCapture(){},getBoundingClientRect(){return {left:0,top:0,width:180,height:180};}} );
 let pad=null,stops=0;
 const mountedJog={analog:{},ready:()=>true,states:{},setAnalog(x,y){this.analog={X:x,Y:y};return true;},stop(){stops++;this.analog={};this.resetInput();return Promise.resolve();}};
 const doc={getElementById:node,hasFocus:()=>true,hidden:false,activeElement:{tagName:'BODY'}};
 const sandbox={document:doc,navigator:{getGamepads:()=>pad?[pad]:[]},setInterval:f=>timers.push(f),Date,console};
 vm.runInNewContext(fs.readFileSync(require.resolve('../dist/gantry-controls.js'),'utf8'),sandbox);
 sandbox.GantryControls.mount(axes,mountedJog,()=>{});
 node('joystick').events.pointerdown({pointerId:1,clientX:180,clientY:90,preventDefault(){}});timers[0]();assert.equal(mountedJog.analog.X,1);
 node('joystick').events.pointerup({pointerId:1});assert.equal(mountedJog.analog.X,undefined);
 node('useGamepad').checked=true;pad={index:0,connected:true,id:'test',axes:[1,0],buttons:[{pressed:true}]};timers[0]();assert.equal(mountedJog.analog.X,undefined);
 pad.axes=[0,0];timers[0]();pad.axes=[1,0];timers[0]();assert.equal(mountedJog.analog.X,1);
 pad.buttons[0].pressed=false;timers[0]();assert.equal(mountedJog.analog.X,undefined);
 pad.buttons[0].pressed=true;pad.axes=[0,0];timers[0]();pad.axes=[0,-1];timers[0]();assert.equal(mountedJog.analog.Y,1);
 pad=null;timers[0]();assert.equal(stops,1);assert.equal(mountedJog.analog.Y,undefined);
 console.log('PASS mounted pointer release, gamepad activation/hold button/release and disconnect stop');
}
