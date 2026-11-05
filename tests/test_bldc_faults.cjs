const assert=require('node:assert/strict');
const {describeFault,FaultMonitor}=require('../dist/bldc-faults.js');
const sample={id:1,at_ms:1500,reason:'Driver nFAULT asserted',stopped:true,gate:0x18000000,controller:0x000c0000,voltage_v:19.5,current_a:1.1,input_a:.9,align_a:2,phase_a:3,lock_a:2.5,vds_v:1.2};
let event=describeFault(sample);
for(const name of ['VDS overcurrent','Sense overcurrent','Phase CBC current limit','Lock-current limit'])assert.ok(event.title.includes(name));
assert.ok(event.details.some(x=>x.includes('align 2 A, run 3 A')));
assert.ok(event.details.some(x=>x.includes('Gate 0x18000000')));
event=describeFault({...sample,reason:'Motor-feed current limit',gate:0,controller:0});assert.equal(event.title,'Input-current cutoff triggered');assert.ok(event.details.includes('Input cutoff 0.9 A'));
event=describeFault({...sample,gate:0xffffffff,controller:0xffffffff});assert.equal(event.title,'Driver fault — cause unavailable');assert.ok(event.details.at(-1).includes('Gate unavailable'));
event=describeFault({...sample,reason:'Motor voltage out of range',gate:0,controller:0});assert.equal(event.title,'Motor voltage limit triggered');assert.ok(event.details.some(x=>x.includes('Source not identified')));
const events=[],monitor=new FaultMonitor(e=>events.push(e));
monitor.receive({uptime_ms:1000,fault_event:{...sample,id:0}});assert.equal(events.length,0);
monitor.receive({uptime_ms:2000,fault_event:sample});monitor.receive({uptime_ms:2200,fault_event:sample});assert.equal(events.length,1);
monitor.receive({uptime_ms:3000,fault_event:{...sample,id:2}});assert.equal(events.length,2); // Identical fault, new event.
monitor.receive({uptime_ms:4000,fault_event:{...sample,id:5}});assert.equal(events.at(-1).missed,2);
monitor.receive({uptime_ms:50,fault_event:sample});assert.equal(events.length,4); // Reboot, ID reused.
monitor.reset();monitor.receive({uptime_ms:100,fault_event:sample});assert.equal(events.length,5); // Reconnect reports retained last event.
event=describeFault({...sample,reason:'Driver current limiting',stopped:false,gate:0,controller:0x80000});assert.equal(event.title,'Phase CBC current limit');assert.match(event.details[0],/no stop commanded/);
console.log('PASS fault decoding, unavailable register reads, snapshot thresholds, repeated trips, telemetry deduplication, reboot and reconnect');
