#!/usr/bin/env python3
"""Build docs/pptx/RV32I_TrinhBay.pptx: the project presentation (Vietnamese) with native shapes, tables and charts.

    python tools/build_pptx.py            # needs: pip install python-pptx pillow
Screenshots of the web page (docs/web/index.html) are taken with headless Edge when it is installed (optional).
"""
import os
import subprocess
import sys
import tempfile

from lxml import etree
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "docs", "pptx", "RV32I_TrinhBay.pptx")
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

def rgb(h): return RGBColor.from_string(h)
NAVY, BLUE, ORANGE, GREEN, RED, PURPLE, GRAY, LIGHT, WHITE, INK = "1F2A44", "2F6DF6", "E8870C", "178A3E", "D63A3A", "8B5CF6", "5F6C7E", "F3F5F9", "FFFFFF", "18202C"
STAGE = {"IF": "3B82F6", "ID": "10B981", "EX": "F59E0B", "MEM": "EF4444", "WB": "8B5CF6"}
FONT, MONO = "Calibri", "Consolas"

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]
TOTAL = [0]
slides = []


# ------------------------------------------------------------------ helpers
def new_slide(title, notes="", section=""):
    s = prs.slides.add_slide(BLANK)
    slides.append(s)
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(0.12))
    fill(bar, BLUE); bar.line.fill.background()
    text(s, 0.55, 0.28, 12.2, 0.8, [(title, dict(size=30, bold=True, color=NAVY))], anchor="middle")
    ln = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(1.08), Inches(1.2), Inches(0.05))
    fill(ln, ORANGE); ln.line.fill.background()
    if section:
        text(s, 9.3, 0.3, 3.5, 0.3, [(section, dict(size=11, color=GRAY))], align="right")
    if notes:
        s.notes_slide.notes_text_frame.text = notes
    return s


def fill(shape, hexcolor):
    shape.fill.solid(); shape.fill.fore_color.rgb = rgb(hexcolor)


def text(slide, x, y, w, h, paras, align="left", anchor="top", font=FONT, wrap=True, margin=0.05):
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame; tf.word_wrap = wrap
    tf.margin_left = tf.margin_right = Inches(margin); tf.margin_top = tf.margin_bottom = Inches(0.03)
    tf.vertical_anchor = {"top": MSO_ANCHOR.TOP, "middle": MSO_ANCHOR.MIDDLE, "bottom": MSO_ANCHOR.BOTTOM}[anchor]
    fill_tf(tf, paras, align, font)
    return tb


def fill_tf(tf, paras, align="left", font=FONT):
    first = True
    for item in paras:
        t, o = (item, {}) if isinstance(item, str) else item
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = {"left": PP_ALIGN.LEFT, "center": PP_ALIGN.CENTER, "right": PP_ALIGN.RIGHT}[o.get("align", align)]
        if o.get("space"): p.space_before = Pt(o["space"])
        if o.get("bullet"):
            pPr = p._p.get_or_add_pPr()
            pPr.set("marL", str(int(Inches(0.28)))); pPr.set("indent", str(-int(Inches(0.28))))
            bu = etree.SubElement(pPr, qn("a:buChar")); bu.set("char", "•")
        runs = o.get("runs") or [(t, {})]
        for rt, ro in runs:
            r = p.add_run(); r.text = rt
            f = r.font; f.name = ro.get("font", o.get("font", font)); f.size = Pt(ro.get("size", o.get("size", 18)))
            f.bold = ro.get("bold", o.get("bold", False)); f.italic = ro.get("italic", o.get("italic", False))
            f.color.rgb = rgb(ro.get("color", o.get("color", INK)))


def bullets(slide, x, y, w, h, items, size=18, gap=6, color=INK):
    paras = []
    for it in items:
        if isinstance(it, tuple):   # (bold lead, rest)
            paras.append(("", dict(bullet=True, space=gap, runs=[(it[0], dict(bold=True, color=NAVY, size=size)), (it[1], dict(size=size, color=color))])))
        else:
            paras.append((it, dict(bullet=True, size=size, space=gap, color=color)))
    return text(slide, x, y, w, h, paras)


def box(slide, x, y, w, h, title, body="", color=BLUE, tsize=15, bsize=12, shape=MSO_SHAPE.ROUNDED_RECTANGLE, txt=WHITE, line=None):
    sh = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    fill(sh, color)
    if line: sh.line.color.rgb = rgb(line); sh.line.width = Pt(1.25)
    else: sh.line.fill.background()
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        sh.adjustments[0] = 0.08
    tf = sh.text_frame; tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(0.08); tf.margin_top = tf.margin_bottom = Inches(0.05)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    paras = [(title, dict(size=tsize, bold=True, color=txt, align="center"))]
    if body: paras.append((body, dict(size=bsize, color=txt, align="center")))
    fill_tf(tf, paras)
    return sh


def arrow(slide, x1, y1, x2, y2, color=GRAY, width=2.0, dash=False):
    c = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    c.line.color.rgb = rgb(color); c.line.width = Pt(width)
    ln = c.line._get_or_add_ln()
    if dash:
        d = etree.SubElement(ln, qn("a:prstDash")); d.set("val", "dash")
    t = etree.SubElement(ln, qn("a:tailEnd")); t.set("type", "triangle")
    return c


def table(slide, x, y, w, rows, col_w, font=12, header=NAVY, row_h=0.36, first_bold=False, zebra=True, align=None):
    nr, nc = len(rows), len(rows[0])
    shp = slide.shapes.add_table(nr, nc, Inches(x), Inches(y), Inches(w), Inches(row_h * nr))
    tb = shp.table
    tblPr = shp._element.graphic.graphicData.tbl.tblPr
    for a in ("bandRow", "firstRow"):
        tblPr.set(a, "0")
    for j, cw in enumerate(col_w):
        tb.columns[j].width = Inches(cw)
    for i, row in enumerate(rows):
        tb.rows[i].height = Inches(row_h)
        for j, val in enumerate(row):
            c = tb.cell(i, j)
            c.margin_left = c.margin_right = Inches(0.07); c.margin_top = c.margin_bottom = Inches(0.03)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            c.fill.solid()
            c.fill.fore_color.rgb = rgb(header if i == 0 else (LIGHT if (zebra and i % 2 == 0) else WHITE))
            tf = c.text_frame; tf.word_wrap = True
            a = (align[j] if align else "left")
            o = dict(size=font, bold=(i == 0 or (first_bold and j == 0)), color=WHITE if i == 0 else INK, align=a)
            fill_tf(tf, [(str(val), o)])
    return tb


def footer_numbers():
    n = len(slides)
    for i, s in enumerate(slides, 1):
        if i == 1:
            continue
        text(s, 0.55, 7.08, 8, 0.3, [("Thiết kế máy tính RISC-V 32-bit trên Logisim Evolution", dict(size=10, color=GRAY))])
        text(s, 11.8, 7.08, 1.0, 0.3, [(f"{i} / {n}", dict(size=10, color=GRAY, align="right"))], align="right")


# ------------------------------------------------------------------ screenshots of the web page (optional)
SHOTS = {}


def take_shots():
    try:
        from PIL import Image
    except ImportError:
        return
    if not os.path.exists(EDGE):
        return
    html = "file:///" + os.path.join(ROOT, "docs", "web", "index.html").replace("\\", "/")
    tmp = tempfile.mkdtemp()
    jobs = {"single": (f"{html}?prog=demo&t=14#single", 1000, (16, 222, 1092, 858)),
            "conveyor": (f"{html}?prog=hazards_demo&t=8#pipe", 1000, (16, 240, 1484, 570)),
            "detail": (f"{html}?prog=hazards_demo&t=8#pipe", 1500, (16, 582, 1484, 1245))}
    for name, (url, h, box_) in jobs.items():
        png = os.path.join(tmp, name + ".png")
        subprocess.run([EDGE, "--headless=new", "--disable-gpu", "--hide-scrollbars", f"--window-size=1500,{h}", "--virtual-time-budget=6000", f"--screenshot={png}", url],
                       capture_output=True, timeout=120)
        if os.path.exists(png):
            out = os.path.join(tmp, name + "_c.png")
            Image.open(png).crop(box_).save(out)
            SHOTS[name] = out


def picture(slide, key, x, y, w):
    if key in SHOTS:
        from PIL import Image
        iw, ih = Image.open(SHOTS[key]).size
        slide.shapes.add_picture(SHOTS[key], Inches(x), Inches(y), width=Inches(w), height=Inches(w * ih / iw))
        return w * ih / iw
    text(slide, x, y, w, 1, [("(hình chụp trang web: chạy tools/build_pptx.py khi có Microsoft Edge)", dict(size=12, color=GRAY))])
    return 1


# ================================================================== SLIDES
take_shots()

# 1 -------------------------------------------------------------- title
s = prs.slides.add_slide(BLANK); slides.append(s)
bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height); fill(bg, NAVY); bg.line.fill.background()
band = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, Inches(5.6), prs.slide_width, Inches(1.9)); fill(band, BLUE); band.line.fill.background()
for i, k in enumerate(["IF", "ID", "EX", "MEM", "WB"]):
    b = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8 + i * 1.25), Inches(1.0), Inches(1.1), Inches(0.5)); fill(b, STAGE[k]); b.line.fill.background()
    fill_tf(b.text_frame, [(k, dict(size=16, bold=True, color=WHITE, align="center"))]); b.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
    if i < 4: arrow(s, 1.92 + i * 1.25, 1.25, 2.03 + i * 1.25, 1.25, color="AAB4C6", width=1.5)
text(s, 0.8, 1.9, 11.8, 2.2, [("THIẾT KẾ MÁY TÍNH RISC-V 32-BIT", dict(size=44, bold=True, color=WHITE)), ("trên Logisim Evolution", dict(size=36, bold=True, color="BFD3FF"))])
text(s, 0.8, 4.0, 11.8, 0.9, [("Kiến trúc tập lệnh RV32I: CPU đơn chu kỳ và CPU pipeline 5 tầng", dict(size=22, color="DCE4F5"))])
text(s, 0.8, 5.85, 11.8, 1.4, [("Nhóm thực hiện: ........................................", dict(size=18, color=WHITE)),
                               ("Giảng viên hướng dẫn: ........................................", dict(size=18, color=WHITE, space=6)),
                               ("Môn học: ........................................", dict(size=18, color=WHITE, space=6))])
s.notes_slide.notes_text_frame.text = ("Chào thầy. Em xin trình bày bài tập lớn: thiết kế máy tính RISC-V 32-bit trên Logisim Evolution, "
                                       "gồm một CPU đơn chu kỳ và một CPU pipeline 5 tầng.")

# 2 -------------------------------------------------------------- goals
s = new_slide("Mục tiêu và kết quả", "Đề bài yêu cầu hai phiên bản CPU, pipeline 5 tầng xử lý đúng hazard, nạp chương trình qua bộ nhớ lệnh và có bộ test. Em đã làm đủ và còn làm cả các lệnh tùy chọn.", "Giới thiệu")
bullets(s, 0.6, 1.4, 6.6, 5.4, [
    ("Đề bài: ", "máy tính 32-bit theo RISC-V RV32I gồm CPU, bộ nhớ lệnh, bộ nhớ dữ liệu và điều khiển"),
    ("Hai phiên bản CPU: ", "đơn chu kỳ (single-cycle) và pipeline 5 tầng IF, ID, EX, MEM, WB"),
    ("Xử lý hazard: ", "forwarding, stall load-use, flush khi rẽ nhánh"),
    ("Đủ tập lệnh: ", "toàn bộ RV32I, kể cả lb, lh, sb, sh, blt, bgeu"),
    ("Chạy từ chương trình: ", "assembler tự viết, nạp qua ROM"),
    ("Kiểm thử: ", "test module, 7 chương trình, chương trình ngẫu nhiên"),
], size=19)
kp = [("2", "CPU dùng chung\ncác khối", BLUE), ("14", "circuit trong\nLogisim", GREEN), ("106", "hàng test-vector\n(9 module)", ORANGE), ("7", "chương trình\ntrên 2 CPU", PURPLE), ("100%", "khớp bộ mô phỏng\ntham chiếu", RED)]
for i, (v, l, c) in enumerate(kp):
    x, y = 7.6 + (i % 2) * 2.65, 1.5 + (i // 2) * 1.85
    b = box(s, x, y, 2.45, 1.6, v, l, color=c, tsize=34, bsize=12)

# 3 -------------------------------------------------------------- architecture
s = new_slide("Kiến trúc tổng thể", "Kiến trúc Harvard: ROM lệnh và RAM dữ liệu riêng nên không xung đột khi vừa nạp lệnh vừa truy cập dữ liệu. Mỗi dây có tên, các tunnel cùng tên là cùng một dây.", "Kiến trúc")
names = [("PC", "địa chỉ lệnh", STAGE["IF"]), ("ROM lệnh", "256 × 32", STAGE["IF"]), ("Giải mã\n+ điều khiển", "InstructionDecode\nMainControl", STAGE["ID"]), ("Thanh ghi", "x0..x31\n32 × 32 bit", STAGE["ID"]),
         ("ALU", "tính kết quả\nso sánh", STAGE["EX"]), ("RAM dữ liệu", "256 × 32\nLoad / Store", STAGE["MEM"]), ("Ghi lại", "chọn giá trị\nghi vào rd", STAGE["WB"])]
for i, (t, b_, c) in enumerate(names):
    x = 0.55 + i * 1.78
    box(s, x, 1.7, 1.55, 1.5, t, b_, color=c, tsize=15, bsize=11)
    if i < 6: arrow(s, x + 1.56, 2.45, x + 1.76, 2.45, color=GRAY, width=2)
arrow(s, 8.45, 3.2, 8.45, 3.75, color=ORANGE, width=2)
arrow(s, 8.45, 3.75, 1.3, 3.75, color=ORANGE, width=2)
arrow(s, 1.3, 3.75, 1.3, 3.2, color=ORANGE, width=2)
text(s, 3.2, 3.8, 5.5, 0.4, [("PC kế tiếp: PC + 4, đích rẽ nhánh/jal, hoặc đích jalr", dict(size=12, color=ORANGE, align="center"))], align="center")
bullets(s, 0.6, 4.4, 12.2, 2.5, [
    ("Harvard: ", "ROM lệnh 256 từ chỉ đọc và RAM dữ liệu 256 từ riêng, không có hazard cấu trúc"),
    ("Dữ liệu 32 bit, lệnh 32 bit, ", "32 thanh ghi x0..x31 (x0 luôn bằng 0), PC 32 bit"),
    ("Tín hiệu có tên: ", "RegWrite, ALUSrc, ASel, ALUOp, ImmSel, MemWrite, MemRead, WBSel, IsBranch, IsJAL, IsJALR; tunnel cùng tên là cùng một dây"),
    ("Hai CPU dùng chung các khối: ", "chỉ khác cách nối và thanh ghi pipeline"),
], size=17)

# 4 -------------------------------------------------------------- ISA
s = new_slide("Tập lệnh RV32I", "Có sáu định dạng lệnh. Điểm hay của RISC-V: các trường opcode, rd, rs1, rs2 luôn ở cùng vị trí bit, nên đọc thanh ghi song song với giải mã.", "Kiến trúc")
rows = [["Kiểu", "31–25", "24–20", "19–15", "14–12", "11–7", "6–0"],
        ["R", "funct7", "rs2", "rs1", "funct3", "rd", "opcode"], ["I", "imm[11:0]", "", "rs1", "funct3", "rd", "opcode"], ["S", "imm[11:5]", "rs2", "rs1", "funct3", "imm[4:0]", "opcode"],
        ["B", "imm[12|10:5]", "rs2", "rs1", "funct3", "imm[4:1|11]", "opcode"], ["U", "imm[31:12]", "", "", "", "rd", "opcode"], ["J", "imm[20|10:1|11|19:12]", "", "", "", "rd", "opcode"]]
table(s, 0.6, 1.4, 12.1, rows, [0.9, 2.6, 1.3, 1.3, 1.3, 2.4, 2.3], font=13, row_h=0.4, first_bold=True)
rows = [["Nhóm", "Lệnh"], ["Số học / logic", "ADD SUB AND OR XOR SLT SLTU SLL SRL SRA"], ["Hằng số", "ADDI ANDI ORI XORI SLTI SLTIU SLLI SRLI SRAI"],
        ["Bộ nhớ", "LW SW  +  LB LH LBU LHU SB SH"], ["Rẽ nhánh / nhảy", "BEQ BNE BLT BGE BLTU BGEU  +  JAL JALR"], ["Khác", "LUI AUIPC"]]
table(s, 0.6, 4.4, 12.1, rows, [2.6, 9.5], font=14, row_h=0.4, first_bold=True)

# 5 -------------------------------------------------------------- blocks
s = new_slide("Các khối của CPU (14 circuit)", "Mỗi khối là một circuit riêng, có file test-vector riêng. Hai CPU là main và Pipeline.", "Thiết kế")
blocks = [("InstructionDecode", "cắt lệnh thành các trường", STAGE["ID"]), ("MainControl", "từ opcode sinh tín hiệu điều khiển", STAGE["ID"]), ("ImmGen", "dựng hằng số 32 bit theo kiểu lệnh", STAGE["ID"]),
          ("RegisterFile", "32 thanh ghi, 2 cổng đọc, 1 cổng ghi", STAGE["ID"]), ("ALUControl", "đổi ALUOp + funct thành mã ALU", STAGE["EX"]), ("ALU", "cộng, trừ, logic, dịch, so sánh", STAGE["EX"]),
          ("BranchUnit", "quyết định có rẽ nhánh không", STAGE["EX"]), ("Memory", "RAM + LoadExtract + StoreMerge", STAGE["MEM"]), ("ForwardingUnit", "chọn nguồn mới nhất cho toán hạng", NAVY),
          ("HazardUnit", "phát hiện load-use, phát stall", NAVY), ("main", "CPU đơn chu kỳ", BLUE), ("Pipeline", "CPU pipeline 5 tầng", BLUE)]
for i, (t, b_, c) in enumerate(blocks):
    x, y = 0.6 + (i % 4) * 3.07, 1.5 + (i // 4) * 1.75
    box(s, x, y, 2.9, 1.55, t, b_, color=c, tsize=17, bsize=13)
text(s, 0.6, 6.75, 12, 0.3, [("Màu: xanh lá = tầng ID, vàng = EX, đỏ = MEM, xanh đậm = xử lý hazard, xanh dương = hai CPU.", dict(size=12, color=GRAY))])

# 6 -------------------------------------------------------------- single-cycle
s = new_slide("CPU đơn chu kỳ (main)", "Mỗi lệnh chạy trọn vẹn trong một chu kỳ. Sơ đồ này chụp từ bản web mô phỏng: khối và dây sáng là phần đang dùng cho lệnh hiện tại.", "CPU đơn chu kỳ")
h = picture(s, "single", 0.55, 1.35, 7.9)
bullets(s, 8.7, 1.4, 4.2, 5.5, [
    "Mỗi lệnh đi qua IF, ID, EX, MEM, WB trong một chu kỳ; CPI = 1",
    ("PC kế tiếp: ", "PC+4; hoặc PC+imm nếu branch được rẽ / jal; hoặc (rs1+imm) bỏ bit 0 nếu jalr"),
    ("lui, auipc, jal, jalr ", "dùng lại ALU và đường ghi lại nhờ ASel và WBSel"),
    ("Đọc thanh ghi và RAM ", "bất đồng bộ để có dữ liệu ngay trong chu kỳ"),
], size=16)

# 7 -------------------------------------------------------------- one instruction
s = new_slide("Một lệnh đi qua năm tầng: add x10, x10, x11", "Ví dụ ở tick 3 của chương trình mẫu: x10 = 0, x11 = 10, ALU cộng ra 0x0a rồi ghi vào x10.", "CPU đơn chu kỳ")
steps = [("IF", "ROM tại PC = 0x08\ntrả 00b50533\nPC+4 = 0x0c"), ("ID", "opcode 0x33 (kiểu R)\nrd=10 rs1=10 rs2=11\nRegWrite=1 ALUSrc=0\nđọc x10=0, x11=0x0a"),
         ("EX", "ALUControl: ADD\nALU: 0 + 0x0a\n= 0x0a"), ("MEM", "không dùng RAM\n(MemRead=MemWrite=0)"), ("WB", "WBSel = 00: chọn ALU\nghi 0x0a vào x10\nPC = 0x0c")]
for i, (k, body) in enumerate(steps):
    x = 0.55 + i * 2.5
    box(s, x, 1.6, 2.3, 0.7, k, "", color=STAGE[k], tsize=22)
    box(s, x, 2.4, 2.3, 2.4, "", "", color=LIGHT, line="C9D1E0")
    text(s, x + 0.05, 2.5, 2.2, 2.2, [(body, dict(size=13, color=INK, align="center", font=MONO))], align="center")
    if i < 4: arrow(s, x + 2.32, 1.95, x + 2.48, 1.95, color=GRAY, width=2)
rows = [["Tick", "x10 sau tick", "Ý nghĩa"], ["3", "0x0a", "lần cộng đầu: 0 + 10"], ["6", "0x13", "10 + 9 = 19"], ["12", "0x22", "27 + 7 = 34"], ["30", "0x37 = 55", "tổng 10 + 9 + ... + 1"]]
table(s, 0.6, 5.1, 7.4, rows, [1.2, 2.2, 4.0], font=14, row_h=0.36)
text(s, 8.4, 5.1, 4.4, 1.8, [("Chương trình mẫu demo.s cộng 10+9+...+1 = 55, lưu vào RAM, đọc lại, gọi một hàm nhân đôi (110).", dict(size=14, color=GRAY))])

# 8 -------------------------------------------------------------- pipeline
s = new_slide("CPU pipeline 5 tầng", "Năm lệnh chạy chồng nhau, mỗi tầng một lệnh. Bốn thanh ghi pipeline giữ mọi thứ lệnh cần ở tầng sau, kể cả từ điều khiển được sinh một lần ở ID.", "CPU pipeline")
stg = [("IF", "Nạp lệnh"), ("ID", "Giải mã,\nđọc thanh ghi"), ("EX", "ALU,\nquyết định nhánh"), ("MEM", "Truy cập RAM"), ("WB", "Ghi lại")]
for i, (k, b_) in enumerate(stg):
    x = 0.55 + i * 2.5
    box(s, x, 1.55, 1.85, 1.5, k, b_, color=STAGE[k], tsize=22, bsize=13)
    if i < 4:
        r = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x + 1.93), Inches(1.55), Inches(0.28), Inches(1.5)); fill(r, "FFE98A"); r.line.color.rgb = rgb("C9A400")
        text(s, x + 1.55, 3.1, 0.95, 0.3, [(["IF/ID", "ID/EX", "EX/MEM", "MEM/WB"][i], dict(size=11, color=GRAY, align="center"))], align="center")
arrow(s, 8.9, 3.45, 8.9, 4.0, color=GREEN, width=2.5); arrow(s, 8.9, 4.0, 5.9, 4.0, color=GREEN, width=2.5); arrow(s, 5.9, 4.0, 5.9, 3.5, color=GREEN, width=2.5)
text(s, 6.0, 4.02, 2.8, 0.3, [("forwarding về EX", dict(size=12, color=GREEN, bold=True, align="center"))], align="center")
bullets(s, 0.6, 4.5, 12.2, 2.5, [
    ("Từ điều khiển ", "sinh một lần ở ID rồi đi cùng lệnh: 13 bit ở ID/EX, 5 bit ở EX/MEM, 3 bit ở MEM/WB"),
    ("Register file ghi ở cạnh xuống ", "của xung nhịp: lệnh ở WB ghi nửa đầu chu kỳ, lệnh ở ID đọc nửa sau nên thấy giá trị mới"),
    ("Hai khối xử lý hazard: ", "ForwardingUnit (chọn toán hạng mới nhất) và HazardUnit (phát hiện load-use)"),
], size=17)

# 9 -------------------------------------------------------------- hazard types
s = new_slide("Ba loại hazard và cách giải quyết", "Forwarding không tốn chu kỳ; load rồi dùng ngay tốn 1 chu kỳ; rẽ nhánh được rẽ tốn 2 chu kỳ vì hủy hai lệnh đã nạp.", "CPU pipeline")
rows = [["Hazard", "Khi nào xảy ra", "Cách giải quyết", "Chi phí"],
        ["Dữ liệu (ALU)", "lệnh sau dùng giá trị lệnh trước chưa ghi xong", "forwarding từ EX/MEM (10) hoặc MEM/WB (01) vào toán hạng của ALU", "0 chu kỳ"],
        ["Load-use", "lệnh sau dùng ngay giá trị vừa load (dữ liệu chỉ có ở cuối MEM)", "stall 1 chu kỳ: PC và IF/ID đứng yên, chèn bubble vào ID/EX; rồi forwarding", "1 chu kỳ"],
        ["Điều khiển", "branch được rẽ, jal, jalr quyết định ở EX", "flush: PC nhảy tới đích, hai lệnh đã nạp phía sau thành bubble", "2 chu kỳ"],
        ["Branch không rẽ", "dự đoán tĩnh \"không rẽ\" đúng", "không làm gì", "0 chu kỳ"]]
table(s, 0.6, 1.5, 12.1, rows, [1.9, 3.7, 4.9, 1.6], font=14, row_h=0.85, first_bold=True, align=["left", "left", "left", "center"])
text(s, 0.6, 6.05, 12.1, 0.9, [("ForwardA = 10 nếu lệnh ở MEM ghi đúng thanh ghi rs1 cần (và rd khác x0); nếu không thì 01 nếu lệnh ở WB ghi; còn lại 00 (đọc từ register file). EX/MEM được ưu tiên vì mới hơn.", dict(size=14, color=GRAY))])

# 10 ------------------------------------------------------------- hazards_demo grid
s = new_slide("Ví dụ: chương trình hazards_demo", "Chương trình gom đủ ba loại hazard. Tick 3: forwarding (ForwardB = 10). Tick 4-5: stall load-use, PC đứng yên. Tick 8: lệnh beq rẽ, hai lệnh sau bị hủy; cuối cùng x5 = x6 = 0.", "CPU pipeline")
prog = [("li x1, 100", "IF ID EX MEM WB"), ("sw x1, 0(x0)", "- IF ID EX MEM WB"), ("lw x2, 0(x0)", "- - IF ID EX MEM WB"), ("addi x3, x2, 1", "- - - IF ID ID* EX MEM WB"),
        ("add x4, x3, x2", "- - - - IF IF ID EX MEM WB"), ("beq x4, x4, skip", "- - - - - - IF ID EX MEM WB"), ("addi x5, x0, 1", "- - - - - - - IF ID X"), ("addi x6, x0, 2", "- - - - - - - - IF X"),
        ("addi x7, x0, 7", "- - - - - - - - - IF ID EX MEM WB")]
ncol = 14
rows = [["lệnh"] + [str(i) for i in range(ncol)]]
cellfill = {}
for r, (name, pat) in enumerate(prog, 1):
    toks = pat.split()
    row = [name] + [""] * ncol
    for c, t in enumerate(toks):
        if t == "-": continue
        row[c + 1] = t.replace("*", "")
        base = t.replace("*", "")
        cellfill[(r, c + 1)] = "F0B94A" if t.endswith("*") else ("D63A3A" if base == "X" else {"IF": "9DBDFB", "ID": "8EE0B9", "EX": "FBD38D", "MEM": "F7A8A8", "WB": "CDB8FB"}[base])
    rows.append(row)
tb = table(s, 0.6, 1.5, 12.1, rows, [2.2] + [0.71] * ncol, font=11, row_h=0.42, header=NAVY, zebra=False, align=["left"] + ["center"] * ncol)
for (r, c), col in cellfill.items():
    cell = tb.cell(r, c); cell.fill.solid(); cell.fill.fore_color.rgb = rgb(col)
    for p in cell.text_frame.paragraphs:
        for run in p.runs:
            run.font.bold = True; run.font.color.rgb = rgb(WHITE if col == "D63A3A" else INK)
bullets(s, 0.6, 5.85, 12.1, 1.2, [
    ("Forwarding (tick 3): ", "sw cần x1 vừa tính xong → lấy từ EX/MEM"),
    ("Stall (ô cam, ID lặp): ", "addi x3 dùng x2 ngay sau lw → chờ 1 chu kỳ"),
    ("Flush (ô đỏ X): ", "beq rẽ ở tick 8 → addi x5, addi x6 bị hủy; kết quả x5 = x6 = 0"),
], size=15, gap=3)

# 11 ------------------------------------------------------------- pipeline detail (web)
s = new_slide("Datapath pipeline chi tiết (bản web)", "Đây là sơ đồ chi tiết của mạch Pipeline trên bản web: bốn thanh ghi pipeline, HazardUnit, ForwardingUnit, các mux forwarding, ALU, BranchUnit, bộ nhớ, ghi lại. Hộp đỏ là stall hoặc flush.", "CPU pipeline")
h = picture(s, "detail", 0.9, 1.3, 11.5)
text(s, 0.9, 1.3 + h + 0.03, 11.5, 0.4, [("Chụp ở tick 8 của hazards_demo: lệnh beq ở EX rẽ nhánh (pc_src_ex = 1), ForwardA và ForwardB đều lấy từ EX/MEM.", dict(size=13, color=GRAY))])

# 12 ------------------------------------------------------------- one trigger
s = new_slide("Chạy một lần bấm", "Trong Logisim, bật Auto-Tick một lần (Ctrl+K) là chương trình chạy từ đầu đến cuối rồi tự dừng, đèn DONE sáng. Chân PAUSE để tạm dừng. Logisim không tự tick được nên một lần Ctrl+K chính là cú kích hoạt.", "Logisim")
box(s, 0.6, 1.6, 2.6, 1.1, "Clock", "xung nhịp thật", color=GRAY)
box(s, 4.1, 1.6, 2.6, 1.1, "AND", "cho xung đi qua khi clk_en = 1", color=BLUE)
box(s, 7.6, 1.6, 2.6, 1.1, "CPU", "PC, thanh ghi, RAM", color=GREEN)
arrow(s, 3.25, 2.15, 4.05, 2.15, width=2.5); arrow(s, 6.75, 2.15, 7.55, 2.15, width=2.5)
box(s, 4.1, 3.5, 2.6, 1.0, "NOR", "PAUSE hoặc đã kết thúc", color=ORANGE)
arrow(s, 5.4, 3.45, 5.4, 2.75, color=ORANGE, width=2.5)
box(s, 0.6, 3.5, 2.6, 1.0, "PAUSE = 1", "tạm dừng", color=GRAY); arrow(s, 3.25, 4.0, 4.05, 4.0, color=ORANGE, width=2)
box(s, 7.6, 3.5, 2.6, 1.0, "DONE = 1", "chương trình đã kết thúc", color=RED); arrow(s, 7.55, 4.0, 6.75, 4.0, color=ORANGE, width=2)
bullets(s, 0.6, 4.9, 12.2, 2.1, [
    ("Đơn chu kỳ: ", "dừng khi lệnh hiện tại là halt: j halt (0x0000006f)"),
    ("Pipeline: ", "dừng một chu kỳ sau khi lệnh halt tới EX, lúc mọi lệnh cũ đã ghi xong"),
    ("Cách chạy: ", "Simulate → Auto-Tick Enabled (Ctrl+K) một lần; Ctrl+R để chạy lại. Không dùng phím tắt: dùng menu Simulate"),
], size=17)

# 13 ------------------------------------------------------------- verification
s = new_slide("Kiểm chứng ở ba mức", "Bộ mô phỏng tham chiếu viết độc lập bằng Python; hai CPU phải cho kết quả giống hệt ở cả 32 thanh ghi và bộ nhớ.", "Kiểm thử")
lv = [("1. Test module", "106 hàng test-vector\n9 module do Logisim chạy", BLUE), ("2. Chương trình", "7 chương trình trên 2 CPU\nso với bộ mô phỏng tham chiếu", GREEN), ("3. Ngẫu nhiên", "chương trình ngẫu nhiên\n60–80 lệnh, nhiều phụ thuộc", ORANGE)]
for i, (t, b_, c) in enumerate(lv):
    box(s, 0.6 + i * 4.1, 1.5, 3.8, 1.7, t, b_, color=c, tsize=20, bsize=15)
box(s, 0.6, 3.7, 3.6, 1.0, "Chương trình .s", "", color=GRAY); box(s, 4.6, 3.7, 3.4, 1.0, "Assembler", "tools/rv.py", color=NAVY)
box(s, 8.4, 3.2 + 0.5, 4.3, 0.55, "CPU đơn chu kỳ  (Logisim)", "", color=BLUE, tsize=14); box(s, 8.4, 4.35, 4.3, 0.55, "CPU pipeline  (Logisim)", "", color=ORANGE, tsize=14)
box(s, 8.4, 5.0, 4.3, 0.55, "Mô phỏng tham chiếu (Python)", "", color=GREEN, tsize=14)
arrow(s, 4.25, 4.2, 4.55, 4.2, width=2.5); arrow(s, 8.05, 4.2, 8.35, 3.95, width=2.5); arrow(s, 8.05, 4.2, 8.35, 4.6, width=2.5); arrow(s, 8.05, 4.25, 8.35, 5.25, width=2.5)
box(s, 0.6, 5.2, 7.4, 0.9, "So sánh cả 32 thanh ghi và mọi từ RAM → OK / DIFFERENT", "", color=RED, tsize=16)
text(s, 0.6, 6.2, 12.1, 0.7, [("Bộ mô phỏng tham chiếu còn được kiểm bằng các mã hóa đã biết (addi x1,x0,5 = 00500093) và bằng chương trình tự kiểm có kết quả tính tay.", dict(size=13, color=GRAY))])

# 14 ------------------------------------------------------------- results chart
s = new_slide("Kết quả: số chu kỳ của hai CPU", "Số chu kỳ đo đến lần ghi thanh ghi cuối cùng. CPU đơn chu kỳ luôn có CPI = 1; pipeline cao hơn ở chương trình có nhiều lệnh rẽ nhánh được rẽ.", "Kết quả")
data = [("demo", 39, 64), ("alu", 91, 94), ("mem", 69, 73), ("hazard", 67, 82), ("jump", 27, 38), ("branch", 69, 104), ("fib", 123, 181)]
cd = CategoryChartData(); cd.categories = [d[0] for d in data]
cd.add_series("single-cycle", [d[1] for d in data]); cd.add_series("pipeline", [d[2] for d in data])
gf = s.shapes.add_chart(XL_CHART_TYPE.COLUMN_CLUSTERED, Inches(0.6), Inches(1.4), Inches(7.6), Inches(5.4), cd)
ch = gf.chart; ch.has_legend = True; ch.legend.position = XL_LEGEND_POSITION.TOP; ch.legend.include_in_layout = False; ch.legend.font.size = Pt(13)
ch.font.size = Pt(12); ch.font.name = FONT
for ser, col in zip(ch.series, (BLUE, ORANGE)):
    ser.format.fill.solid(); ser.format.fill.fore_color.rgb = rgb(col)
    ser.data_labels.show_value = True; ser.data_labels.font.size = Pt(11)
ch.plots[0].gap_width = 60
ch.value_axis.has_major_gridlines = True; ch.value_axis.major_gridlines.format.line.color.rgb = rgb("DDE3EC")
rows = [["Chương trình", "Lệnh", "Đơn", "Pipe", "CPI"], ["alu", "91", "91", "94", "1,03"], ["mem", "69", "69", "73", "1,06"], ["hazard", "67", "67", "82", "1,22"], ["jump", "27", "27", "38", "1,41"],
        ["branch", "69", "69", "104", "1,51"], ["fib", "123", "123", "181", "1,47"], ["demo", "39", "39", "64", "1,64"]]
table(s, 8.5, 1.5, 4.3, rows, [1.3, 0.75, 0.75, 0.75, 0.75], font=13, row_h=0.4, first_bold=True, align=["left", "right", "right", "right", "right"])
text(s, 8.5, 4.9, 4.3, 1.9, [("Đơn = CPU đơn chu kỳ, Pipe = CPU pipeline. CPI của pipeline = số chu kỳ / số lệnh.", dict(size=13, color=GRAY))])

# 15 ------------------------------------------------------------- analysis
s = new_slide("Phân tích: vì sao pipeline không ít chu kỳ hơn?", "Trong mô phỏng của Logisim không có độ trễ cổng, nên pipeline không nhanh hơn tính theo chu kỳ. Lợi ích thật là chu kỳ xung nhịp ngắn hơn vì mỗi tầng chỉ làm một việc. Cái giá là 2 chu kỳ cho mỗi lệnh rẽ nhánh được rẽ.", "Kết quả")
parts = [("39", "lệnh", BLUE), ("+ 22", "11 lần chuyển hướng × 2\n(9 bnez, 1 jal, 1 ret)", RED), ("+ 3", "làm đầy pipeline", GRAY), ("= 64", "chu kỳ của pipeline\n(CPI 1,64)", ORANGE)]
for i, (v, l, c) in enumerate(parts):
    box(s, 0.6 + i * 3.1, 1.6, 2.9, 1.9, v, l, color=c, tsize=36, bsize=14)
bullets(s, 0.6, 3.9, 12.2, 3.0, [
    ("Đơn chu kỳ: ", "mỗi chu kỳ dài (nạp lệnh + giải mã + ALU + RAM + ghi lại) nhưng CPI = 1"),
    ("Pipeline: ", "chu kỳ ngắn hơn nhiều (một tầng), CPI > 1 do branch rẽ và load-use"),
    ("Tương lai: ", "quyết định jal ở ID (phạt 1 chu kỳ), bộ dự đoán nhánh sẽ loại bỏ phần lớn chi phí này"),
], size=18)

# 16 ------------------------------------------------------------- bugs
s = new_slide("Các lỗi đã tìm thấy nhờ kiểm thử", "Các khối ban đầu lần đầu được test bằng test-vector và chương trình hoàn chỉnh; việc này tìm ra lỗi thật. Em kể ngắn ba lỗi tiêu biểu: SLTU, SLL và RAM đọc đồng bộ.", "Kiểm thử")
rows = [["Ở đâu", "Lỗi", "Cách sửa"], ["ALU", "SLTU trả FFFFFFFF thay vì 1 (kết quả 1 bit bị mở rộng dấu)", "mở rộng bằng 0"], ["ALUControl", "SLL kiểu R chọn mã của SRL", "sửa hằng số"],
        ["MainControl", "JALR so với opcode của JAL; LUI chọn hằng số kiểu B", "viết lại phần giải mã"], ["ImmGen", "kiểu U thiếu << 12; bit 0 của kiểu J bằng 1", "đã sửa"],
        ["Memory", "load trả dữ liệu không xác định (RAM đọc đồng bộ)", "đọc bất đồng bộ"], ["Datapath", "JAL, JALR, LUI, AUIPC chưa có đường dữ liệu", "thêm ASel, WBSel, logic PC"]]
table(s, 0.6, 1.5, 12.1, rows, [2.1, 6.9, 3.1], font=15, row_h=0.62, first_bold=True)
text(s, 0.6, 6.0, 12.1, 0.9, [("Cạm bẫy của Logisim: dây chỉ nối ở đầu mút; mọi thứ phải trên lưới 10 px; Constant mặc định bằng 1; RAM mặc định đọc đồng bộ. Bộ sinh mạch hiện kiểm tra tất cả điều này.", dict(size=14, color=GRAY))])

# 17 ------------------------------------------------------------- web
s = new_slide("Bản web trực quan", "Đây là bản mô phỏng trên web để dễ nhìn dữ liệu chạy qua từng tầng. Engine JavaScript được kiểm bằng bộ mô phỏng tham chiếu Python và các giá trị đo trên mạch thật.", "Công cụ")
h = picture(s, "conveyor", 0.55, 1.35, 12.2)
text(s, 0.6, 1.35 + h + 0.03, 12.1, 0.4, [("Chụp ở tick 8 của hazards_demo: thẻ đỏ là hai lệnh bị flush, đường xanh là forwarding.", dict(size=12, color=GRAY))])
bullets(s, 0.6, 1.35 + h + 0.5, 6.0, 2.6, [
    ("Băng chuyền lệnh: ", "mỗi lệnh là một thẻ tiến qua 5 tầng"),
    ("Stall, flush, forwarding ", "hiện bằng thẻ nhấp nháy, thẻ đỏ, mũi tên xanh"),
    ("Chạy tự động ", "đến hết hoặc từng tick, có nút lùi"),
], size=16)
bullets(s, 6.9, 1.35 + h + 0.5, 6.0, 2.6, [
    ("Datapath chi tiết ", "của mạch Pipeline với giá trị thật"),
    ("Biểu đồ hiệu năng, ", "sơ đồ luồng của 14 circuit"),
    ("Kiểm chứng engine: ", "node tools/web/test_engine.js"),
], size=16)

# 18 ------------------------------------------------------------- demo plan
s = new_slide("Kịch bản demo", "Đây là thứ tự demo trực tiếp (10 đến 12 phút). Chi tiết ở file HUONG_DAN_TRINH_BAY.", "Demo")
rows = [["Bước", "Làm gì", "Cho thầy xem"], ["1", "Mở Logisim, chỉ vào main và Pipeline", "hai CPU dùng chung các khối"], ["2", "Ctrl+R, rồi Ctrl+F9 từng lần", "x10 = 0x0a ở tick 3, 0x13 ở tick 6"],
        ["3", "Bật Auto-Tick (Ctrl+K) một lần", "chạy hết, DONE = 1: x10 = 0x37, x12 = 0x6e"], ["4", "Load Image hazards_demo.hex, chạy 8 tick", "x5 = x6 = 0, x3 = 0x65, x4 = 0xc9"],
        ["5", "Mở Pipeline, chạy từng tick", "ForwardB = 10 (tick 3), stall = 1 (tick 4), pc_src_ex = 1 (tick 8)"], ["6", "python tools\\live_proof.py", "VERDICT: both CPUs produce exactly the reference result"],
        ["7", "Mở trang web, chạy tự động đến hết", "băng chuyền lệnh và biểu đồ hiệu năng"]]
table(s, 0.6, 1.5, 12.1, rows, [0.9, 5.2, 6.0], font=15, row_h=0.62, first_bold=True)

# 19 ------------------------------------------------------------- future + conclusion
s = new_slide("Hướng phát triển và kết luận", "Chưa làm các mục tùy chọn nâng cao. Kết luận: đủ yêu cầu cơ bản, hai CPU khớp bộ mô phỏng tham chiếu.", "Kết luận")
text(s, 0.6, 1.4, 6.0, 0.5, [("Chưa cài đặt (tùy chọn)", dict(size=20, bold=True, color=NAVY))])
bullets(s, 0.6, 1.95, 5.9, 4.5, ["Dự đoán rẽ nhánh, cache", "Nhân / chia (mở rộng M)", "Ngắt, GPIO / UART, số thực", ("Bước tiếp theo rẻ nhất: ", "quyết định jal ở ID; bộ dự đoán nhánh 1–2 bit")], size=17)
text(s, 6.9, 1.4, 6.0, 0.5, [("Kết luận", dict(size=20, bold=True, color=NAVY))])
bullets(s, 6.9, 1.95, 5.9, 4.8, ["Đủ RV32I, kể cả lệnh tùy chọn", "Hai CPU: đơn chu kỳ và pipeline 5 tầng", "Hazard dữ liệu và điều khiển xử lý đúng", "Chương trình nạp qua ROM bằng assembler",
                                 "Kiểm thử ba mức: hai CPU khớp bộ mô phỏng độc lập", "Pipeline cần nhiều chu kỳ hơn trong mô phỏng, đúng như lý thuyết"], size=17)

# 20 ------------------------------------------------------------- Q&A
s = prs.slides.add_slide(BLANK); slides.append(s)
bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height); fill(bg, NAVY); bg.line.fill.background()
text(s, 0.8, 2.3, 11.8, 1.6, [("Cảm ơn thầy đã lắng nghe", dict(size=44, bold=True, color=WHITE, align="center")), ("Em xin nhận câu hỏi", dict(size=28, color="BFD3FF", align="center", space=12))], align="center")
qa = ["Pipeline khác single-cycle thế nào?", "Forwarding là gì?", "Vì sao load-use phải stall?", "Branch mất bao nhiêu chu kỳ?", "Làm sao biết CPU đúng?"]
text(s, 0.8, 5.0, 11.8, 1.8, [("Câu hỏi dự kiến: " + "   •   ".join(qa), dict(size=14, color="AAB4C6", align="center"))], align="center")
s.notes_slide.notes_text_frame.text = ("Pipeline khác single-cycle: single-cycle xong một lệnh trong một chu kỳ; pipeline chia 5 tầng cho 5 lệnh chạy chồng nhau. "
                                       "Forwarding: lấy kết quả của lệnh trước ngay từ thanh ghi pipeline. Load-use: dữ liệu load chỉ có ở cuối MEM nên lệnh sau phải chờ 1 chu kỳ. "
                                       "Branch được rẽ mất 2 chu kỳ, không rẽ thì không mất. Kiểm chứng: test module, 7 chương trình so với bộ mô phỏng độc lập, chương trình ngẫu nhiên.")

footer_numbers()
os.makedirs(os.path.dirname(OUT), exist_ok=True)
prs.save(OUT)
print("wrote", os.path.relpath(OUT, ROOT), f"({len(slides)} slides, {len(SHOTS)} screenshots)")
