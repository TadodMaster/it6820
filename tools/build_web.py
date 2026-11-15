#!/usr/bin/env python3
"""Build docs/web/index.html: a single self-contained page (engine + programs + flowcharts inlined).

  python tools/build_web.py          # writes docs/web/index.html
"""
import json
import re
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WEB = os.path.join(ROOT, "tools", "web")


def read(p):
    return open(p, encoding="utf-8").read()


def js_json(obj):
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\/")


def flow_vi():
    """The Vietnamese flowcharts are the last section of docs/KIEN_TRUC.md; promote its headings back by one level."""
    md = read(os.path.join(ROOT, "docs", "KIEN_TRUC.md"))
    md = md[md.index("## Sơ đồ luồng (flowchart) của từng circuit"):]
    out, fence = [], False
    for ln in md.splitlines():
        if ln.lstrip().startswith("```"):
            fence = not fence
        if not fence and re.match(r"#{2,6} ", ln):
            ln = ln[1:]
        out.append(ln)
    return chr(10).join(out) + chr(10)


def main():
    progs = json.loads(subprocess.run([sys.executable, os.path.join(WEB, "dump_programs.py")], cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8"))
    page = read(os.path.join(WEB, "template.html"))
    page = page.replace("/*__ENGINE__*/", read(os.path.join(WEB, "engine.js")).replace("</", "<\/"))
    page = page.replace("/*__PDETAIL__*/", read(os.path.join(WEB, "pipeline_detail.js")).replace("</", "<\/"))
    page = page.replace("/*__PCONV__*/", read(os.path.join(WEB, "pipeline_conveyor.js")).replace("</", "<\/"))
    page = page.replace("/*__PROGRAMS__*/{}", js_json(progs))
    page = page.replace('/*__FLOW_VI__*/""', js_json(flow_vi()))
    page = page.replace('/*__FLOW_EN__*/""', js_json(read(os.path.join(WEB, "flowcharts_en.md"))))
    out = os.path.join(ROOT, "docs", "web", "index.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8", newline="\n").write(page)
    print("wrote", os.path.relpath(out, ROOT), f"({len(page) // 1024} KB)")


if __name__ == "__main__":
    main()
