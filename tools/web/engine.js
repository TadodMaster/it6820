/* RV32I engine for the web visualisation: single-cycle CPU and 5-stage pipeline.
 * It mirrors the Logisim circuits block by block (same signal names), so the page shows what the circuits do.
 * Pure JavaScript, no dependencies: used by the page and by tools/web/test_engine.js (node). */
(function (root) {
  "use strict";

  const u32 = (v) => v >>> 0;
  const sx = (v, bits) => (v << (32 - bits)) >> (32 - bits);
  const hex = (v, n) => "0x" + u32(v).toString(16).padStart(n === undefined ? 8 : n, "0");

  // ---------------------------------------------------------------- InstructionDecode
  function decode(w) {
    return { opcode: w & 0x7f, rd: (w >>> 7) & 31, f3: (w >>> 12) & 7, rs1: (w >>> 15) & 31, rs2: (w >>> 20) & 31, f7: (w >>> 25) & 0x7f };
  }

  // ---------------------------------------------------------------- MainControl
  function control(opcode) {
    const R = opcode === 0x33, I = opcode === 0x13, L = opcode === 0x03, S = opcode === 0x23, B = opcode === 0x63;
    const LUI = opcode === 0x37, AU = opcode === 0x17, J = opcode === 0x6f, JR = opcode === 0x67;
    const n = (b) => (b ? 1 : 0);
    return {
      RegWrite: n(R || I || L || LUI || AU || J || JR),
      ALUSrc: n(I || L || S || LUI || AU || JR),
      MemWrite: n(S), MemRead: n(L), IsBranch: n(B), IsJAL: n(J), IsJALR: n(JR),
      ALUOp: (n(R || I) << 1) | n(I || B),
      ImmSel: (n(J) << 2) | (n(B || LUI || AU) << 1) | n(S || LUI || AU),
      ASel: (n(LUI) << 1) | n(AU),
      WBSel: (n(J || JR) << 1) | n(L),
    };
  }
  const NOCTRL = control(0);

  // ---------------------------------------------------------------- ImmGen
  function immgen(w, sel) {
    switch (sel) {
      case 0: return u32(sx(w >>> 20, 12));
      case 1: return u32(sx(((w >>> 25) << 5) | ((w >>> 7) & 31), 12));
      case 2: return u32(sx(((w >>> 31) << 12) | (((w >>> 7) & 1) << 11) | (((w >>> 25) & 63) << 5) | (((w >>> 8) & 15) << 1), 13));
      case 3: return u32(w & 0xfffff000);
      case 4: return u32(sx(((w >>> 31) << 20) | (((w >>> 12) & 255) << 12) | (((w >>> 20) & 1) << 11) | (((w >>> 21) & 1023) << 1), 21));
      default: return 0;
    }
  }

  // ---------------------------------------------------------------- ALUControl and ALU
  const ALU_NAMES = ["ADD", "SUB", "AND", "OR", "XOR", "SLL", "SRL", "SRA", "SLT", "SLTU"];
  function aluctrl(aluop, f3, f7) {
    if (aluop === 0) return 0;
    if (aluop === 1) return 1;
    const b5 = (f7 >>> 5) & 1;
    switch (f3) {
      case 0: return aluop === 2 ? (b5 ? 1 : 0) : 0;
      case 1: return 5;
      case 2: return 8;
      case 3: return 9;
      case 4: return 4;
      case 5: return b5 ? 7 : 6;
      case 6: return 3;
      default: return 2;
    }
  }
  function alu(a, b, c) {
    a = u32(a); b = u32(b);
    switch (c) {
      case 0: return u32(a + b);
      case 1: return u32(a - b);
      case 2: return u32(a & b);
      case 3: return u32(a | b);
      case 4: return u32(a ^ b);
      case 5: return u32(a << (b & 31));
      case 6: return u32(a >>> (b & 31));
      case 7: return u32((a | 0) >> (b & 31));
      case 8: return (a | 0) < (b | 0) ? 1 : 0;
      case 9: return a < b ? 1 : 0;
      default: return 0;
    }
  }

  // ---------------------------------------------------------------- BranchUnit
  function branch(a, b, f3, isBranch) {
    a = u32(a); b = u32(b);
    let cond = 0;
    switch (f3) {
      case 0: cond = a === b; break;
      case 1: cond = a !== b; break;
      case 4: cond = (a | 0) < (b | 0); break;
      case 5: cond = (a | 0) >= (b | 0); break;
      case 6: cond = a < b; break;
      case 7: cond = a >= b; break;
      default: cond = 0;
    }
    return isBranch && cond ? 1 : 0;
  }

  // ---------------------------------------------------------------- Memory: RAM + LoadExtract + StoreMerge
  function loadExtract(word, addr, f3) {
    const boff = addr & 3;
    const byte = (word >>> (8 * boff)) & 0xff;
    const half = (word >>> (16 * ((addr >>> 1) & 1))) & 0xffff;
    switch (f3) {
      case 0: return u32(sx(byte, 8));
      case 1: return u32(sx(half, 16));
      case 4: return byte;
      case 5: return half;
      default: return u32(word);
    }
  }
  // 16-row ROM {size, boff} -> 4 byte enables, exactly as in the circuit
  const EN_ROM = [1, 2, 4, 8, 3, 3, 12, 12, 15, 15, 15, 15, 15, 15, 15, 15];
  function storeMerge(oldWord, wdata, f3, addr) {
    const size = f3 & 3, boff = addr & 3;
    const en = EN_ROM[(size << 2) | boff];
    const wd = [0, 1, 2, 3].map((i) => (wdata >>> (8 * i)) & 0xff);
    const src = [wd[0], [wd[0], wd[1], wd[1], wd[1]][size], [wd[0], wd[0], wd[2], wd[2]][size], [wd[0], wd[1], wd[3], wd[3]][size]];
    let out = 0;
    for (let i = 0; i < 4; i++) {
      const old = (oldWord >>> (8 * i)) & 0xff;
      out |= ((en >> i) & 1 ? src[i] : old) << (8 * i);
    }
    return { word: u32(out), en };
  }

  function makeRam() { return new Array(256).fill(0); }
  const widx = (addr) => (addr >>> 2) & 255;

  function fresh(rom) {
    const r = new Array(256).fill(0);
    rom.forEach((w, i) => { r[i] = u32(w); });
    return r;
  }

  // ================================================================ single-cycle CPU (circuit `main`)
  class SingleCycle {
    constructor(rom) { this.rom = fresh(rom); this.reset(); }
    reset() { this.pc = 0; this.regs = new Array(32).fill(0); this.ram = makeRam(); this.tick = 0; this.last = null; }
    /** Combinational view of the instruction at the current PC (what the probes show before the tick). */
    peek() {
      const pc = this.pc, w = this.rom[(pc >>> 2) & 255];
      const d = decode(w), c = control(d.opcode);
      const imm = immgen(w, c.ImmSel);
      const rs1d = d.rs1 ? this.regs[d.rs1] : 0, rs2d = d.rs2 ? this.regs[d.rs2] : 0;
      const alu_a = [rs1d, pc, 0, 0][c.ASel], alu_b = c.ALUSrc ? imm : rs2d;
      const ctrl = aluctrl(c.ALUOp, d.f3, d.f7);
      const alu_result = alu(alu_a, alu_b, ctrl);
      const branch_taken = branch(rs1d, rs2d, d.f3, c.IsBranch);
      const word = this.ram[widx(alu_result)];
      const mem_rdata = loadExtract(word, alu_result, d.f3);
      const pc_plus4 = u32(pc + 4), pc_target = u32(pc + imm), jalr_target = u32(alu_result & 0xfffffffe);
      const take_target = branch_taken || c.IsJAL ? 1 : 0;
      const pc_a = take_target ? pc_target : pc_plus4;
      const next_pc = c.IsJALR ? jalr_target : pc_a;
      const wb_data = [alu_result, mem_rdata, pc_plus4, 0][c.WBSel];
      const sm = storeMerge(word, rs2d, d.f3, alu_result);
      return Object.assign({ pc, instr: w }, d, c, { imm, rs1_data: rs1d, rs2_data: rs2d, alu_a, alu_b, ALUCtrl: ctrl,
        alu_result, branch_taken, mem_rdata, pc_plus4, pc_target, jalr_target, take_target, next_pc, wb_data,
        new_word: sm.word, byte_en: sm.en, ram_word: word });
    }
    step() {
      const s = this.peek();
      const before = this.regs.slice();
      if (s.MemWrite) this.ram[widx(s.alu_result)] = s.new_word;
      if (s.RegWrite && s.rd !== 0) this.regs[s.rd] = s.wb_data;
      this.pc = s.next_pc;
      this.tick++;
      s.reg_written = s.RegWrite && s.rd !== 0 ? s.rd : -1;
      s.reg_changed = s.reg_written >= 0 && before[s.rd] !== this.regs[s.rd];
      s.mem_written = s.MemWrite ? widx(s.alu_result) : -1;
      this.last = s;
      return s;
    }
  }

  // ================================================================ 5-stage pipeline (circuit `Pipeline`)
  const ZERO_EX = () => ({ ctrl: Object.assign({}, NOCTRL), pc: 0, rs1d: 0, rs2d: 0, imm: 0, rs1: 0, rs2: 0, rd: 0, f3: 0, f7: 0, id: -1, flush: false, instr: 0 });
  class Pipeline {
    constructor(rom, text) {
      this.rom = fresh(rom);
      this.text = text || {};          // pc -> source text, for the display only
      this.reset();
    }
    reset() {
      this.pc = 0; this.regs = new Array(32).fill(0); this.ram = makeRam(); this.tick = 0;
      this.ifid = { pc: 0, instr: 0, id: -1, flush: false };
      this.idex = ZERO_EX();
      this.exmem = { alu_result: 0, store_data: 0, pc4: 0, rd: 0, f3: 0, RegWrite: 0, MemWrite: 0, MemRead: 0, WBSel: 0, id: -1, instr: 0 };
      this.memwb = { alu_result: 0, mem_rdata: 0, pc4: 0, rd: 0, RegWrite: 0, WBSel: 0, id: -1, instr: 0 };
      this.fid = 0; this.seq = 1;       // id of the instruction at the IF stage; next free id
      this.fetched = { 0: { pc: 0 } };  // id -> {pc}
      this.history = [];
      this.snap();
    }
    /** All combinational signals of the current state (what the probes of circuit Pipeline show). */
    comb() {
      const S = this, ie = S.idex, em = S.exmem, mw = S.memwb, fi = S.ifid;
      const dID = decode(fi.instr), cID = control(dID.opcode);
      const stall = ie.ctrl.MemRead && ie.rd !== 0 && (ie.rd === dID.rs1 || ie.rd === dID.rs2) ? 1 : 0;
      const run = stall ? 0 : 1;
      // EX stage
      const memValid = em.RegWrite && em.rd !== 0, wbValid = mw.RegWrite && mw.rd !== 0;
      const fwd = (rs) => {
        const fromMem = memValid && em.rd === rs, fromWb = wbValid && mw.rd === rs && !fromMem;
        return fromMem ? 2 : fromWb ? 1 : 0;
      };
      const ForwardA = fwd(ie.rs1), ForwardB = fwd(ie.rs2);
      const wb_data = [mw.alu_result, mw.mem_rdata, mw.pc4, 0][mw.WBSel];
      const fwd_mem_val = (em.WBSel >> 1) & 1 ? em.pc4 : em.alu_result;
      const opA = [ie.rs1d, wb_data, fwd_mem_val, ie.rs1d][ForwardA];
      const opB = [ie.rs2d, wb_data, fwd_mem_val, ie.rs2d][ForwardB];
      const c = ie.ctrl;
      const alu_a = [opA, ie.pc, 0, 0][c.ASel], alu_b = c.ALUSrc ? ie.imm : opB;
      const ALUCtrl = aluctrl(c.ALUOp, ie.f3, ie.f7);
      const alu_result_ex = alu(alu_a, alu_b, ALUCtrl);
      const branch_taken = branch(opA, opB, ie.f3, c.IsBranch);
      const pc_target = u32(ie.pc + ie.imm), jalr_target = u32(alu_result_ex & 0xfffffffe);
      const target_ex = c.IsJALR ? jalr_target : pc_target;
      const pc_src_ex = branch_taken || c.IsJAL || c.IsJALR ? 1 : 0;
      const pc_plus4_ex = u32(ie.pc + 4);
      // MEM stage
      const mem_word = S.ram[widx(em.alu_result)];
      const mem_rdata_mem = loadExtract(mem_word, em.alu_result, em.f3);
      const sm = storeMerge(mem_word, em.store_data, em.f3, em.alu_result);
      // ID stage
      const imm_id = immgen(fi.instr, cID.ImmSel);
      const rs1_data_id = dID.rs1 ? S.regs[dID.rs1] : 0, rs2_data_id = dID.rs2 ? S.regs[dID.rs2] : 0;
      const bubble = stall || pc_src_ex ? 1 : 0;
      // IF stage
      const instr_if = S.rom[(S.pc >>> 2) & 255];
      const instr_in = pc_src_ex ? 0 : instr_if;
      const next_pc = pc_src_ex ? target_ex : u32(S.pc + 4);
      return { stall, run, ForwardA, ForwardB, wb_data, fwd_mem_val, opA, opB, alu_a, alu_b, ALUCtrl, alu_result_ex, branch_taken,
        pc_target, jalr_target, target_ex, pc_src_ex, pc_plus4_ex, mem_rdata_mem, new_word: sm.word, mem_word,
        dID, cID, imm_id, rs1_data_id, rs2_data_id, bubble, instr_if, instr_in, next_pc, pc_if: S.pc };
    }
    snap() {
      const k = this.comb();
      const cell = (id, flush) => ({ id, flush: !!flush });
      this.history.push({
        tick: this.tick, IF: this.fid, ID: this.ifid.id, IDflush: this.ifid.flush, EX: this.idex.id, EXflush: this.idex.flush,
        MEM: this.exmem.id, WB: this.memwb.id, stall: k.stall, pc_src_ex: k.pc_src_ex, ForwardA: k.ForwardA, ForwardB: k.ForwardB, pc: this.pc,
      });
      return cell;
    }
    step() {
      const S = this, k = S.comb(), ie = S.idex, em = S.exmem, mw = S.memwb, fi = S.ifid;
      // ---- rising edge: every register loads the value computed from the current state
      const nPC = k.run ? k.next_pc : S.pc;
      const nIFID = k.run ? { pc: S.pc, instr: k.instr_in, id: S.fid, flush: !!k.pc_src_ex } : fi;
      const d = k.dID;
      const nIDEX = {
        ctrl: k.bubble ? Object.assign({}, NOCTRL) : k.cID, pc: fi.pc, rs1d: k.rs1_data_id, rs2d: k.rs2_data_id, imm: k.imm_id,
        rs1: d.rs1, rs2: d.rs2, rd: d.rd, f3: d.f3, f7: d.f7,
        id: k.stall ? -1 : fi.flush ? -1 : fi.id, flush: !k.stall && !!k.pc_src_ex && !fi.flush && fi.id >= 0, instr: k.bubble ? 0 : fi.instr,
      };
      const nEXMEM = {
        alu_result: k.alu_result_ex, store_data: k.opB, pc4: k.pc_plus4_ex, rd: ie.rd, f3: ie.f3,
        RegWrite: ie.ctrl.RegWrite, MemWrite: ie.ctrl.MemWrite, MemRead: ie.ctrl.MemRead, WBSel: ie.ctrl.WBSel, id: ie.flush ? -1 : ie.id, instr: ie.instr,
      };
      const nMEMWB = { alu_result: em.alu_result, mem_rdata: k.mem_rdata_mem, pc4: em.pc4, rd: em.rd, RegWrite: em.RegWrite, WBSel: em.WBSel, id: em.id, instr: em.instr };
      if (em.MemWrite) S.ram[widx(em.alu_result)] = k.new_word;
      // ids of the fetched instructions
      let nfid = S.fid;
      if (k.run) { nfid = S.seq++; S.fetched[nfid] = { pc: nPC }; }
      S.pc = nPC; S.ifid = nIFID; S.idex = nIDEX; S.exmem = nEXMEM; S.memwb = nMEMWB; S.fid = nfid;
      // ---- falling edge: the register file writes what the MEM/WB register now holds
      const w = S.comb();
      S.wbWritten = -1;
      if (nMEMWB.RegWrite && nMEMWB.rd !== 0) { S.regs[nMEMWB.rd] = w.wb_data; S.wbWritten = nMEMWB.rd; }
      S.tick++;
      S.snap();
      return k;
    }
  }

  const api = { u32, sx, hex, decode, control, immgen, aluctrl, alu, branch, loadExtract, storeMerge, SingleCycle, Pipeline, ALU_NAMES, EN_ROM };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.RV = api;
})(typeof self !== "undefined" ? self : this);
