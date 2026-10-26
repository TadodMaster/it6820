"""Generators for the control / memory / hazard sub-circuits of the RV32I CPU."""
from circgen import Circ


# 16-row ROM: address = {size, Address[1:0]}, data = byte enables (bit i = lane i is written)
BYTE_ENABLES = "addr/data: 4 4\n1 2 4 8 3 3 c c f f f f f f f f\n"


def bits(n, per):
    """Splitter bit assignment: bit k goes to branch k // per."""
    return {f"bit{k}": k // per for k in range(n)}


def splitter(fanout, incoming, assign, facing=None):
    a = {"fanout": fanout, "incoming": incoming, "spacing": 3}   # wide pin spacing leaves room for tunnels
    a.update({f"bit{k}": v for k, v in assign.items()})
    if facing:
        a["facing"] = facing
    return a


def sp_even(fanout, incoming, facing=None):
    per = incoming // fanout
    return splitter(fanout, incoming, {k: k // per for k in range(incoming)}, facing)


# ------------------------------------------------------------------------------------------------
def main_control(proj):
    c = Circ(proj, "MainControl", spread=(1.2, 1.1))
    c.title(520, 30, "MainControl")
    c.text(520, 50, "Compares opcode with each instruction class (left) and combines the flags into control signals (right).")
    c.pin_in("opcode", 7, (120, 120), radix=None)
    classes = [("IsR", 0x33, "R-type"), ("IsI", 0x13, "I-type ALU"), ("IsLoad", 0x03, "load"),
               ("IsStore", 0x23, "store"), ("IsBranch", 0x63, "branch"), ("IsLui", 0x37, "LUI"),
               ("IsAuipc", 0x17, "AUIPC"), ("IsJAL", 0x6F, "JAL"), ("IsJALR", 0x67, "JALR")]
    for i, (flag, op, desc) in enumerate(classes):
        y = 110 + 80 * i
        k = c.add("Constant", (330, y + 10), {"value": f"0x{op:02x}", "width": 7})
        cmp_ = c.add("Comparator", (560, y), {"width": 7, "mode": "unsigned"}, {"a": "opcode", "eq": flag})
        c.link(k, "out", cmp_, "b", xm=420)
        c.text(330, y - 18, f"opcode 0x{op:02X} = {desc}")
    # --- single-output decodes
    x = 1100
    c.text(x - 20, 70, "RegWrite: every class that writes rd")
    c.add("OR Gate", (x, 160), {"inputs": 3}, {"out": "rw_a", "in1": "IsR", "in2": "IsI", "in3": "IsLoad"})
    c.add("OR Gate", (x, 260), {"inputs": 3}, {"out": "rw_b", "in1": "IsLui", "in2": "IsAuipc", "in3": "IsJAL"})
    c.add("OR Gate", (x + 360, 210), {"inputs": 3}, {"in1": "rw_a", "in2": "rw_b", "in3": "IsJALR", "out": "RegWrite"})
    c.text(x - 20, 330, "ALUSrc = 1: ALU operand B is the immediate")
    c.add("OR Gate", (x, 420), {"inputs": 3}, {"out": "as_a", "in1": "IsI", "in2": "IsLoad", "in3": "IsStore"})
    c.add("OR Gate", (x, 520), {"inputs": 3}, {"out": "as_b", "in1": "IsLui", "in2": "IsAuipc", "in3": "IsJALR"})
    c.add("OR Gate", (x + 360, 470), {"inputs": 2}, {"in1": "as_a", "in2": "as_b", "out": "ALUSrc"})
    # ALUOp bus: bit0 = I | Branch ; bit1 = R | I
    c.add("OR Gate", (x, 700), {}, {"out": "ALUOp0", "in1": "IsI", "in2": "IsBranch"})
    c.add("OR Gate", (x, 780), {}, {"out": "ALUOp1", "in1": "IsR", "in2": "IsI"})
    c.add("Splitter", (x + 360, 740), splitter(2, 2, {0: 0, 1: 1}, "west"), {"bus": "ALUOp", "b0": "ALUOp0", "b1": "ALUOp1"})
    c.text(x - 20, 640, "ALUOp: 00 add (load/store/LUI/AUIPC/jumps)  01 sub (branch)  10 R-type  11 I-type")
    # ImmSel bus: bit0 = Store|LUI|AUIPC ; bit1 = Branch|LUI|AUIPC ; bit2 = JAL
    c.add("OR Gate", (x, 960), {"inputs": 3}, {"out": "ImmSel0", "in1": "IsStore", "in2": "IsLui", "in3": "IsAuipc"})
    c.add("OR Gate", (x, 1060), {"inputs": 3}, {"out": "ImmSel1", "in1": "IsBranch", "in2": "IsLui", "in3": "IsAuipc"})
    c.add("Splitter", (x + 360, 1020), splitter(3, 3, {0: 0, 1: 1, 2: 2}, "west"),
          {"bus": "ImmSel", "b0": "ImmSel0", "b1": "ImmSel1", "b2": "IsJAL"})
    c.text(x - 20, 900, "ImmSel: 000 I   001 S (store)   010 B (branch)   011 U (LUI, AUIPC)   100 J (JAL)")
    # ASel bus: bit0 = AUIPC (PC), bit1 = LUI (zero)
    c.add("Splitter", (x + 360, 1260), splitter(2, 2, {0: 0, 1: 1}, "west"),
          {"bus": "ASel", "b0": "IsAuipc", "b1": "IsLui"})
    c.text(x - 20, 1200, "ASel (ALU operand A): 00 rs1   01 PC (AUIPC)   10 zero (LUI)")
    # WBSel bus: bit0 = Load ; bit1 = JAL | JALR
    c.add("OR Gate", (x, 1400), {}, {"out": "WBSel1", "in1": "IsJAL", "in2": "IsJALR"})
    c.add("Splitter", (x + 360, 1420), splitter(2, 2, {0: 0, 1: 1}, "west"),
          {"bus": "WBSel", "b0": "IsLoad", "b1": "WBSel1"})
    c.text(x - 20, 1340, "WBSel (value written to rd): 00 ALU result   01 memory   10 PC + 4 (JAL, JALR)")
    # outputs
    outs = [("RegWrite", 1, "RegWrite"), ("ALUSrc", 1, "ALUSrc"), ("MemWrite", 1, "IsStore"), ("MemRead", 1, "IsLoad"),
            ("IsBranch", 1, "IsBranch"), ("ALUOp", 2, "ALUOp"), ("ImmSel", 3, "ImmSel"), ("ASel", 2, "ASel"),
            ("WBSel", 2, "WBSel"), ("IsJAL", 1, "IsJAL"), ("IsJALR", 1, "IsJALR")]
    for i, (lab, w, net) in enumerate(outs):
        # pin net can differ from its label: the label is the pin name, the net is where it connects
        c.add("Pin", (1700, 120 + 40 * i), {"appearance": "classic", "facing": "west", "label": lab, "type": "output",
                                            **({"width": w} if w > 1 else {})}, {"p": net})
    c.install()
    return c


# ------------------------------------------------------------------------------------------------
def branch_unit(proj):
    c = Circ(proj, "BranchUnit", spread=(1.2, 1.1))
    c.title(520, 30, "BranchUnit")
    c.text(520, 50, "Decides whether a conditional branch is taken: funct3 picks the comparison, IsBranch enables it.")
    c.pin_in("rs1_data", 32, (120, 140), radix=16)
    c.pin_in("rs2_data", 32, (120, 180), radix=16)
    c.pin_in("IsBranch", 1, (120, 220))
    c.pin_in("funct3", 3, (120, 260))
    c.add("Comparator", (750, 160), {"width": 32, "mode": "unsigned"}, {"a": "rs1_data", "b": "rs2_data", "eq": "eq", "lt": "ltu"})
    c.add("Comparator", (750, 300), {"width": 32}, {"a": "rs1_data", "b": "rs2_data", "lt": "lts"})
    c.text(750, 105, "unsigned compare")
    c.text(750, 245, "signed compare")
    c.add("NOT Gate", (1000, 160), {}, {"in": "eq", "out": "ne"})
    c.add("NOT Gate", (1000, 300), {}, {"in": "lts", "out": "ges"})
    c.add("NOT Gate", (1000, 220), {}, {"in": "ltu", "out": "geu"})
    c.add("Constant", (1000, 420), {"width": 1, "value": "0x0"}, {"out": "zero"})
    # funct3: 000 beq, 001 bne, 100 blt, 101 bge, 110 bltu, 111 bgeu
    c.add("Multiplexer", (1700, 280), {"select": 3, "width": 1},
          {"d0": "eq", "d1": "ne", "d2": "zero", "d3": "zero", "d4": "lts", "d5": "ges", "d6": "ltu", "d7": "geu",
           "sel": "funct3", "out": "cond"})
    c.text(1700, 140, "funct3: 000 beq  001 bne  100 blt  101 bge  110 bltu  111 bgeu")
    c.add("AND Gate", (1950, 280), {}, {"in1": "IsBranch", "in2": "cond", "out": "branch_taken"})
    c.pin_out("branch_taken", 1, (2200, 280))
    c.install()
    return c


# ------------------------------------------------------------------------------------------------
def load_extract(proj):
    c = Circ(proj, "LoadExtract", spread=(1.3, 1.2))
    c.title(700, 30, "LoadExtract")
    c.text(700, 50, "Picks the loaded byte / halfword out of the 32-bit word and extends it: lb lh lw lbu lhu.")
    c.pin_in("word", 32, (120, 160), radix=16)
    c.pin_in("boff", 2, (120, 220))
    c.pin_in("funct3", 3, (120, 280))
    c.add("Splitter", (500, 200), sp_even(4, 32), {"bus": "word", "b0": "by0", "b1": "by1", "b2": "by2", "b3": "by3"})
    c.add("Splitter", (500, 460), sp_even(2, 32), {"bus": "word", "b0": "hw0", "b1": "hw1"})
    c.add("Splitter", (500, 640), splitter(2, 2, {0: 0, 1: 1}), {"bus": "boff", "b1": "boff1"})
    c.add("Multiplexer", (1000, 220), {"select": 2, "width": 8}, {"d0": "by0", "d1": "by1", "d2": "by2", "d3": "by3", "sel": "boff", "out": "ldbyte"})
    c.add("Multiplexer", (1000, 480), {"select": 1, "width": 16}, {"d0": "hw0", "d1": "hw1", "sel": "boff1", "out": "ldhalf"})
    c.text(1000, 150, "byte selected by Address[1:0]")
    c.text(1000, 410, "halfword selected by Address[1]")
    c.add("Bit Extender", (1400, 200), {"in_width": 8, "out_width": 32, "type": "sign"}, {"in": "ldbyte", "out": "lb"})
    c.add("Bit Extender", (1400, 300), {"in_width": 8, "out_width": 32, "type": "zero"}, {"in": "ldbyte", "out": "lbu"})
    c.add("Bit Extender", (1400, 480), {"in_width": 16, "out_width": 32, "type": "sign"}, {"in": "ldhalf", "out": "lh"})
    c.add("Bit Extender", (1400, 580), {"in_width": 16, "out_width": 32, "type": "zero"}, {"in": "ldhalf", "out": "lhu"})
    c.add("Multiplexer", (1900, 420), {"select": 3, "width": 32},
          {"d0": "lb", "d1": "lh", "d2": "word", "d3": "word", "d4": "lbu", "d5": "lhu", "d6": "word", "d7": "word",
           "sel": "funct3", "out": "read_data"})
    c.text(1900, 250, "funct3: 000 lb  001 lh  010 lw  100 lbu  101 lhu")
    c.pin_out("read_data", 32, (2300, 420), radix=16)
    c.install()
    return c


def store_merge(proj):
    c = Circ(proj, "StoreMerge", spread=(1.3, 1.2))
    c.title(900, 30, "StoreMerge")
    c.text(900, 50, "A store writes a whole RAM word, so keep the old bytes that are not written: sb, sh, sw.")
    c.pin_in("old_word", 32, (120, 160), radix=16)
    c.pin_in("write_data", 32, (120, 220), radix=16)
    c.pin_in("funct3", 3, (120, 280))
    c.pin_in("boff", 2, (120, 340))
    c.add("Splitter", (500, 200), sp_even(4, 32), {"bus": "old_word", "b0": "ob0", "b1": "ob1", "b2": "ob2", "b3": "ob3"})
    c.add("Splitter", (500, 460), sp_even(4, 32), {"bus": "write_data", "b0": "wd0", "b1": "wd1", "b2": "wd2", "b3": "wd3"})
    c.add("Splitter", (500, 700), splitter(2, 3, {0: 0, 1: 0, 2: 1}), {"bus": "funct3", "b0": "size"})
    c.text(500, 800, "size = funct3[1:0]: 00 byte  01 half  10 word")
    # which byte of write_data lands in each lane (lane 0 always takes wd0)
    c.add("Multiplexer", (1000, 200), {"select": 2, "width": 8}, {"d0": "wd0", "d1": "wd1", "d2": "wd1", "d3": "wd1", "sel": "size", "out": "src1"})
    c.add("Multiplexer", (1000, 400), {"select": 2, "width": 8}, {"d0": "wd0", "d1": "wd0", "d2": "wd2", "d3": "wd2", "sel": "size", "out": "src2"})
    c.add("Multiplexer", (1000, 600), {"select": 2, "width": 8}, {"d0": "wd0", "d1": "wd1", "d2": "wd3", "d3": "wd3", "sel": "size", "out": "src3"})
    c.text(1000, 140, "source byte for lane 1 / 2 / 3")
    # byte enables: row = {size, boff}
    c.add("Splitter", (1000, 880), splitter(2, 4, {0: 0, 1: 0, 2: 1, 3: 1}, "west"), {"bus": "enaddr", "b0": "boff", "b1": "size"})
    c.add("ROM", (1400, 840), {"addrWidth": 4, "dataWidth": 4, "contents": BYTE_ENABLES, "appearance": "classic"},
          {"addr": "enaddr", "dout": "en"})
    c.text(1400, 800, "byte enables: row = {size, Address[1:0]}")
    c.text(1400, 1010, "byte 0001 0010 0100 1000 | half 0011 0011 1100 1100 | word 1111")
    c.add("Splitter", (1900, 880), sp_even(4, 4), {"bus": "en", "b0": "en0", "b1": "en1", "b2": "en2", "b3": "en3"})
    for i, (old, src) in enumerate((("ob0", "wd0"), ("ob1", "src1"), ("ob2", "src2"), ("ob3", "src3"))):
        c.add("Multiplexer", (2300, 220 + 220 * i), {"select": 1, "width": 8}, {"d0": old, "d1": src, "sel": f"en{i}", "out": f"nb{i}"})
    c.text(2300, 130, "lane i = enable ? new byte : old byte")
    c.add("Splitter", (2800, 560), sp_even(4, 32, "west"), {"bus": "new_word", "b0": "nb0", "b1": "nb1", "b2": "nb2", "b3": "nb3"})
    c.pin_out("new_word", 32, (3200, 560), radix=16)
    c.install()
    return c


def memory(proj):
    c = Circ(proj, "Memory", spread=(1.2, 1.2))
    c.title(900, 30, "Memory")
    c.text(900, 50, "Data RAM 256 x 32 with asynchronous read.  Loads: lb lh lw lbu lhu.  Stores: sb sh sw (read-modify-write of one word).")
    c.pin_in("Address", 32, (120, 160), radix=16)
    c.pin_in("write_data", 32, (120, 220), radix=16)
    c.pin_in("MemWrite", 1, (120, 280))
    c.pin_in("CLK", 1, (120, 340))
    c.pin_in("funct3", 3, (120, 400))
    c.add("Splitter", (500, 200), splitter(3, 32, {**{0: 0, 1: 0}, **{k: 1 for k in range(2, 10)}, **{k: 2 for k in range(10, 32)}}),
          {"bus": "Address", "b0": "boff", "b1": "widx"})
    c.text(500, 90, "Address[1:0] = byte in the word, Address[9:2] = word index")
    c.add("RAM", (1100, 300), {"addrWidth": 8, "dataWidth": 32, "enables": "line", "asyncread": "true", "appearance": "classic"},
          {"addr": "widx", "dout": "word", "din": "wnew", "we": "MemWrite", "clk": "CLK"})
    c.text(1100, 260, "RAM: writes on the clock edge when MemWrite = 1")
    c.add("StoreMerge", (1900, 700), None, {"old_word": "word", "write_data": "write_data", "funct3": "funct3", "boff": "boff",
                                             "new_word": "wnew"})
    c.text(1700, 650, "StoreMerge: new word to write")
    c.add("LoadExtract", (1900, 1100), None, {"word": "word", "boff": "boff", "funct3": "funct3", "read_data": "read_data"})
    c.text(1700, 1050, "LoadExtract: value delivered to the CPU")
    c.pin_out("read_data", 32, (2600, 1100), radix=16)
    c.install()
    return c


def forwarding_unit(proj):
    c = Circ(proj, "ForwardingUnit", spread=(1.5, 1.3))
    c.title(600, 30, "ForwardingUnit")
    c.text(600, 50, "Pipeline data hazards: take an operand of the EX stage from a later stage instead of the register file.")
    c.pin_in("rs1_ex", 5, (120, 140))
    c.pin_in("rs2_ex", 5, (120, 180))
    c.pin_in("rd_mem", 5, (120, 220))
    c.pin_in("RegWrite_mem", 1, (120, 260))
    c.pin_in("rd_wb", 5, (120, 300))
    c.pin_in("RegWrite_wb", 1, (120, 340))
    c.add("Constant", (400, 760), {"width": 5, "value": "0x0"}, {"out": "x0"})
    c.add("Comparator", (700, 160), {"width": 5, "mode": "unsigned"}, {"a": "rd_mem", "b": "x0", "eq": "mem_is_x0"})
    c.add("Comparator", (700, 300), {"width": 5, "mode": "unsigned"}, {"a": "rd_wb", "b": "x0", "eq": "wb_is_x0"})
    c.add("NOT Gate", (950, 160), {}, {"in": "mem_is_x0", "out": "mem_ok0"})
    c.add("NOT Gate", (950, 300), {}, {"in": "wb_is_x0", "out": "wb_ok0"})
    c.add("AND Gate", (1200, 160), {"inputs": 2}, {"in1": "RegWrite_mem", "in2": "mem_ok0", "out": "mem_valid"})
    c.add("AND Gate", (1200, 300), {"inputs": 2}, {"in1": "RegWrite_wb", "in2": "wb_ok0", "out": "wb_valid"})
    c.text(950, 120, "a stage can forward only if it writes a register other than x0")
    for tag, rs, y0 in (("A", "rs1_ex", 520), ("B", "rs2_ex", 940)):
        c.add("Comparator", (700, y0), {"width": 5, "mode": "unsigned"}, {"a": "rd_mem", "b": rs, "eq": f"mem_eq_{tag}"})
        c.add("Comparator", (700, y0 + 140), {"width": 5, "mode": "unsigned"}, {"a": "rd_wb", "b": rs, "eq": f"wb_eq_{tag}"})
        c.add("AND Gate", (1200, y0), {"inputs": 2}, {"in1": "mem_valid", "in2": f"mem_eq_{tag}", "out": f"from_mem_{tag}"})
        c.add("AND Gate", (1200, y0 + 140), {"inputs": 2}, {"in1": "wb_valid", "in2": f"wb_eq_{tag}", "out": f"wb_hit_{tag}"})
        c.add("NOT Gate", (1450, y0 + 140), {}, {"in": f"from_mem_{tag}", "out": f"not_mem_{tag}"})
        c.add("AND Gate", (1700, y0 + 140), {"inputs": 2}, {"in1": f"wb_hit_{tag}", "in2": f"not_mem_{tag}", "out": f"from_wb_{tag}"})
        c.add("Splitter", (1950, y0 + 80), splitter(2, 2, {0: 0, 1: 1}, "west"),
              {"bus": f"Forward{tag}", "b0": f"from_wb_{tag}", "b1": f"from_mem_{tag}"})
        c.pin_out(f"Forward{tag}", 2, (2300, 140 + (0 if tag == "A" else 40)))
    c.text(700, 480, "operand A (rs1): EX/MEM has priority over MEM/WB")
    c.text(700, 900, "operand B (rs2)")
    c.text(1700, 480, "Forward: 00 register file   01 from MEM/WB   10 from EX/MEM")
    c.install()
    return c


def hazard_unit(proj):
    c = Circ(proj, "HazardUnit", spread=(1.5, 1.3))
    c.title(600, 30, "HazardUnit")
    c.text(600, 50, "Load-use hazard: the instruction in ID needs a value that the load in EX has not read from memory yet -> stall 1 cycle.")
    c.pin_in("MemRead_ex", 1, (120, 140))
    c.pin_in("rd_ex", 5, (120, 180))
    c.pin_in("rs1_id", 5, (120, 220))
    c.pin_in("rs2_id", 5, (120, 260))
    c.add("Constant", (400, 560), {"width": 5, "value": "0x0"}, {"out": "x0"})
    c.add("Comparator", (700, 160), {"width": 5, "mode": "unsigned"}, {"a": "rd_ex", "b": "x0", "eq": "rd_is_x0"})
    c.add("NOT Gate", (950, 160), {}, {"in": "rd_is_x0", "out": "rd_ok"})
    c.add("Comparator", (700, 300), {"width": 5, "mode": "unsigned"}, {"a": "rd_ex", "b": "rs1_id", "eq": "hit1"})
    c.add("Comparator", (700, 440), {"width": 5, "mode": "unsigned"}, {"a": "rd_ex", "b": "rs2_id", "eq": "hit2"})
    c.add("OR Gate", (1200, 370), {}, {"in1": "hit1", "in2": "hit2", "out": "uses"})
    c.add("AND Gate", (1450, 300), {"inputs": 3}, {"in1": "MemRead_ex", "in2": "rd_ok", "in3": "uses", "out": "stall"})
    c.text(1200, 330, "rd of the load matches a source of the next instruction")
    c.text(1450, 260, "stall = load in EX AND rd != x0 AND (rd == rs1 OR rd == rs2)")
    c.pin_out("stall", 1, (1750, 300))
    c.install()
    return c
