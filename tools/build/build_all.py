"""Rebuild RiscVComputer.circ: library blocks + both CPU versions.

usage: python tools/build/build_all.py <input.circ> <output.circ> [--stage blocks|all]

The input already contains the hand-drawn blocks (ALU, InstructionDecode, RegisterFile, ImmGen, ALUControl);
everything else is regenerated from the netlists in blocks.py / cpus.py.
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from circgen import Project  # noqa: E402
import circgen  # noqa: E402
import blocks  # noqa: E402


def patch_alucontrol(proj):
    """R-type SLL (funct3 = 001) must give ALUCtrl 0101; the constant was 0110."""
    blk = proj.block("ALUControl")
    new = re.sub(r'(<comp lib="0" loc="\(770,650\)" name="Constant">\s*<a name="value" val=")0x6(")', r"\g<1>0x5\2", blk)
    proj.set("ALUControl", new)
    return new != blk


def label_registers(proj):
    """Label the 32 registers of RegisterFile x0..x31 (used by the tests and shown in the GUI)."""
    blk = proj.block("RegisterFile")
    tunnels = []
    for t in re.finditer(r'<comp lib="0" loc="\((\d+),(\d+)\)" name="Tunnel">(.*?)</comp>', blk, re.S):
        lab = re.search(r'name="label" val="([^"]+)"', t.group(3))
        if lab and re.fullmatch(r"X\d+", lab.group(1)):
            tunnels.append((int(t.group(1)), int(t.group(2)), lab.group(1)))
    n = 0

    def lab(mo):
        nonlocal n
        x, y, body = int(mo.group(1)), int(mo.group(2)), mo.group(3)
        if 'name="label"' in body:
            return mo.group(0)
        cand = [t for t in tunnels if t[1] == y + 30 and t[0] >= x + 60]
        num = min(cand)[2][1:]
        n += 1
        return (f'<comp lib="5" loc="({x},{y})" name="Register">'
                + body.replace('      <a name="width"', f'      <a name="label" val="x{num}"/>\n      <a name="width"', 1) + "</comp>")

    new = re.sub(r'<comp lib="5" loc="\((\d+),(\d+)\)" name="Register">(.*?)</comp>', lab, blk, flags=re.S)
    proj.set("RegisterFile", new)
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--stage", default="all", choices=["blocks", "all"])
    a = ap.parse_args()
    proj = Project(a.src)
    print("ALUControl SLL constant fixed:", patch_alucontrol(proj))
    print("registers labelled:", label_registers(proj))
    for name, fn in (("MainControl", blocks.main_control), ("BranchUnit", blocks.branch_unit),
                     ("LoadExtract", blocks.load_extract), ("StoreMerge", blocks.store_merge),
                     ("Memory", blocks.memory), ("ForwardingUnit", blocks.forwarding_unit),
                     ("HazardUnit", blocks.hazard_unit)):
        print("generating", name)
        fn(proj)
    if a.stage == "all":
        import cpus
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        import rv
        demo = os.path.join(os.path.dirname(__file__), "..", "..", "programs", "demo.s")
        words, _, _ = rv.assemble(open(demo, encoding="utf-8").read())
        cpus.build(proj, cpus.rom_text(words))
    import fonts
    proj.text = fonts.monospace(proj.text)
    proj.save(a.dst)
    print("wrote", a.dst, "circuits:", ", ".join(proj.names()))
    from verify import verify
    bad = 0
    for circ in circgen.BUILT:
        probs = verify(circ, a.dst)
        print(f"verify {circ.name:16} {'ok' if not probs else str(len(probs)) + ' problem(s)'}")
        for pr in probs[:10]:
            print("    ", pr)
        bad += bool(probs)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
