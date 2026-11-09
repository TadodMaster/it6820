#!/usr/bin/env python3
"""Build docs/web/index.html: a single self-contained page (engine + programs + flowcharts inlined).

  python tools/build_web.py          # writes docs/web/index.html
"""
import json
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
WEB = os.path.join(ROOT, "tools", "web")


def read(p):
    return open(p, encoding="utf-8").read()


def js_json(obj):
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\/")


def main():
    progs = json.loads(subprocess.run([sys.executable, os.path.join(WEB, "dump_programs.py")], cwd=ROOT, capture_output=True, check=True).stdout.decode("utf-8"))
    page = read(os.path.join(WEB, "template.html"))
    page = page.replace("/*__ENGINE__*/", read(os.path.join(WEB, "engine.js")).replace("</", "<\/"))
    page = page.replace("/*__PDETAIL__*/", read(os.path.join(WEB, "pipeline_detail.js")).replace("</", "<\/"))
    page = page.replace("/*__PCONV__*/", read(os.path.join(WEB, "pipeline_conveyor.js")).replace("</", "<\/"))
    page = page.replace("/*__PROGRAMS__*/{}", js_json(progs))
    page = page.replace('/*__FLOW_VI__*/""', js_json(read(os.path.join(ROOT, "docs", "vi", "FLOWCHARTS.md"))))
    page = page.replace('/*__FLOW_EN__*/""', js_json(read(os.path.join(ROOT, "docs", "FLOWCHARTS.md"))))
    out = os.path.join(ROOT, "docs", "web", "index.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8", newline="\n").write(page)
    print("wrote", os.path.relpath(out, ROOT), f"({len(page) // 1024} KB)")


if __name__ == "__main__":
    main()
