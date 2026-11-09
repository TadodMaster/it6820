#!/usr/bin/env python3
"""Assemble the demo programs and print them (words, listing, reference result) as JSON for the web page and its tests."""
import glob
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import rv  # noqa: E402

NAMES = [("demo", "programs/demo.s", "demo.s - tổng 10+9+...+1, store/load, gọi hàm"),
         ("hazards_demo", "programs/hazards_demo.s", "hazards_demo.s - forwarding, stall load-use, flush")]
for p in sorted(glob.glob(os.path.join(ROOT, "tests", "programs", "*.s"))):
    n = os.path.splitext(os.path.basename(p))[0]
    NAMES.append((n, os.path.relpath(p, ROOT).replace(os.sep, "/"), f"{n}.s - chương trình thử trong tests/programs"))


def main():
    out = {}
    for key, rel, title in NAMES:
        src = open(os.path.join(ROOT, rel), encoding="utf-8").read()
        words, listing, _ = rv.assemble(src)
        sim = rv.Sim(words)
        done = sim.run()
        out[key] = {
            "title": title, "file": rel, "words": [w & 0xFFFFFFFF for w in words],
            "listing": [[pc, w & 0xFFFFFFFF, t.split("#")[0].strip()] for pc, w, t in listing],
            "halts": bool(done), "steps": sim.steps, "regs": [r & 0xFFFFFFFF for r in sim.regs],
            "mem": {str(i * 4): v for i, v in enumerate(sim.mem) if v},
        }
    sys.stdout.write(json.dumps(out, ensure_ascii=True))


if __name__ == "__main__":
    main()
