#!/usr/bin/env python3
"""Live proof for the demo: run a program on the single-cycle CPU, on the pipeline CPU and on the reference simulator,
then show the three results side by side.

  python tools/live_proof.py [program.s] [--circ file.circ] [--no-color]

The reference simulator (tools/rv.py) was written independently of the circuits, so if the two CPUs agree with it, they compute
what a RISC-V machine must compute.  Takes about 10 seconds (one Logisim run per CPU).
Set JAVA to a JDK 21 java.exe if `java` on the PATH is older.
"""
import argparse
import os
import sys
import tempfile
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "tests"))
import rv  # noqa: E402
from run_cpu_tests import run_circuit_full, settle_cycles  # noqa: E402

ABI = ("zero ra sp gp tp t0 t1 t2 s0 s1 a0 a1 a2 a3 a4 a5 a6 a7 "
       "s2 s3 s4 s5 s6 s7 s8 s9 s10 s11 t3 t4 t5 t6").split()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("program", nargs="?", default=os.path.join(ROOT, "programs", "demo.s"))
    ap.add_argument("--circ", default=os.path.join(ROOT, "RiscVComputer.circ"))
    ap.add_argument("--no-color", action="store_true")
    a = ap.parse_args()
    if a.no_color or not sys.stdout.isatty():
        G = R = B = D = Z = ""
    else:
        os.system("")  # enable ANSI colours on Windows 10+
        G, R, B, D, Z = "\033[92m", "\033[91m", "\033[1m", "\033[2m", "\033[0m"

    src = open(a.program, encoding="utf-8").read()
    words, listing, _ = rv.assemble(src)
    sim = rv.Sim(words)
    if not sim.run():
        sys.exit("the reference simulator did not reach the final 'halt' loop")
    hexfile = os.path.join(tempfile.gettempdir(), "live_proof.hex")
    open(hexfile, "w", newline="\n").write(rv.to_hex(words))

    try:
        shown = os.path.relpath(a.program, ROOT)
    except ValueError:  # the program is on another drive
        shown = os.path.abspath(a.program)
    print(f"{B}PROGRAM  {shown}   ({len(words)} instructions in the ROM){Z}")
    for pc, w, text in listing:
        print(f"  {pc:04x}  {w:08x}  {text}")
    print(f"\n{B}REFERENCE SIMULATOR{Z}: halts after {sim.steps} instructions")

    cycles = sim.steps * 2 + 30
    results = {}
    for name, label in (("main", "single-cycle"), ("Pipeline", "5-stage pipeline")):
        t0 = time.time()
        pc, regs, mem, pcs, snaps = run_circuit_full(a.circ, name, hexfile, cycles, trace=True)
        final = tuple(sim.regs[i] for i in range(1, 32))
        reach = settle_cycles(snaps, final) if snaps else None
        results[name] = (regs, mem, reach, label, time.time() - t0)

    names = ["main", "Pipeline"]
    show = [i for i in range(32) if sim.regs[i] or any(results[n][0][i] for n in names)]
    print(f"\n{B}REGISTERS  (only registers that are not 0){Z}")
    print(f"  {'reg':<9}{'reference':>12}{'single-cycle':>14}{'pipeline':>12}   result")
    bad = 0
    for i in show:
        vals = [results[n][0][i] for n in names]
        ok = all(v == sim.regs[i] for v in vals)
        bad += not ok
        mark = f"{G}OK{Z}" if ok else f"{R}DIFFERENT{Z}"
        print(f"  x{i:<2} {ABI[i]:<4}{sim.regs[i]:12x}{vals[0]:14x}{vals[1]:12x}   {mark}")
    # every register, including the zero ones, is compared
    all_ok = all(results[n][0][i] == sim.regs[i] for n in names for i in range(32))
    exp_mem = {i * 4: v for i, v in enumerate(sim.mem) if v}
    print(f"\n{B}DATA MEMORY  (only words that are not 0){Z}")
    addrs = sorted(set(exp_mem) | {ad for n in names for ad in results[n][1]})
    if not addrs:
        print("  (all words are 0 in all three)")
    else:
        print(f"  {'address':<9}{'reference':>12}{'single-cycle':>14}{'pipeline':>12}   result")
    for ad in addrs:
        vals = [results[n][1].get(ad, 0) for n in names]
        ok = all(v == exp_mem.get(ad, 0) for v in vals)
        bad += not ok
        all_ok = all_ok and ok
        print(f"  {ad:#06x}   {exp_mem.get(ad, 0):12x}{vals[0]:14x}{vals[1]:12x}   {G + 'OK' + Z if ok else R + 'DIFFERENT' + Z}")

    n_instr = sim.last_change
    print(f"\n{B}SPEED  (clock cycles until the last register write is done; {n_instr} instructions up to that write){Z}")
    for n in names:
        reach, label = results[n][2], results[n][3]
        cpi = f"CPI {reach / n_instr:.2f}" if reach and n_instr else "?"
        print(f"  {label:<18}{reach} cycles  ({cpi})")
    print(f"  {D}pipeline: 2 extra cycles per taken branch / jump, 1 per load-use stall; a shorter clock period is the gain{Z}")

    print()
    if all_ok and not bad:
        print(f"{G}{B}VERDICT: both CPUs produce exactly the reference result: all 32 registers and the data memory match.{Z}")
    else:
        print(f"{R}{B}VERDICT: MISMATCH - see the lines marked DIFFERENT.{Z}")
    return 0 if all_ok and not bad else 1


if __name__ == "__main__":
    sys.exit(main())
