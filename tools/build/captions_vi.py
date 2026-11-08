"""Vietnamese captions placed right next to the components of every circuit.

Each caption says what the component does *here* and why it is built this way (2-3 short lines).

  lines(circuit, name, attrs, pins) -> list of caption lines, or None when the component needs no caption
    circuit - name of the circuit that contains the component
    name    - Logisim component name ("Splitter", "Register", "Multiplexer", a sub-circuit name, ...)
    attrs   - dict of the component's attributes (strings; defaults are not stored in the file)
    pins    - {pin name: net name} from the netlist generator (None for the hand-drawn circuits)
"""

SKIP = {"Tunnel", "Probe", "Pin", "Text"}
HAND = {"ALU", "InstructionDecode", "RegisterFile", "ImmGen", "ALUControl"}

# ---------------------------------------------------------------------------------------------------------------
# sub-circuit instances (what the block does, why it exists)
SUB = {
    "InstructionDecode": "InstructionDecode: cắt lệnh 32 bit thành các trường|Các trường nằm cố định nên chỉ cần đi dây",
    "MainControl": "MainControl: từ opcode sinh mọi tín hiệu điều khiển|Mỗi nhóm lệnh bật một tổ hợp tín hiệu riêng",
    "ImmGen": "ImmGen: dựng hằng số imm 32 bit từ lệnh|Hằng số kiểu I, S, B, U, J nằm ở chỗ khác nhau",
    "RegisterFile": "RegisterFile: 32 thanh ghi, đọc rs1, rs2, ghi rd|Mọi lệnh đọc/ghi toán hạng ở đây",
    "ALUControl": "ALUControl: đổi ALUOp + funct3/7 thành ALUCtrl|Tách bảng mã ALU khỏi MainControl cho gọn",
    "ALU": "ALU: tính kết quả theo mã ALUCtrl|Một khối chung cho cộng, logic, dịch, so sánh",
    "BranchUnit": "BranchUnit: quyết định branch có rẽ không|So rs1 với rs2 theo funct3 (beq, bne, blt...)",
    "Memory": "Memory: RAM dữ liệu, load/store byte, nửa từ, từ|Lệnh load/store là nơi duy nhất đụng RAM",
    "LoadExtract": "LoadExtract: lấy byte/nửa từ ra khỏi từ, mở rộng|RAM đọc nguyên từ 32 bit",
    "StoreMerge": "StoreMerge: ghép byte mới vào từ cũ|RAM chỉ ghi nguyên từ nên sb/sh phải đọc-sửa-ghi",
    "ForwardingUnit": "ForwardingUnit: chọn nguồn mới nhất cho toán hạng EX|Lệnh trước chưa kịp ghi vào thanh ghi",
    "HazardUnit": "HazardUnit: phát hiện load-use, phát tín hiệu stall|Dữ liệu load chỉ có ở cuối MEM",
}

# ---------------------------------------------------------------------------------------------------------------
CLS = {  # net -> (opcode, nhóm lệnh)
    "IsR": ("0x33", "kiểu R (add, sub, and, or, sll...)"),
    "IsI": ("0x13", "kiểu I-ALU (addi, andi, slli...)"),
    "IsLoad": ("0x03", "load (lb, lh, lw, lbu, lhu)"),
    "IsStore": ("0x23", "store (sb, sh, sw)"),
    "IsBranch": ("0x63", "branch (beq, bne, blt, bge...)"),
    "IsLui": ("0x37", "lui (nạp hằng số vào 20 bit cao)"),
    "IsAuipc": ("0x17", "auipc (PC + hằng số 20 bit cao)"),
    "IsJAL": ("0x6f", "jal (nhảy và lưu địa chỉ trả về)"),
    "IsJALR": ("0x67", "jalr (nhảy theo thanh ghi)"),
}
OPC = {v[0]: (k, v[1]) for k, v in CLS.items()}

SPECIFIC = {
    # ---------------- MainControl
    ("MainControl", "rw_a"): "OR: IsR hoặc IsI hoặc IsLoad|Nửa đầu của điều kiện RegWrite|Cổng OR tối đa 3 ngõ, nên chia hai nửa",
    ("MainControl", "rw_b"): "OR: IsLui hoặc IsAuipc hoặc IsJAL|Nửa sau của điều kiện RegWrite|Cổng OR tối đa 3 ngõ, nên chia hai nửa",
    ("MainControl", "RegWrite"): "RegWrite = nửa đầu hoặc nửa sau hoặc IsJALR|=1: lệnh phải ghi kết quả vào rd|Store và branch không ghi thanh ghi",
    ("MainControl", "as_a"): "OR: IsI hoặc IsLoad hoặc IsStore|Nửa đầu của điều kiện ALUSrc|Các lệnh này dùng hằng số imm",
    ("MainControl", "as_b"): "OR: IsLui hoặc IsAuipc hoặc IsJALR|Nửa sau của điều kiện ALUSrc|Các lệnh này cũng dùng hằng số imm",
    ("MainControl", "ALUSrc"): "ALUSrc = as_a hoặc as_b|=1: toán hạng B của ALU là hằng số imm|R và branch dùng rs2, lệnh còn lại dùng imm",
    ("MainControl", "ALUOp0"): "ALUOp bit 0 = IsI hoặc IsBranch|ALUOp: 00 cộng, 01 trừ, 10 kiểu R, 11 kiểu I|Branch cần phép trừ, kiểu I cần tra funct3",
    ("MainControl", "ALUOp1"): "ALUOp bit 1 = IsR hoặc IsI|=1: ALUControl phải tra bảng theo funct3/funct7|Các lệnh khác chỉ cần cộng hoặc trừ",
    ("MainControl", "ALUOp|ALUOp0"): "Ghép 2 bit thành bus ALUOp (2 bit)|ALUControl nhận một bus duy nhất",
    ("MainControl", "ImmSel0"): "ImmSel bit 0 = IsStore hoặc IsLui hoặc IsAuipc|ImmSel: 000 I, 001 S, 010 B, 011 U, 100 J|Bit 0 = 1 cho kiểu S và U",
    ("MainControl", "ImmSel1"): "ImmSel bit 1 = IsBranch hoặc IsLui hoặc IsAuipc|Bit 1 = 1 cho kiểu B và U",
    ("MainControl", "ImmSel|ImmSel0"): "Ghép ImmSel0, ImmSel1, IsJAL thành bus 3 bit|Kiểu J (jal) = 100 nên bit 2 chính là IsJAL",
    ("MainControl", "ASel|IsAuipc"): "Ghép IsAuipc, IsLui thành bus ASel|ASel: 00 rs1, 01 PC (auipc), 10 số 0 (lui)|Auipc cần PC, lui cần 0",
    ("MainControl", "WBSel1"): "WBSel bit 1 = IsJAL hoặc IsJALR|=1: ghi PC+4 (địa chỉ trả về) vào rd|Jal/jalr lưu địa chỉ quay lại",
    ("MainControl", "WBSel|IsLoad"): "Ghép IsLoad, WBSel1 thành bus WBSel|WBSel: 00 ALU, 01 RAM (load), 10 PC+4|Load lấy dữ liệu từ RAM",
    # ---------------- BranchUnit
    ("BranchUnit", "eq"): "So sánh không dấu: ra '=' và '<'|Beq/bne cần '=', bltu/bgeu cần '<' không dấu",
    ("BranchUnit", "lts"): "So sánh có dấu: ra '<' có dấu|Blt/bge coi số là có dấu (-1 nhỏ hơn 1)",
    ("BranchUnit", "ne"): "NOT: đảo '=' thành '!='|Bne = không bằng",
    ("BranchUnit", "ges"): "NOT: đảo '<' có dấu thành '>='|Bge = lớn hơn hoặc bằng",
    ("BranchUnit", "geu"): "NOT: đảo '<' không dấu thành '>='|Bgeu = lớn hơn hoặc bằng, không dấu",
    ("BranchUnit", "zero"): "Hằng số 0: điều kiện 'không bao giờ rẽ'|Funct3 = 010/011 không phải lệnh branch",
    ("BranchUnit", "cond"): "Mux 8:1: chọn điều kiện theo funct3|000 beq, 001 bne, 100 blt, 101 bge, 110 bltu, 111 bgeu|Funct3 cho biết lệnh branch nào",
    ("BranchUnit", "branch_taken"): "AND: IsBranch và điều kiện|=1: phải rẽ|Lệnh không phải branch không bao giờ rẽ",
    # ---------------- LoadExtract
    ("LoadExtract", "word|by0"): "Tách từ 32 bit thành 4 byte|Lb/lbu cần lấy riêng một byte",
    ("LoadExtract", "word|hw0"): "Tách từ 32 bit thành 2 nửa từ|Lh/lhu cần lấy riêng một nửa từ",
    ("LoadExtract", "boff|boff1"): "Lấy bit 1 của Address[1:0]|Nửa từ chọn bằng bit 1 của địa chỉ",
    ("LoadExtract", "ldbyte"): "Mux 4:1: chọn byte theo Address[1:0]|Byte nằm ở một trong 4 vị trí của từ",
    ("LoadExtract", "ldhalf"): "Mux 2:1: chọn nửa từ theo Address[1]|Nửa từ nằm ở 1 trong 2 vị trí của từ",
    ("LoadExtract", "lb"): "Mở rộng dấu byte thành 32 bit (lb)|Byte âm phải giữ giá trị âm (0x80 -> 0xFFFFFF80)",
    ("LoadExtract", "lbu"): "Mở rộng 0 byte thành 32 bit (lbu)|Lbu coi byte là số không dấu",
    ("LoadExtract", "lh"): "Mở rộng dấu nửa từ thành 32 bit (lh)|Giữ giá trị âm của số 16 bit",
    ("LoadExtract", "lhu"): "Mở rộng 0 nửa từ thành 32 bit (lhu)|Lhu coi nửa từ là số không dấu",
    ("LoadExtract", "read_data"): "Mux 8:1: chọn kết quả theo funct3|000 lb, 001 lh, 010 lw, 100 lbu, 101 lhu|Funct3 cho biết loại lệnh load",
    # ---------------- StoreMerge
    ("StoreMerge", "old_word|ob0"): "Tách từ cũ thành 4 byte|Byte không ghi phải giữ nguyên",
    ("StoreMerge", "write_data|wd0"): "Tách dữ liệu mới thành 4 byte|Mỗi làn có thể nhận một byte khác nhau",
    ("StoreMerge", "funct3|size"): "Lấy size = funct3[1:0]|00 byte, 01 nửa từ, 10 từ|Funct3 của store cho biết sb, sh, sw",
    ("StoreMerge", "src1"): "Mux: nguồn byte cho làn 1|sb lấy byte thấp wd0, sh/sw lấy wd1|Sb luôn lấy byte thấp của dữ liệu",
    ("StoreMerge", "src2"): "Mux: nguồn byte cho làn 2|sw lấy wd2, sb/sh lấy wd0|Làn 2 thuộc nửa từ cao",
    ("StoreMerge", "src3"): "Mux: nguồn byte cho làn 3|sw lấy wd3, sh lấy wd1, sb lấy wd0|Làn 3 thuộc nửa từ cao",
    ("StoreMerge", "enaddr|boff"): "Ghép {size, Address[1:0]} thành 4 bit|Đây là địa chỉ của ROM cho phép byte",
    ("StoreMerge", "en"): "ROM 16 x 4: tra ra 4 bit cho phép từng làn|1 2 4 8 = byte, 3 c = nửa từ, f = từ|Bảng 16 dòng viết bằng ROM gọn và dễ đọc",
    ("StoreMerge", "en|en0"): "Tách 4 bit cho phép thành từng làn|Mỗi mux làn cần một bit riêng",
    ("StoreMerge", "nb0"): "Làn 0: byte mới (en0=1) hay byte cũ (en0=0)|Chỉ làn được cho phép mới bị ghi đè",
    ("StoreMerge", "nb1"): "Làn 1: byte mới (en1=1) hay byte cũ (en1=0)|Chỉ làn được cho phép mới bị ghi đè",
    ("StoreMerge", "nb2"): "Làn 2: byte mới (en2=1) hay byte cũ (en2=0)|Chỉ làn được cho phép mới bị ghi đè",
    ("StoreMerge", "nb3"): "Làn 3: byte mới (en3=1) hay byte cũ (en3=0)|Chỉ làn được cho phép mới bị ghi đè",
    ("StoreMerge", "new_word|nb0"): "Ghép 4 làn thành từ mới 32 bit|RAM ghi nguyên từ, đây là từ sẽ được ghi",
    # ---------------- Memory
    ("Memory", "Address|boff"): "Tách địa chỉ: byte trong từ và chỉ số từ|Address[1:0] chọn byte, Address[9:2] chọn từ|RAM đánh địa chỉ theo từ",
    ("Memory", "word"): "RAM 256 x 32: đọc bất đồng bộ, ghi ở cạnh xung khi MemWrite = 1|Load cần dữ liệu ngay trong chu kỳ",
    # ---------------- ForwardingUnit
    ("ForwardingUnit", "x0"): "Hằng số 0 (số thanh ghi x0)|X0 luôn bằng 0, không cần forward",
    ("ForwardingUnit", "mem_is_x0"): "rd_mem có phải x0 không|Ghi vào x0 vô nghĩa nên không forward",
    ("ForwardingUnit", "wb_is_x0"): "rd_wb có phải x0 không|Ghi vào x0 vô nghĩa nên không forward",
    ("ForwardingUnit", "mem_ok0"): "NOT: rd_mem khác x0|Điều kiện hợp lệ để forward từ MEM",
    ("ForwardingUnit", "wb_ok0"): "NOT: rd_wb khác x0|Điều kiện hợp lệ để forward từ WB",
    ("ForwardingUnit", "mem_valid"): "AND: lệnh ở MEM có ghi thanh ghi và rd khác x0|Chỉ khi đó kết quả của nó đáng forward",
    ("ForwardingUnit", "wb_valid"): "AND: lệnh ở WB có ghi thanh ghi và rd khác x0|Chỉ khi đó kết quả của nó đáng forward",
    ("ForwardingUnit", "mem_eq_A"): "rd_mem có bằng rs1_ex không|Lệnh ở EX đang cần đúng thanh ghi MEM sắp ghi",
    ("ForwardingUnit", "wb_eq_A"): "rd_wb có bằng rs1_ex không|Lệnh ở EX đang cần đúng thanh ghi WB sắp ghi",
    ("ForwardingUnit", "from_mem_A"): "AND: forward toán hạng A từ EX/MEM|Lệnh ngay trước có kết quả mới nhất",
    ("ForwardingUnit", "wb_hit_A"): "AND: WB cũng khớp toán hạng A|Ứng viên forward từ MEM/WB",
    ("ForwardingUnit", "not_mem_A"): "NOT: EX/MEM không khớp toán hạng A|EX/MEM được ưu tiên hơn MEM/WB",
    ("ForwardingUnit", "from_wb_A"): "AND: forward toán hạng A từ MEM/WB|Chỉ khi EX/MEM không khớp (nó mới hơn)",
    ("ForwardingUnit", "ForwardA|from_wb_A"): "Ghép thành ForwardA: 10 EX/MEM, 01 MEM/WB, 00 thanh ghi|Mux ở EX nhận mã 2 bit",
    ("ForwardingUnit", "mem_eq_B"): "rd_mem có bằng rs2_ex không|Lệnh ở EX đang cần đúng thanh ghi MEM sắp ghi",
    ("ForwardingUnit", "wb_eq_B"): "rd_wb có bằng rs2_ex không|Lệnh ở EX đang cần đúng thanh ghi WB sắp ghi",
    ("ForwardingUnit", "from_mem_B"): "AND: forward toán hạng B từ EX/MEM|Lệnh ngay trước có kết quả mới nhất",
    ("ForwardingUnit", "wb_hit_B"): "AND: WB cũng khớp toán hạng B|Ứng viên forward từ MEM/WB",
    ("ForwardingUnit", "not_mem_B"): "NOT: EX/MEM không khớp toán hạng B|EX/MEM được ưu tiên hơn MEM/WB",
    ("ForwardingUnit", "from_wb_B"): "AND: forward toán hạng B từ MEM/WB|Chỉ khi EX/MEM không khớp (nó mới hơn)",
    ("ForwardingUnit", "ForwardB|from_wb_B"): "Ghép thành ForwardB: 10 EX/MEM, 01 MEM/WB, 00 thanh ghi|Mux ở EX nhận mã 2 bit",
    # ---------------- HazardUnit
    ("HazardUnit", "x0"): "Hằng số 0 (số thanh ghi x0)|Load vào x0 không gây phụ thuộc thật",
    ("HazardUnit", "rd_is_x0"): "rd_ex có phải x0 không|Load vào x0 không cần stall",
    ("HazardUnit", "rd_ok"): "NOT: rd_ex khác x0|Chỉ khi đích thật mới có phụ thuộc",
    ("HazardUnit", "hit1"): "rd_ex có bằng rs1_id không|Lệnh ở ID cần thanh ghi mà load đang đọc",
    ("HazardUnit", "hit2"): "rd_ex có bằng rs2_id không|Lệnh ở ID cần thanh ghi mà load đang đọc",
    ("HazardUnit", "uses"): "OR: lệnh ở ID dùng rs1 hoặc rs2 của load|Chỉ cần một trong hai khớp",
    ("HazardUnit", "stall"): "AND: load ở EX và rd khác x0 và có người dùng|=1: dừng PC, IF/ID một chu kỳ, chèn bubble|Forwarding không cứu được load-use",
    # ---------------- main
    ("main", "pc"): "PC (Program Counter): địa chỉ lệnh đang chạy|Nạp next_pc ở mỗi cạnh xung, RESET đưa về 0|Single-cycle cập nhật PC mỗi chu kỳ",
    ("main", "pc|pc_word"): "Lấy PC[9:2] làm địa chỉ từ của ROM|Lệnh dài 4 byte nên 2 bit thấp luôn 0",
    ("main", "four"): "Hằng số 4|Mỗi lệnh dài 4 byte, PC+4 là lệnh kế tiếp",
    ("main", "pc_plus4"): "Bộ cộng PC + 4: địa chỉ lệnh kế tiếp|Lệnh thường chạy tuần tự; jal/jalr cũng lưu PC+4 làm địa chỉ trả về",
    ("main", "instr"): "ROM lệnh 256 x 32: trả mã máy tại địa chỉ PC|Chương trình nằm sẵn trong ROM (kiểu Harvard)",
    ("main", "zero32"): "Hằng số 0 (32 bit)|Lui cần toán hạng A = 0 (ASel = 10)",
    ("main", "alu_a"): "Mux chọn toán hạng A của ALU theo ASel|00 rs1, 01 PC (auipc), 10 số 0 (lui)|Lui và auipc dùng lại ALU thay vì thêm phần cứng",
    ("main", "alu_b"): "Mux chọn toán hạng B của ALU theo ALUSrc|0 = rs2, 1 = hằng số imm|Lệnh R dùng thanh ghi, lệnh I/load/store dùng imm",
    ("main", "pc_target"): "Bộ cộng PC + imm: đích của branch/jal|ALU bận tính điều kiện/địa chỉ nên cần bộ cộng riêng",
    ("main", "mask_even"): "Hằng số 0xFFFFFFFE|Jalr xóa bit 0 của địa chỉ đích",
    ("main", "jalr_target"): "AND: (rs1 + imm) với mặt nạ, xóa bit 0|Đích của jalr phải là địa chỉ chẵn theo RISC-V",
    ("main", "take_target"): "OR: branch được rẽ hoặc là jal|=1: PC kế tiếp là PC + imm|Jal luôn nhảy, branch nhảy khi điều kiện đúng",
    ("main", "pc_a"): "Mux: PC+4 (0) hay PC+imm (1) theo take_target|Chọn giữa chạy tuần tự và rẽ nhánh/jal",
    ("main", "next_pc"): "Mux: pc_a (0) hay đích jalr (1) theo IsJALR|Jalr có đích tính bằng ALU, ưu tiên cao nhất",
    ("main", "wb_data"): "Mux chọn giá trị ghi vào rd theo WBSel|00 ALU, 01 RAM (load), 10 PC+4 (jal/jalr)|Mỗi loại lệnh lấy kết quả từ nguồn khác nhau",
    ("main", "one"): "Hằng số 1 (cho phép ghi PC mọi chu kỳ)|CPU single-cycle không bao giờ dừng PC",
    # ---------------- Pipeline
    ("Pipeline", "pc_if"): "PC (Program Counter): địa chỉ đang nạp lệnh|Giữ nguyên khi stall (run = 0), RESET đưa về 0|Stall dừng PC để lệnh load-use chờ",
    ("Pipeline", "pc_if|pc_word"): "Lấy PC[9:2] làm địa chỉ từ của ROM|Lệnh dài 4 byte nên 2 bit thấp luôn 0",
    ("Pipeline", "four"): "Hằng số 4|Mỗi lệnh dài 4 byte, PC+4 là lệnh kế tiếp",
    ("Pipeline", "pc_plus4_if"): "Bộ cộng PC + 4 ở tầng IF|Mặc định chạy tuần tự (dự đoán không rẽ)",
    ("Pipeline", "instr_if"): "ROM lệnh 256 x 32: trả mã máy tại PC|Chương trình nằm sẵn trong ROM (kiểu Harvard)",
    ("Pipeline", "next_pc"): "Mux: PC+4 (0) hay đích nhảy từ EX (1) theo pc_src_ex|Branch/jal/jalr được quyết định ở EX",
    ("Pipeline", "zero32"): "Hằng số 0 (32 bit)|Dùng làm lệnh rỗng (flush), toán hạng lui, ngả không dùng",
    ("Pipeline", "instr_in"): "Mux: lệnh vừa nạp (0) hay 0 = NOP (1) theo pc_src_ex|Khi rẽ nhánh, lệnh nạp nhầm phải bị hủy (flush)",
    ("Pipeline", "run"): "NOT: run = không stall|run = 0 thì PC và IF/ID đứng yên|Giữ lệnh trong ID khi phải chờ load",
    ("Pipeline", "pc_id"): "Thanh ghi IF/ID: PC của lệnh đang ở tầng ID|Đứng yên khi stall (we = run)|Sang tầng sau, tầng IF đã nạp lệnh khác",
    ("Pipeline", "instr_id"): "Thanh ghi IF/ID: mã máy của lệnh ở tầng ID|Đứng yên khi stall, thành 0 khi flush|Để ID giải mã trong khi IF nạp lệnh kế",
    ("Pipeline", "bubble"): "OR: stall hoặc flush (pc_src_ex)|=1: xóa từ điều khiển đưa vào ID/EX|Chèn lệnh rỗng (bubble) thay cho lệnh bị dừng/hủy",
    ("Pipeline", "zero_ctrl"): "Hằng số 0 (13 bit): từ điều khiển rỗng|Từ điều khiển bằng 0 = NOP, không ghi gì",
    ("Pipeline", "ctrl_in"): "Mux: từ điều khiển thật (0) hay rỗng (1) theo bubble|Đây là chỗ chèn bubble vào pipeline",
    ("Pipeline", "ctrl_id|RegWrite_id"): "Ghép các tín hiệu điều khiển thành từ 13 bit|Điều khiển sinh một lần ở ID rồi đi cùng lệnh",
    ("Pipeline", "ctrl_ex|RegWrite_ex"): "Tách từ điều khiển 13 bit ở tầng EX|Mỗi tầng chỉ lấy phần mình cần",
    ("Pipeline", "ctrl_mem_in|RegWrite_ex"): "Gom RegWrite, MemWrite, MemRead, WBSel cho tầng MEM|Các tín hiệu ALU/branch không cần nữa",
    ("Pipeline", "ctrl_mem|RegWrite_mem"): "Tách từ điều khiển 5 bit ở tầng MEM|MEM chỉ cần ghi/đọc RAM và chọn kết quả",
    ("Pipeline", "WBSel_mem|WBSel_mem"): "Lấy bit 1 của WBSel (kết quả là PC+4)|Forward từ EX/MEM phải biết là jal/jalr",
    ("Pipeline", "ctrl_wb_in|RegWrite_mem"): "Gom RegWrite, WBSel cho tầng WB|WB chỉ cần ghi thanh ghi và chọn kết quả",
    ("Pipeline", "ctrl_wb|RegWrite_wb"): "Tách từ điều khiển 3 bit ở tầng WB|WB chỉ cần RegWrite và WBSel",
    ("Pipeline", "fwd_mem_val"): "Mux: giá trị forward từ EX/MEM|0 = kết quả ALU, 1 = PC+4 (jal/jalr)|Jal/jalr ghi PC+4 chứ không phải kết quả ALU",
    ("Pipeline", "opA"): "Mux toán hạng A sau forwarding, chọn theo ForwardA|00 thanh ghi, 01 MEM/WB, 10 EX/MEM|Lấy giá trị mới nhất của rs1",
    ("Pipeline", "opB"): "Mux toán hạng B sau forwarding, chọn theo ForwardB|00 thanh ghi, 01 MEM/WB, 10 EX/MEM|Lấy giá trị mới nhất của rs2 (cũng là dữ liệu store)",
    ("Pipeline", "alu_a"): "Mux đầu vào A của ALU theo ASel_ex|opA, PC (auipc) hoặc 0 (lui)|Lui/auipc dùng lại ALU",
    ("Pipeline", "alu_b"): "Mux đầu vào B của ALU theo ALUSrc_ex|opB (rs2) hoặc imm|Lệnh R dùng thanh ghi, lệnh I/load/store dùng imm",
    ("Pipeline", "pc_target"): "Bộ cộng PC + imm: đích của branch/jal ở tầng EX|ALU bận tính điều kiện/địa chỉ nên cần bộ cộng riêng",
    ("Pipeline", "mask_even"): "Hằng số 0xFFFFFFFE|Jalr xóa bit 0 của địa chỉ đích",
    ("Pipeline", "jalr_target"): "AND: kết quả ALU với mặt nạ, xóa bit 0|Đích của jalr phải là địa chỉ chẵn",
    ("Pipeline", "target_ex"): "Mux: đích branch/jal (0) hay jalr (1) theo IsJALR_ex|Hai cách tính đích khác nhau, chọn một",
    ("Pipeline", "pc_src_ex"): "OR: branch được rẽ, jal hoặc jalr|=1: PC nhảy tới đích, flush IF/ID và ID/EX|Quyết định ở EX nên 2 lệnh đã nạp bị hủy",
    ("Pipeline", "pc_plus4_ex"): "Bộ cộng PC + 4 của lệnh ở EX|Jal/jalr phải lưu địa chỉ trả về PC+4",
    ("Pipeline", "wb_data"): "Mux chọn giá trị ghi vào rd theo WBSel_wb|00 ALU, 01 RAM (load), 10 PC+4|Cũng là nguồn forward từ MEM/WB",
    ("Pipeline", "one"): "Hằng số 1 (cho phép ghi mọi chu kỳ)|Các thanh ghi pipeline luôn nạp, trừ PC và IF/ID",
    ("Pipeline", "CLK_n"): "NOT: xung nhịp đảo CLK_n|RegisterFile ghi ở cạnh xuống để lệnh ở WB ghi và ID đọc cùng chu kỳ",
}

# meaning of the base name of a pipeline register
REGM = {
    "pc": "PC của lệnh", "instr": "mã máy của lệnh", "rs1_data": "giá trị thanh ghi rs1", "rs2_data": "giá trị thanh ghi rs2",
    "imm": "hằng số imm", "rs1": "số thanh ghi rs1", "rs2": "số thanh ghi rs2", "rd": "số thanh ghi đích rd",
    "funct3": "trường funct3", "funct7": "trường funct7", "ctrl": "từ điều khiển đóng gói",
    "alu_result": "kết quả ALU", "store_data": "dữ liệu của lệnh store", "pc_plus4": "PC+4 (địa chỉ trả về)",
    "mem_rdata": "dữ liệu đọc từ RAM",
}
STAGE = {"ex": ("ID/EX", "tầng EX"), "mem": ("EX/MEM", "tầng MEM"), "wb": ("MEM/WB", "tầng WB")}
WHYREG = {
    "ctrl": "Điều khiển sinh một lần ở ID rồi đi cùng lệnh",
    "rd": "Số thanh ghi đích phải đi cùng lệnh đến WB để ghi đúng chỗ",
    "pc_plus4": "Jal/jalr ghi PC+4, nên phải mang nó tới WB",
    "alu_result": "Là địa chỉ load/store hoặc kết quả ghi vào rd, dùng ở tầng sau",
    "mem_rdata": "Dữ liệu load đến WB để ghi vào rd",
    "store_data": "Dữ liệu store phải tới tầng MEM cùng lúc với địa chỉ",
}


def _i(attrs, key, default):
    try:
        return int(str(attrs.get(key, default)), 0)
    except ValueError:
        return default


def key_of(name, pins):
    """Key that identifies a component inside its circuit: its main output net."""
    if not pins:
        return None
    if name == "Splitter":
        bs = sorted(k for k in pins if k.startswith("b") and k != "bus")
        return f"{pins.get('bus')}|{pins[bs[0]]}" if bs else str(pins.get("bus"))
    if name == "Comparator":
        for k in ("eq", "lt", "gt"):
            if k in pins:
                return pins[k]
    if name == "Register":
        return pins.get("q")
    for k in ("out", "dout", "result"):
        if k in pins:
            return pins[k]
    return None


def _reg_caption(attrs, pins):
    lab = str(attrs.get("label", "")).strip()
    w = _i(attrs, "width", 8)
    if lab in ("PC",) or not lab:
        return None
    base, _, stage = lab.rpartition("_")
    if stage in STAGE and base in REGM:
        reg, where = STAGE[stage]
        return [f"{lab}: thanh ghi {reg} ({w} bit), lưu {REGM[base]}", "Chuyển giá trị sang " + where + " ở cạnh xung",
                WHYREG.get(base, "Mỗi tầng xử lý một lệnh khác nhau trong cùng chu kỳ")]
    return None


def _hand(circ, name, attrs):
    """Captions for the five hand-drawn circuits (components are told apart by type and attributes)."""
    if circ == "ALU":
        m = {
            "Adder": "Bộ cộng A + B (ALUCtrl = 0, ADD)|Add, addi, địa chỉ load/store, jalr đều cần phép cộng",
            "Subtractor": "Bộ trừ A - B (ALUCtrl = 1, SUB)|Sub và so sánh trong branch cần phép trừ",
            "AND Gate": "AND từng bit A và B (ALUCtrl = 2)|And, andi",
            "OR Gate": "OR từng bit A và B (ALUCtrl = 3)|Or, ori",
            "XOR Gate": "XOR từng bit A và B (ALUCtrl = 4)|Xor, xori",
            "Multiplexer": "Mux 16:1: chọn kết quả theo ALU_Ctrl|Mọi phép tính chạy song song, mux lấy phép cần dùng",
            "Splitter": "Splitter: lấy 5 bit thấp của B làm lượng dịch|RISC-V chỉ dịch 0..31 bit",
        }
        if name == "Shifter":
            k = str(attrs.get("shift", "ll"))
            return {"ll": "Dịch trái logic A << B[4:0] (ALUCtrl = 5, SLL)|Sll, slli",
                    "lr": "Dịch phải logic A >> B[4:0] (ALUCtrl = 6, SRL)|Srl, srli (chèn bit 0)",
                    "ar": "Dịch phải số học (ALUCtrl = 7, SRA)|Sra, srai (giữ nguyên bit dấu)"}[k]
        if name == "Comparator":
            if str(attrs.get("mode", "")) == "unsigned":
                return "So sánh không dấu A < B (ALUCtrl = 9, SLTU)|Sltu, sltiu coi số là không dấu"
            return "So sánh có dấu A < B (ALUCtrl = 8, SLT)|Slt, slti coi số là có dấu"
        if name == "Bit Extender":
            return "Mở rộng 0 kết quả 1 bit thành 32 bit (0 hoặc 1)|SLT phải trả đúng 0/1, mở rộng dấu sẽ ra 0xFFFFFFFF (lỗi đã sửa)"
        return m.get(name)
    if circ == "InstructionDecode" and name == "Splitter":
        return "Splitter 32 -> 6 phần: opcode, rd, funct3, rs1, rs2, funct7|Các trường nằm cố định trong lệnh nên chỉ cần đi dây"
    if circ == "RegisterFile":
        if name == "Demultiplexer":
            return "Demux 1:32: đưa RegWrite tới thanh ghi số rd|Chỉ thanh ghi đích được cho phép ghi"
        if name == "Multiplexer":
            return "Mux 32:1: cổng đọc, chọn thanh ghi theo rs1 hoặc rs2|Đọc bất đồng bộ để có toán hạng ngay"
        if name == "Constant":
            return "Hằng số 0 nối vào x0|X0 luôn bằng 0, không bao giờ đổi"
    if circ == "ImmGen":
        if name == "Splitter":
            return "Splitter: cắt các bit của hằng số khỏi lệnh / ghép đúng thứ tự|Bit hằng số bị xáo trộn có chủ đích trong lệnh"
        if name == "Bit Extender":
            return f"Mở rộng dấu {_i(attrs, 'in_width', 12)} bit thành 32 bit|Số âm phải giữ nguyên giá trị (-8 -> 0xFFFFFFF8)"
        if name == "Constant":
            return ("12 bit 0 đệm vào cuối (imm << 12)|Kiểu U (lui, auipc) đặt hằng số vào 20 bit cao"
                    if _i(attrs, "width", 1) == 12 else
                    "Bit 0 luôn bằng 0|Đích branch/jal là địa chỉ chẵn")
        if name == "Multiplexer":
            return "Mux 8:1: chọn kiểu hằng số theo ImmSel|0 I, 1 S, 2 B, 3 U, 4 J|Mỗi nhóm lệnh có kiểu hằng số khác nhau"
    if circ == "ALUControl":
        ops = {0: "ADD", 1: "SUB", 2: "AND", 3: "OR", 4: "XOR", 5: "SLL", 6: "SRL", 7: "SRA", 8: "SLT", 9: "SLTU"}
        if name == "Constant":
            v = _i(attrs, "value", 1)
            return f"Mã ALUCtrl = {v} ({ops.get(v, '?')})|Mỗi dòng của bảng mã ALU là một hằng số"
        if name == "Multiplexer":
            s = _i(attrs, "select", 1)
            if s == 3:
                return "Mux 8:1: tra bảng mã theo funct3|Funct3 chọn phép trong nhóm lệnh R hoặc I"
            if s == 2:
                return "Mux 4:1 theo ALUOp: 00 ADD, 01 SUB, 10 bảng R, 11 bảng I|Load/store/branch không cần tra funct3"
            return "Mux 2:1 theo funct7[5]: ADD/SUB hoặc SRL/SRA|Bit này phân biệt hai lệnh có cùng funct3"
        if name == "Splitter":
            return "Splitter: lấy funct7[5] (bit 30 của lệnh)|Chỉ bit này phân biệt ADD/SUB và SRL/SRA"
    return None


def lines(circ, name, attrs, pins=None):
    attrs = attrs or {}
    if name in SKIP:
        return None
    text = None
    if name in SUB and circ not in HAND:
        text = SUB[name]
    elif circ in HAND:
        text = _hand(circ, name, attrs)
    else:
        if name == "Register" and pins:
            cap = _reg_caption(attrs, pins)
            if cap:
                return cap
        k = key_of(name, pins)
        text = SPECIFIC.get((circ, k))
        if text is None and name == "Comparator" and circ == "MainControl" and k in CLS:
            op, cls = CLS[k]
            text = f"So opcode với hằng số {op}: nhóm {cls}|=1 thì cờ {k} bật. Mỗi nhóm có opcode riêng"
        if text is None and name == "Clock":
            text = "Xung nhịp (Clock): 0 -> 1 -> 0|Bấm Ctrl+F9 = một chu kỳ|Mọi thanh ghi đổi trạng thái theo xung này"
    if text is None:
        return None
    return text.split("|")
