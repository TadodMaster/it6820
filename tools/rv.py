#!/usr/bin/env python3
"""Tiny RV32I assembler + reference simulator for the Logisim project.

  python tools/rv.py asm  prog.s [-o prog.hex] [-l]     assemble to a Logisim ROM image
  python tools/rv.py sim  prog.s [-n 100000]            run on the reference simulator, print registers

Supported: all of RV32I except fence/ecall/ebreak (treated as no-ops), plus the usual pseudo
instructions: nop li mv not neg chk(self-check, see tests/programs) j jr ret call beqz bnez bltz bgez blez bgtz bgt ble bgtu bleu seqz snez.
Syntax: labels `name:`, comments `#` or `;`, directives `.word v[,v...]`, registers x0..x31 or ABI names.
The reference simulator models the same data memory as the circuit: 256 words, address wraps modulo 1 KiB.
"""
import argparse
import re
import sys

MASK = 0xFFFFFFFF
ABI = ("zero ra sp gp tp t0 t1 t2 s0 s1 a0 a1 a2 a3 a4 a5 a6 a7 "
       "s2 s3 s4 s5 s6 s7 s8 s9 s10 s11 t3 t4 t5 t6").split()
REG = {n: i for i, n in enumerate(ABI)}
REG.update({f"x{i}": i for i in range(32)})
REG["fp"] = 8

R_OPS = {  # name: (funct3, funct7)
    "add": (0, 0), "sub": (0, 0x20), "sll": (1, 0), "slt": (2, 0), "sltu": (3, 0),
    "xor": (4, 0), "srl": (5, 0), "sra": (5, 0x20), "or": (6, 0), "and": (7, 0)}
I_OPS = {"addi": 0, "slti": 2, "sltiu": 3, "xori": 4, "ori": 6, "andi": 7}
SH_OPS = {"slli": (1, 0), "srli": (5, 0), "srai": (5, 0x20)}
LOADS = {"lb": 0, "lh": 1, "lw": 2, "lbu": 4, "lhu": 5}
STORES = {"sb": 0, "sh": 1, "sw": 2}
BRANCHES = {"beq": 0, "bne": 1, "blt": 4, "bge": 5, "bltu": 6, "bgeu": 7}


class AsmError(Exception):
    pass


def sx(v, bits):
    v &= (1 << bits) - 1
    return v - (1 << bits) if v >> (bits - 1) else v


def reg(tok):
    t = tok.strip().lower()
    if t not in REG:
        raise AsmError(f"unknown register '{tok}'")
    return REG[t]


def num(tok, labels=None, pc=None):
    t = tok.strip()
    if labels is not None and t in labels:
        return labels[t] - pc if pc is not None else labels[t]
    try:
        return int(t, 0)
    except ValueError:
        raise AsmError(f"bad number or unknown label '{tok}'")


def enc_r(f7, rs2, rs1, f3, rd, op):
    return (f7 << 25) | (rs2 << 20) | (rs1 << 15) | (f3 << 12) | (rd << 7) | op


def enc_i(imm, rs1, f3, rd, op):
    if not -2048 <= imm <= 2047:
        raise AsmError(f"immediate {imm} does not fit in 12 bits")
    return ((imm & 0xFFF) << 20) | (rs1 << 15) | (f3 << 12) | (rd << 7) | op


def enc_s(imm, rs2, rs1, f3, op):
    if not -2048 <= imm <= 2047:
        raise AsmError(f"offset {imm} does not fit in 12 bits")
    imm &= 0xFFF
    return ((imm >> 5) << 25) | (rs2 << 20) | (rs1 << 15) | (f3 << 12) | ((imm & 0x1F) << 7) | op


def enc_b(imm, rs2, rs1, f3):
    if imm % 2 or not -4096 <= imm <= 4094:
        raise AsmError(f"branch offset {imm} out of range")
    imm &= 0x1FFF
    return (((imm >> 12) & 1) << 31) | (((imm >> 5) & 0x3F) << 25) | (rs2 << 20) | (rs1 << 15) | \
        (f3 << 12) | (((imm >> 1) & 0xF) << 8) | (((imm >> 11) & 1) << 7) | 0x63


def enc_u(imm20, rd, op):
    return ((imm20 & 0xFFFFF) << 12) | (rd << 7) | op


def enc_j(imm, rd):
    if imm % 2 or not -(1 << 20) <= imm < (1 << 20):
        raise AsmError(f"jump offset {imm} out of range")
    imm &= 0x1FFFFF
    return (((imm >> 20) & 1) << 31) | (((imm >> 1) & 0x3FF) << 21) | (((imm >> 11) & 1) << 20) | \
        (((imm >> 12) & 0xFF) << 12) | (rd << 7) | 0x6F


def split_args(s):
    return [a.strip() for a in s.split(",")] if s.strip() else []


def parse_mem(arg):
    m = re.fullmatch(r"\s*(.*?)\s*\(\s*(\w+)\s*\)\s*", arg)
    if not m:
        raise AsmError(f"expected offset(reg), got '{arg}'")
    return (m.group(1) or "0"), m.group(2)


def expand(line_no, mnem, args):
    """Expand pseudo instructions into lists of (mnemonic, args...) with raw strings; returns list of (mn, [args])."""
    a = args
    m = mnem
    if m == "nop":
        return [("addi", ["x0", "x0", "0"])]
    if m == "mv":
        return [("addi", [a[0], a[1], "0"])]
    if m == "not":
        return [("xori", [a[0], a[1], "-1"])]
    if m == "neg":
        return [("sub", [a[0], "x0", a[1]])]
    if m == "seqz":
        return [("sltiu", [a[0], a[1], "1"])]
    if m == "snez":
        return [("sltu", [a[0], "x0", a[1]])]
    if m == "j":
        return [("jal", ["x0", a[0]])]
    if m == "jr":
        return [("jalr", ["x0", f"0({a[0]})"])]
    if m == "ret":
        return [("jalr", ["x0", "0(ra)"])]
    if m == "call":
        return [("jal", ["ra", a[0]])]
    if m == "beqz":
        return [("beq", [a[0], "x0", a[1]])]
    if m == "bnez":
        return [("bne", [a[0], "x0", a[1]])]
    if m == "bltz":
        return [("blt", [a[0], "x0", a[1]])]
    if m == "bgez":
        return [("bge", [a[0], "x0", a[1]])]
    if m == "blez":
        return [("bge", ["x0", a[0], a[1]])]
    if m == "bgtz":
        return [("blt", ["x0", a[0], a[1]])]
    if m == "bgt":
        return [("blt", [a[1], a[0], a[2]])]
    if m == "ble":
        return [("bge", [a[1], a[0], a[2]])]
    if m == "bgtu":
        return [("bltu", [a[1], a[0], a[2]])]
    if m == "bleu":
        return [("bgeu", [a[1], a[0], a[2]])]
    if m == "chk":  # self-check: chk rd, value  ->  li x30, value ; bne rd, x30, fail   (uses x30)
        return expand(line_no, "li", ["x30", a[1]]) + [("bne", [a[0], "x30", "fail"])]
    if m == "li":
        v = sx(int(a[1], 0), 32)
        if -2048 <= v <= 2047:
            return [("addi", [a[0], "x0", str(v)])]
        lo = sx(v, 12)
        hi = ((v - lo) >> 12) & 0xFFFFF
        out = [("lui", [a[0], str(hi)])]
        if lo:
            out.append(("addi", [a[0], a[0], str(lo)]))
        return out
    return [(m, a)]


def assemble(text):
    """Returns (words, listing, labels)."""
    items = []  # (line_no, source, mnemonic, args)
    labels = {}
    pc = 0
    for no, raw in enumerate(text.splitlines(), 1):
        line = re.split(r"[#;]", raw, 1)[0].strip()
        while True:
            m = re.match(r"^([A-Za-z_.$][\w.$]*)\s*:\s*(.*)$", line)
            if not m:
                break
            if m.group(1) in labels:
                raise AsmError(f"line {no}: duplicate label {m.group(1)}")
            labels[m.group(1)] = pc
            line = m.group(2).strip()
        if not line:
            continue
        parts = line.split(None, 1)
        mn = parts[0].lower()
        args = split_args(parts[1]) if len(parts) > 1 else []
        try:
            if mn == ".word":
                for v in args:
                    items.append((no, raw.strip(), ".word", [v]))
                    pc += 4
                continue
            for emn, eargs in expand(no, mn, args):
                items.append((no, raw.strip(), emn, eargs))
                pc += 4
        except (AsmError, IndexError, ValueError) as e:
            raise AsmError(f"line {no}: {e}")
    words, listing = [], []
    for idx, (no, src, mn, a) in enumerate(items):
        pc = idx * 4
        try:
            w = encode(mn, a, labels, pc)
        except (AsmError, IndexError, ValueError) as e:
            raise AsmError(f"line {no}: {src}: {e}")
        words.append(w & MASK)
        listing.append((pc, w & MASK, src))
    return words, listing, labels


def encode(mn, a, labels, pc):
    if mn == ".word":
        return int(a[0], 0)
    if mn in R_OPS:
        f3, f7 = R_OPS[mn]
        return enc_r(f7, reg(a[2]), reg(a[1]), f3, reg(a[0]), 0x33)
    if mn in I_OPS:
        return enc_i(num(a[2]), reg(a[1]), I_OPS[mn], reg(a[0]), 0x13)
    if mn in SH_OPS:
        f3, f7 = SH_OPS[mn]
        sh = num(a[2])
        if not 0 <= sh < 32:
            raise AsmError("shift amount must be 0..31")
        return enc_r(f7, sh, reg(a[1]), f3, reg(a[0]), 0x13)
    if mn in LOADS:
        off, base = parse_mem(a[1])
        return enc_i(num(off), reg(base), LOADS[mn], reg(a[0]), 0x03)
    if mn in STORES:
        off, base = parse_mem(a[1])
        return enc_s(num(off), reg(a[0]), reg(base), STORES[mn], 0x23)
    if mn in BRANCHES:
        return enc_b(num(a[2], labels, pc), reg(a[1]), reg(a[0]), BRANCHES[mn])
    if mn == "jal":
        if len(a) == 1:
            a = ["ra", a[0]]
        return enc_j(num(a[1], labels, pc), reg(a[0]))
    if mn == "jalr":
        if len(a) == 2:
            off, base = parse_mem(a[1])
            return enc_i(num(off), reg(base), 0, reg(a[0]), 0x67)
        return enc_i(num(a[2]), reg(a[1]), 0, reg(a[0]), 0x67)
    if mn == "lui":
        return enc_u(num(a[1]), reg(a[0]), 0x37)
    if mn == "auipc":
        return enc_u(num(a[1]), reg(a[0]), 0x17)
    if mn in ("fence", "ecall", "ebreak"):
        return enc_i(0, 0, 0, 0, 0x13)  # no-op
    raise AsmError(f"unknown instruction '{mn}'")


# ---------------------------------------------------------------- reference simulator
class Sim:
    def __init__(self, words):
        self.rom = list(words) + [0] * (256 - len(words))
        self.regs = [0] * 32
        self.pc = 0
        self.mem = [0] * 256
        self.steps = 0

    def load(self, addr, f3):
        w = self.mem[(addr >> 2) & 0xFF]
        sh = (addr & 3) * 8
        if f3 == 2:
            return w
        if f3 in (0, 4):
            b = (w >> sh) & 0xFF
            return b if f3 == 4 else sx(b, 8) & MASK
        if f3 in (1, 5):
            h = (w >> (addr & 2) * 8) & 0xFFFF
            return h if f3 == 5 else sx(h, 16) & MASK
        raise ValueError("bad load funct3")

    def store(self, addr, f3, val):
        i = (addr >> 2) & 0xFF
        if f3 == 2:
            self.mem[i] = val & MASK
        elif f3 == 0:
            sh = (addr & 3) * 8
            self.mem[i] = (self.mem[i] & ~(0xFF << sh) & MASK) | ((val & 0xFF) << sh)
        elif f3 == 1:
            sh = (addr & 2) * 8
            self.mem[i] = (self.mem[i] & ~(0xFFFF << sh) & MASK) | ((val & 0xFFFF) << sh)

    def step(self):
        w = self.rom[(self.pc >> 2) & 0xFF]
        op, rd, f3 = w & 0x7F, (w >> 7) & 31, (w >> 12) & 7
        rs1, rs2, f7 = (w >> 15) & 31, (w >> 20) & 31, w >> 25
        r = self.regs
        a, b = r[rs1], r[rs2]
        nxt = (self.pc + 4) & MASK
        val = None
        if op == 0x33:
            val = alu(f3, f7, a, b, True)
        elif op == 0x13:
            imm = sx(w >> 20, 12) & MASK
            val = alu(f3, f7 if f3 == 5 else 0, a, imm, False)
        elif op == 0x03:
            val = self.load((a + sx(w >> 20, 12)) & MASK, f3)
        elif op == 0x23:
            imm = sx(((w >> 25) << 5) | ((w >> 7) & 31), 12)
            self.store((a + imm) & MASK, f3, b)
        elif op == 0x63:
            imm = sx(((w >> 31) << 12) | (((w >> 7) & 1) << 11) | (((w >> 25) & 0x3F) << 5) | (((w >> 8) & 0xF) << 1), 13)
            taken = {0: a == b, 1: a != b, 4: sx(a, 32) < sx(b, 32), 5: sx(a, 32) >= sx(b, 32),
                     6: a < b, 7: a >= b}.get(f3, False)
            if taken:
                nxt = (self.pc + imm) & MASK
        elif op == 0x37:
            val = w & 0xFFFFF000
        elif op == 0x17:
            val = (self.pc + (w & 0xFFFFF000)) & MASK
        elif op == 0x6F:
            imm = sx(((w >> 31) << 20) | (((w >> 12) & 0xFF) << 12) | (((w >> 20) & 1) << 11) | (((w >> 21) & 0x3FF) << 1), 21)
            val = nxt
            nxt = (self.pc + imm) & MASK
        elif op == 0x67:
            val = nxt
            nxt = (a + sx(w >> 20, 12)) & MASK & ~1
        if val is not None and rd:
            r[rd] = val & MASK
        self.pc = nxt
        self.steps += 1

    def run(self, max_steps=100000):
        """Run until a jump-to-self (halt loop). Returns True if halted."""
        while self.steps < max_steps:
            before = self.pc
            self.step()
            if self.pc == before:
                return True
        return False


def alu(f3, f7, a, b, is_r):
    sh = b & 31
    if f3 == 0:
        return (a - b) & MASK if (is_r and f7 == 0x20) else (a + b) & MASK
    if f3 == 1:
        return (a << sh) & MASK
    if f3 == 2:
        return int(sx(a, 32) < sx(b, 32))
    if f3 == 3:
        return int(a < b)
    if f3 == 4:
        return a ^ b
    if f3 == 5:
        return (sx(a, 32) >> sh) & MASK if f7 == 0x20 else a >> sh
    if f3 == 6:
        return a | b
    return a & b


def to_hex(words):
    return "v2.0 raw\n" + "\n".join(f"{w:08x}" for w in words) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["asm", "sim"])
    ap.add_argument("src")
    ap.add_argument("-o", "--out")
    ap.add_argument("-l", "--list", action="store_true", help="print a listing")
    ap.add_argument("-n", "--max-steps", type=int, default=100000)
    args = ap.parse_args()
    try:
        words, listing, labels = assemble(open(args.src, encoding="utf-8").read())
    except AsmError as e:
        sys.exit(f"error: {e}")
    if len(words) > 256:
        sys.exit(f"error: program has {len(words)} words, the ROM holds 256")
    if args.cmd == "asm":
        if args.list:
            for pc, w, src in listing:
                print(f"{pc:04x}: {w:08x}  {src}")
        out = args.out or re.sub(r"\.\w+$", "", args.src) + ".hex"
        open(out, "w", newline="\n").write(to_hex(words))
        print(f"{len(words)} words -> {out}")
    else:
        s = Sim(words)
        halted = s.run(args.max_steps)
        print(f"{'halted' if halted else 'NOT halted'} after {s.steps} steps, pc={s.pc:#x}")
        for i in range(0, 32, 4):
            print("  ".join(f"x{j:<2}={s.regs[j]:08x}" for j in range(i, i + 4)))
        nz = [(i * 4, v) for i, v in enumerate(s.mem) if v]
        print("memory:", ", ".join(f"[{a:#05x}]={v:08x}" for a, v in nz) or "(all zero)")


if __name__ == "__main__":
    main()
