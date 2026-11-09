/* ================================================================= PIPELINE: animated instruction conveyor (inlined into the page) */
const CV = { track: $("#cvTrack"), fwd: $("#cvFwd"), els: new Map(), bub: {}, timers: new Set() };
const CV_ST = ["IF", "ID", "EX", "MEM", "WB"], CV_COL = [COL.IF, COL.ID, COL.EX, COL.MEM, COL.WB];
const CV_NAMES = ["IF - Nạp lệnh", "ID - Giải mã", "EX - Thực thi", "MEM - Bộ nhớ", "WB - Ghi lại"];
function cvBuild() {
  const t = CV.track;
  t.querySelectorAll(".cvcol").forEach((e) => e.remove());
  CV_ST.forEach((s, i) => {
    const c = document.createElement("div");
    c.className = "cvcol"; c.style.left = i * 20 + "%"; c.style.setProperty("--c", CV_COL[i]);
    c.innerHTML = `<b>${CV_NAMES[i]}</b>`;
    t.appendChild(c);
  });
  CV.fwd.innerHTML = "";
}
function cvReset() {
  CV.els.forEach((e) => e.remove()); CV.els.clear();
  Object.values(CV.bub).forEach((e) => e.remove()); CV.bub = {};
}
function cvInstrColor(id) {
  const f = PL.cpu.fetched[id]; if (!f) return COL.gray;
  const w = PL.prog.words[(f.pc >>> 2) & 255] | 0;
  return CLASS_COL[classOf(w & 0x7f)] || COL.gray;
}
function cvDetail(stage, id, k, cpu) {
  if (stage === 0) return `nạp ${hx(k.instr_if)}`;
  if (stage === 1) return `rs1=${hx(k.rs1_data_id)}`;
  if (stage === 2) return `${RV.ALU_NAMES[k.ALUCtrl]} = ${hx(k.alu_result_ex)}`;
  if (stage === 3) { const em = cpu.exmem; return em.MemWrite ? `ghi ${hx(em.store_data)}` : em.MemRead ? `đọc ${hx(k.mem_rdata_mem)}` : `addr ${hx(em.alu_result)}`; }
  const mw = cpu.memwb; return mw.RegWrite && mw.rd ? `x${mw.rd} <- ${hx(k.wb_data)}` : "không ghi";
}
function cvUpdate() {
  const cpu = PL.cpu, k = cpu.comb(), fi = cpu.ifid, ie = cpu.idex, em = cpu.exmem, mw = cpu.memwb;
  const occ = [];   // real instructions
  const bub = [];   // stages holding a bubble
  occ.push({ id: cpu.fid, st: 0, doomed: !!k.pc_src_ex, held: !!k.stall });
  if (fi.id >= 0) occ.push({ id: fi.id, st: 1, flush: fi.flush, stall: !!k.stall }); else bub.push(1);
  if (ie.id >= 0) occ.push({ id: ie.id, st: 2, flush: ie.flush, redirect: !!k.pc_src_ex && !ie.flush }); else bub.push(2);
  if (em.id >= 0) occ.push({ id: em.id, st: 3 }); else bub.push(3);
  if (mw.id >= 0) occ.push({ id: mw.id, st: 4 }); else bub.push(4);
  const seen = new Set();
  occ.forEach((o) => {
    const key = "i" + o.id; seen.add(key);
    let e = CV.els.get(key), fresh = false;
    if (!e) {
      e = document.createElement("div"); e.className = "cvcard"; e.innerHTML = "<b></b><i></i><u></u>";
      e.style.left = "-20%"; e.style.opacity = "0"; CV.track.appendChild(e); CV.els.set(key, e); fresh = true;
    }
    const col = cvInstrColor(o.id);
    e.style.setProperty("--c", col);
    e.className = "cvcard" + (o.flush ? " flush" : "") + (o.stall ? " stall" : "") + (o.held ? " held" : "") + (o.doomed ? " doomed" : "") + (o.redirect ? " redirect" : "");
    e.querySelector("b").textContent = o.flush ? "X flush" : plName(o.id);
    const f = cpu.fetched[o.id];
    e.querySelector("i").textContent = f ? "PC " + hx(f.pc, 4) : "";
    e.querySelector("u").textContent = o.flush ? "bị hủy" : o.doomed ? "sẽ bị flush" : o.held ? "giữ nguyên (stall)" : cvDetail(o.st, o.id, k, cpu);
    const place = () => { e.style.left = o.st * 20 + "%"; e.style.opacity = "1"; };
    if (fresh) requestAnimationFrame(() => requestAnimationFrame(place)); else place();
  });
  CV.els.forEach((e, key) => {
    if (seen.has(key)) return;
    CV.els.delete(key);
    if (e.classList.contains("flush")) { e.classList.add("dead"); e.style.opacity = "0"; }
    else { e.style.left = "100%"; e.style.opacity = "0"; }
    setTimeout(() => e.remove(), 700);
  });
  // bubbles
  [1, 2, 3, 4].forEach((st) => {
    const need = bub.includes(st) && !(st === 1 && fi.flush);
    let e = CV.bub[st];
    if (need && !e) { e = document.createElement("div"); e.className = "cvbub"; e.style.left = st * 20 + "%"; e.innerHTML = "<b>bubble</b><u>lệnh rỗng (NOP)</u>"; CV.track.appendChild(e); CV.bub[st] = e; requestAnimationFrame(() => (e.style.opacity = "1")); }
    if (!need && e) { e.style.opacity = "0"; delete CV.bub[st]; setTimeout(() => e.remove(), 500); }
  });
  // arrows
  const F = CV.fwd; F.innerHTML = "";
  const cx = (st) => 280 * st + 140;
  const arrow = (d, cls, label, lx, ly) => { el("path", { d, class: "cvarrow " + cls }, F); el("text", { x: lx, y: ly, class: "cvlab " + cls, "text-anchor": "middle" }, F, label); };
  const fa = k.ForwardA, fb = k.ForwardB;
  if (fa === 2 || fb === 2) arrow(`M${cx(3)},-10 C${cx(3)},-52 ${cx(2)},-52 ${cx(2)},-10`, "fwd", `forward ${fa === 2 ? "A" : ""}${fb === 2 ? "B" : ""} = ${hx(k.fwd_mem_val)}`, (cx(3) + cx(2)) / 2, -38);
  if (fa === 1 || fb === 1) arrow(`M${cx(4)},-10 C${cx(4)},-82 ${cx(2)},-82 ${cx(2)},-10`, "fwd", `forward ${fa === 1 ? "A" : ""}${fb === 1 ? "B" : ""} = ${hx(k.wb_data)}`, (cx(4) + cx(2)) / 2, -58);
  if (k.pc_src_ex) arrow(`M${cx(2)},-10 C${cx(2)},-82 ${cx(0)},-82 ${cx(0)},-10`, "flushA", `pc_src_ex: PC <- ${hx(k.target_ex)}, hủy 2 lệnh`, (cx(2) + cx(0)) / 2, -58);
  if (k.stall) arrow(`M${cx(1)},-10 C${cx(1)},-40 ${cx(0)},-40 ${cx(0)},-10`, "stallA", "stall: PC, IF/ID đứng yên", (cx(1) + cx(0)) / 2, -30);
  const chips = [];
  if (k.stall) chips.push('<span class="badge stall">stall</span> load-use: lệnh ở ID chờ dữ liệu của lệnh load ở EX; một bubble được chèn vào EX');
  if (k.pc_src_ex) chips.push('<span class="badge flush">flush</span> lệnh ở EX chuyển hướng PC; hai lệnh nạp phía sau bị hủy (thẻ đỏ)');
  if (fa || fb) chips.push(`<span class="badge fwd">forward</span> EX lấy toán hạng ${fa ? "A" : ""}${fa && fb ? " và " : ""}${fb ? "B" : ""} từ ${fa === 2 || fb === 2 ? "EX/MEM" : "MEM/WB"} thay vì register file`);
  if (!chips.length) chips.push('<span class="badge ok">bình thường</span> các thẻ tiến một tầng mỗi tick');
  $("#cvStatus").innerHTML = chips.join("<br>");
}
function cvEvents(key) {
  const p = PROGRAMS[key], q = new RV.Pipeline(p.words), found = {};
  for (let i = 0; i < Math.min(p.steps * 3 + 60, 300); i++) {
    q.step(); const k = q.comb();
    if (k.stall && !found.stall) found.stall = q.tick;
    if ((k.ForwardA || k.ForwardB) && !found.fwd) found.fwd = q.tick;
    if (k.pc_src_ex && !found.flush) found.flush = q.tick;
  }
  const box = $("#cvJump"); box.innerHTML = "<label>Nhảy tới sự kiện đầu tiên:</label>";
  [["fwd", "forwarding"], ["stall", "stall load-use"], ["flush", "flush (rẽ nhánh)"]].forEach(([f, name]) => {
    const b = document.createElement("button");
    if (found[f]) { b.textContent = `${name} (tick ${found[f]})`; b.onclick = () => plJump(found[f]); } else { b.textContent = `${name}: không có`; b.disabled = true; }
    box.appendChild(b);
  });
}
cvBuild();
