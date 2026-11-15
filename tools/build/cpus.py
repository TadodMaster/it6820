"""Top-level CPU circuits: single-cycle (`main`) and 5-stage pipeline (`Pipeline`)."""
from circgen import Circ
from blocks import splitter

DEMO = """addr/data: 8 32
00500093 00700113 002081b3 40118233 00302423 00802283 00518463 06300313
00100393 0000006f
"""


def stage_headers(c, items, y=60):
    for x, s in items:
        c.title(x, y, s)


def sub(c, name, loc, pins):
    """Sub-circuit instance; `loc` is its first output pin."""
    return c.add(name, loc, None, pins)


def single_cycle(proj, rom_contents=DEMO, spread=(1.0, 1.0)):
    c = Circ(proj, "main", stub=30, spread=spread)
    c.title(1700, 30, "RV32I single-cycle CPU - top level")
    c.text(1700, 52, "One instruction per clock cycle.  Data flows left to right: IF > ID > EX > MEM > WB.  "
                     "Tunnels with the same name are the same wire.")
    stage_headers(c, [(700, "IF - Instruction Fetch"), (1900, "ID - Decode / Register Read"),
                      (3100, "EX - Execute and next PC"), (4150, "MEM - Data Memory"), (5000, "WB - Write Back")], y=100)

    # ---------------------------------------------------------------- IF
    c.add("Clock", (150, 300), {"appearance": "NewPins"}, {"out": "CLK_RAW"})
    c.text(130, 330, "Clock: Ctrl+F9 = 1 full cycle,  Ctrl+K = auto-tick")
    # one-trigger run: the clock is gated.  PAUSE = 1 stops it, and it stops by itself at the final "halt: j halt" (instr = 0x0000006f)
    c.add("AND Gate", (330, 300), {}, {"in1": "CLK_RAW", "in2": "clk_en", "out": "CLK"})
    c.add("Pin", (150, 980), {"appearance": "classic", "label": "PAUSE"}, {"p": "PAUSE"})
    c.text(150, 1010, "PAUSE = 1 stops the clock")
    c.add("NOR Gate", (420, 980), {}, {"in1": "PAUSE", "in2": "is_halt", "out": "clk_en"})
    c.add("Constant", (150, 1100), {"width": 32, "value": "0x6f"}, {"out": "halt_code"})
    c.add("Comparator", (620, 1100), {"width": 32, "mode": "unsigned"}, {"a": "instr", "b": "halt_code", "eq": "is_halt"})
    c.add("Pin", (940, 1100), {"appearance": "classic", "label": "DONE", "type": "output", "facing": "west"}, {"p": "is_halt"})
    c.text(620, 1160, "DONE = 1: the program reached  halt: j halt  and the clock stopped")
    c.add("Pin", (150, 420), {"appearance": "classic", "label": "RESET"}, {"p": "RESET"})
    c.text(150, 450, "RESET = 1 holds PC at 0")
    c.add("Constant", (420, 500), {}, {"out": "one"})
    pc = c.add("Register", (540, 330), {"appearance": "logisim_evolution", "label": "PC", "width": 32, "showInTab": "true"},
               {"q": "pc", "d": "next_pc", "clk": "CLK", "r": "RESET", "we": "one"})
    c.text(570, 310, "PC register")
    c.add("Splitter", (900, 360), splitter(3, 32, {**{0: 0, 1: 0}, **{k: 1 for k in range(2, 10)}, **{k: 2 for k in range(10, 32)}}),
          {"bus": "pc", "b1": "pc_word"})
    c.text(960, 470, "PC[9:2] = word address")
    c.add("Constant", (700, 640), {"width": 32, "value": "0x4"}, {"out": "four"})
    c.add("Adder", (1000, 640), {"width": 32}, {"a": "pc", "b": "four", "out": "pc_plus4"})
    c.text(1000, 600, "PC + 4")
    c.add("ROM", (1000, 800), {"addrWidth": 8, "dataWidth": 32, "contents": rom_contents, "appearance": "classic"},
          {"addr": "pc_word", "dout": "instr"})
    c.text(1120, 780, "Instruction ROM 256 x 32")

    # ---------------------------------------------------------------- ID
    sub(c, "InstructionDecode", (1980, 280), {"Instruction": "instr", "funct7": "funct7", "rs2": "rs2", "rs1": "rs1",
                                              "funct3": "funct3", "rd": "rd", "opcode": "opcode"})
    c.text(1850, 250, "InstructionDecode")
    sub(c, "MainControl", (1980, 700), {"opcode": "opcode", "RegWrite": "RegWrite", "ALUSrc": "ALUSrc",
                                         "MemWrite": "MemWrite", "MemRead": "MemRead", "IsBranch": "IsBranch",
                                         "ALUOp": "ALUOp", "ImmSel": "ImmSel", "ASel": "ASel", "WBSel": "WBSel",
                                         "IsJAL": "IsJAL", "IsJALR": "IsJALR"})
    c.text(1850, 670, "MainControl")
    sub(c, "ImmGen", (1980, 1100), {"Instruction": "instr", "ImmSel": "ImmSel", "Imm": "imm"})
    c.text(1850, 1070, "ImmGen")
    sub(c, "RegisterFile", (1980, 1400), {"write_data": "wb_data", "CLK": "CLK", "write": "RegWrite", "rd": "rd",
                                          "rs1": "rs1", "rs2": "rs2", "rs1_data": "rs1_data", "rs2_data": "rs2_data", "reg_x1": "x1", "reg_x2": "x2", "reg_x3": "x3", "reg_x4": "x4", "reg_x5": "x5", "reg_x6": "x6", "reg_x7": "x7", "reg_x10": "x10", "reg_x11": "x11", "reg_x12": "x12", "reg_x13": "x13", "reg_x14": "x14"})
    c.text(1850, 1370, "RegisterFile")

    # ---------------------------------------------------------------- EX
    c.add("Constant", (2700, 330), {"width": 32, "value": "0x0"}, {"out": "zero32"})
    c.add("Multiplexer", (3050, 380), {"select": 2, "width": 32},
          {"d0": "rs1_data", "d1": "pc", "d2": "zero32", "d3": "zero32", "sel": "ASel", "out": "alu_a"})
    c.text(2800, 300, "ALU operand A: 00 rs1   01 PC (auipc)   10 zero (lui)")
    c.add("Multiplexer", (3050, 620), {"select": 1, "width": 32},
          {"d0": "rs2_data", "d1": "imm", "sel": "ALUSrc", "out": "alu_b"})
    c.text(2800, 570, "ALU operand B: 0 rs2   1 imm")
    sub(c, "ALUControl", (3430, 900), {"funct7": "funct7", "ALUOp": "ALUOp", "funct3": "funct3", "ALUCtrl": "ALUCtrl"})
    c.text(3300, 870, "ALUControl")
    sub(c, "ALU", (3430, 1100), {"rs1_data": "alu_a", "rs2_data": "alu_b", "ALU_Ctrl": "ALUCtrl", "result": "alu_result"})
    c.text(3300, 1070, "ALU")
    sub(c, "BranchUnit", (3430, 1350), {"rs1_data": "rs1_data", "rs2_data": "rs2_data", "IsBranch": "IsBranch",
                                         "funct3": "funct3", "branch_taken": "branch_taken"})
    c.text(3300, 1320, "BranchUnit (beq bne blt bge bltu bgeu)")
    # next PC
    c.title(2750, 1560, "Next PC")
    c.add("Adder", (3050, 1720), {"width": 32}, {"a": "pc", "b": "imm", "out": "pc_target"})
    c.text(2950, 1670, "PC + imm (branch / JAL target)")
    c.add("Constant", (2700, 1900), {"width": 32, "value": "0xfffffffe"}, {"out": "mask_even"})
    c.add("AND Gate", (3050, 1900), {"width": 32}, {"in1": "alu_result", "in2": "mask_even", "out": "jalr_target"})
    c.text(2900, 1850, "JALR target = (rs1 + imm) with bit 0 cleared")
    c.add("OR Gate", (3050, 2060), {}, {"in1": "branch_taken", "in2": "IsJAL", "out": "take_target"})
    c.add("Multiplexer", (3500, 1780), {"select": 1, "width": 32},
          {"d0": "pc_plus4", "d1": "pc_target", "sel": "take_target", "out": "pc_a"})
    c.add("Multiplexer", (3500, 2000), {"select": 1, "width": 32},
          {"d0": "pc_a", "d1": "jalr_target", "sel": "IsJALR", "out": "next_pc"})
    c.text(3300, 1700, "take_target = branch taken OR JAL")
    c.text(3300, 1940, "IsJALR selects the register jump")

    # ---------------------------------------------------------------- MEM / WB
    sub(c, "Memory", (4260, 400), {"Address": "alu_result", "write_data": "rs2_data", "MemWrite": "MemWrite",
                                    "CLK": "CLK", "funct3": "funct3", "read_data": "mem_rdata"})
    c.text(4130, 370, "Memory (lb lh lw lbu lhu sb sh sw)")
    c.add("Multiplexer", (4900, 700), {"select": 2, "width": 32},
          {"d0": "alu_result", "d1": "mem_rdata", "d2": "pc_plus4", "d3": "zero32", "sel": "WBSel", "out": "wb_data"})
    c.text(4650, 620, "WBSel: 00 ALU   01 memory   10 PC+4 (JAL/JALR)")

    c.monitor(700, 2300, 800, [
        ("pc", "PC", 16, ("PC: địa chỉ lệnh đang được nạp", "(tăng 4 mỗi chu kỳ, nhảy khi rẽ nhánh)")),
        ("instr", "instr", 16, ("instr: mã máy 32-bit của lệnh", "đang thực thi (đọc từ ROM)")),
        ("alu_result", "alu_result", 16, ("alu_result: kết quả ALU", "(số học, địa chỉ load/store)")),
        ("branch_taken", "branch_taken", 2, ("branch_taken: 1 = lệnh rẽ nhánh", "được rẽ, PC nhảy tới đích")),
        ("wb_data", "wb_data", 16, ("wb_data: giá trị ghi vào thanh ghi rd", "ở cuối chu kỳ (write-back)")),
    ], "BẢNG THEO DÕI (probe): xem các giá trị này sau mỗi lần bấm Ctrl+F9")
    c.monitor(700, 2560, 800, [
        ("RegWrite", "RegWrite", 2, ("RegWrite = 1: lệnh sẽ ghi", "vào thanh ghi rd")),
        ("MemWrite", "MemWrite", 2, ("MemWrite = 1: lệnh store,", "ghi vào RAM dữ liệu")),
        ("ALUSrc", "ALUSrc", 2, ("ALUSrc: 0 = toán hạng B là rs2,", "1 = là hằng số imm")),
        ("ALUCtrl", "ALUCtrl", 16, ("ALUCtrl: mã phép ALU (0 ADD, 1 SUB,", "2 AND, 3 OR, 4 XOR, 5 SLL, 6 SRL, 7 SRA...)")),
        ("WBSel", "WBSel", 2, ("WBSel: 00 ALU, 01 bộ nhớ,", "10 PC+4 (JAL/JALR)")),
    ], "PROBE ĐIỀU KHIỂN (MainControl): lệnh đang chạy bật những tín hiệu nào")
    c.monitor(700, 2820, 800, [
        ("rs1_data", "rs1_data", 16, ("rs1_data: giá trị thanh ghi rs1", "đọc từ register file")),
        ("rs2_data", "rs2_data", 16, ("rs2_data: giá trị thanh ghi rs2", "(cũng là dữ liệu của lệnh store)")),
        ("imm", "imm", 16, ("imm: hằng số tức thời đã", "mở rộng dấu (ImmGen)")),
        ("mem_rdata", "mem_rdata", 16, ("mem_rdata: dữ liệu đọc từ RAM", "(chỉ có nghĩa với lệnh load)")),
        ("next_pc", "next_pc", 16, ("next_pc: địa chỉ lệnh kế tiếp", "(PC+4, đích rẽ nhánh hoặc JALR)")),
    ], "PROBE DỮ LIỆU: các giá trị chạy trong datapath")
    notes = {1: "địa chỉ trả về / giá trị", 2: "thanh ghi tạm", 3: "thanh ghi tạm", 4: "thanh ghi tạm", 5: "thanh ghi tạm", 6: "thanh ghi tạm", 7: "thanh ghi tạm",
             10: "tổng cộng dồn (demo)", 11: "biến đếm vòng lặp", 12: "kết quả hàm nhân đôi", 13: "giá trị đọc lại từ RAM", 14: "cờ so sánh"}
    for row, grp in enumerate(([1, 2, 3, 4, 5, 6], [7, 10, 11, 12, 13, 14])):
        c.monitor(700, 3080 + row * 260, 800, [(f"x{r}", f"x{r}", 16, (f"x{r}: giá trị thanh ghi x{r}", f"({notes[r]})")) for r in grp],
                  "PROBE THANH GHI (RegisterFile): giá trị các thanh ghi chương trình mẫu dùng" if row == 0 else "PROBE THANH GHI (tiếp)")

    c.install(before="ALU")
    return c


def rom_text(words):
    """Logisim ROM contents (8 words per line) for an assembled program."""
    ws = [f"{w:08x}" for w in words]
    ws += ["00000000"] * (-len(ws) % 8)
    nl = chr(10)
    return "addr/data: 8 32" + nl + nl.join(" ".join(ws[k:k + 8]) for k in range(0, len(ws), 8)) + nl


def tightest(fn, proj, rom, name, candidates, grid=7):
    """Build `fn` with the smallest layout for which the router finds room for every tunnel.

    First the smallest uniform spread factor, then x and y are reduced independently (smallest area first)."""
    import circgen
    start = len(circgen.BUILT)
    last = None
    found = None
    for sp in candidates:
        try:
            c = fn(proj, rom, sp)
            found = (sp, c)
            break
        except ValueError as e:
            last = e
    if found is None:
        raise last
    (bx, by), best = found[0], found[1]
    trials = sorted(((round(bx - i * 0.05, 2), round(by - j * 0.05, 2)) for i in range(0, grid) for j in range(0, grid)
                     if (i or j) and bx - i * 0.05 >= 0.4 and by - j * 0.05 >= 0.4), key=lambda t: (t[0] * t[1], t))
    for sp in trials:
        try:
            c = fn(proj, rom, sp)
        except ValueError:
            continue
        best, bx, by = c, sp[0], sp[1]
        break
    print(f"  {name}: layout spread ({bx}, {by})")
    if best is not found[1]:
        best = fn(proj, rom, (bx, by))   # rebuild so that the project holds the winning layout
    del circgen.BUILT[start:-1]          # only the final layout is verified
    return best


SPREADS = [(0.5, 0.5), (0.55, 0.55), (0.6, 0.6), (0.65, 0.65), (0.7, 0.7), (0.75, 0.75), (0.8, 0.8), (0.9, 0.9), (1.0, 1.0), (1.15, 1.15)]


def build(proj, rom=DEMO):
    import pipeline
    print("generating single_cycle")
    tightest(single_cycle, proj, rom, "main", SPREADS)
    print("generating pipeline")
    tightest(pipeline.pipeline, proj, rom, "Pipeline", SPREADS)
