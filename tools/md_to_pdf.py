"""Convert a Markdown file to PDF via python-markdown + headless Edge.  Usage: python tools/md_to_pdf.py in.md out.pdf"""
import sys, subprocess, tempfile, pathlib, markdown
src, dst = pathlib.Path(sys.argv[1]).resolve(), pathlib.Path(sys.argv[2]).resolve()
body = markdown.markdown(src.read_text(encoding="utf-8"), extensions=["tables", "fenced_code", "sane_lists"])
css = """@page{size:A4;margin:16mm}body{font:11pt/1.5 'Segoe UI',Arial,sans-serif;color:#1a1a1a}
h1{font-size:20pt;border-bottom:2px solid #2f6df6;padding-bottom:4px}h2{font-size:15pt;color:#2f6df6;margin-top:18px;page-break-after:avoid}h3{font-size:12.5pt}
table{border-collapse:collapse;width:100%;margin:8px 0;font-size:10pt;page-break-inside:avoid}th,td{border:1px solid #bbb;padding:4px 7px;vertical-align:top;text-align:left}th{background:#eef2fb}
code{font-family:Consolas,monospace;background:#f1f3f6;padding:0 3px;border-radius:3px;font-size:9.5pt}pre{background:#f1f3f6;padding:8px;border-radius:6px;overflow-wrap:anywhere;white-space:pre-wrap}pre code{background:none;padding:0}
hr{border:0;border-top:1px solid #ccc;margin:14px 0}li{margin:2px 0}"""
html = f"<!doctype html><html lang='vi'><head><meta charset='utf-8'><title>{src.stem}</title><style>{css}</style></head><body>{body}</body></html>"
tmp = pathlib.Path(tempfile.mkdtemp()) / "in.html"; tmp.write_text(html, encoding="utf-8")
edge = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
subprocess.run([edge, "--headless", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={dst}", tmp.as_uri()], check=True, capture_output=True)
print("wrote", dst, dst.stat().st_size, "bytes")
