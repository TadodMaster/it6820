"""Netlist -> Logisim .circ generator.

A circuit is described as components placed at chosen locations, each pin attached to a *named net*.
`Circ.build()` asks Logisim itself for the exact pin positions (java Ends), then draws a short stub and a
named tunnel on every pin, so a net is simply "all pins that share a name". The builder lints every net:
width mismatches, nets without a driver and nets with several drivers are reported.

Wires in Logisim only connect at their end points, so nothing here relies on T-junctions.
"""
import os
import re
import subprocess
import tempfile
from collections import defaultdict
from xml.sax.saxutils import quoteattr

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
JAVA = os.environ.get("JAVA", r"C:\Program Files\Java\jdk-21.0.12.1\bin\java.exe")
JAR = os.path.join(ROOT, "logisim-evolution-4.1.0-all.jar")
BIN = os.path.join(ROOT, "tools", "bin")

LIB = {"Tunnel": 0, "Pin": 0, "Constant": 0, "Splitter": 0, "Clock": 0, "Probe": 0, "Bit Extender": 0,
       "AND Gate": 1, "OR Gate": 1, "NOT Gate": 1, "XOR Gate": 1, "NAND Gate": 1, "NOR Gate": 1,
       "Multiplexer": 2, "Demultiplexer": 2, "Decoder": 2,
       "Adder": 3, "Subtractor": 3, "Comparator": 3, "Shifter": 3,
       "Register": 5, "RAM": 5, "ROM": 5, "Text": 9}
GATES = ("AND Gate", "OR Gate", "XOR Gate", "NAND Gate", "NOR Gate")


def pin_names(name, attrs, sub_pins):
    """Names of the connection points of a component, in Logisim's end order."""
    if name == "Multiplexer":
        n = 2 ** int(attrs.get("select", 1))
        return [f"d{i}" for i in range(n)] + ["sel", "out"]
    if name in ("Adder", "Subtractor"):
        return ["a", "b", "out", "cin", "cout"]
    if name == "Comparator":
        return ["a", "b", "gt", "eq", "lt"]
    if name == "Register":
        return ["q", "d", "clk", "r", "we"]
    if name == "Splitter":
        return ["bus"] + [f"b{i}" for i in range(int(attrs.get("fanout", 2)))]
    if name == "Bit Extender":
        return ["out", "in"]
    if name in ("Constant", "Clock"):
        return ["out"]
    if name in ("Probe", "Pin"):
        return ["p"]
    if name == "Tunnel":
        return ["t"]
    if name in GATES:
        return ["out"] + [f"in{i + 1}" for i in range(int(attrs.get("inputs", 2)))]
    if name == "NOT Gate":
        return ["out", "in"]
    if name == "RAM":
        return (["addr", "dout", "din", "we", "clk"] if attrs.get("enables") == "line"
                else ["addr", "dout", "din", "oe", "we", "clk"])
    if name == "ROM":
        return ["addr", "dout"]
    if name == "Shifter":
        return ["a", "shamt", "out"]
    if name in sub_pins:
        ins, outs = sub_pins[name]
        return ins + outs
    raise KeyError(f"unknown component {name}")


BUILT = []   # every circuit generated in this run (for the verifier)


def est_width(label, size=12):
    """width of a tunnel box for `label` (monospaced bold text, advance about 0.6 em)"""
    return int(0.62 * size * len(label) + 22)


class Project:
    """The text of a .circ file with replaceable circuits."""

    def __init__(self, path):
        self.text = open(path, encoding="utf-8").read()

    def names(self):
        return re.findall(r'  <circuit name="([^"]+)">', self.text)

    def block(self, name):
        m = re.search(rf'  <circuit name="{re.escape(name)}">.*?</circuit>\n', self.text, re.S)
        return m.group(0) if m else None

    def set(self, name, block, before=None):
        old = self.block(name)
        if old:
            self.text = self.text.replace(old, block)
        elif before and self.block(before):
            b = self.block(before)
            self.text = self.text.replace(b, block + b)
        else:
            i = self.text.rindex("</project>")
            self.text = self.text[:i] + block + self.text[i:]

    def remove(self, name):
        old = self.block(name)
        if old:
            self.text = self.text.replace(old, "")

    def sub_pins(self):
        """{circuit: (input labels, output labels)} in box order (sorted by y then x)."""
        res = {}
        for name in self.names():
            blk = self.block(name)
            ins, outs = [], []
            for m in re.finditer(r'<comp lib="0" loc="\((\d+),(\d+)\)" name="Pin">(.*?)</comp>', blk, re.S):
                body = m.group(3)
                lab = re.search(r'name="label" val="([^"]*)"', body)
                if not lab:
                    continue
                is_out = 'name="type" val="output"' in body
                (outs if is_out else ins).append((int(m.group(2)), int(m.group(1)), lab.group(1)))
            res[name] = ([l for _, _, l in sorted(ins)], [l for _, _, l in sorted(outs)])
        return res

    def save(self, path):
        open(path, "w", encoding="utf-8", newline="\n").write(self.text)


class Comp:
    def __init__(self, name, loc, attrs, pins, key):
        self.name, self.loc, self.attrs, self.pins, self.key = name, loc, attrs or {}, pins or {}, key
        self.ends = None
        self.bounds = None


class Circ:
    def __init__(self, proj, name, stub=30, spread=(1.0, 1.0)):
        self.proj, self.name, self.stub, self.spread = proj, name, stub, spread
        self.comps, self.texts, self.notes, self.links = [], [], [], []
        self.sub_pins = proj.sub_pins()
        self.warnings = []

    # ---- description API -------------------------------------------------------------
    def _sp(self, x, y):
        sx, sy = self.spread
        return (int(round(x * sx / 10)) * 10, int(round(y * sy / 10)) * 10)

    def add(self, name, loc, attrs=None, pins=None, key=None):
        c = Comp(name, self._sp(*loc), attrs, pins, key)
        self.comps.append(c)
        return c

    def link(self, c1, p1, c2, p2, xm=None, ym=None):
        """Direct wire from pin p1 of c1 to pin p2 of c2 (Z route through x=xm, or through y=ym if given)."""
        self.links.append((c1, p1, c2, p2, xm, ym))

    def text(self, x, y, s, font="Monospaced plain 12"):
        self.texts.append((*self._sp(x, y), s, font))

    def title(self, x, y, s):
        self.text(x, y, s, "Monospaced bold 16")

    def pin_in(self, label, width, loc, radix=None):
        a = {"appearance": "classic", "label": label}
        if width > 1:
            a["width"] = width
        if radix:
            a["radix"] = radix
        self.add("Pin", loc, a, {"p": label})

    def pin_out(self, label, width, loc, radix=None):
        a = {"appearance": "classic", "facing": "west", "label": label, "type": "output"}
        if width > 1:
            a["width"] = width
        if radix:
            a["radix"] = radix
        self.add("Pin", loc, a, {"p": label})

    # ---- building ----------------------------------------------------------------------
    LABEL_FONTS = {"Tunnel": "Monospaced bold 12", "Pin": "Monospaced bold 12", "Probe": "Monospaced plain 12",
                   "Clock": "Monospaced plain 12", "RAM": "Monospaced plain 12", "ROM": "Monospaced plain 12"}

    def _comp_xml(self, c):
        lib = f' lib="{LIB[c.name]}"' if c.name in LIB else ""
        body = ""
        if c.name in self.LABEL_FONTS and "labelfont" not in c.attrs:
            c.attrs = {**c.attrs, "labelfont": self.LABEL_FONTS[c.name]}
        for k, v in sorted(c.attrs.items()):
            if k == "contents":  # memory contents are stored as element text, not as an attribute
                body += f'      <a name="contents">{v}</a>\n'
            else:
                body += f'      <a name="{k}" val={quoteattr(str(v))}/>\n'
        if body:
            return f'    <comp{lib} loc="({c.loc[0]},{c.loc[1]})" name="{c.name}">\n{body}    </comp>\n'
        return f'    <comp{lib} loc="({c.loc[0]},{c.loc[1]})" name="{c.name}"/>\n'

    def _probe_ends(self):
        probe = "".join(self._comp_xml(c) for c in self.comps)
        blk = f'  <circuit name="ProbeTmp">\n{probe}  </circuit>\n'
        text = self.proj.text
        i = text.rindex("</project>")
        text = text[:i] + blk + text[i:]
        # the circuit being built may already exist in the project; the probe does not depend on it
        fd, path = tempfile.mkstemp(suffix=".circ")
        os.close(fd)
        try:
            open(path, "w", encoding="utf-8", newline="\n").write(text)
            p = subprocess.run([JAVA, "-cp", f"{JAR};{BIN}", "Ends", path, "ProbeTmp"],
                               capture_output=True, text=True, timeout=120)
        finally:
            os.remove(path)
        out = {}
        for line in p.stdout.splitlines():
            m = re.match(r"(.+?) @\((-?\d+),(-?\d+)\) bounds=\((-?\d+),(-?\d+)\): (\d+)x(\d+) ends=(.*)$", line)
            if not m:
                continue
            ends = [(int(a), int(b), int(w), io) for a, b, w, io in re.findall(r"\[\d+:(-?\d+),(-?\d+) w(\d+)([IO]+)\]", m.group(8))]
            out[(m.group(1), int(m.group(2)), int(m.group(3)))] = (ends, tuple(int(m.group(i)) for i in (4, 5, 6, 7)))
        if not out:
            raise RuntimeError("Logisim could not load the probe circuit:\n" + p.stdout[-800:] + p.stderr[-1500:])
        return out

    def build(self):
        seen = set()
        for c in self.comps:
            k = (c.name, c.loc)
            if k in seen:
                raise ValueError(f"{self.name}: two {c.name} at {c.loc}")
            seen.add(k)
        info = self._probe_ends()
        wires, tunnels, nets = [], [], defaultdict(list)
        for c in self.comps:
            ends, bounds = info[(c.name, c.loc[0], c.loc[1])]
            names = pin_names(c.name, c.attrs, self.sub_pins)
            if len(names) != len(ends):
                raise ValueError(f"{self.name}: {c.name}@{c.loc} has {len(ends)} pins but {len(names)} names")
            c.ends, c.bounds = dict(zip(names, ends)), bounds
            for pn in c.pins:
                if pn not in c.ends:
                    raise ValueError(f"{self.name}: {c.name} has no pin '{pn}' (pins: {names})")
        netw = defaultdict(int)
        for c in self.comps:
            for pn, net in c.pins.items():
                if net is not None:
                    netw[net] = max(netw[net], c.ends[pn][2])
        # direct links
        linked = set()
        for i, (c1, p1, c2, p2, xm, ym) in enumerate(self.links):
            for c in (c1, c2):
                if c.ends is None:
                    e, b = info[(c.name, c.loc[0], c.loc[1])]
                    c.ends, c.bounds = dict(zip(pin_names(c.name, c.attrs, self.sub_pins), e)), b
            (x1, y1, w1, io1), (x2, y2, w2, io2) = c1.ends[p1], c2.ends[p2]
            linked.add((id(c1), p1))
            linked.add((id(c2), p2))
            if y1 == y2:
                pts = [(x1, y1), (x2, y2)]
            elif ym is not None:
                pts = [(x1, y1), (x1, ym), (x2, ym), (x2, y2)]
            else:
                mx = xm if xm is not None else (x1 + x2) // 2
                pts = [(x1, y1), (mx, y1), (mx, y2), (x2, y2)]
            for a, b in zip(pts, pts[1:]):
                if a != b:
                    wires.append((a, b))
            nets[f"_link{i}"].append((c1, p1, w1, io1))
            nets[f"_link{i}"].append((c2, p2, w2, io2))
        # tunnels and stubs, with collision avoidance against everything already on the sheet
        occ = []   # rectangles (x1, y1, x2, y2) that stubs must not touch; entries carry an owner to skip own comp

        def blockers(r, owner=None):
            return [o for o in occ if not (o[4] is not None and o[4] is owner)
                    and r[0] < o[2] and r[2] > o[0] and r[1] < o[3] and r[3] > o[1]]

        def rect_hit(r, owner=None):
            return bool(blockers(r, owner))

        for c in self.comps:
            bx, by, bw, bh = c.bounds
            occ.append((bx - 1, by - 1, bx + bw + 1, by + bh + 1, c))
        for c in self.comps:
            bx, by, bw, bh = c.bounds
            sides = defaultdict(list)
            for pn, net in c.pins.items():
                if net is None or (id(c), pn) in linked:
                    continue
                x, y, w, io = c.ends[pn]
                dW, dE, dN, dS = x - bx, bx + bw - x, y - by, by + bh - y
                if min(dW, dE) <= 2:
                    side = "W" if dW <= dE else "E"
                else:
                    side = "N" if dN <= dS else "S"
                sides[side].append((x if side in "NS" else y, pn, net))
                nets[net].append((c, pn, w, io))
            for side, items in sides.items():
                items.sort()
                coords = [it[0] for it in items]
                pitch = min((q - p for p, q in zip(coords, coords[1:])), default=99)
                if side in "WE" and len(items) >= 2 and pitch < 24:
                    # dense pins: fan the stubs out to rows 30-40 px apart (no crossings), tunnels aligned in one column
                    n = len(items)
                    m = (n - 1) / 2
                    ys = [c.ends[pn][1] for _, pn, _ in items]
                    yc = round(sum(ys) / n / 10) * 10
                    rows = [int((yc - 15 * (n - 1) + 30 * k + 5) // 10 * 10) for k in range(n)]
                    cols = [10 + 10 * int(m - abs(k - m)) for k in range(n)]
                    sg_ = -1 if side == "W" else 1
                    ok = False
                    for extra in range(0, 1200, 10):
                        L = self.stub + max(cols) + extra
                        trial, occ_add = [], []
                        good = True
                        for k, (_, pn, net) in enumerate(items):
                            x, y, w, io = c.ends[pn]
                            tw = est_width(net)
                            tx = x + sg_ * L
                            pts = [(x, y), (x + sg_ * cols[k], y), (x + sg_ * cols[k], rows[k]), (tx, rows[k])]
                            box = (tx - tw, rows[k] - 11, tx, rows[k] + 11) if side == "W" else (tx, rows[k] - 11, tx + tw, rows[k] + 11)
                            segs = [(min(p[0], q[0]) - 1, min(p[1], q[1]) - 1, max(p[0], q[0]) + 1, max(p[1], q[1]) + 1)
                                    for p, q in zip(pts, pts[1:])]
                            if rect_hit(box, c) or any(rect_hit(sg, c) for sg in segs):
                                good = False
                                break
                            trial.append((pn, net, w, pts))
                            occ_add += segs + [box]
                        if good:
                            ok = True
                            break
                    if not ok:
                        k0 = items[0]
                        x0, y0 = c.ends[k0[1]][0], c.ends[k0[1]][1]
                        sg0 = -1 if side == "W" else 1
                        near = []
                        for L in (40, 140):
                            for kk, (_, pn2, net2) in enumerate(items):
                                xx, yy = c.ends[pn2][0], c.ends[pn2][1]
                                tx2 = xx + sg0 * (self.stub + max(cols) + L - 40)
                                tw2 = est_width(net2)
                                bx2 = (tx2 - tw2, rows[kk] - 11, tx2, rows[kk] + 11) if side == "W" else (tx2, rows[kk] - 11, tx2 + tw2, rows[kk] + 11)
                                wr2 = (min(xx, tx2) - 1, min(yy, rows[kk]) - 1, max(xx, tx2) + 1, max(yy, rows[kk]) + 1)
                                bl = blockers(bx2, c) + blockers(wr2, c)
                                if bl:
                                    near.append((L, pn2, [(o[0], o[1], o[2], o[3]) for o in bl[:2]]))
                        raise ValueError(f"{self.name}: no room to fan out {n} dense pins of {c.name} at {c.loc} ({side}); rows={rows} cols={cols} near={near}")
                    for (pn, net, w, pts) in trial:
                        for p, q in zip(pts, pts[1:]):
                            if p != q:
                                wires.append((p, q))
                        a = {"label": net}
                        if side == "W":
                            a["facing"] = "east"
                        if netw[net] > 1:
                            a["width"] = netw[net]
                        tunnels.append(Comp("Tunnel", pts[-1], a, {}, None))
                    for r in occ_add:
                        occ.append((*r, None))
                    continue
                for k, (_, pn, net) in enumerate(items):
                    x, y, w, io = c.ends[pn]
                    tw = est_width(net)
                    placed = False
                    jogs = (0,) if side in "NS" else (0, 30, -30, 60, -60, 90, -90, 120, -120)
                    west_box = side in "WNS"
                    for dv, jx, sgn in [(d, j, sg) for d in jogs for j in ((10, 20, 30, 40, 50) if d else (10,))
                                        for sg in ((-1, 1) if side in "NS" else (-1 if side == "W" else 1,))]:
                        for extra in range(0, 1200, 10):
                            length = self.stub + extra
                            if side in "WE":
                                tx = x + sgn * length
                                pts = [(x, y), (tx, y)] if dv == 0 else [(x, y), (x + sgn * jx, y), (x + sgn * jx, y + dv), (tx, y + dv)]
                                if dv and length <= jx:
                                    continue
                            else:
                                dy = 10 + 30 * k if side == "S" else -(10 + 30 * k)
                                pts = [(x, y), (x, y + dy), (x + sgn * length, y + dy)]
                            tx, ty = pts[-1]
                            west_box = sgn < 0
                            box = (tx - tw, ty - 11, tx, ty + 11) if west_box else (tx, ty - 11, tx + tw, ty + 11)
                            segs = [(min(p[0], q[0]) - 1, min(p[1], q[1]) - 1, max(p[0], q[0]) + 1, max(p[1], q[1]) + 1)
                                    for p, q in zip(pts, pts[1:])]
                            if rect_hit(box, c) or any(rect_hit(sg, c) for sg in segs):
                                continue
                            placed = True
                            break
                        if placed:
                            break
                    if not placed:
                        tx = x + (-1 if side == "W" else 1) * (self.stub + 100)
                        probe = (tx - tw, y - 11, tx, y + 11) if side in "WNS" else (tx, y - 11, tx + tw, y + 11)
                        near = [(o[0], o[1], o[2], o[3]) for o in occ if o[0] < x + 20 and o[2] > x - 300 and o[1] < y + 80 and o[3] > y - 80]
                        raise ValueError(f"{self.name}: no room for the tunnel of {c.name}.{pn} ({net}) at {c.loc}; near={near}; "
                                         f"pin ({x},{y}) side {side}; blockers at +100: box {blockers(probe, c)[:4]} wire {blockers((min(x, tx) - 1, y - 1, max(x, tx) + 1, y + 1), c)[:4]}")
                    for sg in segs:
                        occ.append((*sg, None))
                    occ.append((*box, None))
                    for p, q in zip(pts, pts[1:]):
                        if p != q:
                            wires.append((p, q))
                    a = {"label": net}
                    if west_box:
                        a["facing"] = "east"
                    if netw[net] > 1:
                        a["width"] = netw[net]
                    tunnels.append(Comp("Tunnel", pts[-1], a, {}, None))
        # annotation text: move it to the nearest free spot if it overlaps routed wires, tunnels or components
        def trect(x, y, t, font):
            w = int(len(t) * 0.6 * int(font.split()[-1])) + 6
            return (x - w // 2, y - 16, x + w // 2, y + 4)

        placed_t = []
        moved = []
        for (x, y, t, font) in self.texts:
            cand = None
            for dy, dx in [(0, 0)] + [(sy * d, sx) for d in range(20, 400, 20) for sx in (0, 40, -40, 80, -80) for sy in (-1, 1)]:
                r = trect(x + dx, y + dy, t, font)
                if rect_hit(r) or any(r[0] < q[2] and r[2] > q[0] and r[1] < q[3] and r[3] > q[1] for q in placed_t):
                    continue
                cand = (x + dx, y + dy, r)
                break
            if cand is None:
                cand = (x, y, trect(x, y, t, font))
                self.notes.append(f"text '{t[:30]}...' overlaps something and could not be moved")
            placed_t.append(cand[2])
            moved.append((cand[0], cand[1], t, font))
        self.texts = moved
        # lint
        for net, mem in nets.items():
            widths = {w for _, _, w, _ in mem}
            if len(widths) > 1:
                self.warnings.append(f"net '{net}': widths differ {sorted(widths)} at " +
                                     ", ".join(f"{c.name}.{pn}({w})" for c, pn, w, _ in mem))
            drivers = [(c, pn) for c, pn, w, io in mem
                       if (io == "O" and c.name != "Pin") or (c.name == "Pin" and c.attrs.get("type") != "output")]
            sinks = [(c, pn) for c, pn, w, io in mem if io == "I" and not (c.name == "Pin" and c.attrs.get("type") != "output")]
            bidir = [1 for c, pn, w, io in mem if io == "IO"]
            if not drivers and not bidir:
                self.warnings.append(f"net '{net}' has no driver (sinks: {[f'{c.name}.{pn}' for c, pn in sinks]})")
            if len(drivers) > 1:
                self.warnings.append(f"net '{net}' has several drivers: {[f'{c.name}.{pn}' for c, pn in drivers]}")
            if not sinks and not bidir and len(drivers) == 1 and drivers[0][0].name != "Constant":
                self.notes.append(f"net '{net}' is not used ({drivers[0][0].name}.{drivers[0][1]})")
        # everything must sit on Logisim's 10-px grid, otherwise it is snapped and the wires no longer touch the pins
        for p in {pt for w in wires for pt in w} | {t.loc for t in tunnels} | {c.loc for c in self.comps}:
            if p[0] % 10 or p[1] % 10:
                raise ValueError(f"{self.name}: off-grid point {p}")
        # xml
        head = (f'  <circuit name="{self.name}">\n'
                '    <a name="appearance" val="logisim_evolution"/>\n'
                f'    <a name="circuit" val="{self.name}"/>\n'
                '    <a name="circuitnamedboxfixedsize" val="true"/>\n'
                '    <a name="simulationFrequency" val="1.0"/>\n')
        body = "".join(self._comp_xml(c) for c in self.comps + tunnels)
        for x, y, s, font in self.texts:
            body += (f'    <comp lib="9" loc="({x},{y})" name="Text">\n'
                     f'      <a name="font" val={quoteattr(font)}/>\n'
                     f'      <a name="text" val={quoteattr(s)}/>\n    </comp>\n')
        # split every wire at the end points of the others (Logisim connects at end points only)
        pts = {p for w in wires for p in w}
        out = set()
        for a, b in wires:
            inner = [p for p in pts if (a[0] == b[0] == p[0] and min(a[1], b[1]) < p[1] < max(a[1], b[1])) or
                     (a[1] == b[1] == p[1] and min(a[0], b[0]) < p[0] < max(a[0], b[0]))]
            inner.sort(key=lambda p: abs(p[0] - a[0]) + abs(p[1] - a[1]))
            chain = [a] + inner + [b]
            for u, v in zip(chain, chain[1:]):
                out.add((u, v) if u <= v else (v, u))
        body += "".join(f'    <wire from="({a[0]},{a[1]})" to="({b[0]},{b[1]})"/>\n' for a, b in sorted(out))
        return head + body + "  </circuit>\n"

    def install(self, before=None):
        blk = self.build()
        self.proj.set(self.name, blk, before=before)
        BUILT.append(self)
        # keep the cache of box pin names in sync for later circuits
        for w in self.warnings:
            print(f"  WARNING [{self.name}] {w}")
        for n in self.notes:
            print(f"  note    [{self.name}] {n}")
        return blk
