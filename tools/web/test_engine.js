// node tools/web/test_engine.js : checks the web engine against the Python reference simulator and against the traces
// measured on the Logisim circuits (tools/probe.py).
const { execFileSync } = require("child_process");
const path = require("path");
const RV = require("./engine.js");

const root = path.resolve(__dirname, "..", "..");
const progs = JSON.parse(execFileSync("python", [path.join(__dirname, "dump_programs.py")], { cwd: root, maxBuffer: 1 << 26 }).toString());
let fails = 0;
const check = (ok, msg) => { if (!ok) { fails++; console.log("FAIL", msg); } };
const eq = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const memOf = (ram) => { const o = {}; ram.forEach((v, i) => { if (v) o[String(i * 4)] = v >>> 0; }); return o; };

for (const [name, p] of Object.entries(progs)) {
  if (!p.halts) { console.log("skip (does not halt):", name); continue; }
  // single-cycle: run until the PC stops moving
  const s = new RV.SingleCycle(p.words);
  let n = 0;
  for (; n < 20000; n++) { const pc = s.pc; s.step(); if (s.pc === pc) break; }
  check(eq(s.regs.map((v) => v >>> 0), p.regs), `${name}: single-cycle registers`);
  check(eq(memOf(s.ram), p.mem), `${name}: single-cycle memory`);
  // pipeline: enough cycles to drain
  const q = new RV.Pipeline(p.words);
  for (let i = 0; i < p.steps * 3 + 40; i++) q.step();
  check(eq(q.regs.map((v) => v >>> 0), p.regs), `${name}: pipeline registers`);
  check(eq(memOf(q.ram), p.mem), `${name}: pipeline memory`);
  console.log(`${name}: ok (${p.steps} instr)`);
}

// ---- single-cycle probe trace of demo.s (measured on circuit main): [tick, PC, instr, alu_result, branch_taken, wb_data]
const demo = progs.demo.words;
const sc = new RV.SingleCycle(demo);
const expSC = { 1: [4, 0x00a00593, 0xa, 0, 0xa], 2: [8, 0x00b50533, 0xa, 0, 0xa], 3: [0xc, 0xfff58593, 9, 0, 9], 4: [0x10, 0xfe059ce3, 9, 1, 9],
  5: [8, 0x00b50533, 0x13, 0, 0x13], 31: [0x10, 0xfe059ce3, 0, 0, 0], 32: [0x14, 0x00a02023, 0, 0, 0], 33: [0x18, 0x00002603, 0, 0, 0x37], 34: [0x1c, 0x010000ef, 0, 0, 0x20] };
for (let t = 1; t <= 34; t++) {
  sc.step();
  if (expSC[t]) { const k = sc.peek(); check(eq([k.pc, k.instr >>> 0, k.alu_result, k.branch_taken, k.wb_data], expSC[t].map((v) => v >>> 0)), `single-cycle trace tick ${t}`); }
}

// ---- pipeline probe trace of hazards_demo.s (measured on circuit Pipeline):
// tick: [PC, instr_id, stall, pc_src_ex, ForwardA, ForwardB, alu_result_ex, wb_data]
const expP = {
  1: [4, 0x06400093, 0, 0, 0, 0, 0, 0], 2: [8, 0x00102023, 0, 0, 0, 0, 0x64, 0], 3: [0xc, 0x00002103, 0, 0, 0, 2, 0, 0],
  4: [0x10, 0x00110193, 1, 0, 0, 0, 0, 0x64], 5: [0x10, 0x00110193, 0, 0, 2, 0, 0x64, 0], 6: [0x14, 0x00218233, 0, 0, 1, 0, 0x65, 0x64],
  7: [0x18, 0x00420663, 0, 0, 2, 0, 0xc9, 0x64], 8: [0x1c, 0x00100293, 0, 1, 2, 2, 0, 0x65], 9: [0x20, 0, 0, 0, 0, 0, 0x64, 0xc9],
  10: [0x24, 0x00700393, 0, 0, 0, 0, 0, 0], 11: [0x28, 0x6f, 0, 0, 0, 0, 7, 0x64], 12: [0x2c, 0, 0, 1, 0, 0, 0, 0],
  13: [0x24, 0, 0, 0, 0, 0, 0, 7], 14: [0x28, 0x6f, 0, 0, 0, 0, 0, 0x28],
};
const hp = new RV.Pipeline(progs.hazards_demo.words);
for (let t = 1; t <= 14; t++) {
  hp.step();
  const k = hp.comb();
  check(eq([hp.pc, hp.ifid.instr, k.stall, k.pc_src_ex, k.ForwardA, k.ForwardB, k.alu_result_ex, k.wb_data], expP[t]), `pipeline trace tick ${t}: got ` +
    JSON.stringify([hp.pc, hp.ifid.instr, k.stall, k.pc_src_ex, k.ForwardA, k.ForwardB, k.alu_result_ex, k.wb_data].map((v) => v.toString(16))));
}
check(hp.regs[5] === 0 && hp.regs[6] === 0 && hp.regs[7] === 7 && hp.regs[4] === 0xc9, "hazards_demo: x5 = x6 = 0, x7 = 7, x4 = 0xc9");

// ---- pipeline demo.s: after 20 ticks PC 0x14, x10 0x1b, x11 7 (measured on the circuit)
const dp = new RV.Pipeline(demo);
for (let t = 0; t < 20; t++) dp.step();
check(dp.pc === 0x14 && dp.regs[10] === 0x1b && dp.regs[11] === 7, `pipeline demo after 20 ticks: PC ${dp.pc.toString(16)} x10 ${dp.regs[10].toString(16)} x11 ${dp.regs[11]}`);

console.log(fails ? `${fails} FAILED` : "ALL PASSED");
process.exit(fails ? 1 : 0);
