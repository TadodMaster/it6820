"""5-stage pipeline CPU (circuit `Pipeline`)."""
from circgen import Circ
from blocks import splitter
from cpus import DEMO, sub

# control word, LSB first: (signal, width)
CTRL_ID = [("RegWrite", 1), ("ALUSrc", 1), ("MemWrite", 1), ("MemRead", 1), ("IsBranch", 1),
           ("ALUOp", 2), ("ASel", 2), ("WBSel", 2), ("IsJAL", 1), ("IsJALR", 1)]
CTRL_MEM = [("RegWrite", 1), ("MemWrite", 1), ("MemRead", 1), ("WBSel", 2)]
CTRL_WB = [("RegWrite", 1), ("WBSel", 2)]


def pack_attrs(parts, facing):
    """Splitter attributes that pack / unpack `parts` ((name, width), LSB first) into one bus."""
    assign, bit = {}, 0
    for i, (_, w) in enumerate(parts):
        for _ in range(w):
            assign[bit] = i
            bit += 1
    return splitter(len(parts), bit, assign, facing), bit


def pins_of(bus, parts, suffix):
    d = {"bus": bus}
    d.update({f"b{i}": f"{n}_{suffix}" for i, (n, _) in enumerate(parts)})
    return d


def pipeline(proj, rom_contents=DEMO, spread=(1.0, 1.0)):
    c = Circ(proj, "Pipeline", stub=30, spread=spread)
    X = {"IF": 800, "IFID": 1750, "ID": 2450, "IDEX": 3400, "EX": 4100, "EXMEM": 6150, "MEM": 6850,
         "MEMWB": 7550, "WB": 8200}
    c.title(3900, 30, "RV32I 5-stage pipeline - top level")
    c.text(3900, 52, "IF > ID > EX > MEM > WB with pipeline registers between the stages.  "
                     "Forwarding (EX), load-use stall (ID) and branch / jump flush (EX).")
    c.text(3900, 70, "Tunnels with the same name are the same wire.  Suffix _id _ex _mem _wb = the stage a value belongs to.")
    for k, t in (("IF", "IF - Instruction Fetch"), ("ID", "ID - Decode / Register Read"), ("EX", "EX - Execute"),
                 ("MEM", "MEM - Data Memory"), ("WB", "WB - Write Back")):
        c.title(X[k] + 150, 120, t)
    for k, t in (("IFID", "IF/ID"), ("IDEX", "ID/EX"), ("EXMEM", "EX/MEM"), ("MEMWB", "MEM/WB")):
        c.title(X[k] + 100, 160, t + " registers")

    def reg(col, y, label, width, d, q, we="one"):
        c.add("Register", (X[col], y), {"appearance": "logisim_evolution", "label": label, "width": width,
                                       "labelvisible": "true", "labelfont": "Monospaced plain 11"},
              {"d": d, "q": q, "clk": "CLK", "we": we})

    def bank(col, y0, items, dy=170):
        y = y0
        for it in items:
            reg(col, y, *it)
            y += dy

    # ================================================================ IF
    c.add("Clock", (150, 300), {"appearance": "NewPins"}, {"out": "CLK"})
    c.text(120, 330, "Clock: Simulate > Tick")
    c.add("Pin", (150, 420), {"appearance": "classic", "label": "RESET"}, {"p": "RESET"})
    c.text(130, 450, "RESET = 1 holds PC at 0")
    c.add("Constant", (150, 540), {}, {"out": "one"})
    c.add("NOT Gate", (150, 640), {}, {"in": "CLK", "out": "CLK_n"})
    c.text(120, 690, "CLK_n: the register file writes on the falling edge,")
    c.text(120, 708, "so WB can write and ID can read in the same cycle")
    c.add("Register", (X["IF"], 330), {"appearance": "logisim_evolution", "label": "PC", "width": 32},
          {"q": "pc_if", "d": "next_pc", "clk": "CLK", "r": "RESET", "we": "run"})
    c.text(X["IF"] + 30, 310, "PC register (holds while stalled)")
    c.add("Splitter", (X["IF"] + 450, 360),
          splitter(3, 32, {**{0: 0, 1: 0}, **{k: 1 for k in range(2, 10)}, **{k: 2 for k in range(10, 32)}}),
          {"bus": "pc_if", "b1": "pc_word"})
    c.add("Constant", (X["IF"] + 100, 640), {"width": 32, "value": "0x4"}, {"out": "four"})
    c.add("Adder", (X["IF"] + 450, 640), {"width": 32}, {"a": "pc_if", "b": "four", "out": "pc_plus4_if"})
    c.text(X["IF"] + 420, 600, "PC + 4")
    c.add("ROM", (X["IF"] + 450, 820), {"addrWidth": 8, "dataWidth": 32, "contents": rom_contents, "appearance": "classic"},
          {"addr": "pc_word", "dout": "instr_if"})
    c.text(X["IF"] + 560, 800, "Instruction ROM 256 x 32")
    c.add("Multiplexer", (X["IF"] + 450, 1250), {"select": 1, "width": 32},
          {"d0": "pc_plus4_if", "d1": "target_ex", "sel": "pc_src_ex", "out": "next_pc"})
    c.text(X["IF"] + 250, 1180, "next PC: PC+4, or the branch / jump target from EX")
    c.add("Constant", (X["IF"] + 100, 1450), {"width": 32, "value": "0x0"}, {"out": "zero32"})
    c.add("Multiplexer", (X["IF"] + 450, 1450), {"select": 1, "width": 32},
          {"d0": "instr_if", "d1": "zero32", "sel": "pc_src_ex", "out": "instr_in"})
    c.text(X["IF"] + 250, 1380, "a taken branch / jump turns the fetched instruction into a bubble (0)")
    c.add("NOT Gate", (X["IF"] + 450, 1650), {}, {"in": "stall", "out": "run"})
    c.text(X["IF"] + 250, 1700, "run = not stall: PC and IF/ID only advance when run = 1")

    # ================================================================ IF/ID
    bank("IFID", 330, [("pc_id", 32, "pc_if", "pc_id", "run"), ("instr_id", 32, "instr_in", "instr_id", "run")])

    # ================================================================ ID
    i = X["ID"] + 220
    sub(c, "InstructionDecode", (i, 300), {"Instruction": "instr_id", "funct7": "funct7_id", "rs2": "rs2_id",
                                           "rs1": "rs1_id", "funct3": "funct3_id", "rd": "rd_id", "opcode": "opcode_id"})
    c.text(X["ID"] + 60, 270, "InstructionDecode")
    sub(c, "MainControl", (i, 680), {"opcode": "opcode_id", "RegWrite": "RegWrite_id", "ALUSrc": "ALUSrc_id",
                                      "MemWrite": "MemWrite_id", "MemRead": "MemRead_id", "IsBranch": "IsBranch_id",
                                      "ALUOp": "ALUOp_id", "ImmSel": "ImmSel_id", "ASel": "ASel_id",
                                      "WBSel": "WBSel_id", "IsJAL": "IsJAL_id", "IsJALR": "IsJALR_id"})
    c.text(X["ID"] + 60, 650, "MainControl")
    sub(c, "ImmGen", (i, 1080), {"Instruction": "instr_id", "ImmSel": "ImmSel_id", "Imm": "imm_id"})
    c.text(X["ID"] + 60, 1050, "ImmGen")
    sub(c, "RegisterFile", (i, 1380), {"write_data": "wb_data", "CLK": "CLK_n", "write": "RegWrite_wb", "rd": "rd_wb",
                                       "rs1": "rs1_id", "rs2": "rs2_id", "rs1_data": "rs1_data_id", "rs2_data": "rs2_data_id"})
    c.text(X["ID"] + 60, 1350, "RegisterFile (writes on CLK_n)")
    sub(c, "HazardUnit", (i, 1750), {"MemRead_ex": "MemRead_ex", "rd_ex": "rd_ex", "rs1_id": "rs1_id",
                                      "rs2_id": "rs2_id", "stall": "stall"})
    c.text(X["ID"] + 60, 1720, "HazardUnit: load-use stall")
    sp, nb = pack_attrs(CTRL_ID, "west")
    c.add("Splitter", (X["ID"] + 200, 1950), sp, pins_of("ctrl_id", CTRL_ID, "id"))
    c.text(X["ID"] + 20, 1900, "control word (13 bits)")
    c.add("OR Gate", (X["ID"] + 200, 2500), {}, {"in1": "stall", "in2": "pc_src_ex", "out": "bubble"})
    c.add("Constant", (X["ID"] - 250, 2800), {"width": nb, "value": "0x0"}, {"out": "zero_ctrl"})
    c.add("Multiplexer", (X["ID"] + 200, 2700), {"select": 1, "width": nb},
          {"d0": "ctrl_id", "d1": "zero_ctrl", "sel": "bubble", "out": "ctrl_in"})
    c.text(X["ID"] + 20, 2620, "bubble = stall OR flush: the control word becomes 0 (a NOP)")

    # ================================================================ ID/EX
    bank("IDEX", 330, [("pc_ex", 32, "pc_id", "pc_ex"), ("rs1_data_ex", 32, "rs1_data_id", "rs1_data_ex"),
                       ("rs2_data_ex", 32, "rs2_data_id", "rs2_data_ex"), ("imm_ex", 32, "imm_id", "imm_ex"),
                       ("rs1_ex", 5, "rs1_id", "rs1_ex"), ("rs2_ex", 5, "rs2_id", "rs2_ex"),
                       ("rd_ex", 5, "rd_id", "rd_ex"), ("funct3_ex", 3, "funct3_id", "funct3_ex"),
                       ("funct7_ex", 7, "funct7_id", "funct7_ex"), ("ctrl_ex", nb, "ctrl_in", "ctrl_ex")])

    # ================================================================ EX
    ex = X["EX"]
    sp_ex, _ = pack_attrs(CTRL_ID, "east")
    c.add("Splitter", (ex + 30, 640), sp_ex, pins_of("ctrl_ex", CTRL_ID, "ex"))
    c.text(ex - 20, 700, "control word of the instruction in EX")
    sub(c, "ForwardingUnit", (ex + 700, 380), {"rs1_ex": "rs1_ex", "rs2_ex": "rs2_ex", "rd_mem": "rd_mem",
                                               "RegWrite_mem": "RegWrite_mem", "rd_wb": "rd_wb",
                                               "RegWrite_wb": "RegWrite_wb", "ForwardA": "ForwardA", "ForwardB": "ForwardB"})
    c.text(ex + 580, 350, "ForwardingUnit")
    c.add("Multiplexer", (ex + 30, 960), {"select": 1, "width": 32},
          {"d0": "alu_result_mem", "d1": "pc_plus4_mem", "sel": "WBSel1_mem", "out": "fwd_mem_val"})
    c.text(ex - 20, 900, "value in EX/MEM that can be forwarded (ALU result, or PC+4 of JAL/JALR)")
    c.add("Multiplexer", (ex + 30, 1240), {"select": 2, "width": 32},
          {"d0": "rs1_data_ex", "d1": "wb_data", "d2": "fwd_mem_val", "d3": "rs1_data_ex", "sel": "ForwardA", "out": "opA"})
    c.text(ex - 20, 1160, "operand A: 00 register  01 MEM/WB  10 EX/MEM")
    c.add("Multiplexer", (ex + 30, 1560), {"select": 2, "width": 32},
          {"d0": "rs2_data_ex", "d1": "wb_data", "d2": "fwd_mem_val", "d3": "rs2_data_ex", "sel": "ForwardB", "out": "opB"})
    c.text(ex - 20, 1480, "operand B / store data: same choices")
    c.add("Constant", (ex + 30, 1760), {"width": 32, "value": "0x0"}, {"out": "zero32"})
    c.add("Multiplexer", (ex + 400, 1260), {"select": 2, "width": 32},
          {"d0": "opA", "d1": "pc_ex", "d2": "zero32", "d3": "zero32", "sel": "ASel_ex", "out": "alu_a"})
    c.text(ex + 330, 1180, "ALU A: rs1 / PC (auipc) / 0 (lui)")
    c.add("Multiplexer", (ex + 400, 1560), {"select": 1, "width": 32},
          {"d0": "opB", "d1": "imm_ex", "sel": "ALUSrc_ex", "out": "alu_b"})
    c.text(ex + 330, 1480, "ALU B: rs2 / imm")
    sub(c, "ALUControl", (ex + 1130, 960), {"funct7": "funct7_ex", "ALUOp": "ALUOp_ex", "funct3": "funct3_ex", "ALUCtrl": "ALUCtrl"})
    c.text(ex + 1000, 930, "ALUControl")
    sub(c, "ALU", (ex + 1130, 1240), {"rs1_data": "alu_a", "rs2_data": "alu_b", "ALU_Ctrl": "ALUCtrl", "result": "alu_result_ex"})
    c.text(ex + 1000, 1210, "ALU")
    sub(c, "BranchUnit", (ex + 1130, 1520), {"rs1_data": "opA", "rs2_data": "opB", "IsBranch": "IsBranch_ex",
                                            "funct3": "funct3_ex", "branch_taken": "branch_taken"})
    c.text(ex + 1000, 1490, "BranchUnit")
    c.add("Adder", (ex + 1700, 340), {"width": 32}, {"a": "pc_ex", "b": "imm_ex", "out": "pc_target"})
    c.text(ex + 1460, 290, "branch / JAL target = PC + imm")
    c.add("Constant", (ex + 1130, 540), {"width": 32, "value": "0xfffffffe"}, {"out": "mask_even"})
    c.add("AND Gate", (ex + 1700, 540), {"width": 32}, {"in1": "alu_result_ex", "in2": "mask_even", "out": "jalr_target"})
    c.text(ex + 1460, 490, "JALR target = (rs1 + imm), bit 0 cleared")
    c.add("Multiplexer", (ex + 1700, 760), {"select": 1, "width": 32},
          {"d0": "pc_target", "d1": "jalr_target", "sel": "IsJALR_ex", "out": "target_ex"})
    c.add("OR Gate", (ex + 1700, 960), {"inputs": 3}, {"in1": "branch_taken", "in2": "IsJAL_ex", "in3": "IsJALR_ex", "out": "pc_src_ex"})
    c.text(ex + 1460, 900, "pc_src_ex = redirect the PC (taken branch, JAL, JALR) and flush IF/ID + ID/EX")
    c.add("Constant", (ex + 1700, 1160), {"width": 32, "value": "0x4"}, {"out": "four"})
    c.add("Adder", (ex + 1700, 1300), {"width": 32}, {"a": "pc_ex", "b": "four", "out": "pc_plus4_ex"})
    c.text(ex + 1460, 1250, "link address PC+4")

    # ================================================================ EX/MEM
    sp_cm, nbm = pack_attrs(CTRL_MEM, "west")
    c.add("Splitter", (X["EXMEM"] - 120, 2250), sp_cm, pins_of("ctrl_mem_in", CTRL_MEM, "ex"))
    c.text(X["EXMEM"] - 300, 2000, "pack RegWrite, MemWrite, MemRead, WBSel")
    bank("EXMEM", 330, [("alu_result_mem", 32, "alu_result_ex", "alu_result_mem"),
                        ("store_data_mem", 32, "opB", "store_data_mem"),
                        ("pc_plus4_mem", 32, "pc_plus4_ex", "pc_plus4_mem"),
                        ("rd_mem", 5, "rd_ex", "rd_mem"), ("funct3_mem", 3, "funct3_ex", "funct3_mem"),
                        ("ctrl_mem", nbm, "ctrl_mem_in", "ctrl_mem")])

    # ================================================================ MEM
    me = X["MEM"]
    sp_um, _ = pack_attrs(CTRL_MEM, "east")
    c.add("Splitter", (me + 30, 500), sp_um, pins_of("ctrl_mem", CTRL_MEM, "mem"))
    c.text(me - 20, 560, "control word of the instruction in MEM")
    c.add("Splitter", (me + 30, 700), splitter(2, 2, {0: 0, 1: 1}, "east"), {"bus": "WBSel_mem", "b1": "WBSel1_mem"})
    c.text(me - 20, 770, "WBSel bit 1: result is PC+4")
    sub(c, "Memory", (me + 500, 800), {"Address": "alu_result_mem", "write_data": "store_data_mem",
                                       "MemWrite": "MemWrite_mem", "CLK": "CLK", "funct3": "funct3_mem",
                                       "read_data": "mem_rdata_mem"})
    c.text(me + 370, 770, "Memory")

    # ================================================================ MEM/WB
    sp_cw, nbw = pack_attrs(CTRL_WB, "west")
    c.add("Splitter", (X["MEMWB"] - 120, 1450), sp_cw, pins_of("ctrl_wb_in", CTRL_WB, "mem"))
    c.text(X["MEMWB"] - 300, 1400, "pack RegWrite, WBSel")
    bank("MEMWB", 330, [("alu_result_wb", 32, "alu_result_mem", "alu_result_wb"),
                        ("mem_rdata_wb", 32, "mem_rdata_mem", "mem_rdata_wb"),
                        ("pc_plus4_wb", 32, "pc_plus4_mem", "pc_plus4_wb"),
                        ("rd_wb", 5, "rd_mem", "rd_wb"), ("ctrl_wb", nbw, "ctrl_wb_in", "ctrl_wb")])

    # ================================================================ WB
    wb = X["WB"]
    sp_uw, _ = pack_attrs(CTRL_WB, "east")
    c.add("Splitter", (wb + 30, 400), sp_uw, pins_of("ctrl_wb", CTRL_WB, "wb"))
    c.text(wb - 20, 290, "control word of the instruction in WB")
    c.add("Constant", (wb + 30, 640), {"width": 32, "value": "0x0"}, {"out": "zero32"})
    c.add("Multiplexer", (wb + 300, 520), {"select": 2, "width": 32},
          {"d0": "alu_result_wb", "d1": "mem_rdata_wb", "d2": "pc_plus4_wb", "d3": "zero32", "sel": "WBSel_wb", "out": "wb_data"})
    c.text(wb + 150, 440, "WBSel: 00 ALU  01 memory  10 PC+4")
    c.text(wb + 150, 700, "wb_data goes to the register file (ID) and is also forwarded to EX")
    c.add("Probe", (wb + 700, 520), {"appearance": "NewPins", "radix": 16, "label": "wb_data"}, {"p": "wb_data"})
    c.install()
    return c
