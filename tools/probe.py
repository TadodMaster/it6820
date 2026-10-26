#!/usr/bin/env python3
"""Debug helper: run a program on a circuit and show the value of named nets (tunnel labels).

  python tools/probe.py file.circ circuit prog.s cycles label [label ...]            values after `cycles` cycles
  python tools/probe.py --trace file.circ circuit prog.s cycles label [label ...]    a table: one row per clock cycle

Labels are the tunnel names of the top-level circuit, e.g. pc_ex alu_result_ex stall ForwardA.
Set JAVA to a JDK 21 java.exe if `java` on the PATH is older.
"""
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
import rv  # noqa: E402

args = sys.argv[1:]
trace = bool(args) and args[0] == "--trace"
if trace:
    args = args[1:]
circ, circuit, prog, cycles, *labels = args
words, _, _ = rv.assemble(open(prog, encoding="utf-8").read())
hexf = os.path.join(tempfile.gettempdir(), "probe.hex")
open(hexf, "w", newline="\n").write(rv.to_hex(words))
text = open(circ, encoding="utf-8").read()
blk = re.search(rf'  <circuit name="{circuit}">.*?</circuit>', text, re.S).group(0)
locs = {}
for m in re.finditer(r'<comp lib="0" loc="\((\d+),(\d+)\)" name="Tunnel">(.*?)</comp>', blk, re.S):
    lab = re.search(r'name="label" val="([^"]+)"', m.group(3)).group(1)
    locs.setdefault(lab, (m.group(1), m.group(2)))
missing = [l for l in labels if l not in locs]
if missing:
    sys.exit("no tunnel named: " + ", ".join(missing))
cp = os.path.join(ROOT, "logisim-evolution-4.1.0-all.jar") + os.pathsep + os.path.join(ROOT, "tools", "bin")
cmd = [os.environ.get("JAVA", "java"), "-cp", cp, "Run", circ, circuit, hexf, cycles, "trace" if trace else "x"]
cmd += [f"@{locs[l][0]},{locs[l][1]}" for l in labels]
p = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
if trace:
    print(f"{'cycle':>5}  {'PC':>8}  " + "  ".join(f"{l:>12}" for l in labels))
    for line in p.stdout.splitlines():
        if line.startswith("T "):
            parts = line.split()
            print(f"{parts[1]:>5}  {parts[2][3:]:>8}  " + "  ".join(f"{v:>12}" for v in parts[3:]))
else:
    vals = [l for l in p.stdout.splitlines() if l.startswith("PROBE")]
    if not vals:
        print(p.stdout[-400:], p.stderr[-800:])
    for l, v in zip(labels, vals):
        print(f"{l:14} {v.split('=')[1].strip()}")
