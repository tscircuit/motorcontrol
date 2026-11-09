const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync(require.resolve('../dist/three-axis-gantry.html'), 'utf8');
const listeners = {}, windowListeners = {}, nodes = {}, intervals = {};
for (const [, id] of html.matchAll(/id="([^"]+)"/g)) {
  assert.ok(!nodes[id], 'Duplicate element ' + id);
  nodes[id] = {value: id === 'jogSpeed' ? '150' : id === 'jogResolution' ? 'half' : '', checked: false, tagName: 'DIV', classList: {toggle() {}}, addEventListener() {}, replaceChildren(...children) {this.children = children;}, blur() {}};
}
const arrows = [...html.matchAll(/data-arrow="([^"]+)"/g)].map(([, key]) => ({dataset: {arrow: key}, events: {}, classList: {toggle() {}}, addEventListener(name, fn) {this.events[name] = fn;}, setPointerCapture() {}}));
const storage = new Map();
const sandbox = {console, setTimeout, clearTimeout, setInterval(fn, ms) {intervals[ms] = fn;}, navigator: {serial: {}}, window: {localStorage: {getItem(k) {return storage.get(k);}, setItem(k, v) {storage.set(k, v);}}, addEventListener(k, fn) {windowListeners[k] = fn;}}, document: {createElement() {return {};}, body: {dataset: {threeAxis: 'true'}}, hidden: false, getElementById(id) {assert.ok(nodes[id], 'Missing element ' + id); return nodes[id];}, querySelectorAll() {return arrows;}, addEventListener(k, fn) {listeners[k] = fn;}}};
let source = fs.readFileSync(require.resolve('../dist/gantry.js'), 'utf8');
source = source.replace(' render();\n if(!navigator.serial)', ' globalThis.testApi={axes,jog,positions};\n render();\n if(!navigator.serial)');
vm.runInNewContext(source, sandbox);
const {axes, jog, positions} = sandbox.testApi;
assert.deepEqual(Object.keys(axes), ['X', 'Y', 'Z']);
assert.equal(positions.storageKey, 'three-axis-gantry-position-slots-v1');
assert.equal(arrows.length, 6);
assert.match(html, /<h1>3 axis gantry<\/h1>/);
const calls = [];
for (const [axis, a] of Object.entries(axes)) {
  a.port = {}; a.seen = Date.now();
  a.last = {protocol: 3, temperature_c: 25, motor_enabled: false, device_id: axis, position_session: 'boot', position_full_steps: 0, capabilities: {resolutions: {half: 2}, fixed_ramp_ms: 400, deferred_start_supported: true, max_steps: 100000}};
  a.send = async (cmd, fields) => {
    calls.push({axis, cmd, fields});
    if (cmd === 'jog') a.last.motor_enabled = true;
    if (cmd === 'stop' || cmd === 'decelerate') a.last.motor_enabled = false;
    if (cmd === 'start') a.move = fields;
    if (cmd === 'run_move') {a.last.position_full_steps += a.move.direction * a.move.steps / 2; a.last.motor_enabled = false; a.last.stop_reason = 'Step move complete';}
  };
}
const event = (key, extra = {}) => ({key, code: key, repeat: false, shiftKey: false, target: {tagName: 'BODY'}, preventDefault() {}, ...extra});
const flush = () => new Promise(r => setImmediate(r));
const moves = () => calls.filter(c => c.cmd === 'jog');
const keydown = async (key, extra) => {listeners.keydown(event(key, extra)); await flush();};
const keyup = async (key, extra) => {listeners.keyup(event(key, extra)); await flush();};
async function reset() {await jog.stop(); calls.length = 0; for (const a of Object.values(axes)) a.seen = Date.now();}
(async () => {
  // Ordinary arrows retain XY behavior; shifted vertical arrows only start Z.
  for (const [key, shiftKey, axis, direction] of [['ArrowRight', false, 'X', 1], ['ArrowLeft', true, 'X', -1], ['ArrowUp', false, 'Y', 1], ['ArrowDown', false, 'Y', -1], ['ArrowUp', true, 'Z', 1], ['ArrowDown', true, 'Z', -1]]) {
    await reset(); await keydown(key, {shiftKey});
    assert.deepEqual(moves().map(c => [c.axis, c.fields.direction]), [[axis, direction]]);
    // Releasing Shift before the arrow must still decelerate Z, never Y.
    await keyup('Shift'); await keyup(key);
    assert.deepEqual(calls.filter(c => c.cmd === 'decelerate').map(c => c.axis), [axis]);
    assert.equal(jog.held.size, 0);
  }
  await reset(); await keydown('ArrowUp'); await keydown('Shift', {shiftKey: true});
  await keydown('ArrowUp', {shiftKey: true, repeat: true});
  assert.deepEqual(moves().map(c => c.axis), ['Y']);
  await keyup('ArrowUp', {shiftKey: true}); assert.equal(jog.held.size, 0);
  await reset(); nodes.invertZ.checked = true;
  await keydown('ArrowUp', {shiftKey: true}); assert.equal(moves()[0].fields.direction, -1);
  nodes.invertZ.checked = false;
  // All three can run, and releasing Z leaves X/Y running.
  await reset(); await keydown('ArrowRight'); await keydown('ArrowUp');
  const zPlus = arrows.find(b => b.dataset.arrow === 'Shift+ArrowUp');
  zPlus.events.pointerdown({pointerId: 1, preventDefault() {}}); await flush();
  assert.deepEqual(moves().map(c => c.axis), ['X', 'Y', 'Z']);
  zPlus.events.pointerup(); await flush();
  assert.equal(jog.direction('X'), 1); assert.equal(jog.direction('Y'), 1); assert.equal(jog.direction('Z'), 0);
  assert.deepEqual(calls.filter(c => c.cmd === 'decelerate').map(c => c.axis), ['Z']);
  await reset(); await keydown('ArrowUp', {shiftKey: true}); await keydown('ArrowDown', {shiftKey: true});
  assert.equal(jog.direction('Z'), 0); assert.equal(calls.findLast(c => c.cmd === 'decelerate').axis, 'Z');
  // Emergency stop and focus loss clear Z, with no restart from key repeat.
  for (const stop of [() => listeners.keydown(event('Escape')), () => listeners.keydown(event(' ', {code: 'Space'})), () => nodes.stopAll.onclick(), () => windowListeners.blur(), () => {sandbox.document.hidden = true; listeners.visibilitychange();}]) {
    await reset(); await keydown('ArrowUp', {shiftKey: true}); stop(); await flush();
    assert.deepEqual(calls.filter(c => c.cmd === 'stop').map(c => c.axis), ['X', 'Y', 'Z']);
    const before = moves().length;
    await keydown('ArrowUp', {shiftKey: true, repeat: true}); assert.equal(moves().length, before); assert.equal(jog.held.size, 0);
    sandbox.document.hidden = false;
  }
  await reset(); await keydown('ArrowUp', {shiftKey: true, target: {tagName: 'INPUT', type: 'number'}}); assert.equal(calls.length, 0);
  // Z is part of all-board readiness and runtime fault/disconnect checks.
  for (const failure of ['disconnected', 'fault', 'stale']) {
    await reset(); await keydown('ArrowRight');
    if (failure === 'disconnected') axes.Z.port = null;
    if (failure === 'fault') axes.Z.last.driver_fault_asserted = true;
    if (failure === 'stale') axes.Z.seen = 0;
    await jog.tick(150, {});
    assert.equal(jog.held.size, 0); assert.equal(jog.active, null);
    assert.ok(calls.some(c => c.axis === 'X' && c.cmd === 'stop'));
    assert.equal(jog.press('ArrowRight'), false);
    axes.Z.port = {}; axes.Z.last.driver_fault_asserted = false; axes.Z.seen = Date.now();
  }
  // Save all coordinates in isolated storage; wait for Z's preparation ACK.
  await reset();
  for (const [axis, position] of [['X', 10], ['Y', -5], ['Z', 20]]) axes[axis].last.position_full_steps = position;
  assert.equal(positions.save(0), true); assert.equal(storage.size, 1);
  assert.equal(JSON.parse(storage.get(positions.storageKey))[0].Z.position, 20);
  for (const a of Object.values(axes)) a.last.position_full_steps = 0;
  const sendZ = axes.Z.send; let prepared;
  axes.Z.send = async (cmd, fields) => {await sendZ(cmd, fields); if (cmd === 'start') await new Promise(r => {prepared = r;});};
  const returning = positions.goto(0, 150); await flush();
  assert.equal(calls.filter(c => c.cmd === 'start').length, 3);
  assert.equal(calls.some(c => c.cmd === 'run_move'), false);
  prepared(); assert.equal(await returning, true); axes.Z.send = sendZ;
  assert.deepEqual(calls.filter(c => c.cmd === 'start').map(c => [c.axis, c.fields.steps, c.fields.speed_sps]), [['X', 20, 75], ['Y', 10, 37.5], ['Z', 40, 150]]);
  assert.deepEqual(Object.values(axes).map(a => a.last.position_full_steps), [10, -5, 20]);
  jog.update(); assert.match(nodes.positionValue0.textContent, /Z 20.0000/);
  axes.Z.last.position_session = 'restarted'; assert.equal(positions.valid(0), false);
  assert.equal(await positions.goto(0, 150), false);
  console.log('PASS three-axis page, Shift routing/release order, simultaneous XYZ, Z reversal/cancellation, all-axis stops/readiness, isolated XYZ positions and preparation barrier');
})().catch(e => {console.error(e); process.exitCode = 1;});
