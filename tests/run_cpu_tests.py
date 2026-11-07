#!/usr/bin/env python3
"""Whole-CPU tests: run each test program on the Logisim circuit and compare with the reference simulator.

  python tests/run_cpu_tests.py [--circuit main|Pipeline|all] [--circ file.circ] [programs...]

For every program in tests/programs/*.s:
  1. assemble it (tools/rv.py) and run it on the reference simulator -> expected registers / data memory
  2. run it on the circuit for enough clock cycles (tools/java/Run.java) -> actual registers / data memory
  3. compare all 32 registers and every non-zero data word; the program's own self-check must end with x31 = 0x600D
Prints the cycles until the last register write has completed, and the CPI = cycles / instructions up to that write.
"""
import argparse
import glob
import os
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import rv  # noqa: E402

JAVA = os.environ.get("JAVA", "java")
JAR = os.path.join(ROOT, "logisim-evolution-4.1.0-all.jar")
BIN = os.path.join(ROOT, "tools", "bin")


def run_circuit(circ, circuit, hexfile, cycles, trace=False):
    """(pc, regs, mem, pcs) - see run_circuit_full for the per-cycle register snapshots."""
    return run_circuit_full(circ, circuit, hexfile, cycles, trace)[:4]


def settle_cycles(snaps, final):
    """Number of clock cycles after which the registers x1..x31 have reached their final values and never change again."""
    last = 0
    for i, s in enumerate(snaps):
        if s != final:
            last = i + 2   # snaps[i] is the state after cycle i+1, so the first cycle with the final state is i+2
    return last


def run_circuit_full(circ, circuit, hexfile, cycles, trace=False):
    cmd = [JAVA, "-cp", f"{JAR}{os.pathsep}{BIN}", "Run", circ, circuit, hexfile, str(cycles)] + (["trace"] if trace else [])
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
    regs, mem, pcs, pc, snaps = {}, {}, [], None, []
    for line in p.stdout.splitlines():
        if line.startswith("T "):
            for tok in line.split():
                if tok.startswith("R="):
                    snaps.append(tuple(int(v, 16) for v in tok[2:].split(",")))
            tok = line.split("PC=")[1].split()[0]
            try:
                pcs.append(int(tok, 16))
            except ValueError:
                pcs.append(-1)
        elif line.startswith("PC="):
            pc = int(line[3:], 16)
        elif line.startswith("MEM["):
            a, v = line[4:].split("]=")
            mem[int(a, 16)] = int(v, 16)
        elif line.startswith("x") and "=" in line:
            n, v = line.split("=")
            regs[int(n[1:])] = int(v, 16)
    if len(regs) != 32:
        raise RuntimeError(f"circuit run failed:\n{p.stdout[-500:]}\n{p.stderr[-800:]}")
    return pc, regs, mem, pcs, snaps


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--circuit", default="main")
    ap.add_argument("--circ", default=os.path.join(ROOT, "RiscVComputer.circ"))
    ap.add_argument("--trace", action="store_true", help="(cycle counts are always reported)")
    ap.add_argument("programs", nargs="*")
    a = ap.parse_args()
    progs = a.programs or (sorted(glob.glob(os.path.join(ROOT, "tests", "programs", "*.s")))
                           + [os.path.join(ROOT, "programs", "demo.s")])
    circuits = ["main", "Pipeline"] if a.circuit == "all" else [a.circuit]
    bad = 0
    for circuit in circuits:
        print(f"== {circuit}")
        for path in progs:
            name = os.path.basename(path)
            try:
                words, _, _ = rv.assemble(open(path, encoding="utf-8").read())
            except rv.AsmError as e:
                print(f"  {name:14} ASSEMBLY ERROR {e}")
                bad += 1
                continue
            sim = rv.Sim(words)
            if not sim.run():
                print(f"  {name:14} reference simulator did not halt")
                bad += 1
                continue
            hexfile = os.path.join(tempfile.gettempdir(), name + ".hex")
            open(hexfile, "w", newline="\n").write(rv.to_hex(words))
            cycles = sim.steps * 2 + 24
            pc, regs, mem, pcs, snaps = run_circuit_full(a.circ, circuit, hexfile, cycles, trace=True)
            diffs = [f"x{i}: circuit {regs[i]:08x}, expected {sim.regs[i]:08x}" for i in range(32) if regs[i] != sim.regs[i]]
            exp_mem = {i * 4: v for i, v in enumerate(sim.mem) if v}
            for ad in sorted(set(mem) | set(exp_mem)):
                if mem.get(ad, 0) != exp_mem.get(ad, 0):
                    diffs.append(f"mem[{ad:#x}]: circuit {mem.get(ad, 0):08x}, expected {exp_mem.get(ad, 0):08x}")
            if "0x600D" in open(path, encoding="utf-8").read() and regs[31] != 0x600D:
                diffs.append(f"self-check failed: x31 = {regs[31]:08x} (expected 0000600d)")
            halt_pc = sim.pc
            final = tuple(sim.regs[i] for i in range(1, 32))
            settle = settle_cycles(snaps, final) if snaps else 0
            n = sim.last_change
            cpi = f"  {settle} cycles for the {n} instructions up to the last register write (CPI {settle / n:.2f})" if settle and n else ""
            if diffs:
                bad += 1
                print(f"  {name:14} FAIL{cpi}")
                for d in diffs[:12]:
                    print("      " + d)
            else:
                print(f"  {name:14} ok  {len(words)} words{cpi}")
    print("ALL PASSED" if not bad else f"FAILED: {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
