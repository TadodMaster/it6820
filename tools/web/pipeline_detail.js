/* ================================================================= PIPELINE: detailed datapath (inlined into the page) */
const PD = { svg: $("#pdSvg"), els: {} };
// boxes: id -> [x, y, w, h, title, kind, shape]
const PB = {
  // IF
  PC: [26, 372, 62, 50, "PC", "reg", "reg"], ADD4: [26, 250, 62, 36, "PC + 4", "", ""], NPCM: [108, 160, 28, 70, "", "", "mux"],
  ROM: [120, 360, 92, 76, "ROM lệnh", "mem", ""], FLM: [226, 372, 24, 50, "", "", "mux"],
  IFID: [268, 330, 58, 130, "IF/ID", "reg", "regbar"],
  // ID
  DEC: [352, 70, 124, 42, "InstructionDecode", "", ""], CTRL: [352, 126, 124, 42, "MainControl", "ctl", ""], IMM: [352, 182, 124, 42, "ImmGen", "", ""],
  RF: [352, 250, 124, 130, "RegisterFile", "reg", ""], HAZ: [352, 430, 124, 50, "HazardUnit", "ctl", ""], BUBM: [526, 126, 26, 60, "", "ctl", "mux"],
  IDEX: [614, 60, 86, 420, "ID/EX", "reg", "regbar"],
  // EX
  FWD: [736, 72, 120, 44, "ForwardingUnit", "ctl", ""], ALUC: [900, 72, 110, 38, "ALUControl", "ctl", ""],
  OPA: [736, 170, 28, 80, "", "", "mux"], OPB: [736, 280, 28, 80, "", "", "mux"], ALA: [806, 170, 26, 64, "", "", "mux"], ALB: [806, 280, 26, 64, "", "", "mux"],
  ALU: [880, 160, 104, 150, "ALU", "", "alu"], BR: [880, 340, 104, 42, "BranchUnit", "", ""],
  ADDT: [740, 420, 104, 40, "PC + imm", "", ""], JALR: [862, 420, 112, 40, "ALU & ~1", "", ""], TGT: [996, 420, 26, 56, "", "", "mux"], PCS: [996, 340, 34, 40, "OR", "ctl", ""],
  EXMEM: [1072, 150, 74, 300, "EX/MEM", "reg", "regbar"], FWDM: [1066, 96, 82, 40, "fwd_mem_val", "", ""],
  // MEM
  MEM: [1170, 230, 96, 160, "Memory", "mem", ""], MEMWB: [1292, 200, 76, 220, "MEM/WB", "reg", "regbar"],
  // WB
  WBM: [1396, 250, 32, 130, "", "", "mux"],
};
const PBANDS = [["IF - Nạp lệnh", 10, 252, COL.IF], ["ID - Giải mã", 336, 276, COL.ID], ["EX - Thực thi", 702, 360, COL.EX], ["MEM - Bộ nhớ", 1152, 138, COL.MEM], ["WB - Ghi lại", 1370, 120, COL.WB]];
const PW = {
  // IF
  pcrom: ["", [88, 397], [120, 397]], pcadd: ["", [57, 372], [57, 286]], add4m: ["", [88, 268], [100, 268], [100, 185], [108, 185]],
  npcpc: ["", [136, 195], [150, 195], [150, 128], [16, 128], [16, 397], [26, 397]], romfl: ["", [212, 397], [226, 397]], flifid: ["", [250, 397], [268, 397]],
  // ID
  bus: ["", [326, 397], [338, 397], [338, 91]], bus1: ["", [338, 91], [352, 91]], bus2: ["", [338, 203], [352, 203]], bus3: ["", [338, 270], [352, 270]], bus4: ["", [338, 455], [352, 455]],
  deccl: ["", [414, 112], [414, 126]], ctlbub: ["", [476, 147], [526, 147]], bubidex: ["", [552, 156], [614, 156]], immidex: ["", [476, 203], [614, 203]],
  rs1idex: ["", [476, 300], [614, 300]], rs2idex: ["", [476, 350], [614, 350]], wbrf: ["", [1428, 315], [1458, 315], [1458, 585], [330, 585], [330, 330], [352, 330]],
  stallw: ["ctl", [476, 455], [539, 455], [539, 186]],
  // EX
  ida: ["", [700, 190], [736, 190]], idb: ["", [700, 300], [736, 300]], idpc: ["", [700, 130], [780, 130], [780, 217], [806, 217]], idimm: ["", [700, 372], [790, 372], [790, 330], [806, 330]],
  opaal: ["", [764, 210], [806, 190]], opbal: ["", [764, 320], [806, 300]], opbsd: ["", [764, 345], [772, 345], [772, 398], [1048, 398], [1048, 330], [1072, 330]],
  alua: ["", [832, 202], [880, 200]], alub: ["", [832, 312], [880, 270]],
  alures: ["", [984, 235], [1072, 235]], aluc: ["ctl", [955, 110], [955, 160]], fwdctl: ["ctl", [796, 116], [796, 150], [750, 150], [750, 170]],
  brpc: ["", [984, 361], [996, 361]], tgtpcs: ["", [1009, 420], [1009, 380]],
  addtt: ["", [792, 460], [792, 482], [1001, 482], [1001, 476]], jalrt: ["", [918, 460], [918, 478], [1011, 478], [1011, 476]],
  // MEM / WB
  exmemaddr: ["", [1146, 260], [1170, 260]], exmemdata: ["", [1146, 340], [1170, 340]], memw: ["", [1266, 300], [1292, 300]], exw: ["", [1146, 215], [1280, 215], [1280, 232], [1292, 232]],
  w1: ["", [1368, 268], [1396, 268]], w2: ["", [1368, 300], [1396, 300]], w3: ["", [1368, 336], [1396, 336]],
  // control lines along the top
  tgtnpc: ["", [1022, 448], [1040, 448], [1040, 40], [96, 40], [96, 215], [108, 215]],
  pcsrc: ["ctl", [1030, 360], [1052, 360], [1052, 48], [122, 48], [122, 160]], pcsrcfl: ["ctl", [238, 48], [238, 372]], pcsrcbub: ["ctl", [539, 48], [539, 126]],
  // forwarding paths (trunk + branches)
  fwdwbT: ["fwd", [1330, 420], [1330, 520], [710, 520], [710, 206]], fwdwbA: ["fwd", [710, 210], [736, 210]], fwdwbB: ["fwd", [710, 320], [736, 320]], fwdwbB2: ["fwd", [710, 210], [710, 320]],
  fwdmemT: ["fwd", [1107, 450], [1107, 500], [722, 500], [722, 230]], fwdmemA: ["fwd", [722, 230], [736, 230]], fwdmemB: ["fwd", [722, 340], [736, 340]], fwdmemB2: ["fwd", [722, 230], [722, 340]],
  fwdmemsrc: ["fwd", [1107, 136], [1107, 150]],
};
function pdShape(x, y, w, h, shape) {
  if (shape === "mux") return `M${x},${y}L${x + w},${y + 10}L${x + w},${y + h - 10}L${x},${y + h}Z`;
  if (shape === "alu") return `M${x},${y}L${x + w},${y + h * 0.22}L${x + w},${y + h * 0.78}L${x},${y + h}L${x},${y + h * 0.56}L${x + 16},${y + h / 2}L${x},${y + h * 0.44}Z`;
  return null;
}
function pdBuild() {
  const s = PD.svg; s.innerHTML = ""; PD.els = {};
  PBANDS.forEach(([label, x, w, c]) => {
    el("rect", { class: "band", x, y: 52, width: w, height: 548, rx: 14, fill: c }, s);
    el("text", { class: "bandlab", x: x + 10, y: 70, style: `fill:${c}` }, s, label);
  });
  PD.els.chips = [];
  PBANDS.forEach(([, x, w, c]) => { PD.els.chips.push(el("text", { x: x + w / 2, y: 30, "text-anchor": "middle", style: `font:700 13px ui-monospace,Consolas,monospace;fill:${c}` }, s, "")); });
  for (const id in PW) { const [k, ...pts] = PW[id]; PD.els["w_" + id] = el("polyline", { class: "wire " + k, points: pts.map((p) => p.join(",")).join(" ") }, s); }
  for (const id in PB) {
    const [x, y, w, h, title, kind, shape] = PB[id];
    const g = el("g", {}, s), sp = pdShape(x, y, w, h, shape);
    PD.els["b_" + id] = sp ? el("path", { class: "box " + kind, d: sp }, g) : el("rect", { class: "box " + kind, x, y, width: w, height: h, rx: shape === "reg" ? 4 : shape === "regbar" ? 6 : 8 }, g);
    if (shape === "reg") el("path", { d: `M${x},${y + h - 12}L${x + 8},${y + h - 6}L${x},${y + h}`, fill: "none", stroke: "var(--muted)", "stroke-width": 1.2 }, g);
    const tx = shape === "alu" ? x + w / 2 + 6 : x + w / 2;
    if (title) el("text", { class: "title", x: tx, y: y + (shape === "regbar" ? 14 : 15), "text-anchor": "middle" }, g, title);
    const base = shape === "mux" ? y + h / 2 - 2 : shape === "alu" ? y + h / 2 - 22 : shape === "regbar" ? y + 32 : y + 29;
    for (let i = 1; i <= 9; i++) PD.els[`v${i}_${id}`] = el("text", { class: "val", x: tx, y: base + (i - 1) * 12, "text-anchor": "middle" }, g, "");
  }
  const tag = (id, x, y, text, anchor) => { PD.els["t_" + id] = el("text", { class: "tag", x, y, "text-anchor": anchor || "start" }, s, text); };
  tag("zeroFl", 222, 417, "0", "end"); tag("instrFl", 222, 388, "ROM", "end");
  tag("tgtT", 104, 223, "đích", "end"); tag("pc4T", 104, 178, "+4", "end");
  tag("zeroB", 520, 180, "0", "end"); tag("ctlB", 520, 150, "ctrl", "end");
  tag("wbA", 733, 214, "wb", "end"); tag("memA", 733, 234, "mem", "end"); tag("regA", 733, 194, "reg", "end");
  tag("wbB", 733, 324, "wb", "end"); tag("memB", 733, 344, "mem", "end"); tag("regB", 733, 304, "reg", "end");
  tag("pcAl", 803, 221, "pc", "end"); tag("zAl", 803, 231, "0", "end"); tag("opAl", 803, 194, "opA", "end"); tag("opBl", 803, 304, "opB", "end"); tag("immBl", 803, 334, "imm", "end");
  tag("stallT", 476, 475, "stall", "start"); tag("holdT", 18, 118, "", "start"); tag("holdIf", 268, 478, "", "start");
  tag("wbd", 1440, 312, "wb_data", "start");
  tag("fwdwbT", 1000, 536, "forward từ MEM/WB (01)", "middle"); tag("fwdmemT", 900, 516, "forward từ EX/MEM (10)", "middle");
  tag("pcsT", 1034, 62, "pc_src_ex", "start"); tag("tgtT2", 1044, 440, "target_ex", "start");
  tag("alurT", 988, 232, "alu_result", "start");
  tag("rd1", 1330, 442, "rd, RegWrite, WBSel đi cùng lệnh", "middle");
  tag("note", 20, 618, "Nét đứt cam = tín hiệu điều khiển;  nét xanh lá = forwarding;  hộp đỏ = stall hoặc flush ở khối đó", "start");
}
function pdDraw() {
  const cpu = PL.cpu, k = cpu.comb(), E = PD.els, fi = cpu.ifid, ie = cpu.idex, em = cpu.exmem, mw = cpu.memwb, c = ie.ctrl;
  const pID = fi.id >= 0 && !fi.flush, pEX = ie.id >= 0 && !ie.flush, pMEM = em.id >= 0, pWB = mw.id >= 0;
  const bon = (id, f, bad) => { const e = E["b_" + id]; e.classList.toggle("on", !!f && !bad); e.classList.toggle("bad", !!bad); };
  const won = (id, f) => E["w_" + id].classList.toggle("on", !!f);
  const jmp = c.IsBranch || c.IsJAL || c.IsJALR;
  bon("PC", 1); bon("ADD4", 1); bon("NPCM", 1); bon("ROM", 1); bon("FLM", k.pc_src_ex, k.pc_src_ex);
  bon("IFID", fi.id >= 0, 0); bon("DEC", pID); bon("CTRL", pID); bon("IMM", pID); bon("RF", pID || (mw.RegWrite && mw.rd));
  bon("HAZ", pID, k.stall); bon("BUBM", k.bubble, k.stall || k.pc_src_ex);
  bon("IDEX", ie.id >= 0, 0);
  bon("FWD", pEX); bon("OPA", pEX); bon("OPB", pEX); bon("ALA", pEX); bon("ALB", pEX); bon("ALU", pEX); bon("ALUC", pEX);
  bon("BR", pEX && c.IsBranch); bon("ADDT", pEX && (c.IsBranch || c.IsJAL)); bon("JALR", pEX && c.IsJALR); bon("TGT", pEX && jmp); bon("PCS", k.pc_src_ex);
  bon("EXMEM", pMEM); bon("FWDM", k.ForwardA === 2 || k.ForwardB === 2);
  bon("MEM", pMEM && (em.MemRead || em.MemWrite)); bon("MEMWB", pWB); bon("WBM", pWB && mw.RegWrite);
  const fa = k.ForwardA, fb = k.ForwardB;
  const W_ON = { pcrom: 1, pcadd: 1, add4m: !k.pc_src_ex, npcpc: 1, romfl: 1, flifid: 1, bus: pID, bus1: pID, bus2: pID, bus3: pID, bus4: pID, deccl: pID, ctlbub: pID, bubidex: pEX || k.bubble, immidex: pID,
    rs1idex: pID, rs2idex: pID, wbrf: pWB && mw.RegWrite && mw.rd, stallw: k.stall, ida: pEX && fa === 0, idb: pEX && fb === 0, idpc: pEX && c.ASel === 1, idimm: pEX && c.ALUSrc,
    opaal: pEX && c.ASel === 0, opbal: pEX && !c.ALUSrc, opbsd: pEX && c.MemWrite, alua: pEX, alub: pEX, alures: pEX, aluc: pEX, fwdctl: fa || fb,
    brpc: pEX && c.IsBranch, tgtpcs: pEX && jmp, addtt: pEX && (c.IsBranch || c.IsJAL), jalrt: pEX && c.IsJALR,
    exmemaddr: pMEM && (em.MemRead || em.MemWrite), exmemdata: pMEM && em.MemWrite, memw: pMEM && em.MemRead, exw: pMEM,
    w1: pWB && mw.RegWrite && mw.WBSel === 0, w2: pWB && mw.RegWrite && mw.WBSel === 1, w3: pWB && mw.RegWrite && mw.WBSel === 2,
    tgtnpc: k.pc_src_ex, pcsrc: k.pc_src_ex, pcsrcfl: k.pc_src_ex, pcsrcbub: k.pc_src_ex,
    fwdwbT: fa === 1 || fb === 1, fwdwbA: fa === 1, fwdwbB: fb === 1, fwdwbB2: fb === 1 && fa !== 1 ? 0 : fb === 1 && fa === 1,
    fwdmemT: fa === 2 || fb === 2, fwdmemA: fa === 2, fwdmemB: fb === 2, fwdmemB2: fa === 2 && fb === 2, fwdmemsrc: fa === 2 || fb === 2 };
  for (const id in PW) won(id, W_ON[id]);
  // chips
  const nm = (id, flush) => (flush ? "X flush" : id < 0 ? "bubble" : plName(id));
  [nm(cpu.fid), nm(fi.id, fi.flush), nm(ie.id, ie.flush), nm(em.id), nm(mw.id)].forEach((t, i) => { E.chips[i].textContent = t; });
  // values
  const V = (id, ...ls) => { for (let i = 1; i <= 9; i++) E[`v${i}_${id}`].textContent = ls[i - 1] || ""; E[`v1_${id}`].classList.add("hot"); };
  const sel = (n) => ["reg", "wb", "mem", "reg"][n];
  V("PC", hx(cpu.pc)); V("ADD4", hx(u32(cpu.pc + 4))); V("NPCM", ""); V("ROM", hx(k.instr_if)); V("FLM", "");
  V("IFID", "pc_id", hx(fi.pc, 4), "instr_id", hx(fi.instr).slice(2));
  V("DEC", `rd=${k.dID.rd} rs1=${k.dID.rs1} rs2=${k.dID.rs2}`, `f3=${k.dID.f3} f7=${hx(k.dID.f7, 2)}`);
  V("CTRL", `RW=${k.cID.RegWrite} AS=${k.cID.ALUSrc} MW=${k.cID.MemWrite} MR=${k.cID.MemRead}`, `ALUOp=${k.cID.ALUOp} Imm=${k.cID.ImmSel} WB=${k.cID.WBSel}`);
  V("IMM", hx(k.imm_id)); V("RF", "rs1_data", hx(k.rs1_data_id), "rs2_data", hx(k.rs2_data_id), "", `ghi x${mw.RegWrite && mw.rd ? mw.rd : "-"}`);
  V("HAZ", k.stall ? "STALL = 1" : "stall = 0", k.stall ? "giữ PC, IF/ID" : "load-use? không");
  V("BUBM", k.bubble ? "0" : "");
  V("IDEX", "pc_ex " + hx(ie.pc, 4).slice(2), "rs1_data", hx(ie.rs1d).slice(2), "rs2_data", hx(ie.rs2d).slice(2), "imm " + hx(ie.imm).slice(2).replace(/^0+(?=.)/, ""), `rs1=${ie.rs1} rs2=${ie.rs2}`, `rd=${ie.rd} f3=${ie.f3}`, `RW${c.RegWrite}AS${c.ALUSrc}MW${c.MemWrite}MR${c.MemRead}`);
  V("FWD", `ForwardA = ${fa.toString(2).padStart(2, "0")}`, `ForwardB = ${fb.toString(2).padStart(2, "0")}`);
  V("OPA", ""); V("OPB", ""); V("ALA", ""); V("ALB", "");
  V("ALUC", RV.ALU_NAMES[k.ALUCtrl], `ALUCtrl = ${k.ALUCtrl}`);
  V("ALU", `A ${hx(k.alu_a)}`, `B ${hx(k.alu_b)}`, `= ${hx(k.alu_result_ex)}`);
  V("BR", c.IsBranch ? (k.branch_taken ? "RẼ" : "không rẽ") : "-"); V("ADDT", hx(k.pc_target)); V("JALR", hx(k.jalr_target)); V("TGT", ""); V("PCS", `${k.pc_src_ex}`);
  V("EXMEM", "alu_result", hx(em.alu_result).slice(2), "store_data", hx(em.store_data).slice(2), "pc4", hx(em.pc4, 4).slice(2), `rd=${em.rd}`, `RW=${em.RegWrite} MW=${em.MemWrite}`, `MR=${em.MemRead} WB=${em.WBSel}`);
  V("FWDM", hx(k.fwd_mem_val));
  V("MEM", em.MemWrite ? "ghi" : em.MemRead ? "đọc" : "-", em.MemRead || em.MemWrite ? `từ[${(em.alu_result >>> 2) & 255}]` : "", em.MemWrite ? hx(k.new_word) : em.MemRead ? hx(k.mem_rdata_mem) : "");
  V("MEMWB", "alu_result", hx(mw.alu_result).slice(2), "mem_rdata", hx(mw.mem_rdata).slice(2), "pc4", hx(mw.pc4, 4).slice(2), `rd=${mw.rd}`, `RW=${mw.RegWrite} WB=${mw.WBSel}`);
  V("WBM", "");
  const tg = (id, f, bad) => { E["t_" + id].classList.toggle("on", !!f); E["t_" + id].style.fill = bad ? "var(--bad)" : ""; };
  tg("zeroFl", k.pc_src_ex, 1); tg("instrFl", !k.pc_src_ex); tg("tgtT", k.pc_src_ex); tg("pc4T", !k.pc_src_ex);
  tg("regA", pEX && fa === 0); tg("wbA", fa === 1); tg("memA", fa === 2); tg("regB", pEX && fb === 0); tg("wbB", fb === 1); tg("memB", fb === 2);
  tg("opAl", pEX && c.ASel === 0); tg("pcAl", pEX && c.ASel === 1); tg("zAl", pEX && c.ASel === 2); tg("opBl", pEX && !c.ALUSrc); tg("immBl", pEX && c.ALUSrc);
  tg("ctlB", !k.bubble); tg("zeroB", k.bubble, k.stall);
  E.t_stallT.textContent = k.stall ? "stall = 1: dừng PC và IF/ID, chèn bubble" : "stall = 0"; tg("stallT", k.stall, k.stall);
  E.t_holdT.textContent = k.stall ? "PC giữ nguyên (run = 0)" : ""; tg("holdT", k.stall, 1);
  E.t_holdIf.textContent = k.stall ? "IF/ID giữ nguyên" : ""; tg("holdIf", k.stall, 1);
  E.t_wbd.textContent = `wb_data = ${hx(k.wb_data)}`; tg("wbd", pWB && mw.RegWrite);
  tg("fwdwbT", fa === 1 || fb === 1); tg("fwdmemT", fa === 2 || fb === 2);
  E.t_fwdwbT.textContent = fa === 1 || fb === 1 ? `forward từ MEM/WB (01) = ${hx(k.wb_data)}` : "forward từ MEM/WB (01)";
  E.t_fwdmemT.textContent = fa === 2 || fb === 2 ? `forward từ EX/MEM (10) = ${hx(k.fwd_mem_val)}` : "forward từ EX/MEM (10)";
  E.t_pcsT.textContent = `pc_src_ex = ${k.pc_src_ex}`; tg("pcsT", k.pc_src_ex, 1);
  E.t_tgtT2.textContent = `target_ex = ${hx(k.target_ex)}`; tg("tgtT2", k.pc_src_ex);
  E.t_alurT.textContent = `${hx(k.alu_result_ex)}`; tg("alurT", pEX);
  // operand muxes show the chosen source
  E.v1_OPA.textContent = ""; E.v1_OPB.textContent = "";
  pdCtrlTable(k);
}
function u32(v) { return v >>> 0; }
function ctrlText(c) { return `RW${c.RegWrite} AS${c.ALUSrc} MW${c.MemWrite} MR${c.MemRead}`; }
function pdCtrlTable(k) {
  const cpu = PL.cpu, ie = cpu.idex, em = cpu.exmem, mw = cpu.memwb;
  const cols = ["RegWrite", "ALUSrc", "MemWrite", "MemRead", "IsBranch", "IsJAL", "IsJALR", "ALUOp", "ASel", "WBSel"];
  const rows = [
    ["ID (ctrl_in vào ID/EX)", k.bubble ? Object.assign({}, { RegWrite: 0, ALUSrc: 0, MemWrite: 0, MemRead: 0, IsBranch: 0, IsJAL: 0, IsJALR: 0, ALUOp: 0, ASel: 0, WBSel: 0 }) : k.cID, k.bubble ? "bubble (từ điều khiển = 0)" : ""],
    ["EX (ctrl_ex, 13 bit)", ie.ctrl, ""],
    ["MEM (ctrl_mem, 5 bit)", { RegWrite: em.RegWrite, MemWrite: em.MemWrite, MemRead: em.MemRead, WBSel: em.WBSel }, "chỉ giữ 4 tín hiệu cần cho MEM và WB"],
    ["WB (ctrl_wb, 3 bit)", { RegWrite: mw.RegWrite, WBSel: mw.WBSel }, "chỉ giữ RegWrite và WBSel"],
  ];
  let h = "<table><tr><th>từ điều khiển đi cùng lệnh</th>" + cols.map((c) => `<th class='n'>${c}</th>`).join("") + "<th></th></tr>";
  rows.forEach(([name, c, note]) => {
    h += `<tr><td><b>${name}</b></td>` + cols.map((n) => (n in c ? `<td class='n' style='${c[n] ? "font-weight:800;color:var(--accent)" : "color:var(--muted)"}'>${c[n]}</td>` : "<td class='n' style='color:var(--muted)'>-</td>")).join("") + `<td class='tip'>${note}</td></tr>`;
  });
  $("#pdCtrl").innerHTML = h + "</table>";
}
pdBuild();
