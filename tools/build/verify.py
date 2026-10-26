"""Post-build check: the electrical nets of a saved circuit must equal the nets the generator intended."""
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict

from circgen import JAVA, JAR, BIN, pin_names


def ends_of(path, circuit):
    out = subprocess.run([JAVA, "-cp", f"{JAR};{BIN}", "Ends", path, circuit], capture_output=True, text=True, timeout=300).stdout
    res = {}
    for line in out.splitlines():
        m = re.match(r"(.+?) @\((-?\d+),(-?\d+)\) bounds=.* ends=(.*)$", line)
        if m:
            res[(m.group(1), int(m.group(2)), int(m.group(3)))] = [(int(a), int(b)) for a, b in re.findall(r"\[\d+:(-?\d+),(-?\d+) ", m.group(4))]
    return res


def verify(circ, path):
    """Returns a list of problems (empty = ok)."""
    ends = ends_of(path, circ.name)
    root = ET.parse(path).getroot()
    blk = [c for c in root.findall("circuit") if c.get("name") == circ.name][0]
    parent = {}

    def find(a):
        parent.setdefault(a, a)
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def pt(s):
        a, b = s.strip("()").split(",")
        return (int(a), int(b))

    for w in blk.findall("wire"):
        parent[find(pt(w.get("from")))] = find(pt(w.get("to")))
    labels = defaultdict(list)
    for k in blk.findall("comp"):
        if k.get("name") == "Tunnel":
            lab = [a.get("val") for a in k.findall("a") if a.get("name") == "label"][0]
            labels[lab].append(pt(k.get("loc")))
    for lab, pts in labels.items():
        for p in pts[1:]:
            parent[find(p)] = find(pts[0])
    problems = []
    # every tunnel must sit on a wire end (otherwise it is floating)
    wire_pts = {pt(w.get(k)) for w in blk.findall("wire") for k in ("from", "to")}
    for lab, pts in labels.items():
        for p in pts:
            if p not in wire_pts:
                problems.append(f"tunnel '{lab}' at {p} is not on a wire end")
    intended = defaultdict(set)   # intended net -> {electrical root}
    owner = defaultdict(set)      # electrical root -> {intended nets}
    members = defaultdict(list)
    for c in circ.comps:
        e = ends.get((c.name, c.loc[0], c.loc[1]))
        if e is None:
            problems.append(f"component {c.name} at {c.loc} missing in the saved file")
            continue
        names = pin_names(c.name, c.attrs, circ.sub_pins)
        pos = dict(zip(names, e))
        for pn, net in c.pins.items():
            if net is None:
                continue
            r = find(pos[pn])
            intended[net].add(r)
            owner[r].add(net)
            members[net].append(f"{c.name}.{pn}")
    for i, (c1, p1, c2, p2, _, _) in enumerate(circ.links):
        net = f"_link{i}"
        for c, p in ((c1, p1), (c2, p2)):
            e = ends[(c.name, c.loc[0], c.loc[1])]
            r = find(dict(zip(pin_names(c.name, c.attrs, circ.sub_pins), e))[p])
            intended[net].add(r)
            owner[r].add(net)
    for net, roots in intended.items():
        if len(roots) > 1:
            problems.append(f"net '{net}' is split into {len(roots)} pieces: {members[net][:6]}")
    for r, nets in owner.items():
        if len(nets) > 1:
            problems.append(f"SHORT between nets {sorted(nets)}")
    return problems
