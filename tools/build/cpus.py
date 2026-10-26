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
    c.add("Clock", (150, 300), {"appearance": "NewPins"}, {"out": "CLK"})
    c.text(130, 330, "Clock: Simulate > Tick")
    c.add("Pin", (150, 420), {"appearance": "classic", "label": "RESET"}, {"p": "RESET"})
    c.text(150, 450, "RESET = 1 holds PC at 0")
    c.add("Constant", (420, 500), {}, {"out": "one"})
    pc = c.add("Register", (540, 330), {"appearance": "logisim_evolution", "label": "PC", "width": 32},
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
    c.add("Probe", (1400, 900), {"appearance": "NewPins", "radix": 16, "label": "instr"}, {"p": "instr"})

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
                                          "rs1": "rs1", "rs2": "rs2", "rs1_data": "rs1_data", "rs2_data": "rs2_data"})
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
    c.add("Probe", (5300, 700), {"appearance": "NewPins", "radix": 16, "label": "wb_data"}, {"p": "wb_data"})

    c.install(before="ALU")
    return c


def rom_text(words):
    """Logisim ROM contents (8 words per line) for an assembled program."""
    ws = [f"{w:08x}" for w in words]
    ws += ["00000000"] * (-len(ws) % 8)
    nl = chr(10)
    return "addr/data: 8 32" + nl + nl.join(" ".join(ws[k:k + 8]) for k in range(0, len(ws), 8)) + nl


def tightest(fn, proj, rom, name, candidates):
    """Build `fn` with the smallest spread factor for which the router finds room for every tunnel."""
    last = None
    for sp in candidates:
        try:
            c = fn(proj, rom, sp)
            print(f"  {name}: layout spread {sp}")
            return c
        except ValueError as e:
            last = e
    raise last


SPREADS = [(0.5, 0.5), (0.55, 0.55), (0.6, 0.6), (0.65, 0.65), (0.7, 0.7), (0.75, 0.75), (0.8, 0.8), (0.9, 0.9), (1.0, 1.0), (1.15, 1.15)]


def build(proj, rom=DEMO):
    import pipeline
    print("generating single_cycle")
    tightest(single_cycle, proj, rom, "main", SPREADS)
    print("generating pipeline")
    tightest(pipeline.pipeline, proj, rom, "Pipeline", SPREADS)
