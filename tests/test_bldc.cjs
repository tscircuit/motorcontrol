const assert=require('node:assert/strict');
const {BldcClient,validTelemetry,controlState,estimateRpm,validCurrentSettings,currentDefaults}=require('../dist/bldc.js');
assert.equal(estimateRpm(196,6),1960);assert.equal(estimateRpm(196,7),1680);assert.equal(estimateRpm(0,6),0);assert.equal(estimateRpm(NaN,6),null);assert.equal(estimateRpm(100,0),null);
const telemetry={type:'telemetry',protocol:'bldc-1',firmware:'native-bldc',power_ready:true,armed:false,motor_enabled:false,vbus_v:9,vmotor_v:9,feed_current_a:.05,electrical_hz:0,max_percent:8,max_run_ms:1500};
assert.equal(validTelemetry(telemetry),true);
assert.equal(validTelemetry({...telemetry,protocol:3}),false);
assert.equal(validTelemetry({...telemetry,vmotor_v:null}),false);
assert.equal(controlState(telemetry,true,false).arm,true);
assert.equal(controlState(telemetry,false,false).arm,false);
assert.equal(controlState({...telemetry,armed:true},true,false).start,true);
assert.equal(controlState({...telemetry,motor_enabled:true},true,false).arm,false);
assert.equal(controlState({...telemetry,vmotor_v:0,power_ready:false},true,false).power,true);
assert.equal(controlState({...telemetry,armed:true,vmotor_v:0},true,false).power,false);
assert.equal(controlState({...telemetry,pd_change_while_powered:true,armed:true},true,false).power,true);
assert.equal(controlState({...telemetry,pd_change_while_powered:true,motor_enabled:true},true,false).power,true);
assert.equal(controlState({...telemetry,pd_change_while_powered:true},false,false).power,false);
(async()=>{
 let clock=100,seen=[];
 const c=new BldcClient({clock:()=>clock,onTelemetry:d=>seen.push(d),timeout:100});
 const line=JSON.stringify(telemetry)+'\n';c.feed(line.slice(0,20));c.feed(line.slice(20));assert.equal(seen.length,1);assert.equal(c.fresh(),true);clock=2000;assert.equal(c.fresh(),false);
 c.feed('x'.repeat(5000)+line);assert.equal(seen.length,1);c.feed(line);assert.equal(seen.length,2);
 c.feed('{bad}\n'+JSON.stringify({...telemetry,protocol:3})+'\n');assert.equal(seen.length,2);
 let writes=[];c.port={writable:{getWriter:()=>({write:async bytes=>writes.push(JSON.parse(new TextDecoder().decode(bytes))),releaseLock(){}})}};
 const a=c.send('arm');await new Promise(r=>setImmediate(r));c.receive(JSON.stringify({type:'ack',protocol:'bldc-1',id:writes.at(-1).id,ok:true}));await a;
 const bad=c.send('start');await new Promise(r=>setImmediate(r));c.receive(JSON.stringify({type:'ack',protocol:'bldc-1',id:writes.at(-1).id,ok:false,error:'Not armed'}));await assert.rejects(bad,/Not armed/);
 let unblock;c.chain=new Promise(r=>unblock=r);
 const start=c.send('start').catch(e=>e);const stop=c.send('stop');unblock();await new Promise(r=>setImmediate(r));assert.equal(writes.at(-1).cmd,'stop');assert.match((await start).message,/cancelled/);c.receive(JSON.stringify({type:'ack',protocol:'bldc-1',id:writes.at(-1).id,ok:true}));await stop;
 await assert.rejects(c.send('status'),/did not acknowledge/);
 console.log('PASS BLDC telemetry framing, wrong-board rejection, stale gating, ACK errors, timeout, queued-start cancellation on Stop');
})().catch(e=>{console.error(e);process.exitCode=1});

(async()=>{
 const {BldcArrows}=require('../dist/bldc.js');
 const flush=()=>new Promise(r=>setImmediate(r));let calls=[];let gate;let heldArm=false;
 const client={port:{},send:async(cmd,fields)=>{calls.push({cmd,fields});if(cmd==='arm'&&heldArm)await new Promise(r=>gate=r);}};
 const arrows=new BldcArrows({client,canRun:()=>true,settings:()=>({percent:8,duration_ms:1500})});
 arrows.press('ArrowUp');await flush();assert.deepEqual(calls.map(x=>x.cmd),['arm','start']);assert.equal(calls.at(-1).fields.direction,1);
 arrows.press('ArrowUp');await flush();assert.equal(calls.length,2); // ignore repeat
 arrows.release('ArrowUp');assert.equal(calls.at(-1).cmd,'stop');assert.equal(calls.at(-1).fields.source,'arrow_release');
 calls=[];heldArm=true;arrows.press('ArrowLeft');await flush();arrows.release('ArrowLeft');gate();await flush();assert.equal(calls.filter(x=>x.cmd==='start').length,0);heldArm=false;
 calls=[];arrows.press('ArrowDown');await flush();assert.equal(calls.at(-1).fields.direction,-1);
 arrows.press('ArrowRight');assert.equal(calls.at(-1).cmd,'stop');arrows.release('ArrowRight');await flush();assert.equal(calls.filter(x=>x.cmd==='start').length,1);arrows.release('ArrowDown');
 calls=[];arrows.press('ArrowRight');await flush();arrows.receive({motor_enabled:false});arrows.press('ArrowRight');await flush();assert.equal(calls.filter(x=>x.cmd==='start').length,1);arrows.release('ArrowRight');arrows.press('ArrowRight');await flush();assert.equal(calls.filter(x=>x.cmd==='start').length,2);arrows.reset('blur');assert.equal(arrows.held.size,0);assert.equal(calls.at(-1).cmd,'stop');
 console.log('PASS BLDC arrow direction, repeat suppression, release-during-arm race, opposite cancellation, timed-out hold lockout and focus reset');
})().catch(e=>{console.error(e);process.exitCode=1});

(async()=>{
 const {BldcArrows}=require('../dist/bldc.js');const flush=()=>new Promise(r=>setImmediate(r));
 let ready=true,calls=[];const client={port:{},send:async(cmd,fields)=>{calls.push({cmd,fields});}};
 const a=new BldcArrows({client,canRun:()=>ready,settings:()=>({percent:8,duration_ms:0})});
 a.press('ArrowRight');await flush();a.suspend();ready=false;a.resume();await flush();assert.equal(calls.filter(c=>c.cmd==='start').length,1);
 ready=true;a.receive({motor_enabled:false});await flush();assert.equal(calls.filter(c=>c.cmd==='start').length,2);assert.equal(calls.at(-1).fields.direction,1);
 a.suspend();ready=false;a.release('ArrowRight');ready=true;a.resume();await flush();assert.equal(calls.filter(c=>c.cmd==='start').length,2);
 a.press('ArrowLeft');await flush();assert.equal(calls.at(-1).fields.direction,-1);a.reset('finished');
 console.log('PASS voltage-change hold resume and release-during-change cancellation');
})().catch(e=>{console.error(e);process.exitCode=1});

assert.equal(validCurrentSettings(currentDefaults),true);
assert.equal(validCurrentSettings({...currentDefaults,input_enabled:false,phase_enabled:false,lock_enabled:false,sense_ocp_enabled:false,vds_ocp_enabled:false}),true);
assert.equal(validCurrentSettings({...currentDefaults,phase_a:2.3}),false);
assert.equal(validCurrentSettings({...currentDefaults,input_a:0}),false);
assert.equal(validCurrentSettings({...currentDefaults,input_a:8,align_a:.25,phase_a:3.75,lock_a:3.75,vds_v:.06}),true);
assert.equal(validCurrentSettings({...currentDefaults,vds_v:.07}),false);
assert.equal(validCurrentSettings({...currentDefaults,phase_enabled:'false'}),false);
