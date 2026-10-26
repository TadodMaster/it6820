#!/usr/bin/env python3
"""Random-program test: generate terminating random RV32I programs and compare the circuit with the reference simulator.

  python tests/fuzz.py [--circuit main|Pipeline|all] [--circ file.circ] [--count 20] [--seed 1] [--length 60]

The programs use few registers (x1..x7) so that almost every instruction depends on a recent one: this exercises forwarding,
load-use stalls and branch flushes of the pipeline.  Branches and jumps only go forward, so every program terminates.
"""
import argparse
import os
import random
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.dirname(__file__))
import rv  # noqa: E402
from run_cpu_tests import run_circuit  # noqa: E402

REGS = [f"x{i}" for i in range(1, 8)]
ADDR_REGS = ["x20", "x21", "x22"]          # hold fixed word-aligned addresses, never overwritten
R_OPS = ["add", "sub", "and", "or", "xor", "sll", "srl", "sra", "slt", "sltu"]
I_OPS = ["addi", "andi", "ori", "xori", "slti", "sltiu"]
SH_OPS = ["slli", "srli", "srai"]
BR_OPS = ["beq", "bne", "blt", "bge", "bltu", "bgeu"]


def gen(rng, length):
    lines = [f"li {r}, {rng.choice([0, 1, -1, 5, 0x7FFFFFFF, 0x80000000, rng.randrange(-2000, 2000), rng.getrandbits(32)])}" for r in REGS]
    lines += ["li x20, 64", "li x21, 200", "li x22, 512"]
    pending = 0
    n = 0
    label = 0
    while n < length:
        k = rng.random()
        rd, a, b = rng.choice(REGS), rng.choice(REGS + ["x0"]), rng.choice(REGS + ["x0"])
        if k < 0.30:
            lines.append(f"{rng.choice(R_OPS)} {rd}, {a}, {b}")
        elif k < 0.48:
            lines.append(f"{rng.choice(I_OPS)} {rd}, {a}, {rng.randrange(-2048, 2048)}")
        elif k < 0.54:
            lines.append(f"{rng.choice(SH_OPS)} {rd}, {a}, {rng.randrange(32)}")
        elif k < 0.58:
            lines.append(f"{rng.choice(['lui', 'auipc'])} {rd}, {rng.randrange(1 << 20)}")
        elif k < 0.72:
            base = rng.choice(ADDR_REGS)
            op = rng.choice(["lw", "lh", "lhu", "lb", "lbu"])
            off = rng.choice([0, 4, 8, 12, 1, 2, 3, 5, 6, 7]) if op != "lw" else rng.choice([0, 4, 8, 12])
            lines.append(f"{op} {rd}, {off}({base})")
        elif k < 0.84:
            base = rng.choice(ADDR_REGS)
            op = rng.choice(["sw", "sh", "sb"])
            off = {"sw": rng.choice([0, 4, 8, 12]), "sh": rng.choice([0, 2, 4, 6, 8]), "sb": rng.randrange(0, 12)}[op]
            lines.append(f"{op} {a}, {off}({base})")
        elif k < 0.94:
            skip = rng.randrange(1, 4)
            lines.append(f"{rng.choice(BR_OPS)} {a}, {b}, L{label}")
            for _ in range(skip):
                lines.append(f"{rng.choice(R_OPS)} {rng.choice(REGS)}, {rng.choice(REGS)}, {rng.choice(REGS)}")
            lines.append(f"L{label}: addi x0, x0, 0")
            label += 1
            n += skip
        elif k < 0.97:
            lines.append(f"jal {rng.choice(['x0', rd])}, L{label}")
            lines.append(f"addi {rd}, {rd}, 1")
            lines.append(f"L{label}: addi x0, x0, 0")
            label += 1
            n += 2
        else:
            # jalr forward by 2 instructions through a computed register
            lines.append(f"auipc {rd}, 0")
            lines.append(f"addi {rd}, {rd}, 16")
            lines.append(f"jalr {rng.choice(['x0', 'x7'])}, 0({rd})")
            lines.append(f"addi x6, x6, 3")
            lines.append("addi x5, x5, 5")
            n += 4
        n += 1
    lines += ["halt: j halt"]
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--circuit", default="all")
    ap.add_argument("--circ", default=os.path.join(ROOT, "RiscVComputer.circ"))
    ap.add_argument("--count", type=int, default=20)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--length", type=int, default=60)
    a = ap.parse_args()
    circuits = ["main", "Pipeline"] if a.circuit == "all" else [a.circuit]
    bad = 0
    for i in range(a.count):
        seed = a.seed + i
        text = gen(random.Random(seed), a.length)
        try:
            words, _, _ = rv.assemble(text)
        except rv.AsmError as e:
            print(f"seed {seed}: generator produced invalid code: {e}")
            bad += 1
            continue
        sim = rv.Sim(words)
        if not sim.run(20000):
            print(f"seed {seed}: reference simulator did not halt")
            bad += 1
            continue
        hexfile = os.path.join(tempfile.gettempdir(), f"fuzz{seed}.hex")
        open(hexfile, "w", newline="\n").write(rv.to_hex(words))
        for circuit in circuits:
            pc, regs, mem, _ = run_circuit(a.circ, circuit, hexfile, sim.steps * 2 + 30)
            diffs = [f"x{k}: {regs[k]:08x} vs {sim.regs[k]:08x}" for k in range(32) if regs[k] != sim.regs[k]]
            exp = {j * 4: v for j, v in enumerate(sim.mem) if v}
            diffs += [f"mem[{ad:#x}]: {mem.get(ad, 0):08x} vs {exp.get(ad, 0):08x}" for ad in sorted(set(mem) | set(exp))
                      if mem.get(ad, 0) != exp.get(ad, 0)]
            print(f"seed {seed:3} {circuit:9} {len(words):3} words, {sim.steps:3} instr  " + ("ok" if not diffs else "MISMATCH " + "; ".join(diffs[:4])))
            if diffs:
                bad += 1
                open(os.path.join(tempfile.gettempdir(), f"fuzz_fail_{seed}.s"), "w").write(text)
    print("ALL PASSED" if not bad else f"FAILED: {bad} (failing programs saved in {tempfile.gettempdir()})")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
